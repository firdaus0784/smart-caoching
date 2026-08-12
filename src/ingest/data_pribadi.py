"""Pendeteksi bentuk baku data pribadi — R-12, R-13, C-05, KM-03.

Satu salinan, dipakai dua jejak: perpindahan area (fitur 002) dan kurasi
(fitur 010). Pola yang disalin akan berbeda dari aslinya pada hari salah
satunya diperbarui, dan yang tertinggal adalah yang menjaga jejak yang lebih
jarang dibaca. Kekeliruan `IndeksTujuan` yang ditulis dua kali dan lolos dua
fitur (KB-036) berbentuk persis seperti ini.

**Lapis ini menutup bentuk yang paling sering, bukan seluruhnya.** Pendeteksi
data pribadi yang sesungguhnya adalah FR-B04, dan ia dibangun pada fitur 015.
Modul ini tidak berpura-pura menggantikannya.

## Mengembalikan nama pola, bukan nilainya

Pemanggil perlu tahu **jenis** apa yang tersalin agar galatnya menjelaskan.
Ia tidak boleh mengulang **nilainya**: galat yang mengutip muatannya
memindahkan kebocoran dari jejak ke log, yaitu kebalikan persis dari
maksudnya.
"""

from __future__ import annotations

import re

POLA_DATA_PRIBADI: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("nomor induk berdigit panjang", re.compile(r"\b\d{16,18}\b")),
    ("nomor telepon Indonesia", re.compile(r"(?<!\d)(?:\+62|62|0)8[1-9][\d\s.-]{6,12}\d(?!\d)")),
)
"""Bentuk baku data pribadi yang paling sering tersalin ke alasan.

NIK berdigit 16 dan NIP berdigit 18, sehingga keduanya tertangkap satu pola —
memisahkannya menjadi dua pola dengan panjang persis akan meloloskan salah
ketik satu digit, dan salah ketik satu digit tetap membocorkan lima belas.

Nilai awal, bukan hasil kalibrasi. Penyetelannya mengikuti BT-29 (C-16).
"""


def nama_pola_yang_cocok(teks: str) -> str | None:
    """Nama pola pertama yang cocok, atau `None` bila bersih.

    **Tidak pernah mengembalikan nilai yang cocok** — lihat uraian modul.
    """
    for nama, pola in POLA_DATA_PRIBADI:
        if pola.search(teks):
            return nama
    return None
