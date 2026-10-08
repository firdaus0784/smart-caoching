"""Penyimpan riwayat percakapan — T-3 fitur 028, R-02, R-08, R-12, R-13.

FR-F09: *"Sistem menyimpan riwayat percakapan dan memungkinkan pengguna
melanjutkan sesi sebelumnya."* Bentuknya D-14 Bagian 4.3 dan 5.1; tabelnya
`perkakas/basis_data/06-riwayat.sql`.

## Yang disimpan, dan yang sengaja tidak dibaca

Giliran: pertanyaan, rujukan `id_pesan`, dan waktu. Sejak fitur 036 (TK-69,
P-1 A) tanggapan yang terkirim **juga** tersimpan — pada `riwayat.pesan`,
sebagai catatan audit yang dibaca kurator lewat aduan. Penyimpan ini menulisnya
tetapi **tidak pernah membacanya**: `baca` mengembalikan giliran tanpa jawaban,
dan pada PostgreSQL `peran_riwayat` tidak memegang `SELECT` atas tabelnya.
Tanggapan yang tersimpan menua: regulasi yang menjadi dasarnya dapat dicabut
sesudah jawaban disusun, dan jawaban lama yang ditampilkan ulang melanggar C-07
tanpa satu galat pun (D-14 Bagian 4.3).

Giliran dan tanggapannya ditulis **dalam satu pernyataan**. Gagal yang satu,
tidak tertulis keduanya — dan `/tanya` tidak mengirim jawaban yang tidak
tercatat.

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

Permukaannya empat: `catat`, `daftar`, `baca`, `dapat_ditulis` — ditambah
`baris_pesan` pada pelaksana memori saja (lihat di atas). Tidak ada yang mengubah maupun
menghapus — dan pada PostgreSQL ketiadaan itu ditegakkan peladen: `peran_riwayat`
hanya diberi `SELECT` dan `INSERT` (T-2). Penarikan data pengguna (NFR-09)
kelak menjadi tindakan tersendiri dengan peran tersendiri.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, Protocol

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


@dataclass(frozen=True)
class BarisPesan:
    """Tanggapan yang terkirim, sebagaimana tercatat (fitur 036, P-1 A)."""

    id_pesan: str
    id_percakapan: uuid.UUID
    tanggapan: Mapping[str, Any]
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
        tanggapan: Mapping[str, Any],
    ) -> None:
        """Tambahkan satu giliran beserta tanggapannya, dalam satu langkah.
        Percakapan baru terbuka pada giliran pertamanya."""
        ...

    async def daftar(self, *, pemilik: str) -> tuple[uuid.UUID, ...]:
        """Percakapan milik `pemilik`, terbaru lebih dulu (D-14 Bagian 4.3, K-1)."""
        ...

    async def baca(self, *, pemilik: str, id_percakapan: uuid.UUID) -> tuple[BarisGiliran, ...]:
        """Giliran satu percakapan milik `pemilik`, berurutan."""
        ...

    async def dapat_ditulis(self, *, pemilik: str, id_percakapan: uuid.UUID) -> bool:
        """Belum dikenal, atau milik `pemilik`. Membaca saja; tidak membuka apa pun.

        Ditambahkan T-6 (KB-145): pemilik diperiksa **sebelum** jalur penjawab
        dipanggil, sehingga jawaban tidak disusun — dan model tidak dipanggil —
        bagi percakapan milik orang lain. `catat` tetap memeriksa ulang secara
        atomik; pemeriksaan ini bukan penjagaan terakhir.
        """
        ...


def _periksa(
    pemilik: str, pertanyaan: str, id_pesan: str, waktu: datetime, tanggapan: Mapping[str, Any]
) -> None:
    for nama, nilai in (("pemilik", pemilik), ("pertanyaan", pertanyaan), ("id_pesan", id_pesan)):
        if not nilai.strip():
            raise ValueError(f"{nama} tidak boleh kosong")
    if waktu.tzinfo is None or waktu.utcoffset() is None or waktu.utcoffset().total_seconds():  # type: ignore[union-attr]
        raise ValueError("waktu giliran wajib berzona UTC (KM-01)")
    # Batasan yang sama dengan `13-penilaian.sql`, agar kedua pelaksana sepakat.
    if tanggapan.get("id_pesan") != id_pesan:
        raise ValueError("tanggapan milik pesan lain — yang tercatat harus tanggapan pesan ini")
    if "tingkat_keyakinan" in tanggapan:
        raise ValueError("tanggapan tidak boleh membawa tingkat keyakinan (FR-F06)")


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
        self._pesan: dict[str, BarisPesan] = {}

    async def catat(
        self,
        *,
        pemilik: str,
        id_percakapan: uuid.UUID,
        pertanyaan: str,
        id_pesan: str,
        waktu: datetime,
        tanggapan: Mapping[str, Any],
    ) -> None:
        _periksa(pemilik, pertanyaan, id_pesan, waktu, tanggapan)
        # Diperiksa sebelum apa pun berubah — sama dengan kunci utama yang
        # menggagalkan seluruh pernyataan pada PostgreSQL.
        if id_pesan in self._pesan:
            raise ValueError("id_pesan sudah tercatat")
        satu = self._percakapan.get(id_percakapan)
        if satu is not None and satu.pemilik != pemilik:
            raise PercakapanTidakAda
        if satu is None:
            satu = _PercakapanMemori(pemilik=pemilik, dibuat_pada=waktu, giliran=[])
            self._percakapan[id_percakapan] = satu
        satu.giliran.append(BarisGiliran(pertanyaan=pertanyaan, id_pesan=id_pesan, waktu=waktu))
        self._pesan[id_pesan] = BarisPesan(
            id_pesan=id_pesan,
            id_percakapan=id_percakapan,
            tanggapan=json.loads(json.dumps(dict(tanggapan))),
            waktu=waktu,
        )

    def baris_pesan(self) -> dict[str, BarisPesan]:
        """Tanggapan tercatat — **hanya** bagi penilaian di memori, padanan hak
        `SELECT` `peran_penilaian`. Rute riwayat tidak memanggilnya."""
        return dict(self._pesan)

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

    async def dapat_ditulis(self, *, pemilik: str, id_percakapan: uuid.UUID) -> bool:
        satu = self._percakapan.get(id_percakapan)
        return satu is None or satu.pemilik == pemilik


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
), sah AS (
    SELECT 1 WHERE (SELECT pemilik FROM pemilik_sah LIMIT 1) = $2
), pesan AS (
    INSERT INTO riwayat.pesan (id_pesan, id_percakapan, tanggapan, waktu)
    SELECT $4, $1, $6::jsonb, $5 FROM sah
)
INSERT INTO riwayat.giliran (id_percakapan, pertanyaan, id_pesan, waktu)
SELECT $1, $3, $4, $5 FROM sah
RETURNING nomor
"""
"""Membuka percakapan, memeriksa pemilik, dan menambah giliran **beserta
tanggapannya** dalam **satu pernyataan** — atomik tanpa transaksi, yang tidak
disediakan `SambunganAktif`. `pesan` tidak memakai `RETURNING`: peran ini
tidak memegang `SELECT` atas tabelnya (C-07).

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
        tanggapan: Mapping[str, Any],
    ) -> None:
        _periksa(pemilik, pertanyaan, id_pesan, waktu, tanggapan)
        baris = await self._sambungan.fetchrow(
            _CATAT, id_percakapan, pemilik, pertanyaan, id_pesan, waktu, json.dumps(dict(tanggapan))
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

    async def dapat_ditulis(self, *, pemilik: str, id_percakapan: uuid.UUID) -> bool:
        baris = await self._sambungan.fetchrow(
            "SELECT pemilik FROM riwayat.percakapan WHERE id_percakapan = $1", id_percakapan
        )
        return baris is None or baris["pemilik"] == pemilik

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
