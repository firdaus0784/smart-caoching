"""Uji titik jalan pengembangan lokal — `perkakas/jalankan_lokal.py`.

## Mengapa berkas ini ada di `perkakas/`, bukan `src/`

`src/` adalah ciptaan yang disebarkan. Titik jalan ini **bukan** bagian
aplikasi: ia perkakas pengembangan, sederajat dengan pemeriksa kepatuhan yang
juga tinggal di sana. Menaruhnya pada `src/` membuat identitas pengembangan
ikut terbawa ke mana pun aplikasi dipasang.

## Yang paling perlu dijaga uji ini

Titik jalan menyediakan **identitas tanpa autentikasi** — setiap pemanggil
diperlakukan sebagai kepala sekolah. Itu satu-satunya cara menjalankannya
sebelum autentikasi dibangun, dan justru karena itu ia berbahaya: berkas
semacam ini yang paling mungkin terbawa ke lingkungan sungguhan.

Tiga uji menjaganya, dan ketiganya tentang **penolakan**, bukan tentang
kemampuan: menolak alamat selain mesin sendiri, menyatakan diri pada
keluarannya, dan tidak dapat dipanggil dari `src/`.

## Jalur penjawaban sengaja belum dirakit penuh

`AmbangKecukupan` tidak dapat dibentuk tanpa `CatatanKalibrasi` yang menyebut
prosedur kalibrasi sungguhan — dan kalibrasi itu belum pernah dijalankan.
Merakitnya di sini berarti mengarang kalibrasi yang tidak terjadi, persis yang
C-16 cegah.

Karena itu titik jalan memakai penjawab pengganti yang **menyatakan sebabnya
sendiri** lewat `AlasanBerhenti.BUKTI_TIDAK_CUKUP`. Itu bukan penyederhanaan:
korpus memang kosong hari ini, sehingga jawaban yang sama akan keluar seandainya
jalur penuh dirakit.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.konftes_asinkron import jalankan

from perkakas.jalankan_lokal import (
    ALAMAT_AMAN,
    PenjawabBelumSiap,
    susun_untuk_pengembangan,
)

AKAR = Path(__file__).resolve().parents[2]


def test_hanya_mesin_sendiri_yang_diizinkan() -> None:
    """Titik jalan tanpa autentikasi tidak boleh dapat dihadapkan ke jaringan."""
    assert ALAMAT_AMAN == "127.0.0.1"


def test_alamat_selain_mesin_sendiri_ditolak() -> None:
    from perkakas.jalankan_lokal import periksa_alamat

    with pytest.raises(SystemExit):
        periksa_alamat("0.0.0.0")
    with pytest.raises(SystemExit):
        periksa_alamat("192.168.1.10")


def test_alamat_mesin_sendiri_diterima() -> None:
    from perkakas.jalankan_lokal import periksa_alamat

    periksa_alamat("127.0.0.1")
    periksa_alamat("localhost")


def test_aplikasi_dapat_disusun_dan_menjawab() -> None:
    klien = TestClient(susun_untuk_pengembangan())
    tanggapan = klien.post(
        "/api/v1/tanya",
        json={"id_percakapan": str(uuid.uuid4()), "pertanyaan": "Bagaimana menyusun RKAS?"},
    )
    assert tanggapan.status_code == 200
    assert tanggapan.json()["status_dasar"] == "tidak_ditemukan"


def test_jawaban_menyatakan_sebab_belum_menjawab() -> None:
    """Bukan diam. Sebabnya dibawa keluar agar dapat ditagih."""
    hasil = jalankan(PenjawabBelumSiap().jawab("Bagaimana menyusun RKAS?"))
    assert hasil.alasan_berhenti is not None
    assert hasil.alasan_berhenti.value == "bukti_tidak_cukup"


def test_penafian_selalu_ada_pada_jawaban() -> None:
    klien = TestClient(susun_untuk_pengembangan())
    isi = klien.post(
        "/api/v1/tanya",
        json={"id_percakapan": str(uuid.uuid4()), "pertanyaan": "Apa itu akreditasi?"},
    ).json()
    assert isi["penafian"].strip()


def test_rute_bawaan_kerangka_tetap_mati() -> None:
    """Titik jalan tidak boleh menghidupkan kembali apa yang aplikasi matikan."""
    klien = TestClient(susun_untuk_pengembangan())
    for jalur in ("/docs", "/redoc", "/openapi.json"):
        assert klien.get(jalur).status_code == 404, jalur


def test_versi_menyatakan_dirinya_pengembangan() -> None:
    """Jawaban membawa penanda versinya. Yang keluar dari titik jalan ini
    wajib terbaca sebagai pengembangan, bukan sebagai jawaban sungguhan."""
    klien = TestClient(susun_untuk_pengembangan())
    versi = klien.post(
        "/api/v1/tanya", json={"id_percakapan": str(uuid.uuid4()), "pertanyaan": "Apa itu RKAS?"}
    ).json()["versi"]
    assert "pengembangan" in " ".join(str(n) for n in versi.values()).lower()


def test_tidak_diimpor_dari_src() -> None:
    """`src/` tidak boleh bersandar pada perkakas pengembangan.

    Identitas tanpa autentikasi yang terjangkau dari kode yang disebarkan
    adalah identitas tanpa autentikasi yang suatu hari terpakai.
    """
    tersangkut = [
        berkas
        for berkas in (AKAR / "src").rglob("*.py")
        if "jalankan_lokal" in berkas.read_text(encoding="utf-8")
    ]
    assert not tersangkut, f"src/ menyebut perkakas pengembangan: {tersangkut}"


# ── fitur 029 T-7 · autentikasi sungguhan pada titik jalan ──────────


def test_autentikasi_bawaan_adalah_sesi() -> None:
    """K-7: `make jalan` memakai sesi sungguhan kecuali diminta tegas."""
    from perkakas.jalankan_lokal import penghurai

    assert penghurai().parse_args([]).autentikasi == "sesi"
    assert penghurai().parse_args(["--autentikasi", "pengembangan"]).autentikasi == "pengembangan"


def test_dengan_penyimpan_akun_tanpa_sesi_ditolak_dan_masuk_berfungsi() -> None:
    from src.api import sandi
    from src.penyimpanan.akun import AkunMemori, BarisAkun

    murah = sandi.ParameterScrypt(n=2**4, r=8, p=1)
    akun = AkunMemori()
    akun.pasang_akun(
        BarisAkun(
            id="ks-017",
            pseudonim="psd_abcdefghjkmnpqrs",
            peran="pengguna",
            status_aktif=True,
            turunan_sandi=sandi.turunkan("abcd-efgh-jkmn-pqrs", parameter=murah),
            gagal_beruntun=0,
            ditahan_sampai=None,
        )
    )
    klien = TestClient(
        susun_untuk_pengembangan(akun=akun, turunan_tiruan=sandi.turunkan("t", parameter=murah)),
        base_url="https://testserver",
    )
    assert klien.get("/api/v1/percakapan").status_code == 401
    masuk = klien.post(
        "/api/v1/auth/masuk", json={"nama_pengguna": "ks-017", "sandi": "abcd-efgh-jkmn-pqrs"}
    )
    assert masuk.status_code == 204
    assert klien.get("/api/v1/percakapan").status_code == 200


def test_tanpa_penyimpan_akun_rute_masuk_tidak_ada() -> None:
    """Mode `pengembangan`: penentu tiruan, tanpa rute masuk yang tidak dapat
    berbuat apa pun."""
    klien = TestClient(susun_untuk_pengembangan())
    assert klien.post("/api/v1/auth/masuk", json={}).status_code in (404, 405)


def test_titik_jalan_bersesi_memasang_rute_saya_dan_naskah(tmp_path: Path) -> None:
    """Fitur 030: rute `/saya/*` terpasang bersama sesi; versi naskah dibaca
    dari berkas — tanpa berkas, persetujuan ditolak."""
    import json

    from src.penyimpanan.akun import AkunMemori
    from src.penyimpanan.pengguna import PenggunaMemori

    from perkakas.jalankan_lokal import versi_naskah_terpasang

    assert versi_naskah_terpasang(tmp_path / "tidak-ada.json") is None
    berkas = tmp_path / "persetujuan.json"
    berkas.write_text(json.dumps({"versi": "v-uji", "judul": "J", "paragraf": ["P"]}), "utf-8")
    assert versi_naskah_terpasang(berkas) == "v-uji"

    klien = TestClient(
        susun_untuk_pengembangan(
            akun=AkunMemori(), pengguna=PenggunaMemori(), versi_naskah="v-uji"
        ),
        base_url="https://testserver",
    )
    assert klien.get("/api/v1/saya/profil").status_code == 401


def test_titik_jalan_bersesi_memasang_rute_kurasi_dan_penemuan() -> None:
    """Fitur 013: rute kurator dan beranda terpasang bersama sesi; tanpa
    penyimpannya keduanya tidak ada."""
    from src.penyimpanan.akun import AkunMemori
    from src.penyimpanan.kurasi import KurasiMemori
    from src.penyimpanan.penemuan import PenemuanMemori
    from src.penyimpanan.pengguna import PenggunaMemori

    kurasi = KurasiMemori()
    klien = TestClient(
        susun_untuk_pengembangan(
            akun=AkunMemori(),
            pengguna=PenggunaMemori(),
            kurasi=kurasi,
            penemuan=PenemuanMemori(kurasi),
        ),
        base_url="https://testserver",
    )
    assert klien.get("/api/v1/beranda").status_code == 401
    assert klien.get("/api/v1/kurasi/antrean").status_code == 401
    tanpa = TestClient(
        susun_untuk_pengembangan(akun=AkunMemori(), pengguna=PenggunaMemori()),
        base_url="https://testserver",
    )
    assert tanpa.get("/api/v1/beranda").status_code == 404


def test_titik_jalan_bersesi_merekam_dengan_versi_pengembangan() -> None:
    """Fitur 034, K-4: `versi_aplikasi` titik jalan berbunyi `pengembangan`,
    sama dengan penanda versinya; persetujuan tetap yang memutus (C-04)."""
    from datetime import UTC, datetime

    from src.api import sandi
    from src.penyimpanan.akun import AkunMemori, BarisAkun
    from src.penyimpanan.pengguna import PenggunaMemori
    from src.penyimpanan.telemetri import TelemetriMemori
    from tests.konftes_asinkron import jalankan

    from perkakas.jalankan_lokal import VERSI_APLIKASI_PENGEMBANGAN

    murah = sandi.ParameterScrypt(n=2**4, r=8, p=1)
    akun = AkunMemori()
    for nomor, huruf in (("ks-017", "a"), ("ks-018", "b")):
        akun.pasang_akun(
            BarisAkun(
                id=nomor,
                pseudonim="psd_" + huruf * 16,
                peran="pengguna",
                status_aktif=True,
                turunan_sandi=sandi.turunkan("abcd-efgh-jkmn-pqrs", parameter=murah),
                gagal_beruntun=0,
                ditahan_sampai=None,
            )
        )
    pengguna, telemetri = PenggunaMemori(), TelemetriMemori()
    jalankan(
        pengguna.catat_persetujuan(
            "psd_" + "a" * 16, versi_naskah="v-uji", disetujui=True, sekarang=datetime.now(UTC)
        )
    )
    klien = TestClient(
        susun_untuk_pengembangan(
            akun=akun,
            pengguna=pengguna,
            versi_naskah="v-uji",
            telemetri=telemetri,
            turunan_tiruan=sandi.turunkan("t", parameter=murah),
        ),
        base_url="https://testserver",
    )
    for nomor in ("ks-017", "ks-018"):
        jawab = klien.post(
            "/api/v1/auth/masuk", json={"nama_pengguna": nomor, "sandi": "abcd-efgh-jkmn-pqrs"}
        )
        assert jawab.status_code == 204
    (awal,) = jalankan(telemetri.milik("psd_" + "a" * 16))
    assert (awal.jenis, awal.versi_aplikasi) == ("session_start", "pengembangan")
    assert VERSI_APLIKASI_PENGEMBANGAN == "pengembangan"
    assert jalankan(telemetri.milik("psd_" + "b" * 16)) == ()


def test_titik_jalan_bersesi_memasang_rute_penarikan_tanpa_peran_penghapus() -> None:
    """Fitur 033: `DELETE /saya/data` terpasang bersama sesi dan penyimpan
    pengguna — rute itu hanya mencatat. Peran penghapus tidak pernah dipasang
    titik jalan (uji arah T-5); tanpa penyimpan pengguna rutenya tidak ada."""
    from src.penyimpanan.akun import AkunMemori
    from src.penyimpanan.pengguna import PenggunaMemori

    bersesi = TestClient(
        susun_untuk_pengembangan(akun=AkunMemori(), pengguna=PenggunaMemori()),
        base_url="https://testserver",
    )
    assert (
        bersesi.request("DELETE", "/api/v1/saya/data", json={"konfirmasi": True}).status_code == 401
    )
    tanpa = TestClient(susun_untuk_pengembangan(akun=AkunMemori()), base_url="https://testserver")
    assert tanpa.request("DELETE", "/api/v1/saya/data", json={"konfirmasi": True}).status_code in (
        404,
        405,
    )


def test_titik_jalan_bersesi_memasang_rute_analitik() -> None:
    """Fitur 035: rute peneliti terpasang bersama penyimpan analitik; tanpanya tidak ada."""
    from src.penyimpanan.akun import AkunMemori
    from src.penyimpanan.analitik import AnalitikMemori
    from src.penyimpanan.telemetri import TelemetriMemori

    dengan = TestClient(
        susun_untuk_pengembangan(akun=AkunMemori(), analitik=AnalitikMemori(TelemetriMemori())),
        base_url="https://testserver",
    )
    assert dengan.get("/api/v1/analitik/ringkas").status_code == 401
    tanpa = TestClient(susun_untuk_pengembangan(akun=AkunMemori()), base_url="https://testserver")
    assert tanpa.get("/api/v1/analitik/ringkas").status_code == 404
