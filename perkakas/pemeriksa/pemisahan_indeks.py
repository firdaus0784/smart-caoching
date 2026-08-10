"""Pemeriksa pemisahan indeks menurut lisensi — C-02, FR-D06, KL-01.

C-02 berbunyi dua kalimat, dan kalimat keduanya yang menentukan bentuk
pemeriksa ini: *"Pemisahan pada tingkat indeks, bukan penyaringan saat kueri."*

Penyaringan saat kueri terasa cukup — satu klausa, mudah dibaca, mudah diuji.
Yang membuatnya tidak cukup: klausa itu ada pada **setiap** kueri, dan satu
kueri yang lupa memuatnya tidak menghasilkan galat apa pun. Ia menghasilkan
jawaban yang lebih lengkap, dan jawaban yang lebih lengkap tidak pernah terasa
seperti kekeliruan sampai audit lisensi.

## Tiga aturan, dan masing-masing menutup jalan yang berbeda

1. **`PEMANGGIL_LLM` tidak menjangkau indeks metadata.** Di sinilah C-02
   sesungguhnya berdiri: konteks yang dikirim ke LLM disusun jalur ini, dan
   yang tidak dijangkau kredensialnya tidak dapat masuk konteks.
2. **`src/llm/` tidak menyebut indeks metadata sama sekali.** Sengaja lebih
   luas daripada pelanggarannya — penyebutan yang belum membaca apa pun tetap
   salah, sebab langkah berikutnya tinggal satu baris. Bentuk yang sama dengan
   aturan 4 pemeriksa C-03.
3. **Kredensial berbentuk tetapan, bukan hitungan.** Himpunan indeks yang
   dihitung dari sebuah syarat adalah penyaringan yang menyamar sebagai
   pemisahan — persis yang C-02 kalimat kedua tolak.

## Yang sengaja tidak diperiksa

`src/rag/` dan `src/api/` **boleh** menyebut indeks metadata. `docs/D14.md`
Bagian 6 menetapkan `bacaan_lanjutan` sebagai tempat satu-satunya bagi sumber
`indeks_metadata`, dan blok itu disusun jalur penjawaban. Melarangnya di sana
akan menutup pekerjaan yang D-14 tuntut — dan penjagaan yang menutup pekerjaan
sah akan dimatikan orang, lalu yang mati bersamanya adalah aturan 1 dan 2.

Batas yang diakui terbuka, sama dengan pemeriksa C-03: ini pembacaan bentuk
kode. Kredensial yang disusun lewat `getattr` atau dibaca dari berkas tetap
lolos. Yang menutup sisanya bukan pemeriksa melainkan bidang `indeks` yang
wajib pada `Kredensial` — kredensial yang lupa diisi tidak menjangkau apa pun.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_KREDENSIAL = Path("src") / "penyimpanan" / "kredensial_baku.py"

JALUR_TANPA_METADATA = ("src/llm",)
"""Jalur yang tidak boleh menyebut indeks metadata sama sekali.

Hanya `src/llm` — lihat "Yang sengaja tidak diperiksa" pada uraian modul.
"""

KREDENSIAL_TANPA_METADATA = "PEMANGGIL_LLM"
_NAMA_METADATA = "METADATA"


def _di_jalur(berkas: Path, akar: Path, jalur: tuple[str, ...]) -> bool:
    relatif = berkas.relative_to(akar).as_posix()
    return any(relatif.startswith(j + "/") for j in jalur)


def _menyebut_metadata(simpul: ast.AST) -> bool:
    """`IndeksTujuan.METADATA` maupun untai `"metadata"` sebagai indeks."""
    for anak in ast.walk(simpul):
        if isinstance(anak, ast.Attribute) and anak.attr == _NAMA_METADATA:
            return True
        if isinstance(anak, ast.Name) and anak.id == _NAMA_METADATA:
            return True
    return False


def periksa_pemisahan_indeks(akar: Path) -> list[Temuan]:
    """Tiga aturan C-02 — lihat uraian modul."""
    temuan: list[Temuan] = []
    temuan.extend(_periksa_kredensial(akar))
    temuan.extend(_periksa_jalur_llm(akar))
    return temuan


def _periksa_kredensial(akar: Path) -> list[Temuan]:
    """Aturan 1 dan 3, keduanya pada `kredensial_baku.py`."""
    berkas = akar / BERKAS_KREDENSIAL
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "kredensial_baku.py tidak ditemukan — menghapus tempat pemisahan "
                "diwujudkan bukan cara sah meloloskan pemeriksa ini",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    ditemukan = False
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.Assign):
            continue
        nama = [t.id for t in simpul.targets if isinstance(t, ast.Name)]
        if KREDENSIAL_TANPA_METADATA not in nama:
            continue
        ditemukan = True
        for kata in _kata_kunci(simpul.value):
            if kata.arg != "indeks":
                continue
            if _menyebut_metadata(kata.value):
                temuan_metadata = Temuan(
                    berkas,
                    simpul.lineno,
                    f"{KREDENSIAL_TANPA_METADATA} menjangkau indeks metadata — "
                    "konteks yang dikirim ke LLM disusun jalur ini, dan segmen "
                    "berlisensi tertutup tidak boleh masuk ke sana (C-02, FR-D06)",
                )
                return [temuan_metadata]
            if not _tetapan(kata.value):
                return [
                    Temuan(
                        berkas,
                        simpul.lineno,
                        f"himpunan indeks {KREDENSIAL_TANPA_METADATA} dihitung dari "
                        "sebuah syarat — itu penyaringan yang menyamar sebagai "
                        "pemisahan, dan C-02 kalimat kedua menolaknya",
                    )
                ]

    if not ditemukan:
        return [
            Temuan(
                berkas,
                0,
                f"{KREDENSIAL_TANPA_METADATA} tidak ditemukan pada kredensial baku — "
                "pemisahan indeks tidak dapat diperiksa tanpa kredensial yang "
                "menegakkannya",
            )
        ]
    return []


def _kata_kunci(simpul: ast.AST) -> list[ast.keyword]:
    return [k for k in ast.walk(simpul) if isinstance(k, ast.keyword)]


def _tetapan(simpul: ast.AST) -> bool:
    """Himpunan yang disusun langsung, bukan hasil percabangan.

    `frozenset({...})` sah; `frozenset({...}) if syarat else ...` tidak.
    """
    return not any(isinstance(anak, ast.IfExp) for anak in ast.walk(simpul))


def _periksa_jalur_llm(akar: Path) -> list[Temuan]:
    """Aturan 2 — `src/llm/` tidak menyebut indeks metadata sama sekali."""
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if not _di_jalur(berkas, akar, JALUR_TANPA_METADATA):
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if isinstance(simpul, ast.Attribute) and simpul.attr == _NAMA_METADATA:
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        "jalur pemanggilan model menyebut indeks metadata — "
                        "penyebutan yang belum membaca apa pun tetap salah, sebab "
                        "langkah berikutnya tinggal satu baris (C-02)",
                    )
                )
    return temuan
