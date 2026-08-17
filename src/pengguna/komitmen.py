"""Komitmen penerapan — R-11 s.d. R-14, R-16; FR-H03, FR-H04, TK-51.

## Bentuknya yang menanggung buktinya

FR-H03 sebagaimana tertulis pada D-01 meminta *"satu komitmen tindakan konkret
beserta tenggat mandiri"*. Bukti yang dikutip proposal untuk membenarkannya —
Gollwitzer & Sheeran (2006), 94 studi, lebih dari 8.000 partisipan, *d* = 0,65
— berlaku bagi **niat pelaksanaan**: rencana berbentuk **jika-maka** yang
mengaitkan isyarat keadaan tertentu dengan tindakan tertentu (Gollwitzer 1999).

Komitmen konkret bertenggat **bukan** niat pelaksanaan. Modul ini karena itu
menuntut dua bidang terpisah, dan **tidak menyediakan bidang teks bebas
tunggal**. Bidang bebas akan diisi "saya akan lebih rajin memantau" — kalimat
yang tidak membawa satu pun sifat yang membuat besaran itu berlaku.

Yang dijaga di sini bukan pasal konstitusi melainkan **kesahihan bukti**. Bila
bentuknya longgar, sistemnya tetap patuh dan penelitiannya yang kehilangan
dasar: rasio penerapan — variabel hasil utama siklus 2026 — terukur atas
mekanisme yang tidak menanggung bukti yang dikutip untuk merancangnya. Dan
kekeliruannya baru terlihat pada analisis hasil, ketika angkanya mengecewakan
dan tidak seorang pun tahu sebabnya rancangan, bukan populasi.

Keputusan Gerbang 1, TK-51, KB-059. Perubahan naskah FR-H03 pada D-01 sudah
diusulkan pada `docs/D11.md` Bagian 5 dan **masih menunggu berita acara rapat**.

## `tenggat` bukan bagian rencananya

Niat pelaksanaan bersandar pada **isyarat keadaan**, bukan pada tanggal.
`tenggat` di sini hanya menentukan kapan sistem menanyakan status (FR-H04).
Menyatukan keduanya membuat penggunanya menuliskan tanggal sebagai isyarat —
dan tanggal bukan isyarat keadaan.

## Empat status, dan yang keempat menuntut alasan

D-01 FR-H04 sendiri menyebut empat. Menyatukan `BELUM` dengan `TIDAK_JADI`
menghapus perbedaan antara komitmen yang **tertunda** dan yang **dibatalkan** —
dan rasio penerapan dihitung dari perbedaan itu. Alasan wajib hanya pada
`TIDAK_JADI`: yang belum berjalan belum punya alasan, dan menuntutnya akan
membuat penggunanya mengarang.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.nlp.anonimisasi.pola import periksa_data_pribadi

PANJANG_MINIMUM_BAGIAN = 8
"""Batas bawah tiap bagian rencana, dalam aksara.

**Penetapan tim, tanpa dasar literatur** (SI-01). Tidak ada rujukan
terverifikasi yang menetapkan panjang minimum niat pelaksanaan. Prinsip yang
menopangnya, dan itu yang bertahan: isyarat atau tindakan yang muat dalam
sepatah kata bukan rencana melainkan penanda — "besok", "rapat" — dan yang
demikian tidak dapat dibedakan dari bidang yang diisi asal.
"""


class GalatKomitmen(Exception):
    """Komitmen tidak layak disimpan.

    Pesannya **tidak pernah mengutip muatan yang ditolaknya** — sama dengan
    `GalatJejak` (002), `GalatJejakKurasi` (010), dan `GalatPercakapan` (021).
    """


class StatusPenerapan(Enum):
    """Empat status FR-H04 — lihat uraian modul mengapa empat, bukan tiga."""

    SUDAH_DITERAPKAN = "sudah_diterapkan"
    SEDANG_BERJALAN = "sedang_berjalan"
    BELUM = "belum"
    TIDAK_JADI = "tidak_jadi"
    """Satu-satunya yang menuntut alasan."""


class Komitmen(BaseModel):
    """Niat pelaksanaan — **dua bidang, dan tidak ada yang ketiga bagi teks bebas**.

    Beku: komitmen yang dapat diubah setelah ditulis tidak membuktikan apa pun
    tentang apa yang sungguh direncanakan, dan justru itu yang diukur.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # Tanpa ini pydantic menyalin **nilai masukan** ke dalam pesan
        # `ValidationError`, sehingga rencana yang baru ditolak karena memuat
        # data pribadi tetap muncul lewat jalur yang bukan pesan kita sendiri.
        # Aturan lintas modul, `tests/tata_kelola/`, KB-049.
        hide_input_in_errors=True,
    )

    id_komitmen: str = Field(min_length=1)
    id_butir: str = Field(min_length=1)
    """Butir yang melahirkannya — rantai FR-G ke FR-H tidak boleh putus."""
    isyarat: str = Field(min_length=PANJANG_MINIMUM_BAGIAN)
    """**Jika** — kapan atau pada keadaan apa. Sengaja tanpa nilai bawaan."""
    tindakan: str = Field(min_length=PANJANG_MINIMUM_BAGIAN)
    """**Maka** — apa yang dilakukan. Sengaja tanpa nilai bawaan."""
    tenggat: date
    """Kapan sistem menanyakan status. Bukan bagian rencananya."""
    dibuat: datetime

    @field_validator("dibuat")
    @classmethod
    def _berzona(cls, nilai: datetime) -> datetime:
        if nilai.tzinfo is None:
            raise ValueError("waktu wajib berzona UTC")
        return nilai

    @field_validator("isyarat", "tindakan")
    @classmethod
    def _tanpa_data_pribadi(cls, nilai: str) -> str:
        """KM-03 — **tolak, jangan saring.**

        Rencana sungguhan kepala sekolah menyebut orang; menyaringnya diam-diam
        menghasilkan baris yang tampak bersih sementara penulisnya tidak pernah
        tahu ia hampir membocorkan sesuatu.
        """
        temuan = periksa_data_pribadi(nilai)
        if temuan:
            raise ValueError(
                f"rencana memuat pengenal berjenis {temuan[0].jenis} — sebutkan "
                "jenis temuannya, jangan salin nilainya"
            )
        return nilai


