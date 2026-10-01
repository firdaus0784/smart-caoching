"""Perkakas akun tim peneliti — T-7 fitur 029, P-5, P-7, K-5, plan Bagian 9.

    python -m perkakas.akun buat --id ks-017 --peran pengguna
    python -m perkakas.akun atur-ulang-sandi --id ks-017
    python -m perkakas.akun nonaktifkan --id ks-017

Tersambung sebagai `peran_pengelola_akun`; alamat dari `PGHOST` dan `PGPORT`,
sandi peran dari `PGPASSWORD` bila peladen memintanya. Tidak pernah tersambung
ke basis data pseudonim (C-05).

## Yang sengaja tidak diterima

Nama orang, nomor induk, surel, maupun nomor apa pun. `--id` wajib berpola
`^[a-z]{2,8}-[0-9]{3}$` — nama akun buatan tim, misalnya `ks-017` — dan juga
lolos pendeteksi data pribadi FR-B04. Pasangan akun dengan orang sungguhan
dipegang tim di luar layanan aplikasi (P-1 A, KA-03).

## Sandi dicetak sekali

Sandi bangkitan dicetak ke keluaran baku **sekali**, untuk diserahkan kepada
peserta, dan tidak ditulis ke berkas maupun log. Yang tersimpan hanya
turunannya. Kehilangan sandi berarti atur ulang, bukan pembacaan ulang.

Pseudonim dibangkitkan acak dan **tidak dicetak**: ia tidak dibutuhkan siapa
pun yang memegang keluaran perkakas ini.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import secrets
import sys
from datetime import UTC, datetime
from typing import Any, TextIO

from src.api import sandi
from src.api.peran import Peran
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.akun import PERAN_PENGELOLA_AKUN, PengelolaAkunPostgres

POLA_ID = re.compile(r"[a-z]{2,8}-[0-9]{3}")
_HURUF_PSEUDONIM = "abcdefghijklmnopqrstuvwxyz"


def bangkitkan_pseudonim() -> str:
    """`psd_` + 16 huruf kecil acak, sekitar 75 bit — huruf saja (KB-158)."""
    return "psd_" + "".join(secrets.choice(_HURUF_PSEUDONIM) for _ in range(16))


def _id_sah(nilai: str) -> bool:
    return POLA_ID.fullmatch(nilai) is not None and not periksa_data_pribadi(nilai)


def _penghurai() -> argparse.ArgumentParser:
    penghurai = argparse.ArgumentParser(
        prog="python -m perkakas.akun", description="Kelola akun peserta pilot."
    )
    sub = penghurai.add_subparsers(dest="perintah", required=True)
    buat = sub.add_parser("buat", help="buat akun dan cetak sandi awalnya sekali")
    buat.add_argument("--id", required=True)
    buat.add_argument("--peran", required=True)
    for nama, bantuan in (
        ("atur-ulang-sandi", "ganti sandi, cabut seluruh sesi, buka penahanan"),
        ("nonaktifkan", "nonaktifkan akun dan cabut seluruh sesinya"),
    ):
        satu = sub.add_parser(nama, help=bantuan)
        satu.add_argument("--id", required=True)
    return penghurai


async def _jalankan(
    argumen: argparse.Namespace,
    pengelola: PengelolaAkunPostgres,
    keluar: TextIO,
    galat: TextIO,
    parameter: sandi.ParameterScrypt,
) -> int:
    if not _id_sah(argumen.id):
        # Masukan yang ditolak tidak dikutip: ia mungkin nama orang.
        print("Ditolak: --id wajib berpola nama akun tim, misalnya ks-017.", file=galat)
        return 2
    kini = datetime.now(UTC)
    if argumen.perintah == "buat":
        if argumen.peran not in {p.value for p in Peran}:
            print("Ditolak: --peran wajib salah satu peran D-14 Bagian 3.", file=galat)
            return 2
        kata = sandi.bangkitkan_sandi()
        dibuat = await pengelola.buat_akun(
            id_akun=argumen.id,
            pseudonim=bangkitkan_pseudonim(),
            peran=argumen.peran,
            turunan_sandi=sandi.turunkan(kata, parameter=parameter),
            sekarang=kini,
        )
        if not dibuat:
            print(f"Ditolak: akun {argumen.id} sudah ada.", file=galat)
            return 1
        print(f"Akun {argumen.id} dibuat. Sandi awal: {kata}", file=keluar)
        return 0
    if argumen.perintah == "atur-ulang-sandi":
        kata = sandi.bangkitkan_sandi()
        ada = await pengelola.atur_ulang_sandi(
            id_akun=argumen.id,
            turunan_sandi=sandi.turunkan(kata, parameter=parameter),
            sekarang=kini,
        )
        if not ada:
            print(f"Ditolak: akun {argumen.id} tidak ada.", file=galat)
            return 1
        print(f"Sandi akun {argumen.id} diganti. Sandi baru: {kata}", file=keluar)
        return 0
    ada = await pengelola.nonaktifkan(id_akun=argumen.id, sekarang=kini)
    if not ada:
        print(f"Ditolak: akun {argumen.id} tidak ada.", file=galat)
        return 1
    print(f"Akun {argumen.id} dinonaktifkan; seluruh sesinya dicabut.", file=keluar)
    return 0


def utama(
    argv: list[str],
    *,
    pengelola: PengelolaAkunPostgres,
    keluar: TextIO = sys.stdout,
    galat: TextIO = sys.stderr,
    parameter: sandi.ParameterScrypt = sandi.PARAMETER,
) -> int:
    """Titik masuk yang dapat diuji: pengelola dan aliran keluaran disuntikkan.
    `parameter` disuntikkan hanya oleh uji; perkakas sungguhan memakai bawaan."""
    argumen = _penghurai().parse_args(argv)
    return asyncio.run(_jalankan(argumen, pengelola, keluar, galat, parameter))


class _SambunganPengelola:  # pragma: no cover — dipakai orang, bukan uji
    """Satu sambungan baru per kueri, sebagai `peran_pengelola_akun`."""

    def __init__(self, host: str, porta: int) -> None:
        self._host, self._porta = host, porta

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        sambungan = await asyncpg.connect(
            host=self._host, port=self._porta, user=PERAN_PENGELOLA_AKUN, database="smart_coaching"
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

    sambungan = _SambunganPengelola(
        os.environ.get("PGHOST", "127.0.0.1"), int(os.environ.get("PGPORT", "5432"))
    )
    raise SystemExit(utama(sys.argv[1:], pengelola=PengelolaAkunPostgres(sambungan)))
