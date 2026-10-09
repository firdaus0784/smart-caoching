"""Lapisan HTTP — fitur 023, R-01 s.d. R-07.

`plan.md` fitur 021 menetapkan bentuk modul ini sebelum kerangkanya ada, dan
kalimatnya masih berlaku kata demi kata:

> Adaptornya memanggil ketiganya dan **tidak memuat satu pun keputusan**.
> Keputusan yang tinggal di dalam penangan HTTP hanya dapat diuji lewat HTTP,
> dan uji yang menuntut peladen berjalan adalah uji yang dilewati orang ketika
> sedang buru-buru.

Akibatnya tegas: setiap penangan di bawah **hanya menerjemahkan**. Yang tampak
perlu diputuskan di dalam penangan adalah tanda bahwa ia kurang pada lapisan di
bawahnya, dan diperbaiki di sana.

## Tiga rute bawaan dimatikan, dan itu bukan kerapian

`docs_url`, `redoc_url`, dan `openapi_url` menyala secara **baku** pada
FastAPI. AG-02 melarang rute yang tidak ada pada `docs/D14.md` Bagian 3, dan
rute yang menyala tanpa seorang pun mendaftarkannya adalah bentuk pelanggaran
yang paling mungkin luput — tidak ada baris kode yang dapat dibaca sebagai
penyebabnya. Ketiganya dimatikan tegas dan diuji.

## Pola jalur diambil dari peta rute, tidak ditulis ulang

`boleh()` menuntut **pola** D-14, bukan jalur permintaan. Polanya diimpor dari
`src/api/peran.py`, yang mengambilnya lewat pencarian pada peta rutenya
sendiri; tidak ada satu untai jalur pun tertulis pada berkas ini.

Percobaan pertama menuliskannya sebagai tetapan di sini, dan
`periksa_rute_terdaftar` menolaknya pada V-03. Pemeriksa itu dibangun fitur 021
**dengan meramalkan adaptor ini**, dan uraiannya menyebutkan bentuk
kekeliruannya kata demi kata: untai yang tidak pernah masuk `PETA_RUTE` lolos
kedua arah uji peta rute, sementara peladen melayani rute yang kendali perannya
tidak pernah dipanggil. Ia menangkapnya pada percobaan pertama, sebagaimana
dirancang.

## Identitas tidak berbawaan

`susun_aplikasi` menuntut `identitas` tanpa nilai baku, sehingga aplikasi tanpa
penentu identitas **tidak dapat disusun** — bukan disusun lalu ditolak saat
jalan. Nilai baku pada bidang yang menentukan siapa pemanggil adalah nilai baku yang
akan terpakai di lingkungan sungguhan.

Sejak fitur 029 penentu sungguhan adalah `PenentuSesi` (`src/api/autentikasi.py`):
tanpa sesi sah, setiap rute menjawab 401 sebelum membaca badan permintaan.
Penentu tiruan tanpa pemeriksaan tetap hanya terjangkau titik jalan
pengembangan di luar `src/` (R-10).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.api.analitik import PESAN_EKSPOR_TIDAK_SAH, ekspor
from src.api.analitik import ringkasan as ringkasan_analitik
from src.api.autentikasi import (
    MASA_SESI,
    NAMA_KUKI,
    PESAN_BELUM_MASUK,
    PESAN_MASUK_DITOLAK,
    PESAN_MASUK_TIDAK_LENGKAP,
    PenjagaMasuk,
)
from src.api.galat import tanggapan_galat
from src.api.identitas import Identitas, PenentuIdentitas
from src.api.kurasi import (
    PESAN_BUTIR_TIDAK_ADA,
    PESAN_PUTUSAN_TIDAK_SAH,
    PESAN_REGULASI_TIDAK_BERLAKU,
    PESAN_TARIK_TIDAK_SAH,
    ButirTidakAda,
    RegulasiTidakBerlaku,
    antrean,
    putuskan,
    tarik,
)
from src.api.penemuan import (
    PESAN_ALASAN_TIDAK_SAH,
    ButirTidakTampil,
    bukan_butir_dibuka,
    detail,
    susun_beranda,
    tolak,
)
from src.api.penilaian import (
    PESAN_ADUAN_TIDAK_ADA,
    PESAN_JAWABAN_TIDAK_ADA,
    PESAN_PENILAIAN_TIDAK_SAH,
    PESAN_TINDAK_LANJUT_TIDAK_SAH,
    AduanTidakAda,
    daftar_aduan,
    nilai,
    tindak_lanjuti,
)
from src.api.peran import (
    POLA_ADUAN,
    POLA_ANALITIK_EKSPOR,
    POLA_ANALITIK_RINGKAS,
    POLA_ANTREAN,
    POLA_BERANDA,
    POLA_BUTIR,
    POLA_DAFTAR_PERCAKAPAN,
    POLA_DATA_SAYA,
    POLA_KELUAR,
    POLA_MASUK,
    POLA_PENILAIAN,
    POLA_PERSETUJUAN,
    POLA_PRIORITAS,
    POLA_PROFIL,
    POLA_PUTUSAN,
    POLA_SATU_PERCAKAPAN,
    POLA_SUMBER,
    POLA_TANYA,
    POLA_TARIK,
    POLA_TINDAK_LANJUT,
    POLA_TOLAK_BUTIR,
    boleh,
)
from src.api.percakapan import Giliran, giliran_sah
from src.api.rekaman import Perekam
from src.api.saya import (
    PESAN_PENARIKAN_TIDAK_SAH,
    PESAN_PERSETUJUAN_TIDAK_SAH,
    PESAN_PRIORITAS_TIDAK_SAH,
    PESAN_PROFIL_TIDAK_SAH,
    penarikan_sah,
    prioritas_sah,
    profil_sah,
    putuskan_persetujuan,
    ringkasan,
)
from src.api.sumber import (
    PESAN_BAGIAN_TIDAK_SAH,
    PESAN_SUMBER_TIDAK_ADA,
    SumberTidakTampil,
    baca_sumber,
)
from src.api.tanya import HasilTanya
from src.llm.galat import GalatLayananModel, KodeGalat
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.analitik import PenyimpanAnalitik
from src.penyimpanan.kurasi import PenyimpanKurasi
from src.penyimpanan.penemuan import PenyimpanPenemuan
from src.penyimpanan.pengguna import PenyimpanPengguna
from src.penyimpanan.penilaian import PenyimpanAduan, PenyimpanPenilaian, PesanTidakAda
from src.penyimpanan.riwayat import PenyimpanRiwayat, PercakapanTidakAda
from src.penyimpanan.sumber import PembacaSumber
from src.penyimpanan.telemetri import PenyimpanTelemetri

PESAN_TIDAK_BERHAK = "Akun Anda tidak dapat membuka bagian ini."
PESAN_TIDAK_LENGKAP = "Pertanyaan belum lengkap. Tulis ulang dengan kalimat utuh."
PESAN_TIDAK_ADA = "Percakapan yang Anda cari tidak ditemukan."
PESAN_GANGGUAN = "Ada gangguan di sistem kami. Coba lagi sebentar lagi."
PESAN_DATA_PRIBADI = "Pertanyaan memuat nomor pribadi. Hapus nomor itu, lalu kirim ulang."
"""Pesan tetap — C-13 dan R-06: ≤ 20 kata, tanpa istilah teknis, tanpa kode.

