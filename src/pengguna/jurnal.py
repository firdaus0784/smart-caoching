"""Jurnal belajar — R-15, R-18; FR-H06, FR-H07, C-15.

FR-H06: *"Sistem menampilkan 'jurnal belajar' pribadi berisi rekapitulasi: apa
yang dipelajari, apa yang dipahami, apa yang diterapkan."* Tiga bagian, dan
ketiganya berasal dari tempat yang berbeda.

## Tiga bagian, bukan satu angka

| Bagian | Asalnya | Menjawab |
|---|---|---|
| Dipelajari | butir yang dibuka | apa yang dibaca |
| Dipahami | jawaban *knowledge check* | apa yang tinggal setelah membaca |
| Diterapkan | komitmen beserta statusnya | apa yang berubah di sekolahnya |

Meringkasnya menjadi satu angka kemajuan adalah cara paling cepat jurnal ini
berubah menjadi papan skor — dan `constitution.md` C-15 melarangnya *"kosong
pun tidak"*. Ketiganya karena itu berdiri sebagai tiga daftar, dan modul ini
**tidak menyediakan** satu pun bidang bertipe angka yang menjumlahkan
seluruhnya.

## Yang sengaja tidak ada, dan mengapa justru di sini

Jurnal berisi rekapitulasi adalah tempat lencana terasa **paling wajar**: ia
sudah menghitung, sudah berurut waktu, dan sudah menjadi milik satu orang.
Fitur inilah yang paling mengundang pelanggaran C-15, dan itu sebabnya
ketiadaannya diuji di sini alih-alih dianggap sudah aman.

Tidak ada `poin`, `lencana`, `peringkat`, `runtun`, maupun `skor`. D-01 Bagian
4.2 menempatkan gamifikasi di luar siklus 2026, dan D-04 Bagian 9 melarang
tabelnya dibuat.

## Ekspor PDF dinyatakan tertahan, bukan dilewatkan

FR-H07 menuntut ekspor PDF sebagai bukti pengembangan keprofesian
berkelanjutan. Ia menuntut ketergantungan yang belum melewati C-12.
`pdf_tertahan()` **dapat dipanggil** dan mengembalikan alasannya — mengikuti
`parquet_tertahan()` fitur 012. Fungsi yang tidak ada terbaca sebagai fitur
yang tidak pernah diminta; alasan yang dapat dipanggil terbaca sebagai utang
yang dapat ditagih.

## Batas yang diakui terbuka

Di memori. Penyimpanan tetapnya menunggu penggerak PostgreSQL (C-12), sama
dengan `JejakKurasi` (010), `Percakapan` (021), dan komitmen.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.pengguna.komitmen import Komitmen, Penerapan, StatusPenerapan

ALASAN_PDF_TERTAHAN = (
    "ekspor PDF menunggu persetujuan ketergantungan pada rapat C-12; "
    "FR-H07 belum dapat dipenuhi dan itu dinyatakan, bukan dilewatkan"
)


class ButirDipelajari(BaseModel):
    """Satu butir yang dibuka pengguna — bagian pertama FR-H06."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_butir: str = Field(min_length=1)
    judul: str = Field(min_length=1)
    dibuka: datetime

    @field_validator("dibuka")
    @classmethod
    def _berzona(cls, nilai: datetime) -> datetime:
        if nilai.tzinfo is None:
            raise ValueError("waktu wajib berzona UTC")
        return nilai


class PemahamanTercatat(BaseModel):
    """Hasil satu *knowledge check* — bagian kedua FR-H06.

    Menyimpan **benar berapa dari berapa**, bukan nilai. Nilai mengundang
    perbandingan antarpengguna, dan perbandingan antarpengguna adalah papan
    peringkat yang belum diberi nama (C-15).

    Dasarnya Roediger & Karpicke (2006): yang bekerja adalah pengambilan
    kembali dari ingatan, bukan pengujiannya sebagai penilaian. Angka di sini
    ada untuk penggunanya sendiri melihat apa yang belum tersangkut.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_butir: str = Field(min_length=1)
    benar: int = Field(ge=0)
    jumlah_pertanyaan: int = Field(gt=0)
    dijawab: datetime

    @field_validator("dijawab")
    @classmethod
    def _berzona(cls, nilai: datetime) -> datetime:
        if nilai.tzinfo is None:
            raise ValueError("waktu wajib berzona UTC")
        return nilai


class BarisPenerapan(BaseModel):
    """Satu komitmen beserta jawaban terakhirnya — bagian ketiga FR-H06.

    `jawaban` boleh `None`: komitmen yang tenggatnya belum tiba belum punya
    status, dan **sistem tidak menyimpulkannya sendiri**. Status yang
    disimpulkan adalah data perilaku yang tidak pernah dilaporkan siapa pun,
    dan ia masuk ke rasio penerapan sebagai fakta.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    komitmen: Komitmen
    jawaban: Penerapan | None = None

    @property
    def status(self) -> StatusPenerapan | None:
        return None if self.jawaban is None else self.jawaban.status


class Jurnal(BaseModel):
    """Ketiga bagian FR-H06 — dan tidak ada yang keempat.

    Sengaja **tanpa** bidang ringkasan berupa angka. Satu angka kemajuan adalah
    papan skor yang belum diberi nama, dan C-15 melarangnya membuatnya "kosong
    pun tidak".
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    dipelajari: tuple[ButirDipelajari, ...] = ()
    dipahami: tuple[PemahamanTercatat, ...] = ()
    diterapkan: tuple[BarisPenerapan, ...] = ()

    def jumlah_menurut_status(self) -> dict[StatusPenerapan, int]:
        """Cacah komitmen per status — bahan rasio penerapan D-08.

        Berkunci `StatusPenerapan`, bukan berupa daftar berurut: kunci yang
        hilang adalah status yang tidak dihitung, dan itu terlihat. Komitmen
        yang belum dijawab **tidak dihitung pada status mana pun** — memasukkan
        yang belum dijawab ke `BELUM` menyamakan "belum ditanya" dengan "sudah
        ditanya dan belum dikerjakan", dan keduanya menuntut tindakan berbeda.
        """
        cacah = dict.fromkeys(StatusPenerapan, 0)
        for baris in self.diterapkan:
            if baris.status is not None:
                cacah[baris.status] += 1
        return cacah

    def belum_dijawab(self, sampai: date) -> tuple[Komitmen, ...]:
        """Komitmen bertenggat yang sudah lewat dan belum dijawab — FR-H04.

        `sampai` diserahkan pemanggil, bukan dibaca dari jam sistem. Fungsi
        yang membaca jamnya sendiri tidak dapat diuji tanpa membekukan waktu,
        dan yang tidak dapat diuji akan dipercaya begitu saja.
        """
        return tuple(
            baris.komitmen
            for baris in self.diterapkan
            if baris.jawaban is None and baris.komitmen.tenggat <= sampai
        )


def pdf_tertahan() -> str:
    """FR-H07 — alasan yang dapat dipanggil, bukan fitur yang hilang.

    Lihat uraian modul. Bentuk yang sama dengan `parquet_tertahan()` (012).
    """
    return ALASAN_PDF_TERTAHAN
