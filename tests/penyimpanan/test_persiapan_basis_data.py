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
    for peran in (
        "peran_penjawaban",
        "peran_verifikasi",
        "peran_pemanggil_llm",
        "peran_pseudonim",
        "peran_penyematan",
        "peran_riwayat",
        "peran_autentikasi",
        "peran_pengelola_akun",
        "peran_pengguna",
        "peran_kurasi",
        "peran_penayangan",
        "peran_pengisi_antrean",
        "peran_telemetri",
        "peran_penarikan",
        "peran_penarikan_pseudonim",
        "peran_analitik",
        "peran_penilaian",
        "peran_pembaca_sumber",
        "peran_koleksi",
        "peran_ingesti",
        "peran_penarikan_dokumen",
    ):
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

    # Riwayat percakapan (fitur 028) memakai DDL sungguhan `06-riwayat.sql`.
    hasil = _psql(
        PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / "06-riwayat.sql")
    )
    assert hasil.returncode == 0, hasil.stderr

    # Akun dan sesi (fitur 029) memakai DDL sungguhan `07-akun.sql`.
    hasil = _psql(
        PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / "07-akun.sql")
    )
    assert hasil.returncode == 0, hasil.stderr

    # Profil, prioritas, persetujuan (fitur 030) memakai DDL `08-pengguna.sql`.
    hasil = _psql(
        PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / "08-pengguna.sql")
    )
    assert hasil.returncode == 0, hasil.stderr

    # Kurasi dan penemuan (fitur 013) memakai DDL `09-kurasi.sql`.
    hasil = _psql(
        PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / "09-kurasi.sql")
    )
    assert hasil.returncode == 0, hasil.stderr

    # Telemetri (fitur 034) memakai DDL `10-telemetri.sql`.
    hasil = _psql(
        PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / "10-telemetri.sql")
    )
    assert hasil.returncode == 0, hasil.stderr

    # Penarikan data (fitur 033): `11` pada basis data utama, `11b` pada
    # basis data pseudonim — dua peran, dua basis data, tanpa saling menjangkau.
    for nama, basis in (
        ("11-penarikan.sql", "smart_coaching"),
        ("11b-penarikan-pseudonim.sql", "smart_coaching_pseudonim"),
        ("12-analitik.sql", "smart_coaching"),
        ("13-penilaian.sql", "smart_coaching"),
        ("14-sumber-dan-koleksi.sql", "smart_coaching"),
        ("15-ingesti.sql", "smart_coaching"),
    ):
        hasil = _psql(PENGELOLA, basis, "-v", "ON_ERROR_STOP=1", "-f", str(BERKAS / nama))
        assert hasil.returncode == 0, f"{nama} gagal: {hasil.stderr}"


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
    (
        "peran_penjawaban",
        "smart_coaching",
        "update indeks_utama.segmen_teks set vektor_sematan = null where false",
        "C-17 — jalur penjawaban tanpa hak tulis indeks (TK-62)",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "select * from karantina.dokumen_sumber",
        "C-03 — jalur penyematan tidak menjangkau karantina (TK-63)",
    ),
    (
        "peran_penyematan",
        "smart_coaching_pseudonim",
        "select 1",
        "C-05 — jalur penyematan tidak menyambung basis data pseudonim",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "select * from korpus.dokumen_sumber",
        "hak minimum — penyematan membaca teks dari indeks, bukan dari korpus",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "update indeks_utama.segmen_teks set teks = 'x' where false",
        "hak tulis per kolom — penyematan tidak menyunting teks segmen",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "insert into indeks_utama.segmen_teks (id_segmen) values ('x')",
        "penyematan tidak menambah segmen",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "delete from indeks_metadata.segmen_teks where false",
        "penyematan tidak menghapus segmen",
    ),
    (
        "peran_pemanggil_llm",
        "smart_coaching",
        "create table public.titipan (a int)",
        "USAGE pada public tidak disertai CREATE (TK-64)",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "create table public.titipan (a int)",
        "USAGE pada public tidak disertai CREATE (TK-64)",
    ),
    # ── Riwayat percakapan — fitur 028, R-05, R-08, R-12 ────────────────
    # Tambah-saja ditegakkan peladen: peran penulisnya tidak dapat mengubah,
    # menghapus, maupun mengosongkan baris — termasuk memindahkan pemilik.
    *[
        (
            "peran_riwayat",
            "smart_coaching",
            kueri,
            f"R-08 — riwayat tambah-saja ({kueri.split()[0]} {tabel})",
        )
        for tabel in ("riwayat.percakapan", "riwayat.giliran")
        for kueri in (
            f"update {tabel} set id_percakapan = id_percakapan where false",
            f"delete from {tabel} where false",
            f"truncate {tabel}",
        )
    ],
    (
        "peran_riwayat",
        "smart_coaching",
        "update riwayat.percakapan set pemilik = 'lain' where false",
        "R-02 — pemilik percakapan tidak dapat dipindahkan",
    ),
    (
        "peran_riwayat",
        "smart_coaching",
        "create table riwayat.titipan (a int)",
        "peran riwayat tanpa CREATE pada skemanya",
    ),
    (
        "peran_riwayat",
        "smart_coaching",
        "select * from karantina.dokumen_sumber",
        "C-03 — penulis riwayat tidak menjangkau karantina",
    ),
    (
        "peran_riwayat",
        "smart_coaching",
        "select * from korpus.dokumen_sumber",
        "hak minimum — penulis riwayat tidak membaca korpus",
    ),
    (
        "peran_riwayat",
        "smart_coaching_pseudonim",
        "select 1",
        "C-05 — penulis riwayat tidak menyambung basis data pseudonim",
    ),
    (
        "peran_penjawaban",
        "smart_coaching",
        "select * from riwayat.giliran",
        "R-05, R-07 — jalur penjawaban tidak membaca riwayat",
    ),
    (
        "peran_penjawaban",
        "smart_coaching",
        "insert into riwayat.percakapan (id_percakapan, pemilik, dibuat_pada) "
        "values (gen_random_uuid(), 'x', now())",
        "C-17 — jalur penjawaban tanpa hak tulis riwayat",
    ),
    (
        "peran_pemanggil_llm",
        "smart_coaching",
        "select * from riwayat.giliran",
        "hak minimum — riwayat tidak pernah masuk permintaan model",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "select * from riwayat.giliran",
        "hak minimum — penyematan tidak membaca riwayat",
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
    (
        "peran_penyematan",
        "smart_coaching",
        "select id_segmen, teks, lisensi from indeks_utama.segmen_teks",
    ),
    (
        "peran_penyematan",
        "smart_coaching",
        "update indeks_metadata.segmen_teks set vektor_sematan = null, "
        "versi_model_sematan = null where id_segmen = 'tidak-ada'",
    ),
    # TK-64 — tipe `vector` hidup di skema `public`. Tanpa baris-baris ini,
    # pencarian vektor fitur 019 gagal pada peran produksi dengan
    # `type "vector" does not exist`, dan tidak ada uji yang menangkapnya
    # sebab seluruh uji vektor tersambung sebagai pengelola.
    ("peran_penjawaban", "smart_coaching", "select '[1,2]'::vector <=> '[1,3]'::vector"),
    ("peran_pemanggil_llm", "smart_coaching", "select '[1,2]'::vector <=> '[1,3]'::vector"),
    ("peran_penyematan", "smart_coaching", "select '[1,2]'::vector <=> '[1,3]'::vector"),
    # Fitur 028 — peran riwayat **berjalan**, bukan hanya ditolak (TK-64):
    # membuka percakapan, termasuk bentuk `ON CONFLICT DO NOTHING` yang
    # dipakai penyimpan, menambah giliran, lalu membacanya.
    (
        "peran_riwayat",
        "smart_coaching",
        "insert into riwayat.percakapan (id_percakapan, pemilik, dibuat_pada) values "
        "('11111111-1111-4111-8111-111111111111', 'pseudonim-uji', now()) "
        "on conflict (id_percakapan) do nothing; "
        "insert into riwayat.giliran (id_percakapan, pertanyaan, id_pesan, waktu) values "
        "('11111111-1111-4111-8111-111111111111', 'Bagaimana supervisi?', 'pesan-1', now()); "
        "select p.pemilik, g.nomor from riwayat.percakapan p "
        "join riwayat.giliran g using (id_percakapan)",
    ),
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK)
def test_peladen_menolak(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    """Ditolak **peladen**, bukan ditolak kode. Itu arti 'tidak terjangkau'.

    **Sebab penolakannya diperiksa, bukan hanya kejadiannya.** Uji ini semula
    hanya menuntut kode keluar bukan-nol — sehingga peran yang **tidak ada**
    pun tercatat "ditolak", dan uji penolakan bagi peran baru lulus sebelum
    perannya dibuat. Ditemukan saat TK-63 dikerjakan. Bentuk yang sama dengan
    KB-113: gagal karena alasan yang bukan alasannya.
    """
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


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
    import src.penyimpanan.kredensial_baku as baku
    from src.penyimpanan.kredensial import Kredensial

    sql = (BERKAS / "01-peran-dan-basis-data.sql").read_text(encoding="utf-8")

    # Dibaca dari modulnya, bukan daftar yang ditulis tangan. Daftar tangan
    # semula memuat tiga nama, sehingga kredensial keempat `PENYEMATAN`
    # (fitur 026) tidak terlihat sama sekali — dan TK-63 lolos Gerbang 4.
    # Sifat seluruh daftar, bukan kasus yang kebetulan dikenal penulis uji.
    semua = [k for k in vars(baku).values() if isinstance(k, Kredensial)]
    assert len(semua) >= 4, f"kredensial baku terbaca {len(semua)} — pembacaannya rusak"
    tanpa_peran = [k.nama for k in semua if f"peran_{k.nama}" not in sql]
    assert not tanpa_peran, (
        f"kredensial tanpa pasangan peran basis data: {tanpa_peran}. Pemisahannya "
        "dijaga kode saja, bukan peladen"
    )


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


def test_hak_peran_riwayat_persis_baca_dan_tambah(basis_data_siap: None) -> None:
    """R-08, R-12 — himpunan hak dibaca dari katalog, bukan dicoba satu per satu.

    Uji penolakan di atas mencoba `UPDATE`, `DELETE`, dan `TRUNCATE`. Hak lain
    — `TRIGGER`, `REFERENCES` — tidak dicoba di sana, dan pemicu yang dapat
    dipasang peran penulis adalah jalan memutar menuju pengubahan baris.
    """
    hasil = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select table_name || ':' || string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where grantee = 'peran_riwayat' and table_schema = 'riwayat' "
        "group by table_name order by table_name",
    )
    # Fitur 036: `pesan` ditambah saja, tidak dibaca — rute riwayat tidak dapat
    # menayangkan ulang jawaban (C-07), ditegakkan peladen.
    assert hasil.stdout.split() == [
        "giliran:INSERT,SELECT",
        "percakapan:INSERT,SELECT",
        "pesan:INSERT",
    ]
    # Fitur 033: satu-satunya pemegang hapus atas riwayat adalah peran
    # penarikan, yang tidak dipegang layanan aplikasi.
    lain = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where table_schema = 'riwayat' and grantee like 'peran\\_%' "
        "and grantee <> 'peran_riwayat' group by grantee, table_name order by 1",
    )
    assert lain.stdout.split() == [
        "peran_penarikan:giliran:DELETE",
        "peran_penarikan:penilaian:DELETE",
        "peran_penarikan:percakapan:DELETE",
        "peran_penarikan:pesan:DELETE",
        "peran_penilaian:penilaian:INSERT",
    ]


def test_giliran_menolak_pertanyaan_kosong_dan_percakapan_tak_ada(basis_data_siap: None) -> None:
    """Batasan tabel sebagai lapis kedua sesudah model `Giliran`."""
    kosong = _psql(
        "peran_riwayat",
        "smart_coaching",
        "-c",
        "insert into riwayat.giliran (id_percakapan, pertanyaan, id_pesan, waktu) values "
        "('11111111-1111-4111-8111-111111111111', '', 'p', now())",
    )
    assert "violates check constraint" in kosong.stderr
    yatim = _psql(
        "peran_riwayat",
        "smart_coaching",
        "-c",
        "insert into riwayat.giliran (id_percakapan, pertanyaan, id_pesan, waktu) values "
        "('22222222-2222-4222-8222-222222222222', 'x', 'p', now())",
    )
    assert "violates foreign key constraint" in yatim.stderr


def test_skema_public_tidak_memuat_relasi_apa_pun(basis_data_siap: None) -> None:
    """**Penjaga atas hak USAGE pada `public` (TK-64).**

    `USAGE` pada `public` diberikan kepada tiga peran agar tipe dan operator
    `vector` dapat dipakai. Pemberian itu netral terhadap data **hanya
    selama `public` tidak memuat tabel maupun view**. Hari ini jumlahnya nol.
    Tabel yang kelak dibuat di sana akan terjangkau ketiganya tanpa satu baris
    hak pun ditulis — dan uji ini yang membuatnya terlihat pada hari itu.
    """
    hasil = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace "
        "where n.nspname = 'public' and c.relkind in ('r', 'v', 'm', 'p', 'f')",
    )
    assert hasil.stdout.strip() == "0", (
        f"skema public memuat {hasil.stdout.strip()} relasi — hak USAGE pada public "
        "tidak lagi netral terhadap data"
    )


# ── Akun dan sesi — fitur 029, T-2, R-03, R-07, plan Bagian 3.2 ──────────
#
# Layanan aplikasi yang disusupi tidak dapat mengubah sandi maupun menaikkan
# peran siapa pun: bukan karena kodenya tidak menyediakan, melainkan karena
# **peladen** menolaknya. Setiap penolakan menuntut `permission denied` —
# peran yang belum dibuat pun "ditolak", dan uji yang tidak memeriksa sebabnya
# lulus sebelum berkasnya ditulis (KB-098).

_AKUN_CONTOH = (
    "insert into akun.pengguna (id, pseudonim, peran, tanggal_dibuat, turunan_sandi) "
    "values ('ks-901', 'psd_aaaaaaaaaaaaaaaa', 'pengguna', now(), 'scrypt$x')"
)