Ketiganya tidak memuat kembali nilai yang ditolak. Pesan yang mengutip
masukan akan mengutip pula masukan yang ditolak **karena** memuat data
pribadi, lewat jalur yang bukan pesan kita sendiri — KB-049.
"""

RUTE_TANYA = POLA_TANYA
RUTE_DAFTAR_PERCAKAPAN = POLA_DAFTAR_PERCAKAPAN
RUTE_SATU_PERCAKAPAN = POLA_SATU_PERCAKAPAN
"""Diambil dari `src/api/peran.py`, tidak ditulis ulang — lihat uraian modul."""


@runtime_checkable
class JalurPenjawab(Protocol):
    """Bentuk `Jalur.jawab()` sebagaimana dipakai adaptor ini."""

    async def jawab(self, pertanyaan: str, **argumen: Any) -> HasilTanya: ...


class PermintaanTanya(BaseModel):
    """Badan permintaan `POST /api/v1/tanya`.

    `extra="forbid"` menolak bidang tambahan — termasuk bidang bernama `peran`
    yang, bila diterima, akan membuat pemanggil menentukan penjaganya sendiri.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # Pertanyaan berdata pribadi ditolak pada modul ini (R-15). Tanpa
        # setelan ini pesan `ValidationError` menyalin masukannya — KB-049.
        hide_input_in_errors=True,
    )

    pertanyaan: str = Field(min_length=1)
    id_percakapan: uuid.UUID
    """Dibangkitkan klien — D-14 Bagian 4.1, P-2 fitur 028. Peladen tidak dapat
    mengembalikan pengenal yang ia buat tanpa menambah bidang tanggapan (C-20)."""

    @field_validator("id_percakapan")
    @classmethod
    def _uuid_versi_4(cls, nilai: uuid.UUID) -> uuid.UUID:
        """R-16: pengenal yang mudah ditebak — `1`, UUID berbasis waktu — ditolak.
        Keacakan UUID versi 4 yang menanggung batas R-02."""
        if nilai.version != 4 or nilai.variant != uuid.RFC_4122:
            raise ValueError("id_percakapan wajib UUID versi 4")
        return nilai


