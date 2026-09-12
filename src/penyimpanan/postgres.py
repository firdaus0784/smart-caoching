"""Pelaksana `PenyimpanDasar` di atas PostgreSQL — T-3 fitur 024.

R-01 menuntut pelaksana ini lulus rangkaian uji yang **sama** dengan
`PenyimpanTiruan`, tanpa satu pun uji diubah.

## Urutan yang menentukan, dan sebabnya

Kredensial diperiksa **sebelum** basis data disentuh — sebelum menyambung,
sebelum menyusun kueri. Bukan penghematan, melainkan C-03: penyimpan yang
memeriksa keberadaan dokumen lebih dulu membocorkan keberadaan dokumen
karantina lewat perbedaan galat, dan itu meruntuhkan C-03 **tanpa satu pun
dokumen terbaca**.

Yang membuat pelaksana ini berbeda dari tiruan: pemeriksaan kredensial di sini
**bukan** penjagaan terakhir. Sambungannya sendiri dibangun dari pengguna basis
data yang memang tidak diberi hak atas skema karantina, sehingga kueri yang
lolos pemeriksaan kode pun tetap ditolak peladen. Dua lapis, dan yang kedua
tidak dapat dilewati kekeliruan kode mana pun.

## Satu tabel per area, bukan satu tabel dengan kolom penanda

`docs/D14.md` Bagian 5.1 menyebut `dokumen_sumber.area_simpan`, dan ADR-06
menegaskan kredensial berbeda — bukan penanda. Hak akses PostgreSQL berlaku
pada skema dan tabel, **tidak pada nilai baris**, sehingga kolom penanda tidak
dapat dijaga peladen. Memisahkan tabel per skema membuat area terbaca dari
tempatnya alih-alih dari isinya.

## Sambungan disuntikkan, tidak disusun sendiri

R-06: pemanggil yang memilih. Pelaksana yang menyusun sambungannya sendiri dari
lingkungan memilih untuk pemanggilnya, dan pilihan yang tersembunyi di dalam
pustaka adalah pilihan yang tidak dapat diuji.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final, Protocol

from src.penyimpanan.area import Area
from src.penyimpanan.catatan_akses import CatatanAkses
from src.penyimpanan.dasar import PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenTidakAda
from src.penyimpanan.kredensial import Kredensial

if TYPE_CHECKING:  # pragma: no cover — hanya bagi pemeriksa tipe
    from collections.abc import Awaitable, Mapping

SKEMA: Final[dict[Area, str]] = {
    Area.KARANTINA: "karantina",
    Area.KORPUS: "korpus",
}
"""Nama skema per area — `perkakas/basis_data/02-skema-dan-hak.sql`.

