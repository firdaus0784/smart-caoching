"""Pemeriksa gerbang kurasi — C-06, R-02, FR-I03.

C-06 berbunyi: *"Butir pengetahuan tidak tayang tanpa persetujuan kurator."*

Seperti C-19, pasal ini melarang sebuah **keadaan saat jalan**, dan pemeriksa
statis tidak dapat menjalankan sistemnya. Yang dapat ditegakkan bentuk adalah
**ketiadaan jalan keluar**: bila butir yang tayang hanya dapat lahir dari
gerbang putusan, maka tidak ada jalur yang melewatinya.

## Dua aturan

1. **`ButirTayang` hanya dibentuk pada `src/ingest/kurasi/putusan.py`.** Bentuk
   yang sama dengan aturan `Instruksi` ADR-13 dan `JawabanTervalidasi` C-19,
   keduanya sudah terbukti. Fitur 011 yang menayangkan feed kemudian tidak
   memiliki cara menayangkan kandidat.
2. **`ButirTayang` tidak memiliki nilai bawaan pada bidang putusannya.** Bidang
   berbawaan membuat butir yang lupa diputuskan terbentuk sebagai butir yang
   disetujui — dan tidak satu uji perilaku pun gagal karenanya, sebab
   putusannya memang ada, hanya saja tidak seorang pun mengambilnya.

Aturan 2 menutup lubang aturan 1: pembentukan yang terbatas pada satu modul
tetap dapat menghasilkan butir yang tidak diputuskan bila bidang putusannya
mengisi dirinya sendiri.

## Batas yang diakui terbuka

Sama dengan pemeriksa C-02, C-03, C-16, dan C-19: ini pembacaan bentuk kode.
Pembentukan lewat `getattr` atau `model_construct` lolos. Yang menutup sisanya
bukan pemeriksa melainkan penjagaan pada bentuk `ButirTayang` sendiri —
putusan yang bukan persetujuan ditolak betapa pun butirnya dibentuk.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_PUTUSAN = Path("src") / "ingest" / "kurasi" / "putusan.py"

NAMA_BUTIR_TAYANG = "ButirTayang"
NAMA_BIDANG_PUTUSAN = "putusan"


def periksa_gerbang_kurasi(akar: Path) -> list[Temuan]:
    """Kedua aturan C-06 — lihat uraian modul."""
    temuan: list[Temuan] = []
    temuan.extend(_aturan_1_pembentukan_terbatas(akar))
    temuan.extend(_aturan_2_putusan_tanpa_bawaan(akar))
    return temuan


def _aturan_1_pembentukan_terbatas(akar: Path) -> list[Temuan]:
    """`ButirTayang` hanya dibentuk pada modul putusan."""
    diizinkan = (akar / BERKAS_PUTUSAN).resolve()
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if berkas.resolve() == diizinkan:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == NAMA_BUTIR_TAYANG
            ):
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        f"{NAMA_BUTIR_TAYANG} dibentuk di luar gerbang putusan — butir "
                        "yang dapat dibentuk di mana saja adalah butir yang dapat tayang "
                        "tanpa persetujuan kurator (C-06, FR-I03)",
                    )
                )
    return temuan


def _aturan_2_putusan_tanpa_bawaan(akar: Path) -> list[Temuan]:
    """Bidang putusan pada `ButirTayang` wajib tanpa nilai bawaan."""
    berkas = akar / BERKAS_PUTUSAN
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul putusan tidak ditemukan — menghapus gerbang kurasi bukan cara "
                "sah meloloskan pemeriksa ini (C-06)",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    kelas = _kelas_bernama(pohon, NAMA_BUTIR_TAYANG)
    if kelas is None:
        return [
            Temuan(
                berkas,
                0,
                f"{NAMA_BUTIR_TAYANG} tidak ditemukan pada gerbang putusan — tipe yang "
                "hilang bukan tipe yang aman, ia tipe yang penjagaannya pindah entah "
                "ke mana (C-06)",
            )
        ]

    for simpul in kelas.body:
        if not isinstance(simpul, ast.AnnAssign):
            continue
        if not isinstance(simpul.target, ast.Name):
            continue
        if simpul.target.id != NAMA_BIDANG_PUTUSAN:
            continue
        if simpul.value is not None:
            return [
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"bidang {NAMA_BIDANG_PUTUSAN} pada {NAMA_BUTIR_TAYANG} memiliki "
                    "nilai bawaan — butir yang lupa diputuskan kemudian terbentuk "
                    "sebagai butir yang disetujui, dan tidak satu uji perilaku pun "
                    "gagal karenanya (C-06)",
                )
            ]
        return []

    return [
        Temuan(
            berkas,
            kelas.lineno,
            f"{NAMA_BUTIR_TAYANG} tidak memiliki bidang {NAMA_BIDANG_PUTUSAN} — butir "
            "tayang yang tidak membawa putusannya tidak dapat ditelusuri kepada "
            "kurator mana pun (C-06, FR-I05)",
        )
    ]


def _kelas_bernama(pohon: ast.Module, nama: str) -> ast.ClassDef | None:
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ClassDef) and simpul.name == nama:
            return simpul
    return None
