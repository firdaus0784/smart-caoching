"""Penyimpan akun dan sesi — T-4 fitur 029, R-04, R-06, P-2, P-4.

Bentuk tabelnya D-14 Bagian 5.1 dan `perkakas/basis_data/07-akun.sql`;
aturannya D-14 Bagian 4.4.

## Yang disimpan, dan yang sengaja tidak

Akun berpseudonim (P-1 A): `id` berupa nama akun buatan tim yang tidak
mengidentifikasi orangnya, dan `pseudonim` acak yang terpisah darinya. Tidak
ada nama orang, nomor induk, maupun surel di sini.

Sesi disimpan sebagai **turunan SHA-256 pengenalnya**, bukan pengenalnya.
Penyimpan ini hanya menerima tepat 32 bita, sehingga pengenal mentah — yang
berpanjang 43 karakter — tidak dapat tersimpan oleh kekeliruan pemanggil.

## Keputusan tidak di sini

Ambang penahanan, lama penahanan, batas tanpa aktivitas, dan masa sesi
diberikan pemanggil (`src/api/autentikasi.py`). Penyimpan ini hanya
menjalankannya secara **atomik**: penaikan penghitung dan penetapan penahanan
terjadi dalam satu pernyataan, sehingga dua percobaan bersamaan tidak dapat
sama-sama membaca angka sembilan.

## Permukaan tanpa hapus, tanpa pengubah sandi

Sesi **dicabut**, tidak dihapus (R-06). Membuat akun, mengatur ulang sandi, dan
menonaktifkan adalah pekerjaan perkakas tim dengan peran basis data
tersendiri; pada PostgreSQL ketiadaannya di sini ditegakkan peladen lewat hak
per kolom `peran_autentikasi` (T-2), bukan hanya oleh ketiadaan metode.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Final, Protocol

from src.penyimpanan.sambungan import SambunganAktif

PERAN_AUTENTIKASI: Final = "peran_autentikasi"
"""Peran basis data layanan aplikasi bagi skema `akun` — `07-akun.sql`.

