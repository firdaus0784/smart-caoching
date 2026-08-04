"""Jejak versi untuk fitur 001 — C-09, R-12, NFR-15.

Tiga dari lima bidang versi memang belum berlaku pada fitur ini: indeks belum
dibangun (fitur 006), skema anotasi belum dibekukan (fitur 003), dan pembagian
data belum ditetapkan (fitur 004, FR-D07).

Modul ini menyediakan satu tempat untuk menyatakan hal itu, sehingga penanda
`belum-berlaku` tidak ditulis berulang di banyak tempat dan tidak ada yang
tergoda mengosongkannya. Ketika ketiga bidang itu berlaku, yang berubah satu
berkas — bukan setiap pemanggil.
"""

from __future__ import annotations

from src.logbook.versi import BELUM_BERLAKU, Versi


def versi_fitur_001(versi_kode: str, versi_model: str = BELUM_BERLAKU) -> Versi:
    """Jejak versi pada tahap fitur 001."""
    return Versi(
        versi_kode=versi_kode,
        versi_model=versi_model,
        versi_indeks=BELUM_BERLAKU,
        versi_skema_anotasi=BELUM_BERLAKU,
        pembagian_data=BELUM_BERLAKU,
    )
