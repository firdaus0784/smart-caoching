"""Galat akses penyimpanan — R-02, R-12, C-03, C-13, `docs/D14.md` Bagian 4.2.

Galat ini menyentuh C-03 dari arah yang tidak terduga. Pesan yang menyebut area
akan memberi tahu pemanggil bahwa dokumen yang dimintanya berada di karantina,
dan keberadaan sebuah dokumen sekolah di karantina adalah keterangan yang tidak
berhak diketahui jalur penjawaban. Pemisahan kredensial yang rapat pun runtuh
bila pesan galatnya bercerita.

Bentuknya memakai `src/llm/galat.py` yang sudah ada, bukan bentuk baru. Dua
bentuk galat pada satu sistem adalah dua tempat yang harus diperbaiki setiap
kali D-14 berubah, dan yang kedua selalu tertinggal.

**Mengapa `TIDAK_BERWENANG`, bukan `SUMBER_TIDAK_ADA`.** Yang kedua
menyembunyikan lebih banyak, tetapi ia berbohong tentang sesuatu yang tidak
diperiksa: kredensial diperiksa sebelum data disentuh, sehingga penyimpan
memang tidak tahu apakah dokumen itu ada. Jawaban yang sama untuk dokumen ada
dan tidak ada sudah menutup kebocorannya tanpa perlu berbohong.
"""

from __future__ import annotations

import uuid
from typing import Final

from src.llm.galat import KodeGalat, TanggapanGalat
from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial


class GalatAksesDitolak(Exception):
    """Kredensial tidak menjangkau area yang diminta — R-02.

    Rincian teknis disimpan untuk log operasional; ia tidak pernah masuk
    tanggapan. Yang dicatat adalah **percobaannya, bukan sasarannya**: id
    dokumen pada log akses menghasilkan daftar dokumen karantina bagi siapa pun
    yang dapat membaca log (R-12).
    """

    PESAN_PENGGUNA: Final = "Anda tidak memiliki akses ke dokumen ini."

    def __init__(self, kredensial: Kredensial, area: Area, operasi: str) -> None:
        super().__init__(self.PESAN_PENGGUNA)
        self.kredensial = kredensial
        self.area = area
        self.operasi = operasi
        self.id_jejak = f"trc_{uuid.uuid4().hex[:12]}"

    def tanggapan(self) -> TanggapanGalat:
        """Bentuk yang aman ditampilkan kepada pengguna."""
        return TanggapanGalat.susun(KodeGalat.TIDAK_BERWENANG, self.PESAN_PENGGUNA, self.id_jejak)

    def untuk_log(self) -> str:
        """Rincian teknis — hanya ke log operasional, tidak pernah ke tanggapan."""
        return (
            f"{self.id_jejak} akses ditolak: kredensial={self.kredensial.nama} "
            f"operasi={self.operasi} area={self.area.value}"
        )
