"""Penyimpan profil, prioritas, persetujuan — T-3 fitur 030, R-02, R-03, R-04, K-3.

Bentuk tabelnya D-14 Bagian 4.5 dan 5.1 dan `perkakas/basis_data/08-pengguna.sql`.

## Baris sederhana, bukan model fitur 022

`src/penyimpanan/` tidak mengimpor `src/pengguna/` — ia lapisan di bawahnya
(AGENTS.md). Penyimpan ini karena itu bekerja dengan baris sederhana, dan
`src/api/saya.py` yang memetakannya ke `ProfilSekolah`, `PrioritasManajerial`,
dan `CatatanPersetujuan`, yang menegakkan aturan isinya.

Yang diperiksa di sini hanya bentuk yang tabelnya juga tolak — pemilik berpola
pseudonim, tiga sampai lima kategori K1 s.d. K8, versi naskah tidak kosong, waktu
UTC — agar kedua pelaksana menolak sama, bukan satu lewat batasan tabel dan
yang lain menerima. Bentuk yang sama dengan `riwayat.py`.

## Tambah-saja

Prioritas: setiap penetapan menambah baris; yang terbaru berlaku. Persetujuan:
setiap putusan menambah catatan; satu-satunya pengubahan adalah mengisi
`dicabut_pada` pada catatan terbaru yang disetujui. Pada PostgreSQL keduanya
ditegakkan peladen lewat hak per kolom `peran_pengguna` (T-2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Final, Protocol

from src.penyimpanan.sambungan import SambunganAktif

PERAN_PENGGUNA: Final = "peran_pengguna"
"""Peran basis data penulis profil — `08-pengguna.sql`. Tanpa tipe kredensial
tersendiri, alasan yang sama dengan `PERAN_RIWAYAT` (KB-142)."""

_POLA_PEMILIK: Final = re.compile(r"psd_[a-z]{16}")
_KATEGORI_SAH: Final = frozenset(f"K{i}" for i in range(1, 9))


@dataclass(frozen=True)
class BarisProfil:
    """Enam isian FR-A02, sebagaimana tersimpan."""

    jabatan: str
    masa_kerja: int
    jumlah_rombel: int
    jumlah_ptk: int
    jalur_akreditasi: str
    wilayah: str


@dataclass(frozen=True)
class ProfilTersimpan:
    isi: BarisProfil
    tanggal_perbarui: datetime | None
    """`None` berarti belum pernah diperbarui sejak disimpan pertama kali."""


@dataclass(frozen=True)
class BarisPersetujuan:
    versi_naskah: str
    disetujui: bool
    tanggal: datetime
    dicabut_pada: datetime | None


class PenyimpanPengguna(Protocol):
    async def baca_profil(self, pemilik: str) -> ProfilTersimpan | None: ...

    async def simpan_profil(self, pemilik: str, profil: BarisProfil, *, sekarang: datetime) -> None:
        """Membuat, atau memperbarui dengan `tanggal_perbarui = sekarang`."""
        ...

    async def baca_prioritas(self, pemilik: str) -> tuple[str, ...]:
        """Penetapan terbaru, berurutan menurut pilihan; `()` bila belum ada."""
        ...

    async def tetapkan_prioritas(
        self, pemilik: str, kategori: tuple[str, ...], *, sekarang: datetime
    ) -> None: ...

    async def riwayat_prioritas(self, pemilik: str) -> tuple[tuple[str, ...], ...]:
        """Seluruh penetapan, terlama lebih dulu — data penelitian (K-3)."""
        ...

    async def baca_persetujuan(self, pemilik: str) -> BarisPersetujuan | None:
        """Catatan terbaru, atau `None` bila belum pernah diminta."""
        ...

    async def catat_persetujuan(
        self, pemilik: str, *, versi_naskah: str, disetujui: bool, sekarang: datetime
    ) -> None: ...

    async def cabut_persetujuan(self, pemilik: str, *, sekarang: datetime) -> bool:
        """`True` bila catatan terbaru disetujui dan belum dicabut, lalu dicabut."""
        ...

    async def jumlah_catatan_persetujuan(self, pemilik: str) -> int: ...


def _pemilik(pemilik: str) -> None:
    if _POLA_PEMILIK.fullmatch(pemilik) is None:
        raise ValueError("pemilik wajib pseudonim akun (C-05)")


def _utc(waktu: datetime) -> None:
    offset = waktu.utcoffset()
    if offset is None or offset.total_seconds():
        raise ValueError("waktu wajib berzona UTC (KM-01)")


def _kategori(kategori: tuple[str, ...]) -> None:
    if not 3 <= len(kategori) <= 5 or not set(kategori) <= _KATEGORI_SAH:
        raise ValueError("prioritas tiga sampai lima kategori K1 s.d. K8 (FR-A03)")


def _larik(nilai: object) -> tuple[str, ...]:
    """Kolom `text[]` sebagaimana dikembalikan penggerak — daftar untai."""
    if not isinstance(nilai, list | tuple):
        raise TypeError("kolom kategori bukan larik")
    return tuple(str(k) for k in nilai)


def _naskah(versi_naskah: str) -> None:
    if not versi_naskah.strip():
        raise ValueError("persetujuan wajib menyebut versi naskah (R-04)")


@dataclass
class _Milik:
    profil: ProfilTersimpan | None = None
    prioritas: list[tuple[str, ...]] = field(default_factory=list)
    persetujuan: list[BarisPersetujuan] = field(default_factory=list)


class PenggunaMemori:
    """Pelaksana di memori — bagi uji. Hilang ketika proses berhenti."""

    def __init__(self) -> None:
        self._milik: dict[str, _Milik] = {}

    def _dari(self, pemilik: str) -> _Milik:
        return self._milik.setdefault(pemilik, _Milik())

    async def baca_profil(self, pemilik: str) -> ProfilTersimpan | None:
        satu = self._milik.get(pemilik)
        return None if satu is None else satu.profil

    async def simpan_profil(self, pemilik: str, profil: BarisProfil, *, sekarang: datetime) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        satu = self._dari(pemilik)
        satu.profil = ProfilTersimpan(
            isi=profil, tanggal_perbarui=None if satu.profil is None else sekarang
        )

    async def baca_prioritas(self, pemilik: str) -> tuple[str, ...]:
        satu = self._milik.get(pemilik)
        return () if satu is None or not satu.prioritas else satu.prioritas[-1]

    async def tetapkan_prioritas(
        self, pemilik: str, kategori: tuple[str, ...], *, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        _kategori(kategori)
        self._dari(pemilik).prioritas.append(tuple(kategori))

    async def riwayat_prioritas(self, pemilik: str) -> tuple[tuple[str, ...], ...]:
        satu = self._milik.get(pemilik)
        return () if satu is None else tuple(satu.prioritas)

    async def baca_persetujuan(self, pemilik: str) -> BarisPersetujuan | None:
        satu = self._milik.get(pemilik)
        return None if satu is None or not satu.persetujuan else satu.persetujuan[-1]

    async def catat_persetujuan(
        self, pemilik: str, *, versi_naskah: str, disetujui: bool, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        _naskah(versi_naskah)
        self._dari(pemilik).persetujuan.append(
            BarisPersetujuan(
                versi_naskah=versi_naskah, disetujui=disetujui, tanggal=sekarang, dicabut_pada=None
            )
        )

    async def cabut_persetujuan(self, pemilik: str, *, sekarang: datetime) -> bool:
        _utc(sekarang)
        satu = self._milik.get(pemilik)
        if satu is None or not satu.persetujuan:
            return False
        akhir = satu.persetujuan[-1]
        if not akhir.disetujui or akhir.dicabut_pada is not None or sekarang <= akhir.tanggal:
            return False
        satu.persetujuan[-1] = BarisPersetujuan(
            versi_naskah=akhir.versi_naskah,
            disetujui=True,
            tanggal=akhir.tanggal,
            dicabut_pada=sekarang,
        )
        return True

    async def jumlah_catatan_persetujuan(self, pemilik: str) -> int:
        satu = self._milik.get(pemilik)
        return 0 if satu is None else len(satu.persetujuan)


_SIMPAN_PROFIL: Final = """
INSERT INTO pengguna.profil_sekolah
  (id_pengguna, jabatan, masa_kerja, jumlah_rombel, jumlah_ptk, jalur_akreditasi, wilayah)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (id_pengguna) DO UPDATE SET
  jabatan = excluded.jabatan, masa_kerja = excluded.masa_kerja,
  jumlah_rombel = excluded.jumlah_rombel, jumlah_ptk = excluded.jumlah_ptk,
  jalur_akreditasi = excluded.jalur_akreditasi, wilayah = excluded.wilayah,
  tanggal_perbarui = $8
