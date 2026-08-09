"""Uji uraian modul praproses — C-4 fitur 015, R-03, C-10, D-03 Bagian 15.

Bukan pekerjaan dokumentasi. Batas kegunaan keluaran praproses tidak dapat
ditegakkan mesin: tidak ada pemeriksa yang dapat mencegah seseorang memakai
daftar token sebagai bahan anotasi. Yang tersedia hanyalah membuat batas itu
tidak dapat dilewatkan oleh pembacanya.

Bentuknya sama dengan uji uraian pemeriksa pola adversarial pada fitur 002,
dan alasannya sama: modul yang tidak menyatakan batasnya akan dipakai
melampaui batasnya, dan yang memakainya tidak akan merasa melakukan sesuatu
yang keliru.
"""

import pytest
import src.nlp.praproses.stemming as modul_stemming
import src.nlp.praproses.token as modul_token
import src.nlp.praproses.tokenisasi as modul_tokenisasi

MODUL = (modul_token, modul_tokenisasi, modul_stemming)


@pytest.mark.parametrize("modul", MODUL, ids=lambda m: m.__name__)
def test_setiap_modul_menyebut_kode_kebutuhannya(modul: object) -> None:
    uraian = modul.__doc__ or ""
    assert "C-10" in uraian


def test_batas_kegunaan_dinyatakan_pada_modul_yang_menghasilkannya() -> None:
    """**Uji terpenting berkas ini.**

    Dinyatakan pada `tokenisasi` dan `stemming` — dua modul yang keluarannya
    menggoda dipakai sebagai teks. `token` tidak dituntut menyebutnya: ia
    tipe, bukan penghasil.
    """
    for modul in (modul_tokenisasi, modul_stemming):
        uraian = (modul.__doc__ or "").lower()
        assert "pencarian" in uraian, modul.__name__
        assert "anotasi" in uraian, modul.__name__


def test_alasan_indeks_karakter_dirujuk_ke_pemiliknya() -> None:
    """D-00 Bagian 3: dokumen lain merujuk, tidak menyalin.

    Alasan indeks karakter dimiliki D-03 Bagian 15. Uraian yang menyalinnya
    akan tertinggal ketika D-03 berubah.
    """
    uraian = modul_stemming.__doc__ or ""
    assert "D-03" in uraian


def test_aturan_stemming_dinyatakan_bukan_hanya_dilaksanakan() -> None:
    """Kode yang membentuk token baru dengan rentang lama tampak berlebihan
    bagi pembaca yang tidak tahu alasannya, dan yang tampak berlebihan akan
    disederhanakan seseorang."""
    uraian = (modul_stemming.__doc__ or "").lower()
    assert "permukaan" in uraian
    assert "rentang lama" in uraian


def test_batas_penurunan_huruf_dinyatakan() -> None:
    """Penurunan huruf aman untuk Bahasa Indonesia, tidak untuk semua bahasa.

    Batas yang tidak tertulis akan dilampaui ketika korpus berkembang, dan
    pelanggarannya berupa panjang teks yang berubah — persis yang C-10
    larang.
    """
    assert "bahasa lain" in (modul_tokenisasi.__doc__ or "").lower()
