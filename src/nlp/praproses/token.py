"""Token praproses dengan rentang karakter — R-07, R-08, C-10, D-03 Bagian 15.

`Token` membawa **empat** hal, bukan tiga: permukaan asli, stem, dan rentang
karakternya pada teks kanonik. Yang keempat itu yang membuat C-10 dapat
ditegakkan sesudah praproses berjalan.

Stemming mengubah panjang kata — "menugaskan" menjadi "tugas". Token yang
hanya menyimpan stem kehilangan tempatnya pada teks asli, dan setiap rentang
anotasi yang menunjuk kepadanya menjadi salah **tanpa satu galat pun**: ia
tetap menunjuk sesuatu, hanya bukan yang dimaksud. Kesalahan semacam itu baru
terlihat pada tahap anotasi, ketika korpusnya sudah terbangun.

Rentangnya menunjuk ke **teks kanonik**, bukan ke teks hasil praproses.
Keluaran praproses tidak memiliki indeks sendiri sama sekali, dan itu
disengaja: dua sistem indeks pada satu dokumen adalah dua sistem yang akan
tertukar.

Panjang rentang wajib sama dengan panjang permukaan. Tanpa syarat itu,
rentangnya boleh berisi angka apa pun dan tetap lolos — dan yang lolos akan
memotong kalimat di tempat yang salah pada setiap pemakaian berikutnya.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Token(BaseModel):
    """Satu kata pada teks kanonik, beserta bentuk dasarnya dan tempatnya.

    `permukaan` untuk menunjuk, `stem` untuk mencari. Keduanya disimpan karena
    keduanya dipakai pihak yang berbeda: rentang anotasi memerlukan yang
    pertama, pengambilan memerlukan yang kedua.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    permukaan: str = Field(min_length=1)
    stem: str = Field(min_length=1)
    mulai: int = Field(ge=0)
    akhir: int = Field(gt=0)

    @model_validator(mode="after")
    def _rentang_masuk_akal(self) -> Token:
        """Tiga syarat sekaligus, karena ketiganya tentang hal yang sama.

        Rentang yang terbalik, kosong, atau berbeda panjang dari permukaannya
        sama-sama berarti token itu tidak menunjuk apa yang dikatakannya.
        """
        if self.akhir <= self.mulai:
            raise ValueError("rentang token wajib maju: akhir lebih besar daripada mulai")
        if self.akhir - self.mulai != len(self.permukaan):
            raise ValueError(
                "panjang rentang wajib sama dengan panjang permukaan — "
                "rentang yang berbeda panjang memotong kalimat di tempat yang salah"
            )
        return self
