"""Penyimpan telemetri — T-3 fitur 034, R-04, R-05, R-10, K-3.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL; yang kedua
tersambung sebagai `peran_telemetri` sendiri (TK-64). Pemilik acak per uji.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from src.penyimpanan.telemetri import (
    PERAN_TELEMETRI,
    BarisPeristiwa,
    PenyimpanTelemetri,
    TelemetriMemori,
    TelemetriPostgres,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

T0 = datetime(2026, 10, 6, 1, 0, tzinfo=UTC)


def _psd() -> str:
    return "psd_" + "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(16))


def _baris(pemilik: str, jenis: str = "session_start", waktu: datetime = T0, **properti: object):
    return BarisPeristiwa(
        pseudonim=pemilik,
        jenis=jenis,
        waktu=waktu,
        properti=dict(properti),
        versi_aplikasi="uji",
        versi_model="tanpa_model",
    )


@pytest.fixture(params=["memori", "postgres"])
def simpan(request: pytest.FixtureRequest) -> PenyimpanTelemetri:
    if request.param == "memori":
        return TelemetriMemori()
    return TelemetriPostgres(SambunganPeran(PERAN_TELEMETRI))  # type: ignore[arg-type]


def test_tambah_lalu_baca_milik_sendiri(simpan: PenyimpanTelemetri) -> None:
    async def uji() -> None:
        a, b = _psd(), _psd()
        await simpan.tambah(_baris(a, "question_asked", panjang_pertanyaan=42))
        await simpan.tambah(_baris(b))
        milik = await simpan.milik(a)
        assert milik == (_baris(a, "question_asked", panjang_pertanyaan=42),)

    jalankan(uji())


def test_terakhir_menurut_jenis(simpan: PenyimpanTelemetri) -> None:
    async def uji() -> None:
        p = _psd()
        assert await simpan.terakhir(p, "session_start") is None
        await simpan.tambah(_baris(p, waktu=T0))
        await simpan.tambah(_baris(p, waktu=T0 + timedelta(days=2)))
        await simpan.tambah(_baris(p, "session_end", waktu=T0 + timedelta(days=3)))
        assert await simpan.terakhir(p, "session_start") == T0 + timedelta(days=2)
        assert await simpan.terakhir(_psd(), "session_start") is None

    jalankan(uji())


@pytest.mark.parametrize(
    "ubah",
    [
        {"pseudonim": "ks-017"},
        {"pseudonim": ""},
        {"jenis": "klik_iklan"},
        {"waktu": datetime(2026, 10, 6)},
        {"versi_model": " "},
        {"versi_aplikasi": ""},
    ],
)
def test_bentuk_salah_ditolak_sama(simpan: PenyimpanTelemetri, ubah: dict[str, object]) -> None:
    """Kedua pelaksana menolak sama, bukan satu lewat batasan tabel."""
    salah = BarisPeristiwa(**{**_baris(_psd()).__dict__, **ubah})
    with pytest.raises(ValueError):
        jalankan(simpan.tambah(salah))


def test_permukaan_tanpa_ubah_dan_hapus() -> None:
    for kelas in (TelemetriMemori, TelemetriPostgres):
        nama = {n for n in dir(kelas) if not n.startswith("_")}
        assert not {n for n in nama if "hapus" in n or "ubah" in n or "ganti" in n}, kelas.__name__


def test_kode_salinan_sama_dengan_taksonomi() -> None:
    from src.penyimpanan import telemetri
    from src.telemetri.peristiwa import JenisPeristiwa

    assert {j.value for j in JenisPeristiwa} == telemetri._KODE
