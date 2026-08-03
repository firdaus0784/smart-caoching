"""Uji pengunci versi dan titik nol R-18 — C-12.

`uv.lock` memuat pohon transitif utuh. `ketergantungan-disetujui.toml` adalah
rekaman himpunan itu pada saat disetujui manusia — titik nol yang menjadi
pembanding. Tanpa titik nol tertulis, R-18 tidak punya pembanding dan
"ketergantungan baru" tidak dapat didefinisikan.

Yang diuji adalah **penyimpangan dari titik nol**, bukan isi lock itu sendiri.
"""

import tomllib
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
LOCK = AKAR / "uv.lock"
DISETUJUI = AKAR / "ketergantungan-disetujui.toml"

# Rekaman keputusan manusia pada Gerbang 2.
LANGSUNG_GERBANG_2 = {"pydantic", "pytest", "pytest-cov", "ruff", "mypy"}


def _normal(nama: str) -> str:
    return nama.strip().lower().replace("_", "-")


def _paket_pada_lock() -> dict[str, str]:
    assert LOCK.is_file(), "uv.lock belum ada — jalankan `make setup`"
    isi = tomllib.loads(LOCK.read_text(encoding="utf-8"))
    return {
        _normal(p["name"]): p.get("version", "")
        for p in isi.get("package", [])
        if _normal(p["name"]) != "smart-coaching"
    }


def _disetujui() -> dict:
    assert DISETUJUI.is_file(), "ketergantungan-disetujui.toml belum ada"
    return tomllib.loads(DISETUJUI.read_text(encoding="utf-8"))


def test_daftar_langsung_sama_dengan_persetujuan_gerbang_2() -> None:
    langsung = {_normal(n) for n in _disetujui()["langsung"]}
    assert langsung == LANGSUNG_GERBANG_2, (
        f"daftar langsung menyimpang dari persetujuan Gerbang 2. "
        f"berlebih={sorted(langsung - LANGSUNG_GERBANG_2)} "
        f"kurang={sorted(LANGSUNG_GERBANG_2 - langsung)}"
    )


def test_himpunan_terkunci_identik_dengan_titik_nol() -> None:
    pada_lock = _paket_pada_lock()
    titik_nol = {_normal(n): v for n, v in _disetujui()["terkunci"].items()}

    berlebih = sorted(set(pada_lock) - set(titik_nol))
    kurang = sorted(set(titik_nol) - set(pada_lock))
    assert not berlebih and not kurang, (
        f"pohon ketergantungan menyimpang dari titik nol. "
        f"masuk tanpa persetujuan={berlebih} hilang={kurang}"
    )


def test_versi_terkunci_tidak_bergeser() -> None:
    pada_lock = _paket_pada_lock()
    titik_nol = {_normal(n): v for n, v in _disetujui()["terkunci"].items()}

    bergeser = [
        f"{n}: titik nol {titik_nol[n]} -> lock {pada_lock[n]}"
        for n in sorted(set(pada_lock) & set(titik_nol))
        if titik_nol[n] != pada_lock[n]
    ]
    assert not bergeser, "versi bergeser tanpa persetujuan: " + "; ".join(bergeser)