class PermintaanMasuk(BaseModel):
    """Badan `POST /api/v1/auth/masuk` — D-14 Bagian 4.4.

    Tepat dua bidang. `sandi` dibatasi 128 karakter **di sini**, sebelum
    penjaga menjalankan turunan apa pun; nilainya tidak pernah disalin ke
    pesan galat.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    nama_pengguna: str = Field(min_length=1, max_length=64)
    sandi: str = Field(min_length=1, max_length=128)


def _berbadan_json(permintaan: Request) -> bool:
    """K-4: rute pengubah keadaan hanya menerima `application/json`.

    Formulir lintas situs tidak dapat mengirim jenis ini tanpa *preflight*,
    dan peladen ini tidak menjawab *preflight* — sehingga syarat ini menutup
    celah yang ditinggal `SameSite`, yang OWASP sebut pertahanan berlapis,
    bukan pengganti.
    """
    jenis = permintaan.headers.get("content-type", "")
    return jenis.split(";", 1)[0].strip().lower() == "application/json"


def susun_aplikasi(
    *,
    jalur: JalurPenjawab,
    identitas: PenentuIdentitas,
    riwayat: PenyimpanRiwayat,
    masuk: PenjagaMasuk | None = None,
    pengguna: PenyimpanPengguna | None = None,
    versi_naskah: str | None = None,
    kurasi: PenyimpanKurasi | None = None,
    penemuan: PenyimpanPenemuan | None = None,
    telemetri: PenyimpanTelemetri | None = None,
    versi_aplikasi: str | None = None,
    analitik: PenyimpanAnalitik | None = None,
    penilaian: PenyimpanPenilaian | None = None,
    aduan: PenyimpanAduan | None = None,
    sumber: PembacaSumber | None = None,
    sekarang: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> FastAPI:
    """Susun peladen — R-04, R-07; riwayat berpemilik sejak fitur 028.

    `identitas` **tanpa nilai baku**, disengaja; lihat uraian modul.
    `riwayat` juga tanpa nilai baku: penyimpan yang diam-diam jatuh ke memori
    adalah riwayat yang hilang saat peladen dimulai ulang tanpa ada yang tahu.

    `masuk` boleh kosong: tanpa penjaga, rute masuk dan keluar **tidak
    terpasang** — titik jalan pengembangan yang memakai penentu tiruan tidak
    menyediakan rute masuk yang tidak dapat berbuat apa pun. Ketiadaannya
    bukan celah: tanpa rute masuk, tidak ada sesi yang dapat diterbitkan.

    `pengguna` sama: tanpa penyimpan, rute `/saya/*` tidak terpasang (fitur
    030). `versi_naskah` adalah versi berkas naskah ET-02 yang terpasang;
    `None` berarti naskah belum ada, dan setiap persetujuan ditolak (C-04).

    `kurasi` sama: tanpa penyimpan, rute kurator D-14 Bagian 3.4 tidak
    terpasang (fitur 013). `penemuan` juga, dan ia **menuntut** `pengguna`:
    beranda disaring terhadap prioritas yang tinggal di sana (FR-G01). Tanpa
    penyimpan pengguna aplikasi tidak dapat disusun, bukan disusun lalu
    menayangkan feed acak.

    `telemetri` boleh kosong: tanpa penyimpan, rute berjalan seperti sebelum
    fitur 034 dan tidak satu peristiwa pun tersimpan. Bila diberikan, ia
    **menuntut** `pengguna` — persetujuan yang dibaca C-04 tinggal di sana —
    dan `versi_aplikasi` yang terisi (FR-J02, K-4).

    `analitik` sama: tanpa penyimpan, rute peneliti D-14 Bagian 3.4 tidak
    terpasang (fitur 035).

    `penilaian` dan `aduan` sama (fitur 036): tanpa penyimpan penilaian rute
    penilaian pengguna tidak terpasang; tanpa penyimpan aduan kedua rute aduan
    kurator tidak terpasang. Keduanya terpisah karena perannya terpisah —
    penilai menulis salinan, kurator membacanya (R-06).

    `sumber` sama (fitur 032): tanpa pembaca, `GET /sumber/{id}` tidak
    terpasang. Pembaca tidak menerima jalur penjawab maupun penyimpan tulis
    apa pun (R-05, C-17).
    """
    if penemuan is not None and pengguna is None:
        raise ValueError("rute penemuan menuntut penyimpan pengguna (FR-G01)")
    perekam: Perekam | None = None
    if telemetri is not None:
        if pengguna is None:
            raise ValueError("telemetri menuntut penyimpan persetujuan pengguna (C-04)")
        perekam = Perekam(pengguna, telemetri, versi_aplikasi=versi_aplikasi or "")
    aplikasi = FastAPI(
        title="Smart-Coaching Adaptif",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # TK-66, R-14: galat yang lolos penangan tetap berbentuk D-14 Bagian 4.2.
    # Tanpanya FastAPI menjawab teks polos "Internal Server Error" — bentuk
    # yang layar harus tebak, dan bentuk yang D-05 Bagian 10 larang.
    @aplikasi.exception_handler(GalatLayananModel)
    async def _layanan_model_gagal(permintaan: Request, galat: Exception) -> JSONResponse:
        jejak = galat.id_jejak if isinstance(galat, GalatLayananModel) else None
        return tanggapan_galat(
            503,
            KodeGalat.LAYANAN_MODEL_GAGAL,
            GalatLayananModel.PESAN_PENGGUNA,
            rute=permintaan.url.path,
            sebab=galat,
            id_jejak=jejak,
        )

    @aplikasi.exception_handler(Exception)
    async def _galat_internal(permintaan: Request, galat: Exception) -> JSONResponse:
        return tanggapan_galat(
            500, KodeGalat.GALAT_INTERNAL, PESAN_GANGGUAN, rute=permintaan.url.path, sebab=galat
        )

    async def _identitas_atau_tolak(permintaan: Request, pola: str) -> Identitas | JSONResponse:
        """R-01 — dipanggil **sebelum** apa pun yang lain pada tiap penangan.

        Identitas dibaca sekali: peran dan pemilik dari satu keadaan yang sama.
        Tanpa sesi sah: 401, sebelum badan permintaan dibaca (R-05 fitur 029).
        Peran tidak mencukupi: 403.
        """
        siapa = await identitas.identitas(permintaan)
        if siapa is None:
            return tanggapan_galat(
                401, KodeGalat.TIDAK_TERAUTENTIKASI, PESAN_BELUM_MASUK, rute=pola
            )
        if not boleh(siapa.peran, permintaan.method, pola):
            return tanggapan_galat(403, KodeGalat.TIDAK_BERWENANG, PESAN_TIDAK_BERHAK, rute=pola)
        return siapa

    def _tidak_ada(pola: str) -> JSONResponse:
        """R-02, R-03: satu bentuk bagi "tidak dikenal" dan "milik orang lain"."""
        return tanggapan_galat(404, KodeGalat.SUMBER_TIDAK_ADA, PESAN_TIDAK_ADA, rute=pola)

    @aplikasi.post(RUTE_TANYA)
    async def tanya(permintaan: Request) -> JSONResponse:
        siapa = await _identitas_atau_tolak(permintaan, RUTE_TANYA)
        if isinstance(siapa, JSONResponse):
            return siapa
        if not _berbadan_json(permintaan):
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_TIDAK_LENGKAP, rute=RUTE_TANYA
            )
        try:
            badan = PermintaanTanya.model_validate(await permintaan.json())
        except (ValidationError, ValueError):
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_TIDAK_LENGKAP, rute=RUTE_TANYA
            )
        if not badan.pertanyaan.strip():
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_TIDAK_LENGKAP, rute=RUTE_TANYA
            )
        # R-15, TK-68: sebelum jalur penjawab — pertanyaan berdata pribadi
        # tidak sampai ke model, riwayat, maupun log. Pesannya tidak mengutip.
        if periksa_data_pribadi(badan.pertanyaan):
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_DATA_PRIBADI, rute=RUTE_TANYA
            )
        # R-02: pemilik diperiksa sebelum jawaban disusun, agar model tidak
        # dipanggil bagi percakapan milik orang lain.
        if not await riwayat.dapat_ditulis(
            pemilik=siapa.pemilik, id_percakapan=badan.id_percakapan
        ):
            return _tidak_ada(RUTE_TANYA)

        if perekam is not None:
            await perekam.rekam_pertanyaan(siapa.pemilik, badan.pertanyaan, sekarang=sekarang())

        # R-07, C-14: jalur menerima pertanyaan saja — tanpa giliran sebelumnya.
        mulai = time.perf_counter()
        hasil = await jalur.jawab(badan.pertanyaan)
        waktu_tanggap_ms = int((time.perf_counter() - mulai) * 1000)

        # R-01, TK-65: giliran dicatat sesudah tanggapan tersusun, oleh lapisan
        # ini — jalur penjawaban tidak memegang hak tulis (R-05, C-17).
        giliran = giliran_sah(
            pertanyaan=badan.pertanyaan, id_pesan=hasil.tanggapan.id_pesan, waktu=sekarang()
        )
        try:
            await riwayat.catat(
                pemilik=siapa.pemilik,
                id_percakapan=badan.id_percakapan,
                pertanyaan=giliran.pertanyaan,
                id_pesan=giliran.id_pesan,
                waktu=giliran.waktu,
                # Fitur 036, P-1 A: catatan audit, tidak pernah ditayangkan ulang.
                tanggapan=hasil.tanggapan.model_dump(mode="json"),
            )
        except PercakapanTidakAda:
            # Pemilik lain membuka percakapan yang sama di antara pemeriksaan
            # dan pencatatan. Jawabannya tidak dikirim: ia tidak tercatat.
            return _tidak_ada(RUTE_TANYA)
        if perekam is not None:
            await perekam.rekam_jawaban(
                siapa.pemilik, hasil, waktu_tanggap_ms=waktu_tanggap_ms, sekarang=sekarang()
            )
        # R-03 fitur 023: tertahan atau tidak, bentuk dan statusnya sama. D-14
        # menetapkan `tidak_ditemukan` memakai bentuk jawaban yang sah, dan
        # status galat akan membuat layar menampilkannya sebagai kegagalan
        # sistem — D-02 titik kritis T3 menuntut sebaliknya.
        return JSONResponse(status_code=200, content=hasil.tanggapan.model_dump(mode="json"))

    @aplikasi.get(RUTE_DAFTAR_PERCAKAPAN)
    async def daftar_percakapan(permintaan: Request) -> JSONResponse:
        siapa = await _identitas_atau_tolak(permintaan, RUTE_DAFTAR_PERCAKAPAN)
        if isinstance(siapa, JSONResponse):
            return siapa
        # TK-67: milik penanya saja, terbaru lebih dulu (D-14 Bagian 4.3).
        milik = await riwayat.daftar(pemilik=siapa.pemilik)
        return JSONResponse(status_code=200, content={"percakapan": [str(i) for i in milik]})

    @aplikasi.get(RUTE_SATU_PERCAKAPAN)
    async def satu_percakapan(permintaan: Request, id: str) -> JSONResponse:
        siapa = await _identitas_atau_tolak(permintaan, RUTE_SATU_PERCAKAPAN)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            id_percakapan = uuid.UUID(id)
            baris = await riwayat.baca(pemilik=siapa.pemilik, id_percakapan=id_percakapan)
        except (ValueError, PercakapanTidakAda):
            # Bukan UUID, tidak dikenal, dan milik orang lain: satu bentuk.
            return _tidak_ada(RUTE_SATU_PERCAKAPAN)
        # R-05 fitur 023: `Giliran` tidak memiliki bidang tanggapan, dan bentuk
        # itu yang menjaga C-07 — tanggapan yang tersimpan menua.
        return JSONResponse(
            status_code=200,
            content={
                "id_percakapan": str(id_percakapan),
                "giliran": [
                    Giliran(pertanyaan=b.pertanyaan, id_pesan=b.id_pesan, waktu=b.waktu).model_dump(
                        mode="json"
                    )
                    for b in baris
                ],
            },
        )

    if masuk is not None:
        _pasang_rute_masuk(aplikasi, masuk, identitas, perekam, sekarang)
    if pengguna is not None:
        _pasang_rute_saya(aplikasi, pengguna, _identitas_atau_tolak, versi_naskah, sekarang)
    if masuk is not None and pengguna is not None:
        _pasang_rute_penarikan(aplikasi, masuk, _identitas_atau_tolak)
    if analitik is not None:
        _pasang_rute_analitik(aplikasi, analitik, _identitas_atau_tolak, sekarang)
    if kurasi is not None:
        _pasang_rute_kurasi(aplikasi, kurasi, _identitas_atau_tolak, sekarang)
    if penemuan is not None and pengguna is not None:
        _pasang_rute_penemuan(
            aplikasi, penemuan, pengguna, _identitas_atau_tolak, perekam, sekarang
        )
    if penilaian is not None:
        _pasang_rute_penilaian(aplikasi, penilaian, _identitas_atau_tolak, perekam, sekarang)
    if aduan is not None:
        _pasang_rute_aduan(aplikasi, aduan, _identitas_atau_tolak, sekarang)
    if sumber is not None:
        _pasang_rute_sumber(aplikasi, sumber, _identitas_atau_tolak, perekam, sekarang)

    return aplikasi


def _pasang_rute_masuk(
    aplikasi: FastAPI,
    penjaga: PenjagaMasuk,
    identitas: PenentuIdentitas,
    perekam: Perekam | None,
    sekarang: Callable[[], datetime],
) -> None:
    """Rute D-14 Bagian 3.1 — bentuknya Bagian 4.4. Hanya menerjemahkan.

    Peristiwa sesi direkam **sesudah** tanggapan ditentukan; perekam tidak
    melempar, sehingga tanggapan tidak bergantung padanya (R-03, R-07)."""

    @aplikasi.post(POLA_MASUK)
    async def masuk(permintaan: Request) -> Response:
        if not _berbadan_json(permintaan):
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_MASUK_TIDAK_LENGKAP, rute=POLA_MASUK
            )
        try:
            badan = PermintaanMasuk.model_validate(await permintaan.json())
        except (ValidationError, ValueError):
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_MASUK_TIDAK_LENGKAP, rute=POLA_MASUK
            )
        pengenal = await penjaga.masuk(badan.nama_pengguna, badan.sandi)
        if pengenal is None:
            return tanggapan_galat(
                401, KodeGalat.TIDAK_TERAUTENTIKASI, PESAN_MASUK_DITOLAK, rute=POLA_MASUK
            )
        # Sesi lama pada peramban yang sama dicabut: satu peramban, satu sesi.
        lama = permintaan.cookies.get(NAMA_KUKI)
        if lama:
            await penjaga.keluar(lama)
        if perekam is not None:
            await perekam.mulai_sesi(lambda: penjaga.pemilik_sesi(pengenal), sekarang=sekarang())
        tanggapan = Response(status_code=204)
        tanggapan.set_cookie(
            NAMA_KUKI,
            pengenal,
            max_age=int(MASA_SESI.total_seconds()),
            path="/",
            secure=True,
            httponly=True,
            samesite="strict",
        )
        return tanggapan

    @aplikasi.post(POLA_KELUAR)
    async def keluar(permintaan: Request) -> Response:
        siapa = await identitas.identitas(permintaan)
        if siapa is None:
            return tanggapan_galat(
                401, KodeGalat.TIDAK_TERAUTENTIKASI, PESAN_BELUM_MASUK, rute=POLA_KELUAR
            )
        if not _berbadan_json(permintaan):
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_TIDAK_LENGKAP, rute=POLA_KELUAR
            )
        # Identitas sudah lolos, sehingga kukinya pasti ada.
        await penjaga.keluar(permintaan.cookies.get(NAMA_KUKI, ""))
        if perekam is not None:
            await perekam.akhiri_sesi(siapa.pemilik, sekarang=sekarang())
        tanggapan = Response(status_code=204)
        tanggapan.delete_cookie(NAMA_KUKI, path="/", secure=True, httponly=True, samesite="strict")
        return tanggapan


def _pasang_rute_saya(
    aplikasi: FastAPI,
    simpan: PenyimpanPengguna,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
    versi_naskah: str | None,
    sekarang: Callable[[], datetime],
) -> None:
    """Rute D-14 Bagian 3.1 `/saya/*` — bentuknya Bagian 4.5. Hanya menerjemahkan;
    aturannya milik `src/api/saya.py` dan model fitur 022."""

    async def _baca(permintaan: Request) -> Any:
        try:
            return await permintaan.json()
        except ValueError:
            return None

    @aplikasi.get(POLA_PROFIL)
    async def baca_profil(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_PROFIL)
        if isinstance(siapa, JSONResponse):
            return siapa
        return JSONResponse(status_code=200, content=await ringkasan(simpan, siapa.pemilik))

    @aplikasi.put(POLA_PROFIL)
    async def simpan_profil(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_PROFIL)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            if not _berbadan_json(permintaan):
                raise ValueError("bukan JSON")
            profil = profil_sah(siapa.pemilik, await _baca(permintaan))
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_PROFIL_TIDAK_SAH, rute=POLA_PROFIL
            )
        await simpan.simpan_profil(siapa.pemilik, profil, sekarang=sekarang())
        return JSONResponse(status_code=200, content=await ringkasan(simpan, siapa.pemilik))

    @aplikasi.put(POLA_PRIORITAS)
    async def tetapkan_prioritas(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_PRIORITAS)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            if not _berbadan_json(permintaan):
                raise ValueError("bukan JSON")
            kategori = prioritas_sah(siapa.pemilik, await _baca(permintaan))
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_PRIORITAS_TIDAK_SAH, rute=POLA_PRIORITAS
            )
        await simpan.tetapkan_prioritas(siapa.pemilik, kategori, sekarang=sekarang())
        return JSONResponse(status_code=200, content=await ringkasan(simpan, siapa.pemilik))

    @aplikasi.post(POLA_PERSETUJUAN)
    async def persetujuan(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_PERSETUJUAN)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            if not _berbadan_json(permintaan):
                raise ValueError("bukan JSON")
            await putuskan_persetujuan(
                simpan,
                siapa.pemilik,
                await _baca(permintaan),
                versi_naskah=versi_naskah,
                sekarang=sekarang(),
            )
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_PERSETUJUAN_TIDAK_SAH, rute=POLA_PERSETUJUAN
            )
        return JSONResponse(status_code=200, content=await ringkasan(simpan, siapa.pemilik))


def _pasang_rute_penarikan(
    aplikasi: FastAPI,
    penjaga: PenjagaMasuk,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
) -> None:
    """`DELETE /saya/data` — D-14 Bagian 4.5, fitur 033. Hanya menerjemahkan:
    mencatat permintaan dan mencabut sesi milik penjaga masuk; penghapusannya
    milik perkakas tim dengan peran yang tidak dipegang layanan ini (K-1)."""

    @aplikasi.delete(POLA_DATA_SAYA)
    async def tarik_data(permintaan: Request) -> Response:
        siapa = await identitas_atau_tolak(permintaan, POLA_DATA_SAYA)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            if not _berbadan_json(permintaan):
                raise ValueError("bukan JSON")
            try:
                badan = await permintaan.json()
            except ValueError:
                badan = None
            penarikan_sah(badan)
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_PENARIKAN_TIDAK_SAH, rute=POLA_DATA_SAYA
            )
        await penjaga.minta_penarikan(siapa.pemilik)
        tanggapan = Response(status_code=202)
        tanggapan.delete_cookie(NAMA_KUKI, path="/", secure=True, httponly=True, samesite="strict")
        return tanggapan


def _pasang_rute_analitik(
    aplikasi: FastAPI,
    simpan: PenyimpanAnalitik,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
    sekarang: Callable[[], datetime],
) -> None:
    """Rute D-14 Bagian 3.4 milik peneliti — bentuknya Bagian 4.8. Hanya
    menerjemahkan; metrik dan ekspor milik `src/api/analitik.py` (fitur 035)."""

    @aplikasi.get(POLA_ANALITIK_RINGKAS)
    async def ringkas(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_ANALITIK_RINGKAS)
        if isinstance(siapa, JSONResponse):
            return siapa
        isi = ringkasan_analitik(await simpan.peristiwa(), sekarang=sekarang())
        return JSONResponse(status_code=200, content=isi.model_dump(mode="json"))

    @aplikasi.post(POLA_ANALITIK_EKSPOR)
    async def unduh(permintaan: Request) -> Response:
        siapa = await identitas_atau_tolak(permintaan, POLA_ANALITIK_EKSPOR)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            if not _berbadan_json(permintaan):
                raise ValueError("bukan JSON")
            try:
                badan = await permintaan.json()
            except ValueError:
                badan = None
            isi, nama = await ekspor(simpan, badan, peneliti=siapa.pemilik, sekarang=sekarang())
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_EKSPOR_TIDAK_SAH, rute=POLA_ANALITIK_EKSPOR
            )
        return Response(
            content=isi,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{nama}"'},
        )


def _pasang_rute_kurasi(
    aplikasi: FastAPI,
    simpan: PenyimpanKurasi,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
    sekarang: Callable[[], datetime],
) -> None:
    """Rute D-14 Bagian 3.4 milik kurator — bentuknya Bagian 4.7. Hanya
    menerjemahkan; aturannya milik `src/api/kurasi.py` dan model fitur 010."""

    def _tidak_ada(pola: str) -> JSONResponse:
        return tanggapan_galat(404, KodeGalat.SUMBER_TIDAK_ADA, PESAN_BUTIR_TIDAK_ADA, rute=pola)

    async def _badan(permintaan: Request) -> Any:
        if not _berbadan_json(permintaan):
            raise ValueError("bukan JSON")
        try:
            return await permintaan.json()
        except ValueError:
            return None

    @aplikasi.get(POLA_ANTREAN)
    async def baca_antrean(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_ANTREAN)
        if isinstance(siapa, JSONResponse):
            return siapa
        return JSONResponse(status_code=200, content=await antrean(simpan, sekarang=sekarang()))

    @aplikasi.post(POLA_PUTUSAN)
    async def putusan(permintaan: Request, id: str) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_PUTUSAN)
        if isinstance(siapa, JSONResponse):
            return siapa
        kini = sekarang()
        try:
            await putuskan(
                simpan, id, await _badan(permintaan), pseudonim=siapa.pemilik, sekarang=kini
            )
        except ButirTidakAda:
            return _tidak_ada(POLA_PUTUSAN)
        except RegulasiTidakBerlaku:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_REGULASI_TIDAK_BERLAKU, rute=POLA_PUTUSAN
            )
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_PUTUSAN_TIDAK_SAH, rute=POLA_PUTUSAN
            )
        return JSONResponse(status_code=200, content=await antrean(simpan, sekarang=kini))

    @aplikasi.post(POLA_TARIK)
    async def penarikan(permintaan: Request, id: str) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_TARIK)
        if isinstance(siapa, JSONResponse):
            return siapa
        kini = sekarang()
        try:
            await tarik(
                simpan, id, await _badan(permintaan), pseudonim=siapa.pemilik, sekarang=kini
            )
        except ButirTidakAda:
            return _tidak_ada(POLA_TARIK)
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_TARIK_TIDAK_SAH, rute=POLA_TARIK
            )
        return JSONResponse(status_code=200, content=await antrean(simpan, sekarang=kini))


def _pasang_rute_penemuan(
    aplikasi: FastAPI,
    penemuan: PenyimpanPenemuan,
    pengguna: PenyimpanPengguna,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
    perekam: Perekam | None,
    sekarang: Callable[[], datetime],
) -> None:
    """Rute D-14 Bagian 3.3 bagi beranda dan butir — bentuknya Bagian 4.6. Hanya
    menerjemahkan; aturannya milik `src/api/penemuan.py` dan fitur 011.

    Peristiwa direkam sesudah tanggapan tersusun dan tidak membacanya kembali
    (R-09): pemilihan beranda tidak menerima perekam maupun penyimpannya."""

    def _tidak_ada(pola: str) -> JSONResponse:
        return tanggapan_galat(404, KodeGalat.SUMBER_TIDAK_ADA, PESAN_BUTIR_TIDAK_ADA, rute=pola)

    @aplikasi.get(POLA_BERANDA)
    async def baca_beranda(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_BERANDA)
        if isinstance(siapa, JSONResponse):
            return siapa
        kini = sekarang()
        isi, baru = await susun_beranda(penemuan, pengguna, siapa.pemilik, sekarang=kini)
        if perekam is not None:
            await perekam.rekam_tayang(siapa.pemilik, baru, sekarang=kini)
        return JSONResponse(status_code=200, content=isi)

    @aplikasi.get(POLA_BUTIR)
    async def baca_butir(permintaan: Request, id: str) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_BUTIR)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            isi = await detail(penemuan, siapa.pemilik, id)
        except ButirTidakTampil:
            return _tidak_ada(POLA_BUTIR)
        if perekam is not None and not bukan_butir_dibuka(permintaan.headers):
            pemilik = siapa.pemilik
            await perekam.rekam_dibuka(
                pemilik, id, lambda: penemuan.kapan_tayang(pemilik, id), sekarang=sekarang()
            )
        return JSONResponse(status_code=200, content=isi)

    @aplikasi.post(POLA_TOLAK_BUTIR)
    async def tolak_butir(permintaan: Request, id: str) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_TOLAK_BUTIR)
        if isinstance(siapa, JSONResponse):
            return siapa
        kini = sekarang()
        try:
            if not _berbadan_json(permintaan):
                raise ValueError("bukan JSON")
            try:
                badan = await permintaan.json()
            except ValueError:
                badan = None
            alasan = await tolak(penemuan, siapa.pemilik, id, badan, sekarang=kini)
        except ButirTidakTampil:
            return _tidak_ada(POLA_TOLAK_BUTIR)
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_ALASAN_TIDAK_SAH, rute=POLA_TOLAK_BUTIR
            )
        isi, baru = await susun_beranda(penemuan, pengguna, siapa.pemilik, sekarang=kini)
        if perekam is not None:
            await perekam.rekam_belum_relevan(siapa.pemilik, id, alasan, sekarang=kini)
            await perekam.rekam_tayang(siapa.pemilik, baru, sekarang=kini)
        return JSONResponse(status_code=200, content=isi)


async def _badan_json(permintaan: Request) -> Any:
    """Badan JSON, atau `None` bila tak terbaca. `ValueError` bila bukan JSON (K-4)."""
    if not _berbadan_json(permintaan):
        raise ValueError("bukan JSON")
    try:
        return await permintaan.json()
    except ValueError:
        return None


def _pasang_rute_penilaian(
    aplikasi: FastAPI,
    simpan: PenyimpanPenilaian,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
    perekam: Perekam | None,
    sekarang: Callable[[], datetime],
) -> None:
    """`POST /pesan/{id}/penilaian` — D-14 Bagian 4.9, fitur 036. Aturannya milik
    `src/api/penilaian.py`; di sini hanya terjemahan galat dan perekaman."""

    def _tidak_sah() -> JSONResponse:
        return tanggapan_galat(
            400, KodeGalat.VALIDASI_GAGAL, PESAN_PENILAIAN_TIDAK_SAH, rute=POLA_PENILAIAN
        )

    @aplikasi.post(POLA_PENILAIAN)
    async def nilai_jawaban(permintaan: Request, id: str) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_PENILAIAN)
        if isinstance(siapa, JSONResponse):
            return siapa
        kini = sekarang()
        try:
            isi, hasil, diterima = await nilai(
                simpan, id, await _badan_json(permintaan), pemilik=siapa.pemilik, sekarang=kini
            )
        except PesanTidakAda:
            return tanggapan_galat(
                404, KodeGalat.SUMBER_TIDAK_ADA, PESAN_JAWABAN_TIDAK_ADA, rute=POLA_PENILAIAN
            )
        except ValueError:
            return _tidak_sah()
        # R-09: perekaman sesudah tercatat, lewat gerbang C-04; galatnya ditelan.
        if perekam is not None:
            await perekam.rekam_penilaian(
                siapa.pemilik,
                id,
                diterima.nilai,
                beralasan=diterima.alasan is not None,
                versi_model=hasil.versi_model,
                sekarang=kini,
            )
        return JSONResponse(status_code=200, content=isi)


def _pasang_rute_sumber(
    aplikasi: FastAPI,
    pembaca: PembacaSumber,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
    perekam: Perekam | None,
    sekarang: Callable[[], datetime],
) -> None:
    """`GET /sumber/{id}?bagian=` — D-14 Bagian 4.10, fitur 032. Aturannya milik
    `src/api/sumber.py`; di sini terjemahan galat dan `citation_opened`."""

    @aplikasi.get(POLA_SUMBER)
    async def baca_sumber_rute(permintaan: Request, id: str) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_SUMBER)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            tampil = await baca_sumber(pembaca, id, permintaan.query_params.get("bagian"))
        except SumberTidakTampil:
            return tanggapan_galat(
                404, KodeGalat.SUMBER_TIDAK_ADA, PESAN_SUMBER_TIDAK_ADA, rute=POLA_SUMBER
            )
        except ValueError:
            return tanggapan_galat(
                400, KodeGalat.VALIDASI_GAGAL, PESAN_BAGIAN_TIDAK_SAH, rute=POLA_SUMBER
            )
        if perekam is not None:
            await perekam.rekam_sumber_dibuka(
                siapa.pemilik, tampil.id_dokumen, tampil.jenis, sekarang=sekarang()
            )
        return JSONResponse(status_code=200, content=tampil.model_dump(mode="json"))


def _pasang_rute_aduan(
    aplikasi: FastAPI,
    simpan: PenyimpanAduan,
    identitas_atau_tolak: Callable[[Request, str], Awaitable[Identitas | JSONResponse]],
    sekarang: Callable[[], datetime],
) -> None:
    """`GET /kurasi/aduan` dan `POST /kurasi/aduan/{id}/tindak-lanjut` — D-14
    Bagian 4.9, peran `kurator`. Bentuk tanggapan keduanya sama (Bagian 4.7)."""

    @aplikasi.get(POLA_ADUAN)
    async def baca_aduan(permintaan: Request) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_ADUAN)
        if isinstance(siapa, JSONResponse):
            return siapa
        return JSONResponse(status_code=200, content=await daftar_aduan(simpan))

    @aplikasi.post(POLA_TINDAK_LANJUT)
    async def tindak_lanjut(permintaan: Request, id: str) -> JSONResponse:
        siapa = await identitas_atau_tolak(permintaan, POLA_TINDAK_LANJUT)
        if isinstance(siapa, JSONResponse):
            return siapa
        try:
            await tindak_lanjuti(
                simpan,
                id,
                await _badan_json(permintaan),
                pseudonim=siapa.pemilik,
                sekarang=sekarang(),
            )
        except AduanTidakAda:
            return tanggapan_galat(
                404, KodeGalat.SUMBER_TIDAK_ADA, PESAN_ADUAN_TIDAK_ADA, rute=POLA_TINDAK_LANJUT
            )
        except ValueError:
            return tanggapan_galat(
                400,
                KodeGalat.VALIDASI_GAGAL,
                PESAN_TINDAK_LANJUT_TIDAK_SAH,
                rute=POLA_TINDAK_LANJUT,
            )
        return JSONResponse(status_code=200, content=await daftar_aduan(simpan))