DITOLAK_AKUN = [
    *[
        ("peran_autentikasi", kueri, sebab)
        for kueri, sebab in (
            (_AKUN_CONTOH, "layanan aplikasi tidak membuat akun (R-01)"),
            (
                "update akun.pengguna set turunan_sandi = 'scrypt$y' where false",
                "layanan aplikasi tidak mengubah sandi",
            ),
            ("update akun.pengguna set peran = 'admin' where false", "tidak menaikkan peran"),
            (
                "update akun.pengguna set status_aktif = true where false",
                "tidak menghidupkan akun yang dinonaktifkan tim",
            ),
            (
                "update akun.pengguna set pseudonim = 'psd_bbbbbbbbbbbbbbbb' where false",
                "pseudonim tidak berpindah (C-05)",
            ),
            ("delete from akun.pengguna where false", "akun tidak dihapus"),
            ("delete from akun.sesi where false", "sesi dicabut, bukan dihapus (R-06)"),
            ("truncate akun.sesi", "sesi tidak dikosongkan"),
            (
                "update akun.sesi set kedaluwarsa_pada = now() where false",
                "masa sesi tidak diperpanjang",
            ),
            ("create table akun.titipan (a int)", "tanpa CREATE pada skema akun"),
        )
    ],
    *[
        ("peran_pengelola_akun", kueri, sebab)
        for kueri, sebab in (
            (
                "update akun.pengguna set peran = 'admin' where false",
                "perkakas tidak menaikkan peran",
            ),
            (
                "update akun.pengguna set pseudonim = 'psd_bbbbbbbbbbbbbbbb' where false",
                "pseudonim tidak berpindah, juga oleh perkakas (C-05)",
            ),
            ("delete from akun.pengguna where false", "perkakas tidak menghapus akun"),
            ("delete from akun.sesi where false", "perkakas mencabut, tidak menghapus"),
            ("select turunan_sandi from akun.pengguna", "perkakas tidak membaca turunan sandi"),
            (
                "insert into akun.sesi (turunan_pengenal) values ('\\x00')",
                "perkakas tidak membuat sesi",
            ),
        )
    ],
    *[
        (peran, kueri, f"skema akun di luar jangkauan {peran}")
        for peran in ("peran_penjawaban", "peran_riwayat", "peran_pemanggil_llm")
        for kueri in ("select * from akun.pengguna", "select * from akun.sesi")
    ],
]


@pytest.mark.parametrize(("peran", "kueri", "sebab"), DITOLAK_AKUN)
def test_peladen_menolak_hak_akun(
    basis_data_siap: None, peran: str, kueri: str, sebab: str
) -> None:
    hasil = _psql(peran, "smart_coaching", "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


@pytest.mark.parametrize("peran", ["peran_autentikasi", "peran_pengelola_akun"])
def test_peran_akun_tidak_menyambung_basis_data_pseudonim(
    basis_data_siap: None, peran: str
) -> None:
    """R-07, C-05, KA-03 — dalam bentuk apa pun yang P-1 putuskan."""
    hasil = _psql(peran, "smart_coaching_pseudonim", "-c", "select 1")
    assert "permission denied" in hasil.stderr, hasil.stderr


def test_peran_akun_berjalan_pada_haknya(basis_data_siap: None) -> None:
    """TK-64: hak yang menolak segalanya juga lulus uji penolakan.

    Tersambung sebagai peran itu sendiri — perkakas membuat akun, layanan
    membaca dan menaikkan penghitung, membuat sesi, menyentuh dan
    mencabutnya; perkakas mengatur ulang sandi dan mencabut sesi akun.
    """
    langkah = [
        ("peran_pengelola_akun", _AKUN_CONTOH),
        (
            "peran_autentikasi",
            "select id, pseudonim, peran, status_aktif, turunan_sandi, gagal_beruntun, "
            "ditahan_sampai from akun.pengguna where id = 'ks-901'",
        ),
        (
            "peran_autentikasi",
            "update akun.pengguna set gagal_beruntun = gagal_beruntun + 1, "
            "ditahan_sampai = null where id = 'ks-901'",
        ),
        (
            "peran_autentikasi",
            "insert into akun.sesi (turunan_pengenal, id_pengguna, dibuat_pada, terakhir_aktif, "
            "kedaluwarsa_pada) values (sha256('pengenal-uji'), 'ks-901', now(), now(), "
            "now() + interval '8 hours')",
        ),
        (
            "peran_autentikasi",
            "update akun.sesi set terakhir_aktif = now() "
            "where turunan_pengenal = sha256('pengenal-uji')",
        ),
        (
            "peran_autentikasi",
            "update akun.sesi set dicabut_pada = now() "
            "where turunan_pengenal = sha256('pengenal-uji') and dicabut_pada is null",
        ),
        (
            "peran_pengelola_akun",
            "update akun.pengguna set turunan_sandi = 'scrypt$baru', gagal_beruntun = 0, "
            "ditahan_sampai = null where id = 'ks-901'",
        ),
        (
            "peran_pengelola_akun",
            "update akun.sesi set dicabut_pada = now() "
            "where id_pengguna = 'ks-901' and dicabut_pada is null",
        ),
        (
            "peran_pengelola_akun",
            "update akun.pengguna set status_aktif = false where id = 'ks-901'",
        ),
    ]
    for peran, kueri in langkah:
        hasil = _psql(peran, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, f"{peran}: {kueri}\n{hasil.stderr}"


def test_hak_peran_akun_persis_menurut_katalog(basis_data_siap: None) -> None:
    """Himpunan hak dibaca dari katalog, bukan dicoba satu per satu.

    Penolakan di atas mencoba hak yang terpikir penulis uji; katalog memuat
    juga yang tidak terpikir — `TRIGGER`, `REFERENCES`, hak kolom yang
    terlampau lebar. Hak tingkat tabel dan hak per kolom dibaca terpisah,
    sebab hak tingkat tabel tampil pula pada setiap kolom.
    """
    tabel = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where table_schema = 'akun' and grantee like 'peran\\_%' "
        "group by grantee, table_name order by 1",
    )
    assert tabel.stdout.split() == [
        "peran_autentikasi:pengguna:SELECT",
        "peran_autentikasi:permintaan_penarikan:INSERT",
        "peran_autentikasi:sesi:INSERT,SELECT",
        "peran_penarikan:pengguna:DELETE",
        "peran_penarikan:sesi:DELETE",
        "peran_pengelola_akun:pengguna:INSERT",
    ]
    kolom = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select a.rolname || ':' || c.relname || ':' || x.privilege_type || ':' "
        "|| string_agg(att.attname, ',' order by att.attname) "
        "from pg_attribute att join pg_class c on c.oid = att.attrelid "
        "join pg_namespace n on n.oid = c.relnamespace and n.nspname = 'akun' "
        "cross join lateral aclexplode(att.attacl) x "
        "join pg_roles a on a.oid = x.grantee "
        "where att.attacl is not null "
        "group by a.rolname, c.relname, x.privilege_type order by 1",
    )
    assert kolom.stdout.split() == [
        "peran_autentikasi:pengguna:UPDATE:ditahan_sampai,gagal_beruntun",
        "peran_autentikasi:permintaan_penarikan:SELECT:dipenuhi_pada,pseudonim",
        "peran_autentikasi:sesi:UPDATE:dicabut_pada,terakhir_aktif",
        "peran_penarikan:pengguna:SELECT:id,pseudonim",
        "peran_penarikan:permintaan_penarikan:SELECT:diminta_pada,dipenuhi_pada,nomor,pseudonim",
        "peran_penarikan:permintaan_penarikan:UPDATE:dipenuhi_pada,jumlah_baris,pseudonim",
        "peran_penarikan:sesi:SELECT:id_pengguna",
        "peran_pengelola_akun:pengguna:SELECT:id,status_aktif",
        "peran_pengelola_akun:pengguna:UPDATE:ditahan_sampai,gagal_beruntun,status_aktif,turunan_sandi",
        "peran_pengelola_akun:sesi:SELECT:dicabut_pada,id_pengguna",
        "peran_pengelola_akun:sesi:UPDATE:dicabut_pada",
    ]


def test_batasan_tabel_akun(basis_data_siap: None) -> None:
    """Lapis kedua sesudah perkakas: pola nama, pseudonim, dan peran."""
    for nilai, sebab in (
        ("('Budi Santoso', 'psd_cccccccccccccccc', 'pengguna')", "nama orang sebagai id"),
        ("('ks-902', '3201010101010001', 'pengguna')", "NIK sebagai pseudonim"),
        (
            "('ks-904', 'psd_0123456789abcdef', 'pengguna')",
            "pseudonim berderet angka — pendeteksi data pribadi membacanya rekening (KB-158)",
        ),
        ("('ks-903', 'psd_dddddddddddddddd', 'kepala')", "peran di luar D-14"),
    ):
        hasil = _psql(
            "peran_pengelola_akun",
            "smart_coaching",
            "-c",
            "insert into akun.pengguna (id, pseudonim, peran, tanggal_dibuat, turunan_sandi) "
            f"values {nilai[:-1]}, now(), 'scrypt$x')",
        )
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"


# ── Profil, prioritas, persetujuan — fitur 030, T-2, R-02, K-2, K-3 ──────
#
# Profil tidak dapat dipindahkan ke pengguna lain, riwayat prioritas tidak
# dapat diubah, dan catatan persetujuan tidak dapat disunting kecuali
# pencabutannya — ditolak **peladen**, dengan sebab `permission denied`.

_PSD = "psd_aaaaaaaaaaaaaaaa"
_PROFIL = (
    "insert into pengguna.profil_sekolah (id_pengguna, jabatan, masa_kerja, jumlah_rombel, "
    "jumlah_ptk, jalur_akreditasi, wilayah) values "
    f"('{_PSD}', 'Kepala Sekolah', 3, 6, 9, 'visitasi', 'Sumedang') "
    "on conflict (id_pengguna) do update set jabatan = excluded.jabatan"
)

DITOLAK_PENGGUNA = [
    *[
        ("peran_pengguna", "smart_coaching", kueri, sebab)
        for kueri, sebab in (
            (
                "update pengguna.profil_sekolah set id_pengguna = 'psd_bbbbbbbbbbbbbbbb' where false",
                "profil tidak berpindah pengguna (C-05)",
            ),
            ("delete from pengguna.profil_sekolah where false", "profil tidak dihapus"),
            (
                "update pengguna.prioritas_manajerial set kategori = '{K1,K2,K3}' where false",
                "riwayat prioritas tidak diubah (K-3)",
            ),
            (
                "delete from pengguna.prioritas_manajerial where false",
                "riwayat prioritas tidak dihapus",
            ),
            (
                "update pengguna.persetujuan set disetujui = true where false",
                "apa yang disetujui tidak diubah",
            ),
            (
                "update pengguna.persetujuan set versi_naskah = 'lain' where false",
                "versi naskah tidak diubah",
            ),
            (
                "update pengguna.persetujuan set tanggal = now() where false",
                "waktu persetujuan tidak diubah",
            ),
            ("delete from pengguna.persetujuan where false", "persetujuan tidak dihapus"),
            ("truncate pengguna.persetujuan", "persetujuan tidak dikosongkan"),
            ("create table pengguna.titipan (a int)", "tanpa CREATE pada skema pengguna"),
            ("select * from akun.pengguna", "penulis profil tidak membaca akun"),
            ("select * from riwayat.giliran", "penulis profil tidak membaca riwayat"),
            ("select * from karantina.dokumen_sumber", "C-03 — tidak menjangkau karantina"),
        )
    ],
    ("peran_pengguna", "smart_coaching_pseudonim", "select 1", "C-05 — tanpa basis data pseudonim"),
    *[
        (
            peran,
            "smart_coaching",
            "select * from pengguna.persetujuan",
            f"skema pengguna di luar {peran}",
        )
        for peran in (
            "peran_penjawaban",
            "peran_pemanggil_llm",
            "peran_autentikasi",
            "peran_riwayat",
        )
    ],
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_PENGGUNA)
def test_peladen_menolak_hak_pengguna(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def test_peran_pengguna_berjalan_pada_haknya(basis_data_siap: None) -> None:
    """TK-64: tersambung sebagai `peran_pengguna` sendiri."""
    langkah = [
        _PROFIL,
        "update pengguna.profil_sekolah set wilayah = 'Bandung', tanggal_perbarui = now() "
        f"where id_pengguna = '{_PSD}'",
        "insert into pengguna.prioritas_manajerial (id_pengguna, kategori, ditetapkan_pada) "
        f"values ('{_PSD}', '{{K5,K1,K7}}', now())",
        "insert into pengguna.persetujuan (id_pengguna, jenis, versi_naskah, disetujui, tanggal) "
        f"values ('{_PSD}', 'penelitian', 'et02-v1', true, now() - interval '1 minute')",
        "update pengguna.persetujuan set dicabut_pada = now() "
        f"where id_pengguna = '{_PSD}' and dicabut_pada is null and disetujui",
        "select p.jabatan, r.kategori, s.dicabut_pada from pengguna.profil_sekolah p "
        "join pengguna.prioritas_manajerial r using (id_pengguna) "
        "join pengguna.persetujuan s using (id_pengguna)",
    ]
    for kueri in langkah:
        hasil = _psql("peran_pengguna", "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, f"{kueri}\n{hasil.stderr}"


def test_hak_peran_pengguna_persis_menurut_katalog(basis_data_siap: None) -> None:
    tabel = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where table_schema = 'pengguna' and grantee like 'peran\\_%' "
        "group by grantee, table_name order by 1",
    )
    assert tabel.stdout.split() == [
        "peran_penarikan:persetujuan:DELETE",
        "peran_penarikan:prioritas_manajerial:DELETE",
        "peran_penarikan:profil_sekolah:DELETE",
        "peran_pengguna:persetujuan:INSERT,SELECT",
        "peran_pengguna:prioritas_manajerial:INSERT,SELECT",
        "peran_pengguna:profil_sekolah:INSERT,SELECT",
    ]
    kolom = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select a.rolname || ':' || c.relname || ':' || x.privilege_type || ':' "
        "|| string_agg(att.attname, ',' order by att.attname) "
        "from pg_attribute att join pg_class c on c.oid = att.attrelid "
        "join pg_namespace n on n.oid = c.relnamespace and n.nspname = 'pengguna' "
        "cross join lateral aclexplode(att.attacl) x "
        "join pg_roles a on a.oid = x.grantee "
        "where att.attacl is not null "
        "group by a.rolname, c.relname, x.privilege_type order by 1",
    )
    assert kolom.stdout.split() == [
        "peran_penarikan:persetujuan:SELECT:id_pengguna",
        "peran_penarikan:prioritas_manajerial:SELECT:id_pengguna",
        "peran_penarikan:profil_sekolah:SELECT:id_pengguna",
        "peran_pengguna:persetujuan:UPDATE:dicabut_pada",
        "peran_pengguna:profil_sekolah:UPDATE:jabatan,jalur_akreditasi,jumlah_ptk,"
        "jumlah_rombel,masa_kerja,tanggal_perbarui,wilayah",
    ]


