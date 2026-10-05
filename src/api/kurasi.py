"""Kurasi — T-5 fitur 013, R-04, R-09, R-10; K-4, K-5, K-6; D-14 Bagian 4.7.

Penerjemah antara tiga rute kurator dan penyimpan kurasi. Aturan isinya
**tidak ditulis di sini**: ia milik fitur 010 — `Putusan`, `terapkan()`,
`ButirTayang`, `JejakKurasi`, `tinjau()` — yang dipakai lewat tepi
`api → ingest`. Menulis ulang C-06 atau lapis kedua C-07 di sini akan
menghasilkan dua tempat yang berselisih.

## Status regulasi terkini (K-4)

Butir dibentuk dari JSON kandidat **dengan status salinan terkini** yang
diperbarui perkakas, bukan status saat butir masuk antrean. Tanpa itu lapis
kedua C-07 pada `terapkan()` memeriksa nilai yang sudah usang — tepat keadaan
yang uraian `putusan.py` sebut.

## Jejak: peran dan pseudonim (K-5)

`JejakKurasi` fitur 010 dipakai sebagai **pemeriksa** alasan sebelum apa pun
ditulis: kode TL saja bagi penolakan, catatan wajib bagi selebihnya, tanpa data
pribadi. Baris yang tersimpan membawa peran **dan** pseudonim kurator dari
sesi — tidak pernah nama akun.

## Penarikan atas `ButirTayang` sungguhan

`tinjau()` menuntut `ButirTayang`. Ia dibentuk ulang dari baris tersimpan
beserta **putusan yang menayangkannya**, dibaca dari basis data — bukan putusan
karangan. Pembentukan itu menjalankan ulang penjaga C-06 dan C-07 pada bentuknya.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from src.api.hari import iso_utc, tanggal_wib
from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.ingest.kurasi.jejak import GalatJejakKurasi, JejakKurasi
from src.ingest.kurasi.penarikan import GalatPenarikan, Pemicu, tinjau
from src.ingest.kurasi.putusan import (
    AlasanTolak,
    ButirTayang,
    GalatPutusan,
    JenisPutusan,
    PeranKurasi,
    Putusan,
    terapkan,
)
from src.ingest.kurasi.sumber import SumberButir
from src.kamus.segmen import StatusKeberlakuan
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.nlp.anotasi.skema import KategoriMasalah
from src.penyimpanan.kurasi import (
    BarisKandidat,
    BarisTayang,
    CatatanPutusan,
    PenyimpanKurasi,
)

PESAN_PUTUSAN_TIDAK_SAH: Final = "Putusan belum lengkap. Periksa isian, lalu kirim lagi."
PESAN_REGULASI_TIDAK_BERLAKU: Final = (
    "Regulasi sumber butir ini tidak lagi berlaku. Pilih Tolak dengan alasan regulasi dicabut."
)
PESAN_TARIK_TIDAK_SAH: Final = (
    "Penarikan belum lengkap. Periksa pemicu dan catatan, lalu kirim lagi."
)
PESAN_BUTIR_TIDAK_ADA: Final = "Butir yang Anda cari tidak ditemukan."
"""C-13: ≤ 20 kata, tanpa istilah teknis, **tanpa mengutip masukan**."""

_PERAN: Final = PeranKurasi.KURATOR
"""Peran akun `kurator` D-14 memutus sebagai `PeranKurasi.KURATOR`. Kurator
pengganti D-06 Bagian 7.1 belum memiliki peran akun tersendiri."""


class ButirTidakAda(Exception):
    """Id tidak menunggu putusan, atau tidak sedang tayang — satu bentuk 404."""


class RegulasiTidakBerlaku(ValueError):
    """Lapis kedua C-07 menolak persetujuan — anjurannya TL-04."""


class _Ketat(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)


class Suntingan(_Ketat):
    """Empat bidang parafrase D-06 Bagian 7.3 — **tidak lebih**."""

    judul: str
    alasan_relevansi: str
    inti_temuan: str
    implikasi_tindakan: list[str]


class _Setujui(_Ketat):
    jenis: Literal["setujui"]
    catatan: str


class _Sunting(_Ketat):
    jenis: Literal["sunting_lalu_setujui"]
    catatan: str
    suntingan: Suntingan


class _Tolak(_Ketat):
    jenis: Literal["tolak"]
    alasan_tolak: AlasanTolak


class _Tunda(_Ketat):
    jenis: Literal["tunda"]
    catatan: str
    kembali_pada: date


PermintaanPutusan = Annotated[_Setujui | _Sunting | _Tolak | _Tunda, Field(discriminator="jenis")]
_PUTUSAN: Final[TypeAdapter[PermintaanPutusan]] = TypeAdapter(PermintaanPutusan)


class PermintaanTarik(_Ketat):
    pemicu: Pemicu
    catatan: str
    status_terkini: StatusKeberlakuan | None = None
    angka_berubah_bermakna: bool = False


# ── tanggapan ────────────────────────────────────────────────────────


class _Tanggapan(BaseModel):
    """Bentuk tanggapan — model bernama agar pemeriksa kontrak V-03 dapat
    membandingkannya dengan `web/src/kontrak.ts` (C-20)."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class KandidatTampil(_Tanggapan):
    id_butir: str
    kategori: KategoriMasalah
    jenis_sumber: JenisSumberButir
    judul: str
    alasan_relevansi: str
    inti_temuan: str
    implikasi_tindakan: list[str]
    perkiraan_waktu_baca: int
    tenggat_terkait: date | None
    lisensi: str
    status_keberlakuan: StatusKeberlakuan | None
    sumber: SumberButir
    masuk_pada: str


