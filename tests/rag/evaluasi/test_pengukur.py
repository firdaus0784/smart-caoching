"""Uji pengukur satu putaran — T-5 fitur 040, R-05, K-5, P-4 A.

Sumber per kueri di bawah adalah ganda uji: ia mengembalikan peringkat yang
ditetapkan bagi setiap teks pertanyaan, sehingga setiap angka dapat dihitung
tangan. Pengukur atas sumber leksikal sungguhan diuji pada perkakas (T-7).
"""

from __future__ import annotations

import asyncio
from fractions import Fraction
from pathlib import Path

import pytest
from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import VersiPenyemat
from src.rag.evaluasi.gold_set import GoldSet, urai
from src.rag.evaluasi.kunci import SegmenDikenal
from src.rag.evaluasi.metrik import Nilai
from src.rag.evaluasi.pengukur import Putusan, SebabLuput, ukur
from src.rag.pengambilan.kandidat import HasilSumber, Kandidat, SumberKandidat
from src.rag.pengambilan.tetapan import JUMLAH_KANDIDAT_PER_SUMBER
from tests.rag.evaluasi.rekaan import baris, berkas

AKAR = Path(__file__).resolve().parents[3]
D08 = (AKAR / "docs" / "D08.md").read_text(encoding="utf-8")


class SumberPerKueri(SumberKandidat):
    """Peringkat tetap bagi setiap kueri; mencatat kueri dan batasnya."""

    def __init__(
        self,
        peringkat: dict[str, list[str]],
        indeks: IndeksTujuan = IndeksTujuan.UTAMA,
        penyemat: VersiPenyemat | None = None,
    ) -> None:
        self._peringkat = peringkat
        self._indeks = indeks
        self._penyemat = penyemat
        self.kueri: list[tuple[str, int]] = []

    @property
    def nama(self) -> str:
        return "bm25"

    @property
    def indeks_tujuan(self) -> IndeksTujuan:
        return self._indeks

    @property
    def versi_indeks(self) -> str:
        return "utama:sidik-uji"

    async def cari(self, kueri: str, *, batas: int) -> HasilSumber:
        self.kueri.append((kueri, batas))
        ids = self._peringkat.get(kueri, [])[:batas]
        return HasilSumber(
            nama_sumber=self.nama,
            versi_indeks=self.versi_indeks,
            peringkat=tuple(
                Kandidat(id_segmen=i, skor=float(len(ids) - n)) for n, i in enumerate(ids)
            ),
            versi_penyemat=self._penyemat,
        )


def _seg(id_: str, dokumen: str, penanda: str) -> SegmenDikenal:
    return SegmenDikenal(id_segmen=id_, id_dokumen=dokumen, penanda=penanda)


SEGMEN = {
    s.id_segmen: s
    for s in [
        _seg("u1", "DOK-1", "Pasal 1"),
        _seg("u2", "DOK-1", "Pasal 2"),
        _seg("u3", "DOK-2", "Pasal 1"),
        *(_seg(f"isi{i}", "DOK-ISI", f"Pasal {i}") for i in range(1, 12)),
        _seg("m1", "DOK-NC", "Pasal 1"),
    ]
}
LAYAK = frozenset({"u1", "u2", *(f"isi{i}" for i in range(1, 12))})
"""u3 ada di korpus tetapi tidak layak (mis. regulasi dicabut)."""
METADATA = frozenset({"m1"})
ISI = [f"isi{i}" for i in range(1, 12)]


def _gold() -> GoldSet:
    return urai(
        berkas(
            baris("q1", kunci=[("DOK-1", "Pasal 1")], pertanyaan="REKAAN satu"),
            baris("q2", kunci=[("DOK-1", "Pasal 2")], pertanyaan="REKAAN dua"),
            baris("q3", kunci=[("DOK-2", "Pasal 1")], pertanyaan="REKAAN tiga"),
            baris("q4", kunci=[("DOK-3", "Pasal 1")], pertanyaan="REKAAN empat"),
            baris("c1", "C", pertanyaan="REKAAN lima"),
            baris("d1", "D", pertanyaan="REKAAN enam"),
        )
    )


def _ukur(sumber: SumberKandidat, gold: GoldSet | None = None):  # type: ignore[no-untyped-def]
    return asyncio.run(
        ukur(gold or _gold(), sumber, segmen=SEGMEN, layak=LAYAK, id_metadata=METADATA)
    )


def _sumber() -> SumberPerKueri:
    return SumberPerKueri(
        {
            "REKAAN satu": ["u1", *ISI],
            "REKAAN dua": [*ISI[:9], "u2"],
            "REKAAN tiga": ISI,
            "REKAAN empat": ISI,
        }
    )


