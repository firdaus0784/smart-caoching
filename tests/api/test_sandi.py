"""Uji turunan sandi — T-3 fitur 029, R-03, P-3, plan Bagian 4.

Sebagian besar uji memakai parameter **murah** yang disuntikkan: parameter
sungguhan menghabiskan 0,3 detik per turunan, dan rangkaian uji yang lambat
adalah rangkaian uji yang dilewati orang. Parameter sungguhan diuji tepat pada
yang hanya dapat dibuktikan dengannya — bahwa ia berjalan sama sekali.
"""

from __future__ import annotations

import string

import pytest
from src.api.sandi import (
    ALFABET_SANDI,
    BATAS_PANJANG_SANDI,
    PARAMETER,
    ParameterScrypt,
    SandiTidakSah,
    bangkitkan_sandi,
    cocok,
    turunkan,
)

MURAH = ParameterScrypt(n=2**4, r=8, p=1)


def test_parameter_sungguhan_sesuai_plan() -> None:
    """P-4, KB-153: N=2^15, r=8, p=3 — baris ketiga OWASP."""
    assert (PARAMETER.n, PARAMETER.r, PARAMETER.p) == (2**15, 8, 3)


def test_parameter_sungguhan_berjalan() -> None:
    """KB-152: OpenSSL 3 menolak parameter ini dengan `memory limit exceeded`
    bila batas memori tidak ditetapkan tegas. Tanpa uji ini kegagalannya baru
    terlihat ketika tim membuat akun pertama di mesin penyebaran."""
    tersimpan = turunkan("abcd-efgh-jkmn-pqrs")
    assert cocok("abcd-efgh-jkmn-pqrs", tersimpan)
    assert not cocok("abcd-efgh-jkmn-pqrt", tersimpan)


def test_turunan_memuat_parameter_dan_garamnya() -> None:
    """Parameter disimpan di dalam turunan: menaikkannya kelak tidak membuat
    sandi lama tidak dapat diperiksa."""
    tersimpan = turunkan("rahasia", parameter=MURAH)
    nama, n, r, p, garam, turunan = tersimpan.split("$")
    assert (nama, n, r, p) == ("scrypt", "16", "8", "1")
    assert garam and turunan
    assert "rahasia" not in tersimpan


def test_parameter_lama_tetap_dapat_diperiksa() -> None:
    lama = turunkan("rahasia", parameter=ParameterScrypt(n=2**5, r=8, p=2))
    assert cocok("rahasia", lama)


def test_sandi_sama_berturunan_berbeda() -> None:
    """Garam per akun: dua akun bersandi sama tidak terbaca sama dari basis data."""
    assert turunkan("rahasia", parameter=MURAH) != turunkan("rahasia", parameter=MURAH)


def test_sandi_salah_tidak_cocok() -> None:
    tersimpan = turunkan("rahasia", parameter=MURAH)
    assert cocok("rahasia", tersimpan)
    assert not cocok("Rahasia", tersimpan)
    assert not cocok("", tersimpan)


def test_tanda_hubung_diabaikan() -> None:
    """Sandi dibagikan berkelompok `xxxx-xxxx-…` agar dapat dibaca; orang yang
    mengetiknya tanpa tanda hubung tetap masuk (plan Bagian 4.2)."""
    tersimpan = turunkan("abcd-efgh-jkmn-pqrs", parameter=MURAH)
    assert cocok("abcdefghjkmnpqrs", tersimpan)
    assert cocok("abcd-efgh-jkmn-pqrs", tersimpan)


def test_sandi_terlalu_panjang_ditolak_sebelum_diturunkan(monkeypatch: pytest.MonkeyPatch) -> None:
    """Penolakan layanan lewat sandi sangat panjang: batasnya diperiksa
    **sebelum** fungsi derivasi dipanggil, bukan sesudahnya."""
    import src.api.sandi as modul

    def _tidak_boleh(*_a: object, **_k: object) -> bytes:
        raise AssertionError("turunan dijalankan atas sandi yang terlalu panjang")

    monkeypatch.setattr(modul.hashlib, "scrypt", _tidak_boleh)
    terlalu = "a" * (BATAS_PANJANG_SANDI + 1)
    with pytest.raises(SandiTidakSah):
        turunkan(terlalu, parameter=MURAH)
    with pytest.raises(SandiTidakSah):
        cocok(terlalu, "scrypt$16$8$1$AAAA$AAAA")


def test_batas_panjang_tepat_masih_diterima() -> None:
    tepat = "a" * BATAS_PANJANG_SANDI
    assert cocok(tepat, turunkan(tepat, parameter=MURAH))


@pytest.mark.parametrize(
    "rusak", ["", "bcrypt$16$8$1$AAAA$AAAA", "scrypt$16$8$1$AAAA", "scrypt$x$8$1$AAAA$AAAA"]
)
def test_turunan_tersimpan_yang_rusak_ditolak_terang(rusak: str) -> None:
    """Turunan rusak adalah kerusakan data, bukan sandi salah — ia tidak boleh
    terbaca sebagai penolakan biasa yang diam."""
    with pytest.raises(ValueError):
        cocok("rahasia", rusak)


def test_sandi_bangkitan_berbentuk_kelompok_empat() -> None:
    sandi = bangkitkan_sandi()
    kelompok = sandi.split("-")
    assert [len(k) for k in kelompok] == [4, 4, 4, 4]


def test_alfabet_tiga_puluh_satu_tanpa_huruf_yang_tertukar() -> None:
    """Sekitar 79 bit; tanpa `0 O 1 l I`, dan tanpa `o i` yang tertukar
    dengan angka pada huruf kecil."""
    assert len(ALFABET_SANDI) == len(set(ALFABET_SANDI)) == 31
    assert not set("0O1lIoi") & set(ALFABET_SANDI)
    assert set(ALFABET_SANDI) <= set(string.ascii_lowercase + string.digits)


def test_sandi_bangkitan_memakai_alfabet_dan_acak() -> None:
    contoh = {bangkitkan_sandi() for _ in range(50)}
    assert len(contoh) == 50
    for sandi in contoh:
        assert set(sandi.replace("-", "")) <= set(ALFABET_SANDI)
    # Seluruh alfabet terpakai pada 50 kali 16 karakter; pembangkit yang hanya
    # memakai sebagian alfabet mengurangi keacakan tanpa terlihat.
    assert set("".join(contoh).replace("-", "")) == set(ALFABET_SANDI)
