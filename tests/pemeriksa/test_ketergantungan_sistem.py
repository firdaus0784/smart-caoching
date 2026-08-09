"""Uji pemeriksa ketergantungan sistem — R-13, C-12, C-09, KB-017.

Mesin OCR adalah program sistem, bukan paket Python, sehingga pemeriksa R-18
tidak melihatnya sama sekali. Berkas ini menguji penutup celah itu.

Yang paling penting di sini bukan uji ketidakcocokan melainkan uji **keadaan
tidak terpasang**. Pemeriksa yang tidak menemukan bahannya lalu melapor
"lulus" adalah laporan palsu, dan laporan palsu menghentikan kewaspadaan —
pelajaran TA-01 diterapkan pada perkakas.
"""

from pathlib import Path

from perkakas.pemeriksa.ketergantungan_sistem import periksa_ketergantungan_sistem

SIDIK = "sha256:45adaade8715f553c108334f603f24e4bc902fc6763892b5a9245afe230c82b4"

DISETUJUI = f"""langsung = ["pytesseract"]

[terkunci]
"pytesseract" = "0.3.13"

[sistem.tesseract]
versi = "5.3.4"
berkas_model = "ind.traineddata"
sidik = "{SIDIK}"
"""


def _pohon(tmp_path: Path, isi: str = DISETUJUI) -> Path:
    (tmp_path / "ketergantungan-disetujui.toml").write_text(isi, encoding="utf-8")
    return tmp_path


def test_mesin_tidak_terpasang_belum_dapat_diperiksa(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini.**

    Tidak menghasilkan temuan — tidak ada yang dilanggar — tetapi juga
    **tidak** boleh terbaca sebagai lulus. Bedanya ada pada `terperiksa`.
    """
    hasil = periksa_ketergantungan_sistem(_pohon(tmp_path), versi_mesin=lambda: None)
    assert hasil.temuan == []
    assert hasil.terperiksa is False
    assert hasil.catatan


def test_versi_mesin_bergeser_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """C-09 menuntut versi tercatat; versi yang bergeser diam-diam membuat
    hasil OCR tidak dapat diulang."""
    hasil = periksa_ketergantungan_sistem(
        _pohon(tmp_path), versi_mesin=lambda: "5.4.0", sidik_model=lambda _: SIDIK
    )
    assert hasil.temuan
    assert hasil.terperiksa is True


def test_sidik_berkas_model_berbeda_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """Berkas model menentukan isi korpus sama banyaknya dengan mesinnya.

    Model yang tertukar menghasilkan teks yang tetap terbaca seperti teks,
    sehingga tidak ada yang menyadarinya dari hasilnya saja.
    """
    hasil = periksa_ketergantungan_sistem(
        _pohon(tmp_path),
        versi_mesin=lambda: "5.3.4",
        sidik_model=lambda _: "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert hasil.temuan


def test_berkas_model_hilang_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """Mesin terpasang tetapi modelnya tidak ada adalah keadaan yang berbeda
    dari mesin yang tidak terpasang, dan hanya yang pertama pelanggaran."""
    hasil = periksa_ketergantungan_sistem(
        _pohon(tmp_path), versi_mesin=lambda: "5.3.4", sidik_model=lambda _: None
    )
    assert hasil.temuan
    assert hasil.terperiksa is True


def test_selaras_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    """Penjagaan yang menyala pada keadaan sah akan dimatikan orang."""
    hasil = periksa_ketergantungan_sistem(
        _pohon(tmp_path), versi_mesin=lambda: "5.3.4", sidik_model=lambda _: SIDIK
    )
    assert hasil.temuan == []
    assert hasil.terperiksa is True


def test_bagian_sistem_hilang_padahal_pytesseract_disetujui(tmp_path: Path) -> None:
    """Menghapus bagian `[sistem]` adalah cara termudah meloloskan seluruh
    pemeriksaan di atas, dan karena itu ia sendiri wajib menjadi temuan."""
    tanpa_sistem = """langsung = ["pytesseract"]

[terkunci]
"pytesseract" = "0.3.13"
"""
    hasil = periksa_ketergantungan_sistem(
        _pohon(tmp_path, tanpa_sistem), versi_mesin=lambda: "5.3.4"
    )
    assert hasil.temuan


def test_tanpa_pytesseract_bagian_sistem_tidak_dituntut(tmp_path: Path) -> None:
    """Proyek yang tidak memakai OCR tidak perlu mencatat mesin OCR.

    Tanpa ini, pemeriksa akan menyala pada seluruh fitur sebelum 015 bila
    seseorang menjalankannya atas riwayat lama.
    """
    tanpa_ocr = """langsung = ["pydantic"]

[terkunci]
"pydantic" = "2.13.4"
"""
    hasil = periksa_ketergantungan_sistem(_pohon(tmp_path, tanpa_ocr), versi_mesin=lambda: None)
    assert hasil.temuan == []
    assert hasil.terperiksa is True


def test_versi_belum_ditetapkan_belum_dapat_diperiksa(tmp_path: Path) -> None:
    """Keadaan proyek hari ini: berkas model sudah diperiksa dan sidiknya
    tercatat, tetapi mesin belum pernah dipasang di lingkungan penelitian.

    Menebak versinya dari lingkungan mana pun akan menghasilkan patokan yang
    tidak pernah dipakai siapa pun, dan patokan palsu lebih buruk daripada
    patokan kosong yang menyatakan dirinya kosong.
    """
    belum = DISETUJUI.replace('versi = "5.3.4"', 'versi = ""')
    hasil = periksa_ketergantungan_sistem(_pohon(tmp_path, belum), versi_mesin=lambda: "5.3.4")
    assert hasil.temuan == []
    assert hasil.terperiksa is False
    assert hasil.catatan


def test_pemeriksa_berjalan_pada_pohon_sesungguhnya() -> None:
    """Dijalankan pada pohon proyek, bukan hanya pada pohon tiruan."""
    akar = Path(__file__).resolve().parents[2]
    hasil = periksa_ketergantungan_sistem(akar)
    assert hasil.temuan == []
