"""Dari dokumen korpus ke segmen terindeks — T-5 fitur 038, R-02 s.d. R-07; K-3.

Satu fungsi, `indekskan`: membaca bahan dokumen korpus, memotongnya menurut
D-07 Bagian 3.2 (`segmentasi.py`), menetapkan lisensi dan indeks tujuan, lalu
— bila diminta menulis — mengganti seluruh segmen dokumen itu.

## Lisensi dan indeks tujuan: fitur 006 apa adanya

`lisensi_dari_metadata` membaca keterangan pada catatan metadata korpus
terbaru; kosong dan tak dikenal berarti tertutup (KL-01). `indeks_bagi`
menetapkan tujuannya saat masuk (R-03). Jenis dokumen tidak disebut di sini
sama sekali: lisensi tidak disimpulkan dari jenis, dan peringkat kepercayaan
maupun status keberlakuan tidak disimpan pada segmen (P-4 A).

## Mengapa `anonimisasi_terverifikasi` benar

Bahan hanya terjangkau dari korpus (R-04), dan korpus hanya terisi lewat
persetujuan gerbang, yang menuntut anonimisasi terverifikasi (fitur 002,
FR-B05). Dokumen yang persetujuannya dicabut keluar dari korpus beserta
segmennya (TK-84 A). Nilai ini kesimpulan dari tempat, bukan tebakan.

## Pengenal

`<id_dokumen>:<urutan empat digit>` mulai `0001` — D-14 Bagian 5.1.
Deterministik: teks yang sama menghasilkan pengenal yang sama (R-06).

## Yang dikembalikan

Penanda dan jumlah kata tiap segmen, tanpa teksnya (R-07): ringkasan ini yang
dicetak perkakas, dan teks segmen tidak pernah sampai ke keluaran atau log.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ingest.segmentasi import potong
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.indeks import SegmenTerindeks, indeks_bagi, lisensi_dari_metadata
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.pengindeks import PenulisIndeks


@dataclass(frozen=True)
class RingkasanSegmen:
    """Satu segmen tanpa teksnya."""

    penanda: str
    jumlah_kata: int


@dataclass(frozen=True)
class HasilPengindeksan:
    id_dokumen: str
    indeks_tujuan: IndeksTujuan
    segmen: tuple[RingkasanSegmen, ...]
    ditulis: bool
    """`False` pada pratinjau: tidak satu baris pun ditulis."""


def pengenal_segmen(id_dokumen: str, urutan: int) -> str:
    """D-14 Bagian 5.1: pengenal dokumen, titik dua, urutan empat digit."""
    return f"{id_dokumen}:{urutan:04d}"


async def indekskan(
    penulis: PenulisIndeks, kredensial: Kredensial, id_dokumen: str, *, tulis: bool
) -> HasilPengindeksan:
    """Potong dan, bila `tulis`, ganti segmen dokumen korpus itu.

    `GalatDokumenTidakAda` bila dokumennya tidak di korpus — termasuk yang di
    karantina — sebelum apa pun ditulis.
    """
    bahan = await penulis.bahan(kredensial, id_dokumen)
    lisensi = lisensi_dari_metadata(bahan.lisensi)
    tujuan = indeks_bagi(lisensi)
    segmen = [
        SegmenTerindeks(
            id_segmen=pengenal_segmen(id_dokumen, urutan),
            id_dokumen=id_dokumen,
            teks=p.teks,
            lisensi=lisensi,
            indeks_tujuan=tujuan,
            anonimisasi_terverifikasi=True,
            penanda_bagian=p.penanda,
        )
        for urutan, p in enumerate(potong(bahan.teks), start=1)
    ]
    if tulis:
        await penulis.ganti(kredensial, id_dokumen, segmen)
    return HasilPengindeksan(
        id_dokumen=id_dokumen,
        indeks_tujuan=tujuan,
        segmen=tuple(RingkasanSegmen(s.penanda_bagian, len(s.teks.split())) for s in segmen),
        ditulis=tulis,
    )
