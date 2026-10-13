"""Jejak *gold set* pada logbook — T-6 fitur 040, R-03, R-06, R-07, C-09, AP-05.

Dua catatan. **Pembekuan** satu baris L2 (D-10 Bagian 4, D-08 Bagian 5.3):
versi, sidik, tanggal, komposisi, pelaku. **Putaran** satu baris L1 (D-10
Bagian 3): kelima bidang `Versi`, sidik *gold set*, konfigurasi, hasil —
termasuk putaran yang gagal.

## Ditulis lewat `tambah_baris`, dibaca di sini

`src/logbook/` milik fitur 026 yang sudah lolos Gerbang 4 dan tidak disentuh
(KB-298). Penulisan lewat `tambah_baris`, pola yang sama dengan pencatatan
ekspor ontologi fitur 005; `penulis.py` tetap satu-satunya jalur menulis.
Pembacaan tidak dibatasi aturan itu.

## Pengenal, tidak pernah teks

Kedua catatan memuat pengenal pertanyaan, dokumen, bagian, dan segmen. Teks
pertanyaan tidak sampai ke logbook (R-07): berkas logbook masuk repositori,
sedangkan *gold set* wajib tinggal di luarnya (R-01).

## Pembukaan dihitung, tidak diingat

AP-05: data uji dibuka satu kali, dan bila terpaksa dipakai ulang hal itu
dinyatakan. Setiap baris L1 membawa urutan pembukaan *gold set*-nya, dihitung
dari L1 sendiri — sehingga pernyataan itu tidak bergantung pada ingatan siapa
pun.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.logbook.penulis import BENTUK_WAKTU, Buku, tambah_baris
from src.logbook.versi import BELUM_BERLAKU, Versi
from src.rag.evaluasi.gold_set import GoldSet
from src.rag.evaluasi.metrik import K_PRESISI, K_RECALL, Nilai, TigaMetrik
from src.rag.evaluasi.pengukur import HasilPutaran

ARTEFAK: Final = "gold-set"
TUGAS: Final = "pengambilan"
TUJUAN: Final = "Mengukur pengambilan atas gold set beku menurut D-08 Bagian 6 (U3)"
_ID_PERCOBAAN: Final = re.compile(r"EXP-\d{4}-\d{3}")


class VersiGoldSet(BaseModel):
    """Baris L2 *gold set* — D-10 Bagian 4, D-08 Bagian 5.3. Tanpa nilai baku."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    artefak: Literal["gold-set"] = ARTEFAK
    versi: str = Field(min_length=1)
    sidik: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    dibekukan_pada: datetime
    jumlah: int = Field(ge=1)
    komposisi_jenis: dict[str, int]
    komposisi_kategori: dict[str, int]
    jumlah_bernomor_regulasi: int = Field(ge=0)
    pelaku: str = Field(min_length=1)
    """Yang dapat ditanya — spec fitur 025 menolak "tim"."""

    @model_validator(mode="after")
    def _utuh(self) -> VersiGoldSet:
        if self.dibekukan_pada.tzinfo is None:
            raise ValueError("dibekukan_pada wajib berzona waktu — KM-01 menuntut UTC")
        if not self.pelaku.strip():
            raise ValueError("pelaku hampa")
        for nama, komposisi in (
            ("jenis", self.komposisi_jenis),
            ("kategori", self.komposisi_kategori),
        ):
            if any(n < 0 for n in komposisi.values()) or sum(komposisi.values()) != self.jumlah:
                raise ValueError(f"komposisi {nama} tidak menjumlah {self.jumlah}")
        if self.jumlah_bernomor_regulasi > self.jumlah:
            raise ValueError("jumlah bernomor regulasi melampaui jumlah pertanyaan")
        return self


class GalatPembekuan(Exception):
    """Pembekuan ditolak; tidak ada yang ditulis."""


def baca(akar: Path, buku: Buku) -> tuple[dict[str, object], ...]:
    """Baris terurai satu buku; buku yang belum ada → kosong."""
    berkas = akar / buku.value
    if not berkas.is_file():
        return ()
    hasil: list[dict[str, object]] = []
    for nomor, mentah in enumerate(berkas.read_text(encoding="utf-8").splitlines(), start=1):
        if not mentah.strip():
            continue
        obj = json.loads(mentah)
        if not isinstance(obj, dict):
            raise ValueError(f"{buku.value} baris {nomor} bukan objek JSON")
        hasil.append(obj)
    return tuple(hasil)


def _beku(akar: Path) -> tuple[VersiGoldSet, ...]:
    """Seluruh baris *gold set* L2. Baris rusak menolak, tidak diabaikan."""
    return tuple(
        VersiGoldSet.model_validate({k: v for k, v in b.items() if k != BENTUK_WAKTU})
        for b in baca(akar, Buku.L2)
        if b.get("artefak") == ARTEFAK
    )


def pembekuan(akar: Path, sidik: str) -> VersiGoldSet | None:
    """Baris pembekuan bersidik ini, bila ada — R-03."""
    return next((v for v in _beku(akar) if v.sidik == sidik), None)


