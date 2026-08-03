"""Pemeriksa nama terlarang — C-15.

C-15 berbunyi: tidak membuat tabel poin, lencana, papan peringkat, atau
pertemanan; membuatnya kosong pun tidak. `docs/D04.md` Bagian 9 menjelaskan
alasannya — tabel kosong mengundang pengisian, dan pengisian itu melanggar
batas ruang lingkup 2026.

Dua keputusan rancangan yang menentukan pemeriksa ini berguna atau justru
dimatikan orang:

**Hanya nama pengenal yang diperiksa, bukan komentar dan untai.** Menjelaskan
mengapa lencana dilarang bukan membuat lencana. Pemeriksa yang menyalak pada
prosa akan membuat penulis menghapus penjelasannya, dan penjelasan itu justru
yang menjaga aturan tetap dipahami.

**Hanya `src/` yang diperiksa.** `perkakas/` memuat daftar kata terlarang ini
sendiri, dan `tests/` memuat pelanggaran buatan yang memang harus ada.

Bahaya terbesar pemeriksa ini bukan melewatkan pelanggaran melainkan menyalak
pada nama yang diwajibkan dokumen lain. `peringkat_kepercayaan` (D-13 Bagian 6)
dan `skor_relevansi` (D-01 Bagian 9) sah dan wajib ada. Karena itu daftar di
bawah memakai pola yang tidak dapat cocok dengan keduanya: "papanperingkat"
sebagai satu kesatuan, bukan "peringkat".
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

# Dicocokkan terhadap nama pengenal yang sudah dinormalkan: huruf kecil,
# garis bawah dan tanda hubung dibuang. Seluruhnya cukup panjang dan khas
# sehingga tidak dapat cocok dengan istilah sah pada kamus data D-14.
TERLARANG = (
    "lencana",
    "badge",
    "papanperingkat",
    "leaderboard",
    "pertemanan",
    "friendship",
    "gamifikasi",
    "gamification",
    "achievement",
    "streak",
    "poin",
)

# Diperiksa sebagai komponen utuh, bukan potongan. "xp" sebagai potongan akan
# cocok dengan "expired"; sebagai komponen ia hanya cocok dengan "xp".
TERLARANG_UTUH = ("xp", "teman", "friend", "point", "points")

POLA_PEMISAH = re.compile(r"[_\-]|(?<=[a-z0-9])(?=[A-Z])")

DIPERIKSA = ("src", "web")


def _normal(pengenal: str) -> str:
    return pengenal.lower().replace("_", "").replace("-", "")


def _komponen(pengenal: str) -> list[str]:
    return [b.lower() for b in POLA_PEMISAH.split(pengenal) if b]


def _melanggar(pengenal: str) -> str | None:
    normal = _normal(pengenal)
    for kata in TERLARANG:
        if kata in normal:
            return kata
    komponen = set(_komponen(pengenal))
    for kata in TERLARANG_UTUH:
        if kata in komponen:
            return kata
    return None


def _pengenal_pada(berkas: Path) -> list[tuple[str, int]]:
    """Nama kelas, fungsi, argumen, dan peubah yang disasarkan.

    Komentar dan untai sengaja tidak termasuk.
    """
    pohon = ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))
    hasil: list[tuple[str, int]] = []
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            hasil.append((simpul.name, simpul.lineno))
        elif isinstance(simpul, ast.Name) and isinstance(simpul.ctx, ast.Store):
            hasil.append((simpul.id, simpul.lineno))
        elif isinstance(simpul, ast.arg):
            hasil.append((simpul.arg, simpul.lineno))
        elif isinstance(simpul, ast.Attribute) and isinstance(simpul.ctx, ast.Store):
            hasil.append((simpul.attr, simpul.lineno))
    return hasil


def periksa_nama_terlarang(akar: Path) -> list[Temuan]:
    temuan: list[Temuan] = []
    for direktori in DIPERIKSA:
        cabang = akar / direktori
        if not cabang.is_dir():
            continue
        for berkas in berkas_python(cabang):
            kata = _melanggar(berkas.stem)
            if kata:
                temuan.append(
                    Temuan(
                        berkas,
                        0,
                        f"nama berkas memuat {kata!r} — C-15 melarang poin, "
                        "lencana, papan peringkat, dan pertemanan, termasuk "
                        "dalam bentuk kosong",
                    )
                )
            for pengenal, baris in _pengenal_pada(berkas):
                kata = _melanggar(pengenal)
                if kata:
                    temuan.append(
                        Temuan(
                            berkas,
                            baris,
                            f"pengenal {pengenal!r} memuat {kata!r} — C-15, "
                            "lihat docs/D04.md Bagian 9",
                        )
                    )
    return temuan
