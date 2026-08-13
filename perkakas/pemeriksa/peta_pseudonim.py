"""Pemeriksa peta pseudonim — C-05, R-09, KA-03.

C-05 berbunyi: *"Kunci pemetaan pseudonim tidak berada pada basis data yang
sama dengan data perilaku, dan tidak terjangkau dari layanan aplikasi."*

Separuh pertama adalah keputusan penyebaran D-09 dan tidak terbaca kode.
Separuh kedua terbaca, dan ketiga aturan di bawah menutup tempat-tempat ia
runtuh tanpa terlihat.

## Tiga aturan

1. **`KredensialPseudonim` tidak dibentuk di mana pun pada `src/`.** Kredensial
   yang dibentuk layanan aplikasi adalah kredensial yang dimiliki layanan
   aplikasi, betapa pun tipenya terpisah. Bentuk yang sama dengan aturan
   `Instruksi` ADR-13 dan `ButirTayang` C-06 — dibalik arahnya: yang itu
   membatasi **di mana** boleh dibentuk, yang ini melarang **di mana pun**.

2. **Peta pseudonim tidak diimpor modul lain pada `src/`.** Aturan 1 hanya
   menutup pembentukan kredensialnya; modul yang mengimpor `PetaPseudonim`
   sudah cukup dekat untuk memanggilnya dengan kredensial yang diteruskan dari
   tempat lain.

3. **`Area` tetap bernilai persis dua.** Memindahkan peta pseudonim menjadi
   nilai ketiga pada `Area` memuaskan kedua aturan pertama sambil membatalkan
   C-05 sepenuhnya — dan AG-04 melarangnya lebih dulu, sebab `Area` mewujudkan
   `dokumen_sumber.area_simpan` milik `docs/D14.md` Bagian 5.1.

Aturan 3 menutup lubang dua aturan pertama, bentuk yang sama dengan aturan
VS-08 pada pemeriksa C-19 (fitur 008): kelengkapan yang dipuaskan dengan
memindahkan sesuatu ke tempat yang lebih longgar.

## Batas yang diakui terbuka

Sama dengan pemeriksa C-02, C-03, C-06, C-16, dan C-19: ini pembacaan bentuk
kode. Pembentukan lewat `getattr` atau muat dinamis lolos. Yang menutup
sisanya bukan pemeriksa melainkan pemisahan basis data D-09 dan klausul RE-05.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_PSEUDONIM = Path("src") / "penyimpanan" / "pseudonim.py"
BERKAS_AREA = Path("src") / "penyimpanan" / "area.py"

NAMA_KREDENSIAL = "KredensialPseudonim"
NAMA_PETA = "PetaPseudonim"
NAMA_ENUM_AREA = "Area"

NILAI_AREA_D14: frozenset[str] = frozenset({"karantina", "korpus"})
"""Kedua nilai `dokumen_sumber.area_simpan` — `docs/D14.md` Bagian 5.1.

Ditulis di sini, bukan dibaca dari enumnya. Pemeriksa yang membaca daftar dari
hal yang diperiksanya hanya membuktikan daftar sama dengan dirinya sendiri —
dan akan tetap lulus ketika nilai ketiga ditambahkan ke keduanya.
"""


def periksa_peta_pseudonim(akar: Path) -> list[Temuan]:
    """Ketiga aturan C-05 — lihat uraian modul."""
    temuan: list[Temuan] = []
    temuan.extend(_aturan_1_kredensial_tidak_dibentuk(akar))
    temuan.extend(_aturan_2_peta_tidak_diimpor(akar))
    temuan.extend(_aturan_3_area_tetap_dua_nilai(akar))
    return temuan


def _aturan_1_kredensial_tidak_dibentuk(akar: Path) -> list[Temuan]:
    """`KredensialPseudonim` tidak dibentuk di mana pun pada `src/`."""
    pemilik = (akar / BERKAS_PSEUDONIM).resolve()
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == NAMA_KREDENSIAL
            ):
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        f"{NAMA_KREDENSIAL} dibentuk pada src/ — kredensial yang "
                        "dibentuk layanan aplikasi adalah kredensial yang dimilikinya, "
                        "betapa pun tipenya terpisah (C-05, KA-03)",
                    )
                )
    if not pemilik.is_file():
        temuan.append(
            Temuan(
                akar / BERKAS_PSEUDONIM,
                0,
                "modul peta pseudonim tidak ditemukan — menghapus tempat kunci "
                "dipisahkan bukan cara sah meloloskan pemeriksa ini (C-05)",
            )
        )
    return temuan


def _aturan_2_peta_tidak_diimpor(akar: Path) -> list[Temuan]:
    """Peta pseudonim tidak diimpor modul lain pada `src/`."""
    pemilik = (akar / BERKAS_PSEUDONIM).resolve()
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if berkas.resolve() == pemilik:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if not isinstance(simpul, ast.ImportFrom):
                continue
            if simpul.module is None or "pseudonim" not in simpul.module:
                continue
            nama = sorted(a.name for a in simpul.names)
            temuan.append(
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"peta pseudonim diimpor di luar modulnya: {nama} — modul yang "
                    "mengimpornya sudah cukup dekat untuk memanggilnya dengan "
                    "kredensial yang diteruskan dari tempat lain (C-05)",
                )
            )
    return temuan


def _aturan_3_area_tetap_dua_nilai(akar: Path) -> list[Temuan]:
    """`Area` bernilai persis dua — AG-04, D-14 Bagian 5.1."""
    berkas = akar / BERKAS_AREA
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul area tidak ditemukan — pemeriksaan nilai enum tidak dapat "
                "dijalankan (C-05, AG-04)",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.ClassDef) or simpul.name != NAMA_ENUM_AREA:
            continue
        nilai = {
            anak.value.value
            for anak in simpul.body
            if isinstance(anak, ast.Assign)
            and isinstance(anak.value, ast.Constant)
            and isinstance(anak.value.value, str)
        }
        if nilai != NILAI_AREA_D14:
            return [
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"{NAMA_ENUM_AREA} bernilai {sorted(nilai)}, seharusnya "
                    f"{sorted(NILAI_AREA_D14)} — memindahkan peta pseudonim menjadi "
                    "nilai ketiga membatalkan C-05 sambil memuaskan dua aturan "
                    "pertama, dan AG-04 melarangnya lebih dulu",
                )
            ]
        return []

    return [
        Temuan(
            berkas,
            0,
            f"{NAMA_ENUM_AREA} tidak ditemukan — enum yang hilang bukan enum yang "
            "aman (C-05, AG-04)",
        )
    ]
