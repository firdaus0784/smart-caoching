"""Pemeriksa penanda placeholder pada bagian Perintah AGENTS.md — R-03.

BACADULU memperingatkan secara khusus:

    Placeholder yang dibiarkan lebih buruk daripada tidak ada bagian itu sama
    sekali — agen akan menjalankannya dan gagal diam-diam.

R-03 mengubah peringatan itu menjadi kegagalan pembangunan. Cakupannya sengaja
dibatasi pada bagian Perintah sesuai bunyi R-03; bagian lain boleh memuat
"TODO" sebagai kata biasa tanpa menggagalkan apa pun.

Dua keadaan selain penanda juga dihitung gagal: bagian Perintah yang hilang,
dan bagian Perintah yang kosong. Keduanya adalah cara meloloskan pemeriksa
tanpa menyelesaikan pekerjaannya.
"""

from __future__ import annotations

import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

JUDUL_BAGIAN = "## Perintah"

PENANDA = (
    re.compile(r"<!--\s*TIM\b", re.IGNORECASE),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bXXX\b"),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"\bisi setelah\b", re.IGNORECASE),
    re.compile(r"\bbelum diisi\b", re.IGNORECASE),
)


def _batas_bagian(baris: list[str]) -> tuple[int, int] | None:
    """Indeks awal dan akhir isi bagian Perintah, atau None bila tidak ada."""
    for i, teks in enumerate(baris):
        if teks.strip() == JUDUL_BAGIAN:
            for j in range(i + 1, len(baris)):
                if baris[j].startswith("## "):
                    return i + 1, j
            return i + 1, len(baris)
    return None


def periksa_placeholder(berkas: Path) -> list[Temuan]:
    if not berkas.is_file():
        return [Temuan(berkas, 0, f"{berkas.name} tidak ditemukan")]

    baris = berkas.read_text(encoding="utf-8").splitlines()
    batas = _batas_bagian(baris)

    if batas is None:
        return [
            Temuan(
                berkas,
                0,
                f"bagian {JUDUL_BAGIAN!r} tidak ditemukan — menghapus bagiannya "
                "bukan cara sah meloloskan pemeriksa ini",
            )
        ]

    awal, akhir = batas
    isi = baris[awal:akhir]

    if not any(t.strip() for t in isi):
        return [
            Temuan(
                berkas,
                awal,
                f"bagian {JUDUL_BAGIAN!r} kosong — agen membaca bagian ini untuk "
                "mengetahui perintah apa yang harus dijalankan",
            )
        ]

    temuan: list[Temuan] = []
    for nomor, teks in enumerate(isi, start=awal + 1):
        for pola in PENANDA:
            if pola.search(teks):
                temuan.append(
                    Temuan(
                        berkas,
                        nomor,
                        f"penanda placeholder {pola.pattern!r} pada bagian "
                        f"{JUDUL_BAGIAN!r}: {teks.strip()!r}",
                    )
                )
                break
    return temuan
