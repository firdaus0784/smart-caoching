"""Metadata asal dokumen — R-06, FR-B06, ET-04, D-04 Bagian 7.2.

FR-B06 menyebut lima bidang. Tiga sudah ada pada model data sejak awal; dua
sisanya — `tingkat_kerahasiaan` dan `status_persetujuan_pemilik` — tidak pernah
masuk ke sana, sehingga kebutuhan berprioritas W itu tidak dapat dipenuhi tanpa
menebak. Nilainya ditetapkan pemegang gerbang (KB-013) sebagai penetapan tim
tanpa dasar literatur, sesuai SI-01.

**Aturan etik yang ditegakkan modul ini: dokumen rahasia hanya boleh masuk
korpus atas persetujuan pemiliknya.** Itu yang memberi `tingkat_kerahasiaan`
gigi. Tanpa aturan itu ia hanya catatan yang terbaca seperti perlindungan pada
ET-05 dan pada naskah, padahal tidak menahan apa pun.

Dua sisi aturannya, dan keduanya disengaja:

- **Dokumen sekolah menuntut persetujuan pada tingkat mana pun**, termasuk
  `publik`. ET-04 berbunyi "persetujuan sekolah atas penggunaan dokumen
  manajerial untuk korpus" tanpa syarat tingkat. Tanpa ini, sebuah dokumen
  sekolah dapat ditandai `publik` untuk melewati gerbang persetujuan.
- **Regulasi publik tidak menuntutnya.** Permendikdasmen tidak punya pemilik
  yang dimintai persetujuan, dan aturan yang menuntutnya akan menghentikan
  kanal K-A seluruhnya — kendali yang menghentikan pekerjaan sah akan dimatikan
  orang.

Penarikan persetujuan berlaku seketika. Persetujuan yang tidak dapat ditarik
bukan persetujuan; FR-A05 dan NFR-09 sudah memberi hak itu kepada pengguna, dan
pemilik dokumen tidak pantas dapat kurang.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, computed_field

from src.ingest.peringkat import JenisSumber, peringkat_bagi
from src.llm.tipe import Peringkat

TAHUN_PALING_AWAL = 1945


class TingkatKerahasiaan(Enum):
    """Seberapa terbatas sebuah dokumen boleh beredar.

    Penetapan tim tanpa dasar literatur (SI-01, KB-013). Nilainya mengikuti
    `docs/D14.md` Bagian 5.1.
    """

    PUBLIK = "publik"
    INTERNAL_SEKOLAH = "internal_sekolah"
    TERBATAS = "terbatas"


class StatusAnonimisasi(Enum):
    """Hasil verifikasi anonimisasi oleh manusia — FR-B05, D-14 Bagian 5.1.

    Hanya `TERVERIFIKASI` yang boleh diindeks. Nilai awalnya `MENUNGGU`, bukan
    `TERVERIFIKASI`: dokumen yang belum diperiksa siapa pun tidak boleh
    dianggap bersih hanya karena belum ada yang menolaknya.
    """

    MENUNGGU = "menunggu"
    TERVERIFIKASI = "terverifikasi"
    DITOLAK = "ditolak"


class StatusPersetujuan(Enum):
    """Persetujuan pemilik dokumen atas pemakaiannya untuk korpus — ET-04.

    Nilai ini menyesuaikan formulir persetujuan ET-02 bila keduanya berbeda;
    formulir yang menang, dan kode yang menyusul.
    """

    BELUM_DIMINTA = "belum_diminta"
    DIBERIKAN = "diberikan"
    DITOLAK = "ditolak"
    DICABUT = "dicabut"


class Dokumen(BaseModel):
    """Metadata asal sebuah dokumen sumber.

    Beku setelah dibentuk: metadata asal yang dapat disunting membuat jejak
    asal tidak berarti.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(min_length=1)
    judul: str = Field(min_length=1)
    jenis: JenisSumber
    penerbit: str = Field(min_length=1)
    tahun: int = Field(ge=TAHUN_PALING_AWAL)
    tingkat_kerahasiaan: TingkatKerahasiaan
    status_persetujuan_pemilik: StatusPersetujuan
    status_anonimisasi: StatusAnonimisasi = StatusAnonimisasi.MENUNGGU

    @computed_field  # type: ignore[prop-decorator]
    @property
    def peringkat(self) -> Peringkat:
        """Diturunkan dari jenis, tidak diisi pemanggil.

        Peringkat yang dapat diisi pemanggil adalah peringkat yang dapat
        dinaikkan pemanggil (R-08).
        """
        return peringkat_bagi(self.jenis)

    @staticmethod
    def anonimisasi_mengizinkan_indeks(status: StatusAnonimisasi) -> bool:
        """Hanya `TERVERIFIKASI`. D-14 Bagian 5.1 menyatakannya sebagai sifat
        seluruh daftar, sehingga nilai keempat yang ditambahkan kelak tidak
        diam-diam ikut lolos."""
        return status is StatusAnonimisasi.TERVERIFIKASI

    @staticmethod
    def persetujuan_mengizinkan_korpus(status: StatusPersetujuan) -> bool:
        """Hanya `DIBERIKAN`. D-03 Bagian 3 mengeluarkan dokumen tanpa
        persetujuan pemilik dari korpus."""
        return status is StatusPersetujuan.DIBERIKAN

    def boleh_masuk_korpus(self) -> bool:
        """Dokumen rahasia hanya boleh masuk korpus atas persetujuan pemiliknya.

        Persetujuan dituntut bila salah satu berlaku: dokumen berasal dari
        sekolah, atau tingkat kerahasiaannya bukan `publik`. Keduanya diperiksa,
        bukan salah satu — dokumen sekolah yang ditandai `publik` tetap milik
        sekolah itu.

        Ini **bukan** satu-satunya gerbang menuju korpus. Verifikasi anonimisasi
        (R-04) dan pemeriksa pola adversarial (R-09) berdiri sendiri, dan
        ketiganya wajib dilewati.
        """
        menuntut_persetujuan = (
            self.jenis is JenisSumber.DOKUMEN_SEKOLAH
            or self.tingkat_kerahasiaan is not TingkatKerahasiaan.PUBLIK
        )
        if not menuntut_persetujuan:
            return True
        return self.persetujuan_mengizinkan_korpus(self.status_persetujuan_pemilik)
