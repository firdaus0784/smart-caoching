"""Penjawab korpus — T-6 fitur 039, R-01 s.d. R-08; K-5, K-6; P-2 A, P-3 A, P-4 A.

Merakit `Jalur` fitur 021 atas korpus PostgreSQL: memuat segmen lewat
`src/penyimpanan/korpus_penjawab.py`, memutus kelayakannya, membangun indeks
leksikal dan bahan validator dari baris yang layak, lalu menyerahkan semuanya
kepada `Jalur.jawab()`. Rute `/tanya` memanggil `jawab(pertanyaan)` saja;
modul ini yang melengkapi sisanya.

**Tidak dipasang pada titik jalan mana pun** (P-1 A). Ia menuntut ambang
berasal BT-29, penyemat, dan pembungkus model dari pemanggil, tanpa nilai
bawaan (R-07); ketiganya belum ada di luar uji.

Tinggal di `api` karena ia memanggil `ingest` (`peringkat_bagi`, `JenisSumber`,
`TingkatKerahasiaan`) dan `rag` sekaligus — tepi yang sah bagi `api` saja.

## Kelayakan sebelum indeks leksikal

Satu baris diperiksa berurutan; yang pertama berlaku menjadi alasannya:

1. tanpa catatan metadata, atau jenis dan tingkat kerahasiaannya tidak terbaca;
2. teksnya tidak boleh tampil — `teks_boleh_tayang` pembaca sumber (P-4 A);
3. indeks utama saja: lisensi dokumen kini tertutup menurut catatan metadata
   terbaru — lapis kedua TK-87 sampai segmennya diindeks ulang;
4. anonimisasi belum terverifikasi;
5. regulasi tanpa catatan status (P-3 A, TK-81 A);
6. berstatus `dicabut` (D-07 Bagian 4.5, C-07).

Hanya baris layak yang diindeks, sehingga yang tak layak tidak pernah menjadi
kandidat dan tidak ikut dihitung penilai kecukupan: tahap 6 mendahului tahap 7,
sesuai urutan D-07 Bagian 4. Alasan dihitung, tidak dibuang — perkakas `cari`
membacanya.

## Muatan diganti utuh

Sidik kedua indeks dibaca pada setiap `jawab()`. Bila berubah, muatan baru
dibangun seluruhnya lalu menggantikan yang lama dalam satu penugasan; yang
lama melayani sampai saat itu (R-06, D-07 Bagian 3.3).

Teks segmen tidak ditulis ke log (R-08); modul ini tidak menulis log sama
sekali.
"""

from __future__ import annotations

import uuid
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, cast

from src.api.sumber import teks_boleh_tayang
from src.api.tanya import BahanSegmen, HasilTanya, Jalur
from src.ingest.dokumen import TingkatKerahasiaan
from src.ingest.peringkat import JenisSumber, peringkat_bagi
from src.kamus.segmen import IndeksTujuan, Peringkat, StatusKeberlakuan
from src.llm.pembungkus import Pembungkus
from src.llm.sematan import Penyemat
from src.llm.tipe import Konfigurasi
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.indeks import (
    SegmenTerindeks,
    StatusLisensi,
    lisensi_dari_metadata,
)
from src.penyimpanan.korpus_penjawab import BarisKorpus, MuatanKorpus, PemuatKorpus
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN
from src.penyimpanan.sambungan import SambunganAktif
from src.rag.jawaban.domain import ranah_di_luar_domain
from src.rag.jawaban.tanggapan import BacaanLanjutan, Sitasi, Versi
from src.rag.pengambilan.bm25 import IndeksLeksikal, SumberBM25, bangun_indeks
from src.rag.pengambilan.kandidat import HasilSumber, SumberKandidat
from src.rag.pengambilan.kecukupan import AmbangKecukupan, PenilaianKecukupan
from src.rag.pengambilan.peringkat_ulang import Pemeringkat
from src.rag.pengambilan.teks_pencarian import ATURAN_PENCARIAN, teks_pencarian
from src.rag.pengambilan.tetapan import (
    JUMLAH_KANDIDAT_PER_SUMBER,
    JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM,
)
from src.rag.pengambilan.vektor import SumberVektor
from src.rag.validator.keluaran import SegmenRujukan

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA


class AlasanTakLayak(Enum):
    """Mengapa sebuah segmen tidak dimuat — urutan pemeriksaannya."""

    TANPA_METADATA = "tanpa_metadata"
    TIDAK_PUBLIK = "tidak_publik"
    LISENSI_TERTUTUP = "lisensi_tertutup"
    BELUM_TERVERIFIKASI = "belum_terverifikasi"
    REGULASI_TANPA_STATUS = "regulasi_tanpa_status"
    DICABUT = "dicabut"


