"""Uji enum Area — R-03, ADR-06, D-14 Bagian 5.1.

`dokumen_sumber.area_simpan` pada D-14 Bagian 5.1 menetapkan dua nilai dengan
catatan tegas "kredensial berbeda; bukan sekadar penanda". Enum ini wujudnya di
dalam kode. Nilai ketiga menuntut D-14 diubah lebih dulu — AG-04 melarang agen
mengubah daftar nilai enum.
"""

import pytest
from src.penyimpanan.area import Area


def test_hanya_dua_area() -> None:
    assert {a.value for a in Area} == {"karantina", "korpus"}


def test_nilai_persis_seperti_d14() -> None:
    """Ejaannya mengikuti dokumen, bukan selera penulis kode. Bila berbeda,
    nilai tersimpan tidak cocok dengan kamus data, dan penyimpangan itu baru
    terlihat saat migrasi."""
    assert Area.KARANTINA.value == "karantina"
    assert Area.KORPUS.value == "korpus"


def test_nilai_asing_ditolak() -> None:
    with pytest.raises(ValueError):
        Area("arsip")


def test_area_dapat_dijadikan_anggota_himpunan() -> None:
    """Kredensial menyimpan area sebagai himpunan (A-2)."""
    assert Area.KARANTINA not in {Area.KORPUS}
