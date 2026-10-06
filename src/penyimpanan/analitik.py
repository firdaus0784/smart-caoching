"""Penyimpan analitik penelitian — T-3 fitur 035, R-02, R-06; K-1.

Bentuk tabelnya D-14 Bagian 5.1 dan `perkakas/basis_data/12-analitik.sql`.

## Membaca peristiwa, menambah jejak — tidak lebih

`peristiwa()` membaca baris telemetri apa adanya; `catat_ekspor()` menambah
satu jejak ekspor. Permukaannya tidak memiliki cara menulis peristiwa,
mengubah, maupun menghapus apa pun (C-17); pada PostgreSQL `peran_analitik`
juga tidak memegang haknya (T-2).

## Baris, bukan `Peristiwa`

Yang dikembalikan `BarisPeristiwa` milik penyimpan telemetri. `Peristiwa`
hanya dibentuk gerbang `rekam()` (C-04); CSV fitur 012 menerima baris
berbidang sama lewat `BarisEkspor`.

## Tanpa saringan di sini

Pemisahan peristiwa `pengembangan` dan pemetaan tanggal WIB milik lapisan
analitik (`src/api/analitik.py`). Penyimpan yang menyaring diam-diam membuat
integritas S-18 tidak dapat menghitung yang disaring.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Final, Protocol

from src.penyimpanan.sambungan import SambunganAktif
from src.penyimpanan.telemetri import BarisPeristiwa, TelemetriMemori

PERAN_ANALITIK: Final = "peran_analitik"
"""Peran basis data analitik — `12-analitik.sql`. Tidak menjangkau akun."""

_POLA_PENELITI: Final = re.compile(r"psd_[a-z]{16}")


@dataclass(frozen=True)
class CatatanEkspor:
    """Satu jejak ekspor — D-14 Bagian 5.1."""

    peneliti: str
    diekspor_pada: datetime
    dari: date
    sampai: date
    termasuk_pengembangan: bool
    jumlah_baris: int


class PenyimpanAnalitik(Protocol):
    async def peristiwa(
        self, *, mulai: datetime | None = None, sebelum: datetime | None = None
    ) -> tuple[BarisPeristiwa, ...]:
        """Peristiwa pada `[mulai, sebelum)`, terlama lebih dulu."""
        ...

    async def catat_ekspor(self, catatan: CatatanEkspor) -> int:
        """Nomor jejak yang tercatat."""
        ...


def _sah(catatan: CatatanEkspor) -> None:
    if _POLA_PENELITI.fullmatch(catatan.peneliti) is None:
        raise ValueError("peneliti wajib pseudonim akun (C-05)")
    if catatan.dari > catatan.sampai:
        raise ValueError("rentang ekspor terbalik")
    if catatan.jumlah_baris < 0:
        raise ValueError("jumlah baris tidak boleh negatif")
    offset = catatan.diekspor_pada.utcoffset()
    if offset is None or offset.total_seconds():
        raise ValueError("waktu wajib berzona UTC (KM-01)")


def _dalam(waktu: datetime, mulai: datetime | None, sebelum: datetime | None) -> bool:
    return (mulai is None or waktu >= mulai) and (sebelum is None or waktu < sebelum)


@dataclass
class AnalitikMemori:
    """Pelaksana di memori — membaca penyimpan telemetri memori yang sama."""

    _telemetri: TelemetriMemori
    _ekspor: list[CatatanEkspor] = field(default_factory=list)

    async def peristiwa(
        self, *, mulai: datetime | None = None, sebelum: datetime | None = None
    ) -> tuple[BarisPeristiwa, ...]:
        return tuple(
            sorted(
                (b for b in self._telemetri._baris if _dalam(b.waktu, mulai, sebelum)),
                key=lambda b: b.waktu,
            )
        )

    async def catat_ekspor(self, catatan: CatatanEkspor) -> int:
        _sah(catatan)
        self._ekspor.append(catatan)
        return len(self._ekspor)


class AnalitikPostgres:
    """Sambungannya wajib tersambung sebagai `PERAN_ANALITIK`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def peristiwa(
        self, *, mulai: datetime | None = None, sebelum: datetime | None = None
    ) -> tuple[BarisPeristiwa, ...]:
        baris = await self._sambungan.fetch(
            "SELECT pseudonim, jenis, waktu, properti, versi_aplikasi, versi_model "
            "FROM telemetri.peristiwa "
            "WHERE ($1::timestamptz IS NULL OR waktu >= $1) "
            "AND ($2::timestamptz IS NULL OR waktu < $2) ORDER BY waktu, nomor",
            mulai,
            sebelum,
        )
        return tuple(
            BarisPeristiwa(
                pseudonim=str(b["pseudonim"]),
                jenis=str(b["jenis"]),
                waktu=b["waktu"],  # type: ignore[arg-type]
                properti=_objek(b["properti"]),
                versi_aplikasi=str(b["versi_aplikasi"]),
                versi_model=str(b["versi_model"]),
            )
            for b in baris
        )

    async def catat_ekspor(self, catatan: CatatanEkspor) -> int:
        _sah(catatan)
        b = await self._sambungan.fetchrow(
            "INSERT INTO telemetri.ekspor (peneliti, diekspor_pada, dari, sampai, "
            "termasuk_pengembangan, jumlah_baris) VALUES ($1, $2, $3, $4, $5, $6) "
            "RETURNING nomor",
            catatan.peneliti,
            catatan.diekspor_pada,
            catatan.dari,
            catatan.sampai,
            catatan.termasuk_pengembangan,
            catatan.jumlah_baris,
        )
        return int(b["nomor"])  # type: ignore[index, arg-type]


def _objek(nilai: object) -> dict[str, Any]:
    hasil = json.loads(nilai) if isinstance(nilai, str) else nilai
    if not isinstance(hasil, dict):
        raise TypeError("kolom properti bukan objek")
    return hasil
