"""Keadaan, hasil, laporan, dan catatan L1 — T-2 fitur 042, R-01, R-02, R-05, R-06.

Tiga keadaan, bukan dua. Uji yang tidak dapat dijalankan bukan uji yang
lulus; laporan yang mencampurkan keduanya membuat PS-01 terpenuhi sebelum
waktunya. Keseluruhan lolos hanya bila kelima belasnya lulus (D-08 Bagian 8,
ambang nol).

Rincian memuat pengenal — peran, tabel, rute, kode SQLSTATE, kode HTTP —
tidak pernah sandi, kuki, maupun isi baris (R-05).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Final

from src.logbook.penulis import Buku, tambah_baris
from src.logbook.versi import BELUM_BERLAKU, Versi


class Keadaan(Enum):
    LULUS = "lulus"
    GAGAL = "gagal"
    BELUM = "belum dapat diperiksa"


KODE_KELUAR: Final[Mapping[Keadaan, int]] = {Keadaan.LULUS: 0, Keadaan.GAGAL: 1, Keadaan.BELUM: 4}
"""0 lolos; 1 ada yang gagal; 4 tidak ada yang gagal tetapi belum lengkap. 2
masukan tidak sah — dipakai perkakas sebelum apa pun dijalankan."""


TUJUAN: Final = "Menjalankan uji kepatuhan U5 (D-08 Bagian 8, D-13 Bagian 8) atas satu lingkungan"


@dataclass(frozen=True)
class HasilUK:
    kode: str
    keadaan: Keadaan
    rincian: tuple[str, ...]


@dataclass(frozen=True)
class KonfigurasiApi:
    """Alamat API, id akun uji, dan kuki sesinya. Kuki tidak pernah tampil."""

    alamat: str
    akun: str
    kuki: str = field(repr=False)

    def __str__(self) -> str:
        return f"{self.alamat} sebagai {self.akun}"


@dataclass(frozen=True)
class Konteks:
    """Yang dibutuhkan pemeriksa: pembuka sambungan per peran dan basis data,
    konfigurasi API bila ada, dan akar kode yang terpasang."""

    buka: Callable[[str, str], Awaitable[Any]]
    api: KonfigurasiApi | None
    akar_repo: Path


Pemeriksa = Callable[[Konteks], Awaitable[HasilUK]]


def gabung(kode: str, bagian: Iterable[HasilUK]) -> HasilUK:
    """Beberapa percobaan satu UK: gagal mengalahkan belum, belum mengalahkan lulus."""
    semua = list(bagian)
    rincian = tuple(r for h in semua for r in h.rincian)
    return HasilUK(kode, keseluruhan(semua), rincian)


def keseluruhan(hasil: Sequence[HasilUK]) -> Keadaan:
    if any(h.keadaan is Keadaan.GAGAL for h in hasil):
        return Keadaan.GAGAL
    if any(h.keadaan is Keadaan.BELUM for h in hasil):
        return Keadaan.BELUM
    return Keadaan.LULUS


def laporan(
    hasil: Sequence[HasilUK], *, lingkungan: str, versi_kode: str, api: KonfigurasiApi | None
) -> str:
    akhir = keseluruhan(hasil)
    baris = [
        f"Lingkungan {lingkungan}; versi kode {versi_kode}.",
        f"API: {api if api is not None else 'tidak diberikan'}.",
    ]
    for h in hasil:
        baris.append(f"{h.kode} {h.keadaan.value}")
        baris.extend(f"  - {r}" for r in h.rincian)
    baris.append(
        "Lolos: kelima belas UK lulus."
        if akhir is Keadaan.LULUS
        else f"Tidak lolos: {sum(h.keadaan is Keadaan.GAGAL for h in hasil)} gagal, "
        f"{sum(h.keadaan is Keadaan.BELUM for h in hasil)} belum dapat diperiksa."
    )
    return "\n".join(baris)


def catat_l1(
    akar: Path,
    *,
    id_percobaan: str,
    lingkungan: str,
    versi_kode: str,
    hasil: Sequence[HasilUK],
) -> None:
    """Satu baris L1 per putaran — D-10 Bagian 3, R-06."""
    gagal = [h.kode for h in hasil if h.keadaan is Keadaan.GAGAL]
    versi = Versi(
        versi_kode=versi_kode,
        versi_model=BELUM_BERLAKU,
        versi_indeks=BELUM_BERLAKU,
        versi_skema_anotasi=BELUM_BERLAKU,
        pembagian_data=BELUM_BERLAKU,
    )
    tambah_baris(
        akar,
        Buku.L1,
        {
            "id_percobaan": id_percobaan,
            "tujuan": TUJUAN,
            "tugas": "kepatuhan",
            "lingkungan": lingkungan,
            "model_dasar": BELUM_BERLAKU,
            "perangkat_keras": BELUM_BERLAKU,
            "hasil": {
                h.kode: {"keadaan": h.keadaan.value, "rincian": list(h.rincian)} for h in hasil
            },
            "keseluruhan": keseluruhan(hasil).value,
            "status": "gagal" if gagal else "berhasil",
            "catatan": f"gagal: {', '.join(gagal)}" if gagal else "",
            **versi.model_dump(),
        },
    )
