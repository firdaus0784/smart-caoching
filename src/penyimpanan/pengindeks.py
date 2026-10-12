"""Penulis indeks — T-5 fitur 038, R-03, R-04, R-05; K-3; P-2 A, TK-86.

Dua pekerjaan saja: membaca **bahan** dokumen korpus (teks dan keterangan
lisensi terbarunya), dan **mengganti** seluruh segmen dokumen itu. Pemotongan
dan penetapan indeks tujuan milik `src/ingest/pengindeksan.py`; di sini segmen
sudah berbentuk `SegmenTerindeks`, yang menolak lisensi tertutup di indeks
utama saat dibentuk (C-02).

## Penggantian satu pernyataan

`ganti` menghapus segmen dokumen itu dari **kedua** indeks lalu menyisipkan
yang baru ke indeks tujuannya, dalam satu pernyataan, hanya bila dokumennya
berada di korpus (R-04, R-05). Sambungan yang putus di mana pun meninggalkan
segmen lama seluruhnya atau baru seluruhnya. Penghapusan dan penyisipan kunci
yang sama dalam satu pernyataan diverifikasi pada peladen sebelum plan
(KB-267).

Dari kedua indeks, bukan dari indeks tujuan saja: dokumen yang lisensinya
kini tertutup tidak boleh meninggalkan segmen di indeks utama.

## Urutan pemeriksaan

Kredensial lebih dulu — baca korpus, lalu tulis kedua indeks — kemudian bentuk
masukan, baru basis data. Penolakan menulis indeks berupa `PermissionError`,
sama dengan jalur penyematan: indeks bukan `Area`, dan `GalatAksesDitolak`
menyebut area. Pesan galat tidak pernah memuat teks dokumen (R-07, KM-03).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.area import Area
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenTidakAda
from src.penyimpanan.indeks import SegmenTerindeks
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.sambungan import SambunganAktif
from src.penyimpanan.skema_indeks import SKEMA_INDEKS, TABEL_SEGMEN

if TYPE_CHECKING:  # pragma: no cover — hanya bagi pemeriksa tipe
    from src.penyimpanan.tiruan import PenyimpanTiruan

PERAN_PENGINDEKS: Final = "peran_pengindeks"
"""Peran basis data penulis segmen — `16-segmen-dan-lisensi.sql`."""


@dataclass(frozen=True)
class BahanDokumen:
    """Teks dokumen korpus dan keterangan lisensi pada catatan metadata
    terbarunya, apa adanya. Kosong tidak diartikan di sini (KL-01)."""

    teks: str
    lisensi: str | None


def _pastikan_baca_korpus(kredensial: Kredensial) -> None:
    if not kredensial.boleh_baca(Area.KORPUS):
        raise GalatAksesDitolak(kredensial=kredensial, area=Area.KORPUS, operasi="baca")


def _pastikan_boleh_ganti(
    kredensial: Kredensial, id_dokumen: str, segmen: Sequence[SegmenTerindeks]
) -> None:
    _pastikan_baca_korpus(kredensial)
    for indeks in IndeksTujuan:
        if not kredensial.boleh_tulis_indeks(indeks):
            raise PermissionError(
                f"kredensial {kredensial.nama!r} tidak boleh menulis ke {indeks.value} — "
                "penggantian menghapus dari kedua indeks (TK-86, C-17)"
            )
    if any(s.id_dokumen != id_dokumen for s in segmen):
        raise ValueError(f"segmen yang diganti wajib milik dokumen {id_dokumen}")
    if len({s.id_segmen for s in segmen}) != len(segmen):
        raise ValueError("pengenal segmen kembar")


def _teks_dari(isi: object) -> str:
    if not isinstance(isi, str):
        raise ValueError("isi dokumen korpus bukan teks; dokumen ini tidak dapat dipotong")
    return isi


class PenulisIndeks(ABC):
    """Kontrak penulis segmen. Kredensial tepat sesudah `self`."""

    @abstractmethod
    async def bahan(self, kredensial: Kredensial, id_dokumen: str) -> BahanDokumen:
        """`GalatDokumenTidakAda` bila dokumennya tidak di korpus — termasuk
        yang berada di karantina, dalam bentuk yang sama."""

    @abstractmethod
    async def ganti(
        self, kredensial: Kredensial, id_dokumen: str, segmen: Sequence[SegmenTerindeks]
    ) -> None:
        """Seluruh segmen dokumen itu diganti, atau tidak satu pun berubah.
        `GalatDokumenTidakAda` tanpa menulis apa pun bila dokumennya tidak di
        korpus."""


# ── Memori ────────────────────────────────────────────────────────────


class PenulisIndeksMemori(PenulisIndeks):
    """Pelaksana memori di atas `PenyimpanTiruan`: korpus dan catatan
    metadatanya dibaca dari sana, segmen disimpan di sini."""

    def __init__(self, penyimpan: PenyimpanTiruan) -> None:
        self._penyimpan = penyimpan
        self._segmen: dict[IndeksTujuan, dict[str, SegmenTerindeks]] = {
            indeks: {} for indeks in IndeksTujuan
        }

    def segmen_tersimpan(
        self, indeks: IndeksTujuan, id_dokumen: str
    ) -> tuple[SegmenTerindeks, ...]:
        """Segmen dokumen itu pada satu indeks, berurutan pengenal — bagi uji,
        bukan kontrak."""
        isi = self._segmen[indeks]
        return tuple(isi[k] for k in sorted(isi) if isi[k].id_dokumen == id_dokumen)

    async def bahan(self, kredensial: Kredensial, id_dokumen: str) -> BahanDokumen:
        _pastikan_baca_korpus(kredensial)
        teks = _teks_dari(await self._penyimpan.baca_dokumen(kredensial, Area.KORPUS, id_dokumen))
        metadata = self._penyimpan.metadata_tercatat(id_dokumen)
        return BahanDokumen(teks=teks, lisensi=metadata[-1].lisensi if metadata else None)

    async def ganti(
        self, kredensial: Kredensial, id_dokumen: str, segmen: Sequence[SegmenTerindeks]
    ) -> None:
        _pastikan_boleh_ganti(kredensial, id_dokumen, segmen)
        await self._penyimpan.baca_dokumen(kredensial, Area.KORPUS, id_dokumen)
        for isi in self._segmen.values():
            for kunci in [k for k, s in isi.items() if s.id_dokumen == id_dokumen]:
                del isi[kunci]
        for s in segmen:
            self._segmen[s.indeks_tujuan][s.id_segmen] = s


# ── PostgreSQL ────────────────────────────────────────────────────────

_BAHAN: Final = """
SELECT d.isi,
  (SELECT m.lisensi FROM korpus.metadata_dokumen m WHERE m.id_dokumen = d.id
   ORDER BY m.nomor DESC LIMIT 1) AS lisensi
