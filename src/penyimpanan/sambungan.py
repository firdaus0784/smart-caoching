"""Konfigurasi sambungan basis data — R-05, C-05, Keputusan Gerbang 1 nomor 1.

Gerbang 1 fitur 024 memutuskan **satu peladen PostgreSQL, dua basis data**:
satu bagi data perilaku dan korpus, satu bagi kunci pemetaan pseudonim.

C-05 berbunyi: *"Kunci pemetaan pseudonim tidak berada pada basis data yang
sama dengan data perilaku, dan tidak terjangkau dari layanan aplikasi."*

## Dua tipe, bukan dua nilai

Keterpisahan itu diwujudkan **dua tipe konfigurasi yang berbeda**. Bentuk yang
sama dengan `KredensialPseudonim` pada fitur 002, dan alasannya sejajar:

- **Nilai lain pada tipe yang sama** dijaga pemeriksaan saat jalan, dan
  pemeriksaan yang lupa dipanggil tidak menghasilkan galat apa pun.
- **Tipe berbeda** tidak dapat dipakaikan oleh kekeliruan pengetikan mana pun.
  Yang tidak cocok tipenya tidak sampai ke pemeriksaan.

Keduanya sengaja **tidak** mewarisi induk bersama. Induk bersama akan
mengundang seseorang menuliskan fungsi yang menerima keduanya, dan fungsi
semacam itu adalah tempat C-05 runtuh tanpa terlihat. Kesamaan bidangnya
disalin dengan sadar; keseragaman yang dicapai lewat pewarisan di sini akan
membeli kerapian dengan menjual pemisahannya.

## Yang tipe tidak dapat jaga, dan karena itu diperiksa

Tipe menjaga *sambungan mana memakai konfigurasi mana*. Ia tidak dapat menjaga
*kedua konfigurasi menunjuk basis data yang berlainan* — dua nilai untai yang
kebetulan sama terbaca sah oleh pemeriksa tipe mana pun.

`periksa_keterpisahan` menutup celah itu, dan ia memeriksa **dua** hal: nama
basis data berbeda, dan nama pengguna berbeda. Basis data terpisah dengan
pengguna yang sama adalah keterpisahan yang dapat ditembus satu pernyataan hak
akses — Keputusan Gerbang 1 nomor 2 menuntut keduanya, bukan salah satu.

## Sandi bukan bidang di sini

Sandi dibaca lingkungan pada saat menyambung, bukan disimpan pada objek yang
punya `__repr__` dan dapat tercetak ke log. V-06 melarang rahasia pada
repositori; bidang sandi pada model adalah cara paling mudah larangan itu
dilanggar tanpa ada yang menuliskannya ke berkas.

## Modul ini tidak membaca lingkungan

R-06: pemanggil yang memilih pelaksana dan menyusun konfigurasinya. Konfigurasi
yang membaca lingkungan sendiri memilih untuk pemanggilnya, dan pilihan yang
tersembunyi di dalam pustaka adalah pilihan yang tidak dapat diuji pemanggil.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

PORTA_BAKU: Final = 5432
"""Porta lazim PostgreSQL. Nilai bawaan bagi kenyamanan, bukan ketentuan."""


class KonfigurasiPerilaku(BaseModel):
    """Sambungan bagi data perilaku dan korpus.

    Beku dan tertutup: konfigurasi yang dapat disunting saat jalan bukan
    pemisahan melainkan penanda.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    peladen: str = Field(min_length=1)
    porta: int = Field(default=PORTA_BAKU, gt=0, lt=65536)
    basis_data: str = Field(min_length=1)
    pengguna: str = Field(min_length=1)


class KonfigurasiPseudonim(BaseModel):
    """Sambungan bagi peta pseudonim — **tipe tersendiri**.

    Sengaja tidak mewarisi maupun menyerupai `KonfigurasiPerilaku`. Lihat
    uraian modul: induk bersama membeli kerapian dengan menjual pemisahan.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    peladen: str = Field(min_length=1)
    porta: int = Field(default=PORTA_BAKU, gt=0, lt=65536)
    basis_data: str = Field(min_length=1)
    pengguna: str = Field(min_length=1)


class Sambungan(BaseModel):
    """Keterangan sambungan yang siap dipakai pelaksana.

    Membawa asal konfigurasinya pada `peran` agar catatan akses dan pesan galat
    dapat menyebut sambungan mana yang dipakai tanpa membaca isinya.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    peran: str = Field(min_length=1)
    peladen: str
    porta: int
    basis_data: str
    pengguna: str


def sambungan_perilaku(konfigurasi: KonfigurasiPerilaku) -> Sambungan:
    """Susun sambungan data perilaku. Menolak konfigurasi pseudonim."""
    if not isinstance(konfigurasi, KonfigurasiPerilaku):
        raise TypeError(
            f"sambungan_perilaku menuntut KonfigurasiPerilaku; diberi {type(konfigurasi).__name__}"
        )
    return Sambungan(
        peran="perilaku",
        peladen=konfigurasi.peladen,
        porta=konfigurasi.porta,
        basis_data=konfigurasi.basis_data,
        pengguna=konfigurasi.pengguna,
    )


def sambungan_pseudonim(konfigurasi: KonfigurasiPseudonim) -> Sambungan:
    """Susun sambungan peta pseudonim. Menolak konfigurasi perilaku."""
    if not isinstance(konfigurasi, KonfigurasiPseudonim):
        raise TypeError(
            "sambungan_pseudonim menuntut KonfigurasiPseudonim; "
            f"diberi {type(konfigurasi).__name__}"
        )
    return Sambungan(
        peran="pseudonim",
        peladen=konfigurasi.peladen,
        porta=konfigurasi.porta,
        basis_data=konfigurasi.basis_data,
        pengguna=konfigurasi.pengguna,
    )


def periksa_keterpisahan(perilaku: KonfigurasiPerilaku, pseudonim: KonfigurasiPseudonim) -> None:
    """Tegakkan C-05 pada nilai yang tipe tidak dapat bedakan.

    Dipanggil pemanggil ketika menyusun kedua sambungan, bukan di dalam
    penyusunnya: penyusun hanya melihat satu konfigurasi dan **tidak dapat**
    membandingkannya dengan yang lain.
    """
    if perilaku.basis_data == pseudonim.basis_data:
        raise ValueError(
            "kedua sambungan menunjuk basis data yang sama "
            f"({perilaku.basis_data!r}) — C-05 menuntut keduanya terpisah"
        )
    if perilaku.pengguna == pseudonim.pengguna:
        raise ValueError(
            "kedua sambungan memakai pengguna basis data yang sama "
            f"({perilaku.pengguna!r}) — keterpisahan yang dapat ditembus satu "
            "pernyataan hak akses bukan keterpisahan"
        )
