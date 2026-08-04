"""Pembatasan konstruksi `Instruksi` pada satu modul — ADR-13, C-18.

Memisahkan parameter instruksi dan data (R-06) tidak mengikat apa pun bila
pemanggil dapat membentuk `Instruksi` dari teks yang berasal dari luar.
Aturan ini yang membuat C-18 tetap tegak pada pemanggil kesepuluh, bukan hanya
pada pemanggil pertama yang menulisnya dengan hati-hati.

`tests/` dikecualikan dengan sadar: uji wajib dapat menyusun masukan
bermusuhan — itu justru tugasnya, dan uji penanda C-18 tidak dapat ditulis
tanpa itu. Uji tidak ikut disebarkan, sehingga pengecualian ini tidak
melebarkan permukaan serangan.
"""

from __future__ import annotations

from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python, panggilan_nama

NAMA_TIPE = "Instruksi"
MODUL_DIIZINKAN = ("src", "llm", "instruksi.py")
DIPERIKSA = ("src", "perkakas")


def periksa_konstruksi_instruksi(akar: Path) -> list[Temuan]:
    temuan: list[Temuan] = []
    for cabang in (akar / d for d in DIPERIKSA):
        if not cabang.is_dir():
            continue
        for berkas in berkas_python(cabang):
            if berkas.relative_to(akar).parts == MODUL_DIIZINKAN:
                continue
            for baris in panggilan_nama(berkas, NAMA_TIPE):
                temuan.append(
                    Temuan(
                        berkas,
                        baris,
                        f"{NAMA_TIPE} dibentuk di luar src/llm/instruksi.py — "
                        "ADR-13 mengunci pembentukannya pada satu modul yang "
                        "tidak menyusun untai dari masukan luar",
                    )
                )
    return temuan
