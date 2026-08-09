"""Tokenisasi dan normalisasi Bahasa Indonesia — R-07, R-08, C-10.

Dua fungsi, dan keduanya tunduk pada satu aturan yang tidak dapat ditawar:
**indeks karakter pada teks kanonik tetap sah sesudah keduanya berjalan.**

`tokenkan` menghasilkan token yang masing-masing membawa rentangnya sendiri,
sehingga sifat berikut berlaku bagi setiap token:

    teks[t.mulai:t.akhir] == t.permukaan

`normalkan` **tidak boleh mengubah panjang teks**. Ini yang paling mudah
dilanggar tanpa sadar: membuang tanda baca dan merapatkan spasi ganda adalah
normalisasi yang lazim, dan keduanya menggeser setiap indeks sesudahnya.
Karena itu normalisasi di sini hanya mengubah karakter menjadi karakter —
tidak pernah menghapus, tidak pernah menambah.

Penurunan huruf besar dipakai karena `str.lower()` pada Bahasa Indonesia tidak
mengubah panjang. Bahasa lain tidak seberuntung itu — huruf Jerman ß menjadi
dua karakter pada `upper()` — dan bila kelak ada teks berbahasa lain, aturan
ini yang wajib diperiksa ulang, bukan dianggap masih berlaku.

**Kegunaannya dibatasi: keluaran praproses untuk pencarian, bukan untuk
menyiapkan bahan anotasi.** Bahan anotasi diambil dari teks kanonik dengan
rentang karakter, dan D-03 Bagian 15 sudah menetapkan alasannya. Modul ini
menyediakan bentuk dasar kata agar pengambilan menemukan "menugaskan" ketika
yang dicari "tugas"; ia tidak menghasilkan teks yang menggantikan aslinya.
"""

from __future__ import annotations

import re

from src.nlp.praproses.token import Token

_APOSTROF = "'\u2019"  # lurus dan melengkung; dokumen sekolah memakai keduanya
_KATA = re.compile(rf"\w+(?:[-{_APOSTROF}]\w+)*", re.UNICODE)
"""Kata beserta bentuk bertanda hubung dan berapostrof.

`lintas-jenjang` satu token, bukan dua: memecahnya menghasilkan dua kata yang
tidak berarti apa-apa sendiri-sendiri. Titik dan koma tidak ikut, sehingga
"kurikulum." dan "kurikulum" menjadi kata yang sama saat dicari.
"""


def normalkan(teks: str) -> str:
    """Bentuk baku teks, **dengan panjang yang persis sama** (C-10).

    Yang dilakukan hanya penurunan huruf. Menambah pembersihan apa pun di sini
    menuntut bukti bahwa panjangnya tidak berubah — dan uji sifat pada berkas
    ujinya menolak yang tidak membuktikannya.
    """
    return teks.lower()


def tokenkan(teks: str) -> list[Token]:
    """Token beserta rentang karakternya pada `teks` yang diberikan.

    `stem` diisi bentuk ternormalkan, bukan bentuk dasar — pemenggalan imbuhan
    adalah pekerjaan C-3 dan menuntut kamus. Memisahkannya menjaga modul ini
    tetap dapat diuji tanpa pustaka luar.

    Teks kosong menghasilkan daftar kosong, bukan galat. Teks kosong tidak
    dapat sampai ke sini karena `TeksKanonik` sudah menolaknya, dan melempar
    galat kedua kalinya hanya menambah jalan yang harus ditangani pemanggil.
    """
    return [
        Token(
            permukaan=cocok.group(0),
            stem=normalkan(cocok.group(0)),
            mulai=cocok.start(),
            akhir=cocok.end(),
        )
        for cocok in _KATA.finditer(teks)
    ]
