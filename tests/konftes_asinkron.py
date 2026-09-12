"""Penjalan korutin bagi uji — Gerbang 2 fitur 024.

`PenyimpanDasar` menjadi asinkron pada 12 September 2026, sehingga uji yang
memanggilnya harus menjalankan korutin. Proyek ini **tidak memakai
`pytest-asyncio`**: ia ketergantungan baru, dan C-12 menuntut persetujuan
penanggung jawab teknis untuk sesuatu yang `asyncio.run` sudah cukup lakukan.

Satu fungsi, dipakai seluruh berkas uji yang menyentuh penyimpanan.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def jalankan(korutin: Coroutine[Any, Any, T]) -> T:
    """Jalankan satu korutin sampai selesai dan kembalikan hasilnya."""
    return asyncio.run(korutin)
