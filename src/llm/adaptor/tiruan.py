"""Adaptor tiruan deterministik — R-10, ADR-12.

Satu-satunya pelaksana `AdaptorDasar` pada fitur 001. BT-14 belum diputuskan,
dan ADR-12 menetapkan pembungkus dibangun terhadap antarmuka abstrak alih-alih
memilih penyedia lewat kode.

Adaptor ini yang membuat kriteria penerimaan spec dapat dipenuhi: tidak ada
pemanggilan ke penyedia luar selama seluruh rangkaian uji (G4-15). Ia tidak
mengimpor pustaka jaringan apa pun, dan uji memeriksa hal itu langsung pada
daftar impornya.

Determinisme bukan kenyamanan melainkan syarat. Uji penanda C-18 membandingkan
muatan yang dihasilkan; muatan yang berubah tiap pemanggilan membuat
perbandingan itu tidak bermakna.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from src.llm.adaptor.dasar import AdaptorDasar, Permintaan
from src.llm.tipe import Tanggapan


class AdaptorTiruan(AdaptorDasar):
    """Penyedia tiruan. Tidak menyentuh jaringan, tidak berbiaya."""

    def __init__(self) -> None:
        self.terakhir: Permintaan | None = None

    def kirim(self, permintaan: Permintaan) -> Tanggapan:
        mulai = datetime.now(UTC)
        self.terakhir = permintaan

        # Sidik dihitung dari instruksi dan data secara terpisah, bukan dari
        # untai gabungan. Merangkai keduanya di sini pun akan menjadi jalur
        # yang bertentangan dengan C-18, meski hanya untuk menghitung sidik.
        pencerna = hashlib.sha256()
        pencerna.update(permintaan.instruksi.teks.encode("utf-8"))
        for butir in permintaan.data:
            pencerna.update(butir.id_segmen.encode("utf-8"))
            pencerna.update(butir.teks.encode("utf-8"))
        sidik = pencerna.hexdigest()

        return Tanggapan(
            teks=f"tanggapan tiruan untuk sidik {sidik[:16]}",
            versi_model=permintaan.konfigurasi.versi_model,
            waktu_mulai=mulai,
            waktu_selesai=datetime.now(UTC),
            biaya=0.0,
            id_jejak=f"trc_tiruan_{sidik[:12]}",
        )
