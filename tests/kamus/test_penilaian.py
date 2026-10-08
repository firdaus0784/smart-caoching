"""Uji kamus penilaian dan tindak lanjut aduan — T-4 fitur 036, R-02.

Nilai dibaca dari baris D-14 Bagian 5.1 yang memilikinya, bukan ditulis ulang
di sini: daftar tangan pada uji akan sepakat dengan daftar tangan pada kode
pada hari keduanya sama-sama tertinggal dari dokumen (KM-04, AG-04).
"""

import ast
import re
from enum import Enum
from pathlib import Path

import pytest
from src.kamus.penilaian import NilaiPenilaian, TindakLanjutAduan

AKAR = Path(__file__).resolve().parents[2]


def _nilai_d14(bidang: str) -> list[str]:
    d14 = (AKAR / "docs" / "D14.md").read_text(encoding="utf-8")
    (baris,) = [b for b in d14.splitlines() if b.startswith(f"| `{bidang}` | enum |")]
    makna = baris.split("|")[3]
    # Nilai berupa kode berhuruf kecil bergaris bawah, sebelum keterangan dalam kurung.
    return [
        n
        for n in re.findall(r"`([a-z_]+)`", makna)
        if n not in {"NilaiPenilaian", "TindakLanjutAduan"}
    ]


@pytest.mark.parametrize(
    ("kelas", "bidang"),
    [
        (NilaiPenilaian, "penilaian.nilai"),
        (TindakLanjutAduan, "tindak_lanjut_aduan.tindak_lanjut"),
    ],
)
def test_nilai_enum_persis_d14(kelas: type[Enum], bidang: str) -> None:
    assert [n.value for n in kelas] == _nilai_d14(bidang)


@pytest.mark.parametrize("nama", ["NilaiPenilaian", "TindakLanjutAduan"])
def test_enum_hanya_didefinisikan_di_kamus(nama: str) -> None:
    tempat = []
    for berkas in sorted((AKAR / "src").rglob("*.py")):
        for simpul in ast.walk(ast.parse(berkas.read_text(encoding="utf-8"))):
            if isinstance(simpul, ast.ClassDef) and simpul.name == nama:
                tempat.append(str(berkas.relative_to(AKAR)))
    assert tempat == ["src/kamus/penilaian.py"]
