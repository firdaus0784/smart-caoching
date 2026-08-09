"""Uji antarmuka ekstraksi — B-2 fitur 015, R-01, R-03, C-10.

`TeksKanonik` bukan pembungkus hiasan atas `str`. Ia yang membuat dua hal
tidak dapat terjadi: teks kosong yang lolos sebagai dokumen sah, dan indeks
karakter yang menunjuk ke teks hasil praproses alih-alih ke teks asli.
"""

import inspect
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.ingest.ekstraksi.dasar import Pengekstrak, TeksKanonik

ISI = "Kepala sekolah menugaskan wakil kurikulum menyusun jadwal supervisi."


def _teks() -> TeksKanonik:
    return TeksKanonik(isi=ISI, asal="berlapis-teks.pdf", pengekstrak="uji")


def test_teks_kanonik_beku() -> None:
    """Teks yang dapat diubah setelah diekstrak membuat setiap rentang
    karakter yang menunjuk kepadanya kehilangan arti."""
    with pytest.raises(ValidationError):
        _teks().isi = "lain"  # type: ignore[misc]


def test_teks_kanonik_menolak_isi_kosong() -> None:
    """**Uji terpenting berkas ini.**

    Dokumen berteks kosong lolos seluruh gerbang fitur 002 tanpa satu pun
    berbunyi: tidak ada pola adversarial pada teks kosong, dan tidak ada data
    pribadi pada teks kosong. Menolaknya di sini berarti tidak ada pengekstrak
    yang **dapat** menghasilkannya, walau penulisnya lupa memeriksa.
    """
    with pytest.raises(ValidationError):
        TeksKanonik(isi="", asal="a.pdf", pengekstrak="uji")


def test_teks_kanonik_menolak_isi_hanya_ruang_kosong() -> None:
    """Untai berisi spasi dan baris baru sama tidak berisinya dengan untai
    kosong, dan justru lebih mungkin lolos pemeriksaan yang ditulis terburu."""
    for isi in (" ", "\n\n", "\t \r\n "):
        with pytest.raises(ValidationError):
            TeksKanonik(isi=isi, asal="a.pdf", pengekstrak="uji")


def test_teks_kanonik_tidak_memangkas_isinya() -> None:
    """Memangkas mengubah indeks karakter setiap temuan sesudahnya.

    Ini yang membedakan penolakan dari pembersihan: yang kosong ditolak, yang
    berisi diterima **apa adanya**.
    """
    berisi_awalan = "\n  Notulen rapat pleno.\n"
    assert TeksKanonik(isi=berisi_awalan, asal="a.pdf", pengekstrak="uji").isi == berisi_awalan


def test_asal_dan_pengekstrak_wajib() -> None:
    """C-09 menuntut keluaran dapat ditelusuri ke penghasilnya. Teks tanpa
    keterangan asal tidak dapat diperiksa ulang oleh siapa pun."""
    with pytest.raises(ValidationError):
        TeksKanonik(isi=ISI)  # type: ignore[call-arg]


def test_teks_kanonik_bukan_str() -> None:
    """Bila ia mewarisi `str`, seluruh kode di hilir dapat memperlakukannya
    sebagai untai biasa dan penjagaan di atas menguap."""
    assert not isinstance(_teks(), str)


def test_pengekstrak_abstrak_tidak_dapat_dibentuk() -> None:
    with pytest.raises(TypeError):
        Pengekstrak()  # type: ignore[abstract]


def test_setiap_metode_ekstrak_mengembalikan_teks_kanonik() -> None:
    """Dinyatakan pada tanda tangannya, bukan diperiksa saat jalan.

    Pengekstrak yang mengembalikan `str` telanjang akan lolos uji perilaku mana
    pun yang hanya membandingkan isi.
    """
    tanda = inspect.signature(Pengekstrak.ekstrak)
    assert tanda.return_annotation in (TeksKanonik, "TeksKanonik")


def test_ekstrak_menerima_jalur_bukan_untai() -> None:
    """Jalur sebagai untai mengundang perakitan jalur dengan penggabungan
    untai, dan itu jalan menuju pembacaan berkas di luar area yang dimaksud."""
    tanda = inspect.signature(Pengekstrak.ekstrak)
    assert tanda.parameters["jalur"].annotation in (Path, "Path")


def test_panjang_dihitung_dalam_karakter() -> None:
    """C-10 — bukan bita, bukan token.

    Diuji dengan teks ber-aksen agar perbedaan karakter dan bita benar-benar
    muncul; pada ASCII keduanya sama dan uji lulus tanpa menguji apa pun.
    """
    teks = TeksKanonik(isi="Ké", asal="a.pdf", pengekstrak="uji")
    assert len(teks) == 2
    assert len(teks.isi.encode("utf-8")) == 3
