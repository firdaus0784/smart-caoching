"""Uji stemming dan stop-word — C-3 fitur 015, R-07, R-08.

Satu sifat menaungi berkas ini, dan ia kelanjutan langsung dari C-2:

**stemming mengubah `stem`, tidak pernah `permukaan`, `mulai`, maupun
`akhir`.**

Di sinilah C-10 paling mudah runtuh. "menugaskan" menjadi "tugas" — lima
karakter lebih pendek — dan versi yang menuliskan hasil stem kembali ke
permukaan akan membuat setiap rentang sesudahnya menunjuk kata yang salah,
tanpa satu galat pun.
"""

import itertools
from pathlib import Path

import pytest
from src.ingest.ekstraksi.docx import PengekstrakDocx
from src.nlp.praproses.stemming import STOP_WORD, stemkan, tanpa_stop_word
from src.nlp.praproses.tokenisasi import tokenkan

BAHAN = Path(__file__).resolve().parents[1] / "bahan"

KALIMAT = "Kepala sekolah menugaskan wakil kurikulum menyusun jadwal supervisi akademik"


def test_stemming_mengubah_stem() -> None:
    hasil = {t.permukaan: t.stem for t in stemkan(tokenkan(KALIMAT))}
    assert hasil["menugaskan"] == "tugas"
    assert hasil["menyusun"] == "susun"


def test_stemming_tidak_menyentuh_permukaan_dan_rentang() -> None:
    """**Sifat terpenting berkas ini.**"""
    sebelum = tokenkan(KALIMAT)
    sesudah = stemkan(sebelum)
    assert len(sebelum) == len(sesudah)
    for lama, baru in zip(sebelum, sesudah, strict=True):
        assert baru.permukaan == lama.permukaan
        assert (baru.mulai, baru.akhir) == (lama.mulai, lama.akhir)


def test_rentang_tetap_menunjuk_permukaannya_sesudah_stemming() -> None:
    """Dinyatakan ulang terhadap teks aslinya, bukan hanya terhadap token
    sebelumnya — itu yang benar-benar dituntut C-10."""
    for t in stemkan(tokenkan(KALIMAT)):
        assert KALIMAT[t.mulai : t.akhir] == t.permukaan


def test_sifat_berlaku_atas_bahan_uji_sungguhan() -> None:
    teks = PengekstrakDocx().ekstrak(BAHAN / "notulen.docx").isi
    token = stemkan(tokenkan(teks))
    assert token
    for t in token:
        assert teks[t.mulai : t.akhir] == t.permukaan


def test_stop_word_dibuang_bukan_dikosongkan() -> None:
    """Token stop-word yang dikosongkan tetap menempati rentangnya, sehingga
    ia tetap muncul sebagai kata kosong pada setiap pemakaian berikutnya."""
    token = tokenkan("Kepala sekolah yang dan atau menugaskan")
    tersisa = tanpa_stop_word(token)
    permukaan = [t.permukaan for t in tersisa]
    assert "yang" not in permukaan
    assert "menugaskan" in permukaan
    assert all(t.permukaan for t in tersisa)


def test_pembuangan_stop_word_tidak_menggeser_rentang_yang_tersisa() -> None:
    """**Ini yang membedakan pembuangan token dari pemotongan teks.**

    Yang dibuang adalah tokennya, bukan karakternya. Teks kanonik tidak
    berubah sama sekali, sehingga rentang token yang tersisa tetap sah.
    """
    teks = "Kepala sekolah yang menugaskan wakil"
    for t in tanpa_stop_word(tokenkan(teks)):
        assert teks[t.mulai : t.akhir] == t.permukaan


def test_urutan_token_terjaga_sesudah_pembuangan() -> None:
    teks = "Kepala sekolah yang dan menugaskan wakil kurikulum"
    tersisa = tanpa_stop_word(tokenkan(teks))
    for sebelum, sesudah in itertools.pairwise(tersisa):
        assert sebelum.mulai < sesudah.mulai


def test_stop_word_tidak_kosong_dan_berbahasa_indonesia() -> None:
    """Daftar kosong membuat `tanpa_stop_word` menjadi fungsi yang tidak
    melakukan apa-apa sambil tampak melakukannya."""
    assert len(STOP_WORD) > 50
    assert {"yang", "dan", "dengan", "untuk"} <= STOP_WORD


def test_stop_word_tidak_memuat_kata_manajerial_penting() -> None:
    """Daftar stop-word bawaan disusun untuk teks umum, bukan untuk dokumen
    manajerial.

    Kata yang menjadi inti kategori D-03 tidak boleh terbuang, karena
    pengambilan yang kehilangan kata "kepala" tidak dapat menemukan dokumen
    tentang kepala sekolah.
    """
    for kata in ("kepala", "sekolah", "guru", "anggaran", "supervisi", "mutu"):
        assert kata not in STOP_WORD, kata


def test_daftar_kosong_menghasilkan_daftar_kosong() -> None:
    assert stemkan([]) == []
    assert tanpa_stop_word([]) == []


@pytest.mark.parametrize("kata", ["pembelajaran", "mengkoordinasikan", "keputusan"])
def test_stem_tidak_pernah_kosong(kata: str) -> None:
    """Pemenggal yang mengembalikan untai kosong pada kata tertentu akan
    membuat `Token` gagal dibentuk, dan seluruh dokumen ikut gagal."""
    assert all(t.stem for t in stemkan(tokenkan(kata)))
