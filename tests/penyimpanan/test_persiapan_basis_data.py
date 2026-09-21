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

import subprocess
from pathlib import Path

import pytest
from tests.peladen import DIMENSI_UJI, PENGELOLA, psql, wajib_ada

AKAR = Path(__file__).resolve().parents[2]
BERKAS = AKAR / "perkakas" / "basis_data"


def _psql(pengguna: str, basis_data: str, *argumen: str) -> subprocess.CompletedProcess[str]:
    return psql(basis_data, *argumen, pengguna=pengguna)


@pytest.fixture(scope="module")
def basis_data_siap() -> None:
    """Jalankan berkas persiapan dari nol, lalu buat tabel SESUDAHNYA.

    Menggagalkan rangkaian uji bila peladen tidak ada — bukan melewatinya.
    Lihat `tests/peladen.py`.
    """
    wajib_ada()
    _psql(PENGELOLA, "postgres", "-c", "DROP DATABASE IF EXISTS smart_coaching")
    _psql(PENGELOLA, "postgres", "-c", "DROP DATABASE IF EXISTS smart_coaching_pseudonim")
    for peran in ("peran_penjawaban", "peran_verifikasi", "peran_pemanggil_llm", "peran_pseudonim"):
        _psql(PENGELOLA, "postgres", "-c", f"DROP ROLE IF EXISTS {peran}")

    for nama, basis in (
        ("01-peran-dan-basis-data.sql", "postgres"),
        # 01b memasang ekstensi pgvector. Basis datanya baru saja dijatuhkan,
        # sehingga ekstensinya ikut hilang — berkas ini wajib ada pada daftar,
        # dan ketiadaannya sempat terbaca sebagai hak akses yang salah.
        ("01b-ekstensi-vektor.sql", "smart_coaching"),
        ("02-skema-dan-hak.sql", "smart_coaching"),
        ("03-basis-data-pseudonim.sql", "smart_coaching_pseudonim"),
    ):
        hasil = _psql(PENGELOLA, basis, "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / nama))
        assert hasil.returncode == 0, f"{nama} gagal: {hasil.stderr}"

    # Tabel dokumen memakai DDL sungguhan, bukan DDL ringkas buatan uji.
    # DDL buatan uji pernah membuat berkas ini dan rangkaian uji kontrak
    # berebut basis data yang sama dengan bentuk tabel berbeda — dan yang
    # gagal adalah berkas yang kebetulan jalan belakangan.
    hasil = _psql(
        PENGELOLA,
        "smart_coaching",
        "-v",
        "ON_ERROR_STOP=1",
        "-f",
        str(BERKAS / "04-tabel-dokumen.sql"),
    )
    assert hasil.returncode == 0, hasil.stderr

    # Tabel segmen memakai DDL sungguhan `05-kolom-vektor.sql`, bukan DDL
    # ringkas buatan uji — alasan yang sama dengan tabel dokumen di atas.
    hasil = _psql(
        PENGELOLA,
        "smart_coaching",
        "-v",
        "ON_ERROR_STOP=1",
        "-v",
        f"dimensi={DIMENSI_UJI}",
        "-f",
        str(BERKAS / "05-kolom-vektor.sql"),
    )
    assert hasil.returncode == 0, hasil.stderr


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
        "insert into korpus.dokumen_sumber (id, isi) values ('b', '{}'::jsonb)",
        "jalur penjawaban tanpa hak tulis (C-17)",
    ),
]

DIBOLEHKAN = [
    ("peran_penjawaban", "smart_coaching", "select * from korpus.dokumen_sumber"),
    ("peran_pemanggil_llm", "smart_coaching", "select * from indeks_utama.segmen_teks"),
    ("peran_verifikasi", "smart_coaching", "select * from karantina.dokumen_sumber"),
    (
        "peran_verifikasi",
        "smart_coaching",
        "insert into korpus.dokumen_sumber (id, isi) values ('a', '{}'::jsonb)",
    ),
    ("peran_pseudonim", "smart_coaching_pseudonim", "select 1"),
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK)
def test_peladen_menolak(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    """Ditolak **peladen**, bukan ditolak kode. Itu arti 'tidak terjangkau'."""
    assert not _boleh(peran, basis_data, kueri), sebab


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


# ── penjagaan berkas persiapan benar-benar menggagalkan ──────────────


def test_tanpa_dimensi_berkas_kolom_vektor_gagal(basis_data_siap: None) -> None:
    """**Penjagaan yang keluar dengan status 0 bukan penjagaan.**

    `05-kolom-vektor.sql` ditulis pada T-4 dengan `\\quit` sebagai jalur
    gagalnya. `\\quit` mengabaikan argumen statusnya diam-diam dan keluar
    dengan **0**: penyiapan yang tidak membuat satu tabel pun terbaca
    berhasil. Ditemukan pada T-9, dengan mencoba.

    Yang diuji status keluarnya, bukan pesannya — pesan dapat berubah, dan
    yang menentukan bagi pemanggil adalah apakah ia tahu penyiapannya gagal.
    """
    hasil = _psql(PENGELOLA, "smart_coaching", "-f", str(BERKAS / "05-kolom-vektor.sql"))
    assert hasil.returncode != 0, hasil.stdout


def test_tidak_ada_lagi_quit_sebagai_jalur_gagal() -> None:
    """Penjagaan yang sama tidak boleh ditulis ulang dengan bentuk yang sudah
    terbukti bocor.

    Sapuan statis, bukan uji perilaku: ia menjaga berkas persiapan yang belum
    ditulis. Uji perilaku hanya dapat menjaga yang sudah ada, dan bentuk ini
    lolos sekali justru karena tampak benar saat dibaca.
    """
    tersangka = [
        f"{berkas.name}:{nomor}"
        for berkas in sorted(BERKAS.glob("*.sql"))
        for nomor, baris in enumerate(berkas.read_text().splitlines(), start=1)
        if baris.strip().startswith("\\quit") or baris.strip().startswith("\\q ")
    ]
    assert not tersangka, (
        "`\\quit` keluar dengan status 0 dan argumennya diabaikan — pakai "
        f"`RAISE EXCEPTION` di dalam blok DO sebagai jalur gagal: {tersangka}"
    )
