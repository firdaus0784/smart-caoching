"""Batas hari WIB — P-4 fitur 013, R-05, FR-G05, KM-01.

Waktu disimpan UTC (KM-01); "butir hari ini" dan tanggal kembali kandidat
bertunda berganti pada tengah malam **WIB** (Asia/Jakarta). Penetapan tim,
tanpa dasar literatur, diganti bila lokus pilot berada di zona lain.

Zona tetap UTC+7, bukan basis data zona: WIB tidak mengenal waktu musim panas,
dan basis data zona yang tidak terpasang pada peladen akan gagal saat jalan —
bukan saat disusun.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from typing import Final

WIB: Final = timezone(timedelta(hours=7), "WIB")


def tanggal_wib(waktu: datetime) -> date:
    """Tanggal WIB dari waktu berzona; waktu tanpa zona ditolak."""
    if waktu.utcoffset() is None:
        raise ValueError("waktu wajib berzona (KM-01)")
    return waktu.astimezone(WIB).date()


def iso_utc(waktu: datetime) -> str:
    """`2026-10-05T01:00:00Z` — bentuk waktu pada tanggapan D-14."""
    return waktu.astimezone(UTC).isoformat().replace("+00:00", "Z")
