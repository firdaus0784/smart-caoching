"""Pemeriksa ketergantungan npm terhadap titik nol — R-19 fitur 027, C-12, KB-123.

Sejajar `ketergantungan.py` bagi Python, dan dengan alasan yang sama: C-12
melarang ketergantungan baru tanpa persetujuan, dan larangan itu tidak dapat
ditegakkan tanpa rekaman pohon paket pada saat disetujui.

Sebelum fitur 027, V-04 **tidak mengenal npm sama sekali**. Paket frontend yang
dipasang akan lolos gerbang tanpa satu baris pun diperiksa — bentuk TA-01 pada
sumbu ketergantungan.

## Kunci pembanding berupa jalur di dalam lock, bukan nama paket

`package-lock.json` dapat memuat satu paket dalam dua versi: satu di puncak
`node_modules/`, satu bersarang di bawah paket yang menuntut versi lain.
Dikunci dengan nama, dua versi itu saling menimpa, dan pergeseran salah
satunya **tidak terlihat**. Dikunci dengan jalur, keduanya dibandingkan sendiri.

## Empat pemeriksaan

- paket langsung pada `package.json` di luar `[npm].langsung` — pintu yang
  paling mungkin dipakai: menambah satu pustaka agar cepat
- paket masuk pada lock di luar `[npm.terkunci]`
- paket hilang dari lock yang ada pada `[npm.terkunci]`
- versi bergeser — himpunan jalur tetap utuh, sehingga pemeriksa yang hanya
  membandingkan nama akan melaporkan bersih
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

AWALAN_LOCK = "node_modules/"


def _jalur_pada_lock(lock: Path) -> dict[str, str]:
    """Jalur paket → versi, tanpa awalan `node_modules/` terdepan."""
    isi = json.loads(lock.read_text(encoding="utf-8"))
    paket: dict[str, str] = {}
    for kunci, butir in isi.get("packages", {}).items():
        if not kunci.startswith(AWALAN_LOCK):
            continue  # kunci "" adalah proyek itu sendiri
        paket[kunci[len(AWALAN_LOCK) :]] = str(butir.get("version", ""))
    return paket


def periksa_ketergantungan_npm(akar: Path) -> list[Temuan]:
    disetujui = akar / "ketergantungan-disetujui.toml"
    paket_json = akar / "web" / "package.json"
    lock = akar / "web" / "package-lock.json"

    if not paket_json.is_file():
        return [
            Temuan(
                paket_json,
                0,
                "web/package.json tidak ditemukan — pemeriksa yang tidak menemukan "
                "bahannya lalu diam adalah laporan palsu",
            )
        ]
    if not lock.is_file():
        return [
            Temuan(
                lock,
                0,
                "web/package-lock.json tidak ditemukan — tanpa kunci, versi yang "
                "terpasang tidak dapat dibandingkan dengan yang disetujui",
            )
        ]

    isi_disetujui = tomllib.loads(disetujui.read_text(encoding="utf-8"))
    npm = isi_disetujui.get("npm")
    if not isinstance(npm, dict):
        return [
            Temuan(
                disetujui,
                0,
                "bagian [npm] tidak ada pada ketergantungan-disetujui.toml — paket "
                "frontend tidak memiliki titik nol untuk dibandingkan",
            )
        ]

    langsung = {str(n) for n in npm.get("langsung", [])}
    titik_nol = {str(j): str(v) for j, v in npm.get("terkunci", {}).items()}
    isi_paket = json.loads(paket_json.read_text(encoding="utf-8"))
    pada_paket = {
        str(n)
        for bagian in (
            "dependencies",
            "devDependencies",
            "optionalDependencies",
            "peerDependencies",
        )
        for n in isi_paket.get(bagian, {})
    }
    pada_lock = _jalur_pada_lock(lock)

    temuan: list[Temuan] = []
    for nama in sorted(pada_paket - langsung):
        temuan.append(
            Temuan(
                paket_json,
                0,
                f"paket {nama!r} ditulis langsung pada package.json tanpa ada pada "
                "`[npm].langsung` — C-12 mensyaratkan persetujuan lebih dulu",
            )
        )
    for jalur in sorted(set(pada_lock) - set(titik_nol)):
        temuan.append(
            Temuan(
                lock,
                0,
                f"paket {jalur!r} ({pada_lock[jalur]}) masuk tanpa persetujuan — "
                "tidak ada pada `[npm.terkunci]`",
            )
        )
    for jalur in sorted(set(titik_nol) - set(pada_lock)):
        temuan.append(
            Temuan(
                disetujui,
                0,
                f"paket {jalur!r} ada pada `[npm.terkunci]` tetapi hilang dari "
                "package-lock.json — titik nol tidak lagi menggambarkan keadaan",
            )
        )
    for nama in sorted(langsung - set(titik_nol)):
        temuan.append(
            Temuan(
                disetujui,
                0,
                f"paket {nama!r} tercatat pada `[npm].langsung` tetapi tidak ada pada "
                "`[npm.terkunci]` — kedua daftar bercerita berbeda",
            )
        )
    if titik_nol and not langsung:
        temuan.append(
            Temuan(
                disetujui,
                0,
                "`[npm].langsung` kosong sementara `[npm.terkunci]` berisi — "
                "mengosongkannya adalah cara termudah meloloskan pemeriksaan paket langsung",
            )
        )
    for jalur in sorted(set(pada_lock) & set(titik_nol)):
        if pada_lock[jalur] != titik_nol[jalur]:
            temuan.append(
                Temuan(
                    lock,
                    0,
                    f"versi {jalur!r} bergeser tanpa persetujuan: titik nol "
                    f"{titik_nol[jalur]} menjadi {pada_lock[jalur]}",
                )
            )
    return temuan
