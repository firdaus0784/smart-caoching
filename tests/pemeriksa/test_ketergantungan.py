"""Uji pemeriksa penyimpangan ketergantungan — R-18, C-12.

C-12 melarang ketergantungan baru tanpa persetujuan penanggung jawab teknis.
Tanpa titik nol tertulis, "baru" tidak dapat didefinisikan — itulah sebabnya
Gerbang 2 meminta ketergantungan-disetujui.toml dibuat lebih dulu.

Tiga jenis penyimpangan diuji terpisah. Yang ketiga paling mudah luput karena
himpunan nama tetap utuh.
"""

from pathlib import Path

from perkakas.pemeriksa.ketergantungan import periksa_ketergantungan

LOCK = """version = 1

[[package]]
name = "smart-coaching"
version = "0.1.0"

[[package]]
name = "pydantic"
version = "2.10.0"

[[package]]
name = "pytest"
version = "8.3.0"
"""

DISETUJUI = """langsung = ["pydantic", "pytest"]

[terkunci]
"pydantic" = "2.10.0"
"pytest" = "8.3.0"
"""


def _tulis(tmp_path: Path, lock: str, disetujui: str) -> Path:
    (tmp_path / "uv.lock").write_text(lock, encoding="utf-8")
    (tmp_path / "ketergantungan-disetujui.toml").write_text(disetujui, encoding="utf-8")
    return tmp_path


def test_selaras_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_ketergantungan(_tulis(tmp_path, LOCK, DISETUJUI)) == []


def test_paket_masuk_tanpa_persetujuan_tertangkap(tmp_path: Path) -> None:
    lock = LOCK + '\n[[package]]\nname = "requests"\nversion = "2.32.0"\n'
    temuan = periksa_ketergantungan(_tulis(tmp_path, lock, DISETUJUI))
    assert len(temuan) == 1, f"paket baru lolos: {temuan}"
    assert "requests" in temuan[0].pesan
    assert "tanpa persetujuan" in temuan[0].pesan


def test_paket_hilang_tertangkap(tmp_path: Path) -> None:
    disetujui = DISETUJUI.replace("[terkunci]", '[terkunci]\n"ruff" = "0.9.0"')
    temuan = periksa_ketergantungan(_tulis(tmp_path, LOCK, disetujui))
    assert len(temuan) == 1, f"paket hilang lolos: {temuan}"
    assert "ruff" in temuan[0].pesan


def test_versi_bergeser_tertangkap(tmp_path: Path) -> None:
    """Himpunan nama tetap utuh — inilah penyimpangan yang paling mudah luput."""
    lock = LOCK.replace('version = "2.10.0"', 'version = "2.11.0"')
    temuan = periksa_ketergantungan(_tulis(tmp_path, lock, DISETUJUI))
    assert len(temuan) == 1, f"pergeseran versi lolos: {temuan}"
    assert "2.10.0" in temuan[0].pesan and "2.11.0" in temuan[0].pesan


def test_titik_nol_hilang_adalah_kegagalan(tmp_path: Path) -> None:
    """Menghapus pembandingnya bukan cara sah meloloskan pemeriksa."""
    (tmp_path / "uv.lock").write_text(LOCK, encoding="utf-8")
    temuan = periksa_ketergantungan(tmp_path)
    assert len(temuan) == 1
    assert "tidak ditemukan" in temuan[0].pesan.lower()


def test_repositori_nyata_tidak_menyimpang() -> None:
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_ketergantungan(akar)
    assert temuan == [], "; ".join(str(t) for t in temuan)
