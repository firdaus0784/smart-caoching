"""Perkakas kurasi tim — T-4 fitur 013, K-3, K-4, FR-I07, plan Bagian 2.2 dan 4.

    python -m perkakas.kurasi isi --berkas kandidat.json
    python -m perkakas.kurasi status --dokumen <id> --status <berlaku|diubah|dicabut>

Tersambung sebagai `peran_pengisi_antrean`; alamat dari `PGHOST` dan `PGPORT`,
sandi peran dari `PGPASSWORD` bila peladen memintanya. Tidak menjangkau
karantina, korpus, maupun basis data pseudonim.

## `isi` — satu-satunya jalan masuk antrean

Berkas JSON berisi daftar `{"butir": ButirPengetahuan, "sumber": SumberButir}`.
**Seluruh berkas diperiksa bentuknya lebih dulu**; satu entri yang salah
menolak seluruhnya, sehingga tidak ada setengah berkas yang tertulis. Sesudah
itu tiap kandidat melewati `saring()` fitur 010, dan **hanya** yang dinyatakan
`boleh_masuk_antrean` yang masuk.

Hari ini itu berarti **tidak satu pun**: lapis L4 menahan seluruh kandidat
sampai ambang relevansi dikalibrasi (BT-24, C-16). Meloloskan kandidat yang
tertahan di L4 sama dengan memilih ambang "longgar" yang uraian `saring.py`
tolak, dan pilihan itu bukan milik perkakas ini — TK-72. Perkakas menyebut
jumlah yang tertahan alih-alih diam.

Keluaran hanya memuat **jumlah**. Isi butir tidak dikutip: ia dapat memuat
apa pun yang terbawa dari dokumen sumber.

## `status` — salinan status regulasi (K-4)

Memperbarui salinan status setiap kandidat dan butir tayang bersumber dokumen
itu. Bila statusnya `diubah` atau `dicabut`, setiap butir tayang yang belum
ditarik **ditarik otomatis** — D-06 Bagian 7.5, aturan yang sama dengan
`tinjau(pemicu=REGULASI_SUMBER_BERUBAH)` fitur 010: regulasi yang tidak lagi
berlaku menarik, tanpa pengecualian. Fungsi itu sendiri tidak dipanggil karena
ia menuntut `ButirTayang` utuh beserta putusannya, dan menyusun ulang putusan
dari baris tersimpan hanya untuk membaca satu pemetaan adalah memalsukan
putusan.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from pydantic import BaseModel, ConfigDict, ValidationError
from src.ingest.kurasi.butir import ButirPengetahuan
from src.ingest.kurasi.saring import HasilSaring, Tindakan, saring
from src.ingest.kurasi.sumber import SumberButir
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.kurasi import (
    PERAN_PENGISI_ANTREAN,
    BarisKandidat,
    PengisiAntrean,
    PengisiAntreanPostgres,
)

_STATUS = ("berlaku", "diubah", "dicabut")

Penyaring = Callable[..., HasilSaring]


class _Entri(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    butir: ButirPengetahuan
    sumber: SumberButir


def _penghurai() -> argparse.ArgumentParser:
    penghurai = argparse.ArgumentParser(
        prog="python -m perkakas.kurasi", description="Isi antrean kurasi dan perbarui status."
    )
    sub = penghurai.add_subparsers(dest="perintah", required=True)
    isi = sub.add_parser("isi", help="masukkan kandidat yang lolos penyaringan ke antrean")
    isi.add_argument("--berkas", required=True)
    status = sub.add_parser("status", help="perbarui status regulasi sebuah dokumen sumber")
    status.add_argument("--dokumen", required=True)
    status.add_argument("--status", required=True)
    return penghurai


def _baca(berkas: str) -> list[_Entri] | None:
    """Seluruh entri, atau `None` bila satu saja tidak sesuai bentuk."""
    try:
        mentah = json.loads(Path(berkas).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(mentah, list):
        return None
    try:
        entri = [_Entri.model_validate(satu) for satu in mentah]
    except ValidationError:
        return None
    ids = [e.butir.id_butir for e in entri]
    return entri if len(set(ids)) == len(ids) else None


async def _isi(
    berkas: str,
    pengisi: PengisiAntrean,
    penyaring: Penyaring,
    keluar: TextIO,
    galat: TextIO,
    sekarang: datetime,
) -> int:
    entri = _baca(berkas)
    if entri is None:
        print(
            "Ditolak: berkas tidak terbaca, atau ada entri yang tidak sesuai bentuk butir "
            "dan sumber, atau id butir ganda. Tidak ada yang dimasukkan.",
            file=galat,
        )
        return 2
    dikenal = set(await pengisi.dokumen_dikenal())
    hitung = {"masuk": 0, "sudah": 0, "tertahan": 0, "dibuang": 0, "historis": 0, "cadangan": 0}
    for satu in entri:
        hasil = penyaring(satu.butir, id_dokumen_dikenal=frozenset(dikenal))
        if not hasil.boleh_masuk_antrean:
            hitung[_KELOMPOK[hasil.tindakan]] += 1
            continue
        masuk = await pengisi.tambah_kandidat(
            BarisKandidat(
                id_butir=satu.butir.id_butir,
                butir=satu.butir.model_dump(mode="json"),
                sumber=satu.sumber.model_dump(mode="json"),
                id_dokumen_sumber=satu.butir.id_dokumen_sumber,
                kategori=satu.butir.kategori.value,
                status_keberlakuan=None
                if satu.butir.status_keberlakuan is None
                else satu.butir.status_keberlakuan.value,
                masuk_pada=sekarang,
            )
        )
        hitung["masuk" if masuk else "sudah"] += 1
        dikenal.add(satu.butir.id_dokumen_sumber)
    print(
        f"Masuk antrean: {hitung['masuk']}. Sudah ada: {hitung['sudah']}. "
        f"Tertahan menunggu penyaring relevansi: {hitung['tertahan']}. "
        f"Dibuang: {hitung['dibuang']}. "
        f"Rujukan historis, tidak masuk antrean: {hitung['historis']}. "
        f"Kolam cadangan: {hitung['cadangan']}.",
        file=keluar,
    )
    return 0


_KELOMPOK: dict[Tindakan, str] = {
    Tindakan.TERTAHAN: "tertahan",
    Tindakan.DIBUANG: "dibuang",
    Tindakan.RUJUKAN_HISTORIS: "historis",
    Tindakan.KOLAM_CADANGAN: "cadangan",
}
"""Pemetaan berkunci: tindakan keenam yang ditambahkan fitur 010 berhenti pada
`KeyError`, bukan terhitung diam-diam sebagai salah satu yang lima."""


async def _status(
    dokumen: str,
    status: str,
    pengisi: PengisiAntrean,
    keluar: TextIO,
    galat: TextIO,
    sekarang: datetime,
) -> int:
    if status not in _STATUS or not dokumen.strip() or periksa_data_pribadi(dokumen):
        # Masukan yang ditolak tidak dikutip: ia mungkin nomor pribadi.
        print(
            "Ditolak: --dokumen wajib id dokumen sumber, --status wajib berlaku, diubah, "
            "atau dicabut.",
            file=galat,
        )
        return 2
    aktif = await pengisi.perbarui_status(dokumen, status)
    ditarik = 0
    if status != "berlaku":
        alasan = f"regulasi sumber berstatus {status} — ditarik otomatis (C-07, KL-07)"
        for id_butir in aktif:
            if await pengisi.tarik_otomatis(id_butir, alasan, sekarang=sekarang):
                ditarik += 1
    print(f"Status dokumen diperbarui. Butir tayang ditarik: {ditarik}.", file=keluar)
    return 0


def utama(
    argv: list[str],
    *,
    pengisi: PengisiAntrean,
    keluar: TextIO = sys.stdout,
    galat: TextIO = sys.stderr,
    penyaring: Penyaring = saring,
    sekarang: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """Titik masuk yang dapat diuji. `penyaring` disuntikkan hanya oleh uji;
    perkakas sungguhan memakai `saring()` fitur 010."""
    argumen = _penghurai().parse_args(argv)
    if argumen.perintah == "isi":
        return asyncio.run(_isi(argumen.berkas, pengisi, penyaring, keluar, galat, sekarang()))
    return asyncio.run(_status(argumen.dokumen, argumen.status, pengisi, keluar, galat, sekarang()))


class _SambunganPengisi:  # pragma: no cover — dipakai orang, bukan uji
    """Satu sambungan baru per kueri, sebagai `peran_pengisi_antrean`."""

    def __init__(self, host: str, porta: int) -> None:
        self._host, self._porta = host, porta

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        sambungan = await asyncpg.connect(
            host=self._host, port=self._porta, user=PERAN_PENGISI_ANTREAN, database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def fetch(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetch", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("execute", kueri, *argumen)


if __name__ == "__main__":  # pragma: no cover
    import os

    sambungan = _SambunganPengisi(
        os.environ.get("PGHOST", "127.0.0.1"), int(os.environ.get("PGPORT", "5432"))
    )
    raise SystemExit(utama(sys.argv[1:], pengisi=PengisiAntreanPostgres(sambungan)))
