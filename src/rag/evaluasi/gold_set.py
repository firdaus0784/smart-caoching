"""Bentuk berkas *gold set* dan sidiknya — T-2 fitur 040, R-02, R-03, R-07.

Bentuknya milik D-08 Bagian 5.3, komposisinya milik D-08 Bagian 5.1. Modul ini
mewujudkan keduanya; uji membacanya dari dokumen, bukan dari berkas ini.

## Pesan galat tanpa teks

Pertanyaan *gold set* adalah kata-kata asli kepala sekolah (D-08 Bagian 5.2),
dan pesan galat dibaca di terminal, disalin ke percakapan, ditempel ke
catatan. Karena itu galat dilaporkan sebagai nomor baris, bidang, dan sebab —
`input` pydantic tidak pernah dibawa, baris yang bukan JSON tidak dikutip.

## Sidik isi, bukan sidik berkas

Urutan baris, urutan bidang, urutan kunci, dan spasi di luar nilai tidak
mengubah isi; menyunting berkas di penyunting lain tidak boleh membuat *gold
set* yang beku tampak berubah. Satu huruf pertanyaan, satu kunci, satu jenis,
atau satu tanda mengubahnya — itulah yang pembekuan D-08 Bagian 5.2 larang.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, StrictBool, ValidationError, model_validator

from src.nlp.anotasi.skema import KategoriMasalah
from src.rag.evaluasi.kunci import Kunci


class JenisPertanyaan(Enum):
    """Enam jenis pertanyaan — D-08 Bagian 5.1."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


KOMPOSISI_D08: Final[Mapping[JenisPertanyaan, int]] = MappingProxyType(
    {
        JenisPertanyaan.A: 100,
        JenisPertanyaan.B: 30,
        JenisPertanyaan.C: 30,
        JenisPertanyaan.D: 15,
        JenisPertanyaan.E: 15,
        JenisPertanyaan.F: 10,
    }
)
"""Komposisi D-08 Bagian 5.1. Pembekuan menuntutnya persis (P-3 A)."""

_KUNCI_MINIMUM: Final[Mapping[JenisPertanyaan, int]] = MappingProxyType(
    {
        JenisPertanyaan.A: 1,
        JenisPertanyaan.B: 1,
        JenisPertanyaan.E: 1,
        JenisPertanyaan.F: 2,
    }
)
"""C dan D tidak berkunci; jawaban benarnya penolakan."""

TANPA_KATEGORI: Final = "tanpa-kategori"


