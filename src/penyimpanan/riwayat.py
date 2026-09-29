"""Penyimpan riwayat percakapan — T-3 fitur 028, R-02, R-08, R-12, R-13.

FR-F09: *"Sistem menyimpan riwayat percakapan dan memungkinkan pengguna
melanjutkan sesi sebelumnya."* Bentuknya D-14 Bagian 4.3 dan 5.1; tabelnya
`perkakas/basis_data/06-riwayat.sql`.

## Yang disimpan, dan yang sengaja tidak

Pertanyaan, rujukan `id_pesan`, dan waktu — **tidak pernah tanggapannya**.
Tanggapan yang tersimpan menua: regulasi yang menjadi dasarnya dapat dicabut
sesudah jawaban disusun, dan jawaban lama yang ditampilkan ulang melanggar C-07
tanpa satu galat pun (D-14 Bagian 4.3).

Pemilik berupa **pseudonim**, bukan identitas langsung (C-05). Pemetaannya
tinggal pada basis data yang peran penulis riwayat tidak dapat sambungi.

## Validasi isi tidak di sini, dan itu aturan arah

`src/penyimpanan/` tidak mengimpor `src/api/` maupun `src/nlp/`. Pemeriksaan
data pribadi (KM-03) karena itu dijalankan `Giliran` pada `src/api/`, sebelum
penyimpan dipanggil. Yang diperiksa di sini hanya bentuk yang tabelnya juga
tolak — isian kosong dan waktu tanpa zona — agar kedua pelaksana berperilaku
sama, bukan satu menolak lewat batasan tabel dan yang lain menerima.

## Satu penolakan bagi dua keadaan

Percakapan milik pemilik lain dan percakapan yang tidak dikenal menghasilkan
`PercakapanTidakAda` yang **sama persis** (R-02, R-03). Galat yang membedakan
keduanya memberi tahu penebak bahwa tebakannya mengenai sesuatu.

## Tambah-saja

Permukaannya tiga: `catat`, `daftar`, `baca`. Tidak ada yang mengubah maupun
menghapus — dan pada PostgreSQL ketiadaan itu ditegakkan peladen: `peran_riwayat`
hanya diberi `SELECT` dan `INSERT` (T-2). Penarikan data pengguna (NFR-09)
kelak menjadi tindakan tersendiri dengan peran tersendiri.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Protocol

from src.penyimpanan.sambungan import SambunganAktif

PERAN_RIWAYAT: Final = "peran_riwayat"
"""Peran basis data penulis riwayat — `01-peran-dan-basis-data.sql`, `06-riwayat.sql`.

Tidak ada tipe kredensial tersendiri bagi riwayat. Pemisahannya ditegakkan
peran basis data, bukan objek Python; tipe kredensial yang tidak menegakkan
apa pun hanya penanda, bentuk yang `pseudonim.py` tolak (KB-142).
"""


class PercakapanTidakAda(Exception):
    """Percakapan tidak dikenal **atau** milik pemilik lain — sengaja tak dibedakan."""

    def __init__(self) -> None:
        super().__init__("percakapan tidak ditemukan")


@dataclass(frozen=True)
class BarisGiliran:
    """Satu giliran sebagaimana tersimpan: pertanyaan dan rujukan, tanpa jawaban."""

    pertanyaan: str
    id_pesan: str
    waktu: datetime


class PenyimpanRiwayat(Protocol):
    async def catat(
        self,
        *,
        pemilik: str,
        id_percakapan: uuid.UUID,
        pertanyaan: str,
        id_pesan: str,
        waktu: datetime,
    ) -> None:
        """Tambahkan satu giliran. Percakapan baru terbuka pada giliran pertamanya."""
        ...

    async def daftar(self, *, pemilik: str) -> tuple[uuid.UUID, ...]:
        """Percakapan milik `pemilik`, terbaru lebih dulu (D-14 Bagian 4.3, K-1)."""
        ...

    async def baca(self, *, pemilik: str, id_percakapan: uuid.UUID) -> tuple[BarisGiliran, ...]:
        """Giliran satu percakapan milik `pemilik`, berurutan."""
        ...


def _periksa(pemilik: str, pertanyaan: str, id_pesan: str, waktu: datetime) -> None:
    for nama, nilai in (("pemilik", pemilik), ("pertanyaan", pertanyaan), ("id_pesan", id_pesan)):
        if not nilai.strip():
            raise ValueError(f"{nama} tidak boleh kosong")
    if waktu.tzinfo is None or waktu.utcoffset() is None or waktu.utcoffset().total_seconds():  # type: ignore[union-attr]
        raise ValueError("waktu giliran wajib berzona UTC (KM-01)")


@dataclass
class _PercakapanMemori:
    pemilik: str
    dibuat_pada: datetime
    giliran: list[BarisGiliran]


class RiwayatMemori:
    """Pelaksana di memori — bagi uji dan `make jalan` tanpa basis data.

    **Tidak memenuhi R-13**: riwayat hilang ketika proses berhenti. Itu
    dinyatakan di sini, dan pada keluaran `make jalan` yang memakainya, agar
    tidak ada yang mengira riwayatnya tersimpan.
    """

    def __init__(self) -> None:
        self._percakapan: dict[uuid.UUID, _PercakapanMemori] = {}

    async def catat(
        self,
        *,
        pemilik: str,
        id_percakapan: uuid.UUID,
        pertanyaan: str,
        id_pesan: str,
        waktu: datetime,
    ) -> None:
        _periksa(pemilik, pertanyaan, id_pesan, waktu)
        satu = self._percakapan.setdefault(
            id_percakapan, _PercakapanMemori(pemilik=pemilik, dibuat_pada=waktu, giliran=[])
        )
        if satu.pemilik != pemilik:
            raise PercakapanTidakAda
        satu.giliran.append(BarisGiliran(pertanyaan=pertanyaan, id_pesan=id_pesan, waktu=waktu))

    async def daftar(self, *, pemilik: str) -> tuple[uuid.UUID, ...]:
        milik = [(p.dibuat_pada, i) for i, p in self._percakapan.items() if p.pemilik == pemilik]
        # Terbaru lebih dulu; pengenal sebagai pemutus seri, sama dengan SQL.
        milik.sort(key=lambda b: (-b[0].timestamp(), str(b[1])))
        return tuple(i for _, i in milik)

    async def baca(self, *, pemilik: str, id_percakapan: uuid.UUID) -> tuple[BarisGiliran, ...]:
        satu = self._percakapan.get(id_percakapan)
        if satu is None or satu.pemilik != pemilik:
            raise PercakapanTidakAda
        return tuple(satu.giliran)


_CATAT: Final = """
WITH buka AS (
    INSERT INTO riwayat.percakapan (id_percakapan, pemilik, dibuat_pada)
    VALUES ($1, $2, $5)
    ON CONFLICT (id_percakapan) DO NOTHING
    RETURNING pemilik
), pemilik_sah AS (
    SELECT pemilik FROM buka
    UNION ALL
    SELECT pemilik FROM riwayat.percakapan WHERE id_percakapan = $1
)
INSERT INTO riwayat.giliran (id_percakapan, pertanyaan, id_pesan, waktu)
SELECT $1, $3, $4, $5
WHERE (SELECT pemilik FROM pemilik_sah LIMIT 1) = $2
RETURNING nomor
"""
"""Membuka percakapan, memeriksa pemilik, dan menambah giliran dalam **satu
pernyataan** — atomik tanpa transaksi, yang tidak disediakan `SambunganAktif`.

