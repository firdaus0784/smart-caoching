"""Uji Kappa per kategori — B-3 fitur 003, R-07, D-03 Bagian 11 dan KM-03.

D-03 Bagian 11 menuntut Kappa dihitung **juga per kategori**, satu lawan
sisanya, "untuk menemukan kategori yang batasnya kabur". Kalimat berikutnya
yang menentukan bentuk modul ini: kategori dengan Kappa rendah berulang
menandakan **definisinya perlu dipertajam, bukan anotatornya perlu ditegur**.

Karena itu hasilnya dipetakan per kategori dan dibawa utuh, bukan diringkas
menjadi satu angka terburuk. Angka terburuk memberi tahu ada yang salah;
petanya memberi tahu di mana.
"""

import pytest
from src.nlp.anotasi.kesepakatan import kappa_kategori, kappa_per_kategori
from src.nlp.anotasi.rentang import PutusanKategori
from src.nlp.anotasi.skema import KategoriMasalah, VersiSkema

VERSI = VersiSkema(mayor=1, minor=0)
K1, K5, K7 = KategoriMasalah.K1, KategoriMasalah.K5, KategoriMasalah.K7


def _pasangan(pola: list[tuple[KategoriMasalah, KategoriMasalah]]):
    a = [
        PutusanKategori(
            id_dokumen=f"dok_{i}", kategori_utama=x, versi_skema=VERSI, id_anotator="ant_a"
        )
        for i, (x, _) in enumerate(pola)
    ]
    b = [
        PutusanKategori(
            id_dokumen=f"dok_{i}", kategori_utama=y, versi_skema=VERSI, id_anotator="ant_b"
        )
        for i, (_, y) in enumerate(pola)
    ]
    return a, b


def test_setiap_kategori_yang_muncul_punya_hasilnya() -> None:
    a, b = _pasangan([(K1, K1)] * 10 + [(K5, K5)] * 10 + [(K7, K1)] * 5)
    peta = kappa_per_kategori(a, b)
    assert {K1, K5, K7} <= set(peta)


def test_kategori_yang_tidak_muncul_tidak_dilaporkan() -> None:
    """Melaporkan kategori yang tidak seorang pun pakai menghasilkan delapan
    baris yang tujuh di antaranya kosong, dan pembacanya berhenti membaca."""
    a, b = _pasangan([(K1, K1)] * 10 + [(K5, K5)] * 10)
    assert set(kappa_per_kategori(a, b)) == {K1, K5}


def test_kategori_yang_batasnya_kabur_bernilai_lebih_rendah() -> None:
    """**Uji terpenting berkas ini** — inilah gunanya perhitungan per kategori.

    K1 dan K5 disepakati sempurna. K7 kacau: lima dokumen, dan anotator kedua
    menyebutnya K1 pada seluruhnya. Kappa keseluruhan tetap tinggi karena
    mayoritas dokumen sepakat, sementara Kappa K7 jatuh — dan itu yang
    menunjukkan definisi K7 perlu dipertajam.
    """
    a, b = _pasangan([(K1, K1)] * 20 + [(K5, K5)] * 20 + [(K7, K1)] * 5)
    peta = kappa_per_kategori(a, b)
    keseluruhan = kappa_kategori(a, b)

    assert keseluruhan.nilai is not None
    assert peta[K7].nilai is not None
    assert peta[K7].nilai < keseluruhan.nilai
    assert peta[K5].nilai == pytest.approx(1.0)


def test_satu_lawan_sisanya_dihitung_tangan() -> None:
    """K1 lawan bukan-K1 atas 40 dokumen.

    A menyebut K1 pada 20, B menyebut K1 pada 25 (20 sepakat + 5 dari K7).
    Tabel: keduanya K1 = 20; A K1 B bukan = 0; A bukan B K1 = 5;
    keduanya bukan = 15.
    po = (20 + 15) / 40 = 0,875
    Sisi A: K1 = 20/40 = 0,5; bukan = 0,5
    Sisi B: K1 = 25/40 = 0,625; bukan = 0,375
    pe = 0,5 * 0,625 + 0,5 * 0,375 = 0,3125 + 0,1875 = 0,5
    kappa = (0,875 - 0,5) / (1 - 0,5) = 0,75
    """
    a, b = _pasangan([(K1, K1)] * 20 + [(K5, K5)] * 15 + [(K7, K1)] * 5)
    assert kappa_per_kategori(a, b)[K1].nilai == pytest.approx(0.75)


def test_kategori_yang_dipakai_seluruh_dokumen_belum_terhitung() -> None:
    """Satu lawan sisanya ketika tidak ada "sisanya" berarti pe = 1.

    Sama dengan keadaan pada Kappa keseluruhan, dan diperlakukan sama:
    belum terhitung, bukan 1,0.
    """
    a, b = _pasangan([(K1, K1)] * 10)
    hasil = kappa_per_kategori(a, b)[K1]
    assert not hasil.terhitung


def test_tanpa_dokumen_bersama_menghasilkan_peta_kosong() -> None:
    """Peta kosong, bukan peta berisi delapan hasil yang belum terhitung.

    Yang kedua terbaca sebagai "sudah diperiksa dan hasilnya nihil", padahal
    tidak ada yang diperiksa sama sekali.
    """
    a, _ = _pasangan([(K1, K1)])
    assert kappa_per_kategori(a, []) == {}


def test_versi_skema_berbeda_menghasilkan_peta_kosong() -> None:
    """Perlakuan yang sama dengan Kappa keseluruhan — bukan sebagian dihitung
    dan sebagian tidak."""
    lain = VersiSkema(mayor=2, minor=0)
    a = [
        PutusanKategori(
            id_dokumen="dok_0", kategori_utama=K1, versi_skema=VERSI, id_anotator="ant_a"
        )
    ]
    b = [
        PutusanKategori(
            id_dokumen="dok_0", kategori_utama=K1, versi_skema=lain, id_anotator="ant_b"
        )
    ]
    assert kappa_per_kategori(a, b) == {}
