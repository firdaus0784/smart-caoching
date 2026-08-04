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


def _untai(simpul: ast.expr | None) -> str:
    """Nilai untai bila simpul adalah tetapan untai; selain itu kosong."""
    if isinstance(simpul, ast.Constant) and isinstance(simpul.value, str):
        return simpul.value
    return ""


def _jalur_penerima(simpul: ast.expr) -> str:
    """Jalur harfiah pada penerima metode: `Path("x").open(...)` atau `"x".open(...)`.

    Penerima berupa peubah tidak terbaca — itu batas yang sama dengan RP-01.
    """
    if (
        isinstance(simpul, ast.Call)
        and isinstance(simpul.func, ast.Name)
        and simpul.func.id in {"Path", "PurePath", "PosixPath"}
        and simpul.args
    ):
        return _untai(simpul.args[0])
    return _untai(simpul)


def _mode_kata_kunci(simpul: ast.Call) -> str:
    for kata in simpul.keywords:
        if kata.arg == "mode":
            return _untai(kata.value)
    return ""


def pembukaan_berkas(berkas: Path) -> list[tuple[int, str, str]]:
    """Pembukaan berkas dengan jalur dan mode yang terbaca harfiah.

    Mengembalikan (baris, jalur, mode). Mode kosong berarti bawaan `r`.

    Tiga bentuk dikenali, dan ketiganya menaruh argumennya di tempat berbeda:

    - `open(jalur, mode)` — bawaan; jalur pada argumen pertama
    - `berkas.open(mode)` — metode `Path`; **mode** pada argumen pertama, dan
      jalurnya ada pada penerima, bukan pada argumen
    - `berkas.write_text(isi)` — menimpa tanpa menyebut mode sama sekali

    Bentuk kedua dan ketiga sempat terbaca keliru: mode dibaca sebagai jalur,
    dan isi dibaca sebagai jalur. Keduanya ditemukan uji C-2, bukan uji B-1.
    """
    hasil: list[tuple[int, str, str]] = []
    for simpul in ast.walk(_pohon(berkas)):
        if not isinstance(simpul, ast.Call):
            continue
        fungsi = simpul.func

        if isinstance(fungsi, ast.Name) and fungsi.id == "open":
            jalur = _untai(simpul.args[0]) if simpul.args else ""
            mode = (_untai(simpul.args[1]) if len(simpul.args) > 1 else "") or _mode_kata_kunci(
                simpul
            )
        elif isinstance(fungsi, ast.Attribute) and fungsi.attr == "open":
            jalur = _jalur_penerima(fungsi.value)
            mode = (_untai(simpul.args[0]) if simpul.args else "") or _mode_kata_kunci(simpul)
        elif isinstance(fungsi, ast.Attribute) and fungsi.attr in {"write_text", "write_bytes"}:
            jalur = _jalur_penerima(fungsi.value)
            mode = "w"
        else:
            continue

        hasil.append((simpul.lineno, jalur, mode))
    return sorted(hasil)
