"""Pembaca sumber — T-4 fitur 032, R-04 s.d. R-07; K-3; FR-F11; D-14 Bagian 4.10.

Satu tempat bagi aturan tampil `GET /api/v1/sumber/{id}`. Rute di
`src/api/aplikasi.py` hanya menerjemahkan galat dan merekam; penyimpan hanya
membaca baris mentah.

## Alasan tanpa teks, berurutan

Yang pertama berlaku menetapkan `tanpa_teks`, dan teks tidak dikirim:

1. `dokumen_tidak_publik` — tingkat kerahasiaan bukan `publik`, **atau**
   dokumen sekolah pada tingkat mana pun. Alasannya sama dengan
   `Dokumen.boleh_masuk_korpus`: dokumen sekolah yang ditandai `publik` tetap
   milik sekolah itu, dan cakupan persetujuan pemiliknya bagi penayangan teks
   kepada peserta lain milik tim etik (ET-04, P-2 A).
2. `status_belum_tercatat` — regulasi tanpa catatan status (TK-81 A). Status
   yang tidak diketahui **bukan** `berlaku`.
3. `dokumen_dicabut` — status terbaru `dicabut`. Teks aturan yang tidak
   berlaku, dibuka dari jawaban, terbaca sebagai dasar jawaban itu (C-07).
4. `bagian_tidak_tersedia` — tidak ada segmen bagian itu yang berlisensi
   terbuka **dan** beranonimisasi terverifikasi.

## Pembaca tidak bertindak

Tidak memanggil model maupun jalur penjawab, tidak menulis apa pun selain
peristiwa yang direkam rutenya (R-05, C-08, C-17).
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict

from src.api.galat import LOG_OPERASIONAL
from src.ingest.dokumen import TingkatKerahasiaan
from src.ingest.peringkat import JenisSumber
from src.kamus.segmen import StatusKeberlakuan
from src.penyimpanan.indeks import StatusLisensi
from src.penyimpanan.sumber import BarisSumber, PembacaSumber, SegmenBagian

PESAN_SUMBER_TIDAK_ADA: Final = "Dokumen ini tidak dapat dibuka di aplikasi."
PESAN_BAGIAN_TIDAK_SAH: Final = (
    "Bagian dokumen tidak dikenali. Buka lagi dari daftar dasar rujukan."
)
"""C-13: ≤ 20 kata, tanpa istilah teknis, tanpa mengutip masukan."""


class AlasanTanpaTeks(Enum):
    """Mengapa teks bagian tidak dikirim — D-14 Bagian 4.10."""

    DOKUMEN_TIDAK_PUBLIK = "dokumen_tidak_publik"
    STATUS_BELUM_TERCATAT = "status_belum_tercatat"
    DOKUMEN_DICABUT = "dokumen_dicabut"
    BAGIAN_TIDAK_TERSEDIA = "bagian_tidak_tersedia"


class SumberTampil(BaseModel):
    """Tanggapan `GET /api/v1/sumber/{id}` — D-14 Bagian 4.10, C-20."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_dokumen: str
    judul: str
    jenis: JenisSumber
    penerbit: str
    tahun: int
    status_keberlakuan: StatusKeberlakuan | None
    rujukan_pengganti: str | None
    bagian: str
    teks_bagian: list[str]
    tanpa_teks: AlasanTanpaTeks | None


class SumberTidakTampil(Exception):
    """Tidak di korpus, tanpa metadata, atau metadatanya tidak terbaca — satu
    bentuk 404 (R-04)."""


def _alasan(
    jenis: JenisSumber,
    tingkat: TingkatKerahasiaan,
    status: StatusKeberlakuan | None,
    teks: list[str],
) -> AlasanTanpaTeks | None:
    if tingkat is not TingkatKerahasiaan.PUBLIK or jenis is JenisSumber.DOKUMEN_SEKOLAH:
        return AlasanTanpaTeks.DOKUMEN_TIDAK_PUBLIK
    if jenis is JenisSumber.REGULASI_RESMI and status is None:
        return AlasanTanpaTeks.STATUS_BELUM_TERCATAT
    if status is StatusKeberlakuan.DICABUT:
        return AlasanTanpaTeks.DOKUMEN_DICABUT
    if not teks:
        return AlasanTanpaTeks.BAGIAN_TIDAK_TERSEDIA
    return None


def _boleh_tampil(segmen: SegmenBagian) -> bool:
    """Lisensi terbuka **dan** terverifikasi, satu per satu (R-04, R-06).
    Nilai lisensi yang tidak dikenal diperlakukan tertutup (D-06)."""
    try:
        terbuka = StatusLisensi(segmen.lisensi) is StatusLisensi.TERBUKA
    except ValueError:
        return False
    return terbuka and segmen.anonimisasi_terverifikasi


def _terbaca(
    baris: BarisSumber,
) -> tuple[JenisSumber, TingkatKerahasiaan, StatusKeberlakuan | None]:
    """Nilai enum dari catatan; yang tidak dikenal menjadi `SumberTidakTampil`.
    Log menyebut dokumen dan jenis galatnya saja, tidak isi catatannya (pola
    TK-78)."""
    try:
        return (
            JenisSumber(baris.metadata.jenis),
            TingkatKerahasiaan(baris.metadata.tingkat_kerahasiaan),
            None if baris.status is None else StatusKeberlakuan(baris.status),
        )
    except ValueError as galat:
        LOG_OPERASIONAL.warning(
            "catatan dokumen tidak terbaca id_dokumen=%s sebab=%s",
            baris.id_dokumen,
            type(galat).__name__,
        )
        raise SumberTidakTampil(baris.id_dokumen) from None


async def baca_sumber(pembaca: PembacaSumber, id_dokumen: str, bagian: str | None) -> SumberTampil:
    """`ValueError` bagi bagian kosong; `SumberTidakTampil` bagi 404."""
    if bagian is None or not bagian.strip():
        raise ValueError("bagian wajib")
    baris = await pembaca.dokumen(id_dokumen)
    if baris is None:
        raise SumberTidakTampil(id_dokumen)
    jenis, tingkat, status = _terbaca(baris)
    teks = [s.teks for s in await pembaca.segmen(id_dokumen, bagian) if _boleh_tampil(s)]
    alasan = _alasan(jenis, tingkat, status, teks)
    return SumberTampil(
        id_dokumen=baris.id_dokumen,
        judul=baris.metadata.judul,
        jenis=jenis,
        penerbit=baris.metadata.penerbit,
        tahun=baris.metadata.tahun,
        status_keberlakuan=status,
        rujukan_pengganti=baris.rujukan_pengganti,
        bagian=bagian,
        teks_bagian=teks if alasan is None else [],
        tanpa_teks=alasan,
    )
