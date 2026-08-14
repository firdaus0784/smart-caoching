"""Kontrak kandidat dan sumbernya — R-01, R-02, R-03, ADR-03, ADR-12.

Bentuk yang dipakai kedua sisi ADR-03. Sisi leksikal dibangun pada fitur 007;
sisi semantik pada fitur 019. Keduanya memenuhi antarmuka yang sama, dan itu
yang membuat penggabungan peringkat tidak perlu tahu asal daftar yang
digabungnya.

## Kandidat membawa `id_segmen`, bukan dokumen

D-07 Bagian 3.2 menetapkan pengambilan atas segmen. Dokumen yang dikembalikan
utuh membanjiri konteks — D-07 Bagian 9 membatasi 5-8 segmen — dan
menghilangkan penanda bagian yang FR-F11 tuntut untuk menautkan sitasi ke
pasal, bukan ke dokumen.

## Seri diputus `id_segmen`, bukan urutan sisipan

Dua segmen berskor identik bukan kasus tepi. Pada BM25, dua segmen yang memuat
kata kueri dengan frekuensi dan panjang sama menghasilkan skor yang **persis**
sama — bukan hampir sama. Mengandalkan kestabilan `sorted` berarti mengikuti
urutan sisipan, dan urutan sisipan datang dari urutan pembacaan berkas.

Hasil yang berubah karena urutan berkas adalah hasil yang tidak dapat diulang.
R-02 gugur tanpa satu galat pun, dan percobaan yang tercatat pada D-10 L1
menjadi percobaan yang tidak dapat diperiksa siapa pun.

## Peringkat dihitung dari posisi, tidak disimpan

`HasilSumber.peringkat` adalah urutan; peringkat sebuah segmen adalah tempatnya
pada urutan itu. Menyimpan nomor peringkat sebagai bidang tersendiri
menciptakan sumber kebenaran kedua bagi hal yang sama, dan yang kedua akan
berbeda ketika salah satunya disunting.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.kamus.segmen import IndeksTujuan


class Kandidat(BaseModel):
    """Satu segmen yang ditemukan sebuah sumber, beserta skornya.

    Skor bermakna **hanya di dalam sumbernya**. Skor BM25 dan skor kemiripan
    vektor tidak sebanding, dan itu justru alasan D-07 Bagian 4.4 memilih
    *Reciprocal Rank Fusion*: ia bekerja atas peringkat, bukan atas skor,
    sehingga tidak menuntut penyetelan bobot manual.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_segmen: str = Field(min_length=1)
    skor: float = Field(ge=0.0)
    """Skor tak-negatif.

    BM25 dan RRF keduanya menghasilkan nilai tak-negatif. Skor negatif berarti
    perhitungannya keliru, dan menerimanya membuat kekeliruan itu terurut
    seperti hasil yang sah — di paling bawah, tanpa ada yang melihat.
    """


def urutkan_kandidat(kandidat: Iterable[Kandidat]) -> tuple[Kandidat, ...]:
    """Urutkan menurun menurut skor; seri diputus `id_segmen` menaik (R-03).

    Satu tempat bagi aturan urutan. Setiap sumber memanggilnya, sehingga sumber
    yang ditambahkan kelak tidak memutuskan urutannya sendiri.
    """
    return tuple(sorted(kandidat, key=lambda k: (-k.skor, k.id_segmen)))


class HasilSumber(BaseModel):
    """Daftar berperingkat dari satu sumber, beserta versi indeksnya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    nama_sumber: str = Field(min_length=1)
    versi_indeks: str = Field(min_length=1)
    """Versi indeks yang melayani pencarian ini — D-07 Bagian 3.3, RT-05.

    "Setiap pembangunan ulang menghasilkan nomor versi; tercatat pada setiap
    jawaban." Tanpanya, dua percobaan atas indeks berbeda tidak dapat dibedakan
    pada catatan D-10 L1, dan perbandingan antarpercobaan menjadi perbandingan
    yang tidak diketahui apa yang berubah.
    """
    peringkat: tuple[Kandidat, ...]

    @model_validator(mode="after")
    def _tanpa_segmen_kembar(self) -> HasilSumber:
        """Satu segmen tidak boleh muncul dua kali pada satu daftar peringkat.

        Bila muncul, RRF menjumlahkan sumbangannya dua kali dari sumber yang
        **sama** — segmen itu naik seolah dua sumber menyetujuinya, padahal
        tidak ada sumber kedua. Itu membatalkan arti skor gabungan.
        """
        terlihat = [k.id_segmen for k in self.peringkat]
        if len(terlihat) != len(set(terlihat)):
            raise ValueError(
                "satu daftar peringkat memuat id_segmen kembar — penggabungan "
                "akan menjumlahkan sumbangannya dua kali dari sumber yang sama"
            )
        return self

    def peringkat_dari(self, id_segmen: str) -> int | None:
        """Peringkat sebuah segmen, dihitung dari 1; `None` bila tidak ada.

        `None`, bukan 0 dan bukan panjang daftar. Nilai angka apa pun bagi
        "tidak ditemukan" akan ikut masuk perhitungan RRF sebagai peringkat
        yang sah — dan segmen yang tidak ditemukan sebuah sumber akan menerima
        sumbangan dari sumber itu.
        """
        for urutan, kandidat in enumerate(self.peringkat, start=1):
            if kandidat.id_segmen == id_segmen:
                return urutan
        return None


class SumberKandidat(ABC):
    """Kontrak satu sisi pengambilan hibrida — ADR-03, ADR-12.

    Antarmuka abstrak dengan pelaksana tiruan deterministik, mengikuti ADR-12
    yang sudah terbukti pada fitur 002 dan 015.

    `indeks_tujuan` bukan pelengkap: penyusun hibrida memeriksanya terhadap
    kredensial **sebelum** memanggil `cari`, sehingga sumber pada indeks yang
    tidak dijangkau tidak dijalankan sama sekali. Menyaring hasilnya sesudah
    pencarian berjalan adalah penyaringan saat kueri, dan C-02 kalimat kedua
    menolaknya.
    """

    @property
    @abstractmethod
    def nama(self) -> str:
        """Nama sumber, dipakai pada daftar penyumbang hasil gabungan (R-06)."""

    @property
    @abstractmethod
    def indeks_tujuan(self) -> IndeksTujuan:
        """Indeks yang dicari sumber ini — diperiksa terhadap kredensial."""

    @property
    @abstractmethod
    def versi_indeks(self) -> str:
        """Versi indeks yang dilayani — D-07 Bagian 3.3, RT-05."""

    @abstractmethod
    def cari(self, kueri: str, *, batas: int) -> HasilSumber:
        """Cari kandidat teratas.

        `batas` **memangkas**, tidak mengisi. Kandidat yang lebih sedikit
        diteruskan seluruhnya; mengisi sampai penuh dengan segmen berskor nol
        memberi penyusun jawaban bahan yang tidak relevan, dan penilaian
        kecukupan bukti kemudian menghitung bahan itu sebagai bukti.
        """
