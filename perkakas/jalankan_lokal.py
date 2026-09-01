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
from typing import Any

from fastapi import FastAPI, Request
from src.api.aplikasi import susun_aplikasi
from src.api.peran import Peran
from src.api.tanya import AlasanBerhenti, HasilTanya
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

    def jawab(self, pertanyaan: str, **_: Any) -> HasilTanya:
        return HasilTanya(
            tanggapan=Tanggapan(
                id_pesan="pengembangan",
                status_dasar=StatusDasar.TIDAK_DITEMUKAN,
                penafian=PENAFIAN,
                versi=VERSI_PENGEMBANGAN,
            ),
            alasan_berhenti=AlasanBerhenti.BUKTI_TIDAK_CUKUP,
        )


class IdentitasPengembangan:
    """Setiap pemanggil diperlakukan sebagai kepala sekolah — **tanpa
    autentikasi apa pun**. Lihat bahaya pada uraian modul."""

    def peran(self, _permintaan: Request) -> Peran:
        return Peran.PENGGUNA


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


def susun_untuk_pengembangan() -> FastAPI:
    """Rakit aplikasi dengan pengganti pengembangan."""
    return susun_aplikasi(
        jalur=PenjawabBelumSiap(),
        identitas=IdentitasPengembangan(),
        percakapan={},
    )


def main() -> None:  # pragma: no cover — dijalankan orang, bukan uji
    penghurai = argparse.ArgumentParser(
        description="Jalankan Smart-Coaching pada mesin sendiri untuk pengembangan."
    )
    penghurai.add_argument("--alamat", default=ALAMAT_AMAN)
    penghurai.add_argument("--porta", type=int, default=8000)
    argumen = penghurai.parse_args()

    periksa_alamat(argumen.alamat)

    import uvicorn

    print(
        "\n  Smart-Coaching — mode pengembangan\n"
        f"  Alamat   : http://{argumen.alamat}:{argumen.porta}\n"
        '  Coba     : POST /api/v1/tanya  {"pertanyaan": "..."}\n'
        "\n"
        "  Tanpa autentikasi. Tanpa penyimpanan bertahan — data hilang saat\n"
        "  dimatikan. Jawaban selalu 'tidak ditemukan' karena korpus kosong.\n"
    )
    uvicorn.run(susun_untuk_pengembangan(), host=argumen.alamat, port=argumen.porta)


if __name__ == "__main__":  # pragma: no cover
    main()
