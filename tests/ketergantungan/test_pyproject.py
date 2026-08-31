"""Uji deklarasi ketergantungan — R-18, C-12.

Ketergantungan langsung wajib **tepat sama** dengan yang disetujui pada
Gerbang 2. Lebih maupun kurang sama-sama menggagalkan: penambahan berarti
ketergantungan masuk tanpa persetujuan, pengurangan berarti daftar disetujui
tidak lagi menggambarkan keadaan.

Himpunan di bawah adalah rekaman keputusan manusia, bukan pilihan agen. Ia
berubah **hanya** bersama keputusan gerbang yang tercatat pada `logbook/L4`,
dan tiap perubahannya menyebut keputusan mana yang menyebabkannya.

Menambahkan nama ke sini untuk meloloskan `make check` membatalkan gunanya.
"""

import tomllib
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
PYPROJECT = AKAR / "pyproject.toml"

DISETUJUI_RUNTIME = {
    # Gerbang 2 fitur 001
    "pydantic",
    # Gerbang 1 fitur 015, keputusan KB-017
    "pypdf",
    "python-docx",
    "openpyxl",
    "pysastrawi",
    "pytesseract",
    # Keputusan KB-044 (13 Agustus 2026), dituliskan pada berkas persetujuan
    # atas perintah tertulis pemegang gerbang pada 18 Agustus 2026 — KB-067.
    "fastapi",
    "uvicorn",
    "httpx",
    "asyncpg",
    "pgvector",
}
DISETUJUI_PENGEMBANGAN = {"pytest", "pytest-cov", "ruff", "mypy"}


def _muat() -> dict:
    assert PYPROJECT.is_file(), "pyproject.toml belum ada"
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _nama(spesifikasi: str) -> str:
    for pemisah in ("[", ">", "<", "=", "!", "~", ";", " "):
        spesifikasi = spesifikasi.split(pemisah)[0]
    return spesifikasi.strip().lower().replace("_", "-")


def test_python_dipatok_pada_312() -> None:
    proyek = _muat()["project"]
    patokan = proyek.get("requires-python", "")
    assert "3.12" in patokan, f"requires-python tidak memuat 3.12: {patokan!r}"
    assert "3.13" in patokan, (
        f"requires-python tidak memberi batas atas: {patokan!r} — "
        "tanpa batas atas, patokan 3.12 tidak berarti apa-apa"
    )


def test_ketergantungan_runtime_tepat_sama() -> None:
    ada = {_nama(d) for d in _muat()["project"].get("dependencies", [])}
    assert ada == DISETUJUI_RUNTIME, (
        f"runtime menyimpang dari yang disetujui Gerbang 2. "
        f"berlebih={sorted(ada - DISETUJUI_RUNTIME)} "
        f"kurang={sorted(DISETUJUI_RUNTIME - ada)}"
    )


def test_ketergantungan_pengembangan_tepat_sama() -> None:
    kelompok = _muat().get("dependency-groups", {})
    ada = {_nama(d) for d in kelompok.get("dev", [])}
    assert ada == DISETUJUI_PENGEMBANGAN, (
        f"pengembangan menyimpang dari yang disetujui Gerbang 2. "
        f"berlebih={sorted(ada - DISETUJUI_PENGEMBANGAN)} "
        f"kurang={sorted(DISETUJUI_PENGEMBANGAN - ada)}"
    )


def test_konfigurasi_perkakas_ada() -> None:
    alat = _muat().get("tool", {})
    hilang = [n for n in ("ruff", "mypy", "pytest", "coverage") if n not in alat]
    assert not hilang, f"konfigurasi perkakas belum ada di pyproject.toml: {hilang}"


def test_cakupan_hanya_mengukur_src() -> None:
    """perkakas/ adalah alat bantu pembangunan, bukan modul inti yang dinilai.

    Memasukkannya ke pengukuran membuat angka C-11 dan NFR-16 kehilangan makna.
    """
    sumber = _muat()["tool"]["coverage"]["run"]["source"]
    assert sumber == ["src"], (
        f"cakupan harus mengukur src/ saja, bukan {sumber} — lihat plan.md "
        "bagian Berkas yang disentuh"
    )
