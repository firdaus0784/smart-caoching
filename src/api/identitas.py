"""Identitas pemanggil — T-4 fitur 028, R-06, R-17, P-1, TK-67.

Sampai fitur 028 penentu identitas hanya mengembalikan **peran**. Peran cukup
bagi kendali rute, tetapi tidak bagi riwayat: tanpa tahu siapa penanyanya,
daftar percakapan hanya dapat berupa daftar seluruh percakapan (TK-67).

`Identitas` membawa **pemilik** di samping peran. Pemilik berupa pseudonim —
bentuk yang sama dengan `Peristiwa.pseudonim` fitur 012 — dan **bukan**
identitas langsung (C-05). Autentikasi (FR-A01, fitur 029) mengisi penentu
identitas dengan pseudonim akun; riwayat tidak berubah karenanya.

## Penjagaan atas pemilik

Pemilik yang berpola data pribadi — NIK, nomor telepon, dan empat pola lain
FR-B04 — ditolak saat dibentuk. Pseudonim yang ternyata NIK adalah identitas
langsung yang menyamar, dan ia akan tersimpan pada basis data perilaku.

**Batas yang diakui terbuka:** pendeteksi hanya mengenal enam pola bernomor
(catatan cakupan FR-B04, BT-70). Surel dan nama orang tidak terdeteksi.
Penjagaan ini lapisan kedua; yang pertama adalah penentu identitas yang memang
mengembalikan pseudonim.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from fastapi import Request
from pydantic import BaseModel, ConfigDict, field_validator

from src.api.peran import Peran
from src.nlp.anonimisasi.pola import periksa_data_pribadi


class Identitas(BaseModel):
    """Siapa pemanggilnya, sejauh yang boleh diketahui aplikasi."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # Tanpa ini pydantic menyalin nilai masukan ke pesan `ValidationError`,
        # sehingga pemilik yang ditolak karena berpola NIK muncul lagi lewat
        # jalur yang bukan pesan kita sendiri. Aturan `tests/tata_kelola/`, KB-049.
        hide_input_in_errors=True,
    )

    peran: Peran
    pemilik: str
    """Pseudonim pemilik riwayat — bukan id pengguna (C-05)."""

    @field_validator("pemilik")
    @classmethod
    def _pseudonim(cls, nilai: str) -> str:
        if not nilai.strip():
            raise ValueError("pemilik tidak boleh kosong")
        temuan = periksa_data_pribadi(nilai)
        if temuan:
            raise ValueError(
                f"pemilik berpola {temuan[0].jenis} — pemilik wajib pseudonim, "
                "bukan identitas langsung (C-05)"
            )
        return nilai


@runtime_checkable
class PenentuIdentitas(Protocol):
    """Pengubah permintaan menjadi identitas — satu-satunya kemampuan yang dituntut.

    `Protocol`, bukan kelas: fitur 029 mengisinya dengan `PenentuSesi` tanpa
    menyentuh riwayat.

    **`async`, dan boleh mengembalikan `None`** sejak T-5 fitur 029. Identitas
    sungguhan dibaca dari sesi di basis data; `None` berarti tidak ada sesi
    sah, dan lapisan HTTP menjawabnya 401 `TIDAK_TERAUTENTIKASI` sebelum
    membaca badan permintaan (R-05).
    """

    async def identitas(self, permintaan: Request) -> Identitas | None: ...
