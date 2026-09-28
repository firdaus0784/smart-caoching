"""Pohon sintaks `web/` bagi pemeriksa pasal — fitur 027, R-12, R-20.

Satu jalur bagi tiga pemeriksa: C-13 (bahasa antarmuka), C-14 (ruang
lingkup), dan C-15 (nama terlarang). Pengumpulnya `teks_web.mjs`, dengan
pengurai `rolldown` yang dibawa `vite` (KB-130).

## Mengapa modul ini ada

Sampai sesudah T-6 fitur 027, C-14 dan C-15 menyapu `web/` tetapi hanya
**berkas Python** di dalamnya, sehingga seluruh sumber TypeScript lolos tanpa
dibaca — laporan bersih yang tidak memeriksa apa pun (TA-01, KB-133).
Pengumpul yang sudah ada bagi C-13 dipindah ke sini agar ketiganya membaca
pohon yang sama, bukan tiga salinan yang akan berselisih.

Tanpa Node, pengumpulan **gagal** — sejajar V-01: gerbang yang lulus tanpa
melihat `web/` adalah laporan palsu. Pohon tanpa `web/package.json` tidak
diperiksa sama sekali dan tidak menuntut Node.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from perkakas.pemeriksa.ast_aturan import Temuan

PENGUMPUL_WEB = Path(__file__).with_name("teks_web.mjs")

_KELAS_CSS = re.compile(r"[.#](-?[A-Za-z_][\w-]*)")
_KOMENTAR_CSS = re.compile(r"/\*.*?\*/", re.DOTALL)
_PEMILIH_CSS = re.compile(r"([^{}]*)\{")


def _kelas_css(berkas: Path) -> list[tuple[int, str]]:
    """Nama kelas dan id pada **pemilih** saja — bukan warna `#46524c` di isi
    blok. Pemilih boleh membentang beberapa baris sebelum `{`."""
    isi = _KOMENTAR_CSS.sub(
        lambda m: "\n" * m.group().count("\n"), berkas.read_text(encoding="utf-8")
    )
    hasil: list[tuple[int, str]] = []
    for pemilih in _PEMILIH_CSS.finditer(isi):
        for kelas in _KELAS_CSS.finditer(isi, pemilih.start(1), pemilih.end(1)):
            hasil.append((isi.count("\n", 0, kelas.start()) + 1, kelas.group(1)))
    return hasil


class GalatPengumpulWeb(Exception):
    """Pengumpul `web/` tidak dapat dijalankan — gerbang gagal, bukan dilewati."""


def ada_web(akar: Path) -> bool:
    return (akar / "web" / "package.json").is_file()


def kumpulkan_teks_web(akar: Path, *, node: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """Untai `mikrokopi.ts`, teks harfiah `.tsx`, dan pengenal pengikat.

    Terpisah dari pemeriksaannya agar uji dapat membuktikan pengumpulnya
    **menemukan sesuatu**.
    """
    # Absolut: `createRequire` pada pengumpul menolak jalur relatif, dan
    # `make check` memanggil dengan akar relatif (KB-130).
    web = (akar / "web").resolve()
    if not (web / "node_modules").is_dir():
        raise GalatPengumpulWeb("web/node_modules tidak ada — jalankan `make setup`")
    node = node or shutil.which("node")
    if node is None:
        raise GalatPengumpulWeb(
            "node tidak ditemukan — pasang Node.js 22 beserta npm, lalu jalankan `make setup`"
        )
    try:
        hasil = subprocess.run(
            [node, str(PENGUMPUL_WEB), str(web)],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as galat:
        raise GalatPengumpulWeb(f"pengumpul teks web/ tidak dapat dijalankan: {galat}") from galat
    if hasil.returncode != 0:
        # Node menutup galat tak tertangkap dengan baris versinya; baris
        # galatnya sendiri yang berguna bagi pembaca laporan.
        baris = hasil.stderr.strip().splitlines()
        sebab = next((b for b in baris if "Error" in b), (baris or ["tanpa keluaran"])[-1])
        raise GalatPengumpulWeb(f"pengumpul teks web/ berhenti: {sebab}")
    data: dict[str, list[dict[str, Any]]] = json.loads(hasil.stdout)
    return data


def nama_pada_web(akar: Path) -> tuple[list[tuple[Path, int, str]], list[Temuan]]:
    """Seluruh nama yang dapat menjadi fitur di `web/`, beserta tempatnya.

    Tiga sumber: pengenal pengikat TypeScript, nama berkas `web/src` dan
    `web/public`, dan nama kelas atau id pada CSS — papan peringkat yang
    hanya berupa gaya tetap papan peringkat. Nama berkas diwakili batang
    namanya; baris 0.

    Mengembalikan `([], [temuan])` bila pengumpul tidak dapat dijalankan.
    """
    if not ada_web(akar):
        return [], []
    try:
        data = kumpulkan_teks_web(akar)
    except GalatPengumpulWeb as galat:
        return [], [Temuan(akar / "web", 0, str(galat))]

    nama: list[tuple[Path, int, str]] = [
        (Path("web") / p["berkas"], int(p["baris"]), str(p["nama"])) for p in data["pengenal"]
    ]
    for cabang in ("src", "public"):
        akar_cabang = akar / "web" / cabang
        if not akar_cabang.is_dir():
            continue
        for berkas in sorted(akar_cabang.rglob("*")):
            if not berkas.is_file():
                continue
            relatif = berkas.relative_to(akar)
            nama.append((relatif, 0, berkas.name.split(".")[0]))
            if berkas.suffix == ".css":
                nama.extend((relatif, baris, kelas) for baris, kelas in _kelas_css(berkas))
    tak_terurai = [
        Temuan(Path("web") / g["berkas"], 0, f"berkas tidak dapat diurai: {g['pesan']}")
        for g in data["galat_urai"]
    ]
    return nama, tak_terurai
