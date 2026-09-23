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

from collections.abc import Mapping, Sequence
from typing import Final

from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import Penyemat
from src.penyimpanan.sambungan import SambunganAktif
from src.rag.pengambilan.kandidat import (
    HasilSumber,
    Kandidat,
    SumberKandidat,
    urutkan_kandidat,
)

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
KOLOM_VEKTOR_SEMATAN: Final = "vektor_sematan"
"""Nama kolom vektor — `docs/D04.md` Bagian 7.2.

Fitur 019 menamainya `vektor`; D-04 sudah menetapkan `vektor_sematan`
sebelum proyek ini berjalan. Diluruskan pada T-1 fitur 026 (TK-60).
"""

KOLOM_VERSI_SEMATAN: Final = "versi_model_sematan"
"""Versi model yang menghasilkan vektor pada baris itu — D-04 Bagian 7.2."""


class GalatDimensiVektor(Exception):
    """Dimensi penyemat tidak cocok dengan dimensi kolom.

    Bukan galat yang menghadapi pengguna: ia menghadapi orang yang memasang
    sistem, dan karena itu pesannya justru wajib menyebut angka dan nama.
    """


def _bilangan(baris: Mapping[str, object] | None, kolom: str, bila_kosong: str) -> int:
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
        SKEMA[indeks_tujuan],
        TABEL,
        KOLOM_VEKTOR_SEMATAN,
    )
    return _bilangan(
        baris,
        "dimensi",
        f"kolom {KOLOM_VEKTOR_SEMATAN!r} tidak ada pada {SKEMA[indeks_tujuan]}.{TABEL} — "
        "jalankan perkakas/basis_data/05-kolom-vektor.sql lebih dulu",
    )


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
            f"sedangkan kolom {SKEMA[indeks_tujuan]}.{TABEL}.{KOLOM_VEKTOR_SEMATAN} "
            f"berdimensi {dari_kolom}. Jalankan ulang "
            f"perkakas/basis_data/05-kolom-vektor.sql dengan -v dimensi="
            f"{penyemat.dimensi}, atau pasang penyemat yang sesuai"
        )


