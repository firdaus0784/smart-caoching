"""Uji tiga kredensial baku — R-01, R-01a, R-01b, C-03, C-05, KD-10.

Di sinilah C-03 benar-benar diwujudkan. Uji ditulis sebagai pernyataan tentang
apa yang **tidak boleh ada**; kredensial yang kelebihan kemampuan tidak
menggagalkan uji yang hanya memeriksa kemampuan yang diharapkan.
"""

from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.kredensial_baku import (
    PEMANGGIL_LLM,
    PENJAWABAN,
    SELURUH_KREDENSIAL,
    VERIFIKASI,
)


def test_penjawaban_tidak_dapat_membaca_karantina() -> None:
    """C-03, R-01a — inti seluruh fitur ini."""
    assert not PENJAWABAN.boleh_baca(Area.KARANTINA)


def test_pemanggil_llm_tidak_dapat_membaca_karantina() -> None:
    """KD-10 menyebutnya terpisah; peran berbeda dapat keliru sendiri-sendiri."""
    assert not PEMANGGIL_LLM.boleh_baca(Area.KARANTINA)


def test_pemanggil_llm_tidak_dapat_menulis_ke_mana_pun() -> None:
    """R-01b, KD-10, NFR-21."""
    assert PEMANGGIL_LLM.tulis == frozenset()


def test_hanya_verifikasi_yang_menjangkau_karantina() -> None:
    """Sifat seluruh daftar, bukan tiga pernyataan terpisah. Kredensial
    keempat yang ditambahkan kelak tertangkap di sini."""
    penjangkau = {k.nama for k in SELURUH_KREDENSIAL if k.boleh_baca(Area.KARANTINA)}
    assert penjangkau == {VERIFIKASI.nama}


def test_penjawaban_dapat_membaca_korpus() -> None:
    """Pemisahan yang menutup segalanya bukan pemisahan melainkan kelumpuhan."""
    assert PENJAWABAN.boleh_baca(Area.KORPUS)


def test_penjawaban_tidak_dapat_menulis() -> None:
    """C-17 — tanpa akses tulis dari jalur penjawaban."""
    assert PENJAWABAN.tulis == frozenset()


def test_ketiganya_bernama_berbeda() -> None:
    nama = [k.nama for k in SELURUH_KREDENSIAL]
    assert len(nama) == len(set(nama))


def test_seluruh_kredensial_memuat_ketiganya() -> None:
    assert set(SELURUH_KREDENSIAL) == {PENJAWABAN, VERIFIKASI, PEMANGGIL_LLM}


def test_tidak_ada_yang_menulis_ke_kedua_area() -> None:
    """Yang menulis ke karantina adalah ingesti; yang memindahkan ke korpus
    adalah verifikasi."""
    for k in SELURUH_KREDENSIAL:
        assert k.tulis != frozenset(Area), k.nama


def test_seluruhnya_bertipe_kredensial() -> None:
    for k in SELURUH_KREDENSIAL:
        assert isinstance(k, Kredensial)