Bukan disusun dari `area.value` saat jalan. Nama skema yang dirakit dari nilai
enum akan ikut berubah diam-diam ketika enum berubah, dan yang berubah
bersamanya adalah kueri yang sudah berjalan di lingkungan sungguhan.
"""

TABEL: Final = "dokumen_sumber"
"""`docs/D14.md` Bagian 5."""


class Sambungan(Protocol):
    """Permukaan `asyncpg` yang dipakai modul ini — dan hanya itu.

    Dinyatakan sebagai protokol agar uji dapat memasok sambungan lain tanpa
    pelaksana ini mengimpor `asyncpg` secara langsung. Yang tidak disebut di
    sini tidak dipakai.
    """

    def fetchrow(
        self, kueri: str, /, *argumen: object
    ) -> Awaitable[Mapping[str, object] | None]: ...
    def execute(self, kueri: str, /, *argumen: object) -> Awaitable[object]: ...


class PenyimpanPostgres(PenyimpanDasar):
    """Penyimpan di atas PostgreSQL. Isinya bertahan sesudah proses berhenti."""

    def __init__(self, sambungan: Sambungan, catatan: CatatanAkses | None = None) -> None:
        self._sambungan = sambungan
        self._catatan = catatan

    # ── pemeriksaan kredensial — sebelum basis data disentuh ──────────

    def _tolak(self, kredensial: Kredensial, area: Area, operasi: str) -> GalatAksesDitolak:
        """Bentuk yang sama persis dengan `PenyimpanTiruan` — R-08.

        Pencatatan mendahului pelemparan agar percobaan tetap tercatat meski
        pemanggil menangkap galatnya dan berpura-pura tidak terjadi apa-apa.

        Hanya penolakan yang dicatat di sini, mengikuti tiruan. Pencatatan
        jalur yang berhasil adalah tugas T-7, dan mengerjakannya lebih awal
        akan membuat kedua pelaksana berbeda bentuk catatannya.
        """
        if self._catatan is not None:
            self._catatan.catat(kredensial.nama, operasi, area)
        return GalatAksesDitolak(kredensial=kredensial, area=area, operasi=operasi)

    def _pastikan_boleh_baca(self, kredensial: Kredensial, area: Area) -> None:
        if not kredensial.boleh_baca(area):
            raise self._tolak(kredensial, area, "baca")

    def _pastikan_boleh_tulis(self, kredensial: Kredensial, area: Area) -> None:
        if not kredensial.boleh_tulis(area):
            raise self._tolak(kredensial, area, "tulis")

    # ── kontrak ──────────────────────────────────────────────────────

    async def baca_dokumen(self, kredensial: Kredensial, area: Area, id_dokumen: str) -> object:
        self._pastikan_boleh_baca(kredensial, area)
        baris = await self._sambungan.fetchrow(
            f"SELECT isi FROM {SKEMA[area]}.{TABEL} WHERE id = $1", id_dokumen
        )
        if baris is None:
            raise GalatDokumenTidakAda(id_dokumen)
        isi = baris["isi"]
        return json.loads(isi) if isinstance(isi, str) else isi

    async def tulis_dokumen(
        self, kredensial: Kredensial, area: Area, id_dokumen: str, isi: object
    ) -> None:
        self._pastikan_boleh_tulis(kredensial, area)
        await self._sambungan.execute(
            f"INSERT INTO {SKEMA[area]}.{TABEL} (id, isi) VALUES ($1, $2) "
            f"ON CONFLICT (id) DO UPDATE SET isi = EXCLUDED.isi",
            id_dokumen,
            json.dumps(isi),
        )

    async def pindahkan(
        self, kredensial: Kredensial, id_dokumen: str, dari: Area, ke: Area, alasan: str
    ) -> None:
        """Pindahkan dokumen antar area dalam **satu pernyataan**.

        Kedua kredensial diperiksa sebelum dokumen disentuh — memeriksa tujuan
        sesudah asal terbaca meninggalkan dokumen terbaca oleh pemanggil yang
        tidak berhak menuliskannya ke mana pun.

        `DELETE ... RETURNING` yang menyuapi `INSERT` menjadikan pemindahan satu
        pernyataan, sehingga sambungan yang putus di tengah tidak meninggalkan
        salinan pada kedua area. Salinan mentah yang tertinggal di karantina
        adalah persis yang ADR-06 cegah.

        `alasan` tidak disimpan di sini; yang mencatatnya `jejak_area`.
        """
        self._pastikan_boleh_baca(kredensial, dari)
        self._pastikan_boleh_tulis(kredensial, ke)
        baris = await self._sambungan.fetchrow(
            f"WITH terangkat AS ("
            f"  DELETE FROM {SKEMA[dari]}.{TABEL} WHERE id = $1 RETURNING id, isi"
            f") INSERT INTO {SKEMA[ke]}.{TABEL} (id, isi) "
            f"SELECT id, isi FROM terangkat RETURNING id",
            id_dokumen,
        )
        if baris is None:
            raise GalatDokumenTidakAda(id_dokumen)
