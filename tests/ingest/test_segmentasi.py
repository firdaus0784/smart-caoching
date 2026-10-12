"""Pemotongan dokumen korpus — T-4 fitur 038, R-01, R-02, R-06; K-2; D-07 Bagian 3.2.

Angka milik D-07: uji membacanya dari tabel D-07, bukan menyalinnya. Teks
contoh berpola peraturan dibuat-buat.
"""

import re
from itertools import pairwise
from pathlib import Path

import pytest
from src.ingest.segmentasi import (
    BATAS_KATA,
    SASARAN_KATA,
    TUMPANG_TINDIH_KATA,
    Potongan,
    potong,
)

AKAR = Path(__file__).resolve().parents[2]


def _kata(n: int, awal: str = "kata") -> str:
    return " ".join(f"{awal}{i}" for i in range(n))


def _jumlah(p: Potongan) -> int:
    return len(p.teks.split())


def test_tetapan_mengikuti_d07() -> None:
    """C-16: ukuran segmen milik D-07, tidak disetel di kode."""
    d07 = (AKAR / "docs" / "D07.md").read_text(encoding="utf-8")
    (ukuran,) = [b for b in d07.splitlines() if b.startswith("| Ukuran sasaran |")]
    (tindih,) = [b for b in d07.splitlines() if b.startswith("| Tumpang tindih |")]
    rentang = re.compile(r"(\d+)\u2013(\d+) kata")
    bawah, atas = map(int, rentang.findall(ukuran)[0])
    tindih_bawah, tindih_atas = map(int, rentang.findall(tindih)[0])
    assert (bawah, atas) == (SASARAN_KATA, BATAS_KATA)
    assert tindih_bawah <= TUMPANG_TINDIH_KATA <= tindih_atas


def test_pasal_pendek_berdiri_sendiri() -> None:
    """M-7: pasal yang lebih pendek dari sasaran tidak digabung (D-07)."""
    hasil = potong("Pasal 1\nKalimat pendek.\nPasal 2\nKalimat lain.\nPasal 2A\nSisipan.")
    assert [p.penanda for p in hasil] == ["Pasal 1", "Pasal 2", "Pasal 2A"]
    assert hasil[0].teks == "Pasal 1\nKalimat pendek."


def test_pembukaan_dan_konteks_bab_ikut_pasal_sesudahnya() -> None:
    teks = (
        "PERATURAN CONTOH NOMOR 1 TAHUN 2026\nMenimbang: bahwa perlu rencana kerja.\n"
        "BAB I\nKETENTUAN UMUM\nPasal 1\nIsi pasal satu.\n"
        "BAB II\nTUGAS\nBagian Kesatu\nUmum\nPasal 2\nIsi pasal dua."
    )
    hasil = potong(teks)
    assert [p.penanda for p in hasil] == ["Pembukaan", "Pasal 1", "Pasal 2"]
    assert hasil[0].teks.startswith("PERATURAN CONTOH")
    assert hasil[1].teks.startswith("BAB I\nKETENTUAN UMUM\nPasal 1")
    assert hasil[2].teks.startswith("BAB II\nTUGAS\nBagian Kesatu\nUmum\nPasal 2")
    assert "BAB II" not in hasil[1].teks


def test_rujukan_pasal_di_dalam_kalimat_bukan_batas() -> None:
    hasil = potong("Pasal 4\nSebagaimana dimaksud dalam Pasal 2, kepala sekolah menyusun.")
    assert [p.penanda for p in hasil] == ["Pasal 4"]


def test_pasal_panjang_dipecah_di_batas_ayat_tanpa_tumpang_tindih() -> None:
    ayat = [f"({i}) {_kata(200, f'a{i}x')}" for i in range(1, 5)]
    hasil = potong("Pasal 3\n" + "\n".join(ayat))
    assert [p.penanda for p in hasil] == [
        "Pasal 3 ayat (1)\u2013(2)",
        "Pasal 3 ayat (3)\u2013(4)",
    ]
    gabungan = " ".join(p.teks for p in hasil).split()
    assert len(gabungan) == len(set(gabungan)), "batas alami tidak diberi tumpang tindih"
    assert all(_jumlah(p) <= BATAS_KATA for p in hasil)


