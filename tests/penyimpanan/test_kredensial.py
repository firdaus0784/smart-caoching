"""Uji Kredensial — R-01, C-03, ADR-06.

Kredensial menyatakan kemampuan, bukan identitas. Dua sifat diuji karena
keduanya tempat C-03 paling mudah runtuh tanpa terlihat: kredensial yang dapat
diubah setelah dibentuk, dan himpunan kosong yang diperlakukan sebagai "semua".
"""

import pytest
from pydantic import ValidationError
from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial


def test_kredensial_membawa_dua_himpunan() -> None:
    k = Kredensial(nama="uji", baca=frozenset({Area.KORPUS}), tulis=frozenset(), indeks=frozenset())
    assert k.boleh_baca(Area.KORPUS)
    assert not k.boleh_tulis(Area.KORPUS)


def test_kredensial_tidak_dapat_diubah_setelah_dibentuk() -> None:
    k = Kredensial(nama="uji", baca=frozenset({Area.KORPUS}), tulis=frozenset(), indeks=frozenset())
    with pytest.raises(ValidationError):
        k.baca = frozenset({Area.KARANTINA})  # type: ignore[misc]


def test_himpunan_baca_tidak_dapat_ditambah_dari_luar() -> None:
    """Objek beku yang memuat himpunan yang dapat ditambah anggotanya tidak
    beku dalam arti yang berguna."""
    k = Kredensial(nama="uji", baca=frozenset({Area.KORPUS}), tulis=frozenset(), indeks=frozenset())
    with pytest.raises(AttributeError):
        k.baca.add(Area.KARANTINA)  # type: ignore[attr-defined]


def test_himpunan_kosong_berarti_tidak_boleh_apa_pun() -> None:
    """Bukan berarti semua. Kekeliruan ini cara paling sunyi meruntuhkan
    C-03: kredensial yang lupa diisi menjangkau seluruh area."""
    k = Kredensial(nama="kosong", baca=frozenset(), tulis=frozenset(), indeks=frozenset())
    for area in Area:
        assert not k.boleh_baca(area)
        assert not k.boleh_tulis(area)


def test_menulis_tidak_menyiratkan_membaca() -> None:
    k = Kredensial(
        nama="uji", baca=frozenset(), tulis=frozenset({Area.KARANTINA}), indeks=frozenset()
    )
    assert k.boleh_tulis(Area.KARANTINA)
    assert not k.boleh_baca(Area.KARANTINA)


def test_nama_wajib_terisi() -> None:
    """Nama dipakai pada catatan percobaan akses (A-7)."""
    with pytest.raises(ValidationError):
        Kredensial(nama="", baca=frozenset(), tulis=frozenset(), indeks=frozenset())
