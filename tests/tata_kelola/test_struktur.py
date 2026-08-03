"""Uji struktur repositori — R-01, R-02.

Struktur direktori adalah prasyarat seluruh pemeriksa berikutnya: `make
compliance` membaca `docs/`, pemeriksa AST menelusuri `src/` dan `perkakas/`,
dan penulis catatan versi menulis ke `logbook/`.
"""

from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]

DIREKTORI_WAJIB = (
    "src",
    "tests",
    "perkakas",
    "logbook",
    "docs",
    "specs/_template",
)


def test_direktori_wajib_ada() -> None:
    hilang = [d for d in DIREKTORI_WAJIB if not (AKAR / d).is_dir()]
    assert not hilang, f"direktori wajib belum ada: {hilang}"


def test_gitignore_ada_dan_tidak_mengabaikan_logbook() -> None:
    gitignore = AKAR / ".gitignore"
    assert gitignore.is_file(), ".gitignore belum ada"

    baris = [
        b.strip()
        for b in gitignore.read_text(encoding="utf-8").splitlines()
        if b.strip() and not b.strip().startswith("#")
    ]
    terlarang = [b for b in baris if b.strip("/").split("/")[0] == "logbook"]
    assert not terlarang, (
        f"logbook/ tidak boleh diabaikan git — ia adalah rekaman penelitian: {terlarang}"
    )