class TayangTampil(_Tanggapan):
    id_butir: str
    kategori: KategoriMasalah
    jenis_sumber: JenisSumberButir
    judul: str
    lisensi: str
    status_keberlakuan: StatusKeberlakuan | None
    tayang_pada: str
    perlu_tinjauan: bool


class Antrean(_Tanggapan):
    menunggu: list[KandidatTampil]
    tayang: list[TayangTampil]


def _kandidat(k: BarisKandidat) -> KandidatTampil:
    b = ButirPengetahuan.model_validate(k.butir)
    return KandidatTampil(
        id_butir=k.id_butir,
        kategori=b.kategori,
        jenis_sumber=b.jenis_sumber,
        judul=b.judul,
        alasan_relevansi=b.alasan_relevansi,
        inti_temuan=b.inti_temuan,
        implikasi_tindakan=list(b.implikasi_tindakan),
        perkiraan_waktu_baca=b.perkiraan_waktu_baca,
        tenggat_terkait=b.tenggat_terkait,
        lisensi=b.lisensi,
        status_keberlakuan=None
        if k.status_keberlakuan is None
        else StatusKeberlakuan(k.status_keberlakuan),
        sumber=SumberButir.model_validate(k.sumber),
        masuk_pada=iso_utc(k.masuk_pada),
    )


def _tayang(t: BarisTayang) -> TayangTampil:
    b = ButirPengetahuan.model_validate(t.butir)
    return TayangTampil(
        id_butir=t.id_butir,
        kategori=b.kategori,
        jenis_sumber=b.jenis_sumber,
        judul=b.judul,
        lisensi=b.lisensi,
        status_keberlakuan=None
        if t.status_keberlakuan is None
        else StatusKeberlakuan(t.status_keberlakuan),
        tayang_pada=iso_utc(t.tayang_pada),
        perlu_tinjauan=t.perlu_tinjauan_pada is not None,
    )


async def antrean(simpan: PenyimpanKurasi, *, sekarang: datetime) -> dict[str, Any]:
    """Bentuk tanggapan bersama ketiga rute — D-14 Bagian 4.7."""
    menunggu = await simpan.menunggu(hari_ini=tanggal_wib(sekarang))
    return Antrean(
        menunggu=[_kandidat(k) for k in menunggu],
        tayang=[_tayang(t) for t in await simpan.tayang_aktif()],
    ).model_dump(mode="json")


# ── putusan ──────────────────────────────────────────────────────────


def _alasan_jejak(putusan: Putusan, catatan: str) -> str:
    """Aturan alasan FR-I05 milik `JejakKurasi`, dijalankan sebelum menulis."""
    jejak = JejakKurasi()
    try:
        jejak.catat(putusan, catatan=catatan)
    except GalatJejakKurasi as galat:
        raise ValueError("alasan putusan tidak sah") from galat
    return jejak.baris[-1].alasan


def _putusan(badan: Any, butir: ButirPengetahuan, waktu: datetime) -> tuple[Putusan, str]:
    """Badan permintaan menjadi `Putusan` fitur 010 beserta catatannya."""
    permintaan = _PUTUSAN.validate_python(badan)
    lebih: dict[str, Any] = {}
    catatan = ""
    if isinstance(permintaan, _Tolak):
        lebih["alasan_tolak"] = permintaan.alasan_tolak
    else:
        catatan = permintaan.catatan
    if isinstance(permintaan, _Tunda):
        lebih["kembali_pada"] = permintaan.kembali_pada
    if isinstance(permintaan, _Sunting):
        lebih["butir_suntingan"] = ButirPengetahuan.model_validate(
            {**butir.model_dump(), **permintaan.suntingan.model_dump()}
        )
    putusan = Putusan(
        jenis=JenisPutusan(permintaan.jenis),
        id_butir=butir.id_butir,
        peran_pemutus=_PERAN,
        waktu=waktu,
        **lebih,
    )
    return putusan, catatan


