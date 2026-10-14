"""Daftar UK — T-2 fitur 042, R-01, P-6 A.

Lima belas kode milik D-08 Bagian 8 (UK-01 s.d. UK-08) dan D-13 Bagian 8
(UK-09 s.d. UK-15); uji membacanya dari kedua tabel itu. Empat UK menunggu
bahannya dan dinyatakan demikian, tidak pernah lulus.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

KODE_UK: Final = tuple(f"UK-{i:02d}" for i in range(1, 16))

BELUM_BAHAN: Final[Mapping[str, str]] = MappingProxyType(
    {
        "UK-01": "menunggu gold set (BT-35) dan model penjawab (ADR-12)",
        "UK-03": "menunggu gold set jenis E (BT-35) dan model penjawab (ADR-12)",
        "UK-06": "menunggu model penjawab (ADR-12)",
        "UK-11": "menunggu himpunan serangan D-13 Bagian 9",
    }
)
"""D-08 Bagian 8 aturan pelaksanaan: belum dapat diperiksa sampai bahannya ada."""