Tanpa tipe kredensial tersendiri, alasan yang sama dengan `PERAN_RIWAYAT`
(KB-142): pemisahannya ditegakkan hak peladen, bukan objek Python.
"""

PANJANG_TURUNAN_PENGENAL: Final = 32


@dataclass(frozen=True)
class BarisAkun:
    """Satu akun sebagaimana tersimpan. `peran` berupa nilai D-14 Bagian 3;
    lapisan API yang memetakannya ke `Peran`."""

    id: str
    pseudonim: str
    peran: str
    status_aktif: bool
    turunan_sandi: str
    gagal_beruntun: int
    ditahan_sampai: datetime | None


@dataclass(frozen=True)
class SesiSah:
    """Sesi yang masih berlaku, beserta peran dan pseudonim **saat ini** dari
    akunnya — dibaca tiap kali, tidak disalin ke sesi (KA-01)."""

    id_pengguna: str
    pseudonim: str
    peran: str
    dibuat_pada: datetime
    terakhir_aktif: datetime
    kedaluwarsa_pada: datetime


class PenyimpanAkun(Protocol):
    async def baca_akun(self, id_akun: str) -> BarisAkun | None:
        """Akun menurut `id`, atau `None`."""
        ...

    async def catat_gagal(
        self, id_akun: str, *, sekarang: datetime, ambang: int, lama_tahan: timedelta
    ) -> bool:
        """Naikkan penghitung kegagalan, atomik. `True` bila penahanan **baru
        dimulai** oleh panggilan ini.

        Selama ditahan, tidak ada yang berubah. Sesudah penahanan lewat,
        penghitung mulai lagi dari satu.
        """
        ...

    async def catat_berhasil(self, id_akun: str) -> None:
        """Penghitung kembali nol, penahanan dihapus."""
        ...

    async def buat_sesi(
        self,
        turunan_pengenal: bytes,
        id_akun: str,
        *,
        sekarang: datetime,
        kedaluwarsa_pada: datetime,
    ) -> None: ...

    async def baca_sesi(
        self, turunan_pengenal: bytes, *, sekarang: datetime, batas_diam: timedelta
    ) -> SesiSah | None:
        """Sesi yang belum dicabut, belum lewat masa mutlaknya, belum diam
        melampaui `batas_diam`, dan akunnya aktif — atau `None`."""
        ...

    async def sentuh_sesi(self, turunan_pengenal: bytes, *, sekarang: datetime) -> None:
        """Perbarui `terakhir_aktif`. Sesi yang dicabut tidak dihidupkan."""
        ...

    async def catat_penarikan(self, pseudonim: str, *, sekarang: datetime) -> bool:
        """Catat permintaan penarikan data dan cabut **seluruh** sesi akun itu —
        fitur 033, R-01, K-1. `True` bila permintaan baru tercatat, `False` bila
        sudah ada yang tertunda. Akun berpermintaan tertunda terbaca nonaktif."""
        ...

    async def cabut_sesi(self, turunan_pengenal: bytes, *, sekarang: datetime) -> None:
        """Sesi tidak berlaku seketika (R-06). Yang sudah dicabut tidak disentuh."""
        ...


def _utc(*waktu: datetime) -> None:
    for w in waktu:
        offset = w.utcoffset()
        if offset is None or offset.total_seconds():
            raise ValueError("waktu wajib berzona UTC (KM-01)")


_POLA_PSEUDONIM: Final = re.compile(r"psd_[a-z]{16}")


def _pseudonim_sah(pseudonim: str) -> None:
    if _POLA_PSEUDONIM.fullmatch(pseudonim) is None:
        raise ValueError("permintaan penarikan wajib berpemilik pseudonim (C-05)")


def _turunan_sah(turunan_pengenal: bytes) -> None:
    if len(turunan_pengenal) != PANJANG_TURUNAN_PENGENAL:
        raise ValueError("sesi hanya menyimpan turunan SHA-256 pengenalnya, 32 bita")


@dataclass
class _SesiMemori:
    id_pengguna: str
    dibuat_pada: datetime
    terakhir_aktif: datetime
    kedaluwarsa_pada: datetime
    dicabut_pada: datetime | None = None


class AkunMemori:
    """Pelaksana di memori — bagi uji. Akun dan sesi hilang ketika proses
    berhenti, sehingga titik jalan memakai `AkunPostgres`."""

    def __init__(self) -> None:
        self._akun: dict[str, BarisAkun] = {}
        self._sesi: dict[bytes, _SesiMemori] = {}
        self._tertunda: set[str] = set()

    def pasang_akun(self, akun: BarisAkun) -> None:
        """Penyiapan uji — peran perkakas tim pada pelaksana memori."""
        self._akun[akun.id] = akun

    async def baca_akun(self, id_akun: str) -> BarisAkun | None:
        akun = self._akun.get(id_akun)
        if akun is not None and akun.pseudonim in self._tertunda:
            return replace(akun, status_aktif=False)
        return akun

    async def catat_gagal(
        self, id_akun: str, *, sekarang: datetime, ambang: int, lama_tahan: timedelta
    ) -> bool:
        _utc(sekarang)
        akun = self._akun.get(id_akun)
        if akun is None:
            return False
        if akun.ditahan_sampai is not None and akun.ditahan_sampai > sekarang:
            return False
        gagal = 1 if akun.ditahan_sampai is not None else akun.gagal_beruntun + 1
        ditahan = sekarang + lama_tahan if gagal >= ambang else None
        self._akun[id_akun] = replace(akun, gagal_beruntun=gagal, ditahan_sampai=ditahan)
        return ditahan is not None

    async def catat_berhasil(self, id_akun: str) -> None:
        akun = self._akun.get(id_akun)
        if akun is not None:
            self._akun[id_akun] = replace(akun, gagal_beruntun=0, ditahan_sampai=None)

    async def buat_sesi(
        self,
        turunan_pengenal: bytes,
        id_akun: str,
        *,
        sekarang: datetime,
        kedaluwarsa_pada: datetime,
    ) -> None:
        _turunan_sah(turunan_pengenal)
        _utc(sekarang, kedaluwarsa_pada)
        if id_akun not in self._akun:
            raise ValueError("sesi menuntut akun yang ada")
        if turunan_pengenal in self._sesi:
            raise ValueError("turunan pengenal sudah dipakai")
        self._sesi[turunan_pengenal] = _SesiMemori(
            id_pengguna=id_akun,
            dibuat_pada=sekarang,
            terakhir_aktif=sekarang,
            kedaluwarsa_pada=kedaluwarsa_pada,
        )

    async def baca_sesi(
        self, turunan_pengenal: bytes, *, sekarang: datetime, batas_diam: timedelta
    ) -> SesiSah | None:
        _utc(sekarang)
        sesi = self._sesi.get(turunan_pengenal)
        if sesi is None or sesi.dicabut_pada is not None:
            return None
        if sesi.kedaluwarsa_pada <= sekarang or sesi.terakhir_aktif <= sekarang - batas_diam:
            return None
        akun = self._akun[sesi.id_pengguna]
        if not akun.status_aktif or akun.pseudonim in self._tertunda:
            return None
        return SesiSah(
            id_pengguna=akun.id,
            pseudonim=akun.pseudonim,
            peran=akun.peran,
            dibuat_pada=sesi.dibuat_pada,
            terakhir_aktif=sesi.terakhir_aktif,
            kedaluwarsa_pada=sesi.kedaluwarsa_pada,
        )

    async def sentuh_sesi(self, turunan_pengenal: bytes, *, sekarang: datetime) -> None:
        _utc(sekarang)
        sesi = self._sesi.get(turunan_pengenal)
        if sesi is not None and sesi.dicabut_pada is None:
            sesi.terakhir_aktif = sekarang

    async def cabut_sesi(self, turunan_pengenal: bytes, *, sekarang: datetime) -> None:
        _utc(sekarang)
        sesi = self._sesi.get(turunan_pengenal)
        if sesi is not None and sesi.dicabut_pada is None:
            sesi.dicabut_pada = sekarang

    async def catat_penarikan(self, pseudonim: str, *, sekarang: datetime) -> bool:
        _pseudonim_sah(pseudonim)
        _utc(sekarang)
        milik = {a.id for a in self._akun.values() if a.pseudonim == pseudonim}
        for sesi in self._sesi.values():
            if sesi.id_pengguna in milik and sesi.dicabut_pada is None:
                sesi.dicabut_pada = sekarang
        if pseudonim in self._tertunda:
            return False
        self._tertunda.add(pseudonim)
        return True


_CATAT_GAGAL: Final = """
UPDATE akun.pengguna
   SET gagal_beruntun = CASE WHEN ditahan_sampai IS NOT NULL THEN 1
                             ELSE gagal_beruntun + 1 END,
       ditahan_sampai = CASE WHEN (CASE WHEN ditahan_sampai IS NOT NULL THEN 1
                                        ELSE gagal_beruntun + 1 END) >= $3
                             THEN $2 + $4::interval ELSE NULL END
 WHERE id = $1
   AND (ditahan_sampai IS NULL OR ditahan_sampai <= $2)
