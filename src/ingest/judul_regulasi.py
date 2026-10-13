"""Judul regulasi bernomor dan bertahun — T-3 fitur 041, R-01, P-3 A, TK-88, D-06 K-A.

D-06 kanal K-A mewajibkan nomor dan tahun sebagai metadata regulasi, tetapi
catatan metadata tidak memiliki bidangnya. Judul menjadi tempatnya: ia ikut
dicari bersama setiap pasal (D-07 Bagian 3.3), sehingga nomor dan tahun pada
judul yang membuat pasal dapat ditemukan dengan menyebut regulasinya.

Polanya milik D-06 beserta contohnya; uji membacanya dari sana. Bentuk
singkat seperti `No. 6/2021` ditolak: pertanyaan menulis "Nomor 6 Tahun
2021", dan judul yang seragam itulah yang membuat identitas dapat dicari.
"""

from __future__ import annotations

import re
from typing import Final

POLA_JUDUL_REGULASI: Final = re.compile(r"\bnomor\s+\S+\s+tahun\s+\d{4}\b", re.IGNORECASE)
"""`Nomor`, satu nomor tanpa spasi, `Tahun`, empat angka — D-06 K-A."""


def judul_regulasi_sah(judul: str) -> bool:
    return POLA_JUDUL_REGULASI.search(judul) is not None