`buka` memuat baris yang baru dimasukkan pernyataan ini; `riwayat.percakapan`
memuat baris yang sudah ada sebelumnya — potret pernyataan tidak melihat
sisipan `buka`, sehingga keduanya digabung. Bila pemiliknya bukan pemanggil,
`INSERT` giliran tidak menulis apa pun dan tidak mengembalikan baris.
"""


class RiwayatPostgres:
    """Pelaksana di atas PostgreSQL — memenuhi R-13.

    Sambungannya disuntikkan dan wajib tersambung sebagai `PERAN_RIWAYAT`;
    peladen yang menolak `UPDATE` dan `DELETE`, bukan kelas ini.
    """

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def catat(
        self,
        *,
        pemilik: str,
        id_percakapan: uuid.UUID,
        pertanyaan: str,
        id_pesan: str,
        waktu: datetime,
    ) -> None:
        _periksa(pemilik, pertanyaan, id_pesan, waktu)
        baris = await self._sambungan.fetchrow(
            _CATAT, id_percakapan, pemilik, pertanyaan, id_pesan, waktu
        )
        if baris is None:
            raise PercakapanTidakAda

    async def daftar(self, *, pemilik: str) -> tuple[uuid.UUID, ...]:
        baris = await self._sambungan.fetch(
            "SELECT id_percakapan FROM riwayat.percakapan WHERE pemilik = $1 "
            "ORDER BY dibuat_pada DESC, id_percakapan::text",
            pemilik,
        )
        return tuple(uuid.UUID(str(b["id_percakapan"])) for b in baris)

    async def baca(self, *, pemilik: str, id_percakapan: uuid.UUID) -> tuple[BarisGiliran, ...]:
        # Pemilik dan keberadaan diperiksa dalam satu kueri, sehingga
        # "tidak ada" dan "milik orang lain" tidak dapat dibedakan dari luar.
        pemilik_baris = await self._sambungan.fetchrow(
            "SELECT 1 FROM riwayat.percakapan WHERE id_percakapan = $1 AND pemilik = $2",
            id_percakapan,
            pemilik,
        )
        if pemilik_baris is None:
            raise PercakapanTidakAda
        baris = await self._sambungan.fetch(
            "SELECT pertanyaan, id_pesan, waktu FROM riwayat.giliran "
            "WHERE id_percakapan = $1 ORDER BY nomor",
            id_percakapan,
        )
        return tuple(
            BarisGiliran(
                pertanyaan=str(b["pertanyaan"]),
                id_pesan=str(b["id_pesan"]),
                waktu=b["waktu"],  # type: ignore[arg-type]
            )
            for b in baris
        )
