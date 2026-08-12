"""Empat kanal sumber — D-06 Bagian 3, FR-I01.

Enum tersendiri, bukan untai bebas: kanal muncul pada pemantauan antrean
(FR-I08), pada perkiraan volume D-06 Bagian 8.1, dan kelak pada penjadwalan
pengambilan. Tiga tempat yang menuliskannya sebagai untai akan mengejanya
dengan tiga cara.

Nilainya mengikuti ejaan D-06 persis — "K-A", bukan "KA" maupun "k_a" —
sehingga baris pemantauan dapat dibaca berdampingan dengan tabelnya tanpa
penerjemahan.

Tinggal pada `src/ingest/`, bukan `src/kamus/`: `src/kamus/` memuat enum milik
`docs/D14.md` Bagian 5, dan D-14 tidak menyebut kanal sama sekali. Kanal adalah
kosakata D-06, dan D-06 mengatur ingesti.
"""

from __future__ import annotations

from enum import Enum


class Kanal(Enum):
    """Keempat kanal D-06 Bagian 3."""

    K_A = "K-A"
    """Regulasi dan panduan resmi."""
    K_B = "K-B"
    """Data resmi pendidikan."""
    K_C = "K-C"
    """Jurnal ilmiah — volume terbesar, tingkat kelolosan terendah."""
    K_D = "K-D"
    """Laporan lembaga dan praktik baik."""
