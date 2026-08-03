"""Keselarasan bagian Perintah AGENTS.md dengan sasaran Makefile — R-03.

Perluasan yang disetujui pada B-4. Menghapus penanda placeholder menyelesaikan
keadaan hari ini; ia tidak mencegah kedua berkas menyimpang enam bulan
kemudian. Penyimpangan itu baru terasa ketika agen menjalankan perintah yang
tidak ada — kegagalan diam-diam yang sama dengan yang diperingatkan BACADULU,
dengan sebab yang berbeda.

Diperiksa dua arah:

- perintah terdokumentasi tanpa sasaran → agen menjalankan sesuatu yang tidak
  ada dan gagal tanpa sebab yang jelas
- sasaran tanpa dokumentasi → agen tidak tahu ia harus dijalankan, sehingga
  gerbang yang sudah dibangun tidak pernah dipakai

Arah kedua sama pentingnya. `make compliance` yang ada tetapi tidak disebut
AGENTS.md adalah gerbang yang tidak menjaga apa pun.
"""

from __future__ import annotations

import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

JUDUL_BAGIAN = "## Perintah"

POLA_PERINTAH = re.compile(r"^\s*make\s+([a-zA-Z][\w-]*)", re.MULTILINE)
POLA_SASARAN = re.compile(r"^([a-zA-Z][\w-]*)\s*:(?!=)", re.MULTILINE)


def _bagian_perintah(agents: Path) -> str:
    baris = agents.read_text(encoding="utf-8").splitlines()
    kumpul: list[str] = []
    di_dalam = False
    for teks in baris:
        if teks.strip() == JUDUL_BAGIAN:
            di_dalam = True
            continue
        if di_dalam and teks.startswith("## "):
            break
        if di_dalam:
            kumpul.append(teks)
    return "\n".join(kumpul)


def periksa_perintah_selaras(akar: Path) -> list[Temuan]:
    agents = akar / "AGENTS.md"
    makefile = akar / "Makefile"

    if not agents.is_file():
        return [Temuan(agents, 0, "AGENTS.md tidak ditemukan")]
    if not makefile.is_file():
        return [Temuan(makefile, 0, "Makefile tidak ditemukan")]

    terdokumentasi = set(POLA_PERINTAH.findall(_bagian_perintah(agents)))
    tersedia = set(POLA_SASARAN.findall(makefile.read_text(encoding="utf-8")))

    temuan: list[Temuan] = []

    for perintah in sorted(terdokumentasi - tersedia):
        temuan.append(
            Temuan(
                agents,
                0,
                f"AGENTS.md mendokumentasikan `make {perintah}` yang tidak ada "
                "sebagai sasaran Makefile — agen akan menjalankannya dan gagal "
                "tanpa sebab yang jelas",
            )
        )

    for sasaran in sorted(tersedia - terdokumentasi):
        temuan.append(
            Temuan(
                makefile,
                0,
                f"sasaran `{sasaran}` ada pada Makefile tetapi tidak disebut "
                "bagian Perintah AGENTS.md — gerbang yang tidak diketahui agen "
                "tidak menjaga apa pun",
            )
        )

    return temuan
