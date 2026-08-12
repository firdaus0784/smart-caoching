"""Pemeriksa bentuk tanggapan dan daftar rute — C-20, AG-02, AG-03.

C-20 berbunyi: *"Bentuk tanggapan dan daftar rute mengikuti `docs/D14.md`.
Penambahan bidang pada tanggapan `/api/v1/tanya` dilarang tanpa persetujuan
manusia — bentuk itu adalah tempat C-02, C-07, dan C-19 diwujudkan."*

Dua kewajiban, dan keduanya diperiksa dari **dokumennya**, bukan dari salinan.

## Aturan 1 · Bidang tanggapan persis blok JSON D-14 Bagian 4.1

Kurang maupun lebih keduanya temuan. AG-03 melarang penambahan; pengurangan
menghapus tempat sebuah pasal diwujudkan.

Daftar bidangnya **tidak ditulis pada berkas ini**. Ia diurai dari blok JSON
pada D-14 saat pemeriksa berjalan. Pemeriksa yang menyalin daftarnya hanya
membuktikan dua salinan sama — termasuk ketika keduanya sudah menyimpang dari
pemiliknya. Bentuk yang sama dengan pemeriksa arah arsitektur, yang membaca
tepinya dari `AGENTS.md`.

## Aturan 2 · Tidak ada rute di luar D-14 Bagian 3

Hari ini `src/api/` belum ada, sehingga nol rute dan nol pelanggaran.

**Itu pernyataan yang benar, bukan pemeriksaan yang hampa**, dan pembedaannya
perlu dinyatakan sebab bentuknya mirip kekeliruan C-01 pada fitur 008 dan
kesimpulannya berlawanan:

- C-01 menuntut sesuatu **ada dan benar** — sitasi terverifikasi. Menandainya
  lulus tanpa VS-03 adalah melaporkan pemeriksaan yang tidak berjalan.
- C-20 aturan 2 menuntut sesuatu **tidak ada** — rute di luar D-14. "Nol rute,
  karena itu nol rute terlarang" benar tanpa syarat.

Preseden yang sudah berjalan: pemeriksa C-15 lulus atas basis data yang belum
memiliki satu tabel pun.

Aturan 1 menjadi nyata pada fitur 009, sehingga C-20 tidak berpindah atas
kekosongan saja.

## Batas yang diakui terbuka

Sama dengan pemeriksa C-02, C-03, C-16, dan C-19: ini pembacaan bentuk kode.
Rute yang didaftarkan lewat pemanggilan dinamis lolos. Yang menutup sisanya
bukan pemeriksa melainkan AG-05, yang menuntut setiap rute baru diuji sebagai
UK-15 — dan uji itu ditulis manusia.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_D14 = Path("docs") / "D14.md"
BERKAS_TANGGAPAN = Path("src") / "rag" / "jawaban" / "tanggapan.py"
DIREKTORI_RUTE = Path("src") / "api"

NAMA_MODEL_TANGGAPAN = "Tanggapan"
_JUDUL_BAGIAN = "### 4.1 Tanggapan Jawaban"
_POLA_JSON = re.compile(r"```json\n(.*?)\n```", re.S)
_POLA_RUTE = re.compile(r"^\s*\|\s*(?:GET|POST|PUT|DELETE|PATCH)\s*\|\s*`([^`]+)`", re.M)
_DEKORATOR_RUTE = frozenset({"get", "post", "put", "delete", "patch"})


def bidang_d14(teks: str) -> set[str]:
    """Kunci blok JSON D-14 Bagian 4.1 — sumbernya, bukan salinannya."""
    awal = teks.find(_JUDUL_BAGIAN)
    if awal < 0:
        return set()
    blok = _POLA_JSON.search(teks[awal:])
    if blok is None:
        return set()
    return set(json.loads(blok.group(1)).keys())


def rute_d14(teks: str) -> set[str]:
    """Rute pada tabel D-14 Bagian 3."""
    return set(_POLA_RUTE.findall(teks))


def periksa_bentuk_tanggapan(akar: Path) -> list[Temuan]:
    """Kedua aturan C-20 — lihat uraian modul."""
    berkas_d14 = akar / BERKAS_D14
    if not berkas_d14.is_file():
        return [
            Temuan(
                berkas_d14,
                0,
                "docs/D14.md tidak ditemukan — menghapus dokumen yang memiliki "
                "kontraknya bukan cara sah meloloskan pemeriksa ini (C-20)",
            )
        ]

    teks = berkas_d14.read_text(encoding="utf-8")
    temuan: list[Temuan] = []
    temuan.extend(_aturan_1_bidang_tanggapan(akar, teks))
    temuan.extend(_aturan_2_rute_terdaftar(akar, teks))
    return temuan


def _aturan_1_bidang_tanggapan(akar: Path, teks_d14: str) -> list[Temuan]:
    """Bidang `Tanggapan` sama persis dengan kunci blok JSON D-14."""
    diharapkan = bidang_d14(teks_d14)
    if not diharapkan:
        return [
            Temuan(
                akar / BERKAS_D14,
                0,
                "blok JSON Bagian 4.1 tidak terbaca pada D-14 — pemeriksa yang tidak "
                "menemukan kontraknya tidak memeriksa apa pun (C-20)",
            )
        ]

    berkas = akar / BERKAS_TANGGAPAN
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul tanggapan tidak ditemukan — menghapus tempat bentuk tanggapan "
                "diwujudkan bukan cara sah meloloskan pemeriksa ini (C-20)",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.ClassDef) or simpul.name != NAMA_MODEL_TANGGAPAN:
            continue
        ada = {
            anak.target.id
            for anak in simpul.body
            if isinstance(anak, ast.AnnAssign) and isinstance(anak.target, ast.Name)
        }
        kurang = diharapkan - ada
        lebih = ada - diharapkan
        if kurang or lebih:
            return [
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"bidang {NAMA_MODEL_TANGGAPAN} tidak sama dengan D-14 Bagian 4.1; "
                    f"kurang: {sorted(kurang)}, lebih: {sorted(lebih)} — AG-03 melarang "
                    "penambahan, dan pengurangan menghapus tempat C-02, C-07, atau "
                    "C-19 diwujudkan",
                )
            ]
        return []

    return [
        Temuan(
            berkas,
            0,
            f"kelas {NAMA_MODEL_TANGGAPAN} tidak ditemukan — aturan 1 menjadi tidak "
            "berarti (C-20)",
        )
    ]


def _aturan_2_rute_terdaftar(akar: Path, teks_d14: str) -> list[Temuan]:
    """Tidak ada rute di luar D-14 Bagian 3 — AG-02.

    Nol rute menghasilkan nol temuan, dan itu **benar**: aturan ini melarang
    keberadaan, bukan menuntut keberadaan. Lihat uraian modul.
    """
    sah = rute_d14(teks_d14)
    if not sah:
        return [
            Temuan(
                akar / BERKAS_D14,
                0,
                "tabel rute Bagian 3 tidak terbaca pada D-14 — pemeriksa yang tidak "
                "menemukan daftar rutenya tidak memeriksa apa pun (C-20, AG-02)",
            )
        ]

    direktori = akar / DIREKTORI_RUTE
    if not direktori.is_dir():
        return []

    temuan: list[Temuan] = []
    for berkas in berkas_python(direktori):
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if not isinstance(simpul, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for hias in simpul.decorator_list:
                jalur = _jalur_rute(hias)
                if jalur is not None and jalur not in sah:
                    temuan.append(
                        Temuan(
                            berkas,
                            simpul.lineno,
                            f"rute `{jalur}` tidak ada pada docs/D14.md Bagian 3 — "
                            "AG-02 melarang agen menambah rute, dan rute yang tidak "
                            "tercatat adalah rute yang perannya tidak pernah "
                            "ditetapkan (AG-05)",
                        )
                    )
    return temuan


def _jalur_rute(hias: ast.expr) -> str | None:
    """Jalur pada dekorator `@router.post("/…")`, atau `None`."""
    if not isinstance(hias, ast.Call):
        return None
    if not isinstance(hias.func, ast.Attribute) or hias.func.attr not in _DEKORATOR_RUTE:
        return None
    if not hias.args:
        return None
    pertama = hias.args[0]
    if isinstance(pertama, ast.Constant) and isinstance(pertama.value, str):
        return pertama.value
    return None
