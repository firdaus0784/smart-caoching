"""Pemeriksaan API penjalan U5 — T-5 fitur 042, R-03, R-04, R-05, K-4, P-3 A.

Atas **aplikasi bersesi yang berjalan** di `127.0.0.1` lewat uvicorn,
tersambung ke PostgreSQL dengan peran sungguhan, dan akun uji yang dibuat
`perkakas.akun` — seperti operator pada D-09 langkah 5. Aplikasi tiruan yang
menjawab 200 bagi segalanya membuktikan pemeriksaan tidak lulus dengan
sendirinya.
"""

from __future__ import annotations

import io
import re
import secrets
import threading
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.api import sandi
from src.kamus.segmen import IndeksTujuan
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.akun import AkunPostgres
from src.penyimpanan.analitik import AnalitikPostgres
from src.penyimpanan.koleksi import KoleksiPostgres
from src.penyimpanan.kurasi import KurasiPostgres
from src.penyimpanan.penemuan import PenemuanPostgres
from src.penyimpanan.pengguna import PenggunaPostgres
from src.penyimpanan.penilaian import AduanPostgres, PenilaianPostgres
from src.penyimpanan.riwayat import RiwayatMemori
from src.penyimpanan.sumber import PembacaSumberPostgres
from src.penyimpanan.telemetri import TelemetriPostgres
from tests.api.test_penjawab_korpus import _tanam
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, psql, siapkan
from tests.penyimpanan.test_akun import SambunganPeran

from perkakas import akun as perkakas_akun
from perkakas.jalankan_lokal import susun_untuk_pengembangan
from perkakas.kepatuhan.__main__ import konteks_dari_lingkungan
from perkakas.kepatuhan.api import (
    nik_rekaan,
    periksa_uk05,
    periksa_uk07,
    periksa_uk14,
    periksa_uk15,
    rute_d14,
)
from perkakas.kepatuhan.hasil import Keadaan, KonfigurasiApi, Konteks

AKAR = Path(__file__).resolve().parents[2]
siapkan()


def _sajikan(app: FastAPI) -> Iterator[str]:
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning"))
    benang = threading.Thread(target=server.run, daemon=True)
    benang.start()
    while not server.started:
        time.sleep(0.01)
    porta = server.servers[0].sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{porta}"
    finally:
        server.should_exit = True
        benang.join(timeout=10)


def _aplikasi_bersesi() -> FastAPI:
    def p(peran: str) -> Any:
        return SambunganPeran(peran)

    return susun_untuk_pengembangan(
        RiwayatMemori(),
        akun=AkunPostgres(p("peran_autentikasi")),
        pengguna=PenggunaPostgres(p("peran_pengguna")),
        versi_naskah="uji-042",
        kurasi=KurasiPostgres(p("peran_kurasi")),
        penemuan=PenemuanPostgres(p("peran_penayangan")),
        telemetri=TelemetriPostgres(p("peran_telemetri")),
        analitik=AnalitikPostgres(p("peran_analitik")),
        penilaian=PenilaianPostgres(p("peran_penilaian")),
        aduan=AduanPostgres(p("peran_kurasi")),
        sumber=PembacaSumberPostgres(p("peran_pembaca_sumber")),
        koleksi=KoleksiPostgres(p("peran_koleksi")),
    )


@pytest.fixture(scope="module")
def alamat() -> Iterator[str]:
    yield from _sajikan(_aplikasi_bersesi())


def _pengelola(kueri: str) -> None:
    hasil = psql("smart_coaching", "-c", kueri)
    assert hasil.returncode == 0, hasil.stderr


