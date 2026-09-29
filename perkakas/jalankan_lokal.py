"""Titik jalan pengembangan lokal — bukan bagian ciptaan yang disebarkan.

Menjalankan aplikasi pada mesin sendiri agar jalur permintaan, kendali hak
akses, bentuk tanggapan, dan riwayat percakapan dapat dicoba langsung.

## Mengapa berkas ini tinggal di `perkakas/`

`src/` adalah kode yang disebarkan. Berkas ini perkakas pengembangan,
sederajat dengan pemeriksa kepatuhan yang juga tinggal di sini. Menaruhnya
pada `src/` membuat identitas pengembangan ikut terbawa ke mana pun aplikasi
dipasang — dan uji `test_tidak_diimpor_dari_src` menuntut `src/` tidak pernah
menyebutnya.

## Bahaya berkas ini, dinyatakan terus terang

Autentikasi (FR-A01) belum dibangun modul mana pun. Titik jalan ini karena itu
menyediakan **identitas tetap tanpa pemeriksaan apa pun**: setiap pemanggil
diperlakukan sebagai kepala sekolah. Itu satu-satunya cara menjalankannya
sebelum autentikasi ada, dan justru itu yang membuatnya berbahaya — berkas
semacam ini yang paling mungkin terbawa ke lingkungan sungguhan.

Tiga penjagaan, dan ketiganya berupa penolakan:

1. **Hanya mengikat pada mesin sendiri.** Alamat selain `127.0.0.1` ditolak
   sebelum peladen menyala, bukan diperingatkan lalu tetap dijalankan.
2. **Menyatakan dirinya pada keluarannya.** Penanda versi pada setiap jawaban
   berbunyi `pengembangan`, sehingga jawaban dari sini tidak dapat tertukar
   dengan jawaban sungguhan.
3. **Tidak terjangkau dari `src/`.** Diuji.

## Mengapa jalur penjawaban belum dirakit penuh

`AmbangKecukupan` tidak dapat dibentuk tanpa `CatatanKalibrasi` yang menyebut
prosedur kalibrasi sungguhan, dan kalibrasi itu belum pernah dijalankan.
Merakitnya di sini berarti **mengarang kalibrasi yang tidak terjadi** — persis
yang C-16 cegah, dan penolakan bentuk itu bekerja sebagaimana dirancang.

Penggantinya menyatakan sebabnya sendiri lewat `AlasanBerhenti`. Ini bukan
penyederhanaan yang menutupi: korpus memang kosong hari ini, sehingga jawaban
yang keluar sama persis dengan yang akan keluar seandainya jalur penuh dirakit.

Titik jalan ini berhenti berguna begitu fitur 019, 020, dan 024 selesai — dan
sebaiknya dihapus pada hari itu, bukan dibiarkan menua.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from typing import Any

from fastapi import FastAPI, Request
from src.api.aplikasi import susun_aplikasi
from src.api.identitas import Identitas
from src.api.peran import Peran
from src.api.tanya import AlasanBerhenti, HasilTanya
from src.penyimpanan.riwayat import (
    PERAN_RIWAYAT,
    PenyimpanRiwayat,
    RiwayatMemori,
    RiwayatPostgres,
)
from src.rag.jawaban.tanggapan import StatusDasar, Tanggapan, Versi

ALAMAT_AMAN = "127.0.0.1"
"""Satu-satunya alamat yang diizinkan. Lihat uraian modul."""

_ALAMAT_DITERIMA = frozenset({ALAMAT_AMAN, "localhost"})

PENAFIAN = (
    "Jawaban ini bukan pengganti keputusan Anda sebagai kepala sekolah. "
    "Aplikasi berjalan dalam mode pengembangan."
)

VERSI_PENGEMBANGAN = Versi(
    model="belum-dipasang-pengembangan",
    indeks="kosong-pengembangan",
    kode="pengembangan-lokal",
)
"""Penanda versi yang menyatakan dirinya. Lihat penjagaan nomor 2."""


class PenjawabBelumSiap:
    """Pengganti jalur penjawaban selama korpus kosong dan ambang belum ada.

    Menyatakan sebabnya lewat `AlasanBerhenti`, tidak diam. Sebab yang tidak
    dibawa keluar tidak dapat ditagih siapa pun.
    """

    async def jawab(self, pertanyaan: str, **_: Any) -> HasilTanya:
        return HasilTanya(
            tanggapan=Tanggapan(
                id_pesan=f"pengembangan-{uuid.uuid4().hex[:12]}",
                status_dasar=StatusDasar.TIDAK_DITEMUKAN,
                penafian=PENAFIAN,
                versi=VERSI_PENGEMBANGAN,
            ),
            alasan_berhenti=AlasanBerhenti.BUKTI_TIDAK_CUKUP,
        )


PEMILIK_PENGEMBANGAN = "pengembangan-pemilik-tunggal"
"""Satu pemilik tetap bagi seluruh pemanggil — R-17 fitur 028.