def test_tiga_sebab_luput_dan_pertanyaan_tetap_di_penyebut() -> None:
    """K-5; K-4 (M-9): q4 yang kuncinya hilang dari korpus tetap dihitung."""
    hasil = _ukur(_sumber())
    luput = {h.nilai.id: [k.sebab for k in h.luput] for h in hasil.pertanyaan}
    assert luput == {
        "q1": [],
        "q2": [SebabLuput.DI_LUAR_PERINGKAT],
        "q3": [SebabLuput.DI_LUAR_BAHAN],
        "q4": [SebabLuput.DI_LUAR_KORPUS],
        "c1": [],
        "d1": [],
    }
    assert hasil.ringkasan.utama.recall_8 == Nilai(Fraction(1), 4)
    assert [h.nilai.id for h in hasil.gagal] == ["q2", "q3", "q4"]
    assert hasil.pertanyaan[1].nilai.peringkat_pertama == 10


def test_seluruh_pertanyaan_dicari_termasuk_c_dan_d_dengan_kedalaman_d07() -> None:
    """Kebocoran dapat muncul pada kueri apa pun."""
    sumber = _sumber()
    _ukur(sumber)
    assert sorted(k for k, _ in sumber.kueri) == sorted(p.pertanyaan for p in _gold().pertanyaan)
    assert {b for _, b in sumber.kueri} == {JUMLAH_KANDIDAT_PER_SUMBER}


def test_kebocoran_nol_dan_putusan_diukur_tanpa_menyatakan_u3_lulus() -> None:
    """P-4 A: putaran satu sumber tidak menerapkan ambang U3."""
    hasil = _ukur(_sumber())
    assert hasil.kebocoran == ()
    assert hasil.putusan is Putusan.DIUKUR
    assert "hibrida" in hasil.putusan.value
    assert "tidak diterapkan" in hasil.putusan.value
    assert "lulus" not in hasil.putusan.value
    assert hasil.konfigurasi.sumber == "bm25"
    assert hasil.konfigurasi.indeks is IndeksTujuan.UTAMA
    assert hasil.konfigurasi.kedalaman == JUMLAH_KANDIDAT_PER_SUMBER
    assert hasil.konfigurasi.versi_penyemat is None
    assert hasil.versi_indeks == "utama:sidik-uji"


def test_ambang_kebocoran_d08_nol() -> None:
    """R-05: baris D-08 Bagian 6 yang menjadi dasar putusan gagal kepatuhan."""
    tabel = D08.split("## 6. Pengujian Pengambilan (U3)", 1)[1].split("**Aturan pelaksanaan", 1)[0]
    (kebocoran,) = [b for b in tabel.splitlines() if b.startswith("| Kebocoran indeks |")]
    assert kebocoran.rstrip().endswith("| **0** |")


def test_segmen_indeks_metadata_di_antara_kandidat_adalah_kebocoran() -> None:
    """R-05, KL-01 (M-6): dihitung per segmen berbeda, dari kueri mana pun —
    termasuk kueri jenis D."""
    sumber = SumberPerKueri({"REKAAN satu": ["u1", "m1"], "REKAAN enam": ["m1"]})
    hasil = _ukur(sumber)
    assert hasil.kebocoran == ("m1",)
    assert hasil.putusan is Putusan.GAGAL_KEPATUHAN
    bocor = {h.nilai.id: h.bocor for h in hasil.pertanyaan}
    assert bocor["q1"] == ("m1",)
    assert bocor["d1"] == ("m1",)


def test_sumber_atas_indeks_metadata_bocor_seluruhnya() -> None:
    sumber = SumberPerKueri({"REKAAN satu": ["m1"]}, indeks=IndeksTujuan.METADATA)
    hasil = _ukur(sumber)
    assert hasil.putusan is Putusan.GAGAL_KEPATUHAN
    assert hasil.konfigurasi.indeks is IndeksTujuan.METADATA


def test_kandidat_di_luar_korpus_yang_dimuat_ditolak() -> None:
    with pytest.raises(ValueError, match="asing"):
        _ukur(SumberPerKueri({"REKAAN satu": ["tak-dikenal"]}))


def test_versi_penyemat_dinyatakan_bila_sumber_memakainya() -> None:
    """C-09: konfigurasi menyebut model yang benar-benar melayani pencarian."""
    penyemat = VersiPenyemat(nama_model="penyemat-uji", versi_model="1.0")
    hasil = _ukur(SumberPerKueri({}, penyemat=penyemat))
    assert hasil.konfigurasi.versi_penyemat == "penyemat-uji/1.0"