class Penerapan(BaseModel):
    """Jawaban atas pertanyaan tenggat — FR-H04."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    id_komitmen: str = Field(min_length=1)
    status: StatusPenerapan
    alasan: str = ""
    """Wajib **hanya** pada `TIDAK_JADI` — lihat uraian modul."""
    waktu: datetime

    @field_validator("alasan")
    @classmethod
    def _alasan_tanpa_data_pribadi(cls, nilai: str) -> str:
        temuan = periksa_data_pribadi(nilai)
        if temuan:
            raise ValueError(
                f"alasan memuat pengenal berjenis {temuan[0].jenis} — sebutkan "
                "jenis temuannya, jangan salin nilainya"
            )
        return nilai

    @field_validator("waktu")
    @classmethod
    def _berzona(cls, nilai: datetime) -> datetime:
        if nilai.tzinfo is None:
            raise ValueError("waktu wajib berzona UTC")
        return nilai


def catat_penerapan(
    *, id_komitmen: str, status: StatusPenerapan, waktu: datetime, alasan: str = ""
) -> Penerapan:
    """Bentuk satu jawaban penerapan — R-14.

    Aturan "alasan wajib pada `TIDAK_JADI`" ditegakkan **di sini**, bukan pada
    `Penerapan`, justru agar ia satu tempat: penjagaan yang tersebar pada model
    dan pemanggil akan berbeda pada hari salah satunya diubah.
    """
    bersih = alasan.strip()
    if status is StatusPenerapan.TIDAK_JADI and not bersih:
        raise GalatKomitmen(
            "komitmen yang dibatalkan wajib menyertakan alasannya — tanpa itu "
            "rasio penerapan tidak dapat dibedakan dari kegagalan sistem (FR-H04)"
        )
    if status is not StatusPenerapan.TIDAK_JADI and bersih:
        raise GalatKomitmen(
            "alasan hanya diminta ketika komitmen dibatalkan — bidang yang terisi "
            "tanpa sebab akan diabaikan pembacanya, dan yang diabaikan tidak "
            "menjaga apa pun ketika ia sungguh perlu"
        )
    try:
        return Penerapan(id_komitmen=id_komitmen, status=status, alasan=bersih, waktu=waktu)
    except ValidationError as sebab:
        # Rantai sebabnya diputus: `ValidationError` pydantic membawa keterangan
        # tentang muatan yang baru ditolak (KB-049).
        raise GalatKomitmen(_pesan(sebab)) from None


def susun_komitmen(
    *,
    id_komitmen: str,
    id_butir: str,
    isyarat: str,
    tindakan: str,
    tenggat: date,
    dibuat: datetime,
) -> Komitmen:
    """Bentuk satu niat pelaksanaan — R-11.

    Galatnya diseragamkan menjadi `GalatKomitmen` agar pemanggil tidak perlu
    mengenal pydantic, dan agar muatan yang ditolak tidak ikut pada jejaknya.
    """
    try:
        return Komitmen(
            id_komitmen=id_komitmen,
            id_butir=id_butir,
            isyarat=isyarat,
            tindakan=tindakan,
            tenggat=tenggat,
            dibuat=dibuat,
        )
    except ValidationError as sebab:
        raise GalatKomitmen(_pesan(sebab)) from None


def _pesan(sebab: ValidationError) -> str:
    """Sebutkan jenis kekeliruannya tanpa mengulang muatannya.

    Penolakan KM-03 tidak boleh membawa keterangan apa pun tentang isinya;
    penolakan bentuk justru wajib menyebut apa yang kurang, sebab pesan yang
    tidak menyebutnya membuat pemanggil menebak.
    """
    teks = str(sebab)
    if "pengenal berjenis" in teks:
        jenis = teks.split("pengenal berjenis", 1)[1].split(" —", 1)[0].strip()
        return f"rencana memuat pengenal berjenis {jenis} dan tidak disimpan"
    if "waktu wajib berzona UTC" in teks:
        return "waktu wajib berzona UTC"
    return (
        "rencana belum lengkap — niat pelaksanaan menuntut isyarat keadaan "
        "dan tindakan, keduanya terisi"
    )
