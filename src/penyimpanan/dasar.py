"""Antarmuka penyimpan — R-01, R-02, R-03, R-04, C-03, ADR-06, ADR-12.

Antarmuka ini yang menentukan apakah C-03 dapat ditegakkan sama sekali. Dua
sifat bentuknya adalah kendali, bukan sekadar rancangan:

**Kredensial wajib, bukan opsional.** Parameter berbawaan `None` akan berubah
menjadi "tanpa kredensial berarti tanpa batas" pada pemanggilan pertama yang
lupa mengisinya, dan pemanggilan yang lupa itu tidak menggagalkan uji mana pun.

**Kredensial tepat sesudah `self`.** Menempatkannya di akhir daftar parameter
membuatnya terbaca sebagai renungan belakangan, dan yang terbaca sebagai
renungan belakangan akan diperlakukan begitu.

Mengikuti ADR-12: antarmuka abstrak dengan pelaksana tiruan deterministik.
PostgreSQL adalah pekerjaan penyebaran D-09.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial


class PenyimpanDasar(ABC):
    """Kontrak akses penyimpanan. Setiap metode menuntut kredensial."""

    @abstractmethod
    def baca_dokumen(self, kredensial: Kredensial, area: Area, id_dokumen: str) -> object:
        """Baca satu dokumen dari sebuah area.

        Pelaksana wajib memeriksa kredensial **sebelum** menyentuh data.
        Memeriksa keberadaan lebih dulu membocorkan keberadaan dokumen
        karantina lewat perbedaan galat, dan itu meruntuhkan C-03 tanpa satu
        pun dokumen terbaca.
        """

    @abstractmethod
    def tulis_dokumen(
        self, kredensial: Kredensial, area: Area, id_dokumen: str, isi: object
    ) -> None:
        """Simpan satu dokumen pada sebuah area."""

    @abstractmethod
    def pindahkan(
        self, kredensial: Kredensial, id_dokumen: str, dari: Area, ke: Area, alasan: str
    ) -> None:
        """Pindahkan dokumen antar area.

        Menuntut kredensial yang boleh membaca `dari` **dan** menulis `ke`.
        Salah satu saja tidak cukup: memindahkan adalah membaca lalu menulis,
        dan memeriksa hanya sebelahnya meninggalkan separuh gerbang terbuka.
        """
