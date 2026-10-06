"""Rute penarikan data — T-4 fitur 033, R-01, R-05, R-08; K-4, K-5; D-14 Bagian 4.5.

Rute ini tidak menghapus apa pun: ia mencatat permintaan dan mencabut seluruh
sesi akun. Yang diuji karena itu akibatnya bagi permintaan **berikutnya** —
sesi lain, masuk ulang, perekaman — bukan isi basis data.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from typing import Any

import pytest
from src.api.autentikasi import MASA_SESI, NAMA_KUKI
from src.api.saya import PESAN_PENARIKAN_TIDAK_SAH
from src.llm.galat import kalimat_terlalu_panjang
from src.penyimpanan.akun import BarisAkun
from tests.api.test_rekaman_http import A, Lingkungan
from tests.konftes_asinkron import jalankan

DATA = "/api/v1/saya/data"
SETUJU = {"konfirmasi": True}


def _tarik(ling: Lingkungan, badan: Any = SETUJU, **lain: Any) -> Any:
    if "content" not in lain and "headers_tambahan" not in lain:
        lain["json"] = badan
    return ling.minta("DELETE", DATA, **lain)


def test_penarikan_diterima_202_tanpa_badan_dan_kuki_dihapus() -> None:
    ling = Lingkungan()
    ling.masuk()
    tanggapan = _tarik(ling)
    assert tanggapan.status_code == 202
    assert tanggapan.content == b""
    kuki = tanggapan.headers["set-cookie"]
    assert kuki.startswith(f'{NAMA_KUKI}=""') or kuki.startswith(f"{NAMA_KUKI}=;")
    assert "Max-Age=0" in kuki
    # Kuki yang disalin sebelum meminta tidak lagi berlaku di peladen.
    assert ling.minta("GET", "/api/v1/saya/profil").status_code == 401


def test_seluruh_sesi_akun_dicabut_bukan_hanya_yang_meminta() -> None:
    """M-1: rute yang tidak mencabut sesi membiarkan peramban lain tetap masuk."""
    ling = Lingkungan()
    ling.masuk()
    lain = ling.kuki
    ling.masuk()
    assert ling.kuki != lain
    assert _tarik(ling).status_code == 202
    ling.kuki = lain
    assert ling.minta("GET", "/api/v1/saya/profil").status_code == 401


def test_masuk_sesudah_meminta_ditolak_sama_dengan_sandi_salah() -> None:
    """K-4: tanpa kalimat yang memberi tahu orang lain bahwa akun sedang menarik datanya."""
    ling = Lingkungan()
    ling.masuk()
    salah = ling.masuk(kata="bukan-sandinya-sama-sekali")
    _tarik(ling)
    sesudah = ling.masuk()
    assert sesudah.status_code == salah.status_code == 401
    assert sesudah.json()["galat"]["pesan_pengguna"] == salah.json()["galat"]["pesan_pengguna"]
    assert sesudah.json()["galat"]["kode"] == salah.json()["galat"]["kode"]


def test_perekaman_berhenti_seketika_bagi_yang_menyetujui() -> None:
    """R-01: tanpa sesi tidak ada pemilik; tidak satu peristiwa pun sesudah meminta."""
    ling = Lingkungan()
    ling.setuju()
    ling.masuk()
    sebelum = ling.jenis()
    assert sebelum == ["session_start"]
    _tarik(ling)
    ling.kini += timedelta(minutes=1)
    assert ling.minta("POST", "/api/v1/auth/keluar", json={}).status_code == 401
    ling.masuk()
    assert ling.jenis() == sebelum


@pytest.mark.parametrize(
    "badan",
    [
        None,
        {},
        {"konfirmasi": False},
        {"konfirmasi": "ya"},
        {"konfirmasi": 1},
        {"konfirmasi": True, "alasan": "bosan"},
        [True],
    ],
)
def test_tanpa_konfirmasi_tegas_ditolak_dan_tidak_tercatat(badan: Any) -> None:
    """M-8: permintaan kosong yang terkirim tidak sengaja tidak memicu penarikan."""
    ling = Lingkungan()
    ling.masuk()
    tanggapan = _tarik(ling, badan)
    assert tanggapan.status_code == 400
    galat = tanggapan.json()["galat"]
    assert (galat["kode"], galat["pesan_pengguna"]) == ("VALIDASI_GAGAL", PESAN_PENARIKAN_TIDAK_SAH)
    assert ling.minta("GET", "/api/v1/saya/profil").status_code == 200
    assert ling.masuk().status_code == 204


def test_menuntut_json() -> None:
    ling = Lingkungan()
    ling.masuk()
    tanggapan = _tarik(ling, content=b'{"konfirmasi": true}', headers_tambahan={})
    assert tanggapan.status_code == 400
    teks = ling.minta(
        "DELETE",
        DATA,
        content=b'{"konfirmasi": true}',
        headers_tambahan={"Content-Type": "text/plain"},
    )
    assert teks.status_code == 400
    assert ling.minta("GET", "/api/v1/saya/profil").status_code == 200


def test_tanpa_sesi_401_dan_kurator_403() -> None:
    ling = Lingkungan()
    ling.kuki = "tidak-dikenal"
    assert _tarik(ling).status_code == 401
    kurator = BarisAkun(
        id="kr-001",
        pseudonim="psd_kkkkkkkkkkkkkkkk",
        peran="kurator",
        status_aktif=True,
        turunan_sandi="scrypt$16$8$1$AAAA$AAAA",
        gagal_beruntun=0,
        ditahan_sampai=None,
    )
    ling.akun.pasang_akun(kurator)
    pengenal = secrets.token_urlsafe(32)
    jalankan(
        ling.akun.buat_sesi(
            hashlib.sha256(pengenal.encode()).digest(),
            kurator.id,
            sekarang=ling.kini,
            kedaluwarsa_pada=ling.kini + MASA_SESI,
        )
    )
    ling.kuki = pengenal
    assert _tarik(ling).status_code == 403
    # Akun pengguna tidak tersentuh oleh penolakan itu.
    assert jalankan(ling.akun.baca_akun(A.id)) == A


def test_pesan_memenuhi_c13() -> None:
    assert not kalimat_terlalu_panjang(PESAN_PENARIKAN_TIDAK_SAH)


def test_badan_json_rusak_ditolak() -> None:
    ling = Lingkungan()
    ling.masuk()
    rusak = ling.minta(
        "DELETE",
        DATA,
        content=b'{"konfirmasi": tr',
        headers_tambahan={"Content-Type": "application/json"},
    )
    assert rusak.status_code == 400
    assert ling.minta("GET", "/api/v1/saya/profil").status_code == 200
