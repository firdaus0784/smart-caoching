"""Uji antarmuka penyimpan — R-01, R-02, C-03, ADR-06, ADR-12.

Kredensial yang diterima sebagai parameter opsional akan berubah menjadi
"tanpa kredensial berarti tanpa batas" pada pemanggilan pertama yang lupa
mengisinya, dan pemanggilan yang lupa itu tidak menggagalkan uji mana pun
kecuali uji ini ada.
"""

import inspect
from abc import ABC

from src.penyimpanan.dasar import PenyimpanDasar

METODE_WAJIB = ("baca_dokumen", "tulis_dokumen", "pindahkan")


def test_penyimpan_dasar_abstrak() -> None:
    assert issubclass(PenyimpanDasar, ABC)
    assert getattr(PenyimpanDasar, "__abstractmethods__", frozenset())


def test_seluruh_metode_wajib_ada() -> None:
    for nama in METODE_WAJIB:
        assert hasattr(PenyimpanDasar, nama), nama


def test_setiap_metode_menerima_kredensial() -> None:
    """R-01 — tanpa ini, C-03 tidak punya tempat ditegakkan."""
    for nama in METODE_WAJIB:
        assert "kredensial" in inspect.signature(getattr(PenyimpanDasar, nama)).parameters


def test_kredensial_tidak_berparameter_bawaan() -> None:
    for nama in METODE_WAJIB:
        p = inspect.signature(getattr(PenyimpanDasar, nama)).parameters["kredensial"]
        assert p.default is inspect.Parameter.empty, nama


def test_kredensial_bukan_parameter_terakhir_yang_mudah_terlewat() -> None:
    """Menempatkannya di akhir daftar membuatnya terbaca sebagai renungan
    belakangan, dan yang terbaca begitu akan diperlakukan begitu."""
    for nama in METODE_WAJIB:
        p = list(inspect.signature(getattr(PenyimpanDasar, nama)).parameters)
        assert p[:2] == ["self", "kredensial"], (nama, p)


def test_tidak_dapat_dibentuk_tanpa_melengkapi_metode() -> None:
    class Setengah(PenyimpanDasar):
        pass

    try:
        Setengah()  # type: ignore[abstract]
    except TypeError:
        return
    raise AssertionError("kelas tanpa metode lengkap seharusnya tidak dapat dibentuk")
