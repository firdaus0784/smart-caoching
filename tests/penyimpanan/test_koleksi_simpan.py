"""Penyimpan koleksi — T-5 fitur 032, R-01, R-02, R-08; K-1, K-4; FR-G06.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL. Yang kedua
tersambung sebagai `peran_koleksi` (TK-64): peran itu hanya memegang tabel
koleksi, sehingga uji ini juga membuktikan hak T-2 cukup — dan kelayakan butir
memang tidak dibacanya.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from src.penyimpanan.koleksi import (
    PERAN_KOLEKSI,
    BarisKoleksi,
    KoleksiMemori,
    KoleksiPostgres,
    PenyimpanKoleksi,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

T0 = datetime(2026, 10, 9, 1, 0, tzinfo=UTC)


def _psd() -> str:
    return "psd_" + "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(16))


@pytest.fixture(params=["memori", "postgres"])
def koleksi(request: pytest.FixtureRequest) -> PenyimpanKoleksi:
    if request.param == "memori":
        return KoleksiMemori()
    return KoleksiPostgres(SambunganPeran(PERAN_KOLEKSI))  # type: ignore[arg-type]


def test_simpan_lalu_terbaca_pemiliknya_saja(koleksi: PenyimpanKoleksi) -> None:
    a, b = _psd(), _psd()
    baris = jalankan(koleksi.simpan(a, "b-1", "Bahas di rapat guru", sekarang=T0))
    assert baris == BarisKoleksi(id_butir="b-1", catatan="Bahas di rapat guru", disimpan_pada=T0)
    assert jalankan(koleksi.milik(a)) == (baris,)
    assert jalankan(koleksi.milik(b)) == ()


def test_simpan_ulang_mengganti_catatan_dan_waktu(koleksi: PenyimpanKoleksi) -> None:
    a = _psd()
    jalankan(koleksi.simpan(a, "b-1", "Catatan lama", sekarang=T0))
    kedua = jalankan(koleksi.simpan(a, "b-1", None, sekarang=T0 + timedelta(hours=1)))
    assert jalankan(koleksi.milik(a)) == (kedua,)
    assert kedua.catatan is None


def test_terbaru_disimpan_lebih_dulu(koleksi: PenyimpanKoleksi) -> None:
    a = _psd()
    for menit, id_butir in ((0, "b-lama"), (5, "b-baru"), (2, "b-tengah")):
        jalankan(koleksi.simpan(a, id_butir, None, sekarang=T0 + timedelta(minutes=menit)))
    assert [b.id_butir for b in jalankan(koleksi.milik(a))] == ["b-baru", "b-tengah", "b-lama"]


def test_keluarkan_sekali(koleksi: PenyimpanKoleksi) -> None:
    a, b = _psd(), _psd()
    jalankan(koleksi.simpan(a, "b-1", None, sekarang=T0))
    assert not jalankan(koleksi.keluarkan(b, "b-1")), "milik orang lain tidak tersentuh"
    assert jalankan(koleksi.keluarkan(a, "b-1"))
    assert not jalankan(koleksi.keluarkan(a, "b-1"))
    assert jalankan(koleksi.milik(a)) == ()


@pytest.mark.parametrize(
    ("pemilik", "catatan", "waktu"),
    [
        ("ks-017", None, T0),
        ("psd_aaaaaaaaaaaaaaaa", "  ", T0),
        ("psd_aaaaaaaaaaaaaaaa", None, datetime(2026, 10, 9, 1, 0)),
    ],
)
def test_masukan_tidak_sah_ditolak(
    koleksi: PenyimpanKoleksi, pemilik: str, catatan: str | None, waktu: datetime
) -> None:
    """C-05 pemilik pseudonim; catatan kosong disimpan `None`; KM-01 UTC."""
    with pytest.raises(ValueError):
        jalankan(koleksi.simpan(pemilik, "b-1", catatan, sekarang=waktu))