class PertanyaanEmas(BaseModel):
    """Satu baris *gold set* — tabel D-08 Bagian 5.3."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9._-]{1,64}$", strict=True)
    pertanyaan: str = Field(min_length=1, strict=True)
    jenis: JenisPertanyaan
    kategori: KategoriMasalah | None = None
    kunci: tuple[Kunci, ...] = ()
    bernomor_regulasi: StrictBool

    @model_validator(mode="after")
    def _sesuai_jenis(self) -> PertanyaanEmas:
        if not self.pertanyaan.strip():
            raise ValueError("pertanyaan hampa")
        if self.kategori is None and self.jenis is not JenisPertanyaan.D:
            raise ValueError(f"kategori wajib bagi jenis {self.jenis.value}")
        minimum = _KUNCI_MINIMUM.get(self.jenis)
        if minimum is None and self.kunci:
            raise ValueError(f"jenis {self.jenis.value} tidak berkunci")
        if minimum is not None and len(self.kunci) < minimum:
            raise ValueError(f"jenis {self.jenis.value} menuntut sedikitnya {minimum} kunci")
        if len(set(self.kunci)) != len(self.kunci):
            raise ValueError("kunci kembar")
        return self


class GoldSet(BaseModel):
    """Seluruh pertanyaan satu berkas, pengenalnya unik."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pertanyaan: tuple[PertanyaanEmas, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _id_unik(self) -> GoldSet:
        hitung = Counter(p.id for p in self.pertanyaan)
        kembar = sorted(i for i, n in hitung.items() if n > 1)
        if kembar:
            raise ValueError(f"id kembar: {', '.join(kembar)}")
        return self

    @property
    def sidik(self) -> str:
        """SHA-256 atas isi kanonik — D-08 Bagian 5.3."""
        isi = [
            {
                "id": p.id,
                "pertanyaan": p.pertanyaan,
                "jenis": p.jenis.value,
                "kategori": None if p.kategori is None else p.kategori.value,
                "kunci": sorted(
                    ({"dokumen": k.dokumen, "bagian": k.bagian} for k in p.kunci),
                    key=lambda k: (k["dokumen"], k["bagian"]),
                ),
                "bernomor_regulasi": p.bernomor_regulasi,
            }
            for p in sorted(self.pertanyaan, key=lambda p: p.id)
        ]
        padat = json.dumps(isi, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(padat.encode("utf-8")).hexdigest()

    def komposisi(self) -> dict[JenisPertanyaan, int]:
        """Jumlah per jenis, keenamnya tercantum."""
        hitung = Counter(p.jenis for p in self.pertanyaan)
        return {j: hitung[j] for j in JenisPertanyaan}

    def penyimpangan(self) -> dict[JenisPertanyaan, tuple[int, int]]:
        """Jenis yang jumlahnya berbeda dari D-08 → (ada, D-08)."""
        ada = self.komposisi()
        return {j: (ada[j], n) for j, n in KOMPOSISI_D08.items() if ada[j] != n}

    def komposisi_kategori(self) -> dict[str, int]:
        hitung = Counter(
            TANPA_KATEGORI if p.kategori is None else p.kategori.value for p in self.pertanyaan
        )
        return dict(sorted(hitung.items()))

    def jumlah_bernomor_regulasi(self) -> int:
        return sum(p.bernomor_regulasi for p in self.pertanyaan)


class GalatBerkas(Exception):
    """Berkas tidak sah. Pesannya nomor baris, bidang, dan sebab — tanpa teks."""

    def __init__(self, masalah: tuple[str, ...]) -> None:
        super().__init__("\n".join(masalah))
        self.masalah = masalah


def _tanpa_kembar(pasangan: list[tuple[str, object]]) -> dict[str, object]:
    nama = [n for n, _ in pasangan]
    if len(nama) != len(set(nama)):
        raise _KunciJsonKembar
    return dict(pasangan)


class _KunciJsonKembar(Exception):
    pass


def _sebab(galat: ValidationError) -> list[str]:
    """`loc` dan `msg` saja; `input` tidak pernah dibawa (R-07)."""
    hasil = []
    for g in galat.errors(include_input=False, include_url=False, include_context=False):
        tempat = ".".join(str(t) for t in g["loc"])
        hasil.append(f"{tempat}: {g['msg']}" if tempat else str(g["msg"]))
    return hasil


def urai(teks: str) -> GoldSet:
    """Teks JSON Lines menjadi `GoldSet`; seluruh masalah dikumpulkan dulu."""
    masalah: list[str] = []
    sah: list[tuple[int, PertanyaanEmas]] = []
    for nomor, mentah in enumerate(teks.splitlines(), start=1):
        if not mentah.strip():
            continue
        try:
            obj = json.loads(mentah, object_pairs_hook=_tanpa_kembar)
        except _KunciJsonKembar:
            masalah.append(f"baris {nomor}: nama bidang kembar")
            continue
        except json.JSONDecodeError as g:
            masalah.append(f"baris {nomor}: bukan JSON ({g.msg}, kolom {g.colno})")
            continue
        if not isinstance(obj, dict):
            masalah.append(f"baris {nomor}: bukan objek JSON")
            continue
        try:
            sah.append((nomor, PertanyaanEmas.model_validate(obj)))
        except ValidationError as g:
            masalah.extend(f"baris {nomor}: {s}" for s in _sebab(g))
    pertama: dict[str, int] = {}
    for nomor, p in sah:
        if p.id in pertama:
            masalah.append(f"baris {nomor}: id {p.id} juga dipakai baris {pertama[p.id]}")
        else:
            pertama[p.id] = nomor
    if not sah and not masalah:
        masalah.append("berkas tidak memuat pertanyaan")
    if masalah:
        raise GalatBerkas(tuple(masalah))
    return GoldSet(pertanyaan=tuple(p for _, p in sah))
