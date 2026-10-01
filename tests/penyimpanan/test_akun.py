"""Penyimpan akun dan sesi — T-4 fitur 029, R-04, R-06, P-2, P-4.

**Satu himpunan uji, dua pelaksana**, bentuk yang sama dengan
`test_riwayat.py`: setiap uji perilaku dijalankan atas `AkunMemori` dan
`AkunPostgres`. `AkunPostgres` tersambung sebagai `peran_autentikasi` sendiri,
bukan sebagai pengelola (TK-64) — sehingga uji ini juga membuktikan hak per
kolom T-2 cukup bagi pekerjaannya.

Akun uji dibuat lewat `peran_pengelola_akun`, peran yang memang berhak
membuatnya. Nama akunnya acak per uji, sehingga baris uji sebelumnya pada
basis data bersama tidak memengaruhi hasil.
"""

from __future__ import annotations

import asyncio
import hashlib
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from src.penyimpanan.akun import (
    PERAN_AUTENTIKASI,
    AkunMemori,
    AkunPostgres,
    BarisAkun,
    PenyimpanAkun,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, siapkan

siapkan()

T0 = datetime(2026, 10, 1, 7, 0, tzinfo=UTC)
AMBANG = 10
LAMA_TAHAN = timedelta(minutes=15)
BATAS_DIAM = timedelta(minutes=30)
MASA = timedelta(hours=8)


class SambunganPeran:
    """Satu sambungan baru per kueri, sebagai peran tertentu."""

    def __init__(self, peran: str) -> None:
        self._peran = peran

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user=self._peran, database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def fetch(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetch", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("execute", kueri, *argumen)


def _akun_baru() -> BarisAkun:
    return BarisAkun(
        id="".join(secrets.choice("abcdefghjkmnpqrstuvwxyz") for _ in range(6))
        + f"-{secrets.randbelow(1000):03d}",
        pseudonim=f"psd_{secrets.token_hex(8)}",
        peran="pengguna",
        status_aktif=True,
        turunan_sandi="scrypt$16$8$1$AAAA$AAAA",
        gagal_beruntun=0,
        ditahan_sampai=None,
    )


async def _buat_lewat_pengelola(akun: BarisAkun) -> None:
    await SambunganPeran("peran_pengelola_akun").execute(
        "INSERT INTO akun.pengguna (id, pseudonim, peran, status_aktif, tanggal_dibuat, "
        "turunan_sandi) VALUES ($1, $2, $3, $4, $5, $6)",
        akun.id,
        akun.pseudonim,
        akun.peran,
        akun.status_aktif,
        T0,
        akun.turunan_sandi,
    )


class Pasangan:
    """Penyimpan beserta cara menyiapkan akun di belakangnya."""

    def __init__(
        self,
        penyimpan: PenyimpanAkun,
        tambah: Callable[[BarisAkun], Awaitable[None]],
        nonaktifkan: Callable[[str], Awaitable[None]],
    ) -> None:
        self.penyimpan = penyimpan
        self.tambah = tambah
        self.nonaktifkan = nonaktifkan

    async def akun(self) -> BarisAkun:
        # Nama acak dapat bertabrakan dengan baris uji lama; cari yang kosong.
        while True:
            calon = _akun_baru()
            if await self.penyimpan.baca_akun(calon.id) is None:
                await self.tambah(calon)
                return calon


def _memori() -> Pasangan:
    simpan = AkunMemori()

    async def tambah(akun: BarisAkun) -> None:
        simpan.pasang_akun(akun)

    async def nonaktifkan(id_akun: str) -> None:
        akun = await simpan.baca_akun(id_akun)
        assert akun is not None
        simpan.pasang_akun(replace(akun, status_aktif=False))

    return Pasangan(simpan, tambah, nonaktifkan)


def _postgres() -> Pasangan:
    async def nonaktifkan(id_akun: str) -> None:
        await SambunganPeran("peran_pengelola_akun").execute(
            "UPDATE akun.pengguna SET status_aktif = false WHERE id = $1", id_akun
        )

    return Pasangan(
        AkunPostgres(SambunganPeran(PERAN_AUTENTIKASI)),  # type: ignore[arg-type]
        _buat_lewat_pengelola,
        nonaktifkan,
    )


@pytest.fixture(params=["memori", "postgres"])
def pasangan(request: pytest.FixtureRequest) -> Pasangan:
    return _memori() if request.param == "memori" else _postgres()


def _turunan() -> bytes:
    return hashlib.sha256(secrets.token_bytes(32)).digest()


# ── akun ─────────────────────────────────────────────────────────────


def test_baca_akun(pasangan: Pasangan) -> None:
    async def uji() -> None:
        akun = await pasangan.akun()
        baca = await pasangan.penyimpan.baca_akun(akun.id)
        assert baca == akun
        assert await pasangan.penyimpan.baca_akun("tak-ada-000") is None

    jalankan(uji())


def test_kegagalan_beruntun_menahan_pada_ambang(pasangan: Pasangan) -> None:
    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        for ke in range(1, AMBANG):
            baru = await p.catat_gagal(akun.id, sekarang=T0, ambang=AMBANG, lama_tahan=LAMA_TAHAN)
            assert baru is False, ke
        assert await p.catat_gagal(akun.id, sekarang=T0, ambang=AMBANG, lama_tahan=LAMA_TAHAN)
        baca = await p.baca_akun(akun.id)
        assert baca is not None
        assert baca.gagal_beruntun == AMBANG
        assert baca.ditahan_sampai == T0 + LAMA_TAHAN

    jalankan(uji())


def test_percobaan_selama_ditahan_tidak_memperpanjang(pasangan: Pasangan) -> None:
    """Penyerang yang mengetahui nama akun tidak dapat menahannya selamanya."""

    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        for _ in range(AMBANG):
            await p.catat_gagal(akun.id, sekarang=T0, ambang=AMBANG, lama_tahan=LAMA_TAHAN)
        nanti = T0 + timedelta(minutes=10)
        for _ in range(5):
            baru = await p.catat_gagal(
                akun.id, sekarang=nanti, ambang=AMBANG, lama_tahan=LAMA_TAHAN
            )
            assert baru is False
        baca = await p.baca_akun(akun.id)
        assert baca is not None
        assert (baca.gagal_beruntun, baca.ditahan_sampai) == (AMBANG, T0 + LAMA_TAHAN)

    jalankan(uji())


def test_sesudah_penahanan_berakhir_penghitung_mulai_lagi(pasangan: Pasangan) -> None:
    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        for _ in range(AMBANG):
            await p.catat_gagal(akun.id, sekarang=T0, ambang=AMBANG, lama_tahan=LAMA_TAHAN)
        lewat = T0 + LAMA_TAHAN + timedelta(seconds=1)
        assert not await p.catat_gagal(
            akun.id, sekarang=lewat, ambang=AMBANG, lama_tahan=LAMA_TAHAN
        )
        baca = await p.baca_akun(akun.id)
        assert baca is not None
        assert (baca.gagal_beruntun, baca.ditahan_sampai) == (1, None)

    jalankan(uji())


def test_berhasil_mengembalikan_penghitung_ke_nol(pasangan: Pasangan) -> None:
    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        for _ in range(3):
            await p.catat_gagal(akun.id, sekarang=T0, ambang=AMBANG, lama_tahan=LAMA_TAHAN)
        await p.catat_berhasil(akun.id)
        baca = await p.baca_akun(akun.id)
        assert baca is not None
        assert (baca.gagal_beruntun, baca.ditahan_sampai) == (0, None)

    jalankan(uji())


def test_catat_gagal_akun_tak_ada_tidak_menulis_apa_pun(pasangan: Pasangan) -> None:
    async def uji() -> None:
        baru = await pasangan.penyimpan.catat_gagal(
            "tak-ada-000", sekarang=T0, ambang=AMBANG, lama_tahan=LAMA_TAHAN
        )
        assert baru is False
        assert await pasangan.penyimpan.baca_akun("tak-ada-000") is None

    jalankan(uji())


def test_penahanan_atomik_pada_postgres() -> None:
    """Dua belas kegagalan bersamaan: tepat satu penahanan, penghitung tepat
    sepuluh. Membaca lalu menulis akan membuat beberapa percobaan sama-sama
    membaca sembilan."""
    pasangan = _postgres()

    async def uji() -> None:
        akun = await pasangan.akun()
        hasil = await asyncio.gather(
            *[
                pasangan.penyimpan.catat_gagal(
                    akun.id, sekarang=T0, ambang=AMBANG, lama_tahan=LAMA_TAHAN
                )
                for _ in range(AMBANG + 2)
            ]
        )
        assert sum(hasil) == 1
        baca = await pasangan.penyimpan.baca_akun(akun.id)
        assert baca is not None
        assert baca.gagal_beruntun == AMBANG

    jalankan(uji())


# ── sesi ─────────────────────────────────────────────────────────────


def test_sesi_dibuat_lalu_terbaca_bersama_peran_dan_pseudonim(pasangan: Pasangan) -> None:
    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        t = _turunan()
        await p.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)
        sesi = await p.baca_sesi(t, sekarang=T0 + timedelta(minutes=5), batas_diam=BATAS_DIAM)
        assert sesi is not None
        assert (sesi.id_pengguna, sesi.pseudonim, sesi.peran) == (
            akun.id,
            akun.pseudonim,
            akun.peran,
        )
        assert sesi.terakhir_aktif == T0
        assert await p.baca_sesi(_turunan(), sekarang=T0, batas_diam=BATAS_DIAM) is None

    jalankan(uji())


def test_sesi_berakhir_sesudah_tanpa_aktivitas(pasangan: Pasangan) -> None:
    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        t = _turunan()
        await p.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)
        assert await p.baca_sesi(
            t, sekarang=T0 + BATAS_DIAM - timedelta(seconds=1), batas_diam=BATAS_DIAM
        )
        assert await p.baca_sesi(t, sekarang=T0 + BATAS_DIAM, batas_diam=BATAS_DIAM) is None

    jalankan(uji())


