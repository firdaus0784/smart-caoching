"""Penyimpan koleksi — T-5 fitur 032, R-01, R-02, R-08; K-1, K-4; FR-G06.

Bentuk tabelnya D-14 Bagian 5.1 dan `perkakas/basis_data/14-sumber-dan-koleksi.sql`.

## Tabelnya saja

Permukaan ini menyimpan, mengeluarkan, dan mendaftar baris koleksi seorang
pemilik. Ia **tidak** membaca butir tayang maupun tayang harian: kelayakan
butir dibaca penyimpan penemuan, dan `peran_koleksi` tidak memegang hak atas
keduanya. Sebaliknya penayang tidak memegang hak atas koleksi, sehingga
pemilihan beranda tidak dapat membacanya (R-03, C-14).

## Bukan tambah-saja

Peserta mengeluarkan butirnya sendiri, dan menyimpan ulang mengganti catatan
beserta waktunya. Koleksi milik peserta, bukan catatan penelitian; penarikan
data (NFR-09) menghapusnya.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, Protocol

from src.penyimpanan.sambungan import SambunganAktif

PERAN_KOLEKSI: Final = "peran_koleksi"
"""Peran basis data koleksi — `14-sumber-dan-koleksi.sql`."""

_POLA_PEMILIK: Final = re.compile(r"psd_[a-z]{16}")


@dataclass(frozen=True)
class BarisKoleksi:
    id_butir: str
    catatan: str | None
    disimpan_pada: datetime


class PenyimpanKoleksi(Protocol):
    async def simpan(
        self, pemilik: str, id_butir: str, catatan: str | None, *, sekarang: datetime
    ) -> BarisKoleksi:
        """Simpan, atau ganti catatan dan waktu bila sudah tersimpan."""
        ...

    async def keluarkan(self, pemilik: str, id_butir: str) -> bool:
        """`False` bila butir itu tidak ada pada koleksi pemilik."""
        ...

    async def milik(self, pemilik: str) -> tuple[BarisKoleksi, ...]:
        """Koleksi pemilik, terbaru disimpan lebih dulu."""
        ...


def _periksa(pemilik: str, catatan: str | None, sekarang: datetime) -> None:
    if _POLA_PEMILIK.fullmatch(pemilik) is None:
        raise ValueError("pemilik wajib pseudonim akun (C-05)")
    if catatan is not None and not catatan.strip():
        raise ValueError("catatan kosong disimpan sebagai None")
    offset = sekarang.utcoffset()
    if offset is None or offset.total_seconds():
        raise ValueError("waktu wajib berzona UTC (KM-01)")


def _urut(baris: list[BarisKoleksi]) -> tuple[BarisKoleksi, ...]:
    return tuple(sorted(baris, key=lambda b: (-b.disimpan_pada.timestamp(), b.id_butir)))


class KoleksiMemori:
    """Pelaksana di memori — bagi uji dan `make jalan` tanpa basis data."""

    def __init__(self) -> None:
        self._isi: dict[tuple[str, str], BarisKoleksi] = {}

    async def simpan(
        self, pemilik: str, id_butir: str, catatan: str | None, *, sekarang: datetime
    ) -> BarisKoleksi:
        _periksa(pemilik, catatan, sekarang)
        baris = BarisKoleksi(id_butir=id_butir, catatan=catatan, disimpan_pada=sekarang)
        self._isi[(pemilik, id_butir)] = baris
        return baris

    async def keluarkan(self, pemilik: str, id_butir: str) -> bool:
        return self._isi.pop((pemilik, id_butir), None) is not None

    async def milik(self, pemilik: str) -> tuple[BarisKoleksi, ...]:
        return _urut([b for (p, _), b in self._isi.items() if p == pemilik])


class KoleksiPostgres:
    """Sambungannya wajib tersambung sebagai `PERAN_KOLEKSI`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def simpan(
        self, pemilik: str, id_butir: str, catatan: str | None, *, sekarang: datetime
    ) -> BarisKoleksi:
        _periksa(pemilik, catatan, sekarang)
        b: Any = await self._sambungan.fetchrow(
            "INSERT INTO penemuan.koleksi (id_pengguna, id_butir, catatan, disimpan_pada) "
            "VALUES ($1, $2, $3, $4) ON CONFLICT (id_pengguna, id_butir) DO UPDATE "
            "SET catatan = EXCLUDED.catatan, disimpan_pada = EXCLUDED.disimpan_pada "
            "RETURNING id_butir, catatan, disimpan_pada",
            pemilik,
            id_butir,
            catatan,
            sekarang,
        )
        return BarisKoleksi(
            id_butir=str(b["id_butir"]), catatan=b["catatan"], disimpan_pada=b["disimpan_pada"]
        )

    async def keluarkan(self, pemilik: str, id_butir: str) -> bool:
        status = await self._sambungan.execute(
            "DELETE FROM penemuan.koleksi WHERE id_pengguna = $1 AND id_butir = $2",
            pemilik,
            id_butir,
        )
        return int(str(status).rsplit(" ", 1)[-1]) > 0

    async def milik(self, pemilik: str) -> tuple[BarisKoleksi, ...]:
        baris: Any = await self._sambungan.fetch(
            "SELECT id_butir, catatan, disimpan_pada FROM penemuan.koleksi "
            "WHERE id_pengguna = $1 ORDER BY disimpan_pada DESC, id_butir",
            pemilik,
        )
        return tuple(
            BarisKoleksi(
                id_butir=str(b["id_butir"]), catatan=b["catatan"], disimpan_pada=b["disimpan_pada"]
            )
            for b in baris
        )