@pytest.fixture(scope="module")
def dokumen() -> Iterator[str]:
    """Satu dokumen korpus bagi UK-05, dihapus sesudahnya: uji tidak
    meninggalkan baris selain akun uji (tasks.md)."""
    id_dokumen = "d42-" + secrets.token_hex(3)
    _tanam(id_dokumen, IndeksTujuan.UTAMA, "Kepala sekolah menyusun rencana.")
    yield id_dokumen
    for tabel, kolom in (
        ("indeks_utama.segmen_teks", "id_dokumen"),
        ("korpus.status_dokumen", "id_dokumen"),
        ("korpus.metadata_dokumen", "id_dokumen"),
        ("korpus.dokumen_sumber", "id"),
    ):
        _pengelola(f"delete from {tabel} where {kolom} = '{id_dokumen}'")


def _akun_uji(alamat: str) -> tuple[str, str]:
    """Seperti operator: `perkakas.akun buat`, lalu masuk."""
    id_akun = "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz") for _ in range(6)) + "-042"
    keluar = io.StringIO()
    kode = perkakas_akun.utama(
        ["buat", "--id", id_akun, "--peran", "pengguna"],
        pengelola=perkakas_akun.PengelolaAkunPostgres(SambunganPeran("peran_pengelola_akun")),  # type: ignore[arg-type]
        keluar=keluar,
        galat=io.StringIO(),
        parameter=sandi.ParameterScrypt(n=2**4, r=8, p=1),
    )
    assert kode == 0
    (kata,) = re.findall(r"\b[2-9a-z]{4}-[2-9a-z]{4}-[2-9a-z]{4}-[2-9a-z]{4}\b", keluar.getvalue())
    t = httpx.post(f"{alamat}/api/v1/auth/masuk", json={"nama_pengguna": id_akun, "sandi": kata})
    assert t.status_code == 204, t.text
    baris = t.headers["set-cookie"]
    kuki = baris.split(";", 1)[0].split("=", 1)[1]
    return id_akun, kuki


def _konteks(alamat: str, id_akun: str, kuki: str) -> Konteks:
    dasar = konteks_dari_lingkungan({"PGHOST": HOST, "PGPORT": str(PORT)}, AKAR)
    return Konteks(buka=dasar.buka, api=KonfigurasiApi(alamat, id_akun, kuki), akar_repo=AKAR)


def test_rute_dibaca_dari_d14_bagian_3() -> None:
    rute = rute_d14(AKAR)
    assert ("POST", "/api/v1/tanya", "pengguna") in [(r.metode, r.jalur, r.peran) for r in rute]
    assert {r.peran for r in rute} >= {"publik", "semua", "pengguna", "kurator", "peneliti"}


def test_nik_rekaan_dikenali_pendeteksi_dan_bukan_milik_siapa_pun() -> None:
    """UK-14 menguji penolakan, bukan pendeteksi: nomornya wajib terdeteksi."""
    nomor = {nik_rekaan() for _ in range(20)}
    assert len(nomor) == 20
    for n in nomor:
        assert len(n) == 16 and n.isdigit() and n.startswith("00")
        assert [x.jenis for x in periksa_data_pribadi(f"NIK saya {n}")] == ["nik"]


def test_keempat_uk_api_lulus_atas_aplikasi_yang_berjalan(alamat: str, dokumen: str) -> None:
    id_akun, kuki = _akun_uji(alamat)
    konteks = _konteks(alamat, id_akun, kuki)
    for periksa in (periksa_uk05, periksa_uk07, periksa_uk14, periksa_uk15):
        hasil = jalankan(periksa(konteks))
        assert hasil.keadaan is Keadaan.LULUS, (hasil.kode, hasil.rincian)
        assert all(kuki not in r for r in hasil.rincian)
    rincian = jalankan(periksa_uk15(konteks)).rincian
    assert any("/api/v1/kurasi/antrean" in r and "403" in r for r in rincian)


def _pseudonim(id_akun: str) -> str:
    baris: Any = jalankan(
        SambunganPeran("peran_autentikasi").fetchrow(
            "select pseudonim from akun.pengguna where id = $1", id_akun
        )
    )
    return str(baris["pseudonim"])


