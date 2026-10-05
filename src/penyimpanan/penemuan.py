"""Penyimpan butir hari ini dan "belum relevan" — T-3 fitur 013, R-02, R-05, R-07, K-2.

Bentuk tabelnya D-14 Bagian 4.6 dan 5.1 dan `perkakas/basis_data/09-kurasi.sql`.

## Yang dapat dibaca penayang

Butir tayang saja (R-02). Permukaan ini **tidak memiliki** cara membaca
kandidat, putusan, maupun penarikan — bukan dilarang, melainkan tidak ada; dan
peladen menolaknya pula (T-2). Butir yang ditarik tidak pernah tersedia bagi
pemilihan, tetapi `baca_tayang` tetap menyebutnya beserta waktu tariknya, agar
rute dapat menjawab satu bentuk bagi "ditarik" dan "tidak dikenal".

## Butir hari ini dicatat, bukan dihitung ulang (K-2)

Pemilihannya milik `susun_feed()` fitur 011; yang disimpan di sini hasilnya,
per pemilik dan **tanggal WIB** yang diserahkan pemanggil. Satu butir tayang
sekali bagi orang yang sama: pencatatan ulang diabaikan, bukan digandakan —
dua pemanggilan beranda serentak memilih himpunan yang sama.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Final, Protocol

from src.penyimpanan.kurasi import KOLOM_TAYANG, BarisTayang, KurasiMemori, baris_tayang
from src.penyimpanan.sambungan import SambunganAktif

PERAN_PENAYANGAN: Final = "peran_penayangan"
"""Peran basis data penayang — `09-kurasi.sql`."""

_POLA_PEMILIK: Final = re.compile(r"psd_[a-z]{16}")


class PenyimpanPenemuan(Protocol):
    async def baca_tayang(self, id_butir: str) -> BarisTayang | None:
        """Butir tayang, termasuk yang sudah ditarik; `None` bila tidak pernah tayang."""
        ...

    async def tayang_menurut_kategori(self, kategori: tuple[str, ...]) -> tuple[BarisTayang, ...]:
        """Butir tayang **yang belum ditarik** pada kategori itu, terlama lebih dulu."""
        ...

    async def catatan_hari_ini(self, pemilik: str, tanggal: date) -> tuple[str, ...]: ...

    async def catat_hari_ini(
        self, pemilik: str, tanggal: date, id_butir: tuple[str, ...], *, sekarang: datetime
    ) -> None: ...

    async def pernah_tayang(self, pemilik: str) -> frozenset[str]: ...

    async def ditolak(self, pemilik: str) -> frozenset[str]: ...

    async def catat_belum_relevan(
        self, pemilik: str, id_butir: str, alasan: str, *, sekarang: datetime
    ) -> None: ...


def _pemilik(pemilik: str) -> None:
    if _POLA_PEMILIK.fullmatch(pemilik) is None:
        raise ValueError("pemilik wajib pseudonim akun (C-05)")


def _utc(waktu: datetime) -> None:
    offset = waktu.utcoffset()
    if offset is None or offset.total_seconds():
        raise ValueError("waktu wajib berzona UTC (KM-01)")


@dataclass
class _Milik:
    tayang: dict[str, tuple[date, int]] = field(default_factory=dict)
    ditolak: set[str] = field(default_factory=set)


class PenemuanMemori:
    """Pelaksana di memori; butir tayangnya dibaca dari `KurasiMemori` yang sama."""

    def __init__(self, kurasi: KurasiMemori) -> None:
        self._kurasi = kurasi
        self._milik: dict[str, _Milik] = {}

    async def baca_tayang(self, id_butir: str) -> BarisTayang | None:
        return self._kurasi.baris_tayang().get(id_butir)

    async def tayang_menurut_kategori(self, kategori: tuple[str, ...]) -> tuple[BarisTayang, ...]:
        aktif = [
            t
            for t in self._kurasi.baris_tayang().values()
            if t.ditarik_pada is None and t.kategori in kategori
        ]
        return tuple(sorted(aktif, key=lambda t: (t.tayang_pada, t.id_butir)))

    async def catatan_hari_ini(self, pemilik: str, tanggal: date) -> tuple[str, ...]:
        satu = self._milik.get(pemilik)
        if satu is None:
            return ()
        hari = [(urutan, i) for i, (t, urutan) in satu.tayang.items() if t == tanggal]
        return tuple(i for _, i in sorted(hari))

    async def catat_hari_ini(
        self, pemilik: str, tanggal: date, id_butir: tuple[str, ...], *, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        satu = self._milik.setdefault(pemilik, _Milik())
        for urutan, i in enumerate(id_butir, start=1):
            satu.tayang.setdefault(i, (tanggal, urutan))

    async def pernah_tayang(self, pemilik: str) -> frozenset[str]:
        satu = self._milik.get(pemilik)
        return frozenset() if satu is None else frozenset(satu.tayang)

    async def ditolak(self, pemilik: str) -> frozenset[str]:
        satu = self._milik.get(pemilik)
        return frozenset() if satu is None else frozenset(satu.ditolak)

    async def catat_belum_relevan(
        self, pemilik: str, id_butir: str, alasan: str, *, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        if not alasan.strip():
            raise ValueError("alasan wajib terisi (FR-G07)")
        self._milik.setdefault(pemilik, _Milik()).ditolak.add(id_butir)


class PenemuanPostgres:
    """Sambungannya wajib tersambung sebagai `PERAN_PENAYANGAN`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def baca_tayang(self, id_butir: str) -> BarisTayang | None:
        b = await self._sambungan.fetchrow(
            f"SELECT {KOLOM_TAYANG} FROM kurasi.butir_tayang WHERE id_butir = $1", id_butir
        )
        return None if b is None else baris_tayang(b)

    async def tayang_menurut_kategori(self, kategori: tuple[str, ...]) -> tuple[BarisTayang, ...]:
        baris = await self._sambungan.fetch(
            f"SELECT {KOLOM_TAYANG} FROM kurasi.butir_tayang "
            "WHERE ditarik_pada IS NULL AND kategori = ANY($1::text[]) "
            "ORDER BY tayang_pada, id_butir",
            list(kategori),
        )
        return tuple(baris_tayang(b) for b in baris)

    async def catatan_hari_ini(self, pemilik: str, tanggal: date) -> tuple[str, ...]:
        baris = await self._sambungan.fetch(
            "SELECT id_butir FROM penemuan.tayang_harian WHERE id_pengguna = $1 AND tanggal = $2 "
            "ORDER BY urutan, id_butir",
            pemilik,
            tanggal,
        )
        return tuple(str(b["id_butir"]) for b in baris)

    async def catat_hari_ini(
        self, pemilik: str, tanggal: date, id_butir: tuple[str, ...], *, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        await self._sambungan.execute(
            "INSERT INTO penemuan.tayang_harian (id_pengguna, tanggal, id_butir, urutan, "
            "ditayangkan_pada) SELECT $1, $2, x.id, x.n::smallint, $4 "
            "FROM unnest($3::text[]) WITH ORDINALITY AS x(id, n) "
            "ON CONFLICT (id_pengguna, id_butir) DO NOTHING",
            pemilik,
            tanggal,
            list(id_butir),
            sekarang,
        )

    async def pernah_tayang(self, pemilik: str) -> frozenset[str]:
        baris = await self._sambungan.fetch(
            "SELECT id_butir FROM penemuan.tayang_harian WHERE id_pengguna = $1", pemilik
        )
        return frozenset(str(b["id_butir"]) for b in baris)

    async def ditolak(self, pemilik: str) -> frozenset[str]:
        baris = await self._sambungan.fetch(
            "SELECT DISTINCT id_butir FROM penemuan.belum_relevan WHERE id_pengguna = $1", pemilik
        )
        return frozenset(str(b["id_butir"]) for b in baris)

    async def catat_belum_relevan(
        self, pemilik: str, id_butir: str, alasan: str, *, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        if not alasan.strip():
            raise ValueError("alasan wajib terisi (FR-G07)")
        await self._sambungan.execute(
            "INSERT INTO penemuan.belum_relevan (id_pengguna, id_butir, alasan, waktu) "
            "VALUES ($1, $2, $3, $4)",
            pemilik,
            id_butir,
            alasan,
            sekarang,
        )
