"""Catatan percobaan akses yang ditolak — R-02, R-12, C-03, AP-04.

R-02 menuntut percobaan dicatat, bukan sekadar ditolak. Penolakan tanpa catatan
membuat percobaan berulang tidak terlihat, dan percobaan berulang adalah
satu-satunya tanda yang tersedia bahwa ada jalur yang salah arah.

**Yang dicatat adalah percobaannya, bukan sasarannya.** Id dokumen pada catatan
akses menghasilkan daftar dokumen karantina bagi siapa pun yang dapat membaca
catatan — kebocoran yang sama dengan yang urutan pemeriksaan pada `tiruan.py`
tutup, lewat pintu belakang. Karena itu `Baris` tidak memiliki bidang untuk id
dokumen sama sekali: yang tidak dapat dinyatakan tidak dapat bocor.

**Hanya penolakan yang dicatat.** Mencatat seluruh pembacaan korpus
menghasilkan jejak perilaku pengguna, dan jejak perilaku tunduk C-04 serta
milik telemetri penelitian — bukan milik lapisan penyimpanan. AP-04 pada
`docs/D04.md` memisahkan log operasional dari telemetri penelitian, dan
pemisahan itu dimulai dari tidak mencampurnya sejak awal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.penyimpanan.area import Area


@dataclass(frozen=True)
class Baris:
    """Satu percobaan akses yang ditolak.

    Tidak memiliki bidang id dokumen maupun isi. Itu bukan kelalaian melainkan
    bentuk kendalinya (R-12).
    """

    kredensial: str
    operasi: str
    area: Area
    waktu: datetime


class CatatanAkses:
    """Tambah saja. Catatan yang dapat disunting bukan bukti."""

    def __init__(self) -> None:
        self._baris: list[Baris] = []

    def catat(self, kredensial: str, operasi: str, area: Area) -> None:
        """Satu baris per percobaan.

        Tidak diringkas menjadi satu baris berhitung: meringkasnya menghapus
        waktu, dan waktu yang membedakan percobaan iseng dari percobaan
        berulang.
        """
        self._baris.append(
            Baris(kredensial=kredensial, operasi=operasi, area=area, waktu=datetime.now(UTC))
        )

    def baris(self) -> list[Baris]:
        """Salinan, bukan daftar aslinya.

        Pemanggil yang menerima daftar aslinya dapat mengosongkannya, dan
        catatan yang dapat dikosongkan dari luar tidak menjaga apa pun.
        """
        return list(self._baris)
