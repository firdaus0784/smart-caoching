"""Bentuk galat — R-09, C-13, C-20, `docs/D14.md` Bagian 4.2.

Bentuk galat adalah satu-satunya bagian kontrak D-14 yang sudah diwujudkan
pada fitur 001. Ia dipakai ulang oleh keadaan KL-D pada layar (`docs/D05.md`
Bagian 7) ketika fitur 013 tiba; menetapkannya sekarang menghindari
penerjemahan ulang, dan penerjemahan ulang adalah tempat bentuk menyimpang.

Dua aturan yang mudah dilanggar tanpa disadari:

**Pesan pengguna tanpa rincian teknis.** Nama penyedia, kode HTTP, dan jejak
tumpukan tidak boleh sampai ke pengguna. Bukan karena rahasia, melainkan
karena `docs/D05.md` Bagian 10 menetapkan pesan galat ditulis dalam bahasa
manusia — persona P1 tidak dapat berbuat apa pun dengan "HTTP 503".

**Paling banyak dua puluh kata per kalimat** (NFR-19, C-13). Ditegakkan pada
tipenya, bukan pada kehati-hatian penulis: pesan yang melanggar ditolak saat
dibentuk.

Menyembunyikan dari pengguna bukan berarti membuang. Sebab asli tetap
tersimpan dan tersedia untuk log operasional, yang menurut AP-04 pada
`docs/D04.md` terpisah dari telemetri penelitian.
"""

from __future__ import annotations

import re
import uuid
from enum import Enum
from typing import Final

from pydantic import BaseModel, field_validator

BATAS_KATA: Final = 20

KODE_GALAT_D14: Final[frozenset[str]] = frozenset(
    {
        "TIDAK_TERAUTENTIKASI",
        "TIDAK_BERWENANG",
        "VALIDASI_GAGAL",
        "SUMBER_TIDAK_ADA",
        "PAGU_TERLAMPAUI",
        "LAYANAN_MODEL_GAGAL",
        "GALAT_INTERNAL",
    }
)

_PEMISAH_KALIMAT = re.compile(r"[.!?]+")


class KodeGalat(Enum):
    """Kode galat `docs/D14.md` Bagian 4.2. Daftar tertutup (C-20, AG-04)."""

    TIDAK_TERAUTENTIKASI = "TIDAK_TERAUTENTIKASI"
    TIDAK_BERWENANG = "TIDAK_BERWENANG"
    VALIDASI_GAGAL = "VALIDASI_GAGAL"
    SUMBER_TIDAK_ADA = "SUMBER_TIDAK_ADA"
    PAGU_TERLAMPAUI = "PAGU_TERLAMPAUI"
    LAYANAN_MODEL_GAGAL = "LAYANAN_MODEL_GAGAL"
    GALAT_INTERNAL = "GALAT_INTERNAL"


def kalimat_terlalu_panjang(teks: str, batas: int = BATAS_KATA) -> list[str]:
    """Kalimat yang melebihi batas kata — C-13, NFR-19."""
    return [
        kalimat.strip()
        for kalimat in _PEMISAH_KALIMAT.split(teks)
        if kalimat.strip() and len(kalimat.split()) > batas
    ]


class Galat(BaseModel, frozen=True, extra="forbid"):
    """Isi galat sesuai `docs/D14.md` Bagian 4.2."""

    kode: KodeGalat
    pesan_pengguna: str
    id_jejak: str

    @field_validator("pesan_pengguna")
    @classmethod
    def _memenuhi_keterbacaan(cls, nilai: str) -> str:
        panjang = kalimat_terlalu_panjang(nilai)
        if panjang:
            raise ValueError(f"kalimat melebihi {BATAS_KATA} kata (C-13, NFR-19): {panjang}")
        return nilai


class TanggapanGalat(BaseModel, frozen=True, extra="forbid"):
    """Pembungkus luar `{"galat": {...}}` sesuai `docs/D14.md` Bagian 4.2."""

    galat: Galat

    @classmethod
    def susun(cls, kode: KodeGalat, pesan_pengguna: str, id_jejak: str) -> TanggapanGalat:
        return cls(galat=Galat(kode=kode, pesan_pengguna=pesan_pengguna, id_jejak=id_jejak))


class GalatLayananModel(Exception):
    """Penyedia model tidak merespons — R-09.

    Sebab asli disimpan untuk log; ia tidak pernah masuk tanggapan.
    """

    PESAN_PENGGUNA: Final = "Layanan sedang tidak dapat dihubungi. Yang Anda ketik sudah tersimpan."

    def __init__(self, sebab: Exception) -> None:
        super().__init__(self.PESAN_PENGGUNA)
        self.sebab = sebab
        self.id_jejak = f"trc_{uuid.uuid4().hex[:12]}"

    def tanggapan(self) -> TanggapanGalat:
        """Bentuk yang aman ditampilkan kepada pengguna."""
        return TanggapanGalat.susun(
            KodeGalat.LAYANAN_MODEL_GAGAL, self.PESAN_PENGGUNA, self.id_jejak
        )

    def untuk_log(self) -> str:
        """Rincian teknis — hanya ke log operasional, tidak pernah ke tanggapan."""
        return f"{self.id_jejak} {type(self.sebab).__name__}: {self.sebab}"
