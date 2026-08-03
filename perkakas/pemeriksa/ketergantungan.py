"""Pemeriksa penyimpangan ketergantungan terhadap titik nol — R-18, C-12.

C-12 melarang ketergantungan baru tanpa persetujuan penanggung jawab teknis.
Larangan itu tidak dapat ditegakkan tanpa jawaban atas pertanyaan "baru
dibanding apa" — dan itulah gunanya `ketergantungan-disetujui.toml`, yang
merekam pohon transitif pada saat disetujui manusia di Gerbang 2.

Tiga jenis penyimpangan diperiksa terpisah karena akibatnya berbeda:

- paket masuk → ketergantungan menyelinap tanpa persetujuan
- paket hilang → titik nol tidak lagi menggambarkan keadaan
- versi bergeser → himpunan nama tetap utuh, sehingga pemeriksa yang hanya
  membandingkan nama akan melaporkan bersih

Yang ketiga paling mudah luput dan paling sering menjadi sebab hasil tidak
dapat diulang (NFR-15).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

NAMA_PROYEK = "smart-coaching"


def _normal(nama: str) -> str:
    return nama.strip().lower().replace("_", "-")


def _paket_pada_lock(lock: Path) -> dict[str, str]:
    isi = tomllib.loads(lock.read_text(encoding="utf-8"))
    paket: dict[str, str] = {}
    for butir in isi.get("package", []):
        nama = _normal(str(butir.get("name", "")))
        if nama and nama != NAMA_PROYEK:
            paket[nama] = str(butir.get("version", ""))
    return paket


def periksa_ketergantungan(akar: Path) -> list[Temuan]:
    lock = akar / "uv.lock"
    disetujui = akar / "ketergantungan-disetujui.toml"

    if not lock.is_file():
        return [Temuan(lock, 0, "uv.lock tidak ditemukan — jalankan `make setup`")]
    if not disetujui.is_file():
        return [
            Temuan(
                disetujui,
                0,
                "ketergantungan-disetujui.toml tidak ditemukan — menghapus "
                "pembandingnya bukan cara sah meloloskan pemeriksa ini",
            )
        ]

    pada_lock = _paket_pada_lock(lock)
    isi_disetujui = tomllib.loads(disetujui.read_text(encoding="utf-8"))
    titik_nol = {_normal(n): str(v) for n, v in isi_disetujui.get("terkunci", {}).items()}

    temuan: list[Temuan] = []

    for nama in sorted(set(pada_lock) - set(titik_nol)):
        temuan.append(
            Temuan(
                lock,
                0,
                f"paket {nama!r} ({pada_lock[nama]}) masuk tanpa persetujuan — "
                "C-12 mensyaratkan persetujuan penanggung jawab teknis sebelum "
                "ketergantungan baru ditambahkan",
            )
        )

    for nama in sorted(set(titik_nol) - set(pada_lock)):
        temuan.append(
            Temuan(
                disetujui,
                0,
                f"paket {nama!r} ada pada titik nol tetapi hilang dari uv.lock — "
                "titik nol tidak lagi menggambarkan keadaan",
            )
        )

    for nama in sorted(set(pada_lock) & set(titik_nol)):
        if pada_lock[nama] != titik_nol[nama]:
            temuan.append(
                Temuan(
                    lock,
                    0,
                    f"versi {nama!r} bergeser tanpa persetujuan: titik nol "
                    f"{titik_nol[nama]} menjadi {pada_lock[nama]} — himpunan nama "
                    "tetap utuh, sehingga pergeseran ini tidak terlihat dari "
                    "daftar paket",
                )
            )

    return temuan