@dataclass(frozen=True)
class _Terbaca:
    jenis: JenisSumber
    tingkat: TingkatKerahasiaan
    status: StatusKeberlakuan | None


def _terbaca(baris: BarisKorpus) -> _Terbaca | None:
    if baris.metadata is None:
        return None
    try:
        jenis = JenisSumber(baris.metadata.jenis)
        tingkat = TingkatKerahasiaan(baris.metadata.tingkat_kerahasiaan)
        status = None if baris.status is None else StatusKeberlakuan(baris.status)
    except ValueError:
        return None
    return _Terbaca(jenis, tingkat, status)


def alasan_tak_layak(baris: BarisKorpus, indeks: IndeksTujuan) -> AlasanTakLayak | None:
    """Alasan pertama yang berlaku, atau `None` bila layak — lihat uraian modul."""
    terbaca = _terbaca(baris)
    if terbaca is None or baris.metadata is None:
        return AlasanTakLayak.TANPA_METADATA
    if not teks_boleh_tayang(terbaca.jenis, terbaca.tingkat):
        return AlasanTakLayak.TIDAK_PUBLIK
    if (
        indeks is UTAMA
        and lisensi_dari_metadata(baris.metadata.lisensi) is not StatusLisensi.TERBUKA
    ):
        return AlasanTakLayak.LISENSI_TERTUTUP
    if not baris.anonimisasi_terverifikasi:
        return AlasanTakLayak.BELUM_TERVERIFIKASI
    if terbaca.jenis is JenisSumber.REGULASI_RESMI and terbaca.status is None:
        return AlasanTakLayak.REGULASI_TANPA_STATUS
    if terbaca.status is StatusKeberlakuan.DICABUT:
        return AlasanTakLayak.DICABUT
    return None


def _status_bahan(baris: BarisKorpus) -> StatusKeberlakuan:
    """Status bagi baris layak: bukan regulasi tanpa catatan bernilai berlaku."""
    terbaca = _terbaca(baris)
    if terbaca is None or terbaca.status is None:
        return StatusKeberlakuan.BERLAKU
    return terbaca.status


@dataclass(frozen=True)
class Muatan:
    """Potret beku kedua indeks pada satu pasang sidik."""

    sidik_utama: str
    sidik_metadata: str
    indeks_leksikal: Mapping[IndeksTujuan, IndeksLeksikal]
    bahan: Mapping[str, BahanSegmen]
    sitasi: Mapping[str, Sitasi]
    segmen_resmi: frozenset[str]
    """Peringkat T1 — "regulasi dan panduan resmi" D-13 Bagian 6, kriteria
    "rujukan kuat" D-07 Bagian 4.6."""
    layak_utama: frozenset[str]
    bacaan: Mapping[str, tuple[str, BacaanLanjutan]]
    """Segmen indeks metadata yang dokumennya bertautan → (dokumen, bacaan)."""
    tak_layak: Mapping[IndeksTujuan, Mapping[AlasanTakLayak, int]]
    perlu_indeks_ulang: frozenset[str]
    """Dokumen yang segmennya di indeks utama tetapi lisensinya kini tertutup."""

    @property
    def versi_indeks(self) -> str:
        return f"utama:{self.sidik_utama};metadata:{self.sidik_metadata};{ATURAN_PENCARIAN}"


def _segmen(baris: BarisKorpus, indeks: IndeksTujuan, *, judul: str) -> SegmenTerindeks:
    """Segmen bagi indeks leksikal saja: teksnya teks pencarian (fitur 041,
    TK-88). Bahan bagi model dibentuk terpisah dari `baris.teks`."""
    return SegmenTerindeks(
        id_segmen=baris.id_segmen,
        id_dokumen=baris.id_dokumen,
        teks=teks_pencarian(judul, baris.teks),
        lisensi=StatusLisensi(baris.lisensi_segmen),
        indeks_tujuan=indeks,
        anonimisasi_terverifikasi=baris.anonimisasi_terverifikasi,
        penanda_bagian=baris.penanda_bagian,
    )


