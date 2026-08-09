"""Uji pemeriksa impor tunggal pytesseract — D-2 fitur 015, R-05, C-09.

Dibangun **sesudah** `PengekstrakOcr` ada, kebalikan dari urutan biasa dan
sengaja. Pemeriksa impor tunggal yang dibangun sebelum ada yang diimpor akan
lulus karena tidak memeriksa apa pun — pelajaran T-7 fitur 014.

Alasannya sama dengan C-08 bagi `src/llm/`: satu tempat yang tahu versi mesin
dan sidik berkas model. Impor di tempat lain menghasilkan keluaran OCR yang
tidak tercatat versinya, dan korpus yang tidak dapat diulang membatalkan klaim
reproduktibilitas pada naskah.
"""

from pathlib import Path

from perkakas.pemeriksa.impor_ocr import MODUL_SAH, periksa_impor_ocr

AKAR = Path(__file__).resolve().parents[2]


def _pohon(tmp_path: Path, berkas: dict[str, str]) -> Path:
    for nama, isi in berkas.items():
        jalur = tmp_path / nama
        jalur.parent.mkdir(parents=True, exist_ok=True)
        jalur.write_text(isi, encoding="utf-8")
    return tmp_path


def test_impor_pada_modul_sah_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    akar = _pohon(tmp_path, {MODUL_SAH: "import pytesseract\n"})
    assert periksa_impor_ocr(akar) == []


def test_impor_pada_modul_lain_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini.**"""
    akar = _pohon(tmp_path, {"src/rag/pengambil.py": "import pytesseract\n"})
    assert periksa_impor_ocr(akar)


def test_impor_bersarang_di_dalam_fungsi_juga_tertangkap(tmp_path: Path) -> None:
    """Impor di dalam fungsi adalah cara termudah melewati pemeriksa yang
    hanya membaca baris teratas berkas."""
    akar = _pohon(
        tmp_path,
        {"src/nlp/pindai.py": "def baca():\n    import pytesseract\n    return pytesseract\n"},
    )
    assert periksa_impor_ocr(akar)


def test_impor_from_juga_tertangkap(tmp_path: Path) -> None:
    akar = _pohon(tmp_path, {"src/nlp/pindai.py": "from pytesseract import image_to_string\n"})
    assert periksa_impor_ocr(akar)


def test_pohon_tanpa_src_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_impor_ocr(tmp_path) == []


def test_modul_sah_hilang_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """Kegagalan diam yang paling mungkin: berkasnya berpindah nama, dan
    pemeriksa melapor bersih karena tidak ada lagi yang mengimpor apa pun.

    Bentuk yang sama dengan pemeriksa C-03 yang menuntut berkas kredensial
    baku ada.
    """
    akar = _pohon(tmp_path, {"src/ingest/lain.py": "x = 1\n"})
    assert periksa_impor_ocr(akar)


def test_pohon_sesungguhnya_bersih() -> None:
    assert periksa_impor_ocr(AKAR) == []


def test_modul_sah_memang_ada_dan_memang_mengimpornya() -> None:
    """Pemeriksa yang menjaga berkas yang tidak mengimpor apa pun tidak
    menjaga apa pun."""
    sumber = (AKAR / MODUL_SAH).read_text(encoding="utf-8")
    assert "import pytesseract" in sumber