def bekukan(
    akar: Path, gold: GoldSet, *, versi: str, pelaku: str, sekarang: datetime
) -> VersiGoldSet:
    """Satu baris L2. Komposisi D-08 Bagian 5.1 persis (P-3 A)."""
    menyimpang = gold.penyimpangan()
    if menyimpang:
        rincian = ", ".join(f"{j.value} {ada}/{d08}" for j, (ada, d08) in menyimpang.items())
        raise GalatPembekuan(f"komposisi menyimpang dari D-08 Bagian 5.1: {rincian}")
    beku = _beku(akar)
    sama = next((v for v in beku if v.sidik == gold.sidik), None)
    if sama is not None:
        raise GalatPembekuan(f"isi ini sudah beku sebagai versi {sama.versi}")
    if any(v.versi == versi for v in beku):
        raise GalatPembekuan(f"versi {versi} sudah dipakai bersidik lain")
    catatan = VersiGoldSet(
        versi=versi,
        sidik=gold.sidik,
        dibekukan_pada=sekarang,
        jumlah=len(gold.pertanyaan),
        komposisi_jenis={j.value: n for j, n in gold.komposisi().items()},
        komposisi_kategori=gold.komposisi_kategori(),
        jumlah_bernomor_regulasi=gold.jumlah_bernomor_regulasi(),
        pelaku=pelaku,
    )
    tambah_baris(akar, Buku.L2, catatan.model_dump(mode="json"))
    return catatan


def id_percobaan_terpakai(akar: Path, id_percobaan: str) -> bool:
    return any(b.get("id_percobaan") == id_percobaan for b in baca(akar, Buku.L1))


def pembukaan_berikutnya(akar: Path, sidik: str) -> int:
    """Urutan pembukaan putaran berikutnya atas *gold set* bersidik ini."""
    return 1 + sum(
        b.get("tugas") == TUGAS and b.get("sidik_gold_set") == sidik for b in baca(akar, Buku.L1)
    )


def _nilai(n: Nilai) -> dict[str, object]:
    return {
        "pembilang": str(n.pembilang),
        "penyebut": n.penyebut,
        "persen": n.persen(),
        "terhitung": n.terhitung,
    }


def _tiga(t: TigaMetrik) -> dict[str, object]:
    return {"recall_8": _nilai(t.recall_8), "mrr": _nilai(t.mrr), "presisi_5": _nilai(t.presisi_5)}


def konfigurasi_l1(putaran: HasilPutaran) -> dict[str, object]:
    k = putaran.konfigurasi
    return {
        "sumber": k.sumber,
        "indeks": k.indeks.value,
        "kedalaman": k.kedalaman,
        "versi_penyemat": k.versi_penyemat,
        "k_recall": K_RECALL,
        "k_presisi": K_PRESISI,
    }


def hasil_l1(putaran: HasilPutaran) -> dict[str, object]:
    """Bidang `hasil` L1: angka beserta pecahannya, per kelas, pengenal saja."""
    r = putaran.ringkasan
    return {
        "putusan": putaran.putusan.name,
        "jumlah_pertanyaan": len(putaran.pertanyaan),
        "utama": _tiga(r.utama),
        "recall_bernomor_regulasi": _nilai(r.recall_bernomor),
        "per_jenis": {j.value: _tiga(t) for j, t in r.per_jenis.items()},
        "per_kategori": {k: _tiga(t) for k, t in r.per_kategori.items()},
        "kebocoran": {"jumlah": len(putaran.kebocoran), "segmen": list(putaran.kebocoran)},
        "pertanyaan_gagal": [
            {
                "id": h.nilai.id,
                "jenis": h.nilai.jenis.value,
                "peringkat_pertama": h.nilai.peringkat_pertama,
                "kunci_luput": [
                    {
                        "urutan": k.urutan,
                        "dokumen": k.kunci.dokumen,
                        "bagian": k.kunci.bagian,
                        "sebab": k.sebab.name,
                    }
                    for k in h.luput
                ],
            }
            for h in putaran.gagal
        ],
        "pertanyaan_bocor": [
            {"id": h.nilai.id, "segmen": list(h.bocor)} for h in putaran.pertanyaan if h.bocor
        ],
    }


def catat_putaran(
    akar: Path,
    *,
    id_percobaan: str,
    beku: VersiGoldSet,
    versi_kode: str,
    versi_indeks: str,
    versi_model: str,
    konfigurasi: Mapping[str, object],
    hasil: Mapping[str, object],
    status: str,
    catatan: str,
    durasi_detik: int,
) -> None:
    """Satu baris L1 — D-10 Bagian 3, R-06. Putaran gagal wajib tercatat."""
    if not _ID_PERCOBAAN.fullmatch(id_percobaan):
        raise ValueError("id_percobaan wajib berbentuk EXP-2026-nnn (D-10 Bagian 3)")
    if status not in ("berhasil", "gagal"):
        raise ValueError(f"status {status!r} bukan berhasil atau gagal")
    if status == "gagal" and not catatan.strip():
        raise ValueError("putaran gagal wajib menyebut dugaan penyebab (D-10 Bagian 3)")
    if id_percobaan_terpakai(akar, id_percobaan):
        raise ValueError(f"{id_percobaan} sudah tercatat pada L1")
    versi = Versi(
        versi_kode=versi_kode,
        versi_model=versi_model,
        versi_indeks=versi_indeks,
        versi_skema_anotasi=BELUM_BERLAKU,
        pembagian_data=BELUM_BERLAKU,
    )
    tambah_baris(
        akar,
        Buku.L1,
        {
            "id_percobaan": id_percobaan,
            "tujuan": TUJUAN,
            "tugas": TUGAS,
            "model_dasar": BELUM_BERLAKU,
            "perangkat_keras": BELUM_BERLAKU,
            "versi_gold_set": beku.versi,
            "sidik_gold_set": beku.sidik,
            "pembukaan_gold_set": pembukaan_berikutnya(akar, beku.sidik),
            "konfigurasi": dict(konfigurasi),
            "durasi_detik": durasi_detik,
            "hasil": dict(hasil),
            "status": status,
            "catatan": catatan,
            **versi.model_dump(),
        },
    )
