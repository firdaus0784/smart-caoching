"""Titik jalan pengembangan lokal — bukan bagian ciptaan yang disebarkan.

Menjalankan aplikasi pada mesin sendiri agar jalur permintaan, kendali hak
akses, bentuk tanggapan, dan riwayat percakapan dapat dicoba langsung.

## Mengapa berkas ini tinggal di `perkakas/`

`src/` adalah kode yang disebarkan. Berkas ini perkakas pengembangan,
sederajat dengan pemeriksa kepatuhan yang juga tinggal di sini. Menaruhnya
pada `src/` membuat identitas pengembangan ikut terbawa ke mana pun aplikasi
dipasang — dan uji `test_tidak_diimpor_dari_src` menuntut `src/` tidak pernah
menyebutnya.

## Dua mode autentikasi

Sejak fitur 029 bawaannya `--autentikasi sesi`: akun dan sesi di PostgreSQL,
masuk lewat `POST /api/v1/auth/masuk` dengan akun buatan `perkakas.akun`
(K-7). Mode `--autentikasi pengembangan` tetap ada dan tetap berbahaya: ia
menyediakan **identitas tetap tanpa pemeriksaan apa pun**, setiap pemanggil
diperlakukan sebagai kepala sekolah yang sama — berkas semacam ini yang paling
mungkin terbawa ke lingkungan sungguhan.

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
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import PenentuSesi, PenjagaMasuk
from src.api.identitas import Identitas
from src.api.peran import Peran
from src.api.saya import baca_naskah
from src.api.tanya import AlasanBerhenti, HasilTanya
from src.penyimpanan.akun import PERAN_AUTENTIKASI, AkunPostgres, PenyimpanAkun
from src.penyimpanan.analitik import PERAN_ANALITIK, AnalitikPostgres, PenyimpanAnalitik
from src.penyimpanan.kurasi import PERAN_KURASI, KurasiPostgres, PenyimpanKurasi
from src.penyimpanan.penemuan import PERAN_PENAYANGAN, PenemuanPostgres, PenyimpanPenemuan
from src.penyimpanan.pengguna import PERAN_PENGGUNA, PenggunaPostgres, PenyimpanPengguna
from src.penyimpanan.riwayat import (
    PERAN_RIWAYAT,
    PenyimpanRiwayat,
    RiwayatMemori,
    RiwayatPostgres,
)
from src.penyimpanan.telemetri import PERAN_TELEMETRI, PenyimpanTelemetri, TelemetriPostgres
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

VERSI_APLIKASI_PENGEMBANGAN = "pengembangan"
"""`versi_aplikasi` peristiwa telemetri dari titik jalan ini — fitur 034, K-4.
Sama dengan penanda versinya: peristiwa dari mesin pengembang tidak dapat
tertukar dengan peristiwa pilot saat analisis."""


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

    async def identitas(self, _permintaan: Request) -> Identitas:
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
    """Satu sambungan baru per kueri, sebagai satu peran — pengembangan saja.

    Memenuhi `SambunganAktif` tanpa kolam sambungan: sederhana, dan cukup bagi
    satu pengembang pada mesinnya sendiri. Sandi tidak pernah ditulis di sini;
    `asyncpg` membacanya dari lingkungan (`PGPASSWORD`) bila peladen memintanya.
    """

    def __init__(self, host: str, porta: int, peran: str = PERAN_RIWAYAT) -> None:
        self._host = host
        self._porta = porta
        self._peran = peran

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> Any:
        import asyncpg  # type: ignore[import-untyped]

        sambungan = await asyncpg.connect(
            host=self._host, port=self._porta, user=self._peran, database="smart_coaching"
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


def susun_untuk_pengembangan(
    riwayat: PenyimpanRiwayat | None = None,
    *,
    akun: PenyimpanAkun | None = None,
    turunan_tiruan: str | None = None,
    pengguna: PenyimpanPengguna | None = None,
    versi_naskah: str | None = None,
    kurasi: PenyimpanKurasi | None = None,
    penemuan: PenyimpanPenemuan | None = None,
    telemetri: PenyimpanTelemetri | None = None,
    analitik: PenyimpanAnalitik | None = None,
) -> FastAPI:
    """Rakit aplikasi dengan pengganti pengembangan.

    Riwayat bawaannya di memori — hilang saat dimatikan, dan keluaran `main`
    menyatakannya. `--riwayat postgres` memakai PostgreSQL sebagai
    `peran_riwayat` (fitur 028).

    Dengan `akun`, identitas dibaca dari sesi dan rute masuk terpasang
    (fitur 029); tanpanya, penentu tiruan tanpa pemeriksaan dipakai.
    `turunan_tiruan` disuntikkan hanya oleh uji. `kurasi` dan `penemuan`
    memasang rute kurator dan beranda (fitur 013). `telemetri` merekam
    peristiwa bagi pengguna yang menyetujui, bertanda versi `pengembangan`
    (fitur 034). `analitik` memasang rute peneliti (fitur 035).
    """
    if akun is None:
        return susun_aplikasi(
            jalur=PenjawabBelumSiap(),
            identitas=IdentitasPengembangan(),
            riwayat=riwayat if riwayat is not None else RiwayatMemori(),
        )
    return susun_aplikasi(
        jalur=PenjawabBelumSiap(),
        identitas=PenentuSesi(akun),
        riwayat=riwayat if riwayat is not None else RiwayatMemori(),
        masuk=PenjagaMasuk(akun, turunan_tiruan=turunan_tiruan),
        pengguna=pengguna,
        versi_naskah=versi_naskah,
        kurasi=kurasi,
        penemuan=penemuan,
        telemetri=telemetri,
        versi_aplikasi=VERSI_APLIKASI_PENGEMBANGAN if telemetri is not None else None,
        analitik=analitik,
    )


BERKAS_NASKAH = (
    Path(__file__).resolve().parents[1] / "web" / "public" / "naskah" / "persetujuan.json"
)
"""Naskah ET-02 yang diisi tim (fitur 030, K-4). Agen tidak menulisnya."""


def versi_naskah_terpasang(berkas: Path = BERKAS_NASKAH) -> str | None:
    """Versi naskah yang peladen terima, atau `None` bila belum ada naskah."""
    naskah = baca_naskah(berkas)
    return None if naskah is None else naskah.versi


def penghurai() -> argparse.ArgumentParser:
    """Argumen titik jalan — dipisah dari `main` agar bawaannya dapat diuji."""
    hasil = argparse.ArgumentParser(
        description="Jalankan Smart-Coaching pada mesin sendiri untuk pengembangan."
    )
    hasil.add_argument("--alamat", default=ALAMAT_AMAN)
    hasil.add_argument("--porta", type=int, default=8000)
    hasil.add_argument("--riwayat", choices=("memori", "postgres"), default="memori")
    hasil.add_argument("--autentikasi", choices=("sesi", "pengembangan"), default="sesi")
    return hasil


def main() -> None:  # pragma: no cover — dijalankan orang, bukan uji
    argumen = penghurai().parse_args()

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

    akun: PenyimpanAkun | None = None
    pengguna: PenyimpanPengguna | None = None
    kurasi: PenyimpanKurasi | None = None
    penemuan: PenyimpanPenemuan | None = None
    telemetri: PenyimpanTelemetri | None = None
    analitik: PenyimpanAnalitik | None = None
    if argumen.autentikasi == "sesi":
        # Fitur 035: rute peneliti, membaca peristiwa sebagai peran_analitik.
        analitik = AnalitikPostgres(
            SambunganPerKueri(
                os.environ.get("PGHOST", ALAMAT_AMAN),
                int(os.environ.get("PGPORT", "5432")),
                PERAN_ANALITIK,
            )
        )
        # Fitur 034: peristiwa tambah-saja, sebagai peran_telemetri.
        telemetri = TelemetriPostgres(
            SambunganPerKueri(
                os.environ.get("PGHOST", ALAMAT_AMAN),
                int(os.environ.get("PGPORT", "5432")),
                PERAN_TELEMETRI,
            )
        )
        # Fitur 013: kurator dan penayang, masing-masing dengan perannya.
        kurasi = KurasiPostgres(
            SambunganPerKueri(
                os.environ.get("PGHOST", ALAMAT_AMAN),
                int(os.environ.get("PGPORT", "5432")),
                PERAN_KURASI,
            )
        )
        penemuan = PenemuanPostgres(
            SambunganPerKueri(
                os.environ.get("PGHOST", ALAMAT_AMAN),
                int(os.environ.get("PGPORT", "5432")),
                PERAN_PENAYANGAN,
            )
        )
        pengguna = PenggunaPostgres(
            SambunganPerKueri(
                os.environ.get("PGHOST", ALAMAT_AMAN),
                int(os.environ.get("PGPORT", "5432")),
                PERAN_PENGGUNA,
            )
        )
        akun = AkunPostgres(
            SambunganPerKueri(
                os.environ.get("PGHOST", ALAMAT_AMAN),
                int(os.environ.get("PGPORT", "5432")),
                PERAN_AUTENTIKASI,
            )
        )
        keterangan_identitas = (
            "sesi sungguhan — masuk dengan akun buatan `python -m perkakas.akun buat`."
        )
        keterangan_telemetri = "peran_telemetri — hanya bagi pengguna yang menyetujui."
    else:
        keterangan_telemetri = "tidak merekam."
        keterangan_identitas = (
            f"TANPA AUTENTIKASI — {PEMILIK_PENGEMBANGAN}, satu pemilik bagi semua pemanggil."
        )

    print(
        "\n  Smart-Coaching — mode pengembangan\n"
        f"  Alamat    : http://{argumen.alamat}:{argumen.porta}\n"
        f"  Identitas : {keterangan_identitas}\n"
        f"  Riwayat   : {keterangan_riwayat}\n"
        f"  Telemetri : {keterangan_telemetri}\n"
        "\n"
        "  Jawaban selalu 'tidak ditemukan' karena korpus kosong.\n"
    )
    uvicorn.run(
        susun_untuk_pengembangan(
            riwayat,
            akun=akun,
            pengguna=pengguna,
            versi_naskah=versi_naskah_terpasang(),
            kurasi=kurasi,
            penemuan=penemuan,
            telemetri=telemetri,
            analitik=analitik,
        ),
        host=argumen.alamat,
        port=argumen.porta,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
