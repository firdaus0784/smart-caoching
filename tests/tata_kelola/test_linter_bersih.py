"""`make lint` tidak boleh hanyut — temuan sesudah fitur 021.

## Mengapa uji ini ada

`make lint` merah **83 temuan** ketika ditemukan pada fitur 021, dan tidak
seorang pun tahu sejak kapan. Sebabnya sederhana dan patut dicatat: ia bukan
bagian `make check`. Gerbang V-01 s.d. V-06 tidak memanggilnya, `AGENTS.md`
menuntut `make check` sebelum tugas dinyatakan selesai, dan linter karena itu
hanya berjalan bila seseorang mengetiknya sendiri.

Ini bentuk kebalikan TA-01. Pelajaran itu berbunyi *"laporan bersih yang tidak
memeriksa apa pun adalah laporan palsu"*; yang terjadi di sini kembarannya —
**laporan yang selalu merah adalah laporan yang berhenti dibaca**. Keduanya
berakhir sama: sebuah gerbang yang tidak menahan apa pun.

## Mengapa berupa uji, bukan gerbang V-07

Menambah gerbang menuntut perubahan `constitution.md` dan `docs/D12.md` — dan
`constitution.md` tidak diubah agen. Uji berjalan di bawah V-01, yang sudah
memanggil seluruh rangkaian uji, sehingga tidak ada daftar gerbang yang
berubah dan linter tetap tidak dapat hanyut. Biayanya diukur sebelum
dituliskan: `ruff` 0,04 detik, `mypy` 0,25 detik.

## Yang diperiksa, dan yang sengaja tidak

Ketiganya persis apa yang `make lint` jalankan — tidak ditulis ulang di sini,
melainkan **dibaca dari `Makefile`**. Daftar perintah yang disalin akan benar
pada hari ia disalin, lalu `Makefile` berubah dan uji ini menjaga perintah
yang tidak lagi dijalankan siapa pun.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[2]
MAKEFILE = AKAR / "Makefile"


def _perintah_lint() -> list[str]:
    """Baris perintah pada sasaran `lint:` — dibaca, bukan disalin.

    Awalan `$(UV)` diganti `uv`; itu satu-satunya penggantian, dan bila
    `Makefile` kelak memakai peubah lain uji ini akan gagal alih-alih diam.
    """
    isi = MAKEFILE.read_text(encoding="utf-8")
    blok = re.search(r"^lint:\n((?:\t.*\n)+)", isi, re.MULTILINE)
    assert blok is not None, "sasaran `lint:` tidak ditemukan pada Makefile"
    return [baris.strip().replace("$(UV)", "uv") for baris in blok.group(1).splitlines()]


def test_sasaran_lint_terbaca_dan_tidak_kosong() -> None:
    """Sasaran yang kosong membuat ketiga uji di bawah lulus tanpa memeriksa
    apa pun — persis bentuk TA-01 yang uji ini ada untuk mencegahnya."""
    perintah = _perintah_lint()
    assert perintah
    assert all(p.startswith("uv run ") for p in perintah), perintah


@pytest.mark.parametrize("nomor", range(3))
def test_setiap_perintah_lint_bersih(nomor: int) -> None:
    """Satu uji per perintah, bukan satu uji bagi ketiganya.

    Digabung, kegagalan `ruff check` menyembunyikan keadaan `mypy` — dan yang
    tersembunyi adalah yang tidak diperbaiki.
    """
    perintah = _perintah_lint()
    if nomor >= len(perintah):
        pytest.skip(f"Makefile hanya memuat {len(perintah)} perintah lint")
    hasil = subprocess.run(
        perintah[nomor].split(),
        cwd=AKAR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert hasil.returncode == 0, (
        f"`{perintah[nomor]}` gagal — `make lint` hanyut lagi.\n"
        f"{hasil.stdout[-2000:]}{hasil.stderr[-2000:]}"
    )


def test_jumlah_perintah_lint_tetap_tiga() -> None:
    """Perintah yang **hilang** dari `Makefile` tidak menggagalkan uji mana pun
    di atas: yang tersisa tetap bersih, dan `pytest.skip` menutupi sisanya.

    Menyebutkan jumlahnya di sini yang membuat penghapusan terlihat. Bila
    `make lint` memang bertambah atau berkurang perintah, angka ini diubah
    dengan sengaja — dan itu bedanya dengan berkurang tanpa seorang pun tahu.
    """
    assert len(_perintah_lint()) == 3
