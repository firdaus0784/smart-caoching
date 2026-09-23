"""Fakta fisik indeks vektor pada peladen — R-04 dan R-08 fitur 019, C-02, ADR-05, TK-61.

Nama skema, nama tabel, nama kolom, dan pembacaan katalog. Ia **tidak**
mengetahui cara mencari maupun cara menyemat; keduanya milik lapisan di atas.

## Mengapa modul ini ada, dan mengapa baru sekarang

Seluruh isinya semula tinggal pada `src/rag/pengambilan/vektor.py`. Selama
hanya `rag` yang membacanya, letak itu tidak menimbulkan persoalan. Fitur 026
menambahkan sisi **penulisan** di `src/ingest/`, dan `baca_arah()` menegaskan
`ingest → ['llm', 'nlp']` dengan `rag` **bukan** lapisan terbuka — sehingga
jalur penyematan tidak dapat menjangkaunya.

Menyalinnya ditolak oleh uraian `SKEMA_INDEKS` sendiri: nama skema yang
tertulis di dua tempat akan berbeda di salah satunya. Karena itu ia
**dipindahkan**, bukan digandakan, ke lapisan terbuka yang memang memiliki
fakta penyimpanan — sejajar dengan `SKEMA` bagi `Area` yang sudah tinggal di
`postgres.py` sejak fitur 024.

## `pastikan_dimensi_cocok` menerima angka, bukan `Penyemat`

`Penyemat` tinggal di `src/llm/`. `src/penyimpanan/` lapisan di bawah dan
tidak memanggil `llm`; menerima objeknya akan membalik arah itu. Ia karena itu
menerima **dimensi dan nama model sebagai nilai**, dan pemanggil yang
memetakannya — satu baris pada masing-masing dari dua pemanggil, ganti satu
tepi arah yang tidak boleh ada.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final

from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.sambungan import SambunganAktif

SKEMA_INDEKS: Final[dict[IndeksTujuan, str]] = {
    IndeksTujuan.UTAMA: "indeks_utama",
    IndeksTujuan.METADATA: "indeks_metadata",
}
"""Nama skema per indeks tujuan — `perkakas/basis_data/02-skema-dan-hak.sql`.

Bukan dirakit dari `indeks_tujuan.value` saat jalan. Nama skema yang dirakit
akan berbeda dari yang tertulis pada berkas persiapan pada hari salah satunya
berubah, dan yang menemukannya bersamanya adalah kueri yang sudah berjalan di
lingkungan sungguhan. Bentuk yang sama dengan `SKEMA` pada `postgres.py`.
"""

TABEL_SEGMEN: Final = "segmen_teks"

KOLOM_VEKTOR_SEMATAN: Final = "vektor_sematan"
"""Nama kolom vektor — `docs/D04.md` Bagian 7.2.

Fitur 019 menamainya `vektor`; D-04 sudah menetapkan `vektor_sematan` sebelum
proyek ini berjalan. Diluruskan pada T-1 fitur 026 (TK-60).
"""

KOLOM_VERSI_SEMATAN: Final = "versi_model_sematan"
"""Versi model yang menghasilkan vektor pada baris itu — D-04 Bagian 7.2."""


class GalatDimensiVektor(Exception):
    """Dimensi penyemat tidak cocok dengan dimensi kolom.

    Bukan galat yang menghadapi pengguna: ia menghadapi orang yang memasang
    sistem, dan karena itu pesannya justru wajib menyebut angka dan nama.
    """


def bilangan_dari_baris(baris: Mapping[str, object] | None, kolom: str, bila_kosong: str) -> int:
    """Baca satu bilangan dari baris peladen, atau tolak dengan sebab.

    **Satu penjagaan, dipakai setiap kueri yang mengembalikan bilangan.**
    Sebelumnya tiap kueri membawa penjagaannya sendiri, dan dua salinan aturan
    yang sama akan berselisih pada hari salah satunya disunting — yang
    disunting bukan yang diperiksa.

    Cabang "bukan bilangan" tidak dapat dipicu PostgreSQL 16 mana pun; ia
    menjaga **bentuk** keluaran, bukan nilainya, dan diuji lewat sambungan
    buatan. Penjagaan yang tidak pernah dijalankan adalah penjagaan yang belum
    diketahui bekerja atau tidak.
    """
    if baris is None:
        raise GalatDimensiVektor(bila_kosong)
    nilai = baris[kolom]
    if not isinstance(nilai, int):
        raise GalatDimensiVektor(
            f"peladen mengembalikan {kolom} bertipe {type(nilai).__name__}, "
            "bukan bilangan — bentuk keluarannya berubah dan kueri ini perlu ditinjau"
        )
    return nilai


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
        SKEMA_INDEKS[indeks_tujuan],
        TABEL_SEGMEN,
        KOLOM_VEKTOR_SEMATAN,
    )
    return bilangan_dari_baris(
        baris,
        "dimensi",
        f"kolom {KOLOM_VEKTOR_SEMATAN!r} tidak ada pada "
        f"{SKEMA_INDEKS[indeks_tujuan]}.{TABEL_SEGMEN} — jalankan "
        "perkakas/basis_data/05-kolom-vektor.sql lebih dulu",
    )


async def pastikan_dimensi_cocok(
    sambungan: SambunganAktif,
    *,
    dimensi_model: int,
    nama_model: str,
    indeks_tujuan: IndeksTujuan,
) -> None:
    """Tolak ketidakcocokan **saat penyusunan** — R-08 fitur 019.

    Pesannya menyebut kedua angka dan nama modelnya. Galat pemasangan yang
    hanya menyebut satu sisi memaksa yang membacanya menebak sisi mana yang
    keliru, dan tebakan itu dilakukan di lingkungan sungguhan.
    """
    dari_kolom = await dimensi_kolom(sambungan, indeks_tujuan)
    if dari_kolom != dimensi_model:
        raise GalatDimensiVektor(
            f"model {nama_model!r} berdimensi {dimensi_model}, sedangkan kolom "
            f"{SKEMA_INDEKS[indeks_tujuan]}.{TABEL_SEGMEN}.{KOLOM_VEKTOR_SEMATAN} "
            f"berdimensi {dari_kolom}. Jalankan ulang "
            f"perkakas/basis_data/05-kolom-vektor.sql dengan -v dimensi="
            f"{dimensi_model}, atau pasang model yang sesuai"
        )


def untai_vektor(vektor: Sequence[float]) -> str:
    """Bentuk untai `pgvector`: `[a,b,c]`.

    Dikirim sebagai untai lalu dicor `::vector` pada kueri, bukan lewat tipe
    asli — `asyncpg` tidak mengenal tipe ekstensi tanpa pendaftaran pengodek,
    dan pendaftaran itu menuntut sambungan yang sudah hidup.
    """
    return "[" + ",".join(repr(float(n)) for n in vektor) + "]"