Menyatakan dirinya, sama dengan penanda versi `pengembangan`: riwayat yang
tercatat dengan pemilik ini tidak dapat tertukar dengan riwayat sungguhan.
"""


class IdentitasPengembangan:
    """Setiap pemanggil diperlakukan sebagai kepala sekolah yang **sama** —
    **tanpa autentikasi apa pun**. Lihat bahaya pada uraian modul."""

    def identitas(self, _permintaan: Request) -> Identitas:
        return Identitas(peran=Peran.PENGGUNA, pemilik=PEMILIK_PENGEMBANGAN)


def periksa_alamat(alamat: str) -> None:
    """Tolak alamat selain mesin sendiri — penjagaan nomor 1.

    Berhenti, bukan memperingatkan. Peringatan yang tetap menjalankan peladen
    adalah peringatan yang dibaca sesudah peladen menyala.
    """
    if alamat not in _ALAMAT_DITERIMA:
        print(
            f"Ditolak: alamat {alamat!r} bukan mesin sendiri.\n"
            "Titik jalan ini tidak memiliki autentikasi, sehingga hanya boleh\n"
            f"diikat pada {ALAMAT_AMAN}. Untuk lingkungan lain, bangun titik\n"
            "jalan tersendiri beserta autentikasinya (FR-A01).",
            file=sys.stderr,
        )
        raise SystemExit(2)


class SambunganPerKueri:
    """Satu sambungan baru per kueri, sebagai `peran_riwayat` — pengembangan saja.

    Memenuhi `SambunganAktif` tanpa kolam sambungan: sederhana, dan cukup bagi
    satu pengembang pada mesinnya sendiri. Sandi tidak pernah ditulis di sini;
    `asyncpg` membacanya dari lingkungan (`PGPASSWORD`) bila peladen memintanya.
    """

    def __init__(self, host: str, porta: int) -> None:
        self._host = host
        self._porta = porta

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        sambungan = await asyncpg.connect(
            host=self._host, port=self._porta, user=PERAN_RIWAYAT, database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def fetch(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetch", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("execute", kueri, *argumen)


def susun_untuk_pengembangan(riwayat: PenyimpanRiwayat | None = None) -> FastAPI:
    """Rakit aplikasi dengan pengganti pengembangan.

    Riwayat bawaannya di memori — hilang saat dimatikan, dan keluaran `main`
    menyatakannya. `--riwayat postgres` memakai PostgreSQL sebagai
    `peran_riwayat` (fitur 028).
    """
    return susun_aplikasi(
        jalur=PenjawabBelumSiap(),
        identitas=IdentitasPengembangan(),
        riwayat=riwayat if riwayat is not None else RiwayatMemori(),
    )


def main() -> None:  # pragma: no cover — dijalankan orang, bukan uji
    penghurai = argparse.ArgumentParser(
        description="Jalankan Smart-Coaching pada mesin sendiri untuk pengembangan."
    )
    penghurai.add_argument("--alamat", default=ALAMAT_AMAN)
    penghurai.add_argument("--porta", type=int, default=8000)
    penghurai.add_argument("--riwayat", choices=("memori", "postgres"), default="memori")
    argumen = penghurai.parse_args()

    periksa_alamat(argumen.alamat)

    import os

    import uvicorn

    riwayat: PenyimpanRiwayat
    if argumen.riwayat == "postgres":
        riwayat = RiwayatPostgres(
            SambunganPerKueri(
                os.environ.get("PGHOST", ALAMAT_AMAN), int(os.environ.get("PGPORT", "5432"))
            )
        )
        keterangan_riwayat = "PostgreSQL sebagai peran_riwayat — bertahan saat dimatikan."
    else:
        riwayat = RiwayatMemori()
        keterangan_riwayat = "di memori — HILANG saat dimatikan (--riwayat postgres)."

    print(
        "\n  Smart-Coaching — mode pengembangan\n"
        f"  Alamat   : http://{argumen.alamat}:{argumen.porta}\n"
        '  Coba     : POST /api/v1/tanya  {"pertanyaan": "...", "id_percakapan": "<uuid4>"}\n'
        f"  Riwayat  : {keterangan_riwayat}\n"
        f"  Pemilik  : {PEMILIK_PENGEMBANGAN} — satu pemilik bagi semua pemanggil.\n"
        "\n"
        "  Tanpa autentikasi. Jawaban selalu 'tidak ditemukan' karena korpus kosong.\n"
    )
    uvicorn.run(susun_untuk_pengembangan(riwayat), host=argumen.alamat, port=argumen.porta)


if __name__ == "__main__":  # pragma: no cover
    main()
