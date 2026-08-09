"""Antarmuka ekstraksi dan teks kanonik — R-01, R-02, R-03, C-10, ADR-12.

Ada **tiga** bentuk teks pada fitur ini, dan menukarnya adalah cara paling
mudah membatalkan C-10:

| Bentuk | Milik | Indeks karakter |
|---|---|---|
| Berkas asli | `src/penyimpanan/` | — |
| **Teks kanonik** — modul ini | `src/ingest/` | **rujukan tunggal** |
| Keluaran praproses | `src/nlp/` | menunjuk ke teks kanonik |

`TeksKanonik` sengaja **bukan** turunan `str`. Bila ia mewarisi `str`, seluruh
kode di hilir dapat memperlakukannya sebagai untai biasa dan kedua penjagaan
di bawah menguap tanpa satu baris pun berubah.

**Isi kosong ditolak pada tingkat tipe.** Ini penjagaan terpenting modul:
dokumen berteks kosong lolos seluruh gerbang fitur 002 tanpa satu pun berbunyi
— tidak ada pola instruksi adversarial pada teks kosong, dan tidak ada data
pribadi pada teks kosong. Berkas rusak yang diam-diam menjadi untai kosong
karena itu bukan sekadar kehilangan isi; ia dokumen yang menyusup lewat pintu
depan dengan seluruh lampu hijau menyala.

Menolaknya di sini, bukan pada tiap pengekstrak, berarti pengekstrak yang
penulisnya lupa memeriksa **tidak dapat** menghasilkannya.

**Isi tidak dipangkas.** Yang kosong ditolak; yang berisi diterima apa adanya.
Memangkas ruang kosong di awal akan menggeser indeks karakter setiap temuan
sesudahnya, dan C-10 menjadikan pergeseran itu kesalahan diam yang baru
terlihat pada tahap anotasi.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TeksKanonik(BaseModel):
    """Hasil ekstraksi — satu-satunya rujukan indeks karakter.

    `asal` dan `pengekstrak` wajib: C-09 menuntut keluaran dapat ditelusuri ke
    penghasilnya, dan teks tanpa keterangan asal tidak dapat diperiksa ulang
    oleh siapa pun.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    isi: str
    asal: str = Field(min_length=1)
    pengekstrak: str = Field(min_length=1)

    @field_validator("isi")
    @classmethod
    def _tidak_boleh_hampa(cls, nilai: str) -> str:
        """Untai berisi spasi sama tidak berisinya dengan untai kosong.

        Yang kedua lebih berbahaya: ia lolos pemeriksaan `if not isi` yang
        ditulis terburu, dan lolos pemeriksaan panjang pun.
        """
        if not nilai.strip():
            raise ValueError("teks hasil ekstraksi tidak boleh kosong")
        return nilai

    def __len__(self) -> int:
        """Panjang isinya, dalam **karakter** — bukan token, bukan bita (C-10)."""
        return len(self.isi)


class Pengekstrak(ABC):
    """Satu berkas masuk, satu `TeksKanonik` keluar — atau galat.

    Tidak ada jalan ketiga. Pengekstrak yang mengembalikan `None` atau untai
    kosong pada berkas bermasalah memindahkan keputusan ke pemanggilnya, dan
    pemanggil yang lupa memeriksanya menghasilkan dokumen kosong di korpus.

    Mengikuti ADR-12: antarmuka abstrak dengan pelaksana tiruan deterministik,
    sehingga uji perilaku tidak menuntut berkas maupun perkakas luar.
    """

    @abstractmethod
    def ekstrak(self, jalur: Path) -> TeksKanonik:
        """Ekstrak teks, atau lempar `GalatEkstraksi`.

        `jalur` bertipe `Path`, bukan untai. Jalur sebagai untai mengundang
        perakitan dengan penggabungan untai, dan itu jalan menuju pembacaan
        berkas di luar area yang dimaksud.
        """

    @abstractmethod
    def menangani(self, jalur: Path) -> bool:
        """Apakah pengekstrak ini yang berwenang atas berkas tersebut.

        Terpisah dari `ekstrak` supaya pemilihan pengekstrak dapat diuji tanpa
        membaca isi berkas, dan supaya berkas tanpa penangan menjadi keadaan
        yang terlihat alih-alih pengekstrak pertama yang kebetulan tidak gagal.
        """
