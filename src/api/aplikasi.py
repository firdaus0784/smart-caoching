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

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

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
from src.api.peran import (
    POLA_DAFTAR_PERCAKAPAN,
    POLA_KELUAR,
    POLA_MASUK,
    POLA_PERSETUJUAN,
    POLA_PRIORITAS,
    POLA_PROFIL,
    POLA_SATU_PERCAKAPAN,
    POLA_TANYA,
    boleh,
)
from src.api.percakapan import Giliran, giliran_sah
from src.api.saya import (
    PESAN_PERSETUJUAN_TIDAK_SAH,
    PESAN_PRIORITAS_TIDAK_SAH,
    PESAN_PROFIL_TIDAK_SAH,
    prioritas_sah,
    profil_sah,
    putuskan_persetujuan,
    ringkasan,
)
from src.api.tanya import HasilTanya
from src.llm.galat import GalatLayananModel, KodeGalat
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.pengguna import PenyimpanPengguna
from src.penyimpanan.riwayat import PenyimpanRiwayat, PercakapanTidakAda

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
    """
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

        # R-07, C-14: jalur menerima pertanyaan saja — tanpa giliran sebelumnya.
        hasil = await jalur.jawab(badan.pertanyaan)

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
            )
        except PercakapanTidakAda:
            # Pemilik lain membuka percakapan yang sama di antara pemeriksaan
            # dan pencatatan. Jawabannya tidak dikirim: ia tidak tercatat.
            return _tidak_ada(RUTE_TANYA)
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
        _pasang_rute_masuk(aplikasi, masuk, identitas)
    if pengguna is not None:
        _pasang_rute_saya(aplikasi, pengguna, _identitas_atau_tolak, versi_naskah, sekarang)

    return aplikasi


def _pasang_rute_masuk(
    aplikasi: FastAPI, penjaga: PenjagaMasuk, identitas: PenentuIdentitas
) -> None:
    """Rute D-14 Bagian 3.1 — bentuknya Bagian 4.4. Hanya menerjemahkan."""

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
