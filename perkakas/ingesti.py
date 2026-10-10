"""Perkakas ingesti tim — T-6 fitur 037, K-4, P-2 A, P-6 A, TK-83.

    python -m perkakas.ingesti terima --berkas <jalur> --id <id> --judul <judul>
        --jenis <JenisSumber> --penerbit <penerbit> --tahun <tahun>
        --kerahasiaan <TingkatKerahasiaan> --persetujuan <StatusPersetujuan>
        --pelaku <kode-tim>
    python -m perkakas.ingesti daftar
    python -m perkakas.ingesti baca --id <id>
    python -m perkakas.ingesti tinjau --id <id> --pelaku <kode-tim> --catatan <catatan>
    python -m perkakas.ingesti setujui --id <id> --pelaku <kode-tim> --alasan <alasan>
    python -m perkakas.ingesti tolak --id <id> --pelaku <kode-tim> --alasan <alasan>
    python -m perkakas.ingesti cabut --id <id> --pelaku <kode-tim> --alasan <alasan>

**Satu peran per perintah** (P-2 A): `terima` tersambung sebagai
`peran_ingesti`, yang menaruh dokumen tanpa dapat membacanya; `daftar`, `baca`,
`tinjau`, `setujui`, dan `tolak` sebagai `peran_verifikasi`; `cabut` sebagai
`peran_penarikan_dokumen`. Alamat dari `PGHOST` dan `PGPORT`, sandi dari
`PGPASSWORD` bila peladen memintanya. Tiap perintah objek `Gerbang` baru di
atas catatan PostgreSQL: keadaannya bertahan antarperintah (P-1 A).

**Aturan tetap milik gerbang fitur 002.** Perkakas hanya mengekstrak berkas,
memeriksa bentuk masukan, dan menyusun gerbang dengan peran yang benar.

**Pelaku diperiksa sebelum menyambung** (P-6 A): kode anggota tim berpola
`tm-001`, bukan nama orang. Masukan yang ditolak tidak dikutip.

**Teks hanya pada keluaran `baca`**, ke keluaran baku, diawali pernyataan
bahwa nama dan alamat tidak tersamarkan otomatis (BT-70, R-08). Perkakas tidak
menulis apa pun ke log. Keluaran OCR dicatat ke logbook L2 seperti fitur 015
(C-09): versi mesin dan sidik model, bukan teksnya.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Final, TextIO

from pydantic import ValidationError
from src.ingest.dokumen import Dokumen, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.ekstraksi.dasar import Pengekstrak, TeksKanonik
from src.ingest.ekstraksi.docx import PengekstrakDocx
from src.ingest.ekstraksi.galat import GalatEkstraksi
from src.ingest.ekstraksi.jejak_ocr import catat_keluaran_ocr
from src.ingest.ekstraksi.ocr import PengekstrakOcr, TeksPindaian
from src.ingest.ekstraksi.pdf import GalatTanpaLapisanTeks, PengekstrakPdf
from src.ingest.ekstraksi.xlsx import PengekstrakXlsx
from src.ingest.gerbang import GalatGerbang, Gerbang
from src.ingest.jejak import GalatJejak
from src.ingest.peringkat import JenisSumber
from src.nlp.anonimisasi.pola import JENIS
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenTidakAda
from src.penyimpanan.karantina import (
    PERAN_INGESTI,
    PERAN_PENARIKAN_DOKUMEN,
    PERAN_VERIFIKASI,
    CatatanGerbangPostgres,
)
from src.penyimpanan.kredensial_baku import VERIFIKASI
from src.penyimpanan.postgres import PenyimpanPostgres
from src.penyimpanan.sambungan import SambunganAktif

POLA_PELAKU: Final = re.compile(r"^[a-z]{2,8}-[0-9]{3}$")
"""Kode anggota tim — sama dengan batasan tabel `15-ingesti.sql` (P-6 A)."""

PERAN_PERINTAH: Final[dict[str, str]] = {
    "terima": PERAN_INGESTI,
    "daftar": PERAN_VERIFIKASI,
    "baca": PERAN_VERIFIKASI,
    "tinjau": PERAN_VERIFIKASI,
    "setujui": PERAN_VERIFIKASI,
    "tolak": PERAN_VERIFIKASI,
    "cabut": PERAN_PENARIKAN_DOKUMEN,
}
"""Satu peran per perintah — P-2 A. Perintah kedelapan tanpa baris di sini
berhenti pada `KeyError`, bukan tersambung dengan peran yang kebetulan ada."""

PERNYATAAN_BT70: Final = (
    "Perhatian: nama orang, alamat, dan nomor yang ditulis dengan kata tidak tersamarkan "
    "otomatis. Periksa teks di bawah sebelum menyetujui."
)

_LABEL_SAMARAN: Final[dict[str, str]] = {
    "nik": "NIK",
    "nip": "NIP",
    "nisn": "NISN",
    "nuptk": "NUPTK",
    "telepon": "telepon",
    "rekening": "rekening",
}


def pengekstrak_baku() -> list[Pengekstrak]:
    """Pengekstrak fitur 015 berurutan. PDF tanpa lapisan teks dialihkan ke
    OCR (FR-B02) — pengekstrak berikutnya yang menanganinya."""
    return [PengekstrakPdf(), PengekstrakDocx(), PengekstrakXlsx(), PengekstrakOcr()]


def _penghurai() -> argparse.ArgumentParser:
    penghurai = argparse.ArgumentParser(
        prog="python -m perkakas.ingesti",
        description="Gerbang ingesti: terima, daftar, baca, tinjau, setujui, tolak, cabut.",
    )
    sub = penghurai.add_subparsers(dest="perintah", required=True)
    terima = sub.add_parser("terima", help="terima berkas ke karantina")
    terima.add_argument("--berkas", required=True)
    terima.add_argument("--id", required=True)
    terima.add_argument("--judul", required=True)
    terima.add_argument("--jenis", required=True, choices=[j.value for j in JenisSumber])
    terima.add_argument("--penerbit", required=True)
    terima.add_argument("--tahun", required=True, type=int)
    terima.add_argument(
        "--kerahasiaan", required=True, choices=[t.value for t in TingkatKerahasiaan]
    )
    terima.add_argument(
        "--persetujuan", required=True, choices=[s.value for s in StatusPersetujuan]
    )
    terima.add_argument("--pelaku", required=True)
    sub.add_parser("daftar", help="dokumen yang menunggu di karantina")
    baca = sub.add_parser("baca", help="teks tersamar dan temuan, bagi verifikator")
    baca.add_argument("--id", required=True)
    tinjau = sub.add_parser("tinjau", help="tandai temuan pola sudah ditinjau")
    tinjau.add_argument("--id", required=True)
    tinjau.add_argument("--pelaku", required=True)
    tinjau.add_argument("--catatan", required=True)
    for nama, bantuan in (
        ("setujui", "pindahkan ke korpus"),
        ("tolak", "tahan di karantina"),
        ("cabut", "tarik persetujuan pemilik; keluarkan dari korpus"),
    ):
        putusan = sub.add_parser(nama, help=bantuan)
        putusan.add_argument("--id", required=True)
        putusan.add_argument("--pelaku", required=True)
        putusan.add_argument("--alasan", required=True)
    return penghurai


def _ekstrak(jalur: Path, pengekstrak: Sequence[Pengekstrak]) -> TeksKanonik:
    """Pengekstrak pertama yang menangani berkas itu; PDF tanpa lapisan teks
    berlanjut ke penangan berikutnya (OCR)."""
    penangan = [p for p in pengekstrak if p.menangani(jalur)]
    if not penangan:
        raise GalatEkstraksi(
            f"tanpa penangan: {jalur.suffix}",
            "Jenis berkas ini tidak didukung. Gunakan PDF, DOCX, XLSX, atau gambar pindaian.",
        )
    for satu in penangan[:-1]:
        try:
            return satu.ekstrak(jalur)
        except GalatTanpaLapisanTeks:
            continue
    return penangan[-1].ekstrak(jalur)


def _samaran(jumlah: dict[str, int]) -> str:
    return ", ".join(f"{_LABEL_SAMARAN[j]} {jumlah.get(j, 0)}" for j in JENIS)


def _susun(sambung: Callable[[str], SambunganAktif], perintah: str) -> Gerbang:
    sambungan = sambung(PERAN_PERINTAH[perintah])
    dokumen = PenyimpanPostgres(sambungan)
    return Gerbang(dokumen, catatan=CatatanGerbangPostgres(sambungan, dokumen))


async def _jalankan(
    argumen: argparse.Namespace,
    sambung: Callable[[str], SambunganAktif],
    pengekstrak: Sequence[Pengekstrak],
    akar_logbook: Path,
    keluar: TextIO,
) -> None:
    perintah = argumen.perintah
    if perintah == "terima":
        teks = _ekstrak(Path(argumen.berkas), pengekstrak)
        dokumen = Dokumen(
            id=argumen.id,
            judul=argumen.judul,
            jenis=JenisSumber(argumen.jenis),
            penerbit=argumen.penerbit,
            tahun=argumen.tahun,
            tingkat_kerahasiaan=TingkatKerahasiaan(argumen.kerahasiaan),
            status_persetujuan_pemilik=StatusPersetujuan(argumen.persetujuan),
        )
        if isinstance(teks, TeksPindaian):
            catat_keluaran_ocr(akar_logbook, teks)
        gerbang = _susun(sambung, perintah)
        hasil = await gerbang.terima(dokumen, teks.isi, id_penerima=argumen.pelaku)
        print(
            f"Diterima ke karantina: {dokumen.id}. Disamarkan: {_samaran(hasil.samaran)}. "
            f"Temuan pola instruksi: {hasil.jumlah_temuan}.",
            file=keluar,
        )
        return

    gerbang = _susun(sambung, perintah)
    if perintah == "daftar":
        ringkasan = await gerbang.daftar(VERIFIKASI)
        print(f"Dokumen di karantina: {len(ringkasan)}.", file=keluar)
        for r in ringkasan:
            d = r.dokumen
            print(
                f"{d.id} | {d.judul} | {d.jenis.value} | {d.tingkat_kerahasiaan.value} | "
                f"persetujuan {d.status_persetujuan_pemilik.value} | "
                f"anonimisasi {d.status_anonimisasi.value} | temuan {r.jumlah_temuan}"
                f"{', ditinjau' if r.ditinjau else ''} | disamarkan {_samaran(r.samaran)}",
                file=keluar,
            )
        return
    if perintah == "baca":
        isi = await gerbang.penyimpan.baca_dokumen(
            VERIFIKASI, await gerbang.area(VERIFIKASI, argumen.id), argumen.id
        )
        print(PERNYATAAN_BT70, file=keluar)
        print(
            f"Disamarkan: {_samaran(await gerbang.samaran(VERIFIKASI, argumen.id))}.", file=keluar
        )
        print("", file=keluar)
        print(str(isi), file=keluar)
        temuan = await gerbang.temuan(VERIFIKASI, argumen.id)
        print("", file=keluar)
        print(f"Temuan pola instruksi: {len(temuan)}.", file=keluar)
        for t in temuan:
            print(f"- {t.pola} [{t.mulai}-{t.akhir}]: {t.kutipan}", file=keluar)
        return
    if perintah == "tinjau":
        await gerbang.tinjau_temuan(VERIFIKASI, argumen.id, argumen.pelaku, argumen.catatan)
        print(f"Tinjauan tercatat: {argumen.id}.", file=keluar)
    elif perintah == "setujui":
        await gerbang.setujui(
            VERIFIKASI, argumen.id, id_verifikator=argumen.pelaku, alasan=argumen.alasan
        )
        print(f"Disetujui dan dipindahkan ke korpus: {argumen.id}.", file=keluar)
    elif perintah == "tolak":
        await gerbang.tolak(
            VERIFIKASI, argumen.id, id_verifikator=argumen.pelaku, alasan=argumen.alasan
        )
        print(f"Ditolak, tetap di karantina: {argumen.id}.", file=keluar)
    else:
        await gerbang.cabut_persetujuan(
            argumen.id, id_pemohon=argumen.pelaku, alasan=argumen.alasan
        )
        dari = gerbang.jejak.baris()[-1].dari_area.value
        print(f"Persetujuan dicabut: {argumen.id}. Dikeluarkan dari {dari}.", file=keluar)


def utama(
    argv: list[str],
    *,
    sambung: Callable[[str], SambunganAktif],
    keluar: TextIO = sys.stdout,
    galat: TextIO = sys.stderr,
    pengekstrak: Sequence[Pengekstrak] | None = None,
    akar_logbook: Path = Path("logbook"),
) -> int:
    """Titik masuk yang dapat diuji. Kode keluar: 0 berhasil, 1 ditolak gerbang
    atau peladen, 2 masukan tidak sah — sebelum menyambung.

    Pesan galat tidak mengutip masukan, alasan, catatan, maupun teks: semuanya
    dapat memuat data pribadi (KM-03)."""
    try:
        argumen = _penghurai().parse_args(argv)
    except SystemExit as keluar_parser:
        return int(keluar_parser.code or 2)
    if getattr(argumen, "pelaku", None) is not None and not POLA_PELAKU.fullmatch(argumen.pelaku):
        print("Ditolak: --pelaku wajib kode anggota tim berpola tm-001, bukan nama.", file=galat)
        return 2
    try:
        asyncio.run(
            _jalankan(
                argumen,
                sambung,
                pengekstrak if pengekstrak is not None else pengekstrak_baku(),
                akar_logbook,
                keluar,
            )
        )
    except GalatEkstraksi as g:
        print(f"Ditolak: {g.pesan_pengguna}", file=galat)
        return 2
    except ValidationError:
        print(
            "Ditolak: metadata dokumen tidak sah. Periksa judul, penerbit, dan tahun.", file=galat
        )
        return 2
    except (GalatGerbang, GalatJejak) as g:
        print(f"Ditolak gerbang: {g}", file=galat)
        return 1
    except (GalatDokumenTidakAda, GalatAksesDitolak):
        print(
            "Ditolak: dokumen tidak dikenal pada area yang dapat dijangkau perintah ini.",
            file=galat,
        )
        return 1
    except Exception as g:
        print(f"Ditolak peladen ({type(g).__name__}). Tidak ada yang berubah.", file=galat)
        return 1
    return 0


class _SambunganPeran:  # pragma: no cover — dipakai orang, bukan uji
    """Satu sambungan baru per kueri, sebagai peran perintahnya."""

    def __init__(self, host: str, porta: int, peran: str) -> None:
        self._host, self._porta, self._peran = host, porta, peran

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        sambungan = await asyncpg.connect(
            host=self._host, port=self._porta, user=self._peran, database="smart_coaching"
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

    alamat = os.environ.get("PGHOST", "127.0.0.1"), int(os.environ.get("PGPORT", "5432"))
    raise SystemExit(utama(sys.argv[1:], sambung=lambda peran: _SambunganPeran(*alamat, peran)))
