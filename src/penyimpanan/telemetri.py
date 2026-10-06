"""Penyimpan peristiwa telemetri — T-3 fitur 034, R-04, R-05, R-10, K-3.

Bentuk tabelnya D-04 Bagian 7.4, D-14 Bagian 5.1, dan
`perkakas/basis_data/10-telemetri.sql`.

## Baris sederhana, bukan `Peristiwa`

`src/penyimpanan/` tidak mengimpor `src/telemetri/` — ia lapisan di bawahnya
(AGENTS.md). `Peristiwa` tetap hanya dibentuk gerbang `rekam()` fitur 012, dan
`src/api/rekaman.py` yang menerjemahkannya menjadi baris di sini. Yang diperiksa
di sini hanya bentuk yang tabelnya juga tolak — pemilik berpola pseudonim, dua
puluh kode, waktu UTC, versi terisi — agar kedua pelaksana menolak sama.

## Tambah-saja

Permukaannya **tidak memiliki** cara mengubah maupun menghapus; pada
PostgreSQL `peran_telemetri` juga tidak memegang haknya (T-2).

## Tidak dibaca untuk menyesuaikan apa pun

`terakhir` dan `milik` ada bagi perekam (`return_visit`, durasi sesi) dan bagi
uji. Pemilihan beranda dan jawaban tidak menerima penyimpan ini (C-14, R-09).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Final, Protocol

from src.penyimpanan.sambungan import SambunganAktif

PERAN_TELEMETRI: Final = "peran_telemetri"
"""Peran basis data perekam — `10-telemetri.sql`."""

_POLA_PEMILIK: Final = re.compile(r"psd_[a-z]{16}")
_KODE: Final = frozenset(
    {
        "session_start",
        "session_end",
        "question_asked",
        "answer_served",
        "answer_rejected_validator",
        "injection_suspected",
        "answer_rated",
        "citation_opened",
        "discovery_served",
        "discovery_opened",
        "discovery_read_complete",
        "discovery_dismissed",
        "discovery_saved",
        "knowledge_check_started",
        "knowledge_check_completed",
        "commitment_created",
        "commitment_status_updated",
        "return_visit",
        "search_performed",
        "export_performed",
    }
)
"""Salinan nilai `JenisPeristiwa` — lapisan ini tidak mengimpornya. Kesamaannya
dijaga `test_kode_salinan_sama_dengan_taksonomi`, bukan kepercayaan."""


@dataclass(frozen=True)
class BarisPeristiwa:
    """Enam bidang FR-J02, sebagaimana tersimpan."""

    pseudonim: str
    jenis: str
    waktu: datetime
    properti: dict[str, Any]
    versi_aplikasi: str
    versi_model: str


class PenyimpanTelemetri(Protocol):
    async def tambah(self, baris: BarisPeristiwa) -> None: ...

    async def terakhir(self, pemilik: str, jenis: str) -> datetime | None:
        """Waktu peristiwa terbaru berjenis itu milik pemilik, atau `None`."""
        ...

    async def milik(self, pemilik: str) -> tuple[BarisPeristiwa, ...]:
        """Seluruh peristiwa pemilik, terlama lebih dulu."""
        ...


def _sah(baris: BarisPeristiwa) -> None:
    if _POLA_PEMILIK.fullmatch(baris.pseudonim) is None:
        raise ValueError("pemilik peristiwa wajib pseudonim akun (C-05)")
    if baris.jenis not in _KODE:
        raise ValueError("jenis peristiwa di luar taksonomi D-01 Bagian 9 (FR-J01)")
    offset = baris.waktu.utcoffset()
    if offset is None or offset.total_seconds():
        raise ValueError("waktu wajib berzona UTC (KM-01)")
    if not baris.versi_aplikasi.strip() or not baris.versi_model.strip():
        raise ValueError("versi aplikasi dan versi model wajib terisi (FR-J02, C-09)")


@dataclass
class TelemetriMemori:
    """Pelaksana di memori — bagi uji dan `make jalan` tanpa basis data."""

    _baris: list[BarisPeristiwa] = field(default_factory=list)

    async def tambah(self, baris: BarisPeristiwa) -> None:
        _sah(baris)
        self._baris.append(baris)

    async def terakhir(self, pemilik: str, jenis: str) -> datetime | None:
        waktu = [b.waktu for b in self._baris if b.pseudonim == pemilik and b.jenis == jenis]
        return max(waktu, default=None)

    async def milik(self, pemilik: str) -> tuple[BarisPeristiwa, ...]:
        return tuple(
            sorted((b for b in self._baris if b.pseudonim == pemilik), key=lambda b: b.waktu)
        )


class TelemetriPostgres:
    """Sambungannya wajib tersambung sebagai `PERAN_TELEMETRI`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def tambah(self, baris: BarisPeristiwa) -> None:
        _sah(baris)
        await self._sambungan.execute(
            "INSERT INTO telemetri.peristiwa (pseudonim, jenis, waktu, properti, versi_aplikasi, "
            "versi_model) VALUES ($1, $2, $3, $4::jsonb, $5, $6)",
            baris.pseudonim,
            baris.jenis,
            baris.waktu,
            json.dumps(baris.properti),
            baris.versi_aplikasi,
            baris.versi_model,
        )

    async def terakhir(self, pemilik: str, jenis: str) -> datetime | None:
        b = await self._sambungan.fetchrow(
            "SELECT max(waktu) AS w FROM telemetri.peristiwa WHERE pseudonim = $1 AND jenis = $2",
            pemilik,
            jenis,
        )
        return None if b is None else b["w"]  # type: ignore[return-value]

    async def milik(self, pemilik: str) -> tuple[BarisPeristiwa, ...]:
        baris = await self._sambungan.fetch(
            "SELECT pseudonim, jenis, waktu, properti, versi_aplikasi, versi_model "
            "FROM telemetri.peristiwa WHERE pseudonim = $1 ORDER BY waktu, nomor",
            pemilik,
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


def _objek(nilai: object) -> dict[str, Any]:
    hasil = json.loads(nilai) if isinstance(nilai, str) else nilai
    if not isinstance(hasil, dict):
        raise TypeError("kolom properti bukan objek")
    return hasil
