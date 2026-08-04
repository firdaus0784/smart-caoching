"""Uji pembatasan konstruksi Instruksi — ADR-13, C-18.

Memisahkan parameter instruksi dan data tidak berarti apa-apa bila pemanggil
dapat membentuk `Instruksi` dari teks yang berasal dari luar. Aturan inilah
yang membuat C-18 tetap tegak pada pemanggil kesepuluh, bukan hanya pada
pemanggil pertama yang menulisnya dengan hati-hati.
"""

from pathlib import Path

from perkakas.pemeriksa.konstruksi_instruksi import periksa_konstruksi_instruksi


def _tulis(akar: Path, nama: str, isi: str) -> None:
    berkas = akar / nama
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(f'"""ADR-13."""\n{isi}', encoding="utf-8")


def test_konstruksi_di_luar_modul_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/penyusun.py", "i = Instruksi(teks=pertanyaan_pengguna)\n")
    temuan = periksa_konstruksi_instruksi(tmp_path)
    assert len(temuan) == 1, f"konstruksi di luar modul lolos: {temuan}"


def test_konstruksi_di_dalam_modul_diizinkan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/llm/instruksi.py", "i = Instruksi(teks=_TEKS[kunci])\n")
    assert periksa_konstruksi_instruksi(tmp_path) == []


def test_konstruksi_lewat_atribut_modul_tertangkap(tmp_path: Path) -> None:
    """Tanpa ini, aturan dapat dilewati hanya dengan mengimpor modulnya."""
    _tulis(tmp_path, "src/api/rute.py", "i = tipe.Instruksi(teks=x)\n")
    assert len(periksa_konstruksi_instruksi(tmp_path)) == 1


def test_konstruksi_pada_perkakas_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "perkakas/bantu.py", "i = Instruksi(teks=x)\n")
    assert len(periksa_konstruksi_instruksi(tmp_path)) == 1


def test_uji_dikecualikan(tmp_path: Path) -> None:
    """Uji wajib dapat menyusun masukan bermusuhan — itu tugasnya.

    Uji tidak ikut disebarkan, sehingga pengecualian ini tidak melebarkan
    permukaan serangan. Melarangnya justru membuat C-18 tidak dapat diuji.
    """
    _tulis(tmp_path, "tests/test_x.py", "i = Instruksi(teks='muatan serangan')\n")
    assert periksa_konstruksi_instruksi(tmp_path) == []


def test_berkas_bersih_tidak_menyalak(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/penyusun.py", "from src.llm import instruksi\n")
    assert periksa_konstruksi_instruksi(tmp_path) == []


def test_repositori_nyata_bersih() -> None:
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_konstruksi_instruksi(akar)
    assert temuan == [], "; ".join(str(t) for t in temuan)
