"""Inti pemeriksa berbasis AST.

Tiga aturan bersandar pada modul ini:

- larangan impor pustaka penyedia model di luar `src/llm/` (C-08, R-04)
- larangan membuka berkas `logbook/` dengan mode tulis atau potong (R-13)
- pembatasan konstruksi `Instruksi` pada satu modul (ADR-13)

Ketiganya adalah pertanyaan tentang **bentuk kode**, bukan tentang perilaku
saat jalan, sehingga `ast` pada pustaka baku sudah memadai. Memakai pustaka
pemeriksa arsitektur akan menambah ketergantungan untuk pekerjaan yang selesai
dalam ratusan baris, sementara C-12 menjadikan setiap ketergantungan berbiaya
persetujuan.

Batas yang diakui terbuka (RP-01): pemeriksa ini membaca bentuk kode, sehingga
`importlib.import_module`, `getattr`, dan pemanggilan dinamis lain dapat
melewatinya. Ia tidak diklaim tertutup. Sejalan PT-01 pada `docs/D13.md`, yang
dirancang adalah pembatasan kerugian, bukan pencegahan sempurna.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DIREKTORI_DILEWATI = frozenset(
    {
        ".venv",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
    }
)

MODE_MENIMPA = frozenset({"w", "wb", "w+", "x", "xb", "r+", "wt"})


@dataclass(frozen=True)
class Temuan:
    """Satu pelanggaran, dengan tempatnya."""

    berkas: Path
    baris: int
    pesan: str

    def __str__(self) -> str:
        return f"{self.berkas}:{self.baris} — {self.pesan}"


@dataclass(frozen=True)
class Impor:
    modul: str
    baris: int


def berkas_python(akar: Path) -> Iterator[Path]:
    """Seluruh berkas .py di bawah `akar`, melewati direktori singgahan."""
    if akar.is_file():
        if akar.suffix == ".py":
            yield akar
        return
    for jalur in sorted(akar.rglob("*.py")):
        if DIREKTORI_DILEWATI.isdisjoint(jalur.parts):
            yield jalur


def _pohon(berkas: Path) -> ast.Module:
    """Urai berkas.

    SyntaxError sengaja dibiarkan naik. Berkas yang gagal diurai tidak boleh
    dianggap bersih — itu cara termudah melewati seluruh pemeriksa.
    """
    return ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))


def impor_pada(berkas: Path) -> list[Impor]:
    """Seluruh impor, termasuk yang bersarang di dalam fungsi atau kelas.

    Hanya bagian teratas nama modul yang dikembalikan: `dua.tiga` menjadi
    `dua`. Yang ingin diketahui aturan C-08 adalah pustaka mana yang dipakai,
    bukan submodulnya.
    """
    hasil: list[Impor] = []
    for simpul in ast.walk(_pohon(berkas)):
        if isinstance(simpul, ast.Import):
            for nama in simpul.names:
                hasil.append(Impor(nama.name.split(".")[0], simpul.lineno))
        # Impor relatif (`from . import x`) tidak memiliki modul luar.
        elif isinstance(simpul, ast.ImportFrom) and simpul.module and simpul.level == 0:
            hasil.append(Impor(simpul.module.split(".")[0], simpul.lineno))
    return sorted(hasil, key=lambda i: (i.baris, i.modul))


def panggilan_nama(berkas: Path, nama: str) -> list[int]:
    """Nomor baris setiap pemanggilan `nama(...)`.

    Menangkap dua bentuk: `Instruksi(...)` dan `modul.Instruksi(...)`. Tanpa
    bentuk kedua, ADR-13 dapat dilewati hanya dengan mengimpor modulnya.
    """
    baris: list[int] = []
    for simpul in ast.walk(_pohon(berkas)):
        if not isinstance(simpul, ast.Call):
            continue
        fungsi = simpul.func
        if (isinstance(fungsi, ast.Name) and fungsi.id == nama) or (
            isinstance(fungsi, ast.Attribute) and fungsi.attr == nama
        ):
            baris.append(simpul.lineno)
    return sorted(baris)


def pembukaan_berkas(berkas: Path) -> list[tuple[int, str, str]]:
    """Pemanggilan `open(...)` dengan jalur dan mode yang terbaca harfiah.

    Mengembalikan (baris, jalur, mode). Mode kosong berarti bawaan `r`.
    Pemanggilan dengan jalur yang dibentuk saat jalan tidak terbaca di sini —
    batas yang sama dengan RP-01.
    """
    hasil: list[tuple[int, str, str]] = []
    for simpul in ast.walk(_pohon(berkas)):
        if not isinstance(simpul, ast.Call):
            continue
        fungsi = simpul.func
        nama_fungsi = (
            fungsi.id
            if isinstance(fungsi, ast.Name)
            else fungsi.attr
            if isinstance(fungsi, ast.Attribute)
            else ""
        )
        if nama_fungsi not in {"open", "open_text", "write_text", "write_bytes"}:
            continue

        jalur = ""
        if simpul.args and isinstance(simpul.args[0], ast.Constant):
            nilai = simpul.args[0].value
            if isinstance(nilai, str):
                jalur = nilai

        mode = ""
        if len(simpul.args) > 1 and isinstance(simpul.args[1], ast.Constant):
            nilai_mode = simpul.args[1].value
            if isinstance(nilai_mode, str):
                mode = nilai_mode
        for kata in simpul.keywords:
            if kata.arg == "mode" and isinstance(kata.value, ast.Constant):
                nilai_mode = kata.value.value
                if isinstance(nilai_mode, str):
                    mode = nilai_mode

        if nama_fungsi in {"write_text", "write_bytes"}:
            mode = mode or "w"

        hasil.append((simpul.lineno, jalur, mode))
    return sorted(hasil)
