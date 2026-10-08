"""Rute penilaian, aduan, dan tindak lanjut — T-5 fitur 036, R-01, R-03, R-04,
R-06, R-09; D-14 Bagian 4.9.

Akun bersesi sungguhan, tiga peran: dua kepala sekolah dan satu kurator. Jawaban
datang lewat `/tanya` sungguhan, sehingga yang dinilai selalu tanggapan yang
memang tercatat — bukan baris yang ditanam uji.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import MASA_SESI, NAMA_KUKI, PenentuSesi
from src.api.penilaian import (
    PESAN_ADUAN_TIDAK_ADA,
    PESAN_JAWABAN_TIDAK_ADA,
    PESAN_PENILAIAN_TIDAK_SAH,
    PESAN_TINDAK_LANJUT_TIDAK_SAH,
)
from src.llm.galat import kalimat_terlalu_panjang
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.pengguna import PenggunaMemori
from src.penyimpanan.penilaian import AduanMemori, PenilaianMemori
from src.penyimpanan.riwayat import RiwayatMemori
from src.penyimpanan.telemetri import TelemetriMemori
from tests.api.test_penemuan_http import T0, A, B, K
from tests.api.test_riwayat_http import JalurPencatat
from tests.konftes_asinkron import jalankan

VERSI_NASKAH = "ET02-uji"
NIK = "3201234567890001"


class Lingkungan:
    def __init__(self) -> None:
        self.akun = AkunMemori()
        for satu in (A, B, K):
            self.akun.pasang_akun(satu)
        self.riwayat = RiwayatMemori()
        self.penilaian = PenilaianMemori(self.riwayat)
        self.aduan = AduanMemori(self.penilaian)
        self.pengguna = PenggunaMemori()
        self.telemetri = TelemetriMemori()
        self.jalur = JalurPencatat()
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=lambda: T0),
                riwayat=self.riwayat,
                pengguna=self.pengguna,
                versi_naskah=VERSI_NASKAH,
                telemetri=self.telemetri,
                versi_aplikasi="uji-036",
                penilaian=self.penilaian,
                aduan=self.aduan,
                sekarang=lambda: T0,
            ),
            base_url="https://testserver",
            raise_server_exceptions=False,
        )
        self.kuki: dict[str, str] = {}
        for satu in (A, B, K):
            pengenal = secrets.token_urlsafe(32)
            jalankan(
                self.akun.buat_sesi(
                    hashlib.sha256(pengenal.encode()).digest(),
                    satu.id,
                    sekarang=T0,
                    kedaluwarsa_pada=T0 + MASA_SESI,
                )
            )
            self.kuki[satu.id] = pengenal

    def minta(self, metode: str, jalur: str, siapa: BarisAkun | None = A, **lain: Any) -> Any:
        tajuk = {"Cookie": f"{NAMA_KUKI}={self.kuki[siapa.id]}"} if siapa is not None else {}
        return self.klien.request(metode, jalur, headers=tajuk, **lain)

    def setuju(self, siapa: BarisAkun = A) -> None:
        jalankan(
            self.pengguna.catat_persetujuan(
                siapa.pseudonim, versi_naskah=VERSI_NASKAH, disetujui=True, sekarang=T0
            )
        )

    def tanya(self, siapa: BarisAkun = A, pertanyaan: str = "Bagaimana jadwal supervisi?") -> str:
        tanggapan = self.minta(
            "POST",
            "/api/v1/tanya",
            siapa=siapa,
            json={"pertanyaan": pertanyaan, "id_percakapan": str(uuid.uuid4())},
        )
        assert tanggapan.status_code == 200, tanggapan.text
        return str(tanggapan.json()["id_pesan"])

    def nilai(self, id_pesan: str, siapa: BarisAkun = A, **badan: Any) -> Any:
        return self.minta("POST", f"/api/v1/pesan/{id_pesan}/penilaian", siapa=siapa, json=badan)

    def aduan_terbuka(self) -> Any:
        tanggapan = self.minta("GET", "/api/v1/kurasi/aduan", siapa=K)
        assert tanggapan.status_code == 200, tanggapan.text
        return tanggapan.json()

    def tindak(self, nomor: object, **badan: Any) -> Any:
        isi = {
            "tindak_lanjut": "jawaban_sesuai_dasar",
            "catatan": "Sudah sesuai dasarnya.",
            **badan,
        }
        return self.minta("POST", f"/api/v1/kurasi/aduan/{nomor}/tindak-lanjut", siapa=K, json=isi)

    def answer_rated(self, siapa: BarisAkun = A) -> list[Any]:
        return [
            p for p in jalankan(self.telemetri.milik(siapa.pseudonim)) if p.jenis == "answer_rated"
        ]


def _galat(tanggapan: Any) -> tuple[int, str, str]:
    g = tanggapan.json()["galat"]
    return tanggapan.status_code, g["kode"], g["pesan_pengguna"]


# ── penilaian ────────────────────────────────────────────────────────


def test_penilaian_berbentuk_d14() -> None:
    ling = Lingkungan()
    id_pesan = ling.tanya()
    tanggapan = ling.nilai(id_pesan, nilai="membantu")
    assert tanggapan.status_code == 200
    assert tanggapan.json() == {
        "id_pesan": id_pesan,
        "nilai": "membantu",
        "kirim_ke_kurator": False,
    }


def test_pesan_milik_orang_lain_sama_dengan_tidak_dikenal() -> None:
    """R-01, M-4: pemilik pesan tidak diperiksa."""
    ling = Lingkungan()
    id_pesan = ling.tanya(A)
    orang_lain = ling.nilai(id_pesan, siapa=B, nilai="keliru", kirim_ke_kurator=True)
    tak_dikenal = ling.nilai("msg_tidak_ada", siapa=B, nilai="keliru")
    assert _galat(orang_lain) == _galat(tak_dikenal)
    assert _galat(orang_lain) == (404, "SUMBER_TIDAK_ADA", PESAN_JAWABAN_TIDAK_ADA)
    assert ling.aduan_terbuka() == {"aduan": []}


@pytest.mark.parametrize(
    "badan",
    [
        {"nilai": "membantu", "kirim_ke_kurator": True},
        {"nilai": "bagus"},
        {},
        {"nilai": "keliru", "kirim_ke_kurator": "true"},
        {"nilai": "keliru", "pemilik": "psd_xxxxxxxxxxxxxxxx"},
        {"nilai": "keliru", "alasan": 12},
    ],
)
def test_badan_salah_bentuk_ditolak(badan: dict[str, Any]) -> None:
    ling = Lingkungan()
    id_pesan = ling.tanya()
    assert _galat(ling.nilai(id_pesan, **badan)) == (
        400,
        "VALIDASI_GAGAL",
        PESAN_PENILAIAN_TIDAK_SAH,
    )
    assert ling.aduan_terbuka() == {"aduan": []}


def test_bukan_json_ditolak() -> None:
    ling = Lingkungan()
    id_pesan = ling.tanya()
    tajuk = {"Cookie": f"{NAMA_KUKI}={ling.kuki[A.id]}", "Content-Type": "text/plain"}
    tanggapan = ling.klien.post(
        f"/api/v1/pesan/{id_pesan}/penilaian", headers=tajuk, content='{"nilai": "membantu"}'
    )
    assert _galat(tanggapan)[:2] == (400, "VALIDASI_GAGAL")


def test_alasan_berdata_pribadi_ditolak_tanpa_sampai_ke_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """R-03, M-8: alasan tidak diperiksa pendeteksi FR-B04."""
    ling = Lingkungan()
    ling.setuju()
    id_pesan = ling.tanya()
    with caplog.at_level(logging.DEBUG):
        tanggapan = ling.nilai(
            id_pesan, nilai="keliru", alasan=f"Hubungi NIK {NIK}", kirim_ke_kurator=True
        )
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_PENILAIAN_TIDAK_SAH)
    assert NIK not in caplog.text
    assert ling.aduan_terbuka() == {"aduan": []}
    assert ling.answer_rated() == []


def test_alasan_kosong_disimpan_sebagai_ketiadaan() -> None:
    ling = Lingkungan()
    id_pesan = ling.tanya()
    assert (
        ling.nilai(id_pesan, nilai="keliru", alasan="   ", kirim_ke_kurator=True).status_code == 200
    )
    (aduan,) = ling.aduan_terbuka()["aduan"]
    assert aduan["alasan"] is None


def test_penilaian_tidak_menyentuh_jalur_penjawab() -> None:
    """R-04, C-14: penilaian tidak memanggil jalur maupun mengubah apa yang ia terima."""
    ling = Lingkungan()
    id_pesan = ling.tanya()
    ling.nilai(id_pesan, nilai="keliru", alasan="Pasalnya diubah.", kirim_ke_kurator=True)
    ling.tanya(pertanyaan="Pertanyaan berikutnya?")
    assert ling.jalur.panggilan == [
        ("Bagaimana jadwal supervisi?", {}),
        ("Pertanyaan berikutnya?", {}),
    ]


# ── aduan ────────────────────────────────────────────────────────────


def test_aduan_hanya_bila_dikirim_dan_tanpa_penaut_ke_peserta() -> None:
    """P-2 B, R-06."""
    ling = Lingkungan()
    tanpa = ling.tanya(pertanyaan="Pertanyaan tanpa centang?")
    ling.nilai(tanpa, nilai="keliru", alasan="Tidak cocok.")
    assert ling.aduan_terbuka() == {"aduan": []}

    dengan = ling.tanya(pertanyaan="Pertanyaan dengan centang?")
    ling.nilai(dengan, nilai="keliru", alasan="Pasalnya sudah diubah.", kirim_ke_kurator=True)
    isi = ling.aduan_terbuka()
    (aduan,) = isi["aduan"]
    assert set(aduan) == {"nomor", "diadukan_pada", "pertanyaan", "alasan", "tanggapan"}
    assert aduan["pertanyaan"] == "Pertanyaan dengan centang?"
    assert aduan["alasan"] == "Pasalnya sudah diubah."
    assert aduan["diadukan_pada"] == "2026-10-05T01:00:00Z"
    assert aduan["tanggapan"]["status_dasar"] == "kuat"
    assert "id_pesan" not in aduan["tanggapan"]
    teks = json.dumps(isi)
    for penaut in (A.pseudonim, A.id, dengan):
        assert penaut not in teks


def test_tindak_lanjut_sekali_dan_aduan_keluar_dari_antrean() -> None:
    """M-12."""
    ling = Lingkungan()
    id_pesan = ling.tanya()
    ling.nilai(id_pesan, nilai="keliru", kirim_ke_kurator=True)
    (aduan,) = ling.aduan_terbuka()["aduan"]
    pertama = ling.tindak(aduan["nomor"])
    assert pertama.status_code == 200
    assert pertama.json() == {"aduan": []}
    assert _galat(ling.tindak(aduan["nomor"])) == (404, "SUMBER_TIDAK_ADA", PESAN_ADUAN_TIDAK_ADA)
    for nomor in ("abc", "999"):
        assert _galat(ling.tindak(nomor))[:2] == (404, "SUMBER_TIDAK_ADA")


@pytest.mark.parametrize(
    "badan",
    [
        {"tindak_lanjut": "lainnya"},
        {"catatan": "   "},
        {"catatan": f"Telepon NIK {NIK}"},
        {"pseudonim_kurator": "psd_xxxxxxxxxxxxxxxx"},
    ],
)
def test_tindak_lanjut_salah_bentuk_ditolak(badan: dict[str, Any]) -> None:
    ling = Lingkungan()
    id_pesan = ling.tanya()
    ling.nilai(id_pesan, nilai="keliru", kirim_ke_kurator=True)
    (aduan,) = ling.aduan_terbuka()["aduan"]
    assert _galat(ling.tindak(aduan["nomor"], **badan)) == (
        400,
        "VALIDASI_GAGAL",
        PESAN_TINDAK_LANJUT_TIDAK_SAH,
    )
    assert len(ling.aduan_terbuka()["aduan"]) == 1


def test_badan_json_rusak_ditolak() -> None:
    ling = Lingkungan()
    id_pesan = ling.tanya()
    ling.nilai(id_pesan, nilai="keliru", kirim_ke_kurator=True)
    (aduan,) = ling.aduan_terbuka()["aduan"]
    for jalur, siapa, pesan in (
        (f"/api/v1/pesan/{id_pesan}/penilaian", A, PESAN_PENILAIAN_TIDAK_SAH),
        (f"/api/v1/kurasi/aduan/{aduan['nomor']}/tindak-lanjut", K, PESAN_TINDAK_LANJUT_TIDAK_SAH),
    ):
        tajuk = {"Cookie": f"{NAMA_KUKI}={ling.kuki[siapa.id]}", "Content-Type": "application/json"}
        tanggapan = ling.klien.post(jalur, headers=tajuk, content="{rusak")
        assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", pesan)


def test_tanpa_telemetri_penilaian_tetap_tersimpan() -> None:
    """Rute penilaian tidak menuntut perekam — sama dengan rute lain sebelum fitur 034."""
    akun, riwayat = AkunMemori(), RiwayatMemori()
    akun.pasang_akun(A)
    penilaian = PenilaianMemori(riwayat)
    pengenal = secrets.token_urlsafe(32)
    jalankan(
        akun.buat_sesi(
            hashlib.sha256(pengenal.encode()).digest(),
            A.id,
            sekarang=T0,
            kedaluwarsa_pada=T0 + MASA_SESI,
        )
    )
    klien = TestClient(
        susun_aplikasi(
            jalur=JalurPencatat(),
            identitas=PenentuSesi(akun, sekarang=lambda: T0),
            riwayat=riwayat,
            penilaian=penilaian,
            sekarang=lambda: T0,
        ),
        base_url="https://testserver",
    )
    tajuk = {"Cookie": f"{NAMA_KUKI}={pengenal}"}
    id_pesan = klien.post(
        "/api/v1/tanya",
        headers=tajuk,
        json={"pertanyaan": "Bagaimana?", "id_percakapan": str(uuid.uuid4())},
    ).json()["id_pesan"]
    tanggapan = klien.post(
        f"/api/v1/pesan/{id_pesan}/penilaian",
        headers=tajuk,
        json={"nilai": "keliru", "kirim_ke_kurator": True},
    )
    assert tanggapan.status_code == 200
    assert len(penilaian.baris_aduan()) == 1


# ── peran ────────────────────────────────────────────────────────────


def test_peran_dijaga_pada_ketiga_rute() -> None:
    ling = Lingkungan()
    id_pesan = ling.tanya()
    assert ling.nilai(id_pesan, siapa=K, nilai="membantu").status_code == 403
    assert ling.minta("GET", "/api/v1/kurasi/aduan", siapa=A).status_code == 403
    assert (
        ling.minta("POST", "/api/v1/kurasi/aduan/1/tindak-lanjut", siapa=A, json={}).status_code
        == 403
    )
    assert ling.nilai(id_pesan, siapa=None, nilai="membantu").status_code == 401


# ── answer_rated ─────────────────────────────────────────────────────


def test_answer_rated_tiga_properti_tanpa_teks_alasan() -> None:
    """R-09, P-4 B, KB-228; M-9: teks alasan ikut sebagai properti."""
    ling = Lingkungan()
    ling.setuju()
    id_pesan = ling.tanya()
    ling.nilai(id_pesan, nilai="keliru", alasan="Pasalnya sudah diubah.", kirim_ke_kurator=True)
    ling.nilai(id_pesan, nilai="membantu")
    pertama, kedua = ling.answer_rated()
    assert pertama.properti == {"nilai": "keliru", "beralasan": True, "id_pesan": id_pesan}
    assert kedua.properti == {"nilai": "membantu", "beralasan": False, "id_pesan": id_pesan}
    assert pertama.versi_model == "uji-1"
    assert "Pasalnya" not in json.dumps(pertama.properti)


def test_tanpa_persetujuan_aduan_tetap_sampai_tetapi_tidak_direkam() -> None:
    """R-09: persetujuan penelitian mengatur perekaman, bukan layanan."""
    ling = Lingkungan()
    id_pesan = ling.tanya()
    assert ling.nilai(id_pesan, nilai="keliru", kirim_ke_kurator=True).status_code == 200
    assert len(ling.aduan_terbuka()["aduan"]) == 1
    assert ling.answer_rated() == []


def test_pesan_memenuhi_c13() -> None:
    for pesan in (
        PESAN_PENILAIAN_TIDAK_SAH,
        PESAN_JAWABAN_TIDAK_ADA,
        PESAN_TINDAK_LANJUT_TIDAK_SAH,
        PESAN_ADUAN_TIDAK_ADA,
    ):
        assert not kalimat_terlalu_panjang(pesan)
