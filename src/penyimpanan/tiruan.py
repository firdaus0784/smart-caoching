"""Penyimpan tiruan dalam memori — R-01a, R-02, R-04, C-03, ADR-06, ADR-12.

Pelaksana deterministik untuk pengembangan dan pengujian. PostgreSQL adalah
pekerjaan penyebaran D-09; yang diuji di sini **aturan aksesnya**, bukan
ketahanan penyimpanannya.

**Urutan pemeriksaan adalah kendalinya.** Kredensial diperiksa sebelum data
disentuh, tanpa pengecualian. Penyimpan yang memeriksa keberadaan lebih dulu
membocorkan keberadaan dokumen karantina lewat perbedaan galat — pemanggil yang
menerima "tidak ditemukan" untuk satu id dan "tidak berwenang" untuk id lain
sudah mengetahui id mana yang ada di sana. Cukup satu perbedaan untuk menyusun
daftar, dan C-03 runtuh tanpa satu pun dokumen terbaca.

Karena itu `GalatDokumenTidakAda` hanya mungkin muncul pada area yang memang
dijangkau kredensial pemanggil. Di luar itu, jawabannya selalu sama.
"""

from __future__ import annotations

from src.penyimpanan.area import Area
from src.penyimpanan.catatan_akses import CatatanAkses
from src.penyimpanan.dasar import PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial import Kredensial


class GalatDokumenTidakAda(Exception):
    """Dokumen tidak ada pada area yang **boleh dibaca** pemanggil.

    Tidak pernah dilempar bagi area yang tidak dijangkau kredensialnya — di
    sana `GalatAksesDitolak` yang berlaku, tanpa memandang ada tidaknya
    dokumen.
    """


class PenyimpanTiruan(PenyimpanDasar):
    """Penyimpan dalam memori. Isinya hilang bersama objeknya."""

    def __init__(self, catatan: CatatanAkses | None = None) -> None:
        self._isi: dict[Area, dict[str, object]] = {area: {} for area in Area}
        self._catatan = catatan

    def tanam(self, area: Area, id_dokumen: str, isi: object) -> None:
        """Isi awal untuk pengujian, tanpa melewati pemeriksaan kredensial.

        Sengaja diberi nama yang tidak menyerupai `tulis_dokumen`: jalan pintas
        yang tampak seperti jalan biasa akan dipakai sebagai jalan biasa.
        """
        self._isi[area][id_dokumen] = isi

    def _tolak(self, kredensial: Kredensial, area: Area, operasi: str) -> GalatAksesDitolak:
        """Catat lalu susun galatnya.

        Pencatatan mendahului pelemparan agar percobaan tetap tercatat meski
        pemanggil menangkap galatnya dan berpura-pura tidak terjadi apa-apa.
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

    def baca_dokumen(self, kredensial: Kredensial, area: Area, id_dokumen: str) -> object:
        self._pastikan_boleh_baca(kredensial, area)
        if id_dokumen not in self._isi[area]:
            raise GalatDokumenTidakAda(id_dokumen)
        return self._isi[area][id_dokumen]

    def tulis_dokumen(
        self, kredensial: Kredensial, area: Area, id_dokumen: str, isi: object
    ) -> None:
        self._pastikan_boleh_tulis(kredensial, area)
        self._isi[area][id_dokumen] = isi

    def pindahkan(
        self, kredensial: Kredensial, id_dokumen: str, dari: Area, ke: Area, alasan: str
    ) -> None:
        """Baca dari asal, tulis ke tujuan, hapus dari asal.

        Kedua kredensial diperiksa **sebelum** dokumen disentuh. Memeriksa
        tujuan setelah asal terbaca meninggalkan dokumen terbaca oleh pemanggil
        yang tidak berhak menuliskannya ke mana pun.

        Dokumen dihapus dari asal, tidak disalin. Salinan mentah yang
        tertinggal di karantina adalah persis yang ADR-06 cegah.

        `alasan` **tidak disimpan di sini.** Yang mencatatnya adalah
        `jejak_area` pada tugas D-1; penyimpan tiruan menerimanya agar bentuk
        kontraknya sudah benar sejak sekarang.
        """
        self._pastikan_boleh_baca(kredensial, dari)
        self._pastikan_boleh_tulis(kredensial, ke)
        if id_dokumen not in self._isi[dari]:
            raise GalatDokumenTidakAda(id_dokumen)
        self._isi[ke][id_dokumen] = self._isi[dari].pop(id_dokumen)
