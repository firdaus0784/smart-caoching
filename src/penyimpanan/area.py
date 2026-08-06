"""Area penyimpanan — R-03, ADR-06, C-03.

Dua area, dan pemisahannya bukan penanda status melainkan kredensial berbeda.
ADR-06 menolak penandaan status dengan alasan tegas: satu kekeliruan kueri
meloloskan dokumen mentah. Enum ini menamai areanya; yang menjaganya adalah
`kredensial.py` dan `dasar.py`.

Nilainya mengikuti `dokumen_sumber.area_simpan` pada `docs/D14.md` Bagian 5.1
persis, termasuk ejaannya. Menambah nilai ketiga menuntut D-14 diubah lebih
dulu — AG-04 melarang agen mengubah daftar nilai enum, dan berkas ini tempat
larangan itu paling mudah dilanggar tanpa disadari.
"""

from __future__ import annotations

from enum import Enum


class Area(Enum):
    """Tempat sebuah dokumen berada.

    `KARANTINA` menampung dokumen yang belum diverifikasi manusia (FR-B05).
    Jalur penjawaban tidak memiliki kredensial untuk membacanya — bukan tidak
    boleh, melainkan tidak bisa.
    """

    KARANTINA = "karantina"
    KORPUS = "korpus"