class SumberVektor(SumberKandidat):
    """Sisi semantik pengambilan hibrida — ADR-03, R-01, R-03.

    Satu pelaksana baru pada kontrak yang sudah ada. `ambil_hibrida` tidak
    berubah sama sekali karenanya, dan itu ukuran keberhasilan fitur 019.

    ## Disusun lewat `susun`, bukan lewat pemanggilan langsung

    Pencocokan dimensi menanyakan basis data, dan `__init__` tidak dapat
    menunggu. Pemanggil yang menyusun langsung memperoleh objek yang **belum
    diperiksa**; `susun` membuat pemeriksaan itu tidak dapat dilewati.

    ## Mengapa skor berbentuk `2 - jarak`

    `Kandidat.skor` menolak nilai negatif — BM25 dan RRF keduanya tak-negatif,
    dan skor negatif berarti perhitungannya keliru. Jarak kosinus `<=>` berada
    pada [0, 2], sehingga `2 - jarak` tak-negatif **dan** mempertahankan
    urutannya: makin dekat, makin besar.

    Bukan `1 - jarak`, yang bernilai negatif bagi vektor berlawanan arah dan
    akan ditolak justru pada kandidat yang paling tidak relevan.

    ## Segmen tanpa vektor

    Dikeluarkan lewat `WHERE vektor IS NOT NULL`. Segmen yang sudah terindeks
    leksikal tetapi belum disematkan adalah keadaan sah selama penyematan
    berjalan bertahap; yang tidak sah adalah ia muncul sebagai kandidat dengan
    jarak yang tidak terdefinisi.
    """

    def __init__(
        self,
        *,
        sambungan: SambunganAktif,
        penyemat: Penyemat,
        indeks_tujuan: IndeksTujuan,
        versi_indeks: str,
    ) -> None:
        self._sambungan = sambungan
        self._penyemat = penyemat
        self._indeks_tujuan = indeks_tujuan
        self._versi_indeks = versi_indeks

    @classmethod
    async def susun(
        cls,
        *,
        sambungan: SambunganAktif,
        penyemat: Penyemat,
        indeks_tujuan: IndeksTujuan,
        versi_indeks: str,
    ) -> SumberVektor:
        """Susun sesudah dimensi terbukti cocok — R-08."""
        await pastikan_dimensi_cocok(sambungan, penyemat, indeks_tujuan)
        return cls(
            sambungan=sambungan,
            penyemat=penyemat,
            indeks_tujuan=indeks_tujuan,
            versi_indeks=versi_indeks,
        )

    @property
    def nama(self) -> str:
        return "vektor"

    @property
    def indeks_tujuan(self) -> IndeksTujuan:
        return self._indeks_tujuan

    @property
    def versi_indeks(self) -> str:
        return self._versi_indeks

    async def cari(self, kueri: str, *, batas: int) -> HasilSumber:
        if not kueri.strip():
            raise ValueError("kueri kosong tidak dapat dicari")

        vektor = (await self._penyemat.sematkan([kueri]))[0]
        tanpa_vektor = await self._jumlah_tanpa_vektor()
        baris = await self._sambungan.fetch(
            f"SELECT id_segmen, 2 - ({KOLOM_VEKTOR_SEMATAN} <=> $1::vector) AS skor "
            f"FROM {SKEMA[self._indeks_tujuan]}.{TABEL} "
            f"WHERE {KOLOM_VEKTOR_SEMATAN} IS NOT NULL "
            f"ORDER BY {KOLOM_VEKTOR_SEMATAN} <=> $1::vector "
            f"LIMIT $2",
            _untai_vektor(vektor),
            batas,
        )
        return HasilSumber(
            nama_sumber=self.nama,
            versi_indeks=self._versi_indeks,
            peringkat=urutkan_kandidat(
                Kandidat(id_segmen=str(b["id_segmen"]), skor=_angka(b["skor"])) for b in baris
            ),
            versi_penyemat=self._penyemat.versi,
            segmen_tanpa_vektor=tanpa_vektor,
        )

    async def _jumlah_tanpa_vektor(self) -> int:
        """Segmen yang ada pada indeks tetapi belum disematkan — R-06 T-6.

        Kueri tersendiri, bukan disisipkan ke kueri pencarian. Kueri gabungan
        kehilangan angkanya tepat ketika pencarian tidak menemukan apa-apa —
        dan keadaan "nol hasil dengan banyak segmen belum tersemat" justru
        yang paling perlu terbaca.

        Diakui terbuka: antara kedua kueri, isi tabel dapat berubah. Angka ini
        keterangan keadaan indeks, bukan bagian dari hasil pencarian, sehingga
        selisih sesaat tidak mengubah jawaban yang diberikan.
        """
        baris = await self._sambungan.fetchrow(
            f"SELECT count(*) AS jumlah FROM {SKEMA[self._indeks_tujuan]}.{TABEL} "
            f"WHERE {KOLOM_VEKTOR_SEMATAN} IS NULL"
        )
        return _bilangan(
            baris,
            "jumlah",
            f"tabel {SKEMA[self._indeks_tujuan]}.{TABEL} tidak dapat dihitung",
        )


def _angka(nilai: object) -> float:
    """Skor dari peladen, dipastikan bilangan.

    `pgvector` mengembalikan `double precision` bagi ungkapan jaraknya, tetapi
    katalog yang berubah bentuk akan menghasilkan sesuatu yang lain — dan
    `float()` atas sesuatu yang lain menghasilkan galat yang menyebut tipe
    Python, bukan menyebut kueri mana yang berubah.
    """
    if not isinstance(nilai, int | float):
        raise GalatDimensiVektor(
            f"peladen mengembalikan skor bertipe {type(nilai).__name__}, bukan bilangan"
        )
    return float(nilai)


def _untai_vektor(vektor: Sequence[float]) -> str:
    """Bentuk untai yang `pgvector` terima — `[0.1,0.2,...]`.

    Dikirim sebagai untai lalu dicor `::vector` pada kueri, bukan lewat tipe
    `asyncpg` khusus. Itu menghindari pendaftaran tipe yang harus diulang pada
    setiap sambungan baru, dan sambungan di sini sengaja berumur pendek.
    """
    return "[" + ",".join(repr(float(n)) for n in vektor) + "]"
