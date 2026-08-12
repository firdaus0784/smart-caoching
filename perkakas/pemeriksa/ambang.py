"""Pemeriksa penyetelan ambang — C-16, R-08, R-11.

C-16 berbunyi: *"Ambang tidak disetel di luar prosedur kalibrasi `docs/D07.md`
BT-29. Bila tingkat penolakan validator terlalu tinggi, perbaiki pengambilan —
jangan longgarkan validator."*

Pasal ini lebih sulit diperiksa mesin daripada C-02 atau C-03, dan sebabnya
menarik: **C-16 melarang sebuah tindakan, bukan sebuah bentuk kode.** Menyetel
ambang dan mengalibrasi ambang menghasilkan diff yang persis sama. Yang dapat
dibaca kode hanyalah bekasnya.

Karena itu ketiga aturan di bawah tidak mengejar tindakannya melainkan
**menutup tempat-tempat tindakan itu tidak meninggalkan bekas.**

## Tiga aturan

1. **Angka ambang hanya pada rumah tetapan.** Berkas di luar `RUMAH_TETAPAN`
   yang menugaskan bilangan pecahan ke nama berawalan `AMBANG_` atau
   berakhiran `_AMBANG` adalah temuan. Ambang yang tersebar adalah ambang yang
   penyetelannya tidak terlihat pada satu tempat mana pun.

2. **`AmbangKecukupan` tidak memiliki nilai bawaan di mana pun pada `src/`.**
   D-07 Bagian 4.6 menyerahkan nilai tinggi dan menengah ke BT-29; sampai
   kalibrasi itu berlangsung, kekosongannya **yang benar**. Aturan ini gagal
   ketika seseorang mengisinya — termasuk ketika ia mengisinya dengan maksud
   baik, dan itu justru bentuk yang paling mungkin terjadi.

3. **Setiap tetapan pada rumah tetapan menyebut sumbernya.** Angka tanpa asal
   tidak dapat dibedakan dari angka yang disetel seseorang. Aturan ini yang
   membuat perbedaan antara *mengutip* dan *menyetel* dapat ditegakkan —
   menyalin 60 dari Cormack dkk. 2009 sah; menuliskan 60 tanpa menyebut dari
   mana tidak.

Aturan 3 juga yang menutup kelonggaran yang `RUMAH_TETAPAN` timbulkan: berkas
pada daftar itu dilewati sapuan nilai, sehingga tanpa aturan 3 ia menjadi
tempat aman bagi angka mana pun.

## Rumah tetapan tinggal di sini, bukan di `tests/`

Daftarnya lahir sebagai daftar putih uji pada fitur 003. Sejak fitur 007 ia
menjadi **aturan**, dan aturan tidak tinggal di `tests/` — uji yang
mengimpornya dari sana akan berbeda dari pemeriksa yang menyalinnya, dan yang
berbeda adalah yang tidak diperbarui.

## Batas yang diakui terbuka

Sama dengan pemeriksa C-02 dan C-03: ini pembacaan bentuk kode. Ambang yang
dibaca dari berkas konfigurasi saat jalan, atau dihitung dari ungkapan, lolos.
Yang menutup sisanya bukan pemeriksa melainkan `CatatanKalibrasi` yang wajib
pada `AmbangKecukupan` — ambang yang lupa membawa asal-usulnya tidak dapat
dibentuk sama sekali.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

_RUMAH_TETAPAN_NISBI = (
    Path("src") / "nlp" / "anotasi" / "ambang.py",
    Path("src") / "nlp" / "pelatihan" / "pembagian.py",
    Path("src") / "rag" / "pengambilan" / "tetapan.py",
)
"""Modul yang **sengaja** menjadi satu-satunya tempat sekelompok angka.

Daftar ini pendek dan wajib tetap pendek. Menambahnya berarti menyatakan ada
satu kelompok angka lagi yang dimiliki dokumen tertentu, dan pernyataan itu
keputusan — bukan cara meloloskan berkas yang kebetulan menyalakan sapuan.

