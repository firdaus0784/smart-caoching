"""Prioritas manajerial — R-03, R-04, FR-A03, D-04 Bagian 7.1.

FR-A03: pengguna menetapkan **3 sampai 5** prioritas manajerial *"yang menjadi
dasar penyaringan konten"*. Kalimat terakhir itu yang membuat modul ini penting
melebihi ukurannya — prioritas adalah masukan bagi FR-G01, dan pipeline kurasi
fitur 010 **sudah** menyaring terhadapnya sejak sebelum modul ini ada.

## Batas atas sama mengikatnya dengan batas bawah

Batas bawah menjaga feed dari kekurangan isi. Batas atas menjaga hal yang
berbeda dan lebih mudah luput: pengguna yang memilih seluruh delapan kategori
tidak memilih apa pun, dan penyaringan yang meloloskan seluruhnya berhenti
menyaring. "Prioritas" kemudian menjadi nama bagi daftar yang tidak
membedakan.

Karena itu keduanya diuji, dan uji batas atas yang menegakkan aturannya:
implementasi yang hanya menolak kurang dari tiga tetap lulus setiap uji yang
menanyakan "apakah tiga diterima".

## Urutan dihitung dari posisi, tidak disimpan

D-04 Bagian 7.1 menyimpan `urutan` sebagai kolom pada `prioritas_manajerial`.
Di sini ia **dihitung dari posisi** pada `kategori`, dan `baris()` yang
menghasilkan bentuk kolom itu saat dibutuhkan.

Dua tempat yang menyatakan urutan yang sama dapat berselisih, dan yang
berselisih membuat "prioritas pertama" tidak terjawab. Bentuk yang sama dengan
`HasilSaring.boleh_masuk_antrean` (010) dan `HasilValidasi.tervalidasi` (008).

Urutannya **pilihan pengguna**, bukan urutan enum. Mengurutkannya ulang
diam-diam akan mengubah prioritas pertama seseorang tanpa ia tahu.

## `KategoriMasalah` dipakai ulang — pemakaian ketiga

D-04 Bagian 7.1 menulis `kategori (K1-K8)`, dan enum itu sudah mewujudkannya
sejak fitur 003. Impornya lewat tepi `pengguna → nlp` yang tertulis pada
`AGENTS.md`. Enum keempat akan mengulangi kekeliruan `IndeksTujuan` (KB-036) —
yang sudah terulang sekali lagi pada pendeteksi data pribadi, dan diperbaiki
pada tugas A-1.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.nlp.anotasi.skema import KategoriMasalah

JUMLAH_PRIORITAS_MINIMUM = 3
"""Batas bawah FR-A03, `docs/D01.md`.

Menjaga feed dari kekurangan isi: prioritas yang terlalu sempit menyisakan
sedikit butir yang cocok, dan titik kritis T5 pada D-02 mengukur akibatnya.
"""

JUMLAH_PRIORITAS_MAKSIMUM = 5
"""Batas atas FR-A03, `docs/D01.md`.

Menjaga hal yang berbeda dari batas bawah: dari delapan kategori D-03 Bagian 5,
memilih lebih dari lima berarti hampir tidak menyisihkan apa pun — dan
penyaringan yang tidak menyisihkan berhenti menjadi penyaringan.
"""


class PrioritasManajerial(BaseModel):
    """Prioritas seorang pengguna, berurutan menurut pilihannya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_pengguna: str = Field(min_length=1)
    kategori: tuple[KategoriMasalah, ...]
    """Berurutan menurut pilihan pengguna. Posisinya **adalah** urutannya."""

    @field_validator("kategori")
    @classmethod
    def _jumlah_dalam_rentang(
        cls, nilai: tuple[KategoriMasalah, ...]
    ) -> tuple[KategoriMasalah, ...]:
        """Kedua batas, dan keduanya menjaga hal yang berbeda — lihat uraian modul."""
        if not (JUMLAH_PRIORITAS_MINIMUM <= len(nilai) <= JUMLAH_PRIORITAS_MAKSIMUM):
            raise ValueError(
                f"prioritas manajerial berjumlah {JUMLAH_PRIORITAS_MINIMUM} sampai "
                f"{JUMLAH_PRIORITAS_MAKSIMUM} (FR-A03)"
            )
        return nilai

    @field_validator("kategori")
    @classmethod
    def _tanpa_kembar(cls, nilai: tuple[KategoriMasalah, ...]) -> tuple[KategoriMasalah, ...]:
        """Penjagaan tersendiri, bukan akibat penjagaan panjang.

        Tiga pilihan yang dua di antaranya sama tetap berjumlah tiga menurut
        panjangnya — dan kategori kembar berbobot dua kali pada penyaringan
        feed tanpa seorang pun memutuskannya.
        """
        if len(set(nilai)) != len(nilai):
            raise ValueError("prioritas manajerial tidak boleh memuat kategori kembar")
        return nilai

    def baris(self) -> tuple[tuple[str, KategoriMasalah, int], ...]:
        """Bentuk kolom `prioritas_manajerial` D-04 Bagian 7.1.

        `urutan` mulai dari **satu**: urutan yang mulai dari nol akan tampil
        sebagai "prioritas ke-0" pada layar, dan mikrokopi D-05 ditulis untuk
        pembaca, bukan untuk larik.
        """
        return tuple(
            (self.id_pengguna, kategori, urutan)
            for urutan, kategori in enumerate(self.kategori, start=1)
        )
