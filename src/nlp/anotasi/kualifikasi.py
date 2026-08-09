"""Uji kualifikasi anotator — R-14, FR-C09, D-03 Bagian 13.

D-03 Bagian 13 menetapkan syaratnya dalam satu kalimat: 20 dokumen berkunci
jawaban yang disusun adjudikator, dan anotator lulus bila mencapai F1
pencocokan longgar ≥ 0,80 terhadap kunci **dan** Kappa kategori ≥ 0,70.
Kalimat berikutnya yang menentukan taruhannya — *"tidak ada anotasi produksi
sebelum lulus"*.

Karena itu modul ini menilai satu anotator terhadap **kunci jawaban**, bukan
dua anotator terhadap satu sama lain. Perhitungannya tetap yang sama
(`kesepakatan.f1_rentang` dan `kesepakatan.kappa_kategori`) sebab F1 dan Kappa
tidak peduli siapa yang menjadi acuan; yang berbeda adalah ambangnya, dan
`ambang.py` memisahkan keduanya.

## Tiga keadaan, bukan dua

| Keadaan | `dapat_dinilai` | `lulus` |
|---|---|---|
| Kedua ukuran terhitung dan memenuhi ambang | `True` | `True` |
| Kedua ukuran terhitung, salah satu di bawah ambang | `True` | `False` |
| **Salah satu belum terhitung, atau dokumennya kurang** | **`False`** | **`False`** |

Baris ketiga yang menjadi alasan modul ini tidak sekadar dua perbandingan.
Anotator yang tidak menandai apa pun menghasilkan Kappa yang belum terhitung;
melaporkannya "tidak lulus" menyalahkan orang atas keadaan yang mungkin
berupa berkas yang gagal termuat, dan tindak lanjutnya menjadi pendampingan
padahal yang diperlukan adalah memeriksa bahannya.

Melaporkannya "lulus" jauh lebih buruk, dan itu yang dicegah bentuknya:
**`lulus` selalu `False` ketika `dapat_dinilai` `False`.** Pembaca yang lupa
memeriksa keduanya tidak akan melepas anotator ke anotasi produksi karena
kelalaiannya. Bentuk yang sama dengan `HasilSistem` fitur 015 dan dengan
`HasilKesepakatan.memenuhi()` pada B-1 — dan alasan yang sama pula: nilai
bawaan yang aman adalah nilai bawaan yang menahan, bukan yang meloloskan.

**`lulus == False` karena itu bukan pernyataan bahwa anotatornya gagal.**
Yang menyatakan itu adalah `dapat_dinilai and not lulus`. Perbedaannya
menentukan tindakan berikutnya, dan tindakan yang keliru di sini menimpa
orang.

## Jumlah dokumen

Diperiksa, dan bukan sebagai kerapian. Anotator yang lulus atas tiga dokumen
lolos seluruh pemeriksaan ambang — angkanya benar, bahannya yang tidak cukup.
Kegagalan seperti itu tidak meninggalkan jejak pada nilai mana pun, sehingga
satu-satunya tempat ia dapat tertangkap adalah di sini.

Jumlahnya dihitung dari **kunci jawaban**, bukan dari kerja calon. Menghitung
dari kerja calon berarti calon yang melewatkan lima belas dokumen tampak
diuji atas lima dokumen dan dinilai belum dapat dinilai — padahal ia justru
sedang menunjukkan sesuatu.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.nlp.anotasi.ambang import (
    AMBANG_KUALIFIKASI_F1_LONGGAR,
    AMBANG_KUALIFIKASI_KAPPA,
    JUMLAH_DOKUMEN_KUALIFIKASI,
)
from src.nlp.anotasi.kesepakatan import HasilKesepakatan, f1_rentang, kappa_kategori
from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas


class HasilKualifikasi(BaseModel):
    """Putusan kualifikasi seorang anotator, **atau pernyataan bahwa ia belum
    dapat diputuskan.**

    `alasan` terisi hanya pada keadaan ketiga. Hasil yang membawa putusan
    sekaligus alasan tidak dapat diputuskan adalah dua cerita pada satu baris.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    f1_longgar: HasilKesepakatan
    kappa: HasilKesepakatan
    jumlah_dokumen: int = Field(ge=0)
    alasan: str = ""

    @property
    def dapat_dinilai(self) -> bool:
        """Cukupkah bahannya untuk memutuskan sama sekali."""
        return not self.alasan

    @property
    def lulus(self) -> bool:
        """**Selalu `False` ketika belum dapat dinilai** — lihat uraian modul.

        Menuntut keduanya, sesuai kata "dan" pada D-03 Bagian 13. Kata itu
        mudah berubah menjadi "atau" ketika seseorang menyusun ulang
        percabangannya, dan perubahan itu meloloskan orang yang cakap pada
        satu tugas dan tidak pada tugas lainnya.
        """
        if not self.dapat_dinilai:
            return False
        return self.f1_longgar.memenuhi(AMBANG_KUALIFIKASI_F1_LONGGAR) and self.kappa.memenuhi(
            AMBANG_KUALIFIKASI_KAPPA
        )

    @classmethod
    def dari_angka(cls, f1_longgar: float, kappa: float, jumlah_dokumen: int) -> HasilKualifikasi:
        """Bentuk hasil dari dua angka jadi — bagi uji ambang dan pelaporan ulang.

        Bukan jalan pintas kualifikasi: ia tidak menghitung apa pun, sehingga
        angka yang masuk ke sini adalah angka yang sudah dihitung
        `uji_kualifikasi` atau ditulis tangan pada uji.
        """
        return cls(
            f1_longgar=HasilKesepakatan(nilai=f1_longgar, jumlah_satuan=jumlah_dokumen),
            kappa=HasilKesepakatan(nilai=kappa, jumlah_satuan=jumlah_dokumen),
            jumlah_dokumen=jumlah_dokumen,
        )


