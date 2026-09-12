"""Uji berkas persiapan basis data — T-9 fitur 024, C-02, C-03, C-05.

## Golongan uji yang menuntut peladen sungguhan

`plan.md` Bagian 4.2 menetapkan sebagian sifat **tidak dapat ditiru**:
penolakan hak akses oleh peladen adalah salah satunya. Penolakan yang ditiru
membuktikan tiruannya menolak, bukan membuktikan peladennya menolak.

Uji berkas ini karena itu menuntut PostgreSQL yang berjalan. Bila tidak ada, ia
**dilewati dengan sebab tertulis**, bukan didiamkan — rangkaian uji yang diam
ketika tidak menguji apa pun adalah laporan yang keliru (TA-01).

Cara menjalankannya:

    PGHOST=/tmp PGPORT=55432 PGUSER=pengelola uv run pytest tests/penyimpanan/test_persiapan_basis_data.py

## Mengapa tabel sengaja dibuat sesudah hak diberikan

`GRANT ... ON ALL TABLES IN SCHEMA` hanya berlaku bagi tabel yang ada saat
perintah dijalankan. Uji ini membuat tabelnya **sesudah** ketiga berkas
dijalankan, sehingga yang terbukti adalah `ALTER DEFAULT PRIVILEGES` — dan
bukan kebetulan urutan.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[2]
BERKAS = AKAR / "perkakas" / "basis_data"

HOST = os.environ.get("PGHOST", "/tmp")
PORT = os.environ.get("PGPORT", "55432")
PENGELOLA = os.environ.get("PGUSER", "pengelola")


def _psql(pengguna: str, basis_data: str, *argumen: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["psql", "-h", HOST, "-p", PORT, "-U", pengguna, "-d", basis_data, "-tAq", *argumen],
        capture_output=True,
        text=True,
        check=False,
    )


def _ada_peladen() -> bool:
    if shutil.which("psql") is None:
        return False
    return _psql(PENGELOLA, "postgres", "-c", "select 1").returncode == 0


perlu_peladen = pytest.mark.skipif(
    not _ada_peladen(),
    reason=(
        "peladen PostgreSQL tidak dapat dihubungi pada "
        f"{HOST}:{PORT} sebagai {PENGELOLA!r} — uji golongan 4.2 dilewati. "
        "Ini BUKAN kelulusan: penolakan hak akses oleh peladen tidak terbukti."
    ),
)


@pytest.fixture(scope="module")
def basis_data_siap() -> None:
    """Jalankan ketiga berkas dari nol, lalu buat tabel SESUDAHNYA."""
    _psql(PENGELOLA, "postgres", "-c", "DROP DATABASE IF EXISTS smart_coaching")
    _psql(PENGELOLA, "postgres", "-c", "DROP DATABASE IF EXISTS smart_coaching_pseudonim")
    for peran in ("peran_penjawaban", "peran_verifikasi", "peran_pemanggil_llm", "peran_pseudonim"):
        _psql(PENGELOLA, "postgres", "-c", f"DROP ROLE IF EXISTS {peran}")

    for nama, basis in (
        ("01-peran-dan-basis-data.sql", "postgres"),
        ("02-skema-dan-hak.sql", "smart_coaching"),
        ("03-basis-data-pseudonim.sql", "smart_coaching_pseudonim"),
    ):
        hasil = _psql(PENGELOLA, basis, "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / nama))
        assert hasil.returncode == 0, f"{nama} gagal: {hasil.stderr}"

    _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        """
        CREATE TABLE karantina.dokumen_sumber(id text PRIMARY KEY);
        CREATE TABLE korpus.dokumen_sumber(id text PRIMARY KEY);
        CREATE TABLE indeks_utama.segmen_teks(id text PRIMARY KEY);
        CREATE TABLE indeks_metadata.segmen_teks(id text PRIMARY KEY);
    """,
    )


def _boleh(peran: str, basis_data: str, kueri: str) -> bool:
    return _psql(peran, basis_data, "-c", kueri).returncode == 0


DITOLAK = [
    (
        "peran_penjawaban",
        "smart_coaching",
        "select * from karantina.dokumen_sumber",
        "C-03 — jalur penjawaban tidak menjangkau karantina",
    ),
    (
        "peran_penjawaban",
        "smart_coaching_pseudonim",
        "select 1",
        "C-05 — jalur penjawaban tidak menyambung basis data pseudonim",
    ),
    ("peran_pseudonim", "smart_coaching", "select 1", "C-05 arah sebaliknya"),
    (
        "peran_pemanggil_llm",
        "smart_coaching",
        "select * from indeks_metadata.segmen_teks",
        "C-02 — indeks metadata tidak pernah masuk konteks LLM",
    ),
    (
        "peran_penjawaban",
        "smart_coaching",
        "insert into korpus.dokumen_sumber values('b')",
        "jalur penjawaban tanpa hak tulis (C-17)",
    ),
]

DIBOLEHKAN = [
    ("peran_penjawaban", "smart_coaching", "select * from korpus.dokumen_sumber"),
    ("peran_pemanggil_llm", "smart_coaching", "select * from indeks_utama.segmen_teks"),
    ("peran_verifikasi", "smart_coaching", "select * from karantina.dokumen_sumber"),
    ("peran_verifikasi", "smart_coaching", "insert into korpus.dokumen_sumber values('a')"),
    ("peran_pseudonim", "smart_coaching_pseudonim", "select 1"),
]


@perlu_peladen
@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK)
def test_peladen_menolak(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    """Ditolak **peladen**, bukan ditolak kode. Itu arti 'tidak terjangkau'."""
    assert not _boleh(peran, basis_data, kueri), sebab


@perlu_peladen
@pytest.mark.parametrize(("peran", "basis_data", "kueri"), DIBOLEHKAN)
def test_peladen_membolehkan(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str
) -> None:
    """Penjaga atas uji di atasnya: hak yang menolak segalanya juga lulus."""
    assert _boleh(peran, basis_data, kueri)


def test_peran_sql_mencerminkan_kredensial_baku() -> None:
    """Tidak menuntut peladen — membaca kedua berkas dan membandingkannya.

    `kredensial_baku.py` dan berkas SQL adalah dua daftar yang menggambarkan
    hal yang sama. Yang hanyut tidak akan terlihat dari salah satunya.
    """
    sql = (BERKAS / "01-peran-dan-basis-data.sql").read_text(encoding="utf-8")
    baku = (AKAR / "src" / "penyimpanan" / "kredensial_baku.py").read_text(encoding="utf-8")
    for nama in ("penjawaban", "verifikasi", "pemanggil_llm"):
        assert f"peran_{nama}" in sql, f"peran {nama} tidak ada pada berkas SQL"
        assert f'nama="{nama}"' in baku, f"kredensial {nama} tidak ada pada kredensial_baku"


def test_revoke_connect_ada_pada_berkas() -> None:
    """Baris yang paling mudah terlupa, dan tanpanya seluruh berkas sia-sia.

    KB-082: PostgreSQL memberi CONNECT kepada PUBLIC pada setiap basis data
    baru, sehingga dua basis data tidak memisahkan siapa pun tanpa baris ini.
    """
    sql = (BERKAS / "01-peran-dan-basis-data.sql").read_text(encoding="utf-8")
    for basis in ("smart_coaching", "smart_coaching_pseudonim"):
        assert f"REVOKE CONNECT ON DATABASE {basis}" in sql, basis
