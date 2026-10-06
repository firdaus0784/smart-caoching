"""Penemuan — T-6 fitur 013, R-02, R-05 s.d. R-08; K-2; D-14 Bagian 4.6.

Penerjemah antara tiga rute pengguna dan penyimpan penemuan. Aturan isinya
**tidak ditulis di sini**: pemilihan, pagu, dan urutan milik `susun_feed()`
fitur 011; lisensi milik `boleh_teks_penuh()`; "belum relevan" milik
`tandai_belum_relevan()`. Menulis ulang salah satunya di sini akan menghasilkan
dua tempat yang berselisih.

## Butir tayang lewat gerbangnya

`susun_feed()` menerima `ButirTayang`, dan pemeriksa C-06 membatasi
pembentukannya pada modul putusan. Tiap baris karena itu dibentuk lewat
`terapkan()` atas **putusan yang menayangkannya** — dibaca dari basis data,
tanpa pemutus maupun alasan (KB-185). Pembentukan itu juga menjalankan lapis
C-07 dengan **status salinan terkini**: regulasi yang dicabut tidak tampil
meski penarikannya belum berjalan.

## Butir hari ini (K-2)

Yang sudah tampil pada tanggal WIB itu tetap tampil, berurutan; sisa pagu
diisi butir baru yang belum pernah tayang baginya dan tidak ditolaknya.
Pemilihan tidak membaca apa pun selain prioritas yang ia pilih sendiri (C-14).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from src.api.hari import tanggal_wib
from src.api.kurasi import bentuk_ulang
from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.ingest.kurasi.putusan import ButirTayang, GalatPutusan
from src.ingest.kurasi.sumber import SumberButir
from src.nlp.anotasi.skema import KategoriMasalah
from src.pengguna.feed import GalatFeed, boleh_teks_penuh, susun_feed, tandai_belum_relevan
from src.pengguna.prioritas import PrioritasManajerial
from src.penyimpanan.kurasi import BarisTayang
from src.penyimpanan.penemuan import PenyimpanPenemuan
from src.penyimpanan.pengguna import PenyimpanPengguna

PESAN_ALASAN_TIDAK_SAH: Final = "Tulis alasan singkat tanpa nomor pribadi, lalu kirim lagi."
"""C-13: ≤ 20 kata, tanpa istilah teknis, **tanpa mengutip masukan**."""


TAJUK_TUJUAN: Final = "x-tujuan"
TUJUAN_SALINAN: Final = "salinan"
"""Tajuk penanda pengambilan latar bagi salinan luring — K-7 fitur 034, KB-199,
D-14 Bagian 4.6. Ia hanya menentukan apakah `discovery_opened` direkam; bentuk
tanggapan tidak bergantung padanya. Nilai lain diabaikan."""


def bukan_butir_dibuka(tajuk: Mapping[str, str]) -> bool:
    """Pengambilan latar beranda (P-7 fitur 013), bukan butir yang dibuka (TK-74)."""
    return tajuk.get(TAJUK_TUJUAN) == TUJUAN_SALINAN


class ButirTidakTampil(Exception):
    """Tidak dikenal, belum tayang bagi pemanggil, ditarik, atau tak berlaku —
    satu bentuk 404 (D-14 Bagian 4.6)."""


class PermintaanTolak(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    alasan: str


# ── bentuk tanggapan — D-14 Bagian 4.6 ───────────────────────────────
#
# Model bernama, bukan kamus lepas: `web/src/kontrak.ts` menyalinnya, dan
# pemeriksa kontrak V-03 membandingkan keduanya (C-20). Kamus lepas tidak
# memiliki nama untuk dibandingkan.


class KeadaanBeranda(Enum):
    BERISI = "berisi"
    BELUM_ADA_PRIORITAS = "belum_ada_prioritas"
    BELUM_ADA_BUTIR = "belum_ada_butir"
    HABIS = "habis"


class _Tanggapan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ButirRingkas(_Tanggapan):
    id_butir: str
    kategori: KategoriMasalah
    jenis_sumber: JenisSumberButir
    judul: str
    alasan_relevansi: str
    perkiraan_waktu_baca: int


class ButirLengkap(ButirRingkas):
    inti_temuan: str
    implikasi_tindakan: list[str]
    tenggat_terkait: date | None
    boleh_teks_penuh: bool
    sumber: SumberButir


class Beranda(_Tanggapan):
    keadaan: KeadaanBeranda
    butir: list[ButirRingkas]


def _tayang_sah(baris: BarisTayang) -> ButirTayang | None:
    """Butir yang masih boleh tampil, atau `None` — ditarik, tanpa putusan yang
    menyetujui, atau regulasinya tidak lagi berlaku menurut status terkini."""
    if baris.ditarik_pada is not None:
        return None
    try:
        return bentuk_ulang(baris, status_terkini=True)
    except (GalatPutusan, RuntimeError):
        return None


def _ringkas(butir: ButirPengetahuan) -> ButirRingkas:
    return ButirRingkas(
        id_butir=butir.id_butir,
        kategori=butir.kategori,
        jenis_sumber=butir.jenis_sumber,
        judul=butir.judul,
        alasan_relevansi=butir.alasan_relevansi,
        perkiraan_waktu_baca=butir.perkiraan_waktu_baca,
    )


def _isi(keadaan: KeadaanBeranda, butir: list[ButirRingkas]) -> dict[str, Any]:
    return Beranda(keadaan=keadaan, butir=butir).model_dump(mode="json")


async def susun_beranda(
    penemuan: PenyimpanPenemuan,
    pengguna: PenyimpanPengguna,
    pemilik: str,
    *,
    sekarang: datetime,
) -> tuple[dict[str, Any], tuple[ButirRingkas, ...]]:
    """Tanggapan `GET /beranda` dan `POST /butir/{id}/tolak`, beserta butir yang
    **baru** tercatat pada pemanggilan ini — bagi `discovery_served` (fitur
    034). Muat ulang tidak menghasilkan butir baru, sebab yang sudah tercatat
    hari itu tidak dipilih lagi."""
    kode = await pengguna.baca_prioritas(pemilik)
    if not kode:
        return _isi(KeadaanBeranda.BELUM_ADA_PRIORITAS, []), ()
    hari = tanggal_wib(sekarang)
    hari_ini = await penemuan.catatan_hari_ini(pemilik, hari)
    pernah = await penemuan.pernah_tayang(pemilik)
    ditolak = await penemuan.ditolak(pemilik)

    # Butir yang ditolak tidak perlu disaring di sini: ia hanya dapat ditolak
    # bila pernah tayang baginya, sehingga sudah termasuk `pernah` (KB-185).
    tersedia = tuple(
        tayang
        for baris in await penemuan.tayang_menurut_kategori(kode)
        if baris.id_butir not in pernah
        for tayang in (_tayang_sah(baris),)
        if tayang is not None
    )
    prioritas = PrioritasManajerial(
        id_pengguna=pemilik, kategori=tuple(KategoriMasalah(k) for k in kode)
    )
    baru = susun_feed(prioritas=prioritas, tersedia=tersedia, sudah_tayang_hari_ini=len(hari_ini))
    if baru:
        await penemuan.catat_hari_ini(
            pemilik,
            hari,
            tuple(b.butir.id_butir for b in baru),
            sekarang=sekarang,
            mulai=len(hari_ini) + 1,
        )
        hari_ini = await penemuan.catatan_hari_ini(pemilik, hari)

    tampil = []
    for id_butir in hari_ini:
        if id_butir in ditolak:
            continue
        baris = await penemuan.baca_tayang(id_butir)
        tayang = None if baris is None else _tayang_sah(baris)
        if tayang is not None:
            tampil.append(_ringkas(tayang.butir))
    tercatat = tuple(_ringkas(b.butir) for b in baru)
    if tampil:
        return _isi(KeadaanBeranda.BERISI, tampil), tercatat
    sudah_pernah = pernah or bool(hari_ini)
    keadaan = KeadaanBeranda.HABIS if sudah_pernah else KeadaanBeranda.BELUM_ADA_BUTIR
    return _isi(keadaan, []), tercatat


async def detail(penemuan: PenyimpanPenemuan, pemilik: str, id_butir: str) -> dict[str, Any]:
    """Butir lengkap — hanya yang pernah tayang bagi pemanggil dan masih sah."""
    if id_butir not in await penemuan.pernah_tayang(pemilik):
        raise ButirTidakTampil(id_butir)
    baris = await penemuan.baca_tayang(id_butir)
    tayang = None if baris is None else _tayang_sah(baris)
    if baris is None or tayang is None:
        raise ButirTidakTampil(id_butir)
    butir = tayang.butir
    return ButirLengkap(
        **_ringkas(butir).model_dump(),
        inti_temuan=butir.inti_temuan,
        implikasi_tindakan=list(butir.implikasi_tindakan),
        tenggat_terkait=butir.tenggat_terkait,
        boleh_teks_penuh=boleh_teks_penuh(butir),
        sumber=SumberButir.model_validate(baris.sumber),
    ).model_dump(mode="json")


async def tolak(
    penemuan: PenyimpanPenemuan,
    pemilik: str,
    id_butir: str,
    badan: Any,
    *,
    sekarang: datetime,
) -> str:
    """ "Belum relevan" — `ButirTidakTampil` bila bukan butirnya; `ValueError`
    bagi alasan yang tidak sah. Mengembalikan alasan sebagaimana tercatat, agar
    perekam mengukur yang tersimpan, bukan masukan mentah (fitur 034)."""
    await detail(penemuan, pemilik, id_butir)
    try:
        permintaan = PermintaanTolak.model_validate(badan)
        umpan = tandai_belum_relevan(
            id_pengguna=pemilik, id_butir=id_butir, alasan=permintaan.alasan
        )
    except (ValidationError, GalatFeed) as galat:
        raise ValueError("alasan tidak sah") from galat
    await penemuan.catat_belum_relevan(pemilik, id_butir, umpan.alasan, sekarang=sekarang)
    return umpan.alasan
