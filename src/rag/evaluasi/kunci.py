"""Kunci jawaban *gold set* — T-2 dan T-3 fitur 040, R-02, P-2 A, D-08 Bagian 5.3.

Kunci menunjuk **dokumen dan pasal**, bukan segmen. Tim substansi berpikir
dalam pasal, dan pengenal segmen berubah bila ukuran segmen D-07 Bagian 3.2
kelak berubah — sedangkan *gold set* yang beku tidak boleh ikut berubah.

## Satuan, dan satu aturan cocok

Penanda segmen fitur 038 adalah satuan alaminya — `Pasal 7`, `Pembukaan`,
`Penjelasan Pasal 1` — ditambah akhiran pemotongan: ` ayat (…)`,
`, potongan i dari n`, `, bagian k`. Membuang akhiran itu memberi satuannya
kembali. Kunci cocok dengan segmen bila dokumennya sama dan satuannya **sama
persis**: awalan membuat `Pasal 2` cocok dengan `Pasal 21`.

Pemeriksaan korpus memakai `cocok()` yang sama dengan pengukur, sehingga
kunci yang lolos pemeriksaan adalah kunci yang dapat ditemukan pengukur.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from src.rag.evaluasi.gold_set import GoldSet

_AKHIRAN: Final = (" ayat (", ", ")
"""Awal akhiran pemotongan fitur 038 — `src/ingest/segmentasi.py`."""


def satuan(penanda: str) -> str:
    """Penanda tanpa akhiran pemotongan."""
    potong = [i for i in (penanda.find(a) for a in _AKHIRAN) if i >= 0]
    return penanda[: min(potong)] if potong else penanda


class Kunci(BaseModel):
    """Satu kunci: dokumen dan satuannya."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    dokumen: str = Field(min_length=1)
    bagian: str = Field(min_length=1)

    @field_validator("dokumen", "bagian")
    @classmethod
    def _tanpa_spasi_tepi(cls, nilai: str) -> str:
        if nilai != nilai.strip():
            raise ValueError("berspasi di tepi; pencocokan sama persis tidak akan menemukannya")
        return nilai

    @field_validator("bagian")
    @classmethod
    def _satuan(cls, nilai: str) -> str:
        if satuan(nilai) != nilai:
            raise ValueError(
                "bagian di bawah pasal; kunci menunjuk satuan, bukan ayat atau potongan"
            )
        return nilai


def cocok(kunci: Kunci, id_dokumen: str, penanda: str) -> bool:
    """Satu-satunya aturan cocok — D-08 Bagian 5.3."""
    return kunci.dokumen == id_dokumen and satuan(penanda) == kunci.bagian


@dataclass(frozen=True)
class SegmenDikenal:
    """Pengenal dan penanda satu segmen korpus, tanpa teksnya."""

    id_segmen: str
    id_dokumen: str
    penanda: str


class SebabKunci(Enum):
    DI_LUAR_KORPUS = "dokumen di luar korpus"
    TANPA_SEGMEN = "bagian tanpa segmen"


@dataclass(frozen=True)
class TemuanKunci:
    """Satu kunci yang tidak dapat ditemukan, dengan pengenalnya saja (R-07)."""

    id_pertanyaan: str
    urutan: int
    kunci: Kunci
    sebab: SebabKunci

    def __str__(self) -> str:
        return (
            f"pertanyaan {self.id_pertanyaan} kunci {self.urutan}: {self.sebab.value} "
            f"({self.kunci.dokumen}, {self.kunci.bagian})"
        )


def periksa_korpus(gold: GoldSet, segmen: Iterable[SegmenDikenal]) -> tuple[TemuanKunci, ...]:
    """Kunci yang tidak cocok dengan satu segmen pun — R-02.

    `segmen` adalah seluruh segmen kedua indeks, layak atau tidak: kelayakan
    diukur pengukur, bukan syarat bentuk.
    """
    per_dokumen: dict[str, list[str]] = defaultdict(list)
    for s in segmen:
        per_dokumen[s.id_dokumen].append(s.penanda)
    temuan: list[TemuanKunci] = []
    for p in gold.pertanyaan:
        for urutan, k in enumerate(p.kunci, start=1):
            if k.dokumen not in per_dokumen:
                temuan.append(TemuanKunci(p.id, urutan, k, SebabKunci.DI_LUAR_KORPUS))
            elif not any(cocok(k, k.dokumen, pn) for pn in per_dokumen[k.dokumen]):
                temuan.append(TemuanKunci(p.id, urutan, k, SebabKunci.TANPA_SEGMEN))
    return tuple(temuan)
