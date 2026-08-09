"""Uji pengekstrak PDF — B-5 fitur 015, R-01, R-02.

PDF adalah satu-satunya format pada fitur ini yang punya **dua** cara gagal
yang harus dibedakan tegas:

- berkas tidak dapat dibaca → dokumen ditolak
- berkas terbaca tetapi tanpa lapisan teks → dokumen **dialihkan ke OCR**

Menyamakan keduanya berarti seluruh dokumen pindaian ditolak, dan itu
membatalkan FR-B02 sebelum ia dibangun. Membalikkannya lebih buruk lagi:
berkas rusak yang dialihkan ke OCR menghasilkan teks acak yang masuk korpus
sebagai dokumen sah.
"""

from pathlib import Path
from typing import ClassVar

import pytest
from src.ingest.ekstraksi.galat import GalatEkstraksi
from src.ingest.ekstraksi.pdf import GalatTanpaLapisanTeks, PengekstrakPdf

BAHAN = Path(__file__).resolve().parents[1] / "bahan"


def _ekstrak(nama: str) -> str:
    return PengekstrakPdf().ekstrak(BAHAN / nama).isi


def test_pdf_berlapis_teks_terekstrak() -> None:
    isi = _ekstrak("berlapis-teks.pdf")
    assert "Sukamaju" in isi
    assert "jadwal supervisi" in isi


def test_pdf_tanpa_lapisan_teks_dialihkan_bukan_ditolak() -> None:
    """**Uji terpenting berkas ini.**

    Galatnya bertipe khusus, bukan `GalatEkstraksi` biasa. Pemanggil yang
    hanya menangkap tipe umum tidak dapat membedakan "alihkan ke OCR" dari
    "tolak dokumen ini", dan pembedaan itu tidak boleh bersandar pada isi
    pesan galat.
    """
    with pytest.raises(GalatTanpaLapisanTeks):
        _ekstrak("pindaian-tanpa-teks.pdf")


def test_galat_pengalihan_tetap_turunan_galat_ekstraksi() -> None:
    """Pemanggil yang belum peduli OCR tetap menangkapnya sebagai kegagalan.

    Tanpa pewarisan ini, penambahan tipe baru akan lolos dari setiap
    `except GalatEkstraksi` yang sudah ada dan naik sampai menghentikan
    ingesti.
    """
    assert issubclass(GalatTanpaLapisanTeks, GalatEkstraksi)


def test_pdf_tanpa_lapisan_teks_tidak_menghasilkan_teks_kosong() -> None:
    """Dinyatakan terpisah dari uji di atas, dan sengaja.

    Versi yang mengembalikan `TeksKanonik` berisi untai kosong akan gagal uji
    ini walau ia juga melempar sesuatu di tempat lain.
    """
    pengekstrak = PengekstrakPdf()
    try:
        hasil = pengekstrak.ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")
    except GalatTanpaLapisanTeks:
        return
    pytest.fail(f"tidak melempar galat; mengembalikan {hasil.isi!r}")


def test_pdf_terkunci_ditolak_bukan_dibuka_paksa() -> None:
    """Keadaan "PDF terkunci kata sandi" pada `spec.md`.

    Tidak dicoba dibuka dengan kata sandi kosong maupun daftar tebakan.
    Dokumen yang pemiliknya kunci adalah dokumen yang pemiliknya belum
    izinkan dibaca, dan ET-04 sudah menetapkan sikap terhadap itu.
    """
    with pytest.raises(GalatEkstraksi) as galat:
        _ekstrak("terkunci.pdf")
    assert not isinstance(galat.value, GalatTanpaLapisanTeks)


def test_pdf_rusak_ditolak() -> None:
    with pytest.raises(GalatEkstraksi) as galat:
        _ekstrak("rusak.pdf")
    assert not isinstance(galat.value, GalatTanpaLapisanTeks)


def test_pdf_kosong_ditolak() -> None:
    """Berkas nol bita — keadaan tersendiri pada `spec.md`."""
    with pytest.raises(GalatEkstraksi):
        _ekstrak("kosong.pdf")


def test_berkas_tidak_ada_ditolak() -> None:
    with pytest.raises(GalatEkstraksi):
        _ekstrak("tidak-ada.pdf")


def test_menangani_hanya_pdf() -> None:
    pengekstrak = PengekstrakPdf()
    assert pengekstrak.menangani(Path("a.pdf"))
    assert pengekstrak.menangani(Path("a.PDF"))
    assert not pengekstrak.menangani(Path("a.docx"))


def test_asal_dan_pengekstrak_terisi() -> None:
    teks = PengekstrakPdf().ekstrak(BAHAN / "berlapis-teks.pdf")
    assert teks.asal == "berlapis-teks.pdf"
    assert teks.pengekstrak


def test_urutan_halaman_terjaga() -> None:
    """Halaman yang tertukar menghasilkan indeks karakter yang menunjuk
    kalimat orang lain — dan tidak ada yang menyadarinya dari isinya."""
    isi = _ekstrak("berlapis-teks.pdf")
    assert isi.index("Notulen") < isi.index("Sukamaju") < isi.index("jadwal supervisi")


def test_pdf_beraliran_isi_rusak_terbaca_sebagai_pindaian() -> None:
    """Batas yang dinyatakan, bukan perilaku yang diinginkan.

    `isi-rusak.pdf` punya kerangka sah dengan aliran isi yang menyatakan
    dirinya terkompresi Flate padahal bukan. pypdf **tidak melempar galat**
    atas itu; ia mengembalikan teks kosong. Akibatnya berkas rusak semacam ini
    tidak dapat dibedakan dari pindaian pada lapisan ini, dan ia dialihkan ke
    OCR.

    Dinyatakan sebagai uji supaya perilakunya **dipilih dan terlihat**, bukan
    kebetulan. Yang menahan kerugiannya adalah jalur OCR yang juga tidak akan
    menghasilkan teks dari berkas itu, sehingga dokumennya tetap tertahan —
    hanya lewat pintu yang berbeda dari yang diduga.
    """
    with pytest.raises(GalatTanpaLapisanTeks):
        _ekstrak("isi-rusak.pdf")


def test_kegagalan_saat_mengambil_teks_ditolak_bukan_dialihkan(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Bila pustaka **memang** melempar saat mengambil teks — versi lain, atau
    berkas yang bentuk kerusakannya berbeda — hasilnya wajib penolakan, bukan
    pengalihan ke OCR.

    Disuntikkan karena tidak ada berkas pada bahan uji yang memicunya dengan
    pustaka versi ini. Tanpa uji ini, cabang penanganannya tidak pernah
    dijalankan siapa pun dan dapat keliru tanpa ketahuan.
    """
    import pypdf

    class _HalamanRusak:
        def extract_text(self) -> str:
            raise pypdf.errors.PdfReadError("aliran isi tidak dapat diurai")

    class _PembacaRusak:
        is_encrypted = False
        pages: ClassVar[list[_HalamanRusak]] = [_HalamanRusak()]

        def __init__(self, *_: object, **__: object) -> None: ...

    monkeypatch.setattr(pypdf, "PdfReader", _PembacaRusak)
    with pytest.raises(GalatEkstraksi) as galat:
        _ekstrak("berlapis-teks.pdf")
    assert not isinstance(galat.value, GalatTanpaLapisanTeks)
