"""Uji kamus enum segmen — A-1 fitur 008, `docs/D14.md` Bagian 5.

**Berkas ini lahir dari kekeliruan.** `IndeksTujuan` ditulis dua kali:
`src/llm/tipe.py` pada fitur 001, lalu `src/penyimpanan/indeks.py` pada fitur
006 — oleh saya, tanpa memeriksa apakah ia sudah ada. Tidak satu pun gerbang
menangkapnya selama dua fitur.

Yang membuatnya lebih dari kerapian: **enum itu tempat C-02 terbaca.** Dua
definisi berarti perubahan D-14 kelak dapat memperbarui satu dan melewatkan
yang lain, dan tidak satu uji pun gagal karenanya. Kalimat proyek ini sendiri,
diulang pada enam berkas: *yang berbeda adalah yang tidak diperbarui.*

Uji pertama di bawah adalah yang menjaga agar kekeliruan itu tidak terulang.
Ia menyapu seluruh `src/` pada tingkat AST — bukan hanya memeriksa bahwa
`src/kamus/` benar, sebab kekeliruannya bukan pada modul yang benar melainkan
pada modul kedua yang tidak seorang pun sadari ada.
"""

import ast
from pathlib import Path

import pytest
from src.kamus.segmen import (
    PERINGKAT_LEMAH,
    IndeksTujuan,
    Peringkat,
    StatusKeberlakuan,
)

AKAR = Path(__file__).resolve().parents[2]

NAMA_KAMUS = ("IndeksTujuan", "Peringkat", "StatusKeberlakuan")


def _berkas_sumber() -> list[Path]:
    return sorted((AKAR / "src").rglob("*.py"))


@pytest.mark.parametrize("nama", NAMA_KAMUS)
def test_setiap_enum_kamus_hanya_didefinisikan_satu_kali(nama: str) -> None:
    """**Uji terpenting berkas ini.**

    Disapu pada tingkat AST atas seluruh `src/`. Uji yang hanya memeriksa
    `src/kamus/` akan lulus pada hari kekembaran berikutnya dibuat — sebab
    modul yang benar tetap benar.
    """
    tempat = []
    for berkas in _berkas_sumber():
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if isinstance(simpul, ast.ClassDef) and simpul.name == nama:
                tempat.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno}")
    assert len(tempat) == 1, f"{nama} didefinisikan {len(tempat)} kali: " + ", ".join(tempat)


def test_enum_kamus_didefinisikan_pada_src_kamus() -> None:
    """Satu definisi saja tidak cukup — ia wajib berada di kamus.

    Tanpa uji ini, memindahkan enumnya kembali ke `src/llm/` akan lolos: ia
    tetap satu definisi.
    """
    rumah = (AKAR / "src" / "kamus" / "segmen.py").read_text(encoding="utf-8")
    for nama in NAMA_KAMUS:
        assert f"class {nama}" in rumah


def test_kamus_tidak_mengimpor_lapisan_lain() -> None:
    """`src/kamus/` adalah lapisan di bawah `src/penyimpanan/`.

    Kamus yang mengimpor lapisan lain adalah tempat ketergantungan melingkar
    bersembunyi: setiap lapisan mengimpor kamus, sehingga satu impor balik dari
    kamus menjangkau seluruhnya.
    """
    pelanggaran: list[str] = []
    for berkas in sorted((AKAR / "src" / "kamus").rglob("*.py")):
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if isinstance(simpul, ast.ImportFrom) and (simpul.module or "").startswith("src."):
                pelanggaran.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno}: {simpul.module}")
            if isinstance(simpul, ast.Import):
                for alias in simpul.names:
                    if alias.name.startswith("src."):
                        pelanggaran.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno}")
    assert not pelanggaran, "kamus mengimpor lapisan lain: " + "; ".join(pelanggaran)


# ------------------------------------------------------------- nilai D-14


def test_indeks_tujuan_dua_nilai_persis_d14() -> None:
    assert {i.value for i in IndeksTujuan} == {"utama", "metadata"}


def test_peringkat_empat_nilai_persis_d13_bagian_6() -> None:
    assert {p.value for p in Peringkat} == {"T1", "T2", "T3", "T4"}


def test_status_keberlakuan_tiga_nilai_persis_d14_bagian_4_1() -> None:
    """`docs/D14.md` Bagian 4.1: `status_keberlakuan` bernilai
    `berlaku | diubah | dicabut`.

    AG-04 melarang agen mengubah daftar nilai enum. Nilai keempat bernama
    "tidak diketahui" akan mengundang seseorang memperlakukannya sebagai kasus
    yang lebih longgar — bentuk yang sama yang `StatusLisensi` tolak.
    """
    assert {s.value for s in StatusKeberlakuan} == {"berlaku", "diubah", "dicabut"}


def test_peringkat_lemah_dinamai_pada_kamus() -> None:
    """T3 dan T4 bersama-sama adalah satu gagasan D-13 Bagian 6 — "tidak boleh
    menjadi dasar tunggal klaim" — dan gagasan itu dipakai VS-08.

    Dinamai di sini, bukan disusun ulang di validator: himpunan yang disusun
    di tempat pemakainya akan berbeda ketika D-13 menambah peringkat kelima.
    """
    assert PERINGKAT_LEMAH == frozenset({Peringkat.T3, Peringkat.T4})
    assert Peringkat.T1 not in PERINGKAT_LEMAH
    assert Peringkat.T2 not in PERINGKAT_LEMAH


def test_setiap_peringkat_tergolong_lemah_atau_tidak() -> None:
    """Sifat, bukan kasus: peringkat kelima yang ditambahkan D-13 kelak wajib
    diputuskan golongannya, bukan diam-diam masuk golongan kuat."""
    for peringkat in Peringkat:
        assert isinstance(peringkat.lemah, bool)
    assert Peringkat.T3.lemah
    assert not Peringkat.T1.lemah
