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
    PENJAWABAN = "penjawaban"


_TEKS: Final[dict[KunciInstruksi, str]] = {
    # IN-01 s.d. IN-07 `docs/D07.md` Bagian 5.2, ditulis apa adanya sebagai
    # tetapan. Instruksi yang dirakit saat jalan adalah instruksi yang dapat
    # dirakit dari masukan, dan itu persis pintu yang C-18 tutup.
    #
    # D-07 Bagian 5.2 sendiri menyatakan batasnya: "IN-01 sampai IN-03 akan
    # dilanggar model sesekali; itulah sebabnya validator ada." Teks ini
    # melengkapi validator, tidak menggantikannya.
    KunciInstruksi.PENJAWABAN: (
        "Jawab pertanyaan kepala sekolah dasar hanya dari segmen yang "
        "disediakan. Jangan memakai pengetahuanmu sendiri. Setiap klaim "
        "faktual wajib menyertakan id_segmen pendukungnya. Bila segmen tidak "
        "memuat jawabannya, nyatakan demikian; jangan menyusun jawaban yang "
        "terdengar masuk akal. Tulis dalam Bahasa Indonesia, kalimat paling "
        "banyak 20 kata, istilah teknis dijelaskan pada kemunculan pertama. "
        "Jangan menyalin kalimat utuh dari segmen; parafrasekan. Jangan "
        "memberi nasihat hukum, medis, atau keuangan pribadi. Jangan menyebut "
        "nama perorangan meski muncul dalam segmen. Balas sebagai objek JSON "
        "dengan kunci ringkasan_tindakan, penjelasan, klaim, dan "
        "catatan_keberlakuan."
    ),
    KunciInstruksi.UJI_ASAP: (
        "Balas dengan satu kalimat singkat. Instruksi ini hanya untuk menguji "
        "jalur pembungkus dan tidak dipakai menyusun jawaban kepada pengguna."
    ),
}


def susun(kunci: KunciInstruksi) -> Instruksi:
    """Bentuk `Instruksi` dari tetapan. Satu-satunya pintu (ADR-13)."""
    return Instruksi(teks=_TEKS[kunci])
