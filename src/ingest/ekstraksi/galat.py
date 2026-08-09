"""Galat ekstraksi — R-02, C-13.

Satu tipe untuk seluruh kegagalan pembacaan berkas, dengan pesan pengguna
terpisah dari uraian teknisnya. Pemisahan itu bukan kerapian: pesan yang
sama dipakai dua pembaca dengan kebutuhan berlawanan — pengembang perlu tahu
pustaka mana yang gagal, pengguna tidak boleh melihatnya sama sekali (C-13).

Kumpulan pesan pengguna disusun sekali pada B-7, bukan ditempel satu per satu
saat menulis tiap pengekstrak. Pesan yang ditulis sambil lalu adalah pesan
yang menyebut nama pustaka.
"""

from __future__ import annotations


class GalatEkstraksi(Exception):
    """Berkas tidak dapat diurai menjadi teks.

    **Selalu dilempar, tidak pernah diganti untai kosong.** Pengekstrak yang
    mengembalikan untai kosong pada berkas bermasalah menghasilkan dokumen
    yang lolos seluruh gerbang fitur 002 tanpa satu pun berbunyi.
    """

    def __init__(self, pesan_teknis: str, pesan_pengguna: str = "") -> None:
        super().__init__(pesan_teknis)
        self.pesan_pengguna = pesan_pengguna or "Berkas tidak dapat dibaca. Mohon unggah ulang."