def test_batasan_tabel_pengguna(basis_data_siap: None) -> None:
    """Lapis kedua sesudah model fitur 022."""
    for kueri, sebab in (
        (
            "insert into pengguna.profil_sekolah (id_pengguna, jabatan, masa_kerja, jumlah_rombel, "
            "jumlah_ptk, jalur_akreditasi, wilayah) values "
            "('ks-017', 'Kepala', 1, 1, 1, 'visitasi', 'X')",
            "nama akun, bukan pseudonim, sebagai pemilik (C-05)",
        ),
        (
            "insert into pengguna.prioritas_manajerial (id_pengguna, kategori, ditetapkan_pada) "
            f"values ('{_PSD}', '{{K1,K2}}', now())",
            "dua prioritas (FR-A03)",
        ),
        (
            "insert into pengguna.prioritas_manajerial (id_pengguna, kategori, ditetapkan_pada) "
            f"values ('{_PSD}', '{{K1,K2,K9}}', now())",
            "kategori di luar K1-K8",
        ),
        (
            "insert into pengguna.persetujuan (id_pengguna, jenis, versi_naskah, disetujui, tanggal) "
            f"values ('{_PSD}', 'penelitian', ' ', true, now())",
            "versi naskah kosong (R-04)",
        ),
        (
            "insert into pengguna.persetujuan (id_pengguna, jenis, versi_naskah, disetujui, tanggal, "
            f"dicabut_pada) values ('{_PSD}', 'penelitian', 'v', false, now(), now())",
            "penolakan yang dicabut",
        ),
    ):
        hasil = _psql("peran_pengguna", "smart_coaching", "-c", kueri)
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"


# ── Fitur 013 · kurasi dan penemuan ───────────────────────────────────
#
# Tiga peran, satu batas tiap peran (plan Bagian 2.2). Yang menayangkan tidak
# membaca antrean (C-06); yang memutus tidak menambah kandidat (FR-I07); yang
# mengisi antrean tidak menayangkan. Ditolak **peladen**, sebab
# `permission denied`.

_PSD_KURATOR = "psd_kkkkkkkkkkkkkkkk"
_BUTIR = '{"id_butir": "b-uji"}'
_SUMBER = '{"judul": "Sumber", "penerbit": "Penerbit", "tahun": 2025, "tautan": null}'

DITOLAK_KURASI = [
    *[
        ("peran_penayangan", "smart_coaching", kueri, sebab)
        for kueri, sebab in (
            ("select * from kurasi.kandidat", "C-06 — penayang tidak membaca antrean"),
            ("select * from kurasi.putusan", "penayang tidak membaca putusan utuh"),
            (
                "select pseudonim_kurator from kurasi.putusan",
                "C-05 — penayang tidak membaca pemutus",
            ),
            ("select alasan from kurasi.putusan", "penayang tidak membaca alasan putusan"),
            ("select * from kurasi.penarikan", "penayang tidak membaca penarikan"),
            (
                "insert into kurasi.butir_tayang (id_butir) values ('x')",
                "C-06 — penayang tidak menulis butir tayang",
            ),
            (
                "update kurasi.butir_tayang set ditarik_pada = null where false",
                "penayang tidak menarik butir",
            ),
            ("delete from penemuan.tayang_harian where false", "butir hari ini tidak dihapus"),
            (
                "update penemuan.tayang_harian set tanggal = current_date where false",
                "butir hari ini tidak diubah",
            ),
            ("delete from penemuan.belum_relevan where false", "umpan balik tidak dihapus"),
            ("select * from pengguna.profil_sekolah", "penayang tidak membaca profil"),
            ("select * from korpus.dokumen_sumber", "K-3 — penayang tidak membaca korpus"),
            ("select * from karantina.dokumen_sumber", "C-03 — tidak menjangkau karantina"),
        )
    ],
    *[
        ("peran_kurasi", "smart_coaching", kueri, sebab)
        for kueri, sebab in (
            (
                "insert into kurasi.kandidat (id_butir) values ('x')",
                "FR-I07 — kandidat tidak ditambahkan dari layar kurator",
            ),
            (
                "update kurasi.kandidat set butir = '{}' where false",
                "isi kandidat tidak diubah kurator",
            ),
            (
                "update kurasi.kandidat set status_keberlakuan = 'berlaku' where false",
                "C-07 — kurator tidak mengubah status regulasi",
            ),
            ("update kurasi.putusan set jenis = 'tolak' where false", "putusan tidak disunting"),
            ("delete from kurasi.putusan where false", "putusan tidak dihapus"),
            ("delete from kurasi.penarikan where false", "penarikan tidak dihapus"),
            (
                "update kurasi.butir_tayang set butir = '{}' where false",
                "butir tayang tidak disunting sesudah tayang",
            ),
            ("delete from kurasi.butir_tayang where false", "butir tayang tidak dihapus"),
            ("truncate kurasi.putusan", "putusan tidak dikosongkan"),
            ("select * from penemuan.tayang_harian", "kurator tidak membaca perilaku pengguna"),
            ("select * from karantina.dokumen_sumber", "C-03 — tidak menjangkau karantina"),
            ("select * from korpus.dokumen_sumber", "kurator tidak membaca teks korpus"),
            ("create table kurasi.titipan (a int)", "tanpa CREATE pada skema kurasi"),
        )
    ],
    *[
        ("peran_pengisi_antrean", "smart_coaching", kueri, sebab)
        for kueri, sebab in (
            (
                "insert into kurasi.butir_tayang (id_butir) values ('x')",
                "C-06 — pengisi antrean tidak menayangkan",
            ),
            (
                "insert into kurasi.putusan (id_butir) values ('x')",
                "pengisi antrean tidak memutus",
            ),
            (
                "update kurasi.kandidat set butir = '{}' where false",
                "isi kandidat tidak diubah sesudah masuk",
            ),
            ("delete from kurasi.kandidat where false", "kandidat tidak dihapus"),
            ("select * from penemuan.tayang_harian", "pengisi tidak membaca perilaku"),
            ("select * from karantina.dokumen_sumber", "C-03 — tidak menjangkau karantina"),
        )
    ],
    *[
        (
            peran,
            "smart_coaching_pseudonim",
            "select 1",
            f"C-05 — {peran} tanpa basis data pseudonim",
        )
        for peran in ("peran_kurasi", "peran_penayangan", "peran_pengisi_antrean")
    ],
    *[
        (
            peran,
            "smart_coaching",
            "select * from kurasi.butir_tayang",
            f"skema kurasi di luar {peran}",
        )
        for peran in ("peran_penjawaban", "peran_pengguna", "peran_riwayat", "peran_autentikasi")
    ],
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_KURASI)
def test_peladen_menolak_hak_kurasi(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def _kandidat(id_butir: str, dokumen: str = "dok-1") -> str:
    return (
        "insert into kurasi.kandidat (id_butir, butir, sumber, id_dokumen_sumber, kategori, "
        f"status_keberlakuan, masuk_pada) values ('{id_butir}', '{_BUTIR}', '{_SUMBER}', "
        f"'{dokumen}', 'K5', 'berlaku', now())"
    )


def _putusan(id_butir: str, jenis: str, alasan: str = "Layak tayang") -> str:
    return (
        "insert into kurasi.putusan (id_butir, jenis, peran, pseudonim_kurator, alasan, waktu) "
        f"values ('{id_butir}', '{jenis}', 'kurator', '{_PSD_KURATOR}', '{alasan}', now())"
    )


def _tayang(id_butir: str) -> str:
    return (
        "insert into kurasi.butir_tayang (id_butir, butir, sumber, id_dokumen_sumber, kategori, "
        "status_keberlakuan, nomor_putusan, tayang_pada) "
        f"select '{id_butir}', '{_BUTIR}', '{_SUMBER}', 'dok-1', 'K5', 'berlaku', nomor, now() "
        f"from kurasi.putusan where id_butir = '{id_butir}' order by nomor desc limit 1"
    )


def _jalan(peran: str, kueri: str) -> None:
    hasil = _psql(peran, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
    assert hasil.returncode == 0, f"{peran}: {kueri}\n{hasil.stderr}"


def test_peran_kurasi_berjalan_pada_haknya(basis_data_siap: None) -> None:
    """TK-64: tiap peran tersambung sendiri dan menjalankan pekerjaannya."""
    _jalan("peran_pengisi_antrean", _kandidat("b-jalan"))
    _jalan(
        "peran_pengisi_antrean",
        "update kurasi.kandidat set status_keberlakuan = 'berlaku' where id_dokumen_sumber = 'dok-1'",
    )
    _jalan("peran_kurasi", "select * from kurasi.kandidat")
    _jalan("peran_kurasi", "update kurasi.kandidat set kembali_pada = null where false")
    _jalan("peran_kurasi", _putusan("b-jalan", "setujui"))
    _jalan("peran_kurasi", _tayang("b-jalan"))
    _jalan(
        "peran_kurasi",
        "update kurasi.butir_tayang set perlu_tinjauan_pada = now() where id_butir = 'b-jalan'",
    )
    _jalan("peran_penayangan", "select * from kurasi.butir_tayang")
    _jalan(
        "peran_penayangan",
        "select b.id_butir, p.jenis, p.peran, p.waktu from kurasi.butir_tayang b "
        "join kurasi.putusan p on p.nomor = b.nomor_putusan",
    )
    _jalan(
        "peran_penayangan",
        "insert into penemuan.tayang_harian (id_pengguna, tanggal, id_butir, urutan, "
        f"ditayangkan_pada) values ('{_PSD}', current_date, 'b-jalan', 1, now())",
    )
    _jalan(
        "peran_penayangan",
        "insert into penemuan.belum_relevan (id_pengguna, id_butir, alasan, waktu) "
        f"values ('{_PSD}', 'b-jalan', 'Belum menjadi prioritas semester ini', now())",
    )
    _jalan("peran_penayangan", "select * from penemuan.tayang_harian")
    _jalan(
        "peran_kurasi",
        "insert into kurasi.penarikan (id_butir, pemicu, tindakan, peran, pseudonim_kurator, "
        f"alasan, waktu) values ('b-jalan', 'kekeliruan_isi_dilaporkan', 'ditarik', 'kurator', "
        f"'{_PSD_KURATOR}', 'Angka keliru', now())",
    )
    _jalan(
        "peran_pengisi_antrean",
        "insert into kurasi.penarikan (id_butir, pemicu, tindakan, alasan, waktu) values "
        "('b-jalan', 'regulasi_sumber_berubah', 'ditarik', 'Regulasi dicabut', now())",
    )
    _jalan(
        "peran_pengisi_antrean",
        "update kurasi.butir_tayang set ditarik_pada = now(), alasan_tarik = 'dicabut', "
        "status_keberlakuan = 'dicabut' where id_butir = 'b-jalan'",
    )


def test_hak_peran_kurasi_persis_menurut_katalog(basis_data_siap: None) -> None:
    tabel = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_schema || '.' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where table_schema in ('kurasi', 'penemuan') and grantee like 'peran\\_%' "
        "group by grantee, table_schema, table_name order by 1",
    )
    assert tabel.stdout.split() == [
        # Fitur 032: koleksi milik perannya sendiri. Penayang tidak tercantum
        # di sini — pemilihan beranda tidak membaca koleksi (R-03, M-3).
        "peran_koleksi:penemuan.koleksi:DELETE,INSERT,SELECT",
        "peran_kurasi:kurasi.aduan_digantikan:SELECT",
        "peran_kurasi:kurasi.butir_tayang:INSERT,SELECT",
        "peran_kurasi:kurasi.kandidat:SELECT",
        "peran_kurasi:kurasi.penarikan:INSERT,SELECT",
        "peran_kurasi:kurasi.putusan:INSERT,SELECT",
        "peran_kurasi:kurasi.tindak_lanjut_aduan:INSERT,SELECT",
        "peran_penarikan:kurasi.aduan:DELETE",
        "peran_penarikan:kurasi.aduan_digantikan:DELETE",
        "peran_penarikan:kurasi.tindak_lanjut_aduan:DELETE",
        "peran_penarikan:penemuan.belum_relevan:DELETE",
        "peran_penarikan:penemuan.koleksi:DELETE",
        "peran_penarikan:penemuan.tayang_harian:DELETE",
        "peran_penayangan:kurasi.butir_tayang:SELECT",
        "peran_penayangan:penemuan.belum_relevan:INSERT,SELECT",
        "peran_penayangan:penemuan.tayang_harian:INSERT,SELECT",
        "peran_pengisi_antrean:kurasi.butir_tayang:SELECT",
        "peran_pengisi_antrean:kurasi.kandidat:INSERT,SELECT",
        "peran_pengisi_antrean:kurasi.penarikan:INSERT",
        "peran_penilaian:kurasi.aduan:INSERT",
        "peran_penilaian:kurasi.aduan_digantikan:INSERT",
    ]
    kolom = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select a.rolname || ':' || c.relname || ':' || x.privilege_type || ':' "
        "|| string_agg(att.attname, ',' order by att.attname) "
        "from pg_attribute att join pg_class c on c.oid = att.attrelid "
        "join pg_namespace n on n.oid = c.relnamespace and n.nspname in ('kurasi', 'penemuan') "
        "cross join lateral aclexplode(att.attacl) x "
        "join pg_roles a on a.oid = x.grantee "
        "where att.attacl is not null "
        "group by a.rolname, c.relname, x.privilege_type order by 1",
    )
    assert kolom.stdout.split() == [
        "peran_koleksi:koleksi:UPDATE:catatan,disimpan_pada",
        # Fitur 036: kurator membaca salinan aduan tanpa tautannya ke penilaian.
        "peran_kurasi:aduan:SELECT:alasan,diadukan_pada,nomor,pertanyaan,tanggapan",
        "peran_kurasi:butir_tayang:UPDATE:alasan_tarik,ditarik_pada,perlu_tinjauan_pada",
        "peran_kurasi:kandidat:UPDATE:kembali_pada",
        "peran_penarikan:aduan:SELECT:nomor,nomor_penilaian",
        "peran_penarikan:aduan_digantikan:SELECT:nomor_aduan",
        "peran_penarikan:belum_relevan:SELECT:id_pengguna",
        "peran_penarikan:koleksi:SELECT:id_pengguna",
        "peran_penarikan:tayang_harian:SELECT:id_pengguna",
        "peran_penarikan:tindak_lanjut_aduan:SELECT:nomor_aduan",
        "peran_penayangan:putusan:SELECT:id_butir,jenis,menyetujui,nomor,peran,waktu",
        "peran_pengisi_antrean:butir_tayang:UPDATE:alasan_tarik,ditarik_pada,status_keberlakuan",
        "peran_pengisi_antrean:kandidat:UPDATE:status_keberlakuan",
        "peran_penilaian:aduan:SELECT:nomor,nomor_penilaian",
    ]


