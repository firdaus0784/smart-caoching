"""Bentuk galat D-14 Bagian 4.2 pada lapisan HTTP — T-5 fitur 028, R-14, TK-66.

Sejak fitur 023 peladen mengembalikan galat `{"pesan": …}`, bukan bentuk
D-14 — tanpa kode dan tanpa `id_jejak` — dan uji fitur 023 memeriksa isi
pesannya, bukan bentuknya, sehingga selisih itu tidak pernah menjatuhkan
gerbang (TK-66). Berkas ini menuntut bentuknya.

Log operasional diperiksa sama tegasnya dengan tanggapannya: `id_jejak`
yang sama muncul pada keduanya, dan log **tidak pernah** memuat pertanyaan
maupun pesan pengecualian — hanya nama kelasnya.
"""

from __future__ import annotations

import logging
import re

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import (
    PESAN_GANGGUAN,
    PESAN_TIDAK_ADA,
    PESAN_TIDAK_BERHAK,
    PESAN_TIDAK_LENGKAP,
    susun_aplikasi,
)
from src.api.galat import LOG_OPERASIONAL
from src.api.peran import Peran
from src.api.tanya import HasilTanya
from src.llm.galat import GalatLayananModel
from tests.api.test_aplikasi import IdentitasTetap, JalurPalsu, _aplikasi, _tanggapan

POLA_JEJAK = re.compile(r"^trc_[0-9a-f]{12}$")
RAHASIA = "NIK saya 3201234567890123 tolong dicek"


class JalurRusak:
    def __init__(self, galat: Exception) -> None:
        self._galat = galat

    async def jawab(self, pertanyaan: str, **_: object) -> HasilTanya:
        raise self._galat


def _klien_rusak(galat: Exception) -> TestClient:
    aplikasi = susun_aplikasi(
        jalur=JalurRusak(galat), identitas=IdentitasTetap(Peran.PENGGUNA), percakapan={}
    )
    return TestClient(aplikasi, raise_server_exceptions=False)


def _galat(tanggapan: object) -> dict[str, str]:
    badan = tanggapan.json()  # type: ignore[attr-defined]
    assert set(badan) == {"galat"}, badan
    isi: dict[str, str] = badan["galat"]
    assert set(isi) == {"kode", "pesan_pengguna", "id_jejak"}, isi
    assert POLA_JEJAK.match(isi["id_jejak"]), isi["id_jejak"]
    return isi


@pytest.mark.parametrize(
    ("metode", "jalur", "badan", "peran", "status", "kode", "pesan"),
    [
        (
            "post",
            "/api/v1/tanya",
            {"pertanyaan": "x"},
            Peran.ANOTATOR,
            403,
            "TIDAK_BERWENANG",
            PESAN_TIDAK_BERHAK,
        ),
        (
            "get",
            "/api/v1/percakapan",
            None,
            Peran.ANOTATOR,
            403,
            "TIDAK_BERWENANG",
            PESAN_TIDAK_BERHAK,
        ),
        (
            "post",
            "/api/v1/tanya",
            {"pertanyaan": "   "},
            Peran.PENGGUNA,
            400,
            "VALIDASI_GAGAL",
            PESAN_TIDAK_LENGKAP,
        ),
        (
            "post",
            "/api/v1/tanya",
            {"tanya": "x"},
            Peran.PENGGUNA,
            400,
            "VALIDASI_GAGAL",
            PESAN_TIDAK_LENGKAP,
        ),
        (
            "get",
            "/api/v1/percakapan/tidak-ada",
            None,
            Peran.PENGGUNA,
            404,
            "SUMBER_TIDAK_ADA",
            PESAN_TIDAK_ADA,
        ),
    ],
)
def test_galat_berbentuk_d14(
    metode: str,
    jalur: str,
    badan: dict[str, str] | None,
    peran: Peran,
    status: int,
    kode: str,
    pesan: str,
) -> None:
    aplikasi, _ = _aplikasi(peran=peran)
    klien = TestClient(aplikasi)
    tanggapan = klien.post(jalur, json=badan) if metode == "post" else klien.get(jalur)

    assert tanggapan.status_code == status
    isi = _galat(tanggapan)
    assert isi["kode"] == kode
    assert isi["pesan_pengguna"] == pesan


def test_galat_tak_tertangani_menjadi_galat_internal_tanpa_rincian(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        tanggapan = _klien_rusak(RuntimeError(RAHASIA)).post(
            "/api/v1/tanya", json={"pertanyaan": "Bagaimana supervisi?"}
        )

    assert tanggapan.status_code == 500
    isi = _galat(tanggapan)
    assert isi["kode"] == "GALAT_INTERNAL"
    assert isi["pesan_pengguna"] == PESAN_GANGGUAN
    assert "3201234567890123" not in tanggapan.text
    assert "RuntimeError" not in tanggapan.text


def test_penyedia_model_gagal_menjadi_layanan_model_gagal() -> None:
    sebab = TimeoutError("penyedia-x lambat")
    tanggapan = _klien_rusak(GalatLayananModel(sebab)).post(
        "/api/v1/tanya", json={"pertanyaan": "Bagaimana supervisi?"}
    )

    assert tanggapan.status_code == 503
    isi = _galat(tanggapan)
    assert isi["kode"] == "LAYANAN_MODEL_GAGAL"
    assert isi["pesan_pengguna"] == GalatLayananModel.PESAN_PENGGUNA
    assert "penyedia-x" not in tanggapan.text


# ── log operasional ─────────────────────────────────────────────────────


def test_id_jejak_sama_pada_tanggapan_dan_log(caplog: pytest.LogCaptureFixture) -> None:
    aplikasi, _ = _aplikasi(peran=Peran.ANOTATOR)
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        tanggapan = TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "x"})

    id_jejak = _galat(tanggapan)["id_jejak"]
    catatan = [r.getMessage() for r in caplog.records if r.name == LOG_OPERASIONAL.name]
    assert len(catatan) == 1
    assert id_jejak in catatan[0]
    assert "TIDAK_BERWENANG" in catatan[0]
    assert "/api/v1/tanya" in catatan[0]


def test_log_hanya_nama_kelas_sebab_bukan_pesannya(caplog: pytest.LogCaptureFixture) -> None:
    """Pesan pengecualian dapat memuat pertanyaan — termasuk yang berdata
    pribadi. Yang ditulis ke log hanya nama kelasnya."""
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        _klien_rusak(RuntimeError(RAHASIA)).post("/api/v1/tanya", json={"pertanyaan": RAHASIA})

    teks = "\n".join(r.getMessage() for r in caplog.records)
    assert "RuntimeError" in teks
    assert "3201234567890123" not in teks
    assert "NIK saya" not in teks


def test_setiap_galat_membangkitkan_id_jejak_baru() -> None:
    aplikasi, _ = _aplikasi(peran=Peran.ANOTATOR)
    klien = TestClient(aplikasi)
    a = _galat(klien.get("/api/v1/percakapan"))["id_jejak"]
    b = _galat(klien.get("/api/v1/percakapan"))["id_jejak"]
    assert a != b


def test_jawaban_sah_tidak_berbentuk_galat() -> None:
    """Pasangan: `tidak_ditemukan` tetap jawaban 200, bukan galat (R-03 fitur 023)."""
    aplikasi, _ = _aplikasi(hasil=HasilTanya(tanggapan=_tanggapan()))
    tanggapan = TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "x"})
    assert tanggapan.status_code == 200
    assert "galat" not in tanggapan.json()
    assert JalurPalsu  # dipakai bersama berkas uji aplikasi
