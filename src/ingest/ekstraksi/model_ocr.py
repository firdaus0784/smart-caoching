"""Pencarian dan sidik berkas model OCR — R-05, C-09.

Ditempatkan di `src/`, bukan di `perkakas/`, dan arah itu disengaja:
**perkakas boleh bergantung pada kode; kode tidak boleh bergantung pada
perkakas.** Versi pertama `ocr.py` mengimpor pembantu ini dari
`perkakas.pemeriksa`, yang berarti kode produksi tidak dapat dijalankan tanpa
perangkat pemeriksanya — kekeliruan lapisan yang tidak akan terlihat sampai
ada yang memaketkan `src/` sendirian.

Satu tempat, dua pemakai dengan pertanyaan berbeda. `ocr.py` bertanya "model
apa yang saya pakai barusan" untuk dicatat; pemeriksa R-18 bertanya "model apa
yang terpasang" untuk dibandingkan dengan yang disetujui. Menyalinnya menjadi
dua akan menghasilkan aturan kedua yang lupa diperbarui — pelajaran yang sudah
tertangkap sekali pada Fase B fitur 002.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

TEMPAT_BAKU: tuple[str, ...] = (
    "/usr/share/tesseract-ocr/5/tessdata",
    "/usr/share/tesseract-ocr/4.00/tessdata",
    "/usr/share/tessdata",
    "/usr/local/share/tessdata",
)
"""Tempat baku berkas model pada pemasangan lewat pengelola paket sistem."""


def jalur_model(nama_berkas: str) -> Path | None:
    """Jalur berkas model, atau `None` bila tidak ditemukan.

    `TESSDATA_PREFIX` didahulukan karena ia yang dibaca mesinnya sendiri;
    pemeriksa yang melihat tempat lain daripada yang dipakai mesin akan
    melaporkan sidik berkas yang tidak pernah dipakai siapa pun.
    """
    calon: list[Path] = []
    awalan = os.environ.get("TESSDATA_PREFIX")
    if awalan:
        calon += [Path(awalan) / nama_berkas, Path(awalan) / "tessdata" / nama_berkas]
    calon += [Path(tempat) / nama_berkas for tempat in TEMPAT_BAKU]

    for jalur in calon:
        try:
            if jalur.is_file():
                return jalur
        except OSError:
            continue
    return None


def sidik_model(nama_berkas: str) -> str | None:
    """Sidik berkas model, atau `None` bila berkasnya tidak ditemukan.

    Berkas yang tidak dapat dibaca diperlakukan sebagai tidak ada. Pemeriksa
    yang menebak isi berkas yang tidak dapat dibacanya bukan pemeriksa.
    """
    jalur = jalur_model(nama_berkas)
    if jalur is None:
        return None
    try:
        return "sha256:" + hashlib.sha256(jalur.read_bytes()).hexdigest()
    except OSError:
        return None
