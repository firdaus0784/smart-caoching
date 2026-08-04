"""Uji aturan tambah-saja logbook — R-13.

Dua aturan berbeda, karena dua bahaya berbeda:

- **Di dalam `src/logbook/`** tidak boleh ada pembukaan berkas dengan mode
  menimpa sama sekali. Penulis satu-satunya tidak boleh dapat memotong.
- **Di luar `src/logbook/`** tidak boleh ada penulisan ke jalur `logbook/`
  dalam bentuk apa pun, termasuk menambah. Menulis langsung melewati satu-
  satunya pintu yang diuji.

Membaca `logbook/` diizinkan di mana saja.
"""

from pathlib import Path

from perkakas.pemeriksa.logbook_tambah_saja import periksa_logbook_tambah_saja


def _tulis(akar: Path, nama: str, isi: str) -> None:
    berkas = akar / nama
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(f'"""R-13."""\n{isi}', encoding="utf-8")


def test_mode_menimpa_di_dalam_penulis_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/logbook/penulis.py", 'berkas.open("w")\n')
    temuan = periksa_logbook_tambah_saja(tmp_path)
    assert len(temuan) == 1, f"mode menimpa pada penulis lolos: {temuan}"


def test_mode_tambah_di_dalam_penulis_diizinkan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/logbook/penulis.py", 'berkas.open("a", encoding="utf-8")\n')
    assert periksa_logbook_tambah_saja(tmp_path) == []


def test_membaca_di_dalam_penulis_diizinkan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/logbook/pembaca.py", 'berkas.open("r")\n')
    assert periksa_logbook_tambah_saja(tmp_path) == []


def test_menulis_logbook_dari_modul_lain_tertangkap(tmp_path: Path) -> None:
    """Menambah pun tidak boleh: ia melewati satu-satunya pintu yang diuji."""
    _tulis(tmp_path, "src/rag/penyusun.py", 'open("logbook/L1-percobaan.jsonl", "a")\n')
    temuan = periksa_logbook_tambah_saja(tmp_path)
    assert len(temuan) == 1, f"penulisan dari modul lain lolos: {temuan}"


def test_menimpa_logbook_dari_modul_lain_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/api/rute.py", 'open("logbook/L2-versi-artefak.jsonl", "w")\n')
    assert len(periksa_logbook_tambah_saja(tmp_path)) == 1


def test_write_text_ke_logbook_tertangkap(tmp_path: Path) -> None:
    """write_text menimpa tanpa menyebut mode — mudah luput."""
    _tulis(tmp_path, "src/api/rute.py", 'Path("logbook/L1.jsonl").write_text("x")\n')
    assert len(periksa_logbook_tambah_saja(tmp_path)) == 1


def test_membaca_logbook_dari_modul_lain_diizinkan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/api/rute.py", 'open("logbook/L1-percobaan.jsonl")\n')
    assert periksa_logbook_tambah_saja(tmp_path) == []


def test_menulis_berkas_lain_tidak_dianggap_pelanggaran(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/api/rute.py", 'open("keluaran/hasil.json", "w")\n')
    assert periksa_logbook_tambah_saja(tmp_path) == []


def test_repositori_nyata_bersih() -> None:
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_logbook_tambah_saja(akar)
    assert temuan == [], "; ".join(str(t) for t in temuan)