def bangun_muatan(utama: MuatanKorpus, metadata: MuatanKorpus) -> Muatan:
    """Muatan dari dua potret pemuat — murni, tanpa basis data."""
    bahan: dict[str, BahanSegmen] = {}
    sitasi: dict[str, Sitasi] = {}
    resmi: set[str] = set()
    bacaan: dict[str, tuple[str, BacaanLanjutan]] = {}
    tak_layak: dict[IndeksTujuan, Counter[AlasanTakLayak]] = {UTAMA: Counter(), METADATA: Counter()}
    perlu_ulang: set[str] = set()
    layak: dict[IndeksTujuan, list[SegmenTerindeks]] = {UTAMA: [], METADATA: []}

    for indeks, muatan in ((UTAMA, utama), (METADATA, metadata)):
        for baris in muatan.baris:
            alasan = alasan_tak_layak(baris, indeks)
            if alasan is not None:
                tak_layak[indeks][alasan] += 1
                if alasan is AlasanTakLayak.LISENSI_TERTUTUP:
                    perlu_ulang.add(baris.id_dokumen)
                continue
            # Baris layak selalu bercatatan metadata — alasan pertama di atas.
            m = cast(MetadataDokumen, baris.metadata)
            layak[indeks].append(_segmen(baris, indeks, judul=m.judul))
            if indeks is METADATA:
                if m.tautan is not None:
                    bacaan[baris.id_segmen] = (
                        baris.id_dokumen,
                        BacaanLanjutan(judul=m.judul, tautan=m.tautan),
                    )
                continue
            status = _status_bahan(baris)
            peringkat = peringkat_bagi(JenisSumber(m.jenis))
            bahan[baris.id_segmen] = BahanSegmen(
                rujukan=SegmenRujukan(
                    id_segmen=baris.id_segmen,
                    peringkat_kepercayaan=peringkat,
                    indeks_asal=UTAMA,
                    status_keberlakuan=status,
                    tautan=m.tautan,
                ),
                teks=baris.teks,
            )
            sitasi[baris.id_segmen] = Sitasi(
                id_dokumen=baris.id_dokumen,
                judul=m.judul,
                penerbit=m.penerbit,
                tahun=m.tahun,
                bagian=baris.penanda_bagian,
                status_keberlakuan=status,
                rujukan_pengganti=baris.rujukan_pengganti,
                tautan=m.tautan,
            )
            if peringkat is Peringkat.T1:
                resmi.add(baris.id_segmen)

    return Muatan(
        sidik_utama=utama.sidik,
        sidik_metadata=metadata.sidik,
        indeks_leksikal=MappingProxyType(
            {
                indeks: bangun_indeks(
                    layak[indeks],
                    versi=f"{indeks.value}:{potret.sidik};{ATURAN_PENCARIAN}",
                    indeks_tujuan=indeks,
                )
                for indeks, potret in ((UTAMA, utama), (METADATA, metadata))
            }
        ),
        bahan=MappingProxyType(bahan),
        sitasi=MappingProxyType(sitasi),
        segmen_resmi=frozenset(resmi),
        layak_utama=frozenset(s.id_segmen for s in layak[UTAMA]),
        bacaan=MappingProxyType(bacaan),
        tak_layak=MappingProxyType(
            {indeks: MappingProxyType(dict(hitungan)) for indeks, hitungan in tak_layak.items()}
        ),
        perlu_indeks_ulang=frozenset(perlu_ulang),
    )


async def pilih_bacaan_lanjutan(pertanyaan: str, muatan: Muatan) -> tuple[BacaanLanjutan, ...]:
    """Dokumen indeks metadata bertautan, unik per dokumen, menurut peringkat
    pencarian leksikal atas pertanyaan yang sama; paling banyak sejumlah segmen
    yang diteruskan — tetapan D-07 Bagian 9 dipakai ulang, bukan angka baru
    (D-14 Bagian 4.1)."""
    hasil = await SumberBM25(muatan.indeks_leksikal[METADATA]).cari(
        pertanyaan, batas=JUMLAH_KANDIDAT_PER_SUMBER
    )
    terlihat: set[str] = set()
    bacaan: list[BacaanLanjutan] = []
    for kandidat in hasil.peringkat:
        satu = muatan.bacaan.get(kandidat.id_segmen)
        if satu is None or satu[0] in terlihat:
            continue
        terlihat.add(satu[0])
        bacaan.append(satu[1])
        if len(bacaan) == JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM:
            break
    return tuple(bacaan)


