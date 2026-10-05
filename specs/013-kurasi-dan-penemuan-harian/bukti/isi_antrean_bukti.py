"""Pengisi antrean **khusus bukti** — T-9 fitur 013, plan Bagian 10.2.

Di LUAR `make check`, dan tidak dipakai di lingkungan mana pun selain mesin
pembuat bukti.

## Mengapa ia ada, dan apa yang dilewatinya

`saring()` fitur 010 menahan setiap kandidat di lapis L4 sampai ambang
relevansi dikalibrasi (BT-24), sehingga `python -m perkakas.kurasi isi` hari
ini tidak memasukkan apa pun — TK-72, menunggu putusan tim. Bukti ujung ke
ujung tetap perlu antrean berisi.

Skrip ini menjalankan perkakas `isi` yang sama dengan **penyaring yang
menjalankan `saring()` sungguhan lalu meloloskan yang tertahan di L4** —
bentuk pilihan B TK-72 — dan **hanya** itu. Lapis L1 s.d. L3 tetap berjalan.
Butirnya buatan, ditandai "contoh bukti" pada judulnya, dan bukan isi
pengetahuan yang boleh dibaca kepala sekolah.

    cd specs/013-kurasi-dan-penemuan-harian/bukti
    PGHOST=/tmp PGPORT=55432 uv run python isi_antrean_bukti.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

AKAR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(AKAR))

from src.ingest.kurasi.butir import ButirPengetahuan  # noqa: E402
from src.ingest.kurasi.saring import HasilSaring, Keadaan, Lapis, Tindakan, saring  # noqa: E402
from src.penyimpanan.kurasi import PengisiAntreanPostgres  # noqa: E402

from perkakas import kurasi as perkakas_kurasi  # noqa: E402


def loloskan_l4(butir: ButirPengetahuan, **argumen: Any) -> HasilSaring:
    """`saring()` sungguhan; yang tertahan di L4 diloloskan — bukti saja."""
    hasil = saring(butir, **argumen)
    if hasil.lapis_terakhir is Lapis.L4_RELEVANSI and hasil.tindakan is Tindakan.TERTAHAN:
        return HasilSaring(
            lapis_terakhir=Lapis.L4_RELEVANSI,
            keadaan=Keadaan.LOLOS,
            tindakan=Tindakan.MASUK_ANTREAN,
            alasan="bukti fitur 013 — L4 diloloskan, menunggu TK-72",
        )
    return hasil


def entri(
    nomor: int, kategori: str, judul: str, jenis: str = "riset", status: str | None = None
) -> dict[str, Any]:
    return {
        "butir": {
            "id_butir": f"bukti-013-{nomor}",
            "jenis_sumber": jenis,
            "judul": f"{judul} (contoh bukti)",
            "alasan_relevansi": "Sekolah Anda menetapkan bidang ini sebagai prioritas pengelolaan.",
            "inti_temuan": "Contoh isi bagi bukti ujung ke ujung, bukan temuan sungguhan.",
            "implikasi_tindakan": ["Contoh langkah pertama.", "Contoh langkah kedua."],
            "perkiraan_waktu_baca": 3 + nomor % 3,
            "kategori": kategori,
            "id_dokumen_sumber": f"dok-bukti-013-{nomor}",
            "lisensi": "CC-BY",
            "status_keberlakuan": status,
            "tanggal_akses": "2026-10-05",
        },
        "sumber": {
            "judul": f"Dokumen contoh {nomor}",
            "penerbit": "Tim peneliti",
            "tahun": 2026,
            "tautan": None,
        },
    }


ISI = [
    entri(1, "K1", "Supervisi akademik terjadwal"),
    entri(2, "K1", "Pembelajaran berdiferensiasi", jenis="praktik_baik"),
    entri(3, "K5", "Pelaporan dana sekolah", jenis="regulasi", status="berlaku"),
    entri(4, "K7", "Persiapan akreditasi", jenis="data_resmi"),
    entri(5, "K3", "Program kesiswaan"),
]


if __name__ == "__main__":
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as berkas:
        json.dump(ISI, berkas)
    sambungan = perkakas_kurasi._SambunganPengisi(
        os.environ.get("PGHOST", "127.0.0.1"), int(os.environ.get("PGPORT", "5432"))
    )
    raise SystemExit(
        perkakas_kurasi.utama(
            ["isi", "--berkas", berkas.name],
            pengisi=PengisiAntreanPostgres(sambungan),
            penyaring=loloskan_l4,
        )
    )
