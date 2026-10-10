"""Uji kamus putusan gerbang ingesti — T-1 fitur 037, K-1, P-1 A.

Nilai dibaca dari baris D-14 Bagian 5.1 yang memilikinya, bukan ditulis ulang
di sini: daftar tangan pada uji akan sepakat dengan daftar tangan pada kode
pada hari keduanya sama-sama tertinggal dari dokumen (KM-04, AG-04).
"""

import ast
import re
from pathlib import Path

from src.kamus.gerbang import PutusanGerbang

AKAR = Path(__file__).resolve().parents[2]


def _nilai_d14(bidang: str) -> list[str]:
    d14 = (AKAR / "docs" / "D14.md").read_text(encoding="utf-8")
    (baris,) = [b for b in d14.splitlines() if b.startswith(f"| `{bidang}` | enum |")]
    makna = baris.split("|")[3]
    return [n for n in re.findall(r"`([a-z_]+)`", makna) if n != "PutusanGerbang"]


def test_nilai_putusan_persis_d14() -> None:
    assert [n.value for n in PutusanGerbang] == _nilai_d14("jejak_area.putusan")


def test_putusan_hanya_didefinisikan_di_kamus() -> None:
    tempat = []
    for berkas in sorted((AKAR / "src").rglob("*.py")):
        for simpul in ast.walk(ast.parse(berkas.read_text(encoding="utf-8"))):
            if isinstance(simpul, ast.ClassDef) and simpul.name == "PutusanGerbang":
                tempat.append(str(berkas.relative_to(AKAR)))
    assert tempat == ["src/kamus/gerbang.py"]
