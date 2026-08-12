"""Tipe pembungkus model — R-06, C-08, C-17, C-18.

`Peringkat` dan `IndeksTujuan` **tidak lagi didefinisikan di sini**; keduanya
pindah ke `src/kamus/segmen.py` pada fitur 008. Sebabnya: `IndeksTujuan`
ternyata ditulis dua kali — di sini dan pada `src/penyimpanan/indeks.py` fitur
006 — dan enum itu tempat C-02 terbaca. Nilai yang dimiliki D-14 bukan milik
pembungkus model.

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
from pydantic import BaseModel, Field

from src.kamus.segmen import IndeksTujuan, Peringkat


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