def test_sentuh_memperpanjang_aktivitas_bukan_batas_mutlak(pasangan: Pasangan) -> None:
    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        t = _turunan()
        await p.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)
        jam = T0
        while jam < T0 + MASA - timedelta(minutes=20):
            jam += timedelta(minutes=20)
            await p.sentuh_sesi(t, sekarang=jam)
            assert await p.baca_sesi(t, sekarang=jam, batas_diam=BATAS_DIAM)
        await p.sentuh_sesi(t, sekarang=T0 + MASA - timedelta(seconds=1))
        assert await p.baca_sesi(t, sekarang=T0 + MASA, batas_diam=BATAS_DIAM) is None

    jalankan(uji())


def test_sesi_dicabut_tidak_terbaca_dan_sentuh_tidak_menghidupkannya(pasangan: Pasangan) -> None:
    """R-06 — keluar berlaku seketika di peladen."""

    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        t = _turunan()
        await p.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)
        await p.cabut_sesi(t, sekarang=T0 + timedelta(minutes=1))
        await p.sentuh_sesi(t, sekarang=T0 + timedelta(minutes=2))
        assert (
            await p.baca_sesi(t, sekarang=T0 + timedelta(minutes=2), batas_diam=BATAS_DIAM) is None
        )

    jalankan(uji())


