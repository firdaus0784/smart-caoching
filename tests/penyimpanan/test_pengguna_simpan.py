"""Penyimpan profil, prioritas, persetujuan — T-3 fitur 030, R-02, R-03, R-04, K-3.

Satu himpunan uji atas `PenggunaMemori` **dan** `PenggunaPostgres`; yang kedua
tersambung sebagai `peran_pengguna` sendiri (TK-64), sehingga uji ini juga
membuktikan hak per kolom T-2 cukup bagi pekerjaannya. Pemilik tiap uji
pseudonim acak, sehingga baris uji lama pada basis data bersama tidak
memengaruhi hasil.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from src.penyimpanan.pengguna import (
    PERAN_PENGGUNA,
    BarisProfil,
    PenggunaMemori,
    PenggunaPostgres,
    PenyimpanPengguna,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

T0 = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)

PROFIL = BarisProfil(
    jabatan="Kepala Sekolah",
    masa_kerja=3,
    jumlah_rombel=6,
    jumlah_ptk=9,
    jalur_akreditasi="visitasi",
    wilayah="Kabupaten Sumedang",
)


def _psd() -> str:
    return "psd_" + "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(16))


@pytest.fixture(params=["memori", "postgres"])
def simpan(request: pytest.FixtureRequest) -> PenyimpanPengguna:
    if request.param == "memori":
        return PenggunaMemori()
    return PenggunaPostgres(SambunganPeran(PERAN_PENGGUNA))  # type: ignore[arg-type]


# ── profil ───────────────────────────────────────────────────────────


def test_profil_belum_ada(simpan: PenyimpanPengguna) -> None:
    assert jalankan(simpan.baca_profil(_psd())) is None


def test_profil_disimpan_lalu_diperbarui(simpan: PenyimpanPengguna) -> None:
    """Simpan pertama: belum pernah diperbarui. Simpan kedua mencatat waktunya
    (FR-A06) — waktu dari pemanggil yang memegang jam, bukan dari klien."""

    async def uji() -> None:
        p = _psd()
        await simpan.simpan_profil(p, PROFIL, sekarang=T0)
        pertama = await simpan.baca_profil(p)
        assert pertama is not None
        assert pertama.isi == PROFIL
        assert pertama.tanggal_perbarui is None
        baru = BarisProfil(**{**PROFIL.__dict__, "wilayah": "Kota Bandung"})
        await simpan.simpan_profil(p, baru, sekarang=T0 + timedelta(days=1))
        kedua = await simpan.baca_profil(p)
        assert kedua is not None
        assert kedua.isi.wilayah == "Kota Bandung"
        assert kedua.tanggal_perbarui == T0 + timedelta(days=1)

    jalankan(uji())


def test_profil_pemilik_terpisah(simpan: PenyimpanPengguna) -> None:
    async def uji() -> None:
        a, b = _psd(), _psd()
        await simpan.simpan_profil(a, PROFIL, sekarang=T0)
        assert await simpan.baca_profil(b) is None

    jalankan(uji())


@pytest.mark.parametrize("pemilik", ["ks-017", "psd_0123456789abcdef", "", "PSD_AAAAAAAAAAAAAAAA"])
def test_pemilik_bukan_pseudonim_ditolak(simpan: PenyimpanPengguna, pemilik: str) -> None:
    """C-05 — kedua pelaksana menolak sama, bukan satu lewat batasan tabel."""
    with pytest.raises(ValueError):
        jalankan(simpan.simpan_profil(pemilik, PROFIL, sekarang=T0))


# ── prioritas ────────────────────────────────────────────────────────


def test_prioritas_tambah_saja_yang_terbaru_berlaku(simpan: PenyimpanPengguna) -> None:
    """K-3, M-7: penetapan kedua tidak menghapus yang pertama."""

    async def uji() -> None:
        p = _psd()
        assert await simpan.baca_prioritas(p) == ()
        await simpan.tetapkan_prioritas(p, ("K5", "K1", "K7"), sekarang=T0)
        await simpan.tetapkan_prioritas(
            p, ("K2", "K3", "K4", "K8"), sekarang=T0 + timedelta(hours=1)
        )
        assert await simpan.baca_prioritas(p) == ("K2", "K3", "K4", "K8")
        assert await simpan.riwayat_prioritas(p) == (("K5", "K1", "K7"), ("K2", "K3", "K4", "K8"))

    jalankan(uji())


def test_urutan_prioritas_pilihan_pengguna_dipertahankan(simpan: PenyimpanPengguna) -> None:
    async def uji() -> None:
        p = _psd()
        await simpan.tetapkan_prioritas(p, ("K8", "K1", "K5"), sekarang=T0)
        assert await simpan.baca_prioritas(p) == ("K8", "K1", "K5")

    jalankan(uji())


@pytest.mark.parametrize(
    "kategori", [("K1", "K2"), ("K1", "K2", "K3", "K4", "K5", "K6"), ("K1", "K2", "K9")]
)
def test_prioritas_di_luar_aturan_ditolak(
    simpan: PenyimpanPengguna, kategori: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        jalankan(simpan.tetapkan_prioritas(_psd(), kategori, sekarang=T0))


# ── persetujuan ──────────────────────────────────────────────────────


def test_persetujuan_belum_ada(simpan: PenyimpanPengguna) -> None:
    assert jalankan(simpan.baca_persetujuan(_psd())) is None


def test_persetujuan_terbaru_berlaku_dan_berubah_pikiran_menambah(
    simpan: PenyimpanPengguna,
) -> None:
    async def uji() -> None:
        p = _psd()
        await simpan.catat_persetujuan(p, versi_naskah="et02-v1", disetujui=False, sekarang=T0)
        ditolak = await simpan.baca_persetujuan(p)
        assert ditolak is not None and not ditolak.disetujui
        await simpan.catat_persetujuan(
            p, versi_naskah="et02-v1", disetujui=True, sekarang=T0 + timedelta(minutes=5)
        )
        setuju = await simpan.baca_persetujuan(p)
        assert setuju is not None
        assert (setuju.disetujui, setuju.versi_naskah, setuju.tanggal, setuju.dicabut_pada) == (
            True,
            "et02-v1",
            T0 + timedelta(minutes=5),
            None,
        )
        assert await simpan.jumlah_catatan_persetujuan(p) == 2

    jalankan(uji())


def test_pencabutan_hanya_mengisi_dicabut_pada(simpan: PenyimpanPengguna) -> None:
    async def uji() -> None:
        p = _psd()
        await simpan.catat_persetujuan(p, versi_naskah="et02-v1", disetujui=True, sekarang=T0)
        assert await simpan.cabut_persetujuan(p, sekarang=T0 + timedelta(days=2))
        catatan = await simpan.baca_persetujuan(p)
        assert catatan is not None
        assert (catatan.disetujui, catatan.dicabut_pada) == (True, T0 + timedelta(days=2))
        # Yang sudah dicabut tidak dicabut ulang; waktunya tetap.
        assert not await simpan.cabut_persetujuan(p, sekarang=T0 + timedelta(days=3))
        ulang = await simpan.baca_persetujuan(p)
        assert ulang is not None and ulang.dicabut_pada == T0 + timedelta(days=2)
        assert await simpan.jumlah_catatan_persetujuan(p) == 1

    jalankan(uji())


def test_penolakan_tidak_dapat_dicabut(simpan: PenyimpanPengguna) -> None:
    async def uji() -> None:
        p = _psd()
        assert not await simpan.cabut_persetujuan(p, sekarang=T0)
        await simpan.catat_persetujuan(p, versi_naskah="et02-v1", disetujui=False, sekarang=T0)
        assert not await simpan.cabut_persetujuan(p, sekarang=T0 + timedelta(minutes=1))

    jalankan(uji())


def test_versi_naskah_kosong_ditolak(simpan: PenyimpanPengguna) -> None:
    """R-04."""
    with pytest.raises(ValueError):
        jalankan(simpan.catat_persetujuan(_psd(), versi_naskah="  ", disetujui=True, sekarang=T0))


def test_waktu_tanpa_zona_ditolak(simpan: PenyimpanPengguna) -> None:
    with pytest.raises(ValueError):
        jalankan(simpan.simpan_profil(_psd(), PROFIL, sekarang=datetime(2026, 10, 4, 7, 0)))


def test_permukaan_tanpa_hapus() -> None:
    for kelas in (PenggunaMemori, PenggunaPostgres):
        nama = {n for n in dir(kelas) if not n.startswith("_")}
        assert not {n for n in nama if "hapus" in n or "ubah" in n}, kelas.__name__


def test_kolom_kategori_yang_bukan_larik_ditolak_terang() -> None:
    """Penggerak yang mengembalikan bentuk lain adalah kerusakan, bukan
    prioritas kosong — ia tidak boleh terbaca sebagai daftar huruf."""
    from src.penyimpanan.pengguna import _larik

    assert _larik(["K1", "K2", "K3"]) == ("K1", "K2", "K3")
    with pytest.raises(TypeError):
        _larik("K1,K2,K3")