"""

_CABUT: Final = """
UPDATE pengguna.persetujuan SET dicabut_pada = $2
 WHERE nomor = (SELECT max(nomor) FROM pengguna.persetujuan WHERE id_pengguna = $1)
   AND disetujui AND dicabut_pada IS NULL AND tanggal < $2
RETURNING nomor
"""
"""Hanya catatan **terbaru**: persetujuan lama yang sudah digantikan penolakan
tidak dapat dicabut, sebab ia sudah tidak berlaku."""


class PenggunaPostgres:
    """Pelaksana di atas PostgreSQL. Sambungannya wajib tersambung sebagai
    `PERAN_PENGGUNA`; peladen yang menolak pengubahan selain yang diizinkan."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def baca_profil(self, pemilik: str) -> ProfilTersimpan | None:
        b = await self._sambungan.fetchrow(
            "SELECT jabatan, masa_kerja, jumlah_rombel, jumlah_ptk, jalur_akreditasi, wilayah, "
            "tanggal_perbarui FROM pengguna.profil_sekolah WHERE id_pengguna = $1",
            pemilik,
        )
        if b is None:
            return None
        return ProfilTersimpan(
            isi=BarisProfil(
                jabatan=str(b["jabatan"]),
                masa_kerja=int(b["masa_kerja"]),  # type: ignore[call-overload]
                jumlah_rombel=int(b["jumlah_rombel"]),  # type: ignore[call-overload]
                jumlah_ptk=int(b["jumlah_ptk"]),  # type: ignore[call-overload]
                jalur_akreditasi=str(b["jalur_akreditasi"]),
                wilayah=str(b["wilayah"]),
            ),
            tanggal_perbarui=b["tanggal_perbarui"],  # type: ignore[arg-type]
        )

    async def simpan_profil(self, pemilik: str, profil: BarisProfil, *, sekarang: datetime) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        await self._sambungan.execute(
            _SIMPAN_PROFIL,
            pemilik,
            profil.jabatan,
            profil.masa_kerja,
            profil.jumlah_rombel,
            profil.jumlah_ptk,
            profil.jalur_akreditasi,
            profil.wilayah,
            sekarang,
        )

    async def baca_prioritas(self, pemilik: str) -> tuple[str, ...]:
        b = await self._sambungan.fetchrow(
            "SELECT kategori FROM pengguna.prioritas_manajerial WHERE id_pengguna = $1 "
            "ORDER BY nomor DESC LIMIT 1",
            pemilik,
        )
        return () if b is None else _larik(b["kategori"])

    async def tetapkan_prioritas(
        self, pemilik: str, kategori: tuple[str, ...], *, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        _kategori(kategori)
        await self._sambungan.execute(
            "INSERT INTO pengguna.prioritas_manajerial (id_pengguna, kategori, ditetapkan_pada) "
            "VALUES ($1, $2, $3)",
            pemilik,
            list(kategori),
            sekarang,
        )

    async def riwayat_prioritas(self, pemilik: str) -> tuple[tuple[str, ...], ...]:
        baris = await self._sambungan.fetch(
            "SELECT kategori FROM pengguna.prioritas_manajerial WHERE id_pengguna = $1 "
            "ORDER BY nomor",
            pemilik,
        )
        return tuple(_larik(b["kategori"]) for b in baris)

    async def baca_persetujuan(self, pemilik: str) -> BarisPersetujuan | None:
        b = await self._sambungan.fetchrow(
            "SELECT versi_naskah, disetujui, tanggal, dicabut_pada FROM pengguna.persetujuan "
            "WHERE id_pengguna = $1 ORDER BY nomor DESC LIMIT 1",
            pemilik,
        )
        if b is None:
            return None
        return BarisPersetujuan(
            versi_naskah=str(b["versi_naskah"]),
            disetujui=bool(b["disetujui"]),
            tanggal=b["tanggal"],  # type: ignore[arg-type]
            dicabut_pada=b["dicabut_pada"],  # type: ignore[arg-type]
        )

    async def catat_persetujuan(
        self, pemilik: str, *, versi_naskah: str, disetujui: bool, sekarang: datetime
    ) -> None:
        _pemilik(pemilik)
        _utc(sekarang)
        _naskah(versi_naskah)
        await self._sambungan.execute(
            "INSERT INTO pengguna.persetujuan (id_pengguna, jenis, versi_naskah, disetujui, "
            "tanggal) VALUES ($1, 'penelitian', $2, $3, $4)",
            pemilik,
            versi_naskah,
            disetujui,
            sekarang,
        )

    async def cabut_persetujuan(self, pemilik: str, *, sekarang: datetime) -> bool:
        _utc(sekarang)
        b = await self._sambungan.fetchrow(_CABUT, pemilik, sekarang)
        return b is not None

    async def jumlah_catatan_persetujuan(self, pemilik: str) -> int:
        b = await self._sambungan.fetchrow(
            "SELECT count(*) AS n FROM pengguna.persetujuan WHERE id_pengguna = $1", pemilik
        )
        return 0 if b is None else int(b["n"])  # type: ignore[call-overload]