async def putuskan(
    simpan: PenyimpanKurasi,
    id_butir: str,
    badan: Any,
    *,
    pseudonim: str,
    sekarang: datetime,
) -> None:
    """Catat satu putusan. `ButirTidakAda` bila tidak menunggu; `RegulasiTidakBerlaku`
    bila lapis C-07 menolak; `ValueError` bagi badan yang tidak sah."""
    kandidat = await simpan.satu_menunggu(id_butir, hari_ini=tanggal_wib(sekarang))
    if kandidat is None:
        raise ButirTidakAda(id_butir)
    # K-4: status terkini, bukan salinan saat masuk antrean.
    butir = ButirPengetahuan.model_validate(
        {**kandidat.butir, "status_keberlakuan": kandidat.status_keberlakuan}
    )
    try:
        putusan, catatan = _putusan(badan, butir, sekarang)
    except ValidationError as galat:
        raise ValueError("putusan tidak sah") from galat
    try:
        _, tayang = terapkan(butir, putusan)
    except GalatPutusan as galat:
        raise RegulasiTidakBerlaku("regulasi sumber tidak berlaku") from galat
    catat = CatatanPutusan(
        id_butir=id_butir,
        jenis=putusan.jenis.value,
        peran=putusan.peran_pemutus.value,
        pseudonim_kurator=pseudonim,
        alasan=_alasan_jejak(putusan, catatan),
        waktu=sekarang,
    )
    if tayang is not None:
        tercatat = await simpan.setujui(catat, butir=tayang.butir.model_dump(mode="json"))
    elif putusan.kembali_pada is not None:
        tercatat = await simpan.tunda(catat, putusan.kembali_pada)
    else:
        tercatat = await simpan.tolak(catat)
    if not tercatat:
        # Kurator lain memutus di antara pembacaan dan penulisan.
        raise ButirTidakAda(id_butir)


# ── penarikan ────────────────────────────────────────────────────────


def bentuk_ulang(t: BarisTayang, *, status_terkini: bool = False) -> ButirTayang:
    """`ButirTayang` lewat gerbangnya sendiri — `terapkan()` atas putusan tersimpan.

    Konstruktornya tidak dipanggil di sini: pemeriksa C-06 membatasi pembentukan
    `ButirTayang` pada modul putusan, dan `terapkan()` adalah satu-satunya jalan
    sah ke sana. Yang diterapkan putusan **yang sungguh tercatat** — jenis,
    peran, dan waktunya dibaca dari basis data — sehingga penjaga C-06 dan C-07
    berjalan ulang.

    `status_terkini` memakai salinan status yang diperbarui perkakas (K-4);
    regulasi yang tidak lagi berlaku kemudian melempar `GalatPutusan`. Feed
    memakainya; penarikan tidak, sebab butir yang hendak ditarik justru yang
    regulasinya baru dicabut.
    """
    jenis = None if t.putusan is None else JenisPutusan(t.putusan.jenis)
    if t.putusan is None or jenis not in _JENIS_MENYETUJUI:
        raise RuntimeError("baris tayang tanpa putusan yang menyetujui — penyimpan rusak")
    isi = {**t.butir, "status_keberlakuan": t.status_keberlakuan} if status_terkini else t.butir
    butir = ButirPengetahuan.model_validate(isi)
    putusan = Putusan(
        jenis=jenis,
        id_butir=t.id_butir,
        peran_pemutus=PeranKurasi(t.putusan.peran),
        waktu=t.putusan.waktu,
        butir_suntingan=butir if jenis is JenisPutusan.SUNTING_LALU_SETUJUI else None,
    )
    return _wajib(terapkan(butir, putusan)[1])


_JENIS_MENYETUJUI: Final = frozenset({JenisPutusan.SETUJUI, JenisPutusan.SUNTING_LALU_SETUJUI})


def _wajib(tayang: ButirTayang | None) -> ButirTayang:
    """Persetujuan yang diterapkan selalu menghasilkan butir tayang; ketiadaannya
    berarti `terapkan()` berubah arti, dan itu dihentikan terang."""
    if tayang is None:
        raise RuntimeError("persetujuan tidak menghasilkan butir tayang")
    return tayang


async def tarik(
    simpan: PenyimpanKurasi,
    id_butir: str,
    badan: Any,
    *,
    pseudonim: str,
    sekarang: datetime,
) -> None:
    """Tinjau dan tarik satu butir tayang — `tinjau()` fitur 010 yang memutus."""
    try:
        permintaan = PermintaanTarik.model_validate(badan)
    except ValidationError as galat:
        raise ValueError("penarikan tidak sah") from galat
    baris = {t.id_butir: t for t in await simpan.tayang_aktif()}.get(id_butir)
    if baris is None:
        raise ButirTidakAda(id_butir)
    if permintaan.status_terkini is not None and (
        permintaan.pemicu is not Pemicu.REGULASI_SUMBER_BERUBAH
    ):
        raise ValueError("status terkini hanya milik pemicu regulasi")
    try:
        hasil = tinjau(
            bentuk_ulang(baris),
            pemicu=permintaan.pemicu,
            status_terkini=permintaan.status_terkini,
            angka_berubah_bermakna=permintaan.angka_berubah_bermakna,
        )
    except GalatPenarikan as galat:
        raise ValueError("penarikan tidak dapat dijalankan") from galat
    catatan = permintaan.catatan.strip()
    if not catatan or periksa_data_pribadi(catatan):
        raise ValueError("catatan penarikan tidak sah")
    if not await simpan.tarik(
        id_butir,
        pemicu=hasil.pemicu.value,
        tindakan=hasil.tindakan.value,
        peran=_PERAN.value,
        pseudonim_kurator=pseudonim,
        alasan=catatan,
        sekarang=sekarang,
    ):
        raise ButirTidakAda(id_butir)
