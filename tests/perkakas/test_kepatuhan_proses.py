"""Pemeriksaan dalam proses UK-10, UK-12, UK-13 — T-4 fitur 042, K-3, P-5 A.

Pemeriksa dan validator yang sama dengan `make check`, atas kode yang
terpasang. Setiap UK membawa **kendali**: keluaran bersih wajib lulus, agar
validator yang menolak segalanya tidak terbaca patuh.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from src.rag.validator.pemeriksaan import HasilPemeriksaan, KodePemeriksaan, Status
from tests.konftes_asinkron import jalankan

import perkakas.kepatuhan.proses as proses
from perkakas.kepatuhan.hasil import Keadaan, Konteks
from perkakas.pemeriksa.ast_aturan import Temuan

AKAR = Path(__file__).resolve().parents[2]
KONTEKS = Konteks(buka=None, api=None, akar_repo=AKAR)  # type: ignore[arg-type]


@pytest.mark.parametrize("periksa", [proses.periksa_uk10, proses.periksa_uk12, proses.periksa_uk13])
def test_lulus_atas_kode_terpasang(periksa) -> None:  # type: ignore[no-untyped-def]
    hasil = jalankan(periksa(KONTEKS))
    assert hasil.keadaan is Keadaan.LULUS, hasil.rincian


def test_uk10_temuan_pemeriksa_menjadi_gagal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        proses, "periksa_pemisahan_instruksi", lambda akar: [Temuan(AKAR / "x.py", 3, "pesan")]
    )
    hasil = jalankan(proses.periksa_uk10(KONTEKS))
    assert hasil.keadaan is Keadaan.GAGAL
    assert "x.py:3" in hasil.rincian[0]


def _selalu(status: Status, kode: KodePemeriksaan):  # type: ignore[no-untyped-def]
    return lambda keluaran, *, segmen: HasilPemeriksaan(kode=kode, status=status, alasan="uji")


@pytest.mark.parametrize(
    ("nama", "periksa", "kode"),
    [
        ("periksa_penyimpangan", proses.periksa_uk12, KodePemeriksaan.VS_09),
        ("periksa_peringkat_klaim", proses.periksa_uk13, KodePemeriksaan.VS_08),
    ],
)
def test_validator_dilonggarkan_atau_menolak_segalanya_gagal(
    monkeypatch: pytest.MonkeyPatch,
    nama: str,
    periksa,
    kode: KodePemeriksaan,  # type: ignore[no-untyped-def]
) -> None:
    monkeypatch.setattr(proses, nama, _selalu(Status.LULUS, kode))
    assert jalankan(periksa(KONTEKS)).keadaan is Keadaan.GAGAL
    monkeypatch.setattr(proses, nama, _selalu(Status.GAGAL, kode))
    hasil = jalankan(periksa(KONTEKS))
    assert hasil.keadaan is Keadaan.GAGAL
    assert any("kendali" in r for r in hasil.rincian)
