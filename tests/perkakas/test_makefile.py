"""Uji sasaran Makefile — R-14.

Makefile adalah satu-satunya titik masuk perintah yang disebut AGENTS.md. Ia
juga yang menyembunyikan pilihan uv dari alur kerja, sehingga penggantian
pengelola paket menyentuh satu berkas dan tidak mengubah AGENTS.md.
"""

import re
import subprocess
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
MAKEFILE = AKAR / "Makefile"

SASARAN_WAJIB = ("setup", "test", "test-unit", "lint", "check", "compliance")

POLA_SASARAN = re.compile(r"^([a-zA-Z][\w-]*)\s*:(?!=)", re.MULTILINE)


def test_makefile_ada() -> None:
    assert MAKEFILE.is_file(), "Makefile belum ada"


def test_enam_sasaran_wajib_ada() -> None:
    isi = MAKEFILE.read_text(encoding="utf-8")
    ada = set(POLA_SASARAN.findall(isi))
    hilang = [s for s in SASARAN_WAJIB if s not in ada]
    assert not hilang, f"sasaran wajib belum ada di Makefile: {hilang}"


def test_sasaran_wajib_dideklarasikan_phony() -> None:
    isi = MAKEFILE.read_text(encoding="utf-8")
    phony = set()
    for baris in isi.splitlines():
        if baris.startswith(".PHONY:"):
            phony.update(baris.split(":", 1)[1].split())
    hilang = [s for s in SASARAN_WAJIB if s not in phony]
    assert not hilang, f"sasaran belum dideklarasikan .PHONY: {hilang}"


def test_setiap_sasaran_dapat_dipanggil() -> None:
    """`make -n` menguraikan sasaran tanpa menjalankannya."""
    gagal = []
    for sasaran in SASARAN_WAJIB:
        hasil = subprocess.run(
            ["make", "-n", sasaran],
            cwd=AKAR,
            capture_output=True,
            text=True,
        )
        if "No rule to make target" in hasil.stderr:
            gagal.append(sasaran)
    assert not gagal, f"sasaran tidak dapat dipanggil: {gagal}"
