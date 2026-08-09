"""Uji uraian pendeteksi data pribadi — E-3 fitur 015, R-12.

Bukan pekerjaan dokumentasi. Cakupan pendeteksi tidak dapat disimpulkan dari
keluarannya: laporan yang bersih terbaca sama persis, apakah karena dokumennya
memang bersih atau karena yang dicari tidak dicari.

Bentuknya sama dengan uji uraian pemeriksa pola adversarial fitur 002, dan
akibat kelalaiannya di sini lebih tajam: nama orang yang tidak tersamarkan
lolos ke korpus karena seseorang mengira modul ini menanganinya.
"""

import src.nlp.anonimisasi.pola as modul


def test_uraian_menyebut_yang_tidak_dideteksi_dengan_contohnya() -> None:
    """**R-12.** Bentuk yang sama dengan uraian pemeriksa pola adversarial.

    Menyebut jenisnya saja belum cukup: pembaca menilai ketebalan lapisan dari
    contoh, bukan dari daftar istilah.
    """
    uraian = (modul.__doc__ or "").lower()
    assert "nama perorangan" in uraian
    assert "alamat" in uraian
    assert "siti" in uraian, "contoh nama yang lolos wajib tertulis"
    assert "jalan" in uraian, "contoh alamat yang lolos wajib tertulis"


def test_uraian_menunjuk_keputusan_dan_butir_terbukanya() -> None:
    """Kekurangan tanpa penunjuk menjadi kekurangan yang tidak ada pemiliknya."""
    uraian = modul.__doc__ or ""
    assert "BT-70" in uraian
    assert "KB-017" in uraian
    assert "fitur 004" in uraian


def test_uraian_menyebut_yang_menahan_sementara_ini() -> None:
    """Menyatakan kekurangan tanpa menyatakan penggantinya membuat pembaca
    menyimpulkan tidak ada yang menahan sama sekali."""
    uraian = modul.__doc__ or ""
    assert "FR-B05" in uraian
    assert "fitur 002" in uraian
