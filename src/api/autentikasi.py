"""Autentikasi dan sesi — fitur 029, FR-A01, R-05, R-06, KA-01, D-14 Bagian 4.4.

T-5 membangun separuh pertamanya: **penentu identitas dari sesi**. Rute masuk
dan keluar yang membangkitkan dan mencabut sesi menyusul pada T-6.

## Penentu sesi tidak menyediakan peran bawaan

Tanpa kuki, kuki tak dikenal, sesi dicabut, sesi diam melampaui
`BATAS_DIAM`, sesi lewat `MASA_SESI`, akun nonaktif, dan peran yang tidak
dikenal — ketujuhnya menghasilkan `None`, dan lapisan HTTP menjawabnya 401
sebelum membaca badan permintaan. Penentu yang jatuh ke peran `pengguna` bila
ragu adalah penentu tiruan pengembangan dengan nama lain (R-10).

## Peran dibaca dari akun pada tiap permintaan

Sesi tidak menyalin peran. Akun yang dinonaktifkan tim, atau yang perannya
diubah, berlaku pada permintaan berikutnya — bukan sesudah sesinya habis.

## Yang tersimpan adalah turunan pengenal

Kuki membawa pengenal acak; peladen menyimpan SHA-256-nya. Pembaca basis data
tidak memperoleh sesi yang dapat dipakai. SHA-256 tanpa garam cukup di sini,
tidak seperti pada sandi: pengenalnya 256 bit acak, bukan pilihan manusia,
sehingga tidak ada kamus yang dapat dicoba.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Final

from fastapi import Request

from src.api.identitas import Identitas
from src.api.peran import Peran
from src.penyimpanan.akun import PenyimpanAkun

NAMA_KUKI: Final = "__Host-sesi"
"""Awalan `__Host-` membuat peramban menolak kuki ini bila tidak `Secure`,
tidak `Path=/`, atau ber-`Domain` — contoh OWASP *Session Management* kata
demi kata."""

BATAS_DIAM: Final = timedelta(minutes=30)
"""P-4, KB-153 — batas atas rentang OWASP bagi aplikasi berisiko rendah."""

MASA_SESI: Final = timedelta(hours=8)
"""P-4, KB-153 — batas mutlak sejak masuk; aktivitas tidak memperpanjangnya."""

JEDA_SENTUH: Final = timedelta(minutes=1)
"""`terakhir_aktif` ditulis paling sering sekali semenit, agar tiap
permintaan tidak menjadi satu penulisan."""

PESAN_BELUM_MASUK: Final = "Anda perlu masuk untuk membuka bagian ini."
"""C-13: ≤ 20 kata, tanpa istilah teknis. Layar tidak menampilkannya — ia
memakai kalimatnya sendiri dari D-05 S-01 — tetapi D-14 Bagian 4.2 menuntut
setiap badan galat membawa kalimat yang layak dibaca manusia."""

_PANJANG_PENGENAL_MAKS: Final = 256


def turunan_pengenal(pengenal: str) -> bytes:
    """SHA-256 atas pengenal pada kuki — satu-satunya bentuk yang tersimpan."""
    return hashlib.sha256(pengenal.encode("utf-8")).digest()


class PenentuSesi:
    """`PenentuIdentitas` sungguhan: identitas dari kuki sesi yang sah."""

    def __init__(
        self,
        akun: PenyimpanAkun,
        *,
        sekarang: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._akun = akun
        self._sekarang = sekarang

    async def identitas(self, permintaan: Request) -> Identitas | None:
        pengenal = permintaan.cookies.get(NAMA_KUKI)
        if not pengenal or len(pengenal) > _PANJANG_PENGENAL_MAKS:
            return None
        kini = self._sekarang()
        turunan = turunan_pengenal(pengenal)
        sesi = await self._akun.baca_sesi(turunan, sekarang=kini, batas_diam=BATAS_DIAM)
        if sesi is None:
            return None
        try:
            peran = Peran(sesi.peran)
        except ValueError:
            return None
        if kini - sesi.terakhir_aktif >= JEDA_SENTUH:
            await self._akun.sentuh_sesi(turunan, sekarang=kini)
        return Identitas(peran=peran, pemilik=sesi.pseudonim)
