"""Rute analitik — T-4 fitur 035, R-01, R-05, R-06, R-07; K-3; D-14 Bagian 4.8."""

from __future__ import annotations

import csv
import hashlib
import io
import secrets
from datetime import UTC, date, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.analitik import PESAN_EKSPOR_TIDAK_SAH, VERSI_PENGEMBANGAN
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import MASA_SESI, NAMA_KUKI, PenentuSesi
from src.llm.galat import kalimat_terlalu_panjang
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.analitik import AnalitikMemori
from src.penyimpanan.riwayat import RiwayatMemori
from src.penyimpanan.telemetri import BarisPeristiwa, TelemetriMemori
from src.telemetri.ekspor import KOLOM
from tests.api.test_saya_http import JalurPencatat
from tests.konftes_asinkron import jalankan

SEKARANG = datetime(2031, 3, 31, 5, 0, tzinfo=UTC)
RINGKAS = "/api/v1/analitik/ringkas"
EKSPOR = "/api/v1/analitik/ekspor"


def _akun(id_akun: str, huruf: str, peran: str) -> BarisAkun:
    return BarisAkun(
        id=id_akun,
        pseudonim="psd_" + huruf * 16,
        peran=peran,
        status_aktif=True,
        turunan_sandi="scrypt$16$8$1$AAAA$AAAA",
        gagal_beruntun=0,
        ditahan_sampai=None,
    )


PENELITI = _akun("pn-001", "p", "peneliti")
PENGGUNA = _akun("ks-017", "a", "pengguna")
KURATOR = _akun("kr-001", "k", "kurator")


def _baris(waktu: datetime, versi: str = "pilot-1", huruf: str = "a") -> BarisPeristiwa:
    return BarisPeristiwa(
        pseudonim="psd_" + huruf * 16,
        jenis="session_start",
        waktu=waktu,
        properti={},
        versi_aplikasi=versi,
        versi_model="tanpa_model",
    )


class Lingkungan:
    def __init__(self) -> None:
        self.akun = AkunMemori()
        self.telemetri = TelemetriMemori()
        self.analitik = AnalitikMemori(self.telemetri)
        self.kuki: dict[str, str] = {}
        for satu in (PENELITI, PENGGUNA, KURATOR):
            self.akun.pasang_akun(satu)
            pengenal = secrets.token_urlsafe(32)
            jalankan(
                self.akun.buat_sesi(
                    hashlib.sha256(pengenal.encode()).digest(),
                    satu.id,
                    sekarang=SEKARANG,
                    kedaluwarsa_pada=SEKARANG + MASA_SESI,
                )
            )
            self.kuki[satu.id] = pengenal
        self.klien = TestClient(
            susun_aplikasi(
                jalur=JalurPencatat(),
                identitas=PenentuSesi(self.akun, sekarang=lambda: SEKARANG),
                riwayat=RiwayatMemori(),
                analitik=self.analitik,
                sekarang=lambda: SEKARANG,
            ),
            base_url="https://testserver",
        )
        for b in (
            _baris(datetime(2031, 3, 1, 1, tzinfo=UTC)),
            _baris(datetime(2031, 3, 1, 18, tzinfo=UTC)),  # 2 Maret WIB
            _baris(datetime(2031, 3, 2, 18, tzinfo=UTC)),  # 3 Maret WIB — di luar rentang
            _baris(datetime(2031, 3, 1, 2, tzinfo=UTC), versi=VERSI_PENGEMBANGAN),
            _baris(datetime(2031, 2, 28, 16, tzinfo=UTC), huruf="b"),  # 28 Februari 23.00 WIB
        ):
            self.telemetri._baris.append(b)

    def minta(self, metode: str, jalur: str, siapa: BarisAkun = PENELITI, **lain: Any) -> Any:
        return self.klien.request(
            metode, jalur, headers={"Cookie": f"{NAMA_KUKI}={self.kuki[siapa.id]}"}, **lain
        )


def test_ringkas_berbentuk_d14_bagi_peneliti() -> None:
    ling = Lingkungan()
    tanggapan = ling.minta("GET", RINGKAS)
    assert tanggapan.status_code == 200
    isi = tanggapan.json()
    assert set(isi) == {
        "dihitung_pada",
        "keterlibatan",
        "penemuan",
        "penilaian",
        "belum_terukur",
        "integritas",
    }
    assert isi["penilaian"] == {"per_nilai": {"membantu": 0, "tidak_membantu": 0, "keliru": 0}}
    assert set(isi["keterlibatan"]) == {"aktif_harian", "aktif_mingguan", "retensi", "sesi"}
    assert isi["integritas"]["pengembangan"] == 1
    assert isi["penemuan"]["rasio"] is None
    assert isi["dihitung_pada"].endswith("Z") or isi["dihitung_pada"].endswith("+00:00")


@pytest.mark.parametrize("siapa", [PENGGUNA, KURATOR])
def test_selain_peneliti_403(siapa: BarisAkun) -> None:
    """R-01, M-9."""
    ling = Lingkungan()
    assert ling.minta("GET", RINGKAS, siapa=siapa).status_code == 403
    tanggapan = ling.minta(
        "POST", EKSPOR, siapa=siapa, json={"dari": "2031-03-01", "sampai": "2031-03-02"}
    )
    assert tanggapan.status_code == 403
    assert ling.analitik._ekspor == []


