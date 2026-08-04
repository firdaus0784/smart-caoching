"""Tipe pembungkus model — R-06, C-08, C-17, C-18.

Pemisahan instruksi dan data adalah wujud C-18, dan ia dimulai di sini.
`Instruksi` dan `Data` bukan dua nama untuk untai yang sama melainkan dua
tipe yang tidak dapat saling menggantikan — sehingga menempatkan konten
terambil pada posisi instruksi menjadi kekeliruan yang tertangkap saat
periksa, bukan kelalaian yang baru terlihat setelah jawaban keliru tayang.

`Data` sudah membawa `peringkat_kepercayaan` (D-13 Bagian 6) dan `indeks_asal`
(FR-D06) meskipun pengambilan belum ada pada fitur 001. Alasannya sama dengan
alasan G1-4 menempatkan gerbang lebih dulu: bila bidang itu baru ditambahkan
pada fitur 007, C-02 dan C-19 harus disisipkan ke jalur yang sudah berjalan,
dan penyisipan semacam itu selalu lebih mahal. Bidang ini **dideklarasikan,
belum ditegakkan** — C-02 dan C-19 tetap menunggu fitur 006 dan 008.

`Konfigurasi` sengaja tidak memuat parameter alat, pendaftaran fungsi, maupun
keluaran yang dapat dieksekusi. C-17 dimulai dari bentuk konfigurasinya:
kemampuan yang tidak dapat dinyatakan tidak dapat dipakai.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Peringkat(Enum):
    """Tingkat kepercayaan asal segmen — `docs/D13.md` Bagian 6.

    T3 dan T4 tidak boleh menjadi dasar tunggal sebuah klaim (C-19, FR-F15).
    """

    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"


class IndeksTujuan(Enum):
    """Indeks asal segmen — `docs/D14.md` Bagian 5, FR-D06.

    Hanya `utama` yang boleh masuk konteks LLM. `metadata` memuat abstrak
    terbitan berlisensi tertutup dan hanya muncul sebagai bacaan lanjutan.
    """

    UTAMA = "utama"
    METADATA = "metadata"


class Instruksi(BaseModel, frozen=True, extra="forbid"):
    """Perintah kepada model. Hanya dibentuk di `src/llm/instruksi.py` (ADR-13).

    Tipe ini terpisah dari `Data` bukan demi kerapian: ia yang membuat posisi
    instruksi menjadi tempat yang tidak dapat dimasuki konten terambil.
    """

    teks: str = Field(min_length=1)


class Data(BaseModel, frozen=True, extra="forbid"):
    """Segmen terambil. Tidak pernah menempati posisi instruksi (C-18)."""

    id_segmen: str = Field(min_length=1)
    teks: str
    peringkat_kepercayaan: Peringkat
    indeks_asal: IndeksTujuan


class Konfigurasi(BaseModel, frozen=True, extra="forbid"):
    """Setelan pemanggilan. Tanpa parameter alat — C-17."""

    nama_model: str = Field(min_length=1)
    versi_model: str = Field(min_length=1)
    suhu: float = Field(ge=0.0, le=2.0)
    batas_token: int = Field(gt=0)


class Tanggapan(BaseModel, frozen=True, extra="forbid"):
    """Keluaran pemanggilan beserta jejak yang diwajibkan C-08."""

    teks: str
    versi_model: str = Field(min_length=1)
    waktu_mulai: datetime
    waktu_selesai: datetime
    biaya: float = Field(ge=0.0)
    id_jejak: str = Field(min_length=1)
