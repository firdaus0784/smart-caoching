"""Metrik pengujian pengambilan U3 — T-4 fitur 040, R-04, P-5 A, AP-03, AP-06.

Definisi dan populasinya milik D-08 Bagian 6 beserta aturan pelaksanaannya;
modul ini mewujudkannya. Uji membaca k dari tabel D-08, bukan dari berkas ini.

## Setiap kunci, bukan salah satu

Pertanyaan terhitung pada Recall@8 bila **setiap** kuncinya memiliki segmen
cocok pada 8 teratas. Kunci disusun tim sebagai segmen pendukung yang benar;
pertanyaan yang separuh dasarnya terambil adalah pertanyaan yang jawabannya
dapat separuh benar. "Salah satu kunci" menaikkan angka tanpa menaikkan mutu.

## Pecahan tepat, persen dipangkas

Angka disimpan sebagai pecahan tepat beserta penyebutnya, sehingga ambang
kelak dibandingkan tanpa galat pembulatan. Persen ditulis satu desimal
**dipangkas ke bawah** (AP-06): 89,96% yang dibulatkan menjadi 90,0% akan
terbaca memenuhi ambang yang tidak dipenuhinya.

## Tanpa ambang

Ambang D-08 Bagian 6 berlaku bagi pengambilan hibrida. Modul ini tidak
memuatnya; putaran satu sumber tidak menyatakan U3 lulus (P-4 A).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Final

from src.nlp.anotasi.skema import KategoriMasalah
from src.rag.evaluasi.gold_set import TANPA_KATEGORI, JenisPertanyaan, PertanyaanEmas
from src.rag.evaluasi.kunci import SegmenDikenal, cocok

K_RECALL: Final = 8
"""D-08 Bagian 6, "Recall@8"."""

K_PRESISI: Final = 5
"""D-08 Bagian 6, "Precision@5"."""

JENIS_BERKUNCI: Final = (
    JenisPertanyaan.A,
    JenisPertanyaan.B,
    JenisPertanyaan.E,
    JenisPertanyaan.F,
)


@dataclass(frozen=True)
class Nilai:
    """Satu angka: pembilang tepat dan banyaknya pertanyaan."""

    pembilang: Fraction
    penyebut: int

    @property
    def terhitung(self) -> bool:
        return self.penyebut > 0

    @property
    def pecahan(self) -> Fraction | None:
        return self.pembilang / self.penyebut if self.terhitung else None

    def persen(self) -> str:
        """Satu desimal, dipangkas ke bawah — AP-06."""
        if self.pecahan is None:
            return "tidak terhitung (penyebut nol)"
        persepuluh = math.floor(self.pecahan * 1000)
        return f"{persepuluh // 10},{persepuluh % 10}%"


@dataclass(frozen=True)
class NilaiPertanyaan:
    """Yang diukur pada satu pertanyaan — pengenal, bukan teks (R-07)."""

    id: str
    jenis: JenisPertanyaan
    kategori: KategoriMasalah | None
    bernomor_regulasi: bool
    kunci_dalam_k: tuple[bool, ...]
    """Per kunci: adakah segmen cocok pada `K_RECALL` teratas."""
    peringkat_pertama: int | None
    """Peringkat 1-berbasis segmen cocok pertama; `None` di luar daftar."""
    cocok_5: int

    @property
    def kena(self) -> bool:
        return all(self.kunci_dalam_k)


def nilai_pertanyaan(p: PertanyaanEmas, peringkat: Sequence[SegmenDikenal]) -> NilaiPertanyaan:
    """Satu pertanyaan atas satu daftar kandidat berperingkat."""

    def cocok_kunci(s: SegmenDikenal) -> bool:
        return any(cocok(k, s.id_dokumen, s.penanda) for k in p.kunci)

    pertama = next((i for i, s in enumerate(peringkat, start=1) if cocok_kunci(s)), None)
    teratas = peringkat[:K_RECALL]
    return NilaiPertanyaan(
        id=p.id,
        jenis=p.jenis,
        kategori=p.kategori,
        bernomor_regulasi=p.bernomor_regulasi,
        kunci_dalam_k=tuple(
            any(cocok(k, s.id_dokumen, s.penanda) for s in teratas) for k in p.kunci
        ),
        peringkat_pertama=pertama,
        cocok_5=sum(cocok_kunci(s) for s in peringkat[:K_PRESISI]),
    )


@dataclass(frozen=True)
class TigaMetrik:
    recall_8: Nilai
    mrr: Nilai
    presisi_5: Nilai


def _tiga(nilai: Sequence[NilaiPertanyaan]) -> TigaMetrik:
    n = len(nilai)
    return TigaMetrik(
        recall_8=Nilai(Fraction(sum(v.kena for v in nilai)), n),
        mrr=Nilai(
            sum(
                (Fraction(1, v.peringkat_pertama) for v in nilai if v.peringkat_pertama),
                Fraction(0),
            ),
            n,
        ),
        presisi_5=Nilai(sum((Fraction(v.cocok_5, K_PRESISI) for v in nilai), Fraction(0)), n),
    )


@dataclass(frozen=True)
class Ringkasan:
    """Populasi D-08 Bagian 6 dan metrik per kelas (AP-03)."""

    utama: TigaMetrik
    """Jenis A."""
    recall_bernomor: Nilai
    """Jenis A bertanda `bernomor_regulasi`."""
    per_jenis: Mapping[JenisPertanyaan, TigaMetrik]
    per_kategori: Mapping[str, TigaMetrik]
    """Kategori pada jenis A."""


def _kategori(v: NilaiPertanyaan) -> str:
    return TANPA_KATEGORI if v.kategori is None else v.kategori.value


def ringkas(nilai: Iterable[NilaiPertanyaan]) -> Ringkasan:
    semua = list(nilai)
    a = [v for v in semua if v.jenis is JenisPertanyaan.A]
    bernomor = [v for v in a if v.bernomor_regulasi]
    return Ringkasan(
        utama=_tiga(a),
        recall_bernomor=_tiga(bernomor).recall_8,
        per_jenis={j: _tiga([v for v in semua if v.jenis is j]) for j in JENIS_BERKUNCI},
        per_kategori={
            k: _tiga([v for v in a if _kategori(v) == k]) for k in sorted({_kategori(v) for v in a})
        },
    )
