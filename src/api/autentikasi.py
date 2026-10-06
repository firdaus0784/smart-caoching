"""Autentikasi dan sesi — fitur 029, FR-A01, R-05, R-06, KA-01, D-14 Bagian 4.4.

T-5 membangun **penentu identitas dari sesi**; T-6 membangun `PenjagaMasuk`,
yang memeriksa sandi, menerbitkan sesi, dan mencabutnya.

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

import asyncio
import hashlib
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Final

from fastapi import Request

from src.api import sandi
from src.api.galat import LOG_OPERASIONAL, id_jejak_baru
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


# ── T-6 · masuk dan keluar ───────────────────────────────────────────

AMBANG_PENAHANAN: Final = 10
"""P-4, KB-153 — penetapan tim tanpa dasar literatur (SI-01). OWASP
*Authentication Cheat Sheet* menyebut ambang perlu ditetapkan, bukan
berapa."""

LAMA_PENAHANAN: Final = timedelta(minutes=15)
"""P-4, KB-153 — penetapan tim tanpa dasar literatur (SI-01)."""

TURUNAN_BERSAMAAN: Final = 2
"""Paling banyak dua turunan sandi berjalan bersamaan; percobaan berlebih
menunggu, bukan menghabiskan memori peladen. Penetapan tim (plan Bagian 4.3)."""

PESAN_MASUK_DITOLAK: Final = (
    "Nama pengguna atau sandi belum cocok. Periksa lagi, atau hubungi tim peneliti."
)
"""D-05 S-01. **Satu kalimat bagi empat sebab** — akun tak ada, sandi salah,
akun ditahan, akun nonaktif (R-04, K-3). Kalimat yang membedakannya memberi
tahu orang lain bahwa sebuah akun ada."""

PESAN_MASUK_TIDAK_LENGKAP: Final = "Nama pengguna dan sandi wajib diisi."


class PenjagaMasuk:
    """Memeriksa sandi dan menerbitkan sesi — R-03, R-04, R-06.

    ## Satu turunan pada setiap percobaan

    Akun yang tidak ada diperiksa terhadap `turunan_tiruan` — turunan
    berparameter **sama** dengan akun sungguhan, dibangkitkan sekali saat
    penjaga dibuat. Akun yang ditahan dan yang nonaktif tetap diperiksa
    sandinya, lalu ditolak apa pun hasilnya. Keempat penolakan karena itu
    menjalankan tepat satu turunan dan menerima tanggapan yang sama.

    ## Log

    Nama pengguna yang **diketik** tidak pernah dicatat: orang sering mengetik
    sandinya pada isian itu. Yang dicatat hanya penahanan akun yang ada,
    dengan `id` akunnya — bukan pseudonimnya.
    """

    def __init__(
        self,
        akun: PenyimpanAkun,
        *,
        sekarang: Callable[[], datetime] = lambda: datetime.now(UTC),
        cocok: Callable[[str, str], bool] = sandi.cocok,
        turunan_tiruan: str | None = None,
    ) -> None:
        self._akun = akun
        self._sekarang = sekarang
        self._cocok = cocok
        self.turunan_tiruan = turunan_tiruan or sandi.turunkan(secrets.token_urlsafe(16))
        self._semafor = asyncio.Semaphore(TURUNAN_BERSAMAAN)

    async def masuk(self, nama_pengguna: str, sandi_masukan: str) -> str | None:
        """Pengenal sesi baru, atau `None` bagi keempat penolakan."""
        akun = await self._akun.baca_akun(nama_pengguna)
        tersimpan = akun.turunan_sandi if akun is not None else self.turunan_tiruan
        async with self._semafor:
            benar = await asyncio.to_thread(self._cocok, sandi_masukan, tersimpan)
        kini = self._sekarang()
        if akun is None:
            return None
        ditahan = akun.ditahan_sampai is not None and akun.ditahan_sampai > kini
        if not benar:
            await self._catat_gagal(akun.id, kini)
            return None
        if ditahan or not akun.status_aktif:
            return None
        await self._akun.catat_berhasil(akun.id)
        pengenal = secrets.token_urlsafe(32)
        await self._akun.buat_sesi(
            turunan_pengenal(pengenal), akun.id, sekarang=kini, kedaluwarsa_pada=kini + MASA_SESI
        )
        return pengenal

    async def pemilik_sesi(self, pengenal: str) -> str | None:
        """Pseudonim pemilik sesi yang sah, atau `None` — K-5 fitur 034.

        Rute masuk menerbitkan sesi sebelum identitas dapat dibaca dari kuki;
        peristiwa `session_start` membutuhkan pemiliknya dari sesi itu sendiri,
        lewat penyimpan akun yang sama dengan `PenentuSesi`.
        """
        sesi = await self._akun.baca_sesi(
            turunan_pengenal(pengenal), sekarang=self._sekarang(), batas_diam=BATAS_DIAM
        )
        return None if sesi is None else sesi.pseudonim

    async def keluar(self, pengenal: str) -> None:
        """Cabut sesi di peladen (R-06). Pengenal tak dikenal tidak melempar."""
        await self._akun.cabut_sesi(turunan_pengenal(pengenal), sekarang=self._sekarang())

    async def _catat_gagal(self, id_akun: str, kini: datetime) -> None:
        baru = await self._akun.catat_gagal(
            id_akun, sekarang=kini, ambang=AMBANG_PENAHANAN, lama_tahan=LAMA_PENAHANAN
        )
        if baru:
            LOG_OPERASIONAL.warning(
                "akun ditahan %s id_akun=%s sampai=%s",
                id_jejak_baru(),
                id_akun,
                (kini + LAMA_PENAHANAN).isoformat(),
            )