def test_batasan_tabel_kurasi(basis_data_siap: None) -> None:
    """Lapis kedua sesudah model fitur 010 — terutama C-06 pada peladen:
    butir tayang hanya dapat merujuk putusan yang **menyetujui** butir itu."""
    _jalan("peran_pengisi_antrean", _kandidat("b-tolak"))
    _jalan("peran_pengisi_antrean", _kandidat("b-dua"))
    _jalan("peran_kurasi", _putusan("b-tolak", "tolak", "TL-01"))
    _jalan("peran_kurasi", _putusan("b-dua", "setujui"))
    for peran, kueri, pesan, sebab in (
        (
            "peran_kurasi",
            _tayang("b-tolak"),
            "violates foreign key constraint",
            "C-06 — butir tayang berdasar putusan tolak",
        ),
        (
            "peran_kurasi",
            "insert into kurasi.butir_tayang (id_butir, butir, sumber, id_dokumen_sumber, kategori, "
            "status_keberlakuan, nomor_putusan, tayang_pada) select 'b-tolak', butir, sumber, "
            "id_dokumen_sumber, kategori, status_keberlakuan, nomor_putusan, now() "
            "from kurasi.butir_tayang where false union all select 'b-tolak', '{}', '{}', 'dok-1', "
            "'K5', null, nomor, now() from kurasi.putusan where id_butir = 'b-dua'",
            "violates foreign key constraint",
            "C-06 — putusan butir lain",
        ),
        (
            "peran_kurasi",
            _putusan("b-dua", "tolak", "TL-02"),
            "duplicate key",
            "satu putusan akhir per butir",
        ),
        (
            "peran_kurasi",
            "insert into kurasi.putusan (id_butir, jenis, peran, pseudonim_kurator, alasan, waktu) "
            "values ('b-dua', 'tunda', 'kurator', 'ks-017', 'Nanti', now())",
            "violates check constraint",
            "C-05 — nama akun sebagai pemutus",
        ),
        (
            "peran_kurasi",
            "insert into kurasi.putusan (id_butir, jenis, peran, pseudonim_kurator, alasan, waktu) "
            f"values ('b-dua', 'tarik', 'kurator', '{_PSD_KURATOR}', 'x', now())",
            "violates check constraint",
            "empat jenis putusan, bukan lima",
        ),
        (
            "peran_pengisi_antrean",
            "insert into kurasi.penarikan (id_butir, pemicu, tindakan, alasan, waktu) values "
            "('b-dua', 'kekeliruan_isi_dilaporkan', 'ditarik', 'x', now())",
            "violates check constraint",
            "penarikan tanpa pemutus hanya bagi regulasi",
        ),
        (
            "peran_pengisi_antrean",
            "insert into kurasi.kandidat (id_butir, butir, sumber, id_dokumen_sumber, kategori, "
            f"status_keberlakuan, masuk_pada) values ('b-k9', '{_BUTIR}', '{_SUMBER}', 'd', 'K9', "
            "null, now())",
            "violates check constraint",
            "kategori di luar K1-K8",
        ),
        (
            "peran_penayangan",
            "insert into penemuan.tayang_harian (id_pengguna, tanggal, id_butir, urutan, "
            "ditayangkan_pada) values ('ks-017', current_date, 'b-dua', 1, now())",
            "violates check constraint",
            "C-05 — nama akun sebagai pemilik",
        ),
        (
            "peran_penayangan",
            "insert into penemuan.belum_relevan (id_pengguna, id_butir, alasan, waktu) "
            f"values ('{_PSD}', 'b-dua', ' ', now())",
            "violates check constraint",
            "alasan kosong (FR-G07)",
        ),
    ):
        hasil = _psql(peran, "smart_coaching", "-c", kueri)
        assert pesan in hasil.stderr, f"{sebab}: {hasil.stderr}"


def test_butir_tayang_sekali_bagi_orang_yang_sama(basis_data_siap: None) -> None:
    """K-2: kunci utama menolak butir yang sama tayang dua kali bagi satu orang."""
    _jalan("peran_pengisi_antrean", _kandidat("b-sekali"))
    _jalan("peran_kurasi", _putusan("b-sekali", "setujui"))
    _jalan("peran_kurasi", _tayang("b-sekali"))
    sisip = (
        "insert into penemuan.tayang_harian (id_pengguna, tanggal, id_butir, urutan, "
        f"ditayangkan_pada) values ('{_PSD}', current_date + %d, 'b-sekali', 1, now())"
    )
    _jalan("peran_penayangan", sisip % 0)
    hasil = _psql("peran_penayangan", "smart_coaching", "-c", sisip % 1)
    assert "duplicate key" in hasil.stderr, hasil.stderr


# ── Fitur 034 · telemetri ─────────────────────────────────────────────
#
# Tabel peristiwa tambah-saja, ditegakkan peladen; peran telemetri tanpa
# jangkauan skema lain maupun basis data pseudonim (C-05).

_PERISTIWA = (
    "insert into telemetri.peristiwa (pseudonim, jenis, waktu, properti, versi_aplikasi, "
    f"versi_model) values ('{_PSD}', 'session_start', now(), '{{}}', 'uji', 'tanpa_model')"
)

