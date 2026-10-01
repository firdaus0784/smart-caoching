"""Identitas dan pemilik — T-4 fitur 028, R-06, R-17, P-1, TK-67.

Sampai fitur 028 penentu identitas hanya mengembalikan peran, sehingga
riwayat tidak dapat tahu milik siapa sebuah percakapan (TK-67). `Identitas`
membawa pemilik berpseudonim di samping peran; autentikasi kelak mengisinya
tanpa menyentuh riwayat.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.api.identitas import Identitas, PenentuIdentitas
from src.api.peran import Peran
from tests.konftes_asinkron import jalankan

from perkakas.jalankan_lokal import PEMILIK_PENGEMBANGAN, IdentitasPengembangan


def test_identitas_membawa_peran_dan_pemilik() -> None:
    satu = Identitas(peran=Peran.PENGGUNA, pemilik="ps_a1b2")
    assert satu.peran is Peran.PENGGUNA
    assert satu.pemilik == "ps_a1b2"


def test_identitas_beku() -> None:
    satu = Identitas(peran=Peran.PENGGUNA, pemilik="ps_a1b2")
    with pytest.raises(ValidationError):
        satu.pemilik = "ps_lain"  # type: ignore[misc]


@pytest.mark.parametrize("pemilik", ["", "   "])
def test_pemilik_kosong_ditolak(pemilik: str) -> None:
    with pytest.raises(ValidationError, match="pemilik"):
        Identitas(peran=Peran.PENGGUNA, pemilik=pemilik)


@pytest.mark.parametrize(
    ("pemilik", "jenis"), [("3201234567890123", "nik"), ("081234567890", "telepon")]
)
def test_pemilik_berpola_data_pribadi_ditolak_tanpa_mengutip(pemilik: str, jenis: str) -> None:
    """R-06, C-05: pemilik adalah pseudonim, bukan identitas langsung. Pesan
    menyebut jenisnya dan tidak mengulang nilainya (KB-049)."""
    with pytest.raises(ValidationError) as galat:
        Identitas(peran=Peran.PENGGUNA, pemilik=pemilik)
    assert jenis in str(galat.value)
    assert pemilik not in str(galat.value)


def test_bidang_tambahan_ditolak() -> None:
    with pytest.raises(ValidationError):
        Identitas(peran=Peran.PENGGUNA, pemilik="ps_a", id_pengguna="7")  # type: ignore[call-arg]


def test_identitas_pengembangan_menyatakan_dirinya() -> None:
    """R-17: satu pemilik tetap, dan namanya menyatakan pengembangan."""
    identitas = jalankan(IdentitasPengembangan().identitas(object()))  # type: ignore[arg-type]
    assert identitas == Identitas(peran=Peran.PENGGUNA, pemilik=PEMILIK_PENGEMBANGAN)
    assert "pengembangan" in PEMILIK_PENGEMBANGAN


def test_identitas_pengembangan_memenuhi_protokol() -> None:
    assert isinstance(IdentitasPengembangan(), PenentuIdentitas)
