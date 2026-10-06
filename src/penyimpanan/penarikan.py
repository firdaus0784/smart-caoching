"""Penghapusan penarikan data — T-5 fitur 033, R-02, R-03, R-04, R-09; K-1, K-2.

Bentuk tabelnya D-14 Bagian 5.1 dan `perkakas/basis_data/11-penarikan.sql`.

## Hanya dipakai perkakas tim

Modul ini **tidak** dipakai layanan aplikasi. Kedua sambungannya tersambung
sebagai `peran_penarikan` dan `peran_penarikan_pseudonim`, peran yang tidak
dipegang layanan mana pun; uji arah menjaga bahwa `src/api/` dan titik jalan
tidak mengimpornya. Rute `DELETE /saya/data` hanya mencatat permintaan.

## Pemetaan lebih dulu, lalu satu pernyataan

1. Pemetaan pseudonim dihapus pada basis data pseudonim.
2. Satu pernyataan CTE menghapus seluruh data milik pseudonim itu pada
   sepuluh tabel, lalu mengosongkan pseudonim pada baris permintaan dan
   mengisi waktu dipenuhi serta jumlah baris per tabel.

Urutan ini membuat kegagalan di tengah dapat diulang: bila langkah 2 gagal,
langkah 1 diulang tanpa menemukan apa pun. Urutan sebaliknya meninggalkan
pemetaan yang tidak dapat dicari lagi, sebab langkah 2 mengosongkan
pseudonimnya. `SambunganAktif` tanpa transaksi (fitur 024), sehingga langkah 2
ditulis sebagai satu pernyataan — separuh penghapusan tidak dapat terjadi.

## Tanpa pseudonim keluar dari sini

`PermintaanTertunda` dan `HasilPenarikan` tidak membawa pseudonim. Yang
dibutuhkan orang yang menjalankan perkakas adalah nomor dan jumlah, bukan
siapa (R-09).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from src.penyimpanan.sambungan import SambunganAktif

PERAN_PENARIKAN: Final = "peran_penarikan"
PERAN_PENARIKAN_PSEUDONIM: Final = "peran_penarikan_pseudonim"
"""Peran basis data perkakas penarikan — `11-penarikan.sql` dan
`11b-penarikan-pseudonim.sql`. Tidak dipegang layanan aplikasi."""

TABEL_DATA_PENGGUNA: Final = (
    "telemetri.peristiwa",
    "riwayat.giliran",
    "riwayat.percakapan",
    "penemuan.tayang_harian",
    "penemuan.belum_relevan",
    "pengguna.profil_sekolah",
    "pengguna.prioritas_manajerial",
    "pengguna.persetujuan",
    "akun.sesi",
    "akun.pengguna",
)
"""Sepuluh tempat data milik seorang pengguna — tabel `spec.md` fitur 033,
dibaca dari katalog basis data. Catatan persetujuan termasuk (P-3, TK-75)."""

_HAPUS: Final = """
WITH peristiwa AS (
    DELETE FROM telemetri.peristiwa WHERE pseudonim = $1 RETURNING pseudonim
), giliran AS (
    DELETE FROM riwayat.giliran
     WHERE id_percakapan IN (SELECT id_percakapan FROM riwayat.percakapan WHERE pemilik = $1)
    RETURNING id_percakapan
), percakapan AS (
    DELETE FROM riwayat.percakapan WHERE pemilik = $1 RETURNING pemilik
), tayang AS (
    DELETE FROM penemuan.tayang_harian WHERE id_pengguna = $1 RETURNING id_pengguna
), belum_relevan AS (
    DELETE FROM penemuan.belum_relevan WHERE id_pengguna = $1 RETURNING id_pengguna
), profil AS (
    DELETE FROM pengguna.profil_sekolah WHERE id_pengguna = $1 RETURNING id_pengguna
), prioritas AS (
    DELETE FROM pengguna.prioritas_manajerial WHERE id_pengguna = $1 RETURNING id_pengguna
), persetujuan AS (
    DELETE FROM pengguna.persetujuan WHERE id_pengguna = $1 RETURNING id_pengguna
), sesi AS (
    DELETE FROM akun.sesi
     WHERE id_pengguna IN (SELECT id FROM akun.pengguna WHERE pseudonim = $1)
    RETURNING id_pengguna
), akun AS (
    DELETE FROM akun.pengguna WHERE pseudonim = $1 RETURNING pseudonim
), jumlah AS (
    SELECT jsonb_build_object(
        'telemetri.peristiwa', (SELECT count(*) FROM peristiwa),
        'riwayat.giliran', (SELECT count(*) FROM giliran),
        'riwayat.percakapan', (SELECT count(*) FROM percakapan),
        'penemuan.tayang_harian', (SELECT count(*) FROM tayang),
        'penemuan.belum_relevan', (SELECT count(*) FROM belum_relevan),
        'pengguna.profil_sekolah', (SELECT count(*) FROM profil),
        'pengguna.prioritas_manajerial', (SELECT count(*) FROM prioritas),
        'pengguna.persetujuan', (SELECT count(*) FROM persetujuan),
        'akun.sesi', (SELECT count(*) FROM sesi),
        'akun.pengguna', (SELECT count(*) FROM akun)
    ) AS isi
), tandai AS (
    UPDATE akun.permintaan_penarikan
       SET pseudonim = NULL, dipenuhi_pada = $3, jumlah_baris = (SELECT isi FROM jumlah)
     WHERE nomor = $2 AND pseudonim = $1 AND dipenuhi_pada IS NULL
    RETURNING nomor
)
SELECT (SELECT isi FROM jumlah) AS jumlah, (SELECT count(*) FROM tandai) AS ditandai
"""


@dataclass(frozen=True)
class PermintaanTertunda:
    nomor: int
    diminta_pada: datetime


@dataclass(frozen=True)
class HasilPenarikan:
    nomor: int
    jumlah_baris: dict[str, int]
    pemetaan: int
    """Baris pemetaan terhapus pada basis data pseudonim."""


def _utc(waktu: datetime) -> None:
    offset = waktu.utcoffset()
    if offset is None or offset.total_seconds():
        raise ValueError("waktu wajib berzona UTC (KM-01)")


def _jumlah_perintah(status: object) -> int:
    """`DELETE n` dari status perintah PostgreSQL."""
    return int(str(status).rsplit(" ", 1)[-1])


class PenarikanPostgres:
    """`utama` tersambung sebagai `PERAN_PENARIKAN` pada basis data perilaku;
    `pseudonim` sebagai `PERAN_PENARIKAN_PSEUDONIM` pada basis data pseudonim."""

    def __init__(self, utama: SambunganAktif, pseudonim: SambunganAktif) -> None:
        self._utama = utama
        self._pseudonim = pseudonim

    async def tertunda(self) -> tuple[PermintaanTertunda, ...]:
        """Permintaan yang belum dipenuhi, terlama lebih dulu."""
        baris = await self._utama.fetch(
            "SELECT nomor, diminta_pada FROM akun.permintaan_penarikan "
            "WHERE dipenuhi_pada IS NULL ORDER BY diminta_pada, nomor"
        )
        return tuple(
            PermintaanTertunda(nomor=int(b["nomor"]), diminta_pada=b["diminta_pada"])  # type: ignore[call-overload, arg-type]
            for b in baris
        )

    async def jalankan(self, nomor: int, *, sekarang: datetime) -> HasilPenarikan | None:
        """Penuhi satu permintaan; `None` bila tidak ada atau sudah dipenuhi."""
        _utc(sekarang)
        b = await self._utama.fetchrow(
            "SELECT pseudonim FROM akun.permintaan_penarikan "
            "WHERE nomor = $1 AND dipenuhi_pada IS NULL",
            nomor,
        )
        if b is None:
            return None
        pseudonim = str(b["pseudonim"])
        pemetaan = _jumlah_perintah(
            await self._pseudonim.execute(
                "DELETE FROM pseudonim.peta_pseudonim WHERE pseudonim = $1", pseudonim
            )
        )
        hasil = await self._utama.fetchrow(_HAPUS, pseudonim, nomor, sekarang)
        if hasil is None or not int(hasil["ditandai"]):  # type: ignore[call-overload]
            return None
        jumlah = hasil["jumlah"]
        isi = json.loads(jumlah) if isinstance(jumlah, str) else dict(jumlah)  # type: ignore[call-overload]
        return HasilPenarikan(
            nomor=nomor,
            jumlah_baris={str(k): int(v) for k, v in isi.items()},
            pemetaan=pemetaan,
        )
