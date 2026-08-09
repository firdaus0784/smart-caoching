"""Uji pengekstrak DOCX — B-3 fitur 015, R-01.

Keadaan "DOCX dengan perubahan terlacak" pada `spec.md` menuntut teks final.
Yang membuatnya tidak sepele: **`paragraph.text` bawaan python-docx bukan teks
final.** Ia melewatkan teks yang disisipkan karena `w:ins` membungkus run-nya
satu tingkat lebih dalam, sehingga hasilnya kehilangan kata tanpa memberi
tanda apa pun.

Diperiksa langsung pada bahan uji ini, bukan disimpulkan dari dokumentasi:

    paragraph.text -> 'Jadwal supervisi disusun untuk  guru kelas, bukan delapan.'

Kata "enam" hilang, dan yang tersisa adalah kalimat yang tetap terbaca wajar.
Itu bentuk kegagalan yang tidak akan disadari siapa pun dari hasilnya saja.
"""

from pathlib import Path

import pytest
from src.ingest.ekstraksi.docx import PengekstrakDocx
from src.ingest.ekstraksi.galat import GalatEkstraksi

BAHAN = Path(__file__).resolve().parents[1] / "bahan"


def _ekstrak(nama: str) -> str:
    return PengekstrakDocx().ekstrak(BAHAN / nama).isi


def test_teks_dokumen_biasa_terekstrak() -> None:
    isi = _ekstrak("notulen.docx")
    assert "Sukamaju" in isi
    assert "jadwal supervisi" in isi


def test_teks_sisipan_ikut_terambil() -> None:
    """**Uji terpenting berkas ini.**

    Bukan sekadar "terlacak ditangani" melainkan sisipannya benar-benar ada.
    Tanpa uji ini, versi yang memakai `paragraph.text` bawaan akan lulus
    seluruh uji lain — kalimatnya tetap terbaca wajar tanpa kata itu.
    """
    assert "untuk enam guru kelas" in _ekstrak("notulen-terlacak.docx")


def test_teks_yang_dihapus_tidak_ikut() -> None:
    """Teks yang penulisnya hapus tidak pernah menjadi bagian dokumen.

    Membawanya masuk berarti korpus memuat kalimat yang tidak pernah disetujui
    siapa pun — dan pada dokumen manajerial, kalimat yang dicabut biasanya
    dicabut justru karena keliru.
    """
    assert "BATAL DIHAPUS" not in _ekstrak("notulen-terlacak.docx")


def test_berkas_bukan_docx_ditolak() -> None:
    with pytest.raises(GalatEkstraksi):
        PengekstrakDocx().ekstrak(BAHAN / "rusak.pdf")


def test_berkas_tidak_ada_ditolak() -> None:
    with pytest.raises(GalatEkstraksi):
        PengekstrakDocx().ekstrak(BAHAN / "tidak-ada.docx")


def test_menangani_hanya_docx() -> None:
    """Pemilihan pengekstrak diuji tanpa membaca isi berkas."""
    pengekstrak = PengekstrakDocx()
    assert pengekstrak.menangani(Path("a.docx"))
    assert pengekstrak.menangani(Path("a.DOCX"))
    assert not pengekstrak.menangani(Path("a.pdf"))
    assert not pengekstrak.menangani(Path("a.doc"))


def test_asal_dan_pengekstrak_terisi() -> None:
    """C-09 — keluaran dapat ditelusuri ke penghasilnya."""
    teks = PengekstrakDocx().ekstrak(BAHAN / "notulen.docx")
    assert teks.asal == "notulen.docx"
    assert teks.pengekstrak


def test_uraian_modul_menyatakan_keputusan_teks_final() -> None:
    """`spec.md` menuntut keputusan itu dinyatakan pada uraian modul.

    Pembaca berikutnya yang menemukan kode pembacaan XML yang tidak biasa akan
    bertanya mengapa, dan jawabannya harus ada di sana — bukan hanya di
    riwayat commit.
    """
    import src.ingest.ekstraksi.docx as modul

    uraian = (modul.__doc__ or "").lower()
    assert "terlacak" in uraian
    assert "final" in uraian


def test_penghapusan_yang_memakai_w_t_juga_dilewati() -> None:
    """Sebagian penghasil DOCX menulis teks terhapus sebagai `w:t` di dalam
    `w:del`, bukan sebagai `w:delText`.

    Pengekstrak yang hanya melewati `w:delText` akan memasukkan teks yang
    sudah dihapus, dan ujinya tetap hijau selama bahannya hanya memakai bentuk
    yang satu. Cacat ini ada pada versi pertama modul dan tertangkap di sini.
    """
    assert "SALAH TERHAPUS" not in _ekstrak("notulen-terlacak.docx")
    assert "Anggaran disetujui sepenuhnya." in _ekstrak("notulen-terlacak.docx")


def test_docx_terbuka_tetapi_tanpa_teks_ditolak() -> None:
    """Berkas DOCX yang sah tetapi tidak memuat satu kata pun.

    Ia berbeda dari berkas rusak: pustaka membukanya tanpa keluhan. Justru
    karena itu ia jalan termudah menuju dokumen kosong di korpus — tidak ada
    galat yang perlu ditelan siapa pun, cukup hasil yang kebetulan hampa.
    """
    with pytest.raises(GalatEkstraksi):
        PengekstrakDocx().ekstrak(BAHAN / "kosong.docx")
