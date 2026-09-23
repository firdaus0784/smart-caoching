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

from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import Penyemat
from src.penyimpanan.sambungan import SambunganAktif
from src.penyimpanan.skema_indeks import (
    KOLOM_VEKTOR_SEMATAN,
    SKEMA_INDEKS,
    TABEL_SEGMEN,
    GalatDimensiVektor,
    bilangan_dari_baris,
    pastikan_dimensi_cocok,
    untai_vektor,
)
from src.rag.pengambilan.kandidat import (
    HasilSumber,
    Kandidat,
    SumberKandidat,
    urutkan_kandidat,
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
        # Angka dan nama diserahkan sebagai nilai, bukan objek `Penyemat`:
        # `src/penyimpanan/` lapisan di bawah dan tidak memanggil `llm`.
        await pastikan_dimensi_cocok(
            sambungan,
            dimensi_model=penyemat.dimensi,
            nama_model=penyemat.versi.nama_model,
            indeks_tujuan=indeks_tujuan,
        )
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
            f"FROM {SKEMA_INDEKS[self._indeks_tujuan]}.{TABEL_SEGMEN} "
            f"WHERE {KOLOM_VEKTOR_SEMATAN} IS NOT NULL "
            f"ORDER BY {KOLOM_VEKTOR_SEMATAN} <=> $1::vector "
            f"LIMIT $2",
            untai_vektor(vektor),
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
            f"SELECT count(*) AS jumlah FROM {SKEMA_INDEKS[self._indeks_tujuan]}.{TABEL_SEGMEN} "
            f"WHERE {KOLOM_VEKTOR_SEMATAN} IS NULL"
        )
        return bilangan_dari_baris(
            baris,
            "jumlah",
            f"tabel {SKEMA_INDEKS[self._indeks_tujuan]}.{TABEL_SEGMEN} tidak dapat dihitung",
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
