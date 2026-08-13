"""Pemeriksa bentuk `HasilTanya` — B-2 fitur 021, R-06, R-10.

Urutan tahap jalur penjawaban tidak dapat ditegakkan pemeriksa statis: ia
pertanyaan tentang **apa yang terjadi saat jalan**. Yang dapat ditegakkan
bentuk adalah **ketiadaan jalan lain menuju hasilnya** — bila keluaran jalur
hanya dapat lahir dari jalur itu, maka tidak ada pemanggil yang dapat
menyusunnya sendiri dengan melewati tahap mana pun.

## Dua aturan

1. **`HasilTanya` hanya dibentuk pada `src/api/tanya.py`.** Bentuk
   `KredensialPseudonim` (C-05), bukan bentuk `ButirTayang` (C-06) yang
   membatasi *di mana boleh*. Alasannya sejajar dengan C-05: modul yang
   membentuk hasilnya sendiri sudah punya jalur yang tinggal dipanggil,
   sehingga membentuknya sendiri **selalu** berarti melewati sesuatu.
2. **`Jalur` tidak menerima validator yang dapat disuntikkan.** Kolaborator
   yang dapat diganti pemanggil adalah kolaborator yang dapat diganti dengan
   yang lebih longgar, dan validator yang lebih longgar membatalkan C-19 tanpa
   menyentuh satu baris validator sungguhan.

Aturan 2 menutup lubang aturan 1. Pembentukan yang terbatas pada satu modul
tetap menghasilkan apa saja bila modul itu menjalankan validator pilihan
pemanggil — hasilnya sah menurut aturan 1 dan tidak divalidasi menurut apa pun.

## Batas yang diakui terbuka

Sama dengan seluruh pemeriksa AST proyek ini (RP-01): `model_construct`,
`getattr`, dan penukaran atribut saat jalan lolos. Yang menutup sisanya bukan
pemeriksa melainkan `susun()` fitur 009, yang tidak menerima apa pun selain
`JawabanTervalidasi`.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_JALUR = Path("src") / "api" / "tanya.py"

NAMA_HASIL = "HasilTanya"
NAMA_KELAS_JALUR = "Jalur"

NAMA_VALIDATOR_TERLARANG = frozenset({"validator", "penvalidasi", "pemeriksa"})
"""Nama parameter yang, bila ada pada `Jalur.__init__`, berarti validatornya
dapat diganti pemanggil."""


def periksa_hasil_jalur(akar: Path) -> list[Temuan]:
    """Kedua aturan — lihat uraian modul."""
    return [
        *_aturan_1_pembentukan_terbatas(akar),
        *_aturan_2_validator_tidak_disuntikkan(akar),
    ]


def _aturan_1_pembentukan_terbatas(akar: Path) -> list[Temuan]:
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if berkas.relative_to(akar) == BERKAS_JALUR:
            continue
        try:
            pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == NAMA_HASIL
            ):
                temuan.append(
                    Temuan(
                        berkas=berkas.relative_to(akar),
                        baris=simpul.lineno,
                        pesan=(
                            f"{NAMA_HASIL} dibentuk di luar "
                            f"{BERKAS_JALUR.as_posix()} — hasil jalur yang dapat "
                            "disusun sendiri adalah hasil yang melewati tahap "
                            "mana pun tanpa satu galat pun (R-06)"
                        ),
                    )
                )
    return temuan


def _aturan_2_validator_tidak_disuntikkan(akar: Path) -> list[Temuan]:
    berkas = akar / BERKAS_JALUR
    if not berkas.exists():
        return [
            Temuan(
                berkas=BERKAS_JALUR,
                baris=0,
                pesan=(
                    "modul jalur penjawaban tidak ditemukan — aturan yang tidak "
                    "menemukan yang dijaganya wajib berbunyi, bukan diam"
                ),
            )
        ]
    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.ClassDef) or simpul.name != NAMA_KELAS_JALUR:
            continue
        for anggota in simpul.body:
            if not isinstance(anggota, ast.FunctionDef) or anggota.name != "__init__":
                continue
            nama = {
                arg.arg
                for arg in [*anggota.args.args, *anggota.args.kwonlyargs]
                if arg.arg in NAMA_VALIDATOR_TERLARANG
            }
            if nama:
                return [
                    Temuan(
                        berkas=BERKAS_JALUR,
                        baris=anggota.lineno,
                        pesan=(
                            f"{NAMA_KELAS_JALUR} menerima {sorted(nama)} sebagai "
                            "kolaborator — validator yang dapat diganti pemanggil "
                            "membatalkan C-19 tanpa menyentuh satu baris validator "
                            "sungguhan"
                        ),
                    )
                ]
    return []
