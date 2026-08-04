"""Aturan tambah-saja pada `logbook/` — R-13.

Dua aturan berbeda, karena dua bahaya berbeda:

**Di dalam `src/logbook/`** tidak boleh ada pembukaan berkas dengan mode
menimpa sama sekali. Penulis satu-satunya tidak boleh dapat memotong; bila ia
bisa, seluruh jaminan tambah-saja bersandar pada kehati-hatian penulisnya.
Aturan ini tidak melihat jalur berkasnya, karena penulis menyusun jalurnya
saat jalan dan jalur itu tidak terbaca dari bentuk kode.

**Di luar `src/logbook/`** tidak boleh ada penulisan ke jalur yang menyebut
`logbook/` dalam bentuk apa pun, **termasuk menambah**. Menambah dari modul
lain tidak merusak baris lama, tetapi ia melewati satu-satunya pintu yang
diuji — dan pintu yang dapat dilewati bukan pintu.

Membaca `logbook/` diizinkan di mana saja.

Batas yang diakui terbuka (RP-05): jalur yang disusun saat jalan di luar
`src/logbook/` tidak terbaca pemeriksa ini, sama seperti RP-01. Kendali
selebihnya bersifat prosedural dan tertulis pada `AGENTS.md` bagian Batas.
"""

from __future__ import annotations

from pathlib import Path

from perkakas.pemeriksa.ast_aturan import (
    MODE_MENIMPA,
    Temuan,
    berkas_python,
    pembukaan_berkas,
)

PENULIS = ("src", "logbook")
DIPERIKSA = ("src", "perkakas")
MODE_MENULIS = MODE_MENIMPA | frozenset({"a", "ab", "a+", "at"})


def _di_dalam_penulis(berkas: Path, akar: Path) -> bool:
    bagian = berkas.relative_to(akar).parts
    return bagian[: len(PENULIS)] == PENULIS


def periksa_logbook_tambah_saja(akar: Path) -> list[Temuan]:
    temuan: list[Temuan] = []

    for cabang in (akar / d for d in DIPERIKSA):
        if not cabang.is_dir():
            continue
        for berkas in berkas_python(cabang):
            di_penulis = _di_dalam_penulis(berkas, akar)

            for baris, jalur, mode in pembukaan_berkas(berkas):
                if di_penulis:
                    if mode in MODE_MENIMPA:
                        temuan.append(
                            Temuan(
                                berkas,
                                baris,
                                f"mode {mode!r} memotong berkas — penulis logbook "
                                "hanya boleh menambah (R-13)",
                            )
                        )
                    continue

                if "logbook" in jalur and mode in MODE_MENULIS:
                    sebutan = "menimpa" if mode in MODE_MENIMPA else "menambah ke"
                    temuan.append(
                        Temuan(
                            berkas,
                            baris,
                            f"{sebutan} {jalur!r} dari luar src/logbook/ — seluruh "
                            "penulisan logbook melewati src/logbook/penulis.py, "
                            "termasuk penambahan",
                        )
                    )

    return temuan
