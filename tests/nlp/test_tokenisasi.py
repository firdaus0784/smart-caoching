"""Uji tokenisasi dan normalisasi — C-2 fitur 015, R-07, R-08, C-10.

Satu sifat menaungi seluruh berkas ini:

    teks_kanonik[t.mulai:t.akhir] == t.permukaan   untuk setiap token

Dinyatakan sebagai sifat, bukan sebagai kasus. Uji yang memeriksa satu kalimat
akan lolos pada versi yang benar untuk ASCII dan salah untuk teks ber-tanda
baca, ber-spasi ganda, atau ber-aksen — dan dokumen sekolah memuat ketiganya.
"""

import itertools
from pathlib import Path

import pytest
from src.ingest.ekstraksi.docx import PengekstrakDocx
from src.ingest.ekstraksi.pdf import PengekstrakPdf
from src.ingest.ekstraksi.xlsx import PengekstrakXlsx
from src.nlp.praproses.tokenisasi import normalkan, tokenkan

BAHAN = Path(__file__).resolve().parents[1] / "bahan"

TEKS_UJI = (
    "Kepala sekolah menugaskan wakil kurikulum.",
    "Rapat  pleno   dihadiri 24 guru.",
    "Anggaran: Rp12.000.000,- (dua belas juta rupiah)",
    "Kepala sekolah — Dra. Siti — memimpin rapat.",
    "Naïve café, kôordinasi lintas-jenjang.",
    "\n\tIndentasi dan baris baru\n\n",
    "SDN 1 Sukamaju; SDN 2 Sukamaju",
    "email tidak.ada@contoh.sch.id",
)


@pytest.mark.parametrize("teks", TEKS_UJI)
def test_rentang_setiap_token_menunjuk_permukaannya(teks: str) -> None:
    """**Sifat terpenting fitur ini.**"""
    for t in tokenkan(teks):
        assert teks[t.mulai : t.akhir] == t.permukaan, t


@pytest.mark.parametrize(
    "nama", ["notulen.docx", "notulen-terlacak.docx", "serapan.xlsx", "berlapis-teks.pdf"]
)
def test_sifat_berlaku_atas_bahan_uji_sungguhan(nama: str) -> None:
    """Kalimat karangan tidak memuat kejutan yang dimuat berkas sungguhan.

    Teks di sini berasal dari pengekstrak, sehingga ia melewati jalur yang
    sama dengan dokumen yang kelak diunggah.
    """
    jalur = BAHAN / nama
    pengekstrak = next(
        p for p in (PengekstrakDocx(), PengekstrakXlsx(), PengekstrakPdf()) if p.menangani(jalur)
    )
    teks = pengekstrak.ekstrak(jalur).isi
    token = tokenkan(teks)
    assert token
    for t in token:
        assert teks[t.mulai : t.akhir] == t.permukaan, t


@pytest.mark.parametrize("teks", TEKS_UJI)
def test_token_tidak_bertumpang_tindih_dan_berurutan(teks: str) -> None:
    """Token yang bertumpang tindih menghasilkan dua rentang anotasi yang
    mengklaim karakter yang sama, dan D-03 tidak memiliki aturan untuk itu."""
    token = tokenkan(teks)
    for sebelum, sesudah in itertools.pairwise(token):
        assert sebelum.akhir <= sesudah.mulai


def test_ruang_kosong_tidak_menjadi_token() -> None:
    assert all(t.permukaan.strip() for t in tokenkan("Rapat  pleno   dihadiri"))


def test_tanda_baca_tidak_ikut_ke_dalam_token() -> None:
    """ "kurikulum." dan "kurikulum" harus menjadi kata yang sama saat dicari."""
    permukaan = [t.permukaan for t in tokenkan("wakil kurikulum. Rapat")]
    assert "kurikulum" in permukaan
    assert "kurikulum." not in permukaan


def test_angka_tetap_menjadi_token() -> None:
    """Dokumen manajerial penuh angka anggaran, dan pendeteksi data pribadi
    Fase E memerlukannya."""
    assert "24" in [t.permukaan for t in tokenkan("dihadiri 24 guru")]


def test_normalisasi_tidak_mengubah_panjang() -> None:
    """**Ini yang menjaga C-10 pada tahap normalisasi.**

    Normalisasi yang memendekkan teks — membuang tanda baca, merapatkan
    spasi — akan menggeser setiap indeks sesudahnya. Karena itu normalisasi di
    sini hanya boleh mengubah karakter menjadi karakter, tidak pernah
    menghapus atau menambah.
    """
    for teks in TEKS_UJI:
        assert len(normalkan(teks)) == len(teks), teks


def test_normalisasi_menurunkan_huruf() -> None:
    assert normalkan("Kepala Sekolah") == "kepala sekolah"


def test_teks_kosong_menghasilkan_daftar_kosong() -> None:
    """Bukan galat: teks kosong tidak dapat sampai ke sini karena
    `TeksKanonik` sudah menolaknya, dan melempar galat kedua kalinya hanya
    menambah jalan yang harus ditangani pemanggil."""
    assert tokenkan("") == []
    assert tokenkan("   \n\t ") == []