def uji_kualifikasi(
    rentang_calon: list[RentangEntitas],
    rentang_kunci: list[RentangEntitas],
    kategori_calon: list[PutusanKategori],
    kategori_kunci: list[PutusanKategori],
) -> HasilKualifikasi:
    """Nilai seorang calon anotator terhadap kunci jawaban adjudikator.

    Empat daftar terpisah, dan itu bukan kerumitan yang dapat disederhanakan:
    menyatukan rentang dengan kategori pada satu wadah akan mengembalikan
    persis percampuran yang `rentang.py` cegah dengan memisahkan tipenya.

    Urutan argumen menempatkan calon lebih dulu pada tiap pasangan. F1 dan
    Kappa keduanya simetris, sehingga urutan tidak mengubah angkanya — tetapi
    ia mengubah cara orang membaca pemanggilannya, dan calon-lalu-kunci sejalan
    dengan cara D-03 menuliskannya.
    """
    jumlah_dokumen = len({p.id_dokumen for p in kategori_kunci})
    if jumlah_dokumen < JUMLAH_DOKUMEN_KUALIFIKASI:
        return HasilKualifikasi(
            f1_longgar=HasilKesepakatan.belum_terhitung("bahan uji kualifikasi belum lengkap"),
            kappa=HasilKesepakatan.belum_terhitung("bahan uji kualifikasi belum lengkap"),
            jumlah_dokumen=jumlah_dokumen,
            alasan=(
                f"kunci jawaban memuat {jumlah_dokumen} dokumen, "
                f"kurang dari {JUMLAH_DOKUMEN_KUALIFIKASI} yang dituntut D-03 Bagian 13 — "
                "yang perlu ditambah bahannya, bukan pendampingan anotatornya"
            ),
        )

    f1 = f1_rentang(rentang_calon, rentang_kunci).longgar
    kappa = kappa_kategori(kategori_calon, kategori_kunci)

    belum = [
        (nama, hasil.alasan)
        for nama, hasil in (("F1 longgar", f1), ("Kappa kategori", kappa))
        if not hasil.terhitung
    ]
    alasan = ""
    if belum:
        rincian = "; ".join(f"{nama}: {sebab}" for nama, sebab in belum)
        alasan = (
            f"kualifikasi belum dapat diputuskan — {rincian}. "
            "Separuh syarat bukan syarat, dan hasil yang belum dapat diputuskan "
            "tidak sama dengan hasil yang gagal"
        )

    return HasilKualifikasi(
        f1_longgar=f1, kappa=kappa, jumlah_dokumen=jumlah_dokumen, alasan=alasan
    )