`pembagian.py` masuk karena tabrakan yang sungguhan: porsi latih D-08 bernilai
0,70, sama dengan ambang Kappa D-03. `tetapan.py` masuk karena tabrakan sejenis
sekaligus karena ia rumah bagi angka D-07 Bagian 4.4.
"""

_PETUNJUK_SUMBER = ("D-0", "D0", "ADR-", "ADR", "Cormack", "Robertson", "BT-")
"""Penanda bahwa sebuah uraian menyebut asal angkanya.

Sengaja longgar pada ejaan: proyek ini menulis dokumen yang sama sebagai
"D-07" pada prosa dan "docs/D07.md" pada jalur berkas. Pemeriksa yang hanya
mengenali satu ejaan menuntut penulisnya menghafal ejaan mana yang lolos, dan
yang dihafal salah adalah yang dipakai.
"""

_NAMA_AMBANG_KECUKUPAN = "AmbangKecukupan"


def rumah_tetapan(akar: Path) -> frozenset[Path]:
    """Jalur mutlak rumah tetapan pada sebuah akar repositori."""
    return frozenset((akar / nisbi).resolve() for nisbi in _RUMAH_TETAPAN_NISBI)


def periksa_ambang(akar: Path) -> list[Temuan]:
    """Ketiga aturan C-16 — lihat uraian modul."""
    rumah = rumah_tetapan(akar)
    temuan: list[Temuan] = []
    temuan.extend(_aturan_1_ambang_di_luar_rumah(akar, rumah))
    temuan.extend(_aturan_2_tanpa_ambang_kecukupan_bawaan(akar))
    temuan.extend(_aturan_3_tetapan_menyebut_sumbernya(rumah))
    return temuan


def _aturan_1_ambang_di_luar_rumah(akar: Path, rumah: frozenset[Path]) -> list[Temuan]:
    """Angka ambang hanya pada rumah tetapan."""
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if berkas.resolve() in rumah:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if not isinstance(simpul, ast.Assign):
                continue
            if not isinstance(simpul.value, ast.Constant):
                continue
            if not isinstance(simpul.value.value, float):
                continue
            for sasaran in simpul.targets:
                if not isinstance(sasaran, ast.Name):
                    continue
                if _bernama_ambang(sasaran.id):
                    temuan.append(
                        Temuan(
                            berkas,
                            simpul.lineno,
                            f"ambang {sasaran.id} berada di luar rumah tetapan — "
                            "ambang yang tersebar adalah ambang yang penyetelannya "
                            "tidak terlihat pada satu tempat mana pun (C-16)",
                        )
                    )
    return temuan


def _bernama_ambang(nama: str) -> bool:
    return nama.startswith("AMBANG_") or nama.endswith("_AMBANG")


def _aturan_2_tanpa_ambang_kecukupan_bawaan(akar: Path) -> list[Temuan]:
    """`AmbangKecukupan` tidak dibentuk dengan nilai bawaan di mana pun pada `src/`.

    Yang dicari: pemberian nilai bawaan pada parameter fungsi yang bertipe
    `AmbangKecukupan`, dan tetapan tingkat modul yang membentuknya. Keduanya
    bentuk yang membuat ambang tersedia tanpa seorang pun memilihnya.
    """
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if isinstance(simpul, ast.FunctionDef):
                temuan.extend(_bawaan_pada_parameter(berkas, simpul))
            if isinstance(simpul, ast.Assign) and _membentuk_ambang(simpul.value):
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        f"{_NAMA_AMBANG_KECUKUPAN} dibentuk sebagai tetapan modul — "
                        "nilai tinggi dan menengah ditetapkan BT-29 atas gold set, "
                        "dan sampai saat itu kekosongannya yang benar (C-16, D-07 "
                        "Bagian 4.6)",
                    )
                )
    return temuan


def _bawaan_pada_parameter(berkas: Path, fungsi: ast.FunctionDef) -> list[Temuan]:
    argumen = [*fungsi.args.args, *fungsi.args.kwonlyargs]
    bernilai_ambang = {
        a.arg
        for a in argumen
        if a.annotation is not None and _menyebut_ambang_kecukupan(a.annotation)
    }
    if not bernilai_ambang:
        return []
    bawaan = [*fungsi.args.defaults, *(d for d in fungsi.args.kw_defaults if d is not None)]
    if not bawaan:
        return []
    return [
        Temuan(
            berkas,
            fungsi.lineno,
            f"{fungsi.name} memberi nilai bawaan pada parameter "
            f"{_NAMA_AMBANG_KECUKUPAN} — parameter berbawaan akan berubah menjadi "
            "'tanpa ambang berarti tanpa batas' pada pemanggilan pertama yang lupa "
            "mengisinya (C-16, R-11)",
        )
    ]


def _menyebut_ambang_kecukupan(simpul: ast.AST) -> bool:
    for anak in ast.walk(simpul):
        if isinstance(anak, ast.Name) and anak.id == _NAMA_AMBANG_KECUKUPAN:
            return True
        if isinstance(anak, ast.Constant) and anak.value == _NAMA_AMBANG_KECUKUPAN:
            return True
    return False


def _membentuk_ambang(simpul: ast.AST) -> bool:
    return (
        isinstance(simpul, ast.Call)
        and isinstance(simpul.func, ast.Name)
        and simpul.func.id == _NAMA_AMBANG_KECUKUPAN
    )


def _aturan_3_tetapan_menyebut_sumbernya(rumah: frozenset[Path]) -> list[Temuan]:
    """Setiap tetapan pada rumah tetapan menyebut dokumen atau makalah asalnya."""
    temuan: list[Temuan] = []
    for berkas in sorted(rumah):
        if not berkas.is_file():
            temuan.append(
                Temuan(
                    berkas,
                    0,
                    "rumah tetapan tidak ditemukan — menghapus tempat angka dimiliki "
                    "bukan cara sah meloloskan pemeriksa ini (C-16)",
                )
            )
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for nama, baris, uraian in _tetapan_beruraian(pohon):
            if not any(petunjuk in uraian for petunjuk in _PETUNJUK_SUMBER):
                temuan.append(
                    Temuan(
                        berkas,
                        baris,
                        f"tetapan {nama} tidak menyebut asalnya — angka tanpa asal "
                        "tidak dapat dibedakan dari angka yang disetel seseorang, "
                        "dan itu perbedaan yang C-16 tegakkan",
                    )
                )
    return temuan


def _tetapan_beruraian(pohon: ast.Module) -> list[tuple[str, int, str]]:
    """Tetapan tingkat modul beserta uraian yang menyertainya.

    Uraian dibaca dari untai yang **langsung** mengikuti pemberian nilai —
    bentuk uraian atribut. Komentar sengaja tidak dibaca: komentar dapat
    berpindah saat kode disunting, uraian melekat pada tetapannya.
    """
    hasil: list[tuple[str, int, str]] = []
    tertunda: tuple[str, int] | None = None
    for simpul in pohon.body:
        if isinstance(simpul, ast.Assign):
            nama = [t.id for t in simpul.targets if isinstance(t, ast.Name)]
            umum = [n for n in nama if not n.startswith("_")]
            if umum:
                if tertunda is not None:
                    hasil.append((tertunda[0], tertunda[1], ""))
                tertunda = (umum[0], simpul.lineno)
                continue
        if (
            tertunda is not None
            and isinstance(simpul, ast.Expr)
            and isinstance(simpul.value, ast.Constant)
            and isinstance(simpul.value.value, str)
        ):
            hasil.append((tertunda[0], tertunda[1], simpul.value.value))
            tertunda = None
            continue
        if tertunda is not None:
            hasil.append((tertunda[0], tertunda[1], ""))
            tertunda = None
    if tertunda is not None:
        hasil.append((tertunda[0], tertunda[1], ""))
    return hasil
