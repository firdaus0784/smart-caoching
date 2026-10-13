"""Uji metrik U3 — T-4 fitur 040, R-04, K-4, P-5 A, AP-03, AP-06.

Definisinya milik D-08 Bagian 6 beserta aturan pelaksanaannya. Setiap angka
yang diuji di sini dihitung tangan pada uraian ujinya, sehingga uji tidak
sekadar membandingkan kode dengan dirinya sendiri.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

from src.rag.evaluasi.gold_set import JenisPertanyaan, urai
from src.rag.evaluasi.kunci import SegmenDikenal
from src.rag.evaluasi.metrik import (
    K_PRESISI,
    K_RECALL,
    Nilai,
    nilai_pertanyaan,
    ringkas,
)
from tests.rag.evaluasi.rekaan import baris, berkas

AKAR = Path(__file__).resolve().parents[3]
D08 = (AKAR / "docs" / "D08.md").read_text(encoding="utf-8")


def _tabel_u3() -> list[str]:
    bagian = D08.split("## 6. Pengujian Pengambilan (U3)", 1)[1].split("**Aturan pelaksanaan", 1)[0]
    return [b for b in bagian.splitlines() if b.startswith("| ") and not b.startswith("| Metrik")]


def test_k_dibaca_dari_tabel_d08_bagian_6() -> None:
    """R-04: k bagian dari definisi metrik milik D-08, tidak disalin."""
    nama = [b.split("|")[1].strip() for b in _tabel_u3()]
    assert nama == [
        "Recall@8",
        "MRR",
        "Precision@5",
        "Recall pada pertanyaan bernomor regulasi",
        "Kebocoran indeks",
    ]
    (recall,) = [int(m.group(1)) for n in nama if (m := re.fullmatch(r"Recall@(\d+)", n))]
    (presisi,) = [int(m.group(1)) for n in nama if (m := re.fullmatch(r"Precision@(\d+)", n))]
    assert (recall, presisi) == (K_RECALL, K_PRESISI)
    bernomor = next(b for b in _tabel_u3() if b.startswith("| Recall pada"))
    assert f"Recall@{K_RECALL}" in bernomor


def _segmen(dokumen: str, bagian: str, n: int) -> SegmenDikenal:
    return SegmenDikenal(id_segmen=f"{dokumen}:{bagian}:{n}", id_dokumen=dokumen, penanda=bagian)


def _pengisi(n: int) -> list[SegmenDikenal]:
    return [_segmen("DOK-LAIN", f"Pasal {100 + i}", i) for i in range(n)]


def _peringkat(posisi: dict[int, SegmenDikenal], panjang: int = 20) -> list[SegmenDikenal]:
    """Daftar sepanjang `panjang`; posisi 1-berbasis diisi segmen yang diberikan."""
    isi = _pengisi(panjang)
    for p, s in posisi.items():
        isi[p - 1] = s
    return isi


def _empat_pertanyaan_a() -> list:
    """q1 kunci P1 di peringkat 1; q2 kunci P2 di 2 dan P3 di 9; q3 kunci P4 di
    8 dan 3; q4 kunci P5 tidak terambil.

    Recall@8 = 2/4 (q1, q3); q2 tidak, sebab P3 di luar 8 — **setiap** kunci.
    MRR = (1 + 1/2 + 1/3 + 0) / 4 = 11/24.
    Precision@5 = (1/5 + 1/5 + 1/5 + 0) / 4 = 3/20.
    """
    gold = urai(
        berkas(
            baris("q1", kunci=[("D", "Pasal 1")], bernomor_regulasi=True),
            baris("q2", kunci=[("D", "Pasal 2"), ("D", "Pasal 3")], kategori="K2"),
            baris("q3", kunci=[("D", "Pasal 4")], bernomor_regulasi=True),
            baris("q4", kunci=[("D", "Pasal 5")], kategori="K2"),
        )
    )
    peringkat = {
        "q1": _peringkat({1: _segmen("D", "Pasal 1", 0)}),
        "q2": _peringkat({2: _segmen("D", "Pasal 2", 0), 9: _segmen("D", "Pasal 3", 0)}),
        "q3": _peringkat({3: _segmen("D", "Pasal 4", 0), 8: _segmen("D", "Pasal 4", 1)}),
        "q4": _peringkat({}),
    }
    return [nilai_pertanyaan(p, peringkat[p.id]) for p in gold.pertanyaan]


def test_tiga_metrik_dihitung_tangan() -> None:
    hasil = ringkas(_empat_pertanyaan_a())
    assert hasil.utama.recall_8 == Nilai(Fraction(2), 4)
    assert hasil.utama.mrr == Nilai(Fraction(11, 6), 4)
    assert hasil.utama.mrr.pecahan == Fraction(11, 24)
    assert hasil.utama.presisi_5.pecahan == Fraction(3, 20)


def test_recall_menuntut_setiap_kunci() -> None:
    """K-4 (M-7): q2 hanya separuh dasarnya terambil."""
    q2 = _empat_pertanyaan_a()[1]
    assert q2.kunci_dalam_k == (True, False)
    assert not q2.kena


def test_recall_bernomor_regulasi_hanya_jenis_a_bertanda() -> None:
    """q1 dan q3 bertanda dan keduanya kena: 2/2. Pertanyaan B bertanda tidak
    ikut."""
    nilai = _empat_pertanyaan_a()
    gold_b = urai(berkas(baris("b1", "B", kunci=[("D", "Pasal 9")], bernomor_regulasi=True)))
    nilai.append(nilai_pertanyaan(gold_b.pertanyaan[0], _peringkat({})))
    assert ringkas(nilai).recall_bernomor == Nilai(Fraction(2), 2)


def test_presisi_dibagi_lima_walau_daftar_pendek() -> None:
    """P-5 A: batas bawah; daftar dua segmen yang keduanya cocok = 2/5."""
    (p,) = urai(berkas(baris("q1", kunci=[("D", "Pasal 1")]))).pertanyaan
    pendek = [_segmen("D", "Pasal 1", 0), _segmen("D", "Pasal 1", 1)]
    hasil = nilai_pertanyaan(p, pendek)
    assert hasil.cocok_5 == 2
    assert ringkas([hasil]).utama.presisi_5 == Nilai(Fraction(2, 5), 1)


def test_mrr_nol_di_luar_daftar_dan_peringkat_pertama_dari_kunci_mana_pun() -> None:
    (p,) = urai(berkas(baris("q1", "F", kunci=[("D", "Pasal 1"), ("D", "Pasal 2")]))).pertanyaan
    assert nilai_pertanyaan(p, _peringkat({})).peringkat_pertama is None
    hasil = nilai_pertanyaan(
        p, _peringkat({4: _segmen("D", "Pasal 2", 0), 6: _segmen("D", "Pasal 1", 0)})
    )
    assert hasil.peringkat_pertama == 4
    assert hasil.kena


def test_penyebut_nol_tidak_terhitung_bukan_nol() -> None:
    hasil = ringkas([])
    assert not hasil.utama.recall_8.terhitung
    assert hasil.utama.recall_8.pecahan is None
    assert hasil.utama.recall_8.persen() == "tidak terhitung (penyebut nol)"


def test_persen_dipangkas_ke_bawah_satu_desimal() -> None:
    """AP-06 (M-8): 89,96% ditulis 89,9%, bukan 90,0%."""
    assert Nilai(Fraction(8996), 10000).persen() == "89,9%"
    assert Nilai(Fraction(2), 3).persen() == "66,6%"
    assert Nilai(Fraction(1), 1).persen() == "100,0%"
    assert Nilai(Fraction(0), 7).persen() == "0,0%"
    assert Nilai(Fraction(11, 6), 4).persen() == "45,8%"


def test_per_jenis_berkunci_dan_per_kategori_jenis_a() -> None:
    """AP-03. C dan D tidak berkunci sehingga tidak memiliki metrik
    pengambilan; kategori dihitung atas jenis A."""
    nilai = _empat_pertanyaan_a()
    lain = urai(
        berkas(
            baris("e1", "E", kunci=[("D", "Pasal 7")], kategori="K3"),
            baris("c1", "C", kategori="K3"),
            baris("d1", "D"),
        )
    )
    nilai += [
        nilai_pertanyaan(p, _peringkat({1: _segmen("D", "Pasal 7", 0)})) for p in lain.pertanyaan
    ]
    hasil = ringkas(nilai)
    assert set(hasil.per_jenis) == {
        JenisPertanyaan.A,
        JenisPertanyaan.B,
        JenisPertanyaan.E,
        JenisPertanyaan.F,
    }
    assert hasil.per_jenis[JenisPertanyaan.E].recall_8 == Nilai(Fraction(1), 1)
    assert not hasil.per_jenis[JenisPertanyaan.B].recall_8.terhitung
    assert hasil.per_jenis[JenisPertanyaan.A] == hasil.utama
    assert set(hasil.per_kategori) == {"K1", "K2"}
    assert hasil.per_kategori["K1"].recall_8 == Nilai(Fraction(2), 2)
    assert hasil.per_kategori["K2"].recall_8 == Nilai(Fraction(0), 2)