def test_sesi_akun_nonaktif_tidak_terbaca(pasangan: Pasangan) -> None:
    """Peran dan status dibaca dari akun tiap kali, tidak disalin ke sesi."""

    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        t = _turunan()
        await p.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)
        await pasangan.nonaktifkan(akun.id)
        assert await p.baca_sesi(t, sekarang=T0, batas_diam=BATAS_DIAM) is None

    jalankan(uji())


@pytest.mark.parametrize("panjang", [0, 31, 33, 43])
def test_sesi_hanya_menerima_turunan_tiga_puluh_dua_bita(pasangan: Pasangan, panjang: int) -> None:
    """Pengenal mentah `token_urlsafe(32)` berpanjang 43 — ditolak. Bentuk
    penyimpan ini sendiri yang membuat pengenal asli tidak dapat tersimpan."""

    async def uji() -> None:
        akun = await pasangan.akun()
        with pytest.raises(ValueError):
            await pasangan.penyimpan.buat_sesi(
                b"x" * panjang, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA
            )

    jalankan(uji())


def test_waktu_tanpa_zona_ditolak(pasangan: Pasangan) -> None:
    """KM-01 — kedua pelaksana menolak sama, bukan satu lewat batasan tabel."""

    async def uji() -> None:
        akun = await pasangan.akun()
        polos = datetime(2026, 10, 1, 7, 0)
        with pytest.raises(ValueError):
            await pasangan.penyimpan.buat_sesi(
                _turunan(), akun.id, sekarang=polos, kedaluwarsa_pada=polos + MASA
            )

    jalankan(uji())


