"""Penanda cakupan dan pemeriksa penurunan — R-17, C-11, NFR-16.

Dua hal berbeda, sengaja dipisah:

- **C-11** cakupan tidak turun — relatif terhadap penanda tersimpan
- **NFR-16** cakupan modul inti tidak di bawah 60% — mutlak

Sistem dapat memenuhi yang pertama sambil melanggar yang kedua selamanya, bila
penandanya rendah sejak awal dan tidak pernah naik. Menggabungkan keduanya
menjadi satu angka menyembunyikan hal itu, dan angka yang menyembunyikan
sesuatu adalah persis yang PU-03 pada `docs/D08.md` larang.

Cakupan diukur pada `src/` saja. `perkakas/` adalah alat bantu pembangunan,
bukan modul inti yang dinilai TKT 3.

Catatan keadaan pada fitur 001: `src/` masih nyaris kosong sampai Fase D, maka
penanda dimulai pada 0,0 dan lantai NFR-16 belum berlaku. Penanda diisi dengan
nilai terukur sebenarnya sebelum Gerbang 4 — itu butir G4-16, bukan hal yang
boleh terlupa.
"""

from __future__ import annotations

import json
import subprocess
import tomllib
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

BERKAS_PENANDA = "penanda-cakupan.toml"
LANTAI_NFR16 = 60.0


def baca_penanda(akar: Path) -> float:
    """Nilai penanda tersimpan.

    FileNotFoundError sengaja dibiarkan naik: menghapus penanda bukan cara sah
    meloloskan pemeriksa, dan mengembalikan 0,0 diam-diam akan menjadikannya
    demikian.
    """
    berkas = akar / BERKAS_PENANDA
    if not berkas.is_file():
        raise FileNotFoundError(
            f"{BERKAS_PENANDA} tidak ditemukan — tanpa penanda, C-11 tidak punya "
            "pembanding dan 'tidak turun' tidak dapat didefinisikan"
        )
    isi = tomllib.loads(berkas.read_text(encoding="utf-8"))
    return float(isi["tercatat"])


def ukur_cakupan(akar: Path) -> tuple[float, int]:
    """Jalankan uji dengan pengukuran cakupan; kembalikan (persen, pernyataan).

    Memakai subproses, bukan mengimpor `coverage` langsung. `coverage` adalah
    ketergantungan transitif dari pytest-cov, dan mengimpor paket transitif
    secara langsung memperlakukannya sebagai ketergantungan langsung tanpa
    melewati persetujuan C-12.
    """
    laporan = akar / ".cakupan-sementara.json"
    subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "--cov=src",
            f"--cov-report=json:{laporan}",
            "-q",
        ],
        cwd=akar,
        capture_output=True,
        text=True,
        check=False,
    )
    if not laporan.is_file():
        return 0.0, 0
    data = json.loads(laporan.read_text(encoding="utf-8"))
    laporan.unlink()
    ringkas = data["totals"]
    return float(ringkas["percent_covered"]), int(ringkas["num_statements"])


def periksa_penurunan(penanda: float, sekarang: float, berkas: Path) -> list[Temuan]:
    """C-11 — cakupan tidak turun."""
    if sekarang >= penanda:
        return []
    return [
        Temuan(
            berkas,
            0,
            f"cakupan turun dari penanda {penanda} menjadi {sekarang} — C-11 "
            "melarang penurunan cakupan pada modul inti",
        )
    ]


def periksa_lantai(sekarang: float, pernyataan: int, berkas: Path) -> list[Temuan]:
    """NFR-16 — cakupan modul inti tidak di bawah 60%.

    Tidak berlaku selama belum ada pernyataan yang dapat diukur; rasio atas
    nol bukan informasi.
    """
    if pernyataan == 0 or sekarang >= LANTAI_NFR16:
        return []
    return [
        Temuan(
            berkas,
            0,
            f"cakupan modul inti {sekarang} di bawah lantai NFR-16 "
            f"({LANTAI_NFR16}) atas {pernyataan} pernyataan",
        )
    ]


def periksa_cakupan(akar: Path) -> list[Temuan]:
    berkas = akar / BERKAS_PENANDA
    try:
        penanda = baca_penanda(akar)
    except FileNotFoundError as galat:
        return [Temuan(berkas, 0, str(galat))]

    sekarang, pernyataan = ukur_cakupan(akar)
    return [
        *periksa_penurunan(penanda, sekarang, berkas),
        *periksa_lantai(sekarang, pernyataan, berkas),
    ]
