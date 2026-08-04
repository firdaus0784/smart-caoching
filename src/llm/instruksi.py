"""Satu-satunya tempat `Instruksi` dibentuk — ADR-13, C-18.

Memisahkan parameter instruksi dan data (R-06) tidak berarti apa-apa bila
pemanggil dapat membentuk `Instruksi` dari teks yang berasal dari luar.
Pemisahan itu baru mengikat ketika pembentukannya terkunci pada satu modul
yang **tidak memuat pembentukan untai dari masukan apa pun**.

Modul ini karena itu hanya berisi tetapan. Tidak ada rangkaian untai, tidak
ada penyusunan format, tidak ada parameter yang masuk dari luar. Bila suatu
saat instruksi perlu disusun dari bagian-bagian, penyusunannya tetap di sini
dan bahannya tetap tetapan — bukan argumen pemanggil.

**Keadaan pada fitur 001.** Instruksi penyusunan jawaban (IN-01 s.d. IN-07
pada `docs/D07.md` Bagian 5.2) belum ada; ia lahir bersama fitur 009. Yang ada
sekarang hanya satu instruksi untuk menguji jalur pembungkus, dan ia sengaja
diberi nama yang tidak dapat tertukar dengan instruksi penjawaban.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from src.llm.tipe import Instruksi


class KunciInstruksi(Enum):
    """Pengenal instruksi yang tersedia. Bukan teksnya."""

    UJI_ASAP = "uji_asap"


_TEKS: Final[dict[KunciInstruksi, str]] = {
    KunciInstruksi.UJI_ASAP: (
        "Balas dengan satu kalimat singkat. Instruksi ini hanya untuk menguji "
        "jalur pembungkus dan tidak dipakai menyusun jawaban kepada pengguna."
    ),
}


def susun(kunci: KunciInstruksi) -> Instruksi:
    """Bentuk `Instruksi` dari tetapan. Satu-satunya pintu (ADR-13)."""
    return Instruksi(teks=_TEKS[kunci])