def test_tanpa_sesi_401() -> None:
    ling = Lingkungan()
    assert ling.klien.get(RINGKAS).status_code == 401


def test_ekspor_csv_rentang_wib_inklusif_tanpa_pengembangan_dan_tercatat() -> None:
    """R-05, R-06, M-4, M-6."""
    ling = Lingkungan()
    tanggapan = ling.minta("POST", EKSPOR, json={"dari": "2031-03-01", "sampai": "2031-03-02"})
    assert tanggapan.status_code == 200
    assert tanggapan.headers["content-type"].startswith("text/csv")
    assert tanggapan.headers["content-disposition"].startswith("attachment;")
    baris = list(csv.DictReader(io.StringIO(tanggapan.text)))
    assert tuple(baris[0]) == KOLOM
    assert [b["waktu"] for b in baris] == [
        "2031-03-01T01:00:00+00:00",
        "2031-03-01T18:00:00+00:00",
    ]
    (catatan,) = ling.analitik._ekspor
    assert (catatan.peneliti, catatan.dari, catatan.sampai) == (
        PENELITI.pseudonim,
        date(2031, 3, 1),
        date(2031, 3, 2),
    )
    assert (catatan.termasuk_pengembangan, catatan.jumlah_baris) == (False, 2)
    assert catatan.diekspor_pada == SEKARANG


def test_ekspor_dengan_pengembangan_bila_diminta_tegas() -> None:
    ling = Lingkungan()
    tanggapan = ling.minta(
        "POST",
        EKSPOR,
        json={"dari": "2031-02-28", "sampai": "2031-03-01", "termasuk_pengembangan": True},
    )
    versi = [b["versi_aplikasi"] for b in csv.DictReader(io.StringIO(tanggapan.text))]
    assert sorted(versi) == ["pengembangan", "pilot-1", "pilot-1"]
    assert ling.analitik._ekspor[0].termasuk_pengembangan is True


@pytest.mark.parametrize(
    "badan",
    [
        {"dari": "2031-03-05", "sampai": "2031-03-01"},
        {"dari": "2031-03-01"},
        {"dari": "kemarin", "sampai": "2031-03-01"},
        {"dari": "2031-03-01", "sampai": "2031-03-02", "id_pengguna": "x"},
        None,
    ],
)
def test_permintaan_ekspor_salah_400_dan_tidak_tercatat(badan: Any) -> None:
    ling = Lingkungan()
    tanggapan = ling.minta("POST", EKSPOR, json=badan)
    assert tanggapan.status_code == 400
    assert tanggapan.json()["galat"]["pesan_pengguna"] == PESAN_EKSPOR_TIDAK_SAH
    assert ling.analitik._ekspor == []


def test_ekspor_menuntut_json() -> None:
    ling = Lingkungan()
    tanggapan = ling.minta(
        "POST", EKSPOR, content=b'{"dari": "2031-03-01", "sampai": "2031-03-02"}'
    )
    assert tanggapan.status_code == 400


def test_jejak_tercatat_sebelum_berkas_dikirim() -> None:
    """K-3: penyimpan jejak yang gagal menggagalkan ekspor — berkas tidak terkirim."""

    class JejakRusak(AnalitikMemori):
        async def catat_ekspor(self, catatan: Any) -> int:
            raise RuntimeError("jejak tidak tersimpan")

    ling = Lingkungan()
    rusak = JejakRusak(ling.telemetri)
    klien = TestClient(
        susun_aplikasi(
            jalur=JalurPencatat(),
            identitas=PenentuSesi(ling.akun, sekarang=lambda: SEKARANG),
            riwayat=RiwayatMemori(),
            analitik=rusak,
            sekarang=lambda: SEKARANG,
        ),
        base_url="https://testserver",
        raise_server_exceptions=False,
    )
    tanggapan = klien.post(
        EKSPOR,
        json={"dari": "2031-03-01", "sampai": "2031-03-02"},
        headers={"Cookie": f"{NAMA_KUKI}={ling.kuki[PENELITI.id]}"},
    )
    assert tanggapan.status_code == 500
    assert "psd_" not in tanggapan.text


def test_tanpa_penyimpan_analitik_rute_tidak_ada() -> None:
    akun = AkunMemori()
    klien = TestClient(
        susun_aplikasi(jalur=JalurPencatat(), identitas=PenentuSesi(akun), riwayat=RiwayatMemori()),
        base_url="https://testserver",
    )
    assert klien.get(RINGKAS).status_code == 404


def test_pesan_memenuhi_c13() -> None:
    assert not kalimat_terlalu_panjang(PESAN_EKSPOR_TIDAK_SAH)


def test_waktu_ringkas_tanpa_mikrodetik_bergantung_jam() -> None:
    ling = Lingkungan()
    a = ling.minta("GET", RINGKAS).json()
    b = ling.minta("GET", RINGKAS).json()
    assert a == b
