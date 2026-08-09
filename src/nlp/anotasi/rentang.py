"""Dua tipe anotasi yang tidak dapat saling menggantikan — R-05 s.d. R-08, C-10.

`RentangEntitas` dan `PutusanKategori` sengaja **tidak berbagi induk** selain
`BaseModel`, dan itu bukan kerapian melainkan penjagaan.

D-03 Bagian 11 menetapkan dua ukuran kesepakatan bagi dua jenis tugas: Cohen's
Kappa bagi klasifikasi, F1 berpasangan bagi anotasi rentang. Penolakan Kappa
bagi rentang punya alasan yang tertulis dan dua rujukan literatur — jumlah
"kesempatan" tidak terdefinisi ketika anotator menentukan sendiri di mana
rentang dimulai, sehingga peluang kesepakatan acak tidak dapat dihitung.

Menyeragamkan keduanya menjadi satu ukuran **tampak seperti kerapian**: dua
jenis tugas, satu fungsi, kode lebih pendek. Siapa pun yang merapikan modul
ini kelak akan menggodanya, dan angka yang dihasilkannya akan terlihat
meyakinkan tetapi tidak bermakna — lalu masuk naskah.

Yang mencegahnya bukan komentar melainkan **tanda tangan**: fungsi Kappa
menerima `PutusanKategori` dan tidak akan menerima `RentangEntitas` tanpa
mengubah tipenya, dan tipe yang berubah menuntut penjelasan.

Karena itu pula `PutusanKategori` tidak memiliki bidang rentang, dan
`RentangEntitas` tidak memiliki bidang kategori. Bidang yang ada akan dipakai
seseorang.

**Rentang yang tidak cocok ditolak, tidak diperbaiki** (R-06). Rentang yang
diperbaiki diam-diam menunjuk kata lain tanpa satu galat pun, dan
kekeliruannya baru terlihat ketika korpusnya sudah terbangun. Bentuk kegagalan
yang sama dengan stemming yang menimpa permukaan pada fitur 015, dan bentuk
penjagaan yang sama dengan `Token` yang menuntut panjang rentang cocok.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema


class RentangEntitas(BaseModel):
    """Satu anotasi entitas beserta tempatnya pada teks kanonik.

    `mulai` dan `akhir` adalah **indeks karakter** (C-10, D-03 Bagian 15),
    sama dengan seluruh rentang lain pada sistem ini.

    `teks_kanonik` ikut disimpan supaya rentangnya dapat diperiksa saat
    dibentuk. Memeriksa belakangan berarti ada jeda ketika rentang yang keliru
    sudah ada dan belum ketahuan.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    teks_kanonik: str = Field(min_length=1)
    mulai: int = Field(ge=0)
    akhir: int = Field(gt=0)
    label: LabelEntitas
    versi_skema: VersiSkema
    id_anotator: str = Field(min_length=1)
    teks_rentang: str = ""

    @model_validator(mode="after")
    def _rentang_cocok(self) -> RentangEntitas:
        """Tiga syarat, dan ketiganya tentang hal yang sama.

        Rentang yang terbalik, kosong, atau melampaui panjang teks sama-sama
        berarti anotasi itu tidak menunjuk apa yang dikatakannya. Yang keempat
        — `teks_rentang` yang tidak cocok — adalah bentuk yang paling
        berbahaya, sebab ia tampak lengkap.
        """
        if self.akhir <= self.mulai:
            raise ValueError("rentang anotasi wajib maju: akhir lebih besar daripada mulai")
        if self.akhir > len(self.teks_kanonik):
            raise ValueError("rentang anotasi melampaui panjang teks kanonik")

        potongan = self.teks_kanonik[self.mulai : self.akhir]
        if self.teks_rentang and self.teks_rentang != potongan:
            raise ValueError(
                "teks_rentang tidak cocok dengan potongan teks kanonik — "
                "rentang yang diperbaiki diam-diam menunjuk kata lain tanpa "
                "satu galat pun"
            )
        if not self.teks_rentang:
            object.__setattr__(self, "teks_rentang", potongan)
        return self


class PutusanKategori(BaseModel):
    """Satu putusan klasifikasi dokumen — D-03 Bagian 5.

    Sengaja **tanpa bidang rentang**. Bidang rentang di sini akan mengundang
    seseorang menghitung F1 atasnya, dan F1 atas satuan analisis yang tetap
    adalah ukuran yang salah dengan cara yang berlawanan dari Kappa atas
    rentang.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_dokumen: str = Field(min_length=1)
    kategori_utama: KategoriMasalah
    kategori_sekunder: KategoriMasalah | None = None
    versi_skema: VersiSkema
    id_anotator: str = Field(min_length=1)

    @model_validator(mode="after")
    def _kategori_tidak_berulang(self) -> PutusanKategori:
        """Dua kategori yang sama pada satu dokumen membuat dokumen itu
        terhitung dua kali pada distribusi label, dan ketidakseimbangan kelas
        yang dilaporkan FR-C07 menjadi keliru."""
        if self.kategori_sekunder is not None and self.kategori_sekunder is self.kategori_utama:
            raise ValueError("kategori sekunder tidak boleh sama dengan kategori utama")
        return self