FROM korpus.dokumen_sumber d WHERE d.id = $1
"""
"""Hanya korpus; peran pengindeks tidak memegang skema karantina sama sekali."""

_KOLOM_SISIP: Final = 5
"""Larik per indeks: pengenal, teks, lisensi, anonimisasi, penanda."""


def _ganti_sql() -> str:
    bagian = ["ada AS (SELECT 1 FROM korpus.dokumen_sumber WHERE id = $1)"]
    for tujuan, skema in SKEMA_INDEKS.items():
        bagian.append(
            f"hapus_{tujuan.value} AS (DELETE FROM {skema}.{TABEL_SEGMEN} "
            "WHERE id_dokumen = $1 AND EXISTS (SELECT 1 FROM ada) RETURNING id_segmen)"
        )
    terhapus = " + ".join(f"(SELECT count(*) FROM hapus_{t.value})" for t in SKEMA_INDEKS)
    bagian.append(f"terhapus AS (SELECT {terhapus} AS jumlah)")
    for urutan, (tujuan, skema) in enumerate(SKEMA_INDEKS.items()):
        n = 2 + urutan * _KOLOM_SISIP
        bagian.append(
            f"sisip_{tujuan.value} AS (INSERT INTO {skema}.{TABEL_SEGMEN} "
            "(id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian) "
            "SELECT s.id, $1, s.teks, s.lisensi, s.anonimisasi, s.penanda "
            f"FROM unnest(${n}::text[], ${n + 1}::text[], ${n + 2}::text[], "
            f"${n + 3}::bool[], ${n + 4}::text[]) "
            "AS s(id, teks, lisensi, anonimisasi, penanda) "
            "WHERE EXISTS (SELECT 1 FROM ada) AND (SELECT jumlah FROM terhapus) >= 0)"
        )
    return "WITH " + ", ".join(bagian) + " SELECT EXISTS (SELECT 1 FROM ada) AS ada"


_GANTI: Final = _ganti_sql()
"""Satu pernyataan: hapus dari kedua indeks, sisip ke indeks tujuan, hanya
bila dokumennya di korpus. Nama skema dari `skema_indeks.py`.

**Sisip membaca `terhapus`, dan itu bukan hiasan.** PostgreSQL tidak menjamin
urutan bagian `WITH` yang mengubah data: bagian yang tidak dibaca siapa pun
dijalankan sesudah kueri utama, sehingga sisip mendahului hapus dan pengenal
yang sama ditolak sebagai kembar. Syarat yang selalu benar itu memaksa kedua
penghapusan selesai lebih dulu — ditemukan uji T-5, bukan verifikasi KB-267,
yang hanya mencoba indeks yang kosong (KB-272)."""


class PenulisIndeksPostgres(PenulisIndeks):
    """Sambungannya wajib tersambung sebagai `PERAN_PENGINDEKS`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def bahan(self, kredensial: Kredensial, id_dokumen: str) -> BahanDokumen:
        _pastikan_baca_korpus(kredensial)
        baris: Any = await self._sambungan.fetchrow(_BAHAN, id_dokumen)
        if baris is None:
            raise GalatDokumenTidakAda(id_dokumen)
        isi = baris["isi"]
        teks = _teks_dari(json.loads(isi) if isinstance(isi, str) else isi)
        lisensi = baris["lisensi"]
        return BahanDokumen(teks=teks, lisensi=None if lisensi is None else str(lisensi))

    async def ganti(
        self, kredensial: Kredensial, id_dokumen: str, segmen: Sequence[SegmenTerindeks]
    ) -> None:
        _pastikan_boleh_ganti(kredensial, id_dokumen, segmen)
        argumen: list[object] = [id_dokumen]
        for tujuan in SKEMA_INDEKS:
            bagian = [s for s in segmen if s.indeks_tujuan is tujuan]
            argumen += [
                [s.id_segmen for s in bagian],
                [s.teks for s in bagian],
                [s.lisensi.value for s in bagian],
                [s.anonimisasi_terverifikasi for s in bagian],
                [s.penanda_bagian for s in bagian],
            ]
        baris: Any = await self._sambungan.fetchrow(_GANTI, *argumen)
        if baris is None or not baris["ada"]:
            raise GalatDokumenTidakAda(id_dokumen)
