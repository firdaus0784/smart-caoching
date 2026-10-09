"""Rute koleksi — T-5 fitur 032, R-01, R-02, R-03; K-4, K-5; P-1 A, P-4 A;
D-14 Bagian 4.10.

Butir disetujui lewat rute kurator dan tampil lewat beranda sungguhan, sehingga
"pernah tayang bagi pemanggil" adalah keadaan yang memang terjadi, bukan baris
yang ditanam uji.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import MASA_SESI, NAMA_KUKI, PenentuSesi
from src.api.koleksi import (
    PESAN_CATATAN_TIDAK_SAH,
    PESAN_KOLEKSI_TIDAK_ADA,
    PESAN_PENYARING_TIDAK_SAH,
)
from src.api.kurasi import PESAN_BUTIR_TIDAK_ADA
from src.ingest.kurasi.butir import ButirPengetahuan
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.koleksi import KoleksiMemori
from src.penyimpanan.kurasi import BarisKandidat, KurasiMemori
from src.penyimpanan.penemuan import PenemuanMemori
from src.penyimpanan.pengguna import PenggunaMemori
from src.penyimpanan.riwayat import RiwayatMemori
from src.penyimpanan.telemetri import TelemetriMemori
from tests.api.test_kurasi_http import SUMBER, butir
from tests.api.test_penemuan_http import A, B, K, KurasiRusak
from tests.api.test_saya_http import JalurPencatat
from tests.konftes_asinkron import jalankan

T0 = datetime(2026, 10, 9, 1, 0, tzinfo=UTC)
VERSI_NASKAH = "ET02-uji"
NIK = "3201234567890001"


class Lingkungan:
    def __init__(self, kurasi: KurasiMemori | None = None) -> None:
        self.kini = T0
        self.akun = AkunMemori()
        for satu in (K, A, B):
            self.akun.pasang_akun(satu)
        self.kurasi = KurasiMemori() if kurasi is None else kurasi
        self.pengguna = PenggunaMemori()
        self.penemuan = PenemuanMemori(self.kurasi)
        self.koleksi = KoleksiMemori()
        self.telemetri = TelemetriMemori()
        self.jalur = JalurPencatat()
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=lambda: self.kini),
                riwayat=RiwayatMemori(),
                pengguna=self.pengguna,
                versi_naskah=VERSI_NASKAH,
                kurasi=self.kurasi,
                penemuan=self.penemuan,
                koleksi=self.koleksi,
                telemetri=self.telemetri,
                versi_aplikasi="uji-032",
                sekarang=lambda: self.kini,
            ),
            base_url="https://testserver",
            raise_server_exceptions=False,
        )
        self.kuki: dict[str, str] = {}
        for satu in (K, A, B):
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
        for satu in (A, B):
            jalankan(
                self.pengguna.tetapkan_prioritas(satu.pseudonim, ("K1", "K2", "K3"), sekarang=T0)
            )
        jalankan(
            self.pengguna.catat_persetujuan(
                A.pseudonim, versi_naskah=VERSI_NASKAH, disetujui=True, sekarang=T0
            )
        )

    def minta(self, metode: str, jalur: str, siapa: BarisAkun | None = A, **lain: Any) -> Any:
        tajuk = {"Cookie": f"{NAMA_KUKI}={self.kuki[siapa.id]}"} if siapa is not None else {}
        return self.klien.request(metode, jalur, headers=tajuk, **lain)

    def tayangkan(self, *daftar: ButirPengetahuan, siapa: BarisAkun = A) -> None:
        """Lewat kurator dan beranda sungguhan."""
        for b in daftar:
            jalankan(
                self.kurasi.tambah_kandidat(
                    BarisKandidat(
                        id_butir=b.id_butir,
                        butir=b.model_dump(mode="json"),
                        sumber=SUMBER,
                        id_dokumen_sumber=b.id_dokumen_sumber,
                        kategori=b.kategori.value,
                        status_keberlakuan=None
                        if b.status_keberlakuan is None
                        else b.status_keberlakuan.value,
                        masuk_pada=self.kini,
                    )
                )
            )
            hasil = self.minta(
                "POST",
                f"/api/v1/kurasi/{b.id_butir}/putusan",
                siapa=K,
                json={"jenis": "setujui", "catatan": "Layak tayang"},
            )
            assert hasil.status_code == 200, hasil.text
        assert self.minta("GET", "/api/v1/beranda", siapa=siapa).status_code == 200

    def simpan(self, id_butir: str, siapa: BarisAkun = A, **badan: Any) -> Any:
        return self.minta("POST", f"/api/v1/butir/{id_butir}/simpan", siapa=siapa, json=badan)

    def daftar(self, siapa: BarisAkun = A, **penyaring: str) -> Any:
        return self.minta("GET", "/api/v1/koleksi", siapa=siapa, params=penyaring)

    def tersimpan(self) -> list[Any]:
        return [
            p for p in jalankan(self.telemetri.milik(A.pseudonim)) if p.jenis == "discovery_saved"
        ]


def _galat(tanggapan: Any) -> tuple[int, str, str]:
    g = tanggapan.json()["galat"]
    return tanggapan.status_code, g["kode"], g["pesan_pengguna"]


def test_simpan_berbentuk_butir_lengkap_ditambah_koleksi() -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    tanggapan = ling.simpan("b-1", catatan="Bahas di rapat guru")
    assert tanggapan.status_code == 200, tanggapan.text
    isi = tanggapan.json()
    detail = ling.minta("GET", "/api/v1/butir/b-1").json()
    assert isi == {
        **detail,
        "catatan": "Bahas di rapat guru",
        "disimpan_pada": "2026-10-09T01:00:00Z",
        "dasar_berubah": False,
    }


@pytest.mark.parametrize("badan", [{}, {"catatan": ""}, {"catatan": "   "}, {"catatan": None}])
def test_catatan_boleh_kosong(badan: dict[str, Any]) -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    tanggapan = ling.simpan("b-1", **badan)
    assert tanggapan.status_code == 200, tanggapan.text
    assert tanggapan.json()["catatan"] is None


def test_hanya_butir_yang_pernah_tayang_bagi_pemanggil() -> None:
    """R-01; M-10. Bentuk 404 sama dengan detail butir D-14 Bagian 4.6."""
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"), siapa=B)
    bentuk_detail = _galat(ling.minta("GET", "/api/v1/butir/b-1"))
    assert bentuk_detail == (404, "SUMBER_TIDAK_ADA", PESAN_BUTIR_TIDAK_ADA)
    for id_butir in ("b-1", "b-tidak-ada"):
        assert _galat(ling.simpan(id_butir)) == bentuk_detail
    assert ling.daftar().json() == {"koleksi": []}
    assert ling.tersimpan() == []


def test_catatan_berdata_pribadi_ditolak_tanpa_dikutip(caplog: pytest.LogCaptureFixture) -> None:
    """R-02, KM-03; M-11."""
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    with caplog.at_level(logging.DEBUG):
        tanggapan = ling.simpan("b-1", catatan=f"Telepon wali murid {NIK}")
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_CATATAN_TIDAK_SAH)
    assert NIK not in tanggapan.text and NIK not in caplog.text
    assert ling.daftar().json() == {"koleksi": []}
    assert ling.tersimpan() == []


@pytest.mark.parametrize(
    "kirim",
    [
        {"json": {"catatan": "x", "pemilik": "psd_bbbbbbbbbbbbbbbb"}},
        {"json": {"catatan": 5}},
        {"content": b"catatan=x", "headers": {"Content-Type": "text/plain"}},
    ],
)
def test_badan_yang_tidak_sah_ditolak(kirim: dict[str, Any]) -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    tajuk = {"Cookie": f"{NAMA_KUKI}={ling.kuki[A.id]}", **kirim.pop("headers", {})}
    tanggapan = ling.klien.post("/api/v1/butir/b-1/simpan", headers=tajuk, **kirim)
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_CATATAN_TIDAK_SAH)


def test_simpan_ulang_mengganti_catatan() -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    ling.simpan("b-1", catatan="Pertama")
    ling.simpan("b-1", catatan="Kedua")
    koleksi = ling.daftar().json()["koleksi"]
    assert [(b["id_butir"], b["catatan"]) for b in koleksi] == [("b-1", "Kedua")]


def test_daftar_terbaru_lebih_dulu_dan_tersaring() -> None:
    """FR-G06, FR-G10."""
    ling = Lingkungan()
    ling.tayangkan(
        butir("b-1", kategori="K1"),
        butir("b-2", kategori="K2", jenis="regulasi", status="berlaku"),
        butir("b-3", kategori="K1", jenis="praktik_baik"),
    )
    for menit, id_butir in ((1, "b-1"), (2, "b-2"), (3, "b-3")):
        ling.kini = T0.replace(minute=menit)
        assert ling.simpan(id_butir).status_code == 200
    semua = [b["id_butir"] for b in ling.daftar().json()["koleksi"]]
    assert semua == ["b-3", "b-2", "b-1"]
    assert [b["id_butir"] for b in ling.daftar(kategori="K1").json()["koleksi"]] == ["b-3", "b-1"]
    assert [b["id_butir"] for b in ling.daftar(jenis_sumber="regulasi").json()["koleksi"]] == [
        "b-2"
    ]
    keduanya = ling.daftar(kategori="K1", jenis_sumber="praktik_baik").json()["koleksi"]
    assert [b["id_butir"] for b in keduanya] == ["b-3"]


@pytest.mark.parametrize("penyaring", [{"kategori": "K9"}, {"jenis_sumber": "buku"}])
def test_penyaring_di_luar_daftar_ditolak(penyaring: dict[str, str]) -> None:
    ling = Lingkungan()
    assert _galat(ling.daftar(**penyaring)) == (400, "VALIDASI_GAGAL", PESAN_PENYARING_TIDAK_SAH)


def test_butir_ditarik_tetap_terbaca_berpenanda() -> None:
    """P-4 A, D-06 Bagian 7.5; M-14."""
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"), butir("b-2"))
    ling.simpan("b-1", catatan="Untuk rapat")
    ling.simpan("b-2")
    hasil = ling.minta(
        "POST",
        "/api/v1/kurasi/b-1/tarik",
        siapa=K,
        json={"pemicu": "kekeliruan_isi_dilaporkan", "catatan": "Angka keliru"},
    )
    assert hasil.status_code == 200, hasil.text
    koleksi = {b["id_butir"]: b for b in ling.daftar().json()["koleksi"]}
    assert set(koleksi) == {"b-1", "b-2"}
    ditarik = koleksi["b-1"]
    assert ditarik["dasar_berubah"] is True and koleksi["b-2"]["dasar_berubah"] is False
    assert ditarik["catatan"] == "Untuk rapat"
    assert ditarik["inti_temuan"] == butir("b-1").inti_temuan, "isi tetap terbaca"
    # Butir yang ditarik tidak dapat disimpan ulang, tetapi dapat dikeluarkan.
    assert _galat(ling.simpan("b-1"))[0] == 404
    assert ling.minta("DELETE", "/api/v1/butir/b-1/simpan").status_code == 204


def test_regulasi_dicabut_berpenanda_meski_belum_ditarik() -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1", jenis="regulasi", status="berlaku", dokumen="permen-1"))
    ling.simpan("b-1")
    jalankan(ling.kurasi.perbarui_status("permen-1", "dicabut"))
    (satu,) = ling.daftar().json()["koleksi"]
    assert satu["dasar_berubah"] is True


def test_keluarkan_sekali_lalu_404() -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    ling.simpan("b-1")
    pertama = ling.minta("DELETE", "/api/v1/butir/b-1/simpan")
    assert (pertama.status_code, pertama.content) == (204, b"")
    assert _galat(ling.minta("DELETE", "/api/v1/butir/b-1/simpan")) == (
        404,
        "SUMBER_TIDAK_ADA",
        PESAN_KOLEKSI_TIDAK_ADA,
    )
    assert ling.daftar().json() == {"koleksi": []}


def test_koleksi_milik_pemanggil_saja() -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    assert ling.minta("GET", "/api/v1/beranda", siapa=B).status_code == 200
    ling.simpan("b-1", catatan="Milik A")
    assert ling.daftar(siapa=B).json() == {"koleksi": []}
    assert _galat(ling.minta("DELETE", "/api/v1/butir/b-1/simpan", siapa=B))[0] == 404
    assert len(ling.daftar().json()["koleksi"]) == 1


def test_menyimpan_tidak_mengubah_beranda() -> None:
    """R-03, C-14: koleksi bukan sinyal pemilihan."""
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"), butir("b-2"))
    sebelum = ling.minta("GET", "/api/v1/beranda").json()
    ling.simpan("b-2", catatan="Penting")
    assert ling.minta("GET", "/api/v1/beranda").json() == sebelum


def test_discovery_saved_hanya_ada_catatan() -> None:
    """P-3 A; M-12: teks catatan tidak ikut."""
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"), butir("b-2"))
    ling.simpan("b-1", catatan="Rahasia rapat")
    ling.simpan("b-2")
    pertama, kedua = ling.tersimpan()
    assert (pertama.properti, kedua.properti) == ({"ada_catatan": True}, {"ada_catatan": False})
    assert "Rahasia" not in json.dumps(pertama.properti)
    assert pertama.versi_model == "tanpa_model"


def test_tanpa_persetujuan_tidak_direkam() -> None:
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"), siapa=B)
    assert ling.simpan("b-1", siapa=B).status_code == 200
    assert jalankan(ling.telemetri.milik(B.pseudonim)) == ()


def test_hanya_bagi_pengguna_bersesi() -> None:
    ling = Lingkungan()
    for metode, jalur in (
        ("POST", "/api/v1/butir/b-1/simpan"),
        ("DELETE", "/api/v1/butir/b-1/simpan"),
        ("GET", "/api/v1/koleksi"),
    ):
        assert ling.minta(metode, jalur, siapa=None).status_code == 401
        assert ling.minta(metode, jalur, siapa=K).status_code == 403


def test_butir_yang_tidak_terbaca_dilewati(caplog: pytest.LogCaptureFixture) -> None:
    """Pola TK-78: satu baris rusak tidak menjatuhkan koleksi."""
    kurasi = KurasiRusak()
    ling = Lingkungan(kurasi)
    ling.tayangkan(butir("b-1"), butir("b-2"))
    ling.simpan("b-1")
    ling.simpan("b-2")
    kurasi.rusak.add("b-1")
    with caplog.at_level(logging.WARNING):
        koleksi = ling.daftar().json()["koleksi"]
    assert [b["id_butir"] for b in koleksi] == ["b-2"]
    assert "b-1" in caplog.text and "Supervisi" not in caplog.text


def test_baris_tanpa_butir_tayang_dilewati(caplog: pytest.LogCaptureFixture) -> None:
    """Butir tayang tidak pernah dihapus (D-14 Bagian 5.1); baris koleksi yang
    tetap tidak menemukannya — ditulis di luar rute — dilewati, tidak
    menjatuhkan daftar."""
    ling = Lingkungan()
    ling.tayangkan(butir("b-1"))
    ling.simpan("b-1")
    jalankan(ling.koleksi.simpan(A.pseudonim, "b-hilang", None, sekarang=T0))
    with caplog.at_level(logging.WARNING):
        koleksi = ling.daftar().json()["koleksi"]
    assert [b["id_butir"] for b in koleksi] == ["b-1"]
    assert "b-hilang" in caplog.text


def test_koleksi_menuntut_penyimpan_penemuan() -> None:
    with pytest.raises(ValueError, match="penemuan"):
        susun_aplikasi(
            jalur=JalurPencatat(),
            identitas=PenentuSesi(AkunMemori(), sekarang=lambda: T0),
            riwayat=RiwayatMemori(),
            koleksi=KoleksiMemori(),
        )


def test_tanpa_penyimpan_telemetri_tetap_tersimpan() -> None:
    """Sebelum fitur 034 terpasang di sebuah titik jalan: rute berjalan dan
    tidak satu peristiwa pun tersimpan."""
    ling = Lingkungan()
    klien = TestClient(
        susun_aplikasi(
            jalur=ling.jalur,
            identitas=PenentuSesi(ling.akun, sekarang=lambda: T0),
            riwayat=RiwayatMemori(),
            pengguna=ling.pengguna,
            kurasi=ling.kurasi,
            penemuan=ling.penemuan,
            koleksi=ling.koleksi,
            sekarang=lambda: T0,
        ),
        base_url="https://testserver",
    )
    ling.tayangkan(butir("b-1"))
    tanggapan = klien.post(
        "/api/v1/butir/b-1/simpan",
        headers={"Cookie": f"{NAMA_KUKI}={ling.kuki[A.id]}"},
        json={"catatan": "Tanpa telemetri"},
    )
    assert tanggapan.status_code == 200, tanggapan.text
    assert ling.tersimpan() == []
