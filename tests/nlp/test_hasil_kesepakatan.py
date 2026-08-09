"""Uji bentuk hasil kesepakatan — B-1 fitur 003, R-07, R-08.

Satu bentuk, satu maksud: **angka yang lahir dari ketiadaan tidak boleh
terbaca sebagai angka.**

Kesepakatan yang dilaporkan 1,0 karena tidak ada yang dibandingkan adalah
angka yang akan disalin ke naskah sebagai bukti mutu. Bentuk yang mencegahnya
sama dengan `HasilSistem` fitur 015 dan dengan "belum dapat diperiksa" pada
`make compliance` — pola TA-01 yang muncul untuk kelima kalinya.
"""

import pytest
from pydantic import ValidationError
from src.nlp.anotasi.kesepakatan import HasilKesepakatan


def test_hasil_terhitung_membawa_nilainya() -> None:
    hasil = HasilKesepakatan(nilai=0.82, jumlah_satuan=100)
    assert hasil.terhitung
    assert hasil.nilai == 0.82


def test_hasil_belum_terhitung_bernilai_none() -> None:
    """**Uji terpenting berkas ini.**

    Bukan 0,0 dan bukan 1,0. Keduanya angka yang dapat dibaca sebagai hasil,
    dan yang dapat dibaca sebagai hasil akan dibaca sebagai hasil.
    """
    hasil = HasilKesepakatan.belum_terhitung("tidak ada dokumen anotasi ganda")
    assert not hasil.terhitung
    assert hasil.nilai is None
    assert hasil.alasan


def test_belum_terhitung_wajib_menyebut_alasannya() -> None:
    """Hasil kosong tanpa alasan membuat pembacanya menebak — dan tebakan yang
    paling mudah adalah "belum sempat dihitung", padahal sebabnya dapat
    berupa versi skema yang berbeda."""
    with pytest.raises(ValidationError):
        HasilKesepakatan(nilai=None, jumlah_satuan=0, alasan="")


def test_nilai_dan_alasan_tidak_dapat_berdiri_bersama() -> None:
    """Hasil yang membawa keduanya berarti dua cerita pada satu baris, dan
    pembaca akan memilih yang lebih menyenangkan."""
    with pytest.raises(ValidationError):
        HasilKesepakatan(nilai=0.9, jumlah_satuan=10, alasan="sebagian dilewati")


def test_jumlah_satuan_ikut_dibawa() -> None:
    """Kappa 0,9 atas tiga dokumen dan atas tiga ratus dokumen adalah dua
    pernyataan yang sangat berbeda, dan hanya yang kedua layak masuk naskah."""
    assert HasilKesepakatan(nilai=0.9, jumlah_satuan=3).jumlah_satuan == 3


def test_hasil_beku() -> None:
    with pytest.raises(ValidationError):
        HasilKesepakatan(nilai=0.5, jumlah_satuan=10).nilai = 0.9  # type: ignore[misc]


def test_nilai_di_luar_rentang_kappa_ditolak() -> None:
    """Kappa berkisar -1 sampai 1; F1 berkisar 0 sampai 1. Nilai di luar itu
    tanda rumusnya keliru, dan tanda itu tidak boleh lolos menjadi hasil."""
    with pytest.raises(ValidationError):
        HasilKesepakatan(nilai=1.4, jumlah_satuan=10)
    with pytest.raises(ValidationError):
        HasilKesepakatan(nilai=-2.0, jumlah_satuan=10)


def test_memenuhi_ambang_hanya_ketika_terhitung() -> None:
    """**Sifat yang menutup jalan pintas paling menggoda.**

    Hasil yang belum terhitung tidak memenuhi ambang apa pun. Tanpa aturan
    ini, batch tanpa anotasi ganda akan lolos pemeriksaan ambang karena
    tidak ada angka yang lebih kecil daripada ambangnya.
    """
    assert HasilKesepakatan(nilai=0.8, jumlah_satuan=50).memenuhi(0.7)
    assert not HasilKesepakatan(nilai=0.6, jumlah_satuan=50).memenuhi(0.7)
    assert not HasilKesepakatan.belum_terhitung("kurang bahan").memenuhi(0.0)
