"""Pemeriksaan basis data penjalan U5 — T-3 fitur 042, R-03, R-04, K-2, P-2 A.

Seluruhnya atas PostgreSQL sebagai peran sungguhan. Uji pembanding memakai
mesin percobaan yang sama atas pernyataan yang **semestinya berhasil**, agar
lulusnya UK bukan karena percobaan yang selalu gagal.
"""

from __future__ import annotations

import ast
import secrets
from pathlib import Path

import pytest
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, psql

import perkakas.jalankan_lokal as jalankan_lokal
from perkakas.kepatuhan.__main__ import BASIS_DATA, BASIS_DATA_PSEUDONIM, konteks_dari_lingkungan
from perkakas.kepatuhan.basis_data import (
    PERAN_APLIKASI,
    PERAN_RAG,
    Percobaan,
    coba,
    periksa_uk02,
    periksa_uk04,
    periksa_uk08,
    periksa_uk09,
)
from perkakas.kepatuhan.hasil import Keadaan, Konteks

AKAR = Path(__file__).resolve().parents[2]


def _konteks() -> Konteks:
    return konteks_dari_lingkungan({"PGHOST": HOST, "PGPORT": str(PORT)}, AKAR)


@pytest.mark.parametrize("periksa", [periksa_uk02, periksa_uk04, periksa_uk08, periksa_uk09])
def test_uk_basis_data_lulus_pada_peladen_sungguhan(periksa) -> None:  # type: ignore[no-untyped-def]
    hasil = jalankan(periksa(_konteks()))
    assert hasil.keadaan is Keadaan.LULUS, hasil.rincian
    assert hasil.rincian


def test_uk04_mencakup_setiap_peran_aplikasi_dan_uk02_setiap_peran_rag() -> None:
    hasil = jalankan(periksa_uk04(_konteks()))
    for peran in PERAN_APLIKASI:
        assert any(r.startswith(f"{peran}:") for r in hasil.rincian)
    hasil = jalankan(periksa_uk02(_konteks()))
    for peran in PERAN_RAG:
        assert any(r.startswith(f"{peran}:") for r in hasil.rincian)


def test_peran_aplikasi_mencakup_perakitan_jalankan_lokal() -> None:
    """Peran baru pada aplikasi tidak luput dari UK-04."""
    pohon = ast.parse(Path(jalankan_lokal.__file__).read_text(encoding="utf-8"))
    nama = {n.id for n in ast.walk(pohon) if isinstance(n, ast.Name) and n.id.startswith("PERAN_")}
    dipakai = {getattr(jalankan_lokal, n) for n in nama}
    assert dipakai
    assert dipakai <= set(PERAN_APLIKASI)


def test_percobaan_yang_semestinya_berhasil_dilaporkan_gagal() -> None:
    """Pembanding: `peran_verifikasi` berhak membaca karantina."""
    p = Percobaan(
        "peran_verifikasi", BASIS_DATA, "SELECT 1 FROM karantina.dokumen_sumber LIMIT 0", "42501",
        "baca karantina",
    )  # fmt: skip
    hasil = jalankan(coba(_konteks(), p))
    assert hasil.keadaan is Keadaan.GAGAL
    assert "berhasil" in hasil.rincian[0]


def test_sisip_yang_berhasil_tidak_meninggalkan_baris() -> None:
    """R-04 (M-2): transaksi selalu dibatalkan, juga bila pernyataan berhasil."""
    pseudonim = "psd_" + "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(16))
    p = Percobaan(
        "peran_telemetri",
        BASIS_DATA,
        "INSERT INTO telemetri.peristiwa (pseudonim, jenis, waktu, properti, versi_aplikasi, "
        f"versi_model) VALUES ('{pseudonim}', 'session_start', now(), '{{}}', 'v', 'v')",
        "42501",
        "sisip peristiwa",
    )
    gagal = jalankan(coba(_konteks(), p))
    assert gagal.keadaan is Keadaan.GAGAL
    assert "berhasil" in gagal.rincian[0], "pembanding wajib benar-benar berhasil"
    hasil = psql(
        "smart_coaching", "-At", "-c",
        f"select count(*) from telemetri.peristiwa where pseudonim = '{pseudonim}'",
    )  # fmt: skip
    assert hasil.stdout.strip() == "0"


def test_galat_lain_bukan_lulus() -> None:
    """R-03 (M-1): hanya SQLSTATE yang diharapkan."""
    p = Percobaan("peran_pemanggil_llm", BASIS_DATA, "SELEKSI rusak", "42501", "pernyataan rusak")
    hasil = jalankan(coba(_konteks(), p))
    assert hasil.keadaan is Keadaan.GAGAL
    assert "42601" in hasil.rincian[0]


def test_tersambung_padahal_semestinya_ditolak_dilaporkan_gagal() -> None:
    p = Percobaan("peran_pseudonim", BASIS_DATA_PSEUDONIM, None, "42501", "tersambung")
    hasil = jalankan(coba(_konteks(), p))
    assert hasil.keadaan is Keadaan.GAGAL
    assert "tersambung" in hasil.rincian[0]


def test_sambungan_gagal_dilaporkan_gagal_bukan_lulus() -> None:
    async def gagal(peran: str, basis_data: str) -> object:
        raise OSError("tidak terjangkau")

    konteks = Konteks(buka=gagal, api=None, akar_repo=AKAR)
    p = Percobaan("peran_penjawaban", BASIS_DATA_PSEUDONIM, None, "42501", "tersambung")
    hasil = jalankan(coba(konteks, p))
    assert hasil.keadaan is Keadaan.GAGAL
    assert "OSError" in hasil.rincian[0] and "terjangkau" not in hasil.rincian[0]
