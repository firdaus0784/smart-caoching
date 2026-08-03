"""Uji larangan impor pustaka model di luar src/llm/ — R-04, C-08.

C-08 berbunyi "seluruh pemanggilan model lewat src/llm/, tanpa pengecualian",
dan ADR-11 memperjelas bahwa itu mencakup LLM, sematan, NER, dan klasifikasi.
Pembungkus tunggal itulah yang mencatat versi model — tanpa aturan ini,
pencatatan versi bergantung pada ingatan penulis kode.
"""

from pathlib import Path

from perkakas.pemeriksa.impor_penyedia import PUSTAKA_MODEL, periksa_impor_penyedia


def _tulis(akar: Path, nama: str, isi: str) -> None:
    berkas = akar / nama
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(isi, encoding="utf-8")


def test_daftar_mencakup_llm_dan_model_lokal() -> None:
    """ADR-11 menyebut LLM, sematan, NER, dan klasifikasi — bukan LLM saja."""
    for pustaka in ("anthropic", "openai", "transformers", "torch"):
        assert pustaka in PUSTAKA_MODEL, f"{pustaka} tidak ada dalam daftar"


def test_impor_penyedia_di_luar_llm_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/penyusun.py", "import anthropic\n")
    temuan = periksa_impor_penyedia(tmp_path)
    assert len(temuan) == 1, f"pelanggaran tidak tertangkap: {temuan}"
    assert "anthropic" in temuan[0].pesan


def test_impor_di_dalam_src_llm_diizinkan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/llm/adaptor/nyata.py", "import anthropic\n")
    assert periksa_impor_penyedia(tmp_path) == []


def test_impor_bersarang_di_luar_llm_tertangkap(tmp_path: Path) -> None:
    """Memindahkan impor ke dalam fungsi adalah jalan keluar termudah."""
    _tulis(
        tmp_path,
        "src/nlp/ner.py",
        "def muat():\n    import transformers\n    return transformers\n",
    )
    temuan = periksa_impor_penyedia(tmp_path)
    assert len(temuan) == 1, f"impor bersarang lolos: {temuan}"


def test_from_import_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/api/rute.py", "from openai import OpenAI\n")
    assert len(periksa_impor_penyedia(tmp_path)) == 1


def test_perkakas_dan_tests_ikut_terjaga(tmp_path: Path) -> None:
    """Uji yang memanggil penyedia langsung melanggar G4-15 sekaligus C-08."""
    _tulis(tmp_path, "tests/test_x.py", "import openai\n")
    _tulis(tmp_path, "perkakas/bantu.py", "import cohere\n")
    assert len(periksa_impor_penyedia(tmp_path)) == 2


def test_berkas_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/penyusun.py", "from src.llm import pembungkus\n")
    assert periksa_impor_penyedia(tmp_path) == []


def test_temuan_menyebut_berkas_dan_baris(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/x.py", "x = 1\n\n\nimport openai\n")
    temuan = periksa_impor_penyedia(tmp_path)
    assert temuan[0].baris == 4
    assert temuan[0].berkas.name == "x.py"