DITOLAK_TELEMETRI = [
    *[
        ("peran_telemetri", "smart_coaching", kueri, sebab)
        for kueri, sebab in (
            ("update telemetri.peristiwa set jenis = 'session_end' where false", "tidak diubah"),
            ("delete from telemetri.peristiwa where false", "tidak dihapus"),
            ("truncate telemetri.peristiwa", "tidak dikosongkan"),
            ("create table telemetri.titipan (a int)", "tanpa CREATE pada skema telemetri"),
            ("select * from pengguna.persetujuan", "persetujuan dibaca peran pengguna, bukan ini"),
            ("select * from akun.pengguna", "tidak membaca akun"),
            ("select * from penemuan.tayang_harian", "tidak membaca penemuan"),
            ("select * from karantina.dokumen_sumber", "C-03 — tidak menjangkau karantina"),
        )
    ],
    (
        "peran_telemetri",
        "smart_coaching_pseudonim",
        "select 1",
        "C-05 — tanpa basis data pseudonim",
    ),
    *[
        (peran, "smart_coaching", "select * from telemetri.peristiwa", f"telemetri di luar {peran}")
        for peran in ("peran_penjawaban", "peran_pengguna", "peran_penayangan", "peran_kurasi")
    ],
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_TELEMETRI)
def test_peladen_menolak_hak_telemetri(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def test_peran_telemetri_berjalan_pada_haknya(basis_data_siap: None) -> None:
    for kueri in (_PERISTIWA, "select jenis, waktu from telemetri.peristiwa"):
        hasil = _psql("peran_telemetri", "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, f"{kueri}\n{hasil.stderr}"


def test_hak_peran_telemetri_persis_menurut_katalog(basis_data_siap: None) -> None:
    tabel = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where table_schema = 'telemetri' and grantee like 'peran\\_%' "
        "group by grantee, table_name order by 1",
    )
    assert tabel.stdout.split() == [
        "peran_analitik:ekspor:INSERT,SELECT",
        "peran_analitik:peristiwa:SELECT",
        "peran_penarikan:peristiwa:DELETE",
        "peran_telemetri:peristiwa:INSERT,SELECT",
    ]


def test_batasan_tabel_peristiwa(basis_data_siap: None) -> None:
    for kueri, sebab in (
        (_PERISTIWA.replace(_PSD, "ks-017"), "C-05 — nama akun sebagai pemilik"),
        (_PERISTIWA.replace("'session_start'", "'klik_iklan'"), "kode di luar taksonomi"),
        (_PERISTIWA.replace("'tanpa_model'", "' '"), "versi model kosong"),
    ):
        hasil = _psql("peran_telemetri", "smart_coaching", "-c", kueri)
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"


def test_kode_peristiwa_sql_sama_dengan_taksonomi() -> None:
    """Dua puluh kode pada batasan tabel dibaca dari `JenisPeristiwa`, bukan
    dipercaya — salinan yang hanyut menolak peristiwa sah atau menerima kode
    kedua puluh satu."""
    import re

    from src.telemetri.peristiwa import JenisPeristiwa

    sql = (BERKAS / "10-telemetri.sql").read_text(encoding="utf-8")
    blok = sql[sql.index("jenis IN (") : sql.index(")", sql.index("jenis IN ("))]
    assert set(re.findall(r"'([a-z_]+)'", blok)) == {j.value for j in JenisPeristiwa}


# ── Penarikan data — fitur 033 ───────────────────────────────────────
#
# Dua peran di luar layanan aplikasi: `peran_penarikan` menghapus data milik
# satu pseudonim pada basis data utama; `peran_penarikan_pseudonim` menghapus
# pemetaannya pada basis data pseudonim. Tidak satu pun menjangkau basis data
# yang lain (C-05), dan bukti permintaan tidak dapat dihapus siapa pun.

_PSD_TARIK = "psd_tttttttttttttttt"
_MINTA = (
    "insert into akun.permintaan_penarikan (pseudonim, diminta_pada) "
    f"values ('{_PSD_TARIK}', now())"
)

DITOLAK_PENARIKAN = [
    *[
        ("peran_penarikan", "smart_coaching", kueri, sebab)
        for kueri, sebab in (
            ("select turunan_sandi from akun.pengguna", "tidak membaca sandi"),
            ("update akun.pengguna set status_aktif = false where false", "tidak mengubah akun"),
            ("select properti from telemetri.peristiwa", "tidak membaca isi peristiwa"),
            ("select pertanyaan from riwayat.giliran", "tidak membaca pertanyaan"),
            ("select alasan from penemuan.belum_relevan", "tidak membaca alasan"),
            (_PERISTIWA, "tidak menambah peristiwa"),
            ("truncate telemetri.peristiwa", "menghapus per pemilik, tidak mengosongkan"),
            ("delete from akun.permintaan_penarikan where false", "bukti tidak dihapus"),
            ("delete from kurasi.putusan where false", "jejak kurasi bukan data peserta"),
            ("select * from karantina.dokumen_sumber", "C-03 — tidak menjangkau karantina"),
        )
    ],
    (
        "peran_penarikan",
        "smart_coaching_pseudonim",
        "select 1",
        "C-05 — tanpa basis data pseudonim",
    ),
    (
        "peran_penarikan_pseudonim",
        "smart_coaching",
        "select 1",
        "C-05 — pemegang pemetaan tidak menjangkau data perilaku",
    ),
    *[
        ("peran_penarikan_pseudonim", "smart_coaching_pseudonim", kueri, sebab)
        for kueri, sebab in (
            ("select id_pengguna from pseudonim.peta_pseudonim", "tidak membaca identitas"),
            (
                "insert into pseudonim.peta_pseudonim (id_pengguna, pseudonim) "
                f"values ('ks-999', '{_PSD_TARIK}')",
                "tidak menambah pemetaan",
            ),
        )
    ],
    *[
        (peran, "smart_coaching", kueri, sebab)
        for peran, kueri, sebab in (
            (
                "peran_autentikasi",
                "delete from akun.permintaan_penarikan where false",
                "tidak dihapus",
            ),
            (
                "peran_autentikasi",
                "update akun.permintaan_penarikan set dipenuhi_pada = now() where false",
                "pemenuhan milik perkakas",
            ),
            (
                "peran_autentikasi",
                "select diminta_pada from akun.permintaan_penarikan",
                "kolom lain",
            ),
            ("peran_pengguna", "select * from akun.permintaan_penarikan", "di luar peran pengguna"),
            ("peran_telemetri", "select * from akun.permintaan_penarikan", "di luar telemetri"),
            ("peran_penjawaban", "select * from akun.permintaan_penarikan", "C-17"),
        )
    ],
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_PENARIKAN)
def test_peladen_menolak_hak_penarikan(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    """M-6: `GRANT CONNECT` basis data pseudonim kepada `peran_penarikan`."""
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def test_peran_penarikan_berjalan_pada_haknya(basis_data_siap: None) -> None:
    """Tiap peran menjalankan tepat yang menjadi tugasnya — hapus per pemilik."""
    langkah = [
        ("peran_autentikasi", "smart_coaching", _MINTA),
        (
            "peran_autentikasi",
            "smart_coaching",
            f"select dipenuhi_pada from akun.permintaan_penarikan where pseudonim = '{_PSD_TARIK}'",
        ),
        *[
            ("peran_penarikan", "smart_coaching", kueri)
            for kueri in (
                f"delete from telemetri.peristiwa where pseudonim = '{_PSD_TARIK}'",
                "delete from riwayat.giliran where id_percakapan in (select id_percakapan "
                f"from riwayat.percakapan where pemilik = '{_PSD_TARIK}')",
                f"delete from riwayat.percakapan where pemilik = '{_PSD_TARIK}'",
                f"delete from penemuan.tayang_harian where id_pengguna = '{_PSD_TARIK}'",
                f"delete from penemuan.belum_relevan where id_pengguna = '{_PSD_TARIK}'",
                f"delete from pengguna.profil_sekolah where id_pengguna = '{_PSD_TARIK}'",
                f"delete from pengguna.prioritas_manajerial where id_pengguna = '{_PSD_TARIK}'",
                f"delete from pengguna.persetujuan where id_pengguna = '{_PSD_TARIK}'",
                "delete from akun.sesi where id_pengguna in (select id from akun.pengguna "
                f"where pseudonim = '{_PSD_TARIK}')",
                f"delete from akun.pengguna where pseudonim = '{_PSD_TARIK}'",
                "update akun.permintaan_penarikan set pseudonim = null, dipenuhi_pada = now(), "
                f"jumlah_baris = '{{}}' where pseudonim = '{_PSD_TARIK}' and dipenuhi_pada is null",
                "select nomor, diminta_pada, dipenuhi_pada from akun.permintaan_penarikan",
            )
        ],
        (
            "peran_penarikan_pseudonim",
            "smart_coaching_pseudonim",
            f"delete from pseudonim.peta_pseudonim where pseudonim = '{_PSD_TARIK}'",
        ),
    ]
    for peran, basis, kueri in langkah:
        hasil = _psql(peran, basis, "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, f"{peran}: {kueri}\n{hasil.stderr}"


def test_batasan_tabel_permintaan_penarikan(basis_data_siap: None) -> None:
    psd = "psd_bbbbbbbbbbbbbbbb"
    minta = _MINTA.replace(_PSD_TARIK, psd)
    assert _psql("peran_autentikasi", "smart_coaching", "-c", minta).returncode == 0
    for peran, kueri, sebab, pesan in (
        ("peran_autentikasi", minta, "satu permintaan tertunda per pseudonim", "duplicate key"),
        (
            "peran_autentikasi",
            _MINTA.replace(_PSD_TARIK, "ks-017"),
            "C-05 — nama akun",
            "violates check constraint",
        ),
        (
            "peran_penarikan",
            "update akun.permintaan_penarikan set dipenuhi_pada = now(), jumlah_baris = '{}' "
            f"where pseudonim = '{psd}'",
            "M-5 — dipenuhi tanpa mengosongkan pseudonim",
            "violates check constraint",
        ),
        (
            "peran_penarikan",
            "update akun.permintaan_penarikan set pseudonim = null, dipenuhi_pada = now() "
            f"where pseudonim = '{psd}'",
            "dipenuhi tanpa jumlah baris",
            "violates check constraint",
        ),
    ):
        hasil = _psql(peran, "smart_coaching", "-c", kueri)
        assert pesan in hasil.stderr, f"{sebab}: {hasil.stderr}"


def test_hak_peran_penarikan_persis_menurut_katalog(basis_data_siap: None) -> None:
    """Hak tingkat tabel kedua peran baru di seluruh skema — termasuk yang
    tidak terpikir: tidak ada `TRUNCATE`, `TRIGGER`, maupun `REFERENCES`."""
    utama = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_schema || '.' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where grantee in ('peran_penarikan', 'peran_penarikan_pseudonim') "
        "group by grantee, table_schema, table_name order by 1",
    )
    assert utama.stdout.split() == [
        "peran_penarikan:akun.pengguna:DELETE",
        "peran_penarikan:akun.sesi:DELETE",
        "peran_penarikan:kurasi.aduan:DELETE",
        "peran_penarikan:kurasi.aduan_digantikan:DELETE",
        "peran_penarikan:kurasi.tindak_lanjut_aduan:DELETE",
        "peran_penarikan:penemuan.belum_relevan:DELETE",
        "peran_penarikan:penemuan.koleksi:DELETE",
        "peran_penarikan:penemuan.tayang_harian:DELETE",
        "peran_penarikan:pengguna.persetujuan:DELETE",
        "peran_penarikan:pengguna.prioritas_manajerial:DELETE",
        "peran_penarikan:pengguna.profil_sekolah:DELETE",
        "peran_penarikan:riwayat.giliran:DELETE",
        "peran_penarikan:riwayat.penilaian:DELETE",
        "peran_penarikan:riwayat.percakapan:DELETE",
        "peran_penarikan:riwayat.pesan:DELETE",
        "peran_penarikan:telemetri.peristiwa:DELETE",
    ]
    pseudonim = _psql(
        PENGELOLA,
        "smart_coaching_pseudonim",
        "-c",
        "select grantee || ':' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where grantee like 'peran\\_%' group by grantee, table_name order by 1",
    )
    assert pseudonim.stdout.split() == [
        "peran_penarikan_pseudonim:peta_pseudonim:DELETE",
        "peran_pseudonim:peta_pseudonim:INSERT,SELECT",
    ]


# ── Analitik penelitian — fitur 035 ──────────────────────────────────
#
# `peran_analitik` membaca peristiwa dan mencatat ekspor — tidak menjangkau
# akun, profil, riwayat, maupun basis data pseudonim, sehingga pemegang
# ekspor tidak dapat menautkan pseudonim ke akun (C-05). Catatan ekspor
# tambah-saja: jejak ke mana data pergi.

_EKSPOR = (
    "insert into telemetri.ekspor (peneliti, diekspor_pada, dari, sampai, "
    "termasuk_pengembangan, jumlah_baris) values "
    f"('{_PSD}', now(), '2026-10-01', '2026-10-06', false, 3)"
)

DITOLAK_ANALITIK = [
    *[
        ("peran_analitik", "smart_coaching", kueri, sebab)
        for kueri, sebab in (
            ("update telemetri.peristiwa set jenis = 'session_end' where false", "tidak diubah"),
            ("delete from telemetri.peristiwa where false", "tidak dihapus"),
            ("truncate telemetri.peristiwa", "tidak dikosongkan"),
            (_PERISTIWA, "analitik tidak menambah peristiwa"),
            ("update telemetri.ekspor set jumlah_baris = 0 where false", "jejak tidak diubah"),
            ("delete from telemetri.ekspor where false", "jejak tidak dihapus"),
            ("select * from akun.pengguna", "C-05 — tidak menautkan pseudonim ke akun"),
            ("select * from pengguna.profil_sekolah", "tidak membaca profil"),
            ("select * from riwayat.giliran", "tidak membaca pertanyaan"),
            ("select * from penemuan.belum_relevan", "tidak membaca alasan"),
            ("select * from karantina.dokumen_sumber", "C-03 — tidak menjangkau karantina"),
        )
    ],
    ("peran_analitik", "smart_coaching_pseudonim", "select 1", "C-05 — tanpa basis data pseudonim"),
    *[
        (peran, "smart_coaching", kueri, sebab)
        for peran, kueri, sebab in (
            ("peran_telemetri", "select * from telemetri.ekspor", "perekam tidak membaca ekspor"),
            ("peran_pengguna", "select * from telemetri.ekspor", "di luar peran pengguna"),
            ("peran_penjawaban", "select * from telemetri.ekspor", "C-17"),
            ("peran_penarikan", "delete from telemetri.ekspor where false", "jejak tidak dihapus"),
            ("peran_penarikan", "select peneliti from telemetri.ekspor", "tidak membaca peneliti"),
        )
    ],
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_ANALITIK)
def test_peladen_menolak_hak_analitik(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    """M-1: `GRANT SELECT` atas `akun.pengguna` kepada `peran_analitik`."""
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def test_peran_analitik_berjalan_pada_haknya(basis_data_siap: None) -> None:
    for peran, kueri in (
        ("peran_analitik", "select pseudonim, jenis, waktu, properti from telemetri.peristiwa"),
        ("peran_analitik", _EKSPOR),
        ("peran_analitik", "select nomor, peneliti, jumlah_baris from telemetri.ekspor"),
        ("peran_penarikan", "select nomor, diekspor_pada, dari, sampai from telemetri.ekspor"),
        ("peran_penarikan", f"select waktu from telemetri.peristiwa where pseudonim = '{_PSD}'"),
    ):
        hasil = _psql(peran, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, f"{peran}: {kueri}\n{hasil.stderr}"


def test_batasan_tabel_ekspor(basis_data_siap: None) -> None:
    for kueri, sebab in (
        (_EKSPOR.replace(_PSD, "ks-017"), "C-05 — nama akun sebagai peneliti"),
        (
            _EKSPOR.replace("'2026-10-01', '2026-10-06'", "'2026-10-06', '2026-10-01'"),
            "dari > sampai",
        ),
        (_EKSPOR.replace("false, 3)", "false, -1)"), "jumlah baris negatif"),
    ):
        hasil = _psql("peran_analitik", "smart_coaching", "-c", kueri)
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"


# ── Penilaian jawaban dan aduan kurator — fitur 036 ──────────────────
#
# `riwayat.pesan` catatan audit: ditambah peran riwayat, tidak dibacanya (C-07).
# Aduan salinan yang dikirim peserta: kurator membacanya tanpa hak apa pun
# atas skema `riwayat` (R-06, P-2 B). Seluruhnya tambah-saja bagi peran
# aplikasi; hanya peran penarikan yang menghapus (R-07).

_PSD_NILAI = "psd_nnnnnnnnnnnnnnnn"
_PERCAKAPAN_NILAI = "6d2f7c1a-4b3e-4f9a-8c2d-1e5b7a9c3f01"


def _pesan_sql(id_pesan: str, tanggapan: str | None = None) -> str:
    isi = (
        tanggapan
        if tanggapan is not None
        else f'{{"id_pesan": "{id_pesan}", "status_dasar": "kuat", "versi": {{"model": "m"}}}}'
    )
    return (
        "insert into riwayat.pesan (id_pesan, id_percakapan, tanggapan, waktu) "
        f"values ('{id_pesan}', '{_PERCAKAPAN_NILAI}', '{isi}', now())"
    )


def _penilaian_sql(
    id_pesan: str, nilai: str = "keliru", kirim: str = "true", alasan: str = "null"
) -> str:
    return (
        "insert into riwayat.penilaian (id_pesan, nilai, alasan, kirim_ke_kurator, waktu) "
        f"values ('{id_pesan}', '{nilai}', {alasan}, {kirim}, now())"
    )


def _aduan_sql(tanggapan: str = '{"status_dasar": "kuat"}', pertanyaan: str = "Bagaimana?") -> str:
    return (
        "insert into kurasi.aduan (nomor_penilaian, pertanyaan, tanggapan, alasan, diadukan_pada) "
        f"select max(nomor), '{pertanyaan}', '{tanggapan}', null, now() from riwayat.penilaian"
    )


def _tindak_lanjut_sql(
    tindak: str = "jawaban_sesuai_dasar", catatan: str = "Sudah sesuai", psd: str = _PSD_KURATOR
) -> str:
    return (
        "insert into kurasi.tindak_lanjut_aduan "
        "(nomor_aduan, tindak_lanjut, catatan, peran, pseudonim_kurator, waktu) "
        f"select max(nomor), '{tindak}', '{catatan}', 'kurator', '{psd}', now() from kurasi.aduan"
    )


def _siapkan_pesan(id_pesan: str) -> None:
    for kueri in (
        "insert into riwayat.percakapan (id_percakapan, pemilik, dibuat_pada) "
        f"values ('{_PERCAKAPAN_NILAI}', '{_PSD_NILAI}', now()) on conflict do nothing",
        "insert into riwayat.giliran (id_percakapan, pertanyaan, id_pesan, waktu) "
        f"values ('{_PERCAKAPAN_NILAI}', 'Bagaimana menyusun jadwal?', '{id_pesan}', now())",
        _pesan_sql(id_pesan),
    ):
        hasil = _psql(PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, hasil.stderr


DITOLAK_PENILAIAN = [
    *[
        (peran, "smart_coaching", kueri, sebab)
        for peran, kueri, sebab in (
            (
                "peran_riwayat",
                "select tanggapan from riwayat.pesan",
                "C-07 — riwayat tidak membaca jawaban",
            ),
            ("peran_riwayat", "select * from riwayat.penilaian", "riwayat tidak membaca penilaian"),
            ("peran_riwayat", "update riwayat.pesan set waktu = now() where false", "tambah-saja"),
            ("peran_riwayat", "delete from riwayat.pesan where false", "tambah-saja"),
            ("peran_riwayat", "select * from kurasi.aduan", "riwayat tidak membaca aduan"),
            (
                "peran_penilaian",
                "update riwayat.penilaian set nilai = 'membantu' where false",
                "tambah-saja",
            ),
            ("peran_penilaian", "delete from riwayat.penilaian where false", "tambah-saja"),
            (
                "peran_penilaian",
                "select alasan from riwayat.penilaian",
                "alasan tidak dibaca kembali",
            ),
            (
                "peran_penilaian",
                "update riwayat.pesan set waktu = now() where false",
                "penilai tidak mengubah jawaban",
            ),
            ("peran_penilaian", _pesan_sql("msg_tolak036"), "penilai tidak menulis jawaban"),
            (
                "peran_penilaian",
                "select pertanyaan, tanggapan from kurasi.aduan",
                "penilai tidak membaca aduan",
            ),
            (
                "peran_penilaian",
                "update kurasi.aduan set alasan = null where false",
                "aduan tambah-saja",
            ),
            (
                "peran_penilaian",
                "delete from kurasi.aduan_digantikan where false",
                "penanda tambah-saja",
            ),
            ("peran_penilaian", _tindak_lanjut_sql(), "penilai tidak menindaklanjuti"),
            ("peran_penilaian", "select * from akun.pengguna", "C-05 — tidak menjangkau akun"),
            ("peran_penilaian", "select * from telemetri.peristiwa", "tidak membaca peristiwa"),
            (
                "peran_kurasi",
                "select * from riwayat.giliran",
                "R-06 — kurator tidak membaca riwayat",
            ),
            ("peran_kurasi", "select * from riwayat.pesan", "R-06 — hanya salinan yang dikirim"),
            ("peran_kurasi", "select * from riwayat.percakapan", "R-06 — tanpa pemilik"),
            (
                "peran_kurasi",
                "select nomor_penilaian from kurasi.aduan",
                "R-06 — tanpa tautan ke penilaian",
            ),
            ("peran_kurasi", _aduan_sql(), "aduan hanya lahir dari peserta"),
            (
                "peran_kurasi",
                "update kurasi.aduan set alasan = null where false",
                "aduan tambah-saja",
            ),
            ("peran_kurasi", "delete from kurasi.aduan where false", "aduan tidak dihapus kurator"),
            (
                "peran_kurasi",
                "insert into kurasi.aduan_digantikan (nomor_aduan, waktu) select nomor, now() from kurasi.aduan where false",
                "kurator tidak menggugurkan",
            ),
            (
                "peran_kurasi",
                "update kurasi.tindak_lanjut_aduan set catatan = 'x' where false",
                "jejak tambah-saja",
            ),
            (
                "peran_kurasi",
                "delete from kurasi.tindak_lanjut_aduan where false",
                "jejak tidak dihapus",
            ),
            (
                "peran_penjawaban",
                "select * from riwayat.pesan",
                "C-17, R-07 — penjawab tidak membaca jawaban lama",
            ),
            (
                "peran_penjawaban",
                "select * from kurasi.aduan",
                "C-14 — aduan tidak memengaruhi jawaban",
            ),
            (
                "peran_penarikan",
                "select tanggapan from riwayat.pesan",
                "penarikan tidak membaca isi",
            ),
            (
                "peran_penarikan",
                "select alasan from riwayat.penilaian",
                "penarikan tidak membaca alasan",
            ),
            (
                "peran_penarikan",
                "select pertanyaan from kurasi.aduan",
                "penarikan tidak membaca aduan",
            ),
            (
                "peran_penarikan",
                "update kurasi.aduan set alasan = null where false",
                "hapus, bukan ubah",
            ),
            (
                "peran_analitik",
                "select * from riwayat.penilaian",
                "analitik membaca peristiwa saja",
            ),
            ("peran_pengguna", "select * from kurasi.aduan", "di luar peran pengguna"),
        )
    ],
    (
        "peran_penilaian",
        "smart_coaching_pseudonim",
        "select 1",
        "C-05 — tanpa basis data pseudonim",
    ),
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_PENILAIAN)
def test_peladen_menolak_hak_penilaian(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    """M-1: `GRANT SELECT` atas `riwayat.pesan` kepada `peran_riwayat`."""
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def test_skema_riwayat_dan_kurasi_hanya_bagi_perannya(basis_data_siap: None) -> None:
    """M-2: `GRANT USAGE ON SCHEMA riwayat TO peran_kurasi`.

    Hak skema tidak terlihat pada uji penolakan — tanpa hak tabel, kueri
    tetap ditolak — sehingga dibaca dari katalog."""
    for skema, harapan in (
        ("riwayat", ["peran_penarikan", "peran_penilaian", "peran_riwayat"]),
        (
            "kurasi",
            [
                "peran_kurasi",
                "peran_penarikan",
                "peran_penayangan",
                "peran_pengisi_antrean",
                "peran_penilaian",
            ],
        ),
    ):
        hasil = _psql(
            PENGELOLA,
            "smart_coaching",
            "-c",
            "select rolname from pg_roles where rolname like 'peran\\_%' "
            f"and has_schema_privilege(rolname, '{skema}', 'USAGE') order by 1",
        )
        assert hasil.stdout.split() == harapan, skema


def test_hak_kolom_riwayat_persis_menurut_katalog(basis_data_siap: None) -> None:
    kolom = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select a.rolname || ':' || c.relname || ':' || x.privilege_type || ':' "
        "|| string_agg(att.attname, ',' order by att.attname) "
        "from pg_attribute att join pg_class c on c.oid = att.attrelid "
        "join pg_namespace n on n.oid = c.relnamespace and n.nspname = 'riwayat' "
        "cross join lateral aclexplode(att.attacl) x "
        "join pg_roles a on a.oid = x.grantee "
        "where att.attacl is not null "
        "group by a.rolname, c.relname, x.privilege_type order by 1",
    )
    assert kolom.stdout.split() == [
        "peran_penarikan:giliran:SELECT:id_percakapan",
        "peran_penarikan:penilaian:SELECT:id_pesan,nomor",
        "peran_penarikan:percakapan:SELECT:id_percakapan,pemilik",
        "peran_penarikan:pesan:SELECT:id_percakapan,id_pesan",
        "peran_penilaian:giliran:SELECT:id_pesan,pertanyaan",
        "peran_penilaian:penilaian:SELECT:id_pesan,nomor",
        "peran_penilaian:percakapan:SELECT:id_percakapan,pemilik",
        "peran_penilaian:pesan:SELECT:id_percakapan,id_pesan,tanggapan",
    ]


def test_peran_penilaian_berjalan_pada_haknya(basis_data_siap: None) -> None:
    _siapkan_pesan("msg_jalan036")
    for peran, kueri in (
        ("peran_riwayat", _pesan_sql("msg_riwayat036")),
        (
            "peran_penilaian",
            "select p.id_pesan, p.tanggapan, g.pertanyaan, c.pemilik from riwayat.pesan p "
            "join riwayat.giliran g on g.id_pesan = p.id_pesan "
            "join riwayat.percakapan c on c.id_percakapan = p.id_percakapan",
        ),
        ("peran_penilaian", _penilaian_sql("msg_jalan036") + " returning nomor"),
        ("peran_penilaian", _aduan_sql()),
        (
            "peran_penilaian",
            "insert into kurasi.aduan_digantikan (nomor_aduan, waktu) "
            "select min(nomor), now() from kurasi.aduan on conflict do nothing",
        ),
        # Penilaian berikutnya atas pesan yang sama melahirkan aduan baru.
        ("peran_penilaian", _penilaian_sql("msg_jalan036")),
        ("peran_penilaian", _aduan_sql()),
        (
            "peran_kurasi",
            "select nomor, pertanyaan, tanggapan, alasan, diadukan_pada from kurasi.aduan",
        ),
        ("peran_kurasi", "select nomor_aduan from kurasi.aduan_digantikan"),
        ("peran_kurasi", _tindak_lanjut_sql()),
        ("peran_kurasi", "select * from kurasi.tindak_lanjut_aduan"),
        ("peran_penarikan", "select id_pesan, id_percakapan from riwayat.pesan"),
        ("peran_penarikan", "select nomor, id_pesan from riwayat.penilaian"),
        ("peran_penarikan", "select nomor, nomor_penilaian from kurasi.aduan"),
        ("peran_penarikan", "select nomor_aduan from kurasi.aduan_digantikan"),
        ("peran_penarikan", "select nomor_aduan from kurasi.tindak_lanjut_aduan"),
    ):
        hasil = _psql(peran, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, f"{peran}: {kueri}\n{hasil.stderr}"


def test_batasan_tabel_penilaian(basis_data_siap: None) -> None:
    _siapkan_pesan("msg_batas036")
    for kueri, sebab in (
        (_penilaian_sql("msg_batas036", nilai="bagus"), "nilai di luar FR-F07"),
        (_penilaian_sql("msg_batas036", nilai="membantu"), "P-2 B — kirim hanya bersama keliru"),
        (
            _penilaian_sql("msg_batas036", kirim="false", alasan="'  '"),
            "alasan kosong disimpan null",
        ),
        (
            _pesan_sql("msg_beda036", '{"id_pesan": "msg_lain", "versi": {"model": "m"}}'),
            "tanggapan milik pesan lain",
        ),
        (
            _pesan_sql(
                "msg_yakin036",
                '{"id_pesan": "msg_yakin036", "versi": {"model": "m"}, "tingkat_keyakinan": 0.9}',
            ),
            "FR-F06 — tanpa tingkat keyakinan",
        ),
        (
            _pesan_sql("msg_versi036", '{"id_pesan": "msg_versi036", "versi": {"indeks": "i"}}'),
            "KT-06 — tanggapan tanpa versi model",
        ),
        (_aduan_sql('{"id_pesan": "msg_batas036"}'), "R-06 — salinan tanpa id_pesan"),
        (_aduan_sql(pertanyaan=""), "aduan tanpa pertanyaan"),
        (_tindak_lanjut_sql(tindak="lainnya"), "tindak lanjut di luar empat nilai"),
        (_tindak_lanjut_sql(catatan="  "), "catatan wajib"),
        (_tindak_lanjut_sql(psd="ks-017"), "C-05 — nama akun sebagai kurator"),
    ):
        hasil = _psql(PENGELOLA, "smart_coaching", "-c", kueri)
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"

    hasil = _psql(
        PENGELOLA, "smart_coaching", "-c", _penilaian_sql("msg_tidak_ada036", kirim="false")
    )
    assert "violates foreign key constraint" in hasil.stderr, hasil.stderr

    for kueri in (_penilaian_sql("msg_batas036"), _aduan_sql(), _tindak_lanjut_sql()):
        hasil = _psql(PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, hasil.stderr
    kedua = _psql(PENGELOLA, "smart_coaching", "-c", _tindak_lanjut_sql(catatan="Kedua"))
    assert "duplicate key value" in kedua.stderr, "satu tindak lanjut per aduan"


# ── Catatan korpus, pembaca sumber, dan koleksi — fitur 032 ──────────
#
# `peran_pembaca_sumber` membaca bagian yang dirujuk — tidak teks dokumen utuh,
# tidak karantina, tidak `indeks_metadata` — dan tidak menulis apa pun.
# `peran_koleksi` memegang tabel koleksi saja; penayang tidak menjangkaunya,
# sehingga koleksi tidak dapat menjadi sinyal pemilihan beranda (R-03).
# Catatan metadata dan status korpus tambah-saja.

_PSD_KOLEKSI = "psd_kkkkkkkkkkkkkkkk"
_DOK_032 = "dok-032"


def _metadata_sql(
    id_dokumen: str = _DOK_032,
    jenis: str = "regulasi_resmi",
    tingkat: str = "publik",
    tahun: int = 2026,
    judul: str = "Permendikdasmen Nomor 1 Tahun 2026",
) -> str:
    return (
        "insert into korpus.metadata_dokumen "
        "(id_dokumen, judul, jenis, penerbit, tahun, tingkat_kerahasiaan) values "
        f"('{id_dokumen}', '{judul}', '{jenis}', 'Kemendikdasmen', {tahun}, '{tingkat}')"
    )


def _status_sql(
    id_dokumen: str = _DOK_032, status: str = "berlaku", pengganti: str = "null"
) -> str:
    return (
        "insert into korpus.status_dokumen (id_dokumen, status, rujukan_pengganti) "
        f"values ('{id_dokumen}', '{status}', {pengganti})"
    )


def _koleksi_sql(id_butir: str = "b-032", catatan: str = "null", psd: str = _PSD_KOLEKSI) -> str:
    return (
        "insert into penemuan.koleksi (id_pengguna, id_butir, catatan, disimpan_pada) "
        f"values ('{psd}', '{id_butir}', {catatan}, now()) "
        "on conflict (id_pengguna, id_butir) do update "
        "set catatan = excluded.catatan, disimpan_pada = excluded.disimpan_pada"
    )


DITOLAK_SUMBER = [
    *[
        (peran, "smart_coaching", kueri, sebab)
        for peran, kueri, sebab in (
            (
                "peran_pembaca_sumber",
                "select isi from korpus.dokumen_sumber",
                "P-2 A — pembaca tidak membaca teks dokumen utuh",
            ),
            (
                "peran_pembaca_sumber",
                "select * from karantina.dokumen_sumber",
                "C-03 — pembaca tidak menjangkau karantina",
            ),
            (
                "peran_pembaca_sumber",
                "select teks from indeks_metadata.segmen_teks",
                "C-02 — segmen berlisensi tertutup tidak terjangkau",
            ),
            (
                "peran_pembaca_sumber",
                "select vektor_sematan from indeks_utama.segmen_teks",
                "hak minimum — pembaca tidak membaca vektor",
            ),
            ("peran_pembaca_sumber", _status_sql(), "R-05 — pembaca tidak menulis status"),
            ("peran_pembaca_sumber", _metadata_sql(), "R-05 — pembaca tidak menulis metadata"),
            (
                "peran_pembaca_sumber",
                "update indeks_utama.segmen_teks set teks = 'x' where false",
                "R-05, C-17 — pembaca tidak menyunting segmen",
            ),
            (
                "peran_pembaca_sumber",
                "select * from penemuan.koleksi",
                "pembaca tidak membaca koleksi",
            ),
            ("peran_pembaca_sumber", "select * from riwayat.giliran", "hak minimum"),
            ("peran_koleksi", "select * from penemuan.tayang_harian", "kelayakan dibaca penayang"),
            ("peran_koleksi", "select * from kurasi.butir_tayang", "kelayakan dibaca penayang"),
            ("peran_koleksi", "select * from korpus.dokumen_sumber", "hak minimum"),
            (
                "peran_koleksi",
                "update penemuan.koleksi set id_pengguna = 'psd_xxxxxxxxxxxxxxxx' where false",
                "pemilik koleksi tidak dapat dipindahkan",
            ),
            ("peran_koleksi", "truncate penemuan.koleksi", "koleksi tidak dikosongkan sekaligus"),
            (
                "peran_penayangan",
                "select * from penemuan.koleksi",
                "R-03, C-14 — pemilihan beranda tidak membaca koleksi",
            ),
            (
                "peran_penjawaban",
                "select * from penemuan.koleksi",
                "C-14 — koleksi tidak memengaruhi jawaban",
            ),
            ("peran_analitik", "select * from penemuan.koleksi", "analitik membaca peristiwa saja"),
            (
                "peran_penarikan",
                "select catatan from penemuan.koleksi",
                "penarikan tidak membaca catatan",
            ),
            (
                "peran_penarikan",
                "delete from korpus.status_dokumen where false",
                "catatan korpus bukan data peserta",
            ),
            (
                "peran_pengisi_antrean",
                "select * from korpus.status_dokumen",
                "perkakas kurasi tidak membaca korpus",
            ),
            (
                "peran_pengisi_antrean",
                "select id from korpus.dokumen_sumber",
                "perkakas kurasi tidak membaca korpus",
            ),
            ("peran_pengisi_antrean", _metadata_sql(), "metadata milik gerbang ingesti"),
            (
                "peran_pengisi_antrean",
                "update korpus.status_dokumen set status = 'berlaku' where false",
                "status tambah-saja",
            ),
            (
                "peran_verifikasi",
                "update korpus.metadata_dokumen set judul = 'x' where false",
                "metadata tambah-saja",
            ),
            (
                "peran_verifikasi",
                "delete from korpus.metadata_dokumen where false",
                "metadata tambah-saja",
            ),
            ("peran_verifikasi", _status_sql(), "status bukan pekerjaan verifikator"),
            ("peran_penjawaban", _status_sql(), "C-17 — penjawab tanpa hak tulis"),
            ("peran_pemanggil_llm", _metadata_sql(), "C-17 — pemanggil model tanpa hak tulis"),
        )
    ],
    *[
        (peran, "smart_coaching_pseudonim", "select 1", "C-05 — tanpa basis data pseudonim")
        for peran in ("peran_pembaca_sumber", "peran_koleksi")
    ],
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_SUMBER)
def test_peladen_menolak_hak_sumber_dan_koleksi(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def test_skema_korpus_indeks_dan_penemuan_hanya_bagi_perannya(basis_data_siap: None) -> None:
    """M-2: `GRANT USAGE ON SCHEMA indeks_metadata TO peran_pembaca_sumber`.

    Hak skema dibaca dari katalog: tanpa hak tabel, kueri tetap ditolak,
    sehingga uji penolakan tidak melihatnya."""
    for skema, harapan in (
        # Fitur 037: ketiga peran dokumen saja — peran aplikasi mana pun tidak
        # menjangkau karantina (R-05, C-03). M-4 fitur 037 merah di sini.
        ("karantina", ["peran_ingesti", "peran_penarikan_dokumen", "peran_verifikasi"]),
        (
            "korpus",
            [
                "peran_ingesti",
                "peran_pemanggil_llm",
                "peran_pembaca_sumber",
                "peran_penarikan_dokumen",
                "peran_pengisi_antrean",
                "peran_penjawaban",
                "peran_verifikasi",
            ],
        ),
        (
            "indeks_utama",
            [
                "peran_pemanggil_llm",
                "peran_pembaca_sumber",
                "peran_penarikan_dokumen",
                "peran_penjawaban",
                "peran_penyematan",
                "peran_verifikasi",
            ],
        ),
        (
            "indeks_metadata",
            [
                "peran_penarikan_dokumen",
                "peran_penjawaban",
                "peran_penyematan",
                "peran_verifikasi",
            ],
        ),
        ("penemuan", ["peran_koleksi", "peran_penarikan", "peran_penayangan"]),
    ):
        hasil = _psql(
            PENGELOLA,
            "smart_coaching",
            "-c",
            "select rolname from pg_roles where rolname like 'peran\\_%' "
            f"and has_schema_privilege(rolname, '{skema}', 'USAGE') order by 1",
        )
        assert hasil.stdout.split() == harapan, skema


def test_hak_catatan_korpus_persis_menurut_katalog(basis_data_siap: None) -> None:
    """Hak bawaan skema korpus dicabut sebagian (`UPDATE`, `INSERT` status bagi
    verifikator); `SELECT` bagi jalur penjawab dibiarkan — rancangan, bukan
    sisa (plan Bagian 2)."""
    hasil = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_schema || '.' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where table_schema = 'korpus' and table_name in ('metadata_dokumen', 'status_dokumen') "
        "and grantee like 'peran\\_%' group by grantee, table_schema, table_name order by 1",
    )
    assert hasil.stdout.split() == [
        "peran_pemanggil_llm:korpus.metadata_dokumen:SELECT",
        "peran_pemanggil_llm:korpus.status_dokumen:SELECT",
        "peran_pembaca_sumber:korpus.metadata_dokumen:SELECT",
        "peran_pembaca_sumber:korpus.status_dokumen:SELECT",
        "peran_pengisi_antrean:korpus.status_dokumen:INSERT",
        "peran_penjawaban:korpus.metadata_dokumen:SELECT",
        "peran_penjawaban:korpus.status_dokumen:SELECT",
        "peran_verifikasi:korpus.metadata_dokumen:INSERT,SELECT",
        "peran_verifikasi:korpus.status_dokumen:SELECT",
    ]


def test_hak_peran_pembaca_dan_koleksi_persis_di_seluruh_skema(basis_data_siap: None) -> None:
    """M-1: `GRANT SELECT (isi) ON korpus.dokumen_sumber TO peran_pembaca_sumber`.

    Seluruh skema, termasuk hak yang tidak terpikir: tanpa `TRUNCATE`,
    `TRIGGER`, maupun `REFERENCES`."""
    tabel = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_schema || '.' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where grantee in ('peran_pembaca_sumber', 'peran_koleksi') "
        "group by grantee, table_schema, table_name order by 1",
    )
    assert tabel.stdout.split() == [
        "peran_koleksi:penemuan.koleksi:DELETE,INSERT,SELECT",
        "peran_pembaca_sumber:korpus.metadata_dokumen:SELECT",
        "peran_pembaca_sumber:korpus.status_dokumen:SELECT",
    ]
    kolom = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select a.rolname || ':' || n.nspname || '.' || c.relname || ':' || x.privilege_type "
        "|| ':' || string_agg(att.attname, ',' order by att.attname) "
        "from pg_attribute att join pg_class c on c.oid = att.attrelid "
        "join pg_namespace n on n.oid = c.relnamespace "
        "cross join lateral aclexplode(att.attacl) x "
        "join pg_roles a on a.oid = x.grantee "
        "where att.attacl is not null "
        "and a.rolname in ('peran_pembaca_sumber', 'peran_koleksi') "
        "group by a.rolname, n.nspname, c.relname, x.privilege_type order by 1",
    )
    assert kolom.stdout.split() == [
        "peran_koleksi:penemuan.koleksi:UPDATE:catatan,disimpan_pada",
        "peran_pembaca_sumber:indeks_utama.segmen_teks:SELECT:"
        "anonimisasi_terverifikasi,id_dokumen,id_segmen,lisensi,penanda_bagian,teks",
        "peran_pembaca_sumber:korpus.dokumen_sumber:SELECT:id",
    ]


def test_peran_sumber_dan_koleksi_berjalan_pada_haknya(basis_data_siap: None) -> None:
    """TK-64: tiap peran tersambung sendiri dan menjalankan pekerjaannya."""
    for kueri in (
        f"delete from korpus.dokumen_sumber where id = '{_DOK_032}'",
        f"insert into korpus.dokumen_sumber (id, isi) values ('{_DOK_032}', '\"teks\"'::jsonb)",
        f"delete from indeks_utama.segmen_teks where id_dokumen = '{_DOK_032}'",
        "insert into indeks_utama.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
        "anonimisasi_terverifikasi, penanda_bagian) values "
        f"('seg-032', '{_DOK_032}', 'Kepala sekolah menyusun rencana.', 'terbuka', true, "
        "'Pasal 7')",
    ):
        _jalan(PENGELOLA, kueri)
    for peran, kueri in (
        ("peran_verifikasi", _metadata_sql()),
        ("peran_pengisi_antrean", _status_sql(status="diubah", pengganti="'Permen 2/2027'")),
        (
            "peran_pembaca_sumber",
            "select d.id, m.judul, m.jenis, m.tingkat_kerahasiaan, s.status, s.rujukan_pengganti "
            "from korpus.dokumen_sumber d "
            "join korpus.metadata_dokumen m on m.id_dokumen = d.id "
            "left join korpus.status_dokumen s on s.id_dokumen = d.id "
            f"where d.id = '{_DOK_032}' order by m.nomor desc, s.nomor desc limit 1",
        ),
        (
            "peran_pembaca_sumber",
            "select id_segmen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian "
            f"from indeks_utama.segmen_teks where id_dokumen = '{_DOK_032}'",
        ),
        ("peran_koleksi", _koleksi_sql(catatan="'Bahas di rapat guru'")),
        ("peran_koleksi", _koleksi_sql(catatan="null")),
        (
            "peran_koleksi",
            f"select id_butir, catatan, disimpan_pada from penemuan.koleksi "
            f"where id_pengguna = '{_PSD_KOLEKSI}'",
        ),
        (
            "peran_koleksi",
            f"delete from penemuan.koleksi where id_pengguna = '{_PSD_KOLEKSI}' "
            "and id_butir = 'b-032'",
        ),
        ("peran_koleksi", _koleksi_sql(id_butir="b-032-tarik")),
        ("peran_penarikan", "select id_pengguna from penemuan.koleksi"),
        ("peran_penarikan", f"delete from penemuan.koleksi where id_pengguna = '{_PSD_KOLEKSI}'"),
    ):
        _jalan(peran, kueri)


def test_batasan_tabel_sumber_dan_koleksi(basis_data_siap: None) -> None:
    for kueri, sebab in (
        (_metadata_sql(jenis="buku"), "jenis di luar JenisSumber"),
        (_metadata_sql(tingkat="rahasia"), "tingkat di luar TingkatKerahasiaan"),
        (_metadata_sql(tahun=1900), "tahun sebelum TAHUN_PALING_AWAL"),
        (_metadata_sql(judul="  "), "judul wajib"),
        (_status_sql(status="kedaluwarsa"), "status di luar KL-07"),
        (_status_sql(status="berlaku", pengganti="'Permen 2/2027'"), "pengganti tanpa perubahan"),
        (_status_sql(status="dicabut", pengganti="'  '"), "pengganti kosong disimpan null"),
        (_koleksi_sql(psd="ks-017"), "C-05 — nama akun sebagai pemilik"),
        (_koleksi_sql(catatan="'  '"), "catatan kosong disimpan null"),
    ):
        hasil = _psql(PENGELOLA, "smart_coaching", "-c", kueri)
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"

    for kueri in (_status_sql(status="dicabut"), _metadata_sql(id_dokumen="dok-032-lain")):
        hasil = _psql(PENGELOLA, "smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, hasil.stderr


def test_daftar_nilai_batasan_korpus_sama_dengan_enumnya() -> None:
    """Tiga daftar dibaca dari enumnya, bukan dipercaya — salinan yang hanyut
    menolak dokumen sah, atau menerima nilai yang tidak dikenal pembaca."""
    import re

    from src.ingest.dokumen import TingkatKerahasiaan
    from src.ingest.peringkat import JenisSumber
    from src.kamus.segmen import StatusKeberlakuan

    sql = (BERKAS / "14-sumber-dan-koleksi.sql").read_text(encoding="utf-8")

    def daftar(penanda: str) -> set[str]:
        mulai = sql.index(penanda)
        return set(re.findall(r"'([a-z_]+)'", sql[mulai : sql.index(")", mulai)]))

    assert daftar("jenis IN") == {j.value for j in JenisSumber}
    assert daftar("tingkat_kerahasiaan IN") == {t.value for t in TingkatKerahasiaan}
    assert daftar("status IN") == {s.value for s in StatusKeberlakuan}


# ── Fitur 037 · Catatan gerbang ingesti dan peran dokumen ───────────────────
#
# Tiga peran, satu per kredensial kode (P-2 A, TK-83): `peran_ingesti` menulis
# karantina tanpa membaca isinya; `peran_verifikasi` membaca karantina dan hanya
# dapat MENGELUARKAN dokumen darinya; `peran_penarikan_dokumen` mengeluarkan
# dokumen dari korpus beserta segmennya dari kedua indeks (TK-84 A). Catatan
# karantina tambah-saja; pelaku berupa kode anggota tim (P-6 A).

_DOK_037 = "dok-037"
_SAMARAN = '{"nik": 1, "nip": 0, "nisn": 0, "nuptk": 0, "telepon": 0, "rekening": 0}'


def _terima_sql(
    id_dokumen: str = _DOK_037,
    jenis: str = "dokumen_sekolah",
    tingkat: str = "internal_sekolah",
    persetujuan: str = "diberikan",
    penerima: str = "tm-001",
    samaran: str = _SAMARAN,
    tahun: int = 2026,
) -> str:
    """Bentuk pernyataan `terima` T-4: teks, penerimaan, dan temuan sekaligus;
    tidak menulis apa pun bila dokumennya sedang di korpus (TK-85 A).

    Ganti lalu sisip, bukan `ON CONFLICT`: `excluded.isi` menuntut hak baca
    `isi`, padahal ingesti sengaja tidak memegangnya."""
    return (
        "with ganti as ("
        "  update karantina.dokumen_sumber set isi = '\"Notulen rapat [NIK]\"'::jsonb, "
        f"  disimpan_pada = now() where id = '{id_dokumen}' returning id"
        "), baru as ("
        "  insert into karantina.dokumen_sumber (id, isi) "
        f"  select '{id_dokumen}', '\"Notulen rapat [NIK]\"'::jsonb "
        "  where not exists (select 1 from ganti) "
        f"  and not exists (select 1 from korpus.dokumen_sumber where id = '{id_dokumen}') "
        "  returning id"
        "), tulis as (select id from ganti union all select id from baru"
        "), terima as ("
        "  insert into karantina.penerimaan (id_dokumen, judul, jenis, penerbit, tahun, "
        "  tingkat_kerahasiaan, status_persetujuan_pemilik, samaran, id_penerima) "
        f"  select id, 'Notulen rapat pleno', '{jenis}', 'SDN Sukamaju', {tahun}, '{tingkat}', "
        f"  '{persetujuan}', '{samaran}'::jsonb, '{penerima}' from tulis returning nomor"
        ") insert into karantina.temuan_pola (nomor_penerimaan, pola, mulai, akhir, kutipan) "
        "select nomor, 'abaikan instruksi', 0, 17, 'abaikan instruksi' from terima"
    )


def _nomor(id_dokumen: str) -> str:
    return f"(select max(nomor) from karantina.penerimaan where id_dokumen = '{id_dokumen}')"


def _jejak_sql(
    id_dokumen: str = _DOK_037,
    putusan: str = "tolak",
    pelaku: str = "tm-002",
    dari: str = "karantina",
    ke: str = "karantina",
    alasan: str = "memuat nama guru pada halaman 3",
) -> str:
    return (
        "insert into karantina.jejak_area (id_dokumen, nomor_penerimaan, putusan, id_pelaku, "
        f"dari_area, ke_area, alasan) values ('{id_dokumen}', {_nomor(id_dokumen)}, "
        f"'{putusan}', '{pelaku}', '{dari}', '{ke}', '{alasan}')"
    )


def _tinjau_sql(id_dokumen: str = _DOK_037, peninjau: str = "tm-002") -> str:
    return (
        "insert into karantina.tinjauan_temuan (nomor_penerimaan, id_peninjau, catatan) "
        f"values ({_nomor(id_dokumen)}, '{peninjau}', 'kutipan peraturan, bukan perintah')"
    )


def _setujui_sql(id_dokumen: str = _DOK_037) -> str:
    """Bentuk pernyataan `setujui` T-4: pindah, metadata, jejak sekaligus."""
    return (
        "with terangkat as ("
        f"  delete from karantina.dokumen_sumber where id = '{id_dokumen}' returning id, isi"
        "), pindah as ("
        "  insert into korpus.dokumen_sumber (id, isi) select id, isi from terangkat returning id"
        "), catat as ("
        "  insert into korpus.metadata_dokumen "
        "  (id_dokumen, judul, jenis, penerbit, tahun, tingkat_kerahasiaan) "
        "  select id, 'Notulen rapat pleno', 'dokumen_sekolah', 'SDN Sukamaju', 2026, "
        "  'internal_sekolah' from pindah"
        "), jejak as ("
        "  insert into karantina.jejak_area (id_dokumen, nomor_penerimaan, putusan, id_pelaku, "
        "  dari_area, ke_area, alasan) "
        f"  select id, {_nomor(id_dokumen)}, 'setujui', 'tm-002', 'karantina', 'korpus', "
        "  'anonimisasi terperiksa' from pindah"
        ") select id from pindah"
    )


def _cabut_sql(id_dokumen: str = _DOK_037) -> str:
    """Bentuk pernyataan `cabut` T-4: keluar dari korpus beserta segmennya dari
    kedua indeks, dan jejaknya, sekaligus (TK-84 A)."""
    return (
        "with terangkat as ("
        f"  delete from korpus.dokumen_sumber where id = '{id_dokumen}' returning id, isi"
        "), kembali as ("
        "  insert into karantina.dokumen_sumber (id, isi) select id, isi from terangkat"
        "), segmen_utama as ("
        f"  delete from indeks_utama.segmen_teks where id_dokumen = '{id_dokumen}'"
        "), segmen_metadata as ("
        f"  delete from indeks_metadata.segmen_teks where id_dokumen = '{id_dokumen}'"
        ") insert into karantina.jejak_area (id_dokumen, nomor_penerimaan, putusan, id_pelaku, "
        "dari_area, ke_area, alasan) "
        f"select '{id_dokumen}', {_nomor(id_dokumen)}, 'cabut_persetujuan', 'tm-003', "
        "case when exists (select 1 from terangkat) then 'korpus' else 'karantina' end, "
        "'karantina', 'pemilik menarik izin'"
    )


DITOLAK_INGESTI = [
    *[
        (peran, "smart_coaching", kueri, sebab)
        for peran, kueri, sebab in (
            (
                "peran_ingesti",
                "select isi from karantina.dokumen_sumber",
                "ingesti tidak membaca bahan yang ditaruhnya",
            ),
            ("peran_ingesti", "select isi from korpus.dokumen_sumber", "hanya kolom id korpus"),
            ("peran_ingesti", "select judul from karantina.penerimaan", "penerimaan tanpa dibaca"),
            ("peran_ingesti", _jejak_sql(), "putusan milik verifikator"),
            ("peran_ingesti", _tinjau_sql(), "tinjauan milik verifikator"),
            (
                "peran_ingesti",
                f"delete from karantina.dokumen_sumber where id = '{_DOK_037}'",
                "ingesti tidak mengeluarkan dokumen",
            ),
            (
                "peran_ingesti",
                "update karantina.penerimaan set judul = 'x' where false",
                "penerimaan tambah-saja",
            ),
            (
                "peran_ingesti",
                "insert into korpus.dokumen_sumber (id, isi) values ('x', '{}'::jsonb)",
                "R-01 — tidak ada jalan langsung ke korpus",
            ),
            (
                "peran_verifikasi",
                "insert into karantina.dokumen_sumber (id, isi) values ('x', '{}'::jsonb)",
                "P-2 A — verifikator tidak menaruh bahan",
            ),
            (
                "peran_verifikasi",
                "update karantina.dokumen_sumber set isi = '{}'::jsonb where false",
                "P-2 A — verifikator tidak menyunting bahan yang dinilainya",
            ),
            ("peran_verifikasi", _terima_sql(id_dokumen="dok-037-v"), "penerimaan milik ingesti"),
            (
                "peran_verifikasi",
                "update karantina.jejak_area set alasan = 'x' where false",
                "jejak tambah-saja",
            ),
            (
                "peran_verifikasi",
                "delete from karantina.jejak_area where false",
                "jejak tambah-saja",
            ),
            (
                "peran_verifikasi",
                "delete from karantina.tinjauan_temuan where false",
                "tinjauan tambah-saja",
            ),
            (
                "peran_penarikan_dokumen",
                "select teks from indeks_utama.segmen_teks",
                "penarikan tidak membaca teks segmen",
            ),
            (
                "peran_penarikan_dokumen",
                "select isi from karantina.dokumen_sumber",
                "penarikan tidak membaca karantina",
            ),
            (
                "peran_penarikan_dokumen",
                "insert into korpus.dokumen_sumber (id, isi) values ('x', '{}'::jsonb)",
                "penarikan hanya mengurangi korpus",
            ),
            (
                "peran_penarikan_dokumen",
                "insert into indeks_utama.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
                "anonimisasi_terverifikasi, penanda_bagian) values "
                "('s', 'd', 't', 'terbuka', true, 'Pasal 1')",
                "penarikan tidak menambah segmen",
            ),
            (
                "peran_penarikan_dokumen",
                "select * from karantina.temuan_pola",
                "penarikan tidak membaca temuan",
            ),
            (
                "peran_penjawaban",
                "select * from karantina.penerimaan",
                "C-03 — penjawab tidak menjangkau catatan karantina",
            ),
            (
                "peran_pembaca_sumber",
                "select * from karantina.jejak_area",
                "C-03 — pembaca sumber tidak menjangkau jejak karantina",
            ),
        )
    ],
    *[
        (peran, "smart_coaching_pseudonim", "select 1", "C-05 — tanpa basis data pseudonim")
        for peran in ("peran_ingesti", "peran_penarikan_dokumen")
    ],
]


@pytest.mark.parametrize(("peran", "basis_data", "kueri", "sebab"), DITOLAK_INGESTI)
def test_peladen_menolak_hak_ingesti(
    basis_data_siap: None, peran: str, basis_data: str, kueri: str, sebab: str
) -> None:
    hasil = _psql(peran, basis_data, "-c", kueri)
    assert hasil.returncode != 0, sebab
    assert "permission denied" in hasil.stderr, (
        f"ditolak karena sebab lain, bukan hak akses — {sebab}: {hasil.stderr.strip()}"
    )


def test_hak_peran_dokumen_persis_di_seluruh_skema(basis_data_siap: None) -> None:
    """M-1: `GRANT INSERT ON karantina.dokumen_sumber TO peran_verifikasi`.
    M-2: `GRANT SELECT (isi) ON karantina.dokumen_sumber TO peran_ingesti`.

    Ketiga peran dokumen di seluruh skema bagi ingesti dan penarikan; di skema
    karantina bagi verifikator — hak korpus dan indeksnya milik fitur 024."""
    tabel = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select grantee || ':' || table_schema || '.' || table_name || ':' "
        "|| string_agg(privilege_type, ',' order by privilege_type) "
        "from information_schema.role_table_grants "
        "where grantee in ('peran_ingesti', 'peran_penarikan_dokumen') "
        "or (grantee = 'peran_verifikasi' and table_schema = 'karantina') "
        "group by grantee, table_schema, table_name order by 1",
    )
    assert tabel.stdout.split() == [
        "peran_ingesti:karantina.dokumen_sumber:INSERT",
        "peran_ingesti:karantina.penerimaan:INSERT",
        "peran_ingesti:karantina.temuan_pola:INSERT",
        "peran_penarikan_dokumen:indeks_metadata.segmen_teks:DELETE",
        "peran_penarikan_dokumen:indeks_utama.segmen_teks:DELETE",
        "peran_penarikan_dokumen:karantina.dokumen_sumber:INSERT",
        "peran_penarikan_dokumen:karantina.jejak_area:INSERT",
        "peran_penarikan_dokumen:korpus.dokumen_sumber:DELETE,SELECT",
        "peran_verifikasi:karantina.dokumen_sumber:DELETE,SELECT",
        "peran_verifikasi:karantina.jejak_area:INSERT,SELECT",
        "peran_verifikasi:karantina.penerimaan:SELECT",
        "peran_verifikasi:karantina.temuan_pola:SELECT",
        "peran_verifikasi:karantina.tinjauan_temuan:INSERT,SELECT",
    ]
    kolom = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select a.rolname || ':' || n.nspname || '.' || c.relname || ':' || x.privilege_type "
        "|| ':' || string_agg(att.attname, ',' order by att.attname) "
        "from pg_attribute att join pg_class c on c.oid = att.attrelid "
        "join pg_namespace n on n.oid = c.relnamespace "
        "cross join lateral aclexplode(att.attacl) x "
        "join pg_roles a on a.oid = x.grantee "
        "where att.attacl is not null "
        "and (a.rolname in ('peran_ingesti', 'peran_penarikan_dokumen') "
        "or (a.rolname = 'peran_verifikasi' and n.nspname = 'karantina')) "
        "group by a.rolname, n.nspname, c.relname, x.privilege_type order by 1",
    )
    assert kolom.stdout.split() == [
        "peran_ingesti:karantina.dokumen_sumber:SELECT:id",
        "peran_ingesti:karantina.dokumen_sumber:UPDATE:disimpan_pada,isi",
        "peran_ingesti:karantina.penerimaan:SELECT:nomor",
        "peran_ingesti:korpus.dokumen_sumber:SELECT:id",
        "peran_penarikan_dokumen:indeks_metadata.segmen_teks:SELECT:id_dokumen",
        "peran_penarikan_dokumen:indeks_utama.segmen_teks:SELECT:id_dokumen",
        "peran_penarikan_dokumen:karantina.penerimaan:SELECT:id_dokumen,nomor",
    ]


def test_hak_bawaan_karantina_tanpa_tulis_bagi_verifikator(basis_data_siap: None) -> None:
    """P-2 A berlaku juga bagi tabel karantina yang dibuat kelak: hak bawaan
    skema tidak lagi memberi verifikator tambah maupun ubah."""
    hasil = _psql(
        PENGELOLA,
        "smart_coaching",
        "-c",
        "select string_agg(x.privilege_type, ',' order by x.privilege_type) "
        "from pg_default_acl d join pg_namespace n on n.oid = d.defaclnamespace "
        "cross join lateral aclexplode(d.defaclacl) x "
        "join pg_roles a on a.oid = x.grantee "
        "where n.nspname = 'karantina' and d.defaclobjtype = 'r' "
        "and a.rolname = 'peran_verifikasi'",
    )
    assert hasil.stdout.split() == ["SELECT"]


def test_peran_dokumen_berjalan_pada_haknya(basis_data_siap: None) -> None:
    """TK-64, TK-83: tiap peran tersambung sendiri dan menjalankan perintahnya —
    terima, tinjau, setujui, tolak, cabut — dengan pernyataan berbentuk T-4.

    M-3: `DELETE` atas karantina dicabut dari verifikator — `setujui` merah."""
    _jalan("peran_ingesti", _terima_sql())
    _jalan("peran_ingesti", _terima_sql())  # unggahan ulang selama di karantina
    for kueri in (
        f"select nomor, judul, samaran from karantina.penerimaan where id_dokumen = '{_DOK_037}'",
        "select pola, mulai, akhir, kutipan from karantina.temuan_pola",
        f"select isi from karantina.dokumen_sumber where id = '{_DOK_037}'",
        f"select id from korpus.dokumen_sumber where id = '{_DOK_037}'",
        _tinjau_sql(),
        _setujui_sql(),
    ):
        _jalan("peran_verifikasi", kueri)
    for kueri in (
        "insert into indeks_utama.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
        "anonimisasi_terverifikasi, penanda_bagian) values "
        f"('seg-037-u', '{_DOK_037}', 'Rapat pleno.', 'terbuka', true, 'Bagian 1')",
        "insert into indeks_metadata.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
        "anonimisasi_terverifikasi, penanda_bagian) values "
        f"('seg-037-m', '{_DOK_037}', 'Abstrak.', 'tertutup', true, 'Abstrak')",
    ):
        _jalan(PENGELOLA, kueri)

    # TK-85 A: selama di korpus, unggahan ulang tidak menulis apa pun.
    _jalan("peran_ingesti", _terima_sql())
    _jalan("peran_penarikan_dokumen", _cabut_sql())

    # Dokumen lain: ditolak, lalu persetujuannya dicabut selagi di karantina.
    _jalan("peran_ingesti", _terima_sql(id_dokumen="dok-037-b"))
    _jalan("peran_verifikasi", _jejak_sql(id_dokumen="dok-037-b"))
    _jalan("peran_penarikan_dokumen", _cabut_sql(id_dokumen="dok-037-b"))

    hasil = _psql(
        PENGELOLA,
        "smart_coaching",
        "-At",
        "-c",
        "select string_agg(r, ' ' order by r) from ("
        f"  select 'penerimaan:' || count(*) r from karantina.penerimaan where id_dokumen = '{_DOK_037}'"
        "  union all select 'segmen:' || ("
        f"    (select count(*) from indeks_utama.segmen_teks where id_dokumen = '{_DOK_037}')"
        f"    + (select count(*) from indeks_metadata.segmen_teks where id_dokumen = '{_DOK_037}'))"
        "  union all select 'korpus:' || count(*) from korpus.dokumen_sumber "
        f"    where id = '{_DOK_037}'"
        "  union all select 'karantina:' || count(*) from karantina.dokumen_sumber "
        f"    where id = '{_DOK_037}'"
        "  union all select 'jejak:' || string_agg(putusan || '/' || dari_area, ',' order by id) "
        "    from karantina.jejak_area"
        ") s",
    )
    assert hasil.stdout.split() == [
        "jejak:setujui/karantina,cabut_persetujuan/korpus,tolak/karantina,"
        "cabut_persetujuan/karantina",
        "karantina:1",
        "korpus:0",
        "penerimaan:2",
        "segmen:0",
    ]


def test_batasan_tabel_ingesti(basis_data_siap: None) -> None:
    """M-11: batasan pola pelaku dihapus — merah di sini."""
    _jalan(PENGELOLA, _terima_sql(id_dokumen="dok-037-c"))
    for kueri, sebab in (
        (_terima_sql(id_dokumen="dok-037-d", jenis="buku"), "jenis di luar JenisSumber"),
        (_terima_sql(id_dokumen="dok-037-d", tingkat="rahasia"), "tingkat di luar daftar"),
        (_terima_sql(id_dokumen="dok-037-d", persetujuan="lisan"), "persetujuan di luar daftar"),
        (_terima_sql(id_dokumen="dok-037-d", tahun=1900), "tahun sebelum 1945"),
        (_terima_sql(id_dokumen="dok-037-d", penerima="Budi Santoso"), "P-6 A — nama orang"),
        (
            _terima_sql(id_dokumen="dok-037-d", samaran='{"nik": 1}'),
            "samaran wajib keenam jenis",
        ),
        (
            _terima_sql(id_dokumen="dok-037-d", samaran=_SAMARAN.replace('"nik": 1', '"nik": -1')),
            "jumlah samaran bukan bilangan cacah",
        ),
        (
            _terima_sql(id_dokumen="dok-037-d", samaran=_SAMARAN.replace("1", '"3201"')),
            "samaran tidak memuat nilai",
        ),
        (_jejak_sql(id_dokumen="dok-037-c", putusan="hapus"), "putusan di luar PutusanGerbang"),
        (_jejak_sql(id_dokumen="dok-037-c", pelaku="vrf_001"), "P-6 A — pola kode tim"),
        (_jejak_sql(id_dokumen="dok-037-c", alasan=" "), "alasan wajib"),
        (_jejak_sql(id_dokumen="dok-037-c", ke="korpus"), "tolak tidak memindahkan ke korpus"),
        (
            _jejak_sql(id_dokumen="dok-037-c", putusan="setujui"),
            "setujui selalu karantina ke korpus",
        ),
        (
            _jejak_sql(id_dokumen="dok-037-c", putusan="cabut_persetujuan", ke="korpus"),
            "pencabutan tidak memasukkan ke korpus",
        ),
        (_tinjau_sql(id_dokumen="dok-037-c", peninjau="Siti"), "P-6 A — peninjau"),
        (
            "insert into karantina.temuan_pola (nomor_penerimaan, pola, mulai, akhir, kutipan) "
            f"values ({_nomor('dok-037-c')}, 'pola', 9, 3, '')",
            "rentang terbalik",
        ),
    ):
        hasil = _psql(PENGELOLA, "smart_coaching", "-c", kueri)
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"

    hasil = _psql(PENGELOLA, "smart_coaching", "-c", _jejak_sql(id_dokumen="dok-037-tak-dikenal"))
    assert "violates not-null constraint" in hasil.stderr, f"jejak tanpa penerimaan: {hasil.stderr}"


def test_daftar_nilai_batasan_ingesti_sama_dengan_enumnya() -> None:
    """Daftar nilai batasan dibaca dari enumnya, bukan dipercaya."""
    import re

    from src.ingest.dokumen import StatusPersetujuan, TingkatKerahasiaan
    from src.ingest.peringkat import JenisSumber
    from src.kamus.gerbang import PutusanGerbang
    from src.nlp.anonimisasi.pola import JENIS
    from src.penyimpanan.area import Area

    sql = (BERKAS / "15-ingesti.sql").read_text(encoding="utf-8")

    def daftar(penanda: str) -> set[str]:
        mulai = sql.index(penanda)
        return set(re.findall(r"'([a-z_]+)'", sql[mulai : sql.index(")", mulai)]))

    assert daftar("jenis IN") == {j.value for j in JenisSumber}
    assert daftar("tingkat_kerahasiaan IN") == {t.value for t in TingkatKerahasiaan}
    assert daftar("status_persetujuan_pemilik IN") == {s.value for s in StatusPersetujuan}
    assert daftar("putusan IN") == {p.value for p in PutusanGerbang}
    assert daftar("dari_area IN") == {a.value for a in Area}
    assert daftar("samaran ?& ARRAY[") == set(JENIS)
