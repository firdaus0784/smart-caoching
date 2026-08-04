"""Bentuk entri catatan yang ditulis manusia — R-11, `docs/D10.md` Bagian 6 dan 9.

L1 dan L2 ditulis kode dan dijaga tipe `Versi`. L4 dan L7 ditulis manusia, dan
di situlah bidang paling mudah terlewat — biasanya bidang yang paling penting,
karena ia yang paling tidak nyaman diisi.

`docs/D10.md` Bagian 7 memberi contoh sikap yang ditiru di sini: pada L5 ia
membuat bidang `dilaporkan_dalam_naskah` eksplisit, dengan alasan keputusan
untuk tidak melaporkan sesuatu harus diambil sadar, bukan terjadi karena lupa.
Bidang `Pemberi izin` pada L7 ada karena alasan yang sama — `docs/D12.md`
Bagian 8 mewajibkan gerbang yang dilewati dicatat beserta siapa yang
mengizinkannya.

Berkasnya berbentuk Markdown, bukan JSONL, karena pembacanya manusia: ketua
peneliti pada tinjauan bulanan (`docs/D10.md` Bagian 12) dan penyusun naskah.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.logbook.penulis import Temuan

BIDANG_L4: tuple[str, ...] = (
    "Tanggal",
    "Konteks",
    "Keputusan",
    "Alternatif",
    "Dampak",
    "Pemutus",
)

BIDANG_L7: tuple[str, ...] = (
    "Tanggal",
    "Jenis penggunaan",
    "Uraian",
    "Verifikasi manusia",
    "Pemberi izin",
)

# Entri dikenali dari kodenya (KB-001, AI-002), bukan dari sembarang judul
# tingkat dua. Tanpa pembatasan ini, judul dokumentasi pada kepala berkas
# ikut terbaca sebagai entri yang kekurangan seluruh bidangnya.
POLA_ENTRI = re.compile(r"^##\s+([A-Z]{2}-\d+)", re.MULTILINE)
POLA_BIDANG = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$", re.MULTILINE)


def periksa_bentuk_catatan(berkas: Path, bidang_wajib: tuple[str, ...]) -> list[Temuan]:
    """Setiap entri membawa seluruh bidang wajib, dan seluruhnya terisi.

    Berkas tanpa entri bukan pelanggaran: belum ada keputusan tercatat adalah
    keadaan sah di awal siklus.
    """
    if not berkas.is_file():
        return [Temuan(berkas, 0, f"{berkas.name} tidak ditemukan")]

    isi = berkas.read_text(encoding="utf-8")
    tanda = list(POLA_ENTRI.finditer(isi))
    if not tanda:
        return []

    temuan: list[Temuan] = []
    for urutan, awal in enumerate(tanda):
        kode = awal.group(1)
        akhir = tanda[urutan + 1].start() if urutan + 1 < len(tanda) else len(isi)
        potongan = isi[awal.start() : akhir]
        baris_awal = isi[: awal.start()].count("\n") + 1

        terisi = {
            nama.strip(): nilai.strip()
            for nama, nilai in POLA_BIDANG.findall(potongan)
            if nama.strip() and not set(nama.strip()) <= {"-", ":"}
        }

        for nama in bidang_wajib:
            if nama not in terisi:
                temuan.append(
                    Temuan(berkas, baris_awal, f"entri {kode}: bidang {nama!r} tidak ada")
                )
            elif not terisi[nama]:
                temuan.append(
                    Temuan(
                        berkas,
                        baris_awal,
                        f"entri {kode}: bidang {nama!r} kosong — bidang yang ada "
                        "tetapi tidak diisi sama saja dengan tidak ada",
                    )
                )
    return temuan