RETURNING ditahan_sampai IS NOT NULL AS baru_ditahan
"""
"""Satu pernyataan: penguncian baris oleh `UPDATE` menyerialkan percobaan
bersamaan, dan `WHERE` dievaluasi ulang atas versi baris terbaru — sehingga
percobaan yang tiba sesudah penahanan dimulai tidak menulis apa pun."""

_BACA_SESI: Final = """
SELECT s.id_pengguna, p.pseudonim, p.peran, s.dibuat_pada, s.terakhir_aktif,
       s.kedaluwarsa_pada
  FROM akun.sesi s JOIN akun.pengguna p ON p.id = s.id_pengguna
 WHERE s.turunan_pengenal = $1
   AND s.dicabut_pada IS NULL
   AND s.kedaluwarsa_pada > $2
   AND s.terakhir_aktif > $2 - $3::interval
   AND p.status_aktif
   AND NOT EXISTS (SELECT 1 FROM akun.permintaan_penarikan r
                    WHERE r.pseudonim = p.pseudonim AND r.dipenuhi_pada IS NULL)
"""

_CATAT_PENARIKAN: Final = """
WITH minta AS (
    INSERT INTO akun.permintaan_penarikan (pseudonim, diminta_pada) VALUES ($1, $2)
    ON CONFLICT (pseudonim) WHERE dipenuhi_pada IS NULL DO NOTHING
    RETURNING pseudonim
), cabut AS (
    UPDATE akun.sesi SET dicabut_pada = $2
     WHERE id_pengguna IN (SELECT id FROM akun.pengguna WHERE pseudonim = $1)
       AND dicabut_pada IS NULL
)
SELECT count(*) AS baru FROM minta
"""
"""Satu pernyataan: permintaan tercatat dan sesi dicabut bersama, atau tidak
sama sekali (`SambunganAktif` tanpa transaksi, fitur 024)."""

_BACA_AKUN: Final = """
SELECT p.id, p.pseudonim, p.peran, p.turunan_sandi, p.gagal_beruntun, p.ditahan_sampai,
       p.status_aktif AND NOT EXISTS (
           SELECT 1 FROM akun.permintaan_penarikan r
            WHERE r.pseudonim = p.pseudonim AND r.dipenuhi_pada IS NULL
       ) AS status_aktif
  FROM akun.pengguna p WHERE p.id = $1
