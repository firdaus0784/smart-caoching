"""Syarat peladen PostgreSQL bagi rangkaian uji — keputusan tim, 12 September 2026.

## Mengapa ketiadaan peladen menjatuhkan gerbang, bukan dilewati

Fitur 024 menghadirkan `PenyimpanPostgres`, dan sebagian sifat yang dijaganya
**tidak dapat ditiru**: penolakan hak akses oleh peladen, keutuhan penulisan
saat sambungan putus, dan pembedaan galat "tidak dapat dihubungi" dari galat
kredensial. Penolakan yang ditiru membuktikan tiruannya menolak.

Selama uji itu boleh dilewati, `make check` pada mesin tanpa PostgreSQL akan
melaporkan **lulus** sambil tidak memeriksa apa pun dari lapisan penyimpanan
sungguhan — dan laporan palsu lebih berbahaya daripada tidak ada laporan,
karena ia menghentikan kewaspadaan. Itu pelajaran TA-01, diterapkan pada syarat
menjalankan gerbang.

Karena itu ketiadaan peladen **menggagalkan** rangkaian uji, dengan pesan yang
menyebut cara memperbaikinya.

## Yang dituntut

Peladen PostgreSQL yang dapat dihubungi, dengan pengguna yang boleh membuat
basis data. Alamatnya dibaca dari `PGHOST`, `PGPORT`, dan `PGUSER`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

BERKAS = Path(__file__).resolve().parents[1] / "perkakas" / "basis_data"

HOST = os.environ.get("PGHOST", "/tmp")
PORT = os.environ.get("PGPORT", "55432")
PENGELOLA = os.environ.get("PGUSER", "pengelola")

PESAN = f"""
Peladen PostgreSQL tidak dapat dihubungi pada {HOST}:{PORT} sebagai {PENGELOLA!r}.

`make check` MENUNTUT peladen sejak keputusan tim 12 September 2026. Uji yang
dilewati karena peladennya tidak ada akan membuat gerbang melaporkan lulus
sambil tidak memeriksa lapisan penyimpanan sungguhan.

Yang perlu dilakukan:
  1. Jalankan PostgreSQL 16 atau lebih baru.
  2. Setel PGHOST, PGPORT, dan PGUSER bila berbeda dari bawaan di atas.
  3. Pengguna itu harus boleh membuat basis data dan peran.

Rinciannya pada `perkakas/basis_data/README.md`.
"""


def psql(
    basis_data: str, *argumen: str, pengguna: str | None = None
) -> subprocess.CompletedProcess[str]:
    """Jalankan `psql` dan kembalikan hasilnya apa adanya."""
    return subprocess.run(
        [
            "psql",
            "-h",
            HOST,
            "-p",
            PORT,
            "-U",
            pengguna or PENGELOLA,
            "-d",
            basis_data,
            "-tAq",
            *argumen,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def tersedia() -> bool:
    """Peladen dapat dihubungi. Tidak melempar — pemanggil yang memutuskan."""
    if shutil.which("psql") is None:
        return False
    return psql("postgres", "-c", "select 1").returncode == 0


def wajib_ada() -> None:
    """Gagalkan rangkaian uji bila peladen tidak ada, dengan cara memperbaikinya."""
    if not tersedia():
        raise RuntimeError(PESAN)


def siapkan() -> None:
    """Jalankan keempat berkas persiapan — aman dipanggil berulang.

    Tiap modul uji memanggilnya sendiri alih-alih mengandalkan modul lain sudah
    menjalankannya. Urutan uji bukan kontrak, dan berkas uji yang bergantung
    pada tetangganya akan gagal pada hari salah satunya dijalankan sendirian.
    """
    wajib_ada()
    for nama, basis in (
        ("01-peran-dan-basis-data.sql", "postgres"),
        ("02-skema-dan-hak.sql", "smart_coaching"),
        ("03-basis-data-pseudonim.sql", "smart_coaching_pseudonim"),
        ("04-tabel-dokumen.sql", "smart_coaching"),
    ):
        hasil = psql(basis, "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / nama))
        if hasil.returncode != 0:
            raise RuntimeError(f"{nama} gagal: {hasil.stderr}")
