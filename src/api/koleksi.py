"""Koleksi — T-5 fitur 032, R-01, R-02, R-03; K-4; FR-G06, FR-G10; D-14 Bagian 4.10.

Satu tempat bagi aturan tiga rute koleksi. Rute di `src/api/aplikasi.py` hanya
menerjemahkan galat dan merekam.

## Kelayakan milik penemuan

Menyimpan menuntut butir yang **pernah tayang bagi pemanggil dan masih sah** —
pemeriksaan `detail()` fitur 013 apa adanya, sehingga 404-nya berbentuk sama
dengan detail butir (R-01). Daftar membaca butir tayang lewat penyimpan
penemuan; penyimpan koleksi hanya memegang tabelnya sendiri.

## Butir yang dasarnya berubah tetap terbaca

Butir yang ditarik, atau yang status regulasinya `diubah` atau `dicabut`, tetap
tampil beserta judul, catatan, dan isinya, dengan `dasar_berubah` — penandanya
tampil sebelum isi (P-4 A, D-06 Bagian 7.5). Menghapusnya dari koleksi tanpa
penjelasan merusak kepercayaan; menampilkannya tanpa penanda membuatnya terbaca
sebagai dasar yang masih berlaku.

## Koleksi bukan sinyal

Tidak satu fungsi di sini dipanggil pemilihan beranda maupun jalur penjawab
(R-03, C-14), dan peladen menolak penayang membaca tabelnya.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Final

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError

from src.api.galat import LOG_OPERASIONAL
from src.api.penemuan import ButirLengkap, detail, lengkap
from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.nlp.anotasi.skema import KategoriMasalah
from src.penyimpanan.koleksi import BarisKoleksi, PenyimpanKoleksi
from src.penyimpanan.kurasi import BarisTayang
from src.penyimpanan.penemuan import PenyimpanPenemuan

PESAN_CATATAN_TIDAK_SAH: Final = (
    "Catatan belum dapat disimpan. Hapus nama atau nomor pribadi, lalu simpan lagi."
)
PESAN_PENYARING_TIDAK_SAH: Final = "Pilihan penyaring tidak dikenali. Pilih lagi dari daftar."
PESAN_KOLEKSI_TIDAK_ADA: Final = "Butir ini tidak ada di koleksi Anda."
"""C-13: ≤ 20 kata, tanpa istilah teknis, **tanpa mengutip masukan**."""

_STATUS_BERUBAH: Final = frozenset({"diubah", "dicabut"})


class PermintaanSimpan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    catatan: str | None = None


class ButirKoleksi(ButirLengkap):
    """Satu butir koleksi — butir lengkap D-14 Bagian 4.6 ditambah tiga bidang."""

    catatan: str | None
    disimpan_pada: AwareDatetime
    dasar_berubah: bool


class Koleksi(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    koleksi: list[ButirKoleksi]


class ButirTidakDiKoleksi(Exception):
    """Bukan butir pada koleksi pemanggil — 404."""


def _catatan(badan: Any) -> str | None:
    """Catatan yang tersimpan: kosong menjadi `None`; berdata pribadi ditolak
    tanpa dikutip (R-02, KM-03)."""
    try:
        catatan = PermintaanSimpan.model_validate(badan).catatan
    except ValidationError as galat:
        raise ValueError("badan simpan tidak sah") from galat
    if catatan is None or not catatan.strip():
        return None
    if periksa_data_pribadi(catatan):
        raise ValueError("catatan berdata pribadi")
    return catatan


def _butir_koleksi(
    butir: ButirPengetahuan, tayang: BarisTayang, baris: BarisKoleksi
) -> ButirKoleksi:
    berubah = tayang.ditarik_pada is not None or tayang.status_keberlakuan in _STATUS_BERUBAH
    return ButirKoleksi(
        **lengkap(butir, tayang.sumber).model_dump(),
        catatan=baris.catatan,
        disimpan_pada=baris.disimpan_pada,
        dasar_berubah=berubah,
    )


async def simpan(
    penemuan: PenyimpanPenemuan,
    koleksi: PenyimpanKoleksi,
    pemilik: str,
    id_butir: str,
    badan: Any,
    *,
    sekarang: datetime,
) -> ButirKoleksi:
    """`ButirTidakTampil` bila bukan butir yang boleh dibuka pemanggil;
    `ValueError` bagi badan yang tidak sah. Kelayakan diperiksa lebih dulu,
    agar butir orang lain tidak dapat dibedakan lewat galat badan."""
    await detail(penemuan, pemilik, id_butir)
    catatan = _catatan(badan)
    baris = await koleksi.simpan(pemilik, id_butir, catatan, sekarang=sekarang)
    tayang = await penemuan.baca_tayang(id_butir)
    if tayang is None:  # pragma: no cover — `detail` baru saja membacanya
        raise RuntimeError("butir tayang hilang sesudah diperiksa")
    return _butir_koleksi(ButirPengetahuan.model_validate(tayang.butir), tayang, baris)


async def keluarkan(koleksi: PenyimpanKoleksi, pemilik: str, id_butir: str) -> None:
    if not await koleksi.keluarkan(pemilik, id_butir):
        raise ButirTidakDiKoleksi(id_butir)


def _penyaring(kategori: str | None, jenis_sumber: str | None) -> tuple[Any, Any]:
    try:
        return (
            None if kategori is None else KategoriMasalah(kategori),
            None if jenis_sumber is None else JenisSumberButir(jenis_sumber),
        )
    except ValueError as galat:
        raise ValueError("penyaring di luar daftar") from galat


async def daftar(
    penemuan: PenyimpanPenemuan,
    koleksi: PenyimpanKoleksi,
    pemilik: str,
    *,
    kategori: str | None = None,
    jenis_sumber: str | None = None,
) -> dict[str, Any]:
    """Koleksi pemanggil, terbaru lebih dulu, tersaring. Baris yang isinya
    tidak lagi memenuhi model dilewati dan dicatat tanpa isi (pola TK-78)."""
    saring_kategori, saring_jenis = _penyaring(kategori, jenis_sumber)
    hasil: list[ButirKoleksi] = []
    for baris in await koleksi.milik(pemilik):
        tayang = await penemuan.baca_tayang(baris.id_butir)
        if tayang is None:
            LOG_OPERASIONAL.warning("butir koleksi tanpa butir tayang id_butir=%s", baris.id_butir)
            continue
        try:
            butir = ButirPengetahuan.model_validate(tayang.butir)
            satu = _butir_koleksi(butir, tayang, baris)
        except ValidationError as galat:
            LOG_OPERASIONAL.warning(
                "butir koleksi tidak terbaca id_butir=%s sebab=%s",
                baris.id_butir,
                type(galat).__name__,
            )
            continue
        if saring_kategori is not None and butir.kategori is not saring_kategori:
            continue
        if saring_jenis is not None and butir.jenis_sumber is not saring_jenis:
            continue
        hasil.append(satu)
    return Koleksi(koleksi=hasil).model_dump(mode="json")
