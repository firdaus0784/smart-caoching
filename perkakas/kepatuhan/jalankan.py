"""Pelaksana `make compliance` — R-15, R-16.

Tiga keadaan wajib, dan tidak ada keadaan keempat:

- `LULUS` pemeriksa ada dan tidak menemukan pelanggaran
- `GAGAL` pemeriksa ada dan menemukan pelanggaran
- `BELUM` belum ada pemeriksa; wajib menyebut fitur yang akan mengaktifkannya

Dua aturan membuat pelaksana ini tidak dapat berbohong:

1. Kedua puluh pasal wajib muncul tepat sekali. Daftar yang tidak lengkap
   **menggagalkan** pelaksana alih-alih menghasilkan laporan yang lebih
   pendek — sehingga menambah pasal ke konstitusi tanpa menetapkan statusnya
   merusak pembangunan, bukan lolos senyap.
2. Keluaran kosong diperlakukan sebagai kegagalan. Diam bukan lulus (R-16).

Pemeriksa yang melemparkan galat dihitung `GAGAL`, bukan dilewati. Pemeriksa
rusak yang dianggap lulus adalah bentuk paling halus dari laporan palsu.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL, Pasal

DIHARAPKAN = tuple(f"C-{n:02d}" for n in range(1, 21))


class Keadaan(Enum):
    LULUS = "LULUS"
    GAGAL = "GAGAL"
    BELUM = "BELUM-DAPAT-DIPERIKSA"


@dataclass(frozen=True)
class Baris:
    kode: str
    keadaan: Keadaan
    keterangan: str


def _periksa_kelengkapan(daftar: tuple[Pasal, ...]) -> list[Baris]:
    """Pasal yang hilang dari daftar, dilaporkan sebagai kegagalan."""
    ada = {p.kode for p in daftar}
    return [
        Baris(
            kode,
            Keadaan.GAGAL,
            f"pasal {kode} ada pada constitution.md tetapi tidak punya entri "
            "pada daftar — menambah pasal tanpa menetapkan statusnya tidak "
            "boleh lolos senyap",
        )
        for kode in DIHARAPKAN
        if kode not in ada
    ]


def susun_laporan(akar: Path, daftar: tuple[Pasal, ...] = DAFTAR_PASAL) -> list[Baris]:
    hasil: list[Baris] = []

    for pasal in daftar:
        if pasal.pemeriksa is None:
            hasil.append(
                Baris(
                    pasal.kode,
                    Keadaan.BELUM,
                    f"{pasal.ringkas} — menunggu fitur {pasal.fitur_pengunci}",
                )
            )
            continue
        try:
            temuan = pasal.pemeriksa(akar)
        except Exception as galat:  # noqa: BLE001 — pemeriksa rusak bukan lulus
            hasil.append(
                Baris(
                    pasal.kode,
                    Keadaan.GAGAL,
                    f"pemeriksa melemparkan galat: {type(galat).__name__}: {galat}",
                )
            )
            continue
        if temuan:
            hasil.append(
                Baris(
                    pasal.kode,
                    Keadaan.GAGAL,
                    "; ".join(str(t) for t in temuan[:5])
                    + (f" (dan {len(temuan) - 5} lagi)" if len(temuan) > 5 else ""),
                )
            )
        else:
            hasil.append(Baris(pasal.kode, Keadaan.LULUS, pasal.ringkas))

    hasil.extend(_periksa_kelengkapan(daftar))
    hasil.sort(key=lambda b: b.kode)
    return hasil


def _cetak(laporan: list[Baris]) -> None:
    lebar = max((len(b.keadaan.value) for b in laporan), default=0)
    for baris in laporan:
        print(f"{baris.kode}  {baris.keadaan.value:<{lebar}}  {baris.keterangan}")


def main() -> int:
    akar = Path(__file__).resolve().parents[2]
    laporan = susun_laporan(akar)

    if not laporan:
        print("GAGAL — laporan kepatuhan kosong. Diam bukan lulus (R-16).")
        return 1

    _cetak(laporan)

    jumlah = {k: sum(1 for b in laporan if b.keadaan is k) for k in Keadaan}
    print(
        f"\n{jumlah[Keadaan.LULUS]} lulus  "
        f"{jumlah[Keadaan.GAGAL]} gagal  "
        f"{jumlah[Keadaan.BELUM]} belum dapat diperiksa"
    )

    if jumlah[Keadaan.BELUM]:
        print(
            "\nDaftar belum-dapat-diperiksa adalah tagihan, bukan pengecualian.\n"
            "Ia wajib menyusut pada setiap fitur berikutnya, tidak pernah bertambah."
        )

    return 1 if jumlah[Keadaan.GAGAL] else 0


if __name__ == "__main__":
    sys.exit(main())
