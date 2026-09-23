"""Kredensial akses penyimpanan — R-01, R-01a, R-01b, C-03, C-05, ADR-06.

Kredensial menyatakan **kemampuan**, bukan identitas. Ia tidak menyimpan
"siapa" melainkan "boleh membaca area apa, boleh menulis area apa", sehingga
pemeriksaannya menjadi perbandingan himpunan alih-alih penafsiran peran — dan
yang dapat diuji adalah yang tidak menafsirkan.

Dua sifat dijaga di sini karena keduanya tempat C-03 paling mudah runtuh tanpa
terlihat:

- **Beku setelah dibentuk.** Kredensial yang dapat disunting saat jalan bukan
  pemisahan melainkan penanda, dan penanda itulah yang ADR-06 tolak.
- **Himpunan kosong berarti tidak boleh apa pun.** Kekeliruan sebaliknya adalah
  cara paling sunyi meruntuhkan C-03: kredensial yang lupa diisi akan
  menjangkau seluruh area, dan tidak ada uji yang gagal karenanya.

Himpunannya `frozenset`, bukan `set`. Objek beku yang memuat himpunan yang
dapat ditambah anggotanya tidak beku dalam arti yang berguna.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.area import Area


class Kredensial(BaseModel):
    """Kemampuan sebuah jalur layanan terhadap penyimpanan.

    Dibentuk hanya pada `src/penyimpanan/`. Cara yang sama dengan `Instruksi`
    pada ADR-13, dan alasannya sama: kemampuan yang dapat disusun di mana saja
    adalah kemampuan yang tidak dapat dijaga di mana pun.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    nama: str = Field(min_length=1)
    baca: frozenset[Area]
    tulis: frozenset[Area]
    indeks: frozenset[IndeksTujuan]
    """Indeks yang boleh dibaca — C-02, FR-D06.

    Wajib seperti `baca` dan `tulis`, bukan bernilai bawaan. Bidang berbawaan
    di sini akan diisi diam-diam oleh kredensial keempat yang ditambahkan
    kelak, dan yang paling mungkin terjadi adalah ia mewarisi bawaan yang
    longgar tanpa seorang pun memutuskannya.
    """

    tulis_indeks: frozenset[IndeksTujuan]
    """Indeks yang boleh **ditulis** — TK-62, C-02, C-17.

    Terpisah dari `indeks`, dan pemisahan itu bukan kerapian. `indeks`
    menyatakan apa yang boleh **dibaca**; jalur penjawaban menjangkau keduanya
    untuk dibaca. Menyamakan keduanya akan memberi jalur penjawaban hak tulis
    lewat pintu belakang, tanpa satu baris pun yang menyatakannya — dan C-17
    bersandar tepat pada perbedaan itu.

    Wajib, sama dengan `indeks`, dan dengan alasan yang sama: bidang berbawaan
    akan diisi diam-diam oleh kredensial berikutnya dan mewarisi bawaan yang
    longgar tanpa seorang pun memutuskannya.

    Ketiga kredensial yang mendahului bidang ini memperoleh himpunan kosong —
    sehingga ketiadaan hak tulis indeks kini **dinyatakan** alih-alih terjadi
    karena tidak ada cara menyebutnya. Ketiadaan yang dinyatakan dapat diuji.
    """

    def boleh_baca(self, area: Area) -> bool:
        return area in self.baca

    def boleh_tulis(self, area: Area) -> bool:
        return area in self.tulis

    def boleh_baca_indeks(self, indeks: IndeksTujuan) -> bool:
        """Apakah kredensial ini menjangkau sebuah indeks — C-02.

        Pemisahan pada kredensial, bukan penyaringan saat kueri. Yang tidak
        dijangkau kredensial tidak dapat dibaca oleh kekeliruan kueri mana pun.
        """
        return indeks in self.indeks

    def boleh_tulis_indeks(self, indeks: IndeksTujuan) -> bool:
        """Apakah kredensial ini boleh menulis ke sebuah indeks — TK-62.

        Dipakai jalur penyematan sebelum menyentuh satu baris pun, bentuk yang
        sama dengan `ambil_hibrida`: menyaring sesudah kueri berjalan
        menghasilkan hasil yang sama sambil barisnya sudah tersentuh.
        """
        return indeks in self.tulis_indeks
