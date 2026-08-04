"""Kelengkapan jejak versi pada catatan percobaan — C-09, R-11, R-12, NFR-15.

Pemeriksa ini membaca baris yang **sudah tercatat** pada `logbook/L1`. Ia
tidak dapat memaksa sebuah percobaan dicatat — itu kedisiplinan manusia dan
ritme pengisian `docs/D10.md` Bagian 12 — tetapi ia dapat memastikan setiap
yang tercatat membawa jejak versinya utuh.

Pembedaan yang disengaja: `logbook/L1` yang belum ada bukan pelanggaran.
Belum ada percobaan adalah keadaan sah pada awal siklus. Yang tidak sah adalah
catatan yang ada tetapi tidak dapat diulang.
"""

from __future__ import annotations

import json
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

BERKAS_L1 = Path("logbook") / "L1-percobaan.jsonl"

BIDANG_VERSI = (
    "versi_kode",
    "versi_model",
    "versi_indeks",
    "versi_skema_anotasi",
    "pembagian_data",
)


def periksa_catatan_versi(akar: Path) -> list[Temuan]:
    berkas = akar / BERKAS_L1
    if not berkas.is_file():
        return []

    temuan: list[Temuan] = []
    for nomor, baris in enumerate(berkas.read_text(encoding="utf-8").splitlines(), start=1):
        if not baris.strip():
            continue
        try:
            catatan = json.loads(baris)
        except json.JSONDecodeError as galat:
            temuan.append(Temuan(berkas, nomor, f"baris tidak dapat diurai: {galat.msg}"))
            continue

        for bidang in BIDANG_VERSI:
            nilai = catatan.get(bidang)
            if nilai is None:
                temuan.append(
                    Temuan(berkas, nomor, f"bidang versi {bidang!r} tidak tercatat (C-09)")
                )
            elif not str(nilai).strip():
                temuan.append(
                    Temuan(
                        berkas,
                        nomor,
                        f"bidang versi {bidang!r} kosong — isi 'belum-berlaku' "
                        "bila memang belum berlaku (R-12)",
                    )
                )
    return temuan
