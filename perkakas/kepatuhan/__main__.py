"""Titik masuk penjalan uji kepatuhan — T-2 fitur 042, R-01, R-06, P-1 A, P-4 A.

Kode keluar: 0 lolos; 1 ada yang gagal; 2 masukan tidak sah, tanpa apa pun
dijalankan maupun dicatat; 4 tidak ada yang gagal tetapi belum lengkap.

Akar logbook bukan argumen baris perintah (fitur 040): putaran tercatat pada
logbook repositori; uji memanggil `utama(…, akar_logbook=…)`.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final, TextIO

from src.rag.evaluasi.jejak import id_percobaan_terpakai

from perkakas.evaluasi import AKAR_LOGBOOK, versi_kode_git
from perkakas.kepatuhan.basis_data import (
    BASIS_DATA,
    BASIS_DATA_PSEUDONIM,
    periksa_uk02,
    periksa_uk04,
    periksa_uk08,
    periksa_uk09,
)
from perkakas.kepatuhan.daftar import BELUM_BAHAN, KODE_UK
from perkakas.kepatuhan.hasil import (
    KODE_KELUAR,
    HasilUK,
    Keadaan,
    KonfigurasiApi,
    Konteks,
    Pemeriksa,
    catat_l1,
    keseluruhan,
    laporan,
)

_LINGKUNGAN: Final = re.compile(r"[a-z0-9][a-z0-9-]{0,31}")
_ID_PERCOBAAN: Final = re.compile(r"EXP-\d{4}-\d{3}")


def _penghurai() -> argparse.ArgumentParser:
    penghurai = argparse.ArgumentParser(
        prog="python -m perkakas.kepatuhan",
        description="Uji kepatuhan U5 atas satu lingkungan; tiga keadaan per UK.",
    )
    sub = penghurai.add_subparsers(dest="perintah", required=True)
    jalankan = sub.add_parser("jalankan", help="jalankan UK-01 s.d. UK-15")
    jalankan.add_argument("--lingkungan", required=True)
    jalankan.add_argument("--id-percobaan", required=True)
    return penghurai


async def jalankan_semua(
    konteks: Konteks, pemeriksa: Mapping[str, Pemeriksa]
) -> tuple[HasilUK, ...]:
    hasil: list[HasilUK] = []
    for kode in KODE_UK:
        if kode in BELUM_BAHAN:
            hasil.append(HasilUK(kode, Keadaan.BELUM, (BELUM_BAHAN[kode],)))
        elif kode not in pemeriksa:
            hasil.append(HasilUK(kode, Keadaan.BELUM, ("pemeriksaan belum terpasang",)))
        else:
            try:
                hasil.append(await pemeriksa[kode](konteks))
            except Exception as g:
                hasil.append(
                    HasilUK(kode, Keadaan.GAGAL, (f"pemeriksa terhenti ({type(g).__name__})",))
                )
    return tuple(hasil)


def utama(
    argv: list[str],
    *,
    konteks: Callable[[], Konteks],
    pemeriksa: Mapping[str, Pemeriksa],
    keluar: TextIO = sys.stdout,
    galat: TextIO = sys.stderr,
    akar_logbook: Path = AKAR_LOGBOOK,
    versi_kode: Callable[[], str] = versi_kode_git,
) -> int:
    try:
        argumen = _penghurai().parse_args(argv)
    except SystemExit as keluar_parser:
        return int(keluar_parser.code or 2)
    if not _LINGKUNGAN.fullmatch(argumen.lingkungan):
        print("Ditolak: nama lingkungan huruf kecil, angka, dan tanda hubung.", file=galat)
        return 2
    if not _ID_PERCOBAAN.fullmatch(argumen.id_percobaan):
        print("Ditolak: id percobaan wajib berbentuk EXP-2026-nnn (D-10 Bagian 3).", file=galat)
        return 2
    if id_percobaan_terpakai(akar_logbook, argumen.id_percobaan):
        print(f"Ditolak: {argumen.id_percobaan} sudah tercatat pada L1.", file=galat)
        return 2
    kini = konteks()
    kode_versi = versi_kode()
    hasil = asyncio.run(jalankan_semua(kini, pemeriksa))
    catat_l1(
        akar_logbook,
        id_percobaan=argumen.id_percobaan,
        lingkungan=argumen.lingkungan,
        versi_kode=kode_versi,
        hasil=hasil,
    )
    print(
        laporan(hasil, lingkungan=argumen.lingkungan, versi_kode=kode_versi, api=kini.api),
        file=keluar,
    )
    print(f"Tercatat pada L1 sebagai {argumen.id_percobaan}.", file=keluar)
    return KODE_KELUAR[keseluruhan(hasil)]


def konteks_dari_lingkungan(env: Mapping[str, str], akar_repo: Path) -> Konteks:
    """Alamat peladen dari `PGHOST`/`PGPORT` — basis data pseudonim boleh di
    peladen lain lewat `PGHOST_PSEUDONIM`/`PGPORT_PSEUDONIM`. Sandi dibaca
    `asyncpg` dari `PGPASSFILE`; penjalan tidak menerimanya lewat argumen.
    API hanya bila ketiga `KEPATUHAN_API`, `KEPATUHAN_AKUN`, `KEPATUHAN_KUKI` ada."""
    host, porta = env.get("PGHOST", "127.0.0.1"), int(env.get("PGPORT", "5432"))
    alamat = {
        BASIS_DATA: (host, porta),
        BASIS_DATA_PSEUDONIM: (
            env.get("PGHOST_PSEUDONIM", host),
            int(env.get("PGPORT_PSEUDONIM", str(porta))),
        ),
    }

    async def buka(peran: str, basis_data: str) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        h, p = alamat[basis_data]
        return await asyncpg.connect(host=h, port=p, user=peran, database=basis_data)

    nilai = [env.get(n, "").strip() for n in ("KEPATUHAN_API", "KEPATUHAN_AKUN", "KEPATUHAN_KUKI")]
    api = KonfigurasiApi(*nilai) if all(nilai) else None
    return Konteks(buka=buka, api=api, akar_repo=akar_repo)


def pemeriksa_bawaan() -> dict[str, Pemeriksa]:
    """Pemeriksa yang terpasang; UK tanpa pemeriksa belum dapat diperiksa."""
    return {
        "UK-02": periksa_uk02,
        "UK-04": periksa_uk04,
        "UK-08": periksa_uk08,
        "UK-09": periksa_uk09,
    }


if __name__ == "__main__":  # pragma: no cover
    import os

    raise SystemExit(
        utama(
            sys.argv[1:],
            konteks=lambda: konteks_dari_lingkungan(os.environ, AKAR_LOGBOOK.parent),
            pemeriksa=pemeriksa_bawaan(),
        )
    )