def test_butir_di_bawah_ayat_ikut_ayatnya() -> None:
    """Baris lanjutan sebuah ayat — butir `a.`, `b.` — tidak dipisah dari ayatnya."""
    teks = (
        f"Pasal 6\n(1) {_kata(200, 'satu')}\na. {_kata(100, 'butira')}\n"
        f"b. {_kata(100, 'butirb')}\n(2) {_kata(300, 'dua')}"
    )
    hasil = potong(teks)
    assert [p.penanda for p in hasil] == ["Pasal 6 ayat (1)", "Pasal 6 ayat (2)"]
    assert "butira99" in hasil[0].teks and "butirb99" in hasil[0].teks
    assert hasil[1].teks.startswith("(2) dua0")


def test_teks_tanpa_batas_alami_dipecah_bertumpang_tindih() -> None:
    """M-8: jendela sama besar, masing-masing paling banyak 500 kata, bertumpang
    tindih sedikitnya 60 kata, berpenanda sendiri."""
    hasil = potong("Pasal 5\n" + _kata(1000))
    assert [p.penanda for p in hasil] == [
        "Pasal 5, potongan 1 dari 3",
        "Pasal 5, potongan 2 dari 3",
        "Pasal 5, potongan 3 dari 3",
    ]
    jendela = [p.teks.split() for p in hasil]
    assert all(len(j) <= BATAS_KATA for j in jendela)
    for kiri, kanan in pairwise(jendela):
        assert kiri[-TUMPANG_TINDIH_KATA:] == kanan[:TUMPANG_TINDIH_KATA]
    assert jendela[0][0] == "Pasal" and jendela[-1][-1] == "kata999"


def test_dokumen_tanpa_pasal_dikumpulkan_per_paragraf() -> None:
    paragraf = [_kata(120, f"p{i}x") for i in range(10)]
    hasil = potong("\n".join(paragraf))
    assert [p.penanda for p in hasil] == ["Bagian 1", "Bagian 2", "Bagian 3"]
    assert [_jumlah(p) for p in hasil] == [480, 480, 240]


def test_paragraf_tunggal_panjang_tanpa_pasal() -> None:
    hasil = potong(_kata(700))
    assert [p.penanda for p in hasil] == [
        "Bagian 1, potongan 1 dari 2",
        "Bagian 1, potongan 2 dari 2",
    ]


def test_penjelasan_dan_lampiran_berawalan() -> None:
    teks = (
        "Pasal 1\nIsi.\nPENJELASAN\nI. UMUM\nUraian umum.\nPasal 1\nCukup jelas.\n"
        "LAMPIRAN\nTabel rencana kerja."
    )
    assert [p.penanda for p in potong(teks)] == [
        "Pasal 1",
        "Penjelasan",
        "Penjelasan Pasal 1",
        "Lampiran",
    ]


@pytest.mark.parametrize(
    "teks",
    [
        "Pasal 1\n" + _kata(1234),
        "\n".join(_kata(n) for n in (10, 600, 30, 499, 501)),
        "Pembukaan.\n" + _kata(900) + "\nPasal 1\n(1) " + _kata(450) + "\n(2) " + _kata(450),
        "BAB I\nUMUM\nPasal 1\nIsi satu.\nPasal 2\nIsi dua.\nBAB II\nKETENTUAN PENUTUP",
        "Pasal 1\nIsi.\nPENJELASAN\n" + _kata(700) + "\nLAMPIRAN\n" + _kata(30, "lampiran"),
    ],
)
def test_tidak_satu_segmen_melampaui_batas_dan_tidak_ada_teks_hilang(teks: str) -> None:
    hasil = potong(teks)
    assert hasil
    assert all(_jumlah(p) <= BATAS_KATA for p in hasil)
    assert all(p.penanda.strip() and p.teks.strip() for p in hasil)
    assert set(teks.split()) == {k for p in hasil for k in p.teks.split()}


def test_deterministik_dan_teks_hampa() -> None:
    teks = "Pasal 1\n" + _kata(800)
    assert potong(teks) == potong(teks)
    assert potong("") == [] and potong("  \n \n") == []
