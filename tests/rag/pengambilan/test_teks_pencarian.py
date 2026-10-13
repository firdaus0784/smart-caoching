"""Aturan teks pencarian — T-2 fitur 041, R-02, R-04, K-1, K-2, TK-88.

Aturannya milik D-07 Bagian 3.3; uji membaca penanda versinya dari sana.
"""

from __future__ import annotations

from pathlib import Path

from src.rag.pengambilan.teks_pencarian import ATURAN_PENCARIAN, teks_pencarian

AKAR = Path(__file__).resolve().parents[3]
D07 = (AKAR / "docs" / "D07.md").read_text(encoding="utf-8")


def _baris_d07(awal: str) -> str:
    bagian = D07.split("### 3.3 Sematan dan Indeks Leksikal", 1)[1].split("\n## ", 1)[0]
    (baris,) = [b for b in bagian.splitlines() if b.startswith(awal)]
    return baris


def test_penanda_aturan_dibaca_dari_d07() -> None:
    """R-04: versi memuat penanda yang D-07 tetapkan."""
    assert f"`{ATURAN_PENCARIAN}`" in _baris_d07("| Versi indeks |")


def test_d07_menetapkan_judul_lalu_teks_segmen_tanpa_mengubahnya() -> None:
    baris = _baris_d07("| Teks pencarian |")
    assert "judul dokumen" in baris and "teks segmen" in baris
    assert "tidak berubah" in baris


def test_judul_mendahului_teks_segmen_dipisah_baris_baru() -> None:
    assert teks_pencarian("Peraturan Contoh Nomor 6 Tahun 2021", "Isi pasal.") == (
        "Peraturan Contoh Nomor 6 Tahun 2021\nIsi pasal."
    )