"""
"""Akun berpermintaan tertunda terbaca nonaktif — penolakan masuknya sama
dengan akun nonaktif (K-4 fitur 033)."""


class AkunPostgres:
    """Pelaksana di atas PostgreSQL. Sambungannya disuntikkan dan wajib
    tersambung sebagai `PERAN_AUTENTIKASI`; peladen yang menolak penulisan
    sandi, peran, dan pseudonim, bukan kelas ini."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def baca_akun(self, id_akun: str) -> BarisAkun | None:
        b = await self._sambungan.fetchrow(_BACA_AKUN, id_akun)
        if b is None:
            return None
        return BarisAkun(
            id=str(b["id"]),
            pseudonim=str(b["pseudonim"]),
            peran=str(b["peran"]),
            status_aktif=bool(b["status_aktif"]),
            turunan_sandi=str(b["turunan_sandi"]),
            gagal_beruntun=int(b["gagal_beruntun"]),  # type: ignore[call-overload]
            ditahan_sampai=b["ditahan_sampai"],  # type: ignore[arg-type]
        )

    async def catat_gagal(
        self, id_akun: str, *, sekarang: datetime, ambang: int, lama_tahan: timedelta
    ) -> bool:
        _utc(sekarang)
        b = await self._sambungan.fetchrow(_CATAT_GAGAL, id_akun, sekarang, ambang, lama_tahan)
        return b is not None and bool(b["baru_ditahan"])

    async def catat_berhasil(self, id_akun: str) -> None:
        await self._sambungan.execute(
            "UPDATE akun.pengguna SET gagal_beruntun = 0, ditahan_sampai = NULL WHERE id = $1",
            id_akun,
        )

    async def buat_sesi(
        self,
        turunan_pengenal: bytes,
        id_akun: str,
        *,
        sekarang: datetime,
        kedaluwarsa_pada: datetime,
    ) -> None:
        _turunan_sah(turunan_pengenal)
        _utc(sekarang, kedaluwarsa_pada)
        await self._sambungan.execute(
            "INSERT INTO akun.sesi (turunan_pengenal, id_pengguna, dibuat_pada, "
            "terakhir_aktif, kedaluwarsa_pada) VALUES ($1, $2, $3, $3, $4)",
            turunan_pengenal,
            id_akun,
            sekarang,
            kedaluwarsa_pada,
        )

    async def baca_sesi(
        self, turunan_pengenal: bytes, *, sekarang: datetime, batas_diam: timedelta
    ) -> SesiSah | None:
        _utc(sekarang)
        b = await self._sambungan.fetchrow(_BACA_SESI, turunan_pengenal, sekarang, batas_diam)
        if b is None:
            return None
        return SesiSah(
            id_pengguna=str(b["id_pengguna"]),
            pseudonim=str(b["pseudonim"]),
            peran=str(b["peran"]),
            dibuat_pada=b["dibuat_pada"],  # type: ignore[arg-type]
            terakhir_aktif=b["terakhir_aktif"],  # type: ignore[arg-type]
            kedaluwarsa_pada=b["kedaluwarsa_pada"],  # type: ignore[arg-type]
        )

    async def sentuh_sesi(self, turunan_pengenal: bytes, *, sekarang: datetime) -> None:
        _utc(sekarang)
        await self._sambungan.execute(
            "UPDATE akun.sesi SET terakhir_aktif = $2 "
            "WHERE turunan_pengenal = $1 AND dicabut_pada IS NULL",
            turunan_pengenal,
            sekarang,
        )

    async def cabut_sesi(self, turunan_pengenal: bytes, *, sekarang: datetime) -> None:
        _utc(sekarang)
        await self._sambungan.execute(
            "UPDATE akun.sesi SET dicabut_pada = $2 "
            "WHERE turunan_pengenal = $1 AND dicabut_pada IS NULL",
            turunan_pengenal,
            sekarang,
        )

    async def catat_penarikan(self, pseudonim: str, *, sekarang: datetime) -> bool:
        _pseudonim_sah(pseudonim)
        _utc(sekarang)
        b = await self._sambungan.fetchrow(_CATAT_PENARIKAN, pseudonim, sekarang)
        return b is not None and int(b["baru"]) > 0  # type: ignore[call-overload]


