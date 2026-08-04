"""Pemeriksa ketiadaan kemampuan bertindak — C-17, FR-F17, `docs/D13.md` KD-09.

C-17 menyebut tiga hal sekaligus, dan ketiganya diperiksa terpisah karena
jalur pelanggarannya berbeda:

1. **tanpa pemanggilan alat** — tidak ada parameter maupun bidang yang dapat
   menyatakan alat, fungsi, atau plugin
2. **tanpa akses tulis dari jalur penjawaban** — `src/rag/`, `src/llm/`, dan
   `src/api/` tidak membuka berkas dengan mode menulis. `src/logbook/`
   dikecualikan: ia bukan jalur penjawaban, dan justru yang C-09 wajibkan
3. **tanpa pengiriman pesan keluar** — tidak ada pustaka surel, cangkang,
   maupun permintaan jaringan keluar pada `src/`

`docs/D13.md` KD-09 menyebut ini kendali paling berdaya dalam dokumen itu.
Penyisipan instruksi berbahaya karena memberi penyerang kemampuan bertindak
melalui sistem; sistem yang hanya dapat berbicara membatasi kerugian maksimal
menjadi satu jawaban keliru kepada satu pengguna — buruk, tetapi dapat
dipulihkan.

BT-57 mensyaratkan D-13 ditinjau ulang bila kemampuan bertindak ditambahkan
pada siklus mendatang. Pemeriksa ini yang membuat penambahan itu tidak dapat
terjadi diam-diam.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import (
    MODE_MENIMPA,
    Temuan,
    berkas_python,
    impor_pada,
    pembukaan_berkas,
)

JALUR_PENJAWABAN = ("src/rag", "src/llm", "src/api", "src/nlp", "src/ingest")

PUSTAKA_KELUAR = frozenset(
    {"smtplib", "subprocess", "telnetlib", "ftplib", "paramiko", "pexpect", "requests", "httpx"}
)

# Dicocokkan pada **komponen** pengenal, bukan sebagai potongan untai.
# "daftar_alat" harus tertangkap, sementara `\balat\b` tidak cocok dengannya
# karena garis bawah termasuk karakter kata. Ditemukan uji tugas ini.
KATA_ALAT = frozenset(
    {"tool", "tools", "alat", "function", "functions", "fungsi", "plugin", "plugins", "agent"}
)
POLA_PEMISAH = re.compile(r"[_\-]|(?<=[a-z0-9])(?=[A-Z])")


def _menyatakan_alat(pengenal: str) -> bool:
    return bool({b.lower() for b in POLA_PEMISAH.split(pengenal) if b} & KATA_ALAT)


MODE_MENULIS = MODE_MENIMPA | frozenset({"a", "ab", "a+", "at"})


def _di_jalur_penjawaban(berkas: Path, akar: Path) -> bool:
    relatif = berkas.relative_to(akar).as_posix()
    return any(relatif.startswith(j + "/") for j in JALUR_PENJAWABAN)


def _pengenal_alat(berkas: Path) -> list[tuple[str, int]]:
    """Parameter fungsi dan bidang kelas yang menyatakan alat."""
    pohon = ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))
    hasil: list[tuple[str, int]] = []
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.arg) and _menyatakan_alat(simpul.arg):
            hasil.append((simpul.arg, simpul.lineno))
        elif (
            isinstance(simpul, ast.AnnAssign)
            and isinstance(simpul.target, ast.Name)
            and _menyatakan_alat(simpul.target.id)
        ):
            hasil.append((simpul.target.id, simpul.lineno))
    return hasil


def periksa_tanpa_kemampuan_bertindak(akar: Path) -> list[Temuan]:
    cabang = akar / "src"
    if not cabang.is_dir():
        return []

    temuan: list[Temuan] = []
    for berkas in berkas_python(cabang):
        for impor in impor_pada(berkas):
            if impor.modul in PUSTAKA_KELUAR:
                temuan.append(
                    Temuan(
                        berkas,
                        impor.baris,
                        f"pustaka {impor.modul!r} memberi sistem kemampuan mengirim "
                        "atau menjalankan sesuatu — C-17 melarangnya, dan D-13 "
                        "KD-09 menyebut ketiadaannya kendali paling berdaya",
                    )
                )

        for nama, baris in _pengenal_alat(berkas):
            temuan.append(
                Temuan(berkas, baris, f"pengenal {nama!r} menyatakan kemampuan alat (C-17)")
            )

        if not _di_jalur_penjawaban(berkas, akar):
            continue
        for baris, jalur, mode in pembukaan_berkas(berkas):
            if mode in MODE_MENULIS:
                temuan.append(
                    Temuan(
                        berkas,
                        baris,
                        f"akses tulis {mode!r} pada {jalur or '<jalur saat jalan>'} dari "
                        "jalur penjawaban — C-17 dan NFR-21",
                    )
                )
    return temuan
