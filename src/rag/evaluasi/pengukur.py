"""Satu putaran pengujian pengambilan — T-5 fitur 040, R-05, R-06, P-4 A.

Fungsi murni atas satu `SumberKandidat`: pemuat dan perakitan muatan tinggal di
`perkakas/evaluasi.py`, sehingga yang diukur di sana adalah sumber yang sama
dengan yang dipakai jalur penjawab.

## Setiap pertanyaan dicari, termasuk C dan D

Jenis C dan D tidak berkunci, tetapi kebocoran indeks (KL-01) dapat muncul
pada kueri apa pun. Kebocoran adalah segmen `indeks_metadata` di antara
kandidat; ambangnya nol pada setiap konfigurasi (D-08 Bagian 6).

## Tiga sebab luput

Kunci yang tidak terambil disebut sebabnya, karena ketiganya menuntut
perbaikan di tempat berbeda: **di luar korpus** — korpus berubah sesudah
pembekuan; **di luar bahan** — segmennya ada tetapi tidak layak atau berada
di indeks metadata; **di luar peringkat** — pengambilan yang perlu
diperbaiki (C-16 kalimat kedua). Pertanyaan tidak pernah keluar dari
penyebut karena sebab apa pun.

## Dua putusan

Ambang U3 berlaku bagi pengambilan hibrida (ADR-03). Putaran satu sumber
hanya dapat *diukur* atau *gagal kepatuhan*; putusan hibrida menyusul bersama
ADR-12.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from src.kamus.segmen import IndeksTujuan
from src.rag.evaluasi.gold_set import GoldSet
from src.rag.evaluasi.kunci import Kunci, SegmenDikenal, cocok
from src.rag.evaluasi.metrik import NilaiPertanyaan, Ringkasan, nilai_pertanyaan, ringkas
from src.rag.pengambilan.kandidat import SumberKandidat
from src.rag.pengambilan.tetapan import JUMLAH_KANDIDAT_PER_SUMBER


class SebabLuput(Enum):
    DI_LUAR_KORPUS = "kunci tidak ditemukan pada korpus"
    DI_LUAR_BAHAN = "kunci ada di korpus tetapi bukan bahan indeks utama"
    DI_LUAR_PERINGKAT = "kunci di luar 8 teratas"


class Putusan(Enum):
    GAGAL_KEPATUHAN = "gagal kepatuhan KL-01: segmen indeks metadata di antara kandidat"
    DIUKUR = (
        "diukur; ambang U3 D-08 Bagian 6 berlaku bagi pengambilan hibrida "
        "dan tidak diterapkan pada putaran satu sumber"
    )


@dataclass(frozen=True)
class KunciLuput:
    urutan: int
    kunci: Kunci
    sebab: SebabLuput


@dataclass(frozen=True)
class HasilPertanyaan:
    nilai: NilaiPertanyaan
    luput: tuple[KunciLuput, ...]
    bocor: tuple[str, ...]
    """Pengenal segmen indeks metadata di antara kandidat pertanyaan ini."""


@dataclass(frozen=True)
class Konfigurasi:
    """Konfigurasi sumber yang dinyatakan pada laporan dan L1 (P-4 A)."""

    sumber: str
    indeks: IndeksTujuan
    kedalaman: int
    versi_penyemat: str | None


@dataclass(frozen=True)
class HasilPutaran:
    konfigurasi: Konfigurasi
    versi_indeks: str
    pertanyaan: tuple[HasilPertanyaan, ...]
    ringkasan: Ringkasan
    kebocoran: tuple[str, ...]
    """Segmen indeks metadata berbeda yang muncul sebagai kandidat."""

    @property
    def putusan(self) -> Putusan:
        return Putusan.GAGAL_KEPATUHAN if self.kebocoran else Putusan.DIUKUR

    @property
    def gagal(self) -> tuple[HasilPertanyaan, ...]:
        """Pertanyaan berkunci yang sedikitnya satu kuncinya luput (R-06)."""
        return tuple(h for h in self.pertanyaan if h.luput)


async def ukur(
    gold: GoldSet,
    sumber: SumberKandidat,
    *,
    segmen: Mapping[str, SegmenDikenal],
    layak: frozenset[str],
    id_metadata: frozenset[str],
) -> HasilPutaran:
    """Satu putaran atas seluruh pertanyaan.

    `segmen` memuat seluruh segmen kedua indeks; `layak` pengenal bahan indeks
    utama; `id_metadata` pengenal segmen indeks metadata.
    """
    per_dokumen: dict[str, list[SegmenDikenal]] = defaultdict(list)
    for s in segmen.values():
        per_dokumen[s.id_dokumen].append(s)

    def sebab(k: Kunci) -> SebabLuput:
        cocoknya = [s for s in per_dokumen.get(k.dokumen, ()) if cocok(k, s.id_dokumen, s.penanda)]
        if not cocoknya:
            return SebabLuput.DI_LUAR_KORPUS
        if not any(s.id_segmen in layak for s in cocoknya):
            return SebabLuput.DI_LUAR_BAHAN
        return SebabLuput.DI_LUAR_PERINGKAT

    hasil: list[HasilPertanyaan] = []
    penyemat: str | None = None
    for p in gold.pertanyaan:
        temuan = await sumber.cari(p.pertanyaan, batas=JUMLAH_KANDIDAT_PER_SUMBER)
        if temuan.versi_penyemat is not None:
            penyemat = f"{temuan.versi_penyemat.nama_model}/{temuan.versi_penyemat.versi_model}"
        ids = [k.id_segmen for k in temuan.peringkat]
        asing = [i for i in ids if i not in segmen]
        if asing:
            raise ValueError(f"kandidat asing bagi korpus yang dimuat: {', '.join(asing)}")
        nilai = nilai_pertanyaan(p, [segmen[i] for i in ids])
        hasil.append(
            HasilPertanyaan(
                nilai=nilai,
                luput=tuple(
                    KunciLuput(urutan, k, sebab(k))
                    for urutan, (k, ada) in enumerate(
                        zip(p.kunci, nilai.kunci_dalam_k, strict=True), start=1
                    )
                    if not ada
                ),
                bocor=tuple(i for i in ids if i in id_metadata),
            )
        )
    return HasilPutaran(
        konfigurasi=Konfigurasi(
            sumber=sumber.nama,
            indeks=sumber.indeks_tujuan,
            kedalaman=JUMLAH_KANDIDAT_PER_SUMBER,
            versi_penyemat=penyemat,
        ),
        versi_indeks=sumber.versi_indeks,
        pertanyaan=tuple(hasil),
        ringkasan=ringkas(h.nilai for h in hasil),
        kebocoran=tuple(sorted({i for h in hasil for i in h.bocor})),
    )
