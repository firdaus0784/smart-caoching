"""Pencocokan dimensi kolom vektor — T-4 fitur 019, R-08.

Tipe menjaga *penyemat mana dipakai sumber mana*. Ia **tidak** dapat menjaga
*dimensi penyemat sama dengan dimensi kolom*: keduanya bilangan biasa, dan
bilangan yang kebetulan berbeda terbaca sah oleh pemeriksa tipe mana pun.

Ketidakcocokannya juga **tidak menghasilkan galat yang jelas** bila dibiarkan
sampai kueri: `pgvector` menolak perbandingan antardimensi dengan pesan yang
menyebut angka, bukan menyebut penyemat mana yang salah pasang — dan yang
membacanya sudah berada di lingkungan sungguhan.

## Mengapa penyusunannya lewat fungsi, bukan `__init__`

Pemeriksaan ini menanyakan basis data, dan `__init__` tidak dapat menunggu.
Pilihan yang tersedia hanya tiga: memeriksa saat kueri pertama (terlambat),
menyimpan janji dan menunggunya belakangan (ketidakcocokan muncul di tempat
yang jauh dari sebabnya), atau **menyusun lewat fungsi asinkron**.

Yang ketiga dipilih. Ia membuat "ditolak saat penyusunan" benar-benar berarti
saat penyusunan — dan pemanggil yang lupa memanggilnya tidak memperoleh objek
sama sekali, bukan memperoleh objek yang belum diperiksa.

## Dimensi dinyatakan satu tempat, dan tempat itu basis data

Bukan tetapan pada Python. Kolom `vector(N)` sudah membawa N-nya, dan
menuliskannya lagi pada kode menghasilkan dua sumber kebenaran yang akan
berbeda pada hari salah satunya disunting — dan yang berbeda adalah yang tidak
diperbarui. Berkas migrasi `05-kolom-vektor.sql` menuntut dimensinya diberikan
saat dijalankan justru agar tidak ada nilai bawaan yang diam-diam terpakai.
"""

from __future__ import annotations

from typing import Final

from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import Penyemat
from src.penyimpanan.sambungan import SambunganAktif

SKEMA: Final[dict[IndeksTujuan, str]] = {
    IndeksTujuan.UTAMA: "indeks_utama",
    IndeksTujuan.METADATA: "indeks_metadata",
}
"""Nama skema per indeks tujuan — `perkakas/basis_data/02-skema-dan-hak.sql`.

Bukan dirakit dari `indeks_tujuan.value` saat jalan. Nama skema yang dirakit
dari nilai enum ikut berubah diam-diam ketika enum berubah, dan yang berubah
bersamanya adalah kueri yang sudah berjalan di lingkungan sungguhan. Bentuk
yang sama dengan `SKEMA` pada `src/penyimpanan/postgres.py`.
"""

TABEL: Final = "segmen_teks"
KOLOM_VEKTOR: Final = "vektor"


class GalatDimensiVektor(Exception):
    """Dimensi penyemat tidak cocok dengan dimensi kolom.

    Bukan galat yang menghadapi pengguna: ia menghadapi orang yang memasang
    sistem, dan karena itu pesannya justru wajib menyebut angka dan nama.
    """


async def dimensi_kolom(sambungan: SambunganAktif, indeks_tujuan: IndeksTujuan) -> int:
    """Dimensi kolom vektor sebagaimana tercatat peladen.

    Dibaca dari katalog, bukan dari tetapan mana pun pada kode. `atttypmod`
    menyimpan dimensi `vector(N)` apa adanya.
    """
    baris = await sambungan.fetchrow(
        "SELECT a.atttypmod AS dimensi "
        "FROM pg_attribute a "
        "JOIN pg_class c ON c.oid = a.attrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = $1 AND c.relname = $2 AND a.attname = $3",
        SKEMA[indeks_tujuan],
        TABEL,
        KOLOM_VEKTOR,
    )
    if baris is None:
        raise GalatDimensiVektor(
            f"kolom {KOLOM_VEKTOR!r} tidak ada pada {SKEMA[indeks_tujuan]}.{TABEL} — "
            "jalankan perkakas/basis_data/05-kolom-vektor.sql lebih dulu"
        )
    mentah = baris["dimensi"]
    if not isinstance(mentah, int):
        raise GalatDimensiVektor(
            f"katalog peladen mengembalikan dimensi bertipe {type(mentah).__name__}, "
            "bukan bilangan — bentuk katalog berubah dan kueri ini perlu ditinjau"
        )
    return mentah


async def pastikan_dimensi_cocok(
    sambungan: SambunganAktif, penyemat: Penyemat, indeks_tujuan: IndeksTujuan
) -> None:
    """Tolak ketidakcocokan **saat penyusunan** — R-08.

    Pesannya menyebut kedua angka dan nama penyematnya. Galat pemasangan yang
    hanya menyebut satu sisi memaksa yang membacanya menebak sisi mana yang
    keliru, dan tebakan itu dilakukan di lingkungan sungguhan.
    """
    dari_kolom = await dimensi_kolom(sambungan, indeks_tujuan)
    if dari_kolom != penyemat.dimensi:
        raise GalatDimensiVektor(
            f"penyemat {penyemat.versi.nama_model!r} berdimensi {penyemat.dimensi}, "
            f"sedangkan kolom {SKEMA[indeks_tujuan]}.{TABEL}.{KOLOM_VEKTOR} "
            f"berdimensi {dari_kolom}. Jalankan ulang "
            f"perkakas/basis_data/05-kolom-vektor.sql dengan -v dimensi="
            f"{penyemat.dimensi}, atau pasang penyemat yang sesuai"
        )
