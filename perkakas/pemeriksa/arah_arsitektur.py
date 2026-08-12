"""Pemeriksa arah ketergantungan antarlapisan — V-03, R-14, ADR-10.

Menopang C-03 dan C-08 dari sisi yang tidak mereka jaga sendiri: keduanya
menuntut jalur tunggal — penyimpanan lewat `src/penyimpanan/`, pemanggilan
model lewat `src/llm/` — dan jalur tunggal hanya berarti bila arah impor
antarlapisan dapat dibaca mesin.

**Berkas ini lahir dari dua kekeliruan berturut-turut yang tidak tertangkap
gerbang mana pun.**

Fitur 007 menemukan tepi `rag → nlp` sudah dipakai tanpa pernah dituliskan.
Fitur 008 menemukan tepi `ingest → llm` sudah ada **sejak fitur 002** dengan
cara yang sama. Keduanya ditemukan pembacaan mata, bukan oleh `make check` —
dan keduanya sah setelah ditinjau, yang justru membuat temuannya lebih
mengkhawatirkan: yang lolos bukan pelanggaran melainkan **keputusan
arsitektur yang tidak pernah diambil siapa pun**.

`AGENTS.md` menyatakan mengapa itu penting:

> Tepi itu … dituliskan agar impornya terbaca sebagai rancangan, bukan sebagai
> kebiasaan yang tidak dijelaskan dokumen mana pun.

Aturan yang hanya hidup pada prosa akan dilanggar oleh orang yang tidak
membacanya, dan pelanggarannya tidak menghasilkan galat apa pun — ia
menghasilkan kode yang bekerja.

## Arah dibaca dari `AGENTS.md`, tidak disalin ke sini

Daftar tepi **tidak** ditulis pada berkas ini. Menyalinnya akan membuat dua
tempat yang berbeda ketika salah satunya disunting, dan yang berbeda adalah
yang tidak diperbarui — kalimat yang proyek ini ulang pada tujuh berkas.

Yang dibaca dua bentuk kalimat yang `AGENTS.md` sudah pakai:

- `` `x` boleh memanggil `a`, `b` `` — tepi berarah.
- `` `src/x/` boleh diimpor siapa pun `` dan `` Semua … lewat `src/x/` `` —
  lapisan yang boleh diimpor semua.

**Batas yang diakui terbuka, dan disengaja:** tepi yang ditulis dengan kalimat
di luar kedua bentuk itu tidak terbaca, sehingga impornya dilaporkan sebagai
temuan. Itu bukan kelemahan melainkan tekanan ke arah penulisan yang seragam —
dan temuan palsu di sini murah, sebab pembetulannya satu kalimat pada dokumen
yang memang harus memuatnya.

## Yang tidak diperiksa

Impor **di dalam** satu lapisan. `src/rag/validator/` mengimpor
`src/rag/pengambilan/` bukan urusan aturan arah; `AGENTS.md` mengatur antar
lapisan puncak, bukan susunan di dalamnya.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

_POLA_TEPI = re.compile(r"`(\w+)`\s+boleh\s+memanggil\s+((?:`\w+`[,\s]*)+)")
_POLA_MODUL = re.compile(r"`(\w+)`")
_POLA_TERBUKA = (
    re.compile(r"`src/(\w+)/`\s+boleh\s+diimpor\s+siapa\s+pun"),
    re.compile(r"[Ss]emua\s+[^.\n]*?lewat\s+`src/(\w+)/`"),
)


def _lapisan(berkas: Path, akar: Path) -> str | None:
    """Lapisan puncak sebuah berkas — `src/rag/x/y.py` → `rag`."""
    bagian = berkas.relative_to(akar).parts
    if len(bagian) < 2 or bagian[0] != "src":
        return None
    return bagian[1]


def baca_arah(teks: str) -> tuple[dict[str, frozenset[str]], frozenset[str]]:
    """Baca tepi berarah dan lapisan terbuka dari `AGENTS.md`.

    Mengembalikan pemetaan lapisan → himpunan lapisan yang boleh dipanggilnya,
    beserta himpunan lapisan yang boleh diimpor siapa pun.
    """
    tepi: dict[str, set[str]] = {}
    for asal, sasaran in _POLA_TEPI.findall(teks):
        tepi.setdefault(asal, set()).update(_POLA_MODUL.findall(sasaran))
    terbuka: set[str] = set()
    for pola in _POLA_TERBUKA:
        terbuka.update(pola.findall(teks))
    return {k: frozenset(v) for k, v in tepi.items()}, frozenset(terbuka)


def periksa_arah_arsitektur(akar: Path) -> list[Temuan]:
    """Impor antarlapisan mengikuti arah yang `AGENTS.md` tuliskan."""
    berkas_agen = akar / "AGENTS.md"
    if not berkas_agen.is_file():
        return [
            Temuan(
                berkas_agen,
                0,
                "AGENTS.md tidak ditemukan — menghapus tempat aturan arah dituliskan "
                "bukan cara sah meloloskan pemeriksa ini",
            )
        ]

    tepi, terbuka = baca_arah(berkas_agen.read_text(encoding="utf-8"))
    if not tepi:
        return [
            Temuan(
                berkas_agen,
                0,
                "tidak satu pun tepi arah terbaca pada AGENTS.md — pemeriksa yang "
                "tidak menemukan aturan tidak memeriksa apa pun",
            )
        ]

    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        asal = _lapisan(berkas, akar)
        if asal is None:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if not isinstance(simpul, ast.ImportFrom):
                continue
            bagian = (simpul.module or "").split(".")
            if len(bagian) < 2 or bagian[0] != "src":
                continue
            sasaran = bagian[1]
            if sasaran in (asal, *terbuka):
                continue
            if sasaran in tepi.get(asal, frozenset()):
                continue
            temuan.append(
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"tepi `{asal} → {sasaran}` tidak tertulis pada AGENTS.md — "
                    "impor yang tidak dijelaskan dokumen mana pun adalah keputusan "
                    "arsitektur yang tidak pernah diambil siapa pun",
                )
            )
    return temuan
