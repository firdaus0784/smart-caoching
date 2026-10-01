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
    assert hasil.stdout.split() == ["giliran:INSERT,SELECT", "percakapan:INSERT,SELECT"]


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
    "values ('ks-901', 'psd_00000000000000aa', 'pengguna', now(), 'scrypt$x')"
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
                "update akun.pengguna set pseudonim = 'psd_00000000000000bb' where false",
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
                "update akun.pengguna set pseudonim = 'psd_00000000000000bb' where false",
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
        "peran_autentikasi:sesi:INSERT,SELECT",
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
        "peran_autentikasi:sesi:UPDATE:dicabut_pada,terakhir_aktif",
        "peran_pengelola_akun:pengguna:SELECT:id,status_aktif",
        "peran_pengelola_akun:pengguna:UPDATE:ditahan_sampai,gagal_beruntun,status_aktif,turunan_sandi",
        "peran_pengelola_akun:sesi:SELECT:dicabut_pada,id_pengguna",
        "peran_pengelola_akun:sesi:UPDATE:dicabut_pada",
    ]


def test_batasan_tabel_akun(basis_data_siap: None) -> None:
    """Lapis kedua sesudah perkakas: pola nama, pseudonim, dan peran."""
    for nilai, sebab in (
        ("('Budi Santoso', 'psd_00000000000000c1', 'pengguna')", "nama orang sebagai id"),
        ("('ks-902', '3201010101010001', 'pengguna')", "NIK sebagai pseudonim"),
        ("('ks-903', 'psd_00000000000000c3', 'kepala')", "peran di luar D-14"),
    ):
        hasil = _psql(
            "peran_pengelola_akun",
            "smart_coaching",
            "-c",
            "insert into akun.pengguna (id, pseudonim, peran, tanggal_dibuat, turunan_sandi) "
            f"values {nilai[:-1]}, now(), 'scrypt$x')",
        )
        assert "violates check constraint" in hasil.stderr, f"{sebab}: {hasil.stderr}"