def test_permukaan_tanpa_hapus_maupun_pengubah_sandi() -> None:
    """Pencabutan, bukan penghapusan; sandi, peran, dan pseudonim hanya diubah
    perkakas tim — ditegakkan peladen pada T-2, dan permukaan ini tidak
    menawarkannya sejak awal."""
    for kelas in (AkunMemori, AkunPostgres):
        nama = {n for n in dir(kelas) if not n.startswith("_")}
        terlarang = {
            n for n in nama if any(k in n for k in ("hapus", "ubah", "atur", "sandi", "peran"))
        }
        assert not terlarang, (kelas.__name__, terlarang)


def _penolakan() -> tuple[type[BaseException], ...]:
    """Pelaksana memori menolak dengan `ValueError`; PostgreSQL dengan
    pelanggaran batasan. Keduanya menolak — itu yang diuji."""
    import asyncpg

    return (ValueError, asyncpg.exceptions.IntegrityConstraintViolationError)


def test_sesi_bagi_akun_tak_ada_ditolak(pasangan: Pasangan) -> None:
    async def uji() -> None:
        with pytest.raises(_penolakan()):
            await pasangan.penyimpan.buat_sesi(
                _turunan(), "tak-ada-000", sekarang=T0, kedaluwarsa_pada=T0 + MASA
            )

    jalankan(uji())


def test_turunan_pengenal_ganda_ditolak(pasangan: Pasangan) -> None:
    """Pengenal yang bertabrakan tidak boleh diam-diam menimpa sesi orang lain."""

    async def uji() -> None:
        akun = await pasangan.akun()
        t = _turunan()
        await pasangan.penyimpan.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)
        with pytest.raises(_penolakan()):
            await pasangan.penyimpan.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)

    jalankan(uji())


def test_catat_berhasil_akun_tak_ada_tidak_menulis_apa_pun(pasangan: Pasangan) -> None:
    async def uji() -> None:
        await pasangan.penyimpan.catat_berhasil("tak-ada-000")
        assert await pasangan.penyimpan.baca_akun("tak-ada-000") is None

    jalankan(uji())


def test_mencabut_dua_kali_dan_sesi_tak_dikenal_tidak_melempar(pasangan: Pasangan) -> None:
    """Keluar dua kali — dua tab, dua ketukan — bukan galat."""

    async def uji() -> None:
        akun = await pasangan.akun()
        p = pasangan.penyimpan
        t = _turunan()
        await p.buat_sesi(t, akun.id, sekarang=T0, kedaluwarsa_pada=T0 + MASA)
        await p.cabut_sesi(t, sekarang=T0)
        await p.cabut_sesi(t, sekarang=T0 + timedelta(minutes=1))
        await p.cabut_sesi(_turunan(), sekarang=T0)
        await p.sentuh_sesi(_turunan(), sekarang=T0)
        assert await p.baca_sesi(t, sekarang=T0, batas_diam=BATAS_DIAM) is None

    jalankan(uji())