class SumberLayak(SumberKandidat):
    """Sumber yang kandidatnya dibatasi pada segmen layak.

    Bagi sisi vektor fitur 019, yang mencari langsung pada peladen tanpa
    mengetahui catatan korpus. Penyaringan ini kelayakan — keberlakuan dan
    kerahasiaan — **bukan** C-02: pemisahan lisensi tetap dijaga kredensial
    pada tingkat indeks.
    """

    def __init__(self, sumber: SumberKandidat, layak: frozenset[str]) -> None:
        self._sumber = sumber
        self._layak = layak

    @property
    def nama(self) -> str:
        return self._sumber.nama

    @property
    def indeks_tujuan(self) -> IndeksTujuan:
        return self._sumber.indeks_tujuan

    @property
    def versi_indeks(self) -> str:
        return self._sumber.versi_indeks

    async def cari(self, kueri: str, *, batas: int) -> HasilSumber:
        hasil = await self._sumber.cari(kueri, batas=batas)
        return HasilSumber(
            nama_sumber=hasil.nama_sumber,
            versi_indeks=hasil.versi_indeks,
            peringkat=tuple(k for k in hasil.peringkat if k.id_segmen in self._layak),
            versi_penyemat=hasil.versi_penyemat,
            segmen_tanpa_vektor=hasil.segmen_tanpa_vektor,
        )


@dataclass(frozen=True)
class _Siap:
    muatan: Muatan
    vektor: SumberLayak


class PenjawabKorpus:
    """Memenuhi `JalurPenjawab` rute `/tanya`. Seluruh kolaboratornya wajib."""

    def __init__(
        self,
        *,
        pemuat_konteks: PemuatKorpus,
        pemuat_metadata: PemuatKorpus,
        sambungan_vektor: SambunganAktif,
        penyemat: Penyemat,
        pemeringkat: Pemeringkat,
        ambang: AmbangKecukupan,
        pembungkus: Pembungkus,
        konfigurasi: Konfigurasi,
        versi_model: str,
        versi_kode: str,
    ) -> None:
        self._pemuat_konteks = pemuat_konteks
        self._pemuat_metadata = pemuat_metadata
        self._sambungan_vektor = sambungan_vektor
        self._penyemat = penyemat
        self._pemeringkat = pemeringkat
        self._penilai = PenilaianKecukupan(ambang)
        self._pembungkus = pembungkus
        self._konfigurasi = konfigurasi
        self._versi_model = versi_model
        self._versi_kode = versi_kode
        self._siap: _Siap | None = None

    async def _segarkan(self) -> _Siap:
        """Muatan yang sesuai sidik peladen sekarang — lihat uraian modul."""
        sidik = (
            await self._pemuat_konteks.sidik(PEMANGGIL_LLM, UTAMA),
            await self._pemuat_metadata.sidik(PENJAWABAN, METADATA),
        )
        siap = self._siap
        if siap is not None and sidik == (siap.muatan.sidik_utama, siap.muatan.sidik_metadata):
            return siap
        muatan = bangun_muatan(
            await self._pemuat_konteks.muat(PEMANGGIL_LLM, UTAMA),
            await self._pemuat_metadata.muat(PENJAWABAN, METADATA),
        )
        vektor = await SumberVektor.susun(
            sambungan=self._sambungan_vektor,
            penyemat=self._penyemat,
            indeks_tujuan=UTAMA,
            versi_indeks=f"utama:{muatan.sidik_utama}",
        )
        baru = _Siap(muatan=muatan, vektor=SumberLayak(vektor, muatan.layak_utama))
        self._siap = baru
        return baru

    async def jawab(self, pertanyaan: str, **_: Any) -> HasilTanya:
        siap = await self._segarkan()
        muatan = siap.muatan
        # Tahap 1 mendahului setiap pengambilan, termasuk pencarian bacaan
        # lanjutan; `Jalur` memeriksanya lagi dan berhenti sendiri.
        bacaan = (
            ()
            if ranah_di_luar_domain(pertanyaan)
            else await pilih_bacaan_lanjutan(pertanyaan, muatan)
        )
        jalur = Jalur(
            sumber=[SumberBM25(muatan.indeks_leksikal[UTAMA]), siap.vektor],
            pemeringkat=self._pemeringkat,
            penilai=self._penilai,
            pembungkus=self._pembungkus,
            konfigurasi=self._konfigurasi,
        )
        return await jalur.jawab(
            pertanyaan,
            kredensial=PEMANGGIL_LLM,
            bahan=muatan.bahan,
            segmen_resmi=muatan.segmen_resmi,
            id_pesan=f"msg_{uuid.uuid4().hex}",
            versi=Versi(model=self._versi_model, indeks=muatan.versi_indeks, kode=self._versi_kode),
            sitasi=muatan.sitasi,
            bacaan_lanjutan=bacaan,
        )
