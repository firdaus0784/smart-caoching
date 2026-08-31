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
jalan. Autentikasi (FR-A01) belum dibangun modul mana pun, dan nilai baku pada
bidang yang menentukan siapa pemanggil adalah nilai baku yang akan terpakai di
lingkungan sungguhan.

Peladen ini karena itu **belum layak dihadapkan ke jaringan publik**. Keadaan
itu dinyatakan di sini, pada spesifikasinya, dan pada bentuk fungsinya —
bukan pada satu di antaranya saja.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.api.peran import (
    POLA_DAFTAR_PERCAKAPAN,
    POLA_SATU_PERCAKAPAN,
    POLA_TANYA,
    Peran,
    boleh,
)
from src.api.percakapan import Percakapan
from src.api.tanya import HasilTanya

PESAN_TIDAK_BERHAK = "Akun Anda tidak dapat membuka bagian ini."
PESAN_TIDAK_LENGKAP = "Pertanyaan belum lengkap. Tulis ulang dengan kalimat utuh."
PESAN_TIDAK_ADA = "Percakapan yang Anda cari tidak ditemukan."
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
class PenentuIdentitas(Protocol):
    """Pengubah permintaan menjadi peran — satu-satunya kemampuan yang dituntut.

    `Protocol`, bukan kelas: fitur autentikasi kelak mengisinya tanpa menyentuh
    berkas ini.
    """

    def peran(self, permintaan: Request) -> Peran: ...


@runtime_checkable
class JalurPenjawab(Protocol):
    """Bentuk `Jalur.jawab()` sebagaimana dipakai adaptor ini."""

    def jawab(self, pertanyaan: str, **argumen: Any) -> HasilTanya: ...


class PermintaanTanya(BaseModel):
    """Badan permintaan `POST /api/v1/tanya`.

    `extra="forbid"` menolak bidang tambahan — termasuk bidang bernama `peran`
    yang, bila diterima, akan membuat pemanggil menentukan penjaganya sendiri.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    pertanyaan: str = Field(min_length=1)


def _galat(status: int, pesan: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"pesan": pesan})


def susun_aplikasi(
    *,
    jalur: JalurPenjawab,
    identitas: PenentuIdentitas,
    percakapan: dict[str, Percakapan],
) -> FastAPI:
    """Susun peladen — R-04, R-07.

    `identitas` **tanpa nilai baku**, disengaja; lihat uraian modul.
    """
    aplikasi = FastAPI(
        title="Smart-Coaching Adaptif",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    def _tolak_bila_tidak_berhak(permintaan: Request, pola: str) -> JSONResponse | None:
        """R-01 — dipanggil **sebelum** apa pun yang lain pada tiap penangan."""
        if not boleh(identitas.peran(permintaan), permintaan.method, pola):
            return _galat(403, PESAN_TIDAK_BERHAK)
        return None

    @aplikasi.post(RUTE_TANYA)
    async def tanya(permintaan: Request) -> JSONResponse:
        ditolak = _tolak_bila_tidak_berhak(permintaan, RUTE_TANYA)
        if ditolak is not None:
            return ditolak
        try:
            badan = PermintaanTanya.model_validate(await permintaan.json())
        except (ValidationError, ValueError):
            return _galat(400, PESAN_TIDAK_LENGKAP)
        if not badan.pertanyaan.strip():
            return _galat(400, PESAN_TIDAK_LENGKAP)

        hasil = jalur.jawab(badan.pertanyaan)
        # R-03: tertahan atau tidak, bentuk dan statusnya sama. D-14
        # menetapkan `tidak_ditemukan` memakai bentuk jawaban yang sah, dan
        # status galat akan membuat layar menampilkannya sebagai kegagalan
        # sistem — D-02 titik kritis T3 menuntut sebaliknya.
        return JSONResponse(status_code=200, content=hasil.tanggapan.model_dump(mode="json"))

    @aplikasi.get(RUTE_DAFTAR_PERCAKAPAN)
    async def daftar_percakapan(permintaan: Request) -> JSONResponse:
        ditolak = _tolak_bila_tidak_berhak(permintaan, RUTE_DAFTAR_PERCAKAPAN)
        if ditolak is not None:
            return ditolak
        return JSONResponse(status_code=200, content={"percakapan": sorted(percakapan)})

    @aplikasi.get(RUTE_SATU_PERCAKAPAN)
    async def satu_percakapan(permintaan: Request, id: str) -> JSONResponse:
        ditolak = _tolak_bila_tidak_berhak(permintaan, RUTE_SATU_PERCAKAPAN)
        if ditolak is not None:
            return ditolak
        satu = percakapan.get(id)
        if satu is None:
            return _galat(404, PESAN_TIDAK_ADA)
        # R-05: `Giliran` tidak memiliki bidang tanggapan, dan bentuk itu yang
        # menjaga C-07 — tanggapan yang tersimpan menua.
        return JSONResponse(
            status_code=200,
            content={
                "id_percakapan": satu.id_percakapan,
                "giliran": [g.model_dump(mode="json") for g in satu.giliran],
            },
        )

    return aplikasi
