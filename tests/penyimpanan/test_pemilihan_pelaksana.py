"""Pemilihan pelaksana dilakukan pemanggil — T-6 fitur 024, R-06.

R-06 berbunyi: selama peladen belum tersedia sistem tetap dapat dijalankan
memakai `PenyimpanTiruan`, dan pemilihan pelaksana **wajib dilakukan
pemanggil** — bukan ditentukan pelaksana itu sendiri.

## Mengapa ini diuji atas bentuk kode, bukan atas perilaku

Perilaku yang benar hari ini tidak menghalangi seseorang menambahkan
`if os.environ.get("PAKAI_POSTGRES")` besok, dan penambahan itu tidak akan
menggagalkan satu uji perilaku pun — ia justru membuat uji lama tetap lulus
sambil memindahkan keputusan penyebaran ke dalam pustaka.

Keputusan yang tersembunyi di dalam pustaka adalah keputusan yang tidak dapat
diuji pemanggil, tidak terbaca pada berkas penyebaran, dan berbeda diam-diam
antar lingkungan. Bentuk yang sama dengan alasan C-16 melarang ambang disetel
di luar prosedurnya.

## Empat aturan

1. `src/penyimpanan/` tidak membaca peubah lingkungan sama sekali, **dan tidak
   mengimpor `os` maupun `dotenv`**. Impor tanpa pemakaian tidak melanggar
   apa pun — uji mutasi membuktikannya diam, dan diamnya benar. Ia dilarang
   karena ia langkah pertama, dan di lapisan ini tidak ada gunanya yang sah:
   jalur yang ditutup sebelum ditempuh lebih murah daripada jalur yang ditutup
   sesudah seseorang setengah jalan.
2. Tidak ada modul `src/` yang **menyusun** pelaksana penyimpanan — penyusunan
   terjadi pada titik jalan, di luar kode yang disebarkan.
3. Kedua pelaksana menerima ketergantungannya lewat `__init__` tanpa nilai
   bawaan yang memungkinkan mereka menyusun diri sendiri.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[2]
PENYIMPANAN = AKAR / "src" / "penyimpanan"

PEMBACA_LINGKUNGAN = ("environ", "getenv", "load_dotenv", "dotenv_values")
MODUL_LINGKUNGAN = ("os", "dotenv")
PELAKSANA = ("PenyimpanTiruan", "PenyimpanPostgres", "PetaPseudonimPostgres")


def _berkas_python(cabang: Path) -> list[Path]:
    return sorted(b for b in cabang.rglob("*.py") if "__pycache__" not in b.parts)


# ── Aturan 1 · tanpa peubah lingkungan ───────────────────────────────


@pytest.mark.parametrize("berkas", _berkas_python(PENYIMPANAN), ids=lambda b: b.name)
def test_penyimpanan_tidak_membaca_lingkungan(berkas: Path) -> None:
    isi = berkas.read_text(encoding="utf-8")
    pohon = ast.parse(isi)
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.Attribute) and simpul.attr in PEMBACA_LINGKUNGAN:
            pytest.fail(f"{berkas.name}:{simpul.lineno} membaca lingkungan")
        if isinstance(simpul, ast.Name) and simpul.id in PEMBACA_LINGKUNGAN:
            pytest.fail(f"{berkas.name}:{simpul.lineno} membaca lingkungan")


@pytest.mark.parametrize("berkas", _berkas_python(PENYIMPANAN), ids=lambda b: b.name)
def test_penyimpanan_tidak_mengimpor_os(berkas: Path) -> None:
    """Jalur ditutup sebelum ditempuh. Lihat aturan 1 pada uraian berkas."""
    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.Import):
            for nama in simpul.names:
                assert nama.name.split(".")[0] not in MODUL_LINGKUNGAN, (
                    f"{berkas.name}:{simpul.lineno} mengimpor {nama.name}"
                )
        if isinstance(simpul, ast.ImportFrom) and simpul.module:
            assert simpul.module.split(".")[0] not in MODUL_LINGKUNGAN, (
                f"{berkas.name}:{simpul.lineno} mengimpor dari {simpul.module}"
            )


# ── Aturan 2 · src/ tidak menyusun pelaksana ─────────────────────────


def test_tidak_ada_modul_src_yang_menyusun_pelaksana() -> None:
    """Penyusunan terjadi pada titik jalan, di luar kode yang disebarkan.

    Modul `src/` yang menyusun pelaksananya sendiri memilih untuk pemanggilnya
    — dan pilihan itu tidak akan terbaca pada berkas penyebaran mana pun.
    """
    tersangkut: list[str] = []
    for berkas in _berkas_python(AKAR / "src"):
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id in PELAKSANA
            ):
                tersangkut.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno} {simpul.func.id}()")
    assert not tersangkut, "src/ menyusun pelaksana penyimpanan: " + "; ".join(tersangkut)


# ── Aturan 3 · ketergantungan disuntikkan, tanpa bawaan yang menyusun ─


@pytest.mark.parametrize(
    ("modul", "kelas", "parameter"),
    [
        ("postgres.py", "PenyimpanPostgres", "sambungan"),
        ("pseudonim.py", "PetaPseudonimPostgres", "sambungan"),
    ],
)
def test_sambungan_wajib_diberikan_tanpa_bawaan(modul: str, kelas: str, parameter: str) -> None:
    """Parameter berbawaan di sini akan berubah menjadi "tanpa sambungan
    berarti susun sendiri" pada pemanggilan pertama yang lupa mengisinya."""
    pohon = ast.parse((PENYIMPANAN / modul).read_text(encoding="utf-8"))
    definisi = next(s for s in ast.walk(pohon) if isinstance(s, ast.ClassDef) and s.name == kelas)
    init = next(s for s in definisi.body if isinstance(s, ast.FunctionDef) and s.name == "__init__")
    posisi = [a.arg for a in init.args.args]
    assert parameter in posisi, f"{kelas}.__init__ tidak menerima {parameter!r}"

    # nilai bawaan menempel pada argumen terakhir; hitung dari belakang
    berbawaan = set(posisi[len(posisi) - len(init.args.defaults) :])
    assert parameter not in berbawaan, (
        f"{kelas}.__init__({parameter}=...) berbawaan — pelaksana dapat menyusun dirinya sendiri"
    )


def test_tiruan_tetap_dapat_dipakai_tanpa_peladen() -> None:
    """R-06 sisi sebaliknya: pilihan tiruan tetap ada, dan tidak menuntut apa pun."""
    from src.penyimpanan.tiruan import PenyimpanTiruan

    assert PenyimpanTiruan() is not None
