"""Perkakas penarikan data — T-5 fitur 033, NFR-09, K-7, plan Bagian 8.

    python -m perkakas.penarikan daftar
    python -m perkakas.penarikan jalankan

Tersambung sebagai `peran_penarikan` pada basis data perilaku dan
`peran_penarikan_pseudonim` pada basis data pseudonim — dua peran yang tidak
dipegang layanan aplikasi. Alamat dari `PGHOST` dan `PGPORT`, sandi peran dari
`PGPASSWORD` bila peladen memintanya; tidak pernah dari berkas repositori.

## Yang dicetak, dan yang tidak

Nomor permintaan, umurnya, dan jumlah baris terhapus per tabel. **Pseudonim
tidak pernah dicetak** (R-09): orang yang menjalankan perkakas tidak
membutuhkannya, dan keluaran terminal tersalin ke tempat yang tidak dijaga.

## Empat belas hari

`daftar` menandai permintaan yang umurnya melampaui batas NFR-09. Perkakas
tidak menjalankan dirinya sendiri — penjadwal belum ada (P-1 C tidak
dipilih) — sehingga tanda itu satu-satunya pengingat bagi tim.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Final, TextIO

from src.penyimpanan.penarikan import (
    PERAN_PENARIKAN,
    PERAN_PENARIKAN_PSEUDONIM,
    TABEL_DATA_PENGGUNA,
    PenarikanPostgres,
)

BATAS_HARI: Final = 14
"""NFR-09 apa adanya: "permintaan dipenuhi ≤ 14 hari"."""


def _penghurai() -> argparse.ArgumentParser:
    penghurai = argparse.ArgumentParser(
        prog="python -m perkakas.penarikan",
        description="Penuhi permintaan penarikan data peserta (NFR-09).",
    )
    sub = penghurai.add_subparsers(dest="perintah", required=True)
    sub.add_parser("daftar", help="tampilkan permintaan tertunda beserta umurnya")
    sub.add_parser("jalankan", help="penuhi seluruh permintaan tertunda, satu per satu")
    return penghurai


async def _jalankan(
    perintah: str, penarikan: PenarikanPostgres, keluar: TextIO, kini: datetime
) -> int:
    tertunda = await penarikan.tertunda()
    if not tertunda:
        print("Tidak ada permintaan tertunda.", file=keluar)
        return 0
    if perintah == "daftar":
        for p in tertunda:
            umur = (kini - p.diminta_pada).days
            tanda = f" · melewati {BATAS_HARI} hari (NFR-09)" if umur > BATAS_HARI else ""
            print(
                f"#{p.nomor} · diminta {p.diminta_pada.date().isoformat()} · {umur} hari{tanda}",
                file=keluar,
            )
        return 0
    for p in tertunda:
        hasil = await penarikan.jalankan(p.nomor, sekarang=kini)
        if hasil is None:
            print(f"#{p.nomor} sudah dipenuhi atau tidak ada lagi.", file=keluar)
            continue
        jumlah = sum(hasil.jumlah_baris.values())
        print(f"#{p.nomor} dipenuhi — {jumlah} baris terhapus:", file=keluar)
        for tabel in TABEL_DATA_PENGGUNA:
            print(f"  {tabel}: {hasil.jumlah_baris.get(tabel, 0)}", file=keluar)
        print(f"  pemetaan pseudonim: {hasil.pemetaan}", file=keluar)
    return 0


def utama(
    argv: list[str],
    *,
    penarikan: PenarikanPostgres,
    keluar: TextIO = sys.stdout,
    sekarang: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """Titik masuk yang dapat diuji: penyimpan, keluaran, dan jam disuntikkan."""
    argumen = _penghurai().parse_args(argv)
    return asyncio.run(_jalankan(argumen.perintah, penarikan, keluar, sekarang()))


class _Sambungan:  # pragma: no cover — dipakai orang, bukan uji
    """Satu sambungan baru per kueri, sebagai satu peran pada satu basis data."""

    def __init__(self, host: str, porta: int, peran: str, basis_data: str) -> None:
        self._host, self._porta, self._peran, self._basis = host, porta, peran, basis_data

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        sambungan = await asyncpg.connect(
            host=self._host, port=self._porta, user=self._peran, database=self._basis
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def fetch(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetch", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("execute", kueri, *argumen)


if __name__ == "__main__":  # pragma: no cover
    import os

    host = os.environ.get("PGHOST", "127.0.0.1")
    porta = int(os.environ.get("PGPORT", "5432"))
    raise SystemExit(
        utama(
            sys.argv[1:],
            penarikan=PenarikanPostgres(
                _Sambungan(host, porta, PERAN_PENARIKAN, "smart_coaching"),
                _Sambungan(host, porta, PERAN_PENARIKAN_PSEUDONIM, "smart_coaching_pseudonim"),
            ),
        )
    )