def test_akun_berpersetujuan_menjadikan_uk05_belum(alamat: str) -> None:
    """K-4 (M-8): akun uji wajib tanpa persetujuan."""
    id_akun, kuki = _akun_uji(alamat)
    pseudonim = _pseudonim(id_akun)
    jalankan(
        PenggunaPostgres(SambunganPeran("peran_pengguna")).catat_persetujuan(
            pseudonim, versi_naskah="uji-042", disetujui=True, sekarang=datetime.now(UTC)
        )
    )
    hasil = jalankan(periksa_uk05(_konteks(alamat, id_akun, kuki)))
    assert hasil.keadaan is Keadaan.BELUM
    assert "persetujuan" in hasil.rincian[0]


def _tiruan(status_profil: int) -> FastAPI:
    app = FastAPI()

    @app.api_route("/{jalur:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def semua(jalur: str, permintaan: Request) -> JSONResponse:
        if jalur == "api/v1/saya/profil":
            return JSONResponse({"persetujuan": "belum_diminta"}, status_code=status_profil)
        return JSONResponse({"gema": (await permintaan.body()).decode()}, status_code=200)

    return app


def _perekam_tanpa_persetujuan(pseudonim: str) -> FastAPI:
    """Tiruan yang merekam `citation_opened` tanpa membaca persetujuan."""
    app = FastAPI()

    @app.get("/api/v1/saya/profil")
    async def profil() -> JSONResponse:
        return JSONResponse({"persetujuan": "belum_diminta"})

    @app.get("/api/v1/sumber/{id}")
    async def sumber(id: str) -> JSONResponse:
        await SambunganPeran("peran_telemetri").execute(
            "insert into telemetri.peristiwa (pseudonim, jenis, waktu, properti, "
            "versi_aplikasi, versi_model) values ($1, 'citation_opened', now(), '{}', 'v', 'v')",
            pseudonim,
        )
        return JSONResponse({"id_dokumen": id})

    return app


def test_rekaman_tanpa_persetujuan_menggagalkan_uk05(alamat: str, dokumen: str) -> None:
    """Kendali positif UK-05: rekaman yang sungguh terjadi terhitung."""
    id_akun, kuki = _akun_uji(alamat)
    pseudonim = _pseudonim(id_akun)
    try:
        for tiruan in _sajikan(_perekam_tanpa_persetujuan(pseudonim)):
            hasil = jalankan(periksa_uk05(_konteks(tiruan, id_akun, kuki)))
    finally:
        _pengelola(f"delete from telemetri.peristiwa where pseudonim = '{pseudonim}'")
    assert hasil.keadaan is Keadaan.GAGAL
    assert "0 lalu 1" in hasil.rincian[0]


def test_aplikasi_yang_menjawab_200_bagi_segalanya_gagal() -> None:
    for alamat in _sajikan(_tiruan(200)):
        konteks = _konteks(alamat, "uji-042", "kuki-tiruan")
        for periksa in (periksa_uk07, periksa_uk14, periksa_uk15):
            assert jalankan(periksa(konteks)).keadaan is Keadaan.GAGAL


def test_kewarasan_gagal_menggagalkan_keempatnya() -> None:
    """K-4 (M-5): alamat yang salah tidak terbaca 'tidak terjangkau'."""
    for alamat in _sajikan(_tiruan(500)):
        konteks = _konteks(alamat, "uji-042", "kuki-tiruan")
        for periksa in (periksa_uk05, periksa_uk07, periksa_uk14, periksa_uk15):
            hasil = jalankan(periksa(konteks))
            assert hasil.keadaan is Keadaan.GAGAL
            assert "kewarasan" in hasil.rincian[0]


def test_tanpa_konfigurasi_api_belum_dapat_diperiksa() -> None:
    konteks = Konteks(buka=None, api=None, akar_repo=AKAR)  # type: ignore[arg-type]
    for periksa in (periksa_uk05, periksa_uk07, periksa_uk14, periksa_uk15):
        hasil = jalankan(periksa(konteks))
        assert hasil.keadaan is Keadaan.BELUM
        assert "KEPATUHAN_API" in hasil.rincian[0]