# ── T-7 · pengelola akun bagi perkakas tim ───────────────────────────

PERAN_PENGELOLA_AKUN: Final = "peran_pengelola_akun"
"""Peran basis data perkakas tim — `07-akun.sql`. Layanan aplikasi tidak
tersambung sebagai peran ini; bila kelas di bawah dipanggil dengan sambungan
`peran_autentikasi`, peladen menolak tiap pernyataannya."""

_ATUR_ULANG: Final = """
WITH akun_ini AS (
    UPDATE akun.pengguna
       SET turunan_sandi = $2, gagal_beruntun = 0, ditahan_sampai = NULL
     WHERE id = $1
    RETURNING id
), cabut AS (
    UPDATE akun.sesi SET dicabut_pada = $3
     WHERE id_pengguna IN (SELECT id FROM akun_ini) AND dicabut_pada IS NULL
)
SELECT id FROM akun_ini
"""

_NONAKTIFKAN: Final = """
WITH akun_ini AS (
    UPDATE akun.pengguna SET status_aktif = false WHERE id = $1 RETURNING id
), cabut AS (
    UPDATE akun.sesi SET dicabut_pada = $2
     WHERE id_pengguna IN (SELECT id FROM akun_ini) AND dicabut_pada IS NULL
)
SELECT id FROM akun_ini
"""


class PengelolaAkunPostgres:
    """Membuat akun, mengatur ulang sandi, menonaktifkan — P-5, K-5.

    Dipakai `perkakas/akun.py` dengan sambungan sebagai
    `PERAN_PENGELOLA_AKUN`. Tinggal di sini, bukan pada perkakasnya, karena
    seluruh akses penyimpanan lewat `src/penyimpanan/` (C-03, AGENTS.md).

    Atur ulang sandi dan penonaktifan **mencabut seluruh sesi** akun itu dalam
    pernyataan yang sama: sandi yang diganti karena bocor tidak boleh
    meninggalkan sesi yang dibuka dengan sandi lama.
    """

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def buat_akun(
        self,
        *,
        id_akun: str,
        pseudonim: str,
        peran: str,
        turunan_sandi: str,
        sekarang: datetime,
    ) -> bool:
        """`False` bila `id_akun` sudah ada — akun lama tidak disentuh."""
        _utc(sekarang)
        b = await self._sambungan.fetchrow(
            "INSERT INTO akun.pengguna (id, pseudonim, peran, tanggal_dibuat, turunan_sandi) "
            "VALUES ($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING RETURNING id",
            id_akun,
            pseudonim,
            peran,
            sekarang,
            turunan_sandi,
        )
        return b is not None

    async def atur_ulang_sandi(
        self, *, id_akun: str, turunan_sandi: str, sekarang: datetime
    ) -> bool:
        """`False` bila akun tidak ada."""
        _utc(sekarang)
        b = await self._sambungan.fetchrow(_ATUR_ULANG, id_akun, turunan_sandi, sekarang)
        return b is not None

    async def nonaktifkan(self, *, id_akun: str, sekarang: datetime) -> bool:
        """`False` bila akun tidak ada."""
        _utc(sekarang)
        b = await self._sambungan.fetchrow(_NONAKTIFKAN, id_akun, sekarang)
        return b is not None
