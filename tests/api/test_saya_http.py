"""Rute `/saya/*` — T-4 fitur 030, R-01 s.d. R-05, R-08, R-10; K-4, K-5.

Bentuknya D-14 Bagian 4.5: keempat rute mengembalikan satu ringkasan aktivasi.
Identitas dari `PenentuSesi` sungguhan atas `AkunMemori`, sehingga pemilik yang
diuji benar-benar pseudonim dari sesi — bukan identitas tetap.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import MASA_SESI, NAMA_KUKI, PenentuSesi
from src.api.saya import (
    PESAN_PERSETUJUAN_TIDAK_SAH,
    PESAN_PRIORITAS_TIDAK_SAH,
    PESAN_PROFIL_TIDAK_SAH,
    baca_naskah,
)
from src.api.tanya import HasilTanya
from src.llm.galat import kalimat_terlalu_panjang
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.pengguna import PenggunaMemori
from src.penyimpanan.riwayat import RiwayatMemori
from tests.api.test_aplikasi import ID_PERCAKAPAN, _tanggapan
from tests.konftes_asinkron import jalankan

T0 = datetime(2026, 10, 4, 7, 0, tzinfo=UTC)
VERSI = "et02-uji-1"

PROFIL = {
    "jabatan": "Kepala Sekolah",
    "masa_kerja": 3,
    "jumlah_rombel": 6,
    "jumlah_ptk": 9,
    "jalur_akreditasi": "visitasi",
    "wilayah": "Kabupaten Sumedang",
}


class JalurPencatat:
    """Mencatat argumen `jawab` — C-14 menuntut pertanyaan saja."""

    def __init__(self) -> None:
        self.panggilan: list[tuple[str, dict[str, Any]]] = []

    async def jawab(self, pertanyaan: str, **argumen: Any) -> HasilTanya:
        self.panggilan.append((pertanyaan, argumen))
        return HasilTanya(tanggapan=_tanggapan())


def _akun(id_akun: str, pseudonim: str) -> BarisAkun:
    return BarisAkun(
        id=id_akun,
        pseudonim=pseudonim,
        peran="pengguna",
        status_aktif=True,
        turunan_sandi="scrypt$16$8$1$AAAA$AAAA",
        gagal_beruntun=0,
        ditahan_sampai=None,
    )


A = _akun("ks-017", "psd_aaaaaaaaaaaaaaaa")
B = _akun("ks-018", "psd_bbbbbbbbbbbbbbbb")


class Jam:
    """Jam yang dapat dimajukan uji — pencabutan wajib sesudah persetujuannya."""

    def __init__(self) -> None:
        self.kini = T0

    def __call__(self) -> datetime:
        return self.kini


class Lingkungan:
    def __init__(self, versi_naskah: str | None = VERSI) -> None:
        self.jam = Jam()
        self.akun = AkunMemori()
        for satu in (A, B):
            self.akun.pasang_akun(satu)
        self.pengguna = PenggunaMemori()
        self.jalur = JalurPencatat()
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=self.jam),
                riwayat=RiwayatMemori(),
                pengguna=self.pengguna,
                versi_naskah=versi_naskah,
                sekarang=self.jam,
            ),
            base_url="https://testserver",
        )
        self.kuki = {akun.id: self._sesi(akun) for akun in (A, B)}

    def _sesi(self, akun: BarisAkun) -> str:
        pengenal = secrets.token_urlsafe(32)
        jalankan(
            self.akun.buat_sesi(
                hashlib.sha256(pengenal.encode()).digest(),
                akun.id,
                sekarang=T0,
                kedaluwarsa_pada=T0 + MASA_SESI,
            )
        )
        return pengenal

    def minta(self, metode: str, jalur: str, siapa: BarisAkun | None = A, **lain: Any) -> Any:
        tajuk = {"Cookie": f"{NAMA_KUKI}={self.kuki[siapa.id]}"} if siapa is not None else {}
        return self.klien.request(metode, jalur, headers=tajuk, **lain)


def _galat(tanggapan: Any) -> tuple[int, str, str]:
    g = tanggapan.json()["galat"]
    return tanggapan.status_code, g["kode"], g["pesan_pengguna"]


# ── ringkasan aktivasi ──────────────────────────────────────────────


def test_ringkasan_awal_kosong() -> None:
    tanggapan = Lingkungan().minta("GET", "/api/v1/saya/profil")
    assert tanggapan.status_code == 200
    assert tanggapan.json() == {"profil": None, "prioritas": [], "persetujuan": "belum_diminta"}


def test_keempat_rute_mengembalikan_bentuk_yang_sama() -> None:
    ling = Lingkungan()
    jawaban = [
        ling.minta("PUT", "/api/v1/saya/profil", json=PROFIL),
        ling.minta("PUT", "/api/v1/saya/prioritas", json={"kategori": ["K5", "K1", "K7"]}),
        ling.minta(
            "POST", "/api/v1/saya/persetujuan", json={"versi_naskah": VERSI, "disetujui": True}
        ),
        ling.minta("GET", "/api/v1/saya/profil"),
    ]
    assert [j.status_code for j in jawaban] == [200] * 4
    akhir = jawaban[-1].json()
    assert akhir == {"profil": PROFIL, "prioritas": ["K5", "K1", "K7"], "persetujuan": "diberikan"}
    assert jawaban[2].json() == akhir


# ── R-02 · pemilik dari sesi ────────────────────────────────────────


def test_pemilik_adalah_pseudonim_sesi() -> None:
    ling = Lingkungan()
    ling.minta("PUT", "/api/v1/saya/profil", json=PROFIL)
    assert jalankan(ling.pengguna.baca_profil(A.pseudonim)) is not None
    assert jalankan(ling.pengguna.baca_profil(A.id)) is None


def test_b_tidak_membaca_maupun_menulis_milik_a() -> None:
    """M-1."""
    ling = Lingkungan()
    ling.minta("PUT", "/api/v1/saya/profil", json=PROFIL)
    assert ling.minta("GET", "/api/v1/saya/profil", siapa=B).json()["profil"] is None
    ling.minta("PUT", "/api/v1/saya/profil", siapa=B, json={**PROFIL, "wilayah": "Kota Bandung"})
    assert (
        ling.minta("GET", "/api/v1/saya/profil").json()["profil"]["wilayah"] == "Kabupaten Sumedang"
    )


@pytest.mark.parametrize("bidang", ["id_pengguna", "tanggal_perbarui", "pemilik"])
def test_badan_tidak_dapat_menyebut_pemilik_maupun_waktu(bidang: str) -> None:
    ling = Lingkungan()
    tanggapan = ling.minta("PUT", "/api/v1/saya/profil", json={**PROFIL, bidang: B.pseudonim})
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_PROFIL_TIDAK_SAH)


def test_tanpa_sesi_401_dan_peran_lain_403() -> None:
    ling = Lingkungan()
    assert ling.minta("GET", "/api/v1/saya/profil", siapa=None).status_code == 401
    from dataclasses import replace

    ling.akun.pasang_akun(replace(A, peran="kurator"))
    assert _galat(ling.minta("GET", "/api/v1/saya/profil"))[:2] == (403, "TIDAK_BERWENANG")


# ── R-05 · profil dan prioritas ─────────────────────────────────────


@pytest.mark.parametrize(
    "badan",
    [
        {**PROFIL, "jenjang": "SD"},
        {k: v for k, v in PROFIL.items() if k != "wilayah"},
        {**PROFIL, "jalur_akreditasi": "A"},
        {**PROFIL, "jumlah_rombel": 0},
        {**PROFIL, "wilayah": "Hubungi 081234567890"},
        {**PROFIL, "jabatan": "  "},
    ],
)
def test_profil_tidak_sah_ditolak_tanpa_menyimpan(badan: dict[str, Any]) -> None:
    ling = Lingkungan()
    tanggapan = ling.minta("PUT", "/api/v1/saya/profil", json=badan)
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_PROFIL_TIDAK_SAH)
    assert "081234567890" not in tanggapan.text
    assert jalankan(ling.pengguna.baca_profil(A.pseudonim)) is None


def test_profil_diperbarui_kapan_saja() -> None:
    """FR-A06."""
    ling = Lingkungan()
    ling.minta("PUT", "/api/v1/saya/profil", json=PROFIL)
    kedua = ling.minta("PUT", "/api/v1/saya/profil", json={**PROFIL, "masa_kerja": 4})
    assert kedua.json()["profil"]["masa_kerja"] == 4


@pytest.mark.parametrize(
    "kategori",
    [
        ["K1", "K2"],
        ["K1", "K2", "K3", "K4", "K5", "K6"],
        ["K1", "K1", "K2"],
        ["K1", "K2", "K9"],
        [],
    ],
)
def test_prioritas_tidak_sah_ditolak(kategori: list[str]) -> None:
    ling = Lingkungan()
    tanggapan = ling.minta("PUT", "/api/v1/saya/prioritas", json={"kategori": kategori})
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_PRIORITAS_TIDAK_SAH)


def test_prioritas_baru_menambah_bukan_menimpa() -> None:
    ling = Lingkungan()
    ling.minta("PUT", "/api/v1/saya/prioritas", json={"kategori": ["K5", "K1", "K7"]})
    ling.minta("PUT", "/api/v1/saya/prioritas", json={"kategori": ["K2", "K3", "K4"]})
    assert jalankan(ling.pengguna.riwayat_prioritas(A.pseudonim)) == (
        ("K5", "K1", "K7"),
        ("K2", "K3", "K4"),
    )


# ── R-04, K-4 · persetujuan dan naskah ──────────────────────────────


def test_versi_naskah_karangan_ditolak() -> None:
    """M-2."""
    ling = Lingkungan()
    tanggapan = ling.minta(
        "POST", "/api/v1/saya/persetujuan", json={"versi_naskah": "karangan", "disetujui": True}
    )
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_PERSETUJUAN_TIDAK_SAH)
    assert jalankan(ling.pengguna.baca_persetujuan(A.pseudonim)) is None


@pytest.mark.parametrize("disetujui", [True, False])
def test_tanpa_berkas_naskah_setiap_persetujuan_ditolak(disetujui: bool) -> None:
    """M-3 — C-04 terjaga tanpa naskah: tidak ada yang dapat disetujui."""
    ling = Lingkungan(versi_naskah=None)
    tanggapan = ling.minta(
        "POST", "/api/v1/saya/persetujuan", json={"versi_naskah": VERSI, "disetujui": disetujui}
    )
    assert _galat(tanggapan)[:2] == (400, "VALIDASI_GAGAL")
    assert ling.minta("GET", "/api/v1/saya/profil").json()["persetujuan"] == "belum_diminta"


def test_tolak_lalu_setuju_lalu_cabut() -> None:
    ling = Lingkungan()
    langkah = [
        {"versi_naskah": VERSI, "disetujui": False},
        {"versi_naskah": VERSI, "disetujui": True},
        {"cabut": True},
    ]
    keadaan = []
    for badan in langkah:
        ling.jam.kini += timedelta(minutes=1)
        jawab = ling.minta("POST", "/api/v1/saya/persetujuan", json=badan)
        keadaan.append(jawab.json()["persetujuan"])
    assert keadaan == ["ditolak", "diberikan", "dicabut"]


@pytest.mark.parametrize(
    "badan",
    [
        {"cabut": True},
        {"cabut": False},
        {"versi_naskah": VERSI},
        {"disetujui": True},
        {"versi_naskah": VERSI, "disetujui": True, "cabut": True},
    ],
)
def test_bentuk_persetujuan_tidak_sah(badan: dict[str, Any]) -> None:
    """Mencabut tanpa persetujuan yang berlaku juga ditolak."""
    ling = Lingkungan()
    assert _galat(ling.minta("POST", "/api/v1/saya/persetujuan", json=badan)) == (
        400,
        "VALIDASI_GAGAL",
        PESAN_PERSETUJUAN_TIDAK_SAH,
    )


# ── R-03, R-10 · fitur inti tetap; jawaban tidak dipengaruhi ────────


def test_menolak_persetujuan_tidak_menghalangi_tanya() -> None:
    """M-8, FR-A05."""
    ling = Lingkungan()
    ling.minta("POST", "/api/v1/saya/persetujuan", json={"versi_naskah": VERSI, "disetujui": False})
    tanggapan = ling.minta(
        "POST",
        "/api/v1/tanya",
        json={"pertanyaan": "Bagaimana supervisi?", "id_percakapan": ID_PERCAKAPAN},
    )
    assert tanggapan.status_code == 200


def test_profil_dan_prioritas_tidak_sampai_ke_jalur_penjawab() -> None:
    """M-9, C-14: penyaringan milik feed, bukan jawaban."""
    ling = Lingkungan()
    ling.minta("PUT", "/api/v1/saya/profil", json=PROFIL)
    ling.minta("PUT", "/api/v1/saya/prioritas", json={"kategori": ["K5", "K1", "K7"]})
    ling.minta(
        "POST",
        "/api/v1/tanya",
        json={"pertanyaan": "Bagaimana supervisi?", "id_percakapan": ID_PERCAKAPAN},
    )
    assert ling.jalur.panggilan == [("Bagaimana supervisi?", {})]


# ── K-4 fitur 029 · application/json ────────────────────────────────


@pytest.mark.parametrize(
    ("metode", "jalur"),
    [
        ("PUT", "/api/v1/saya/profil"),
        ("PUT", "/api/v1/saya/prioritas"),
        ("POST", "/api/v1/saya/persetujuan"),
    ],
)
def test_rute_penulis_menuntut_json(metode: str, jalur: str) -> None:
    ling = Lingkungan()
    tanggapan = ling.klien.request(
        metode,
        jalur,
        content=json.dumps(PROFIL),
        headers={"Cookie": f"{NAMA_KUKI}={ling.kuki[A.id]}", "Content-Type": "text/plain"},
    )
    assert tanggapan.status_code == 400


def test_kalimat_lolos_c13() -> None:
    for pesan in (PESAN_PROFIL_TIDAK_SAH, PESAN_PRIORITAS_TIDAK_SAH, PESAN_PERSETUJUAN_TIDAK_SAH):
        assert not kalimat_terlalu_panjang(pesan), pesan


# ── berkas naskah ───────────────────────────────────────────────────


def test_berkas_naskah_tidak_ada_berarti_none(tmp_path: Path) -> None:
    assert baca_naskah(tmp_path / "persetujuan.json") is None


def test_berkas_naskah_dibaca_versinya(tmp_path: Path) -> None:
    berkas = tmp_path / "persetujuan.json"
    berkas.write_text(
        json.dumps(
            {"versi": "et02-v1", "judul": "Lembar informasi", "paragraf": ["Satu.", "Dua."]}
        ),
        encoding="utf-8",
    )
    naskah = baca_naskah(berkas)
    assert naskah is not None and naskah.versi == "et02-v1"


@pytest.mark.parametrize(
    "isi",
    [
        "bukan json",
        json.dumps({"versi": "", "judul": "J", "paragraf": ["P"]}),
        json.dumps({"versi": "v", "judul": "J", "paragraf": []}),
        json.dumps({"versi": "v", "judul": "J", "paragraf": ["P"], "lain": 1}),
    ],
)
def test_berkas_naskah_rusak_menolak_terang(tmp_path: Path, isi: str) -> None:
    """Naskah yang rusak bukan "naskah belum ada": peladen berhenti, bukan
    diam-diam menutup persetujuan bagi semua orang."""
    berkas = tmp_path / "persetujuan.json"
    berkas.write_text(isi, encoding="utf-8")
    with pytest.raises(ValueError):
        baca_naskah(berkas)


def test_repositori_tidak_memuat_naskah_persetujuan() -> None:
    """Agen tidak menulis naskah ET-02 (KB-164). Berkasnya diisi tim."""
    akar = Path(__file__).resolve().parents[2]
    assert not (akar / "web" / "public" / "naskah" / "persetujuan.json").exists()


@pytest.mark.parametrize(
    ("metode", "jalur", "badan"),
    [
        ("PUT", "/api/v1/saya/profil", PROFIL),
        ("PUT", "/api/v1/saya/prioritas", {"kategori": ["K5", "K1", "K7"]}),
        ("POST", "/api/v1/saya/persetujuan", {"versi_naskah": VERSI, "disetujui": True}),
    ],
)
def test_rute_penulis_tanpa_sesi_401_tanpa_menyimpan(
    metode: str, jalur: str, badan: dict[str, Any]
) -> None:
    ling = Lingkungan()
    tanggapan = ling.minta(metode, jalur, siapa=None, json=badan)
    assert _galat(tanggapan)[:2] == (401, "TIDAK_TERAUTENTIKASI")
    assert ling.minta("GET", "/api/v1/saya/profil").json() == {
        "profil": None,
        "prioritas": [],
        "persetujuan": "belum_diminta",
    }


def test_badan_json_rusak_400() -> None:
    ling = Lingkungan()
    tanggapan = ling.klien.request(
        "PUT",
        "/api/v1/saya/profil",
        content=b"{",
        headers={"Cookie": f"{NAMA_KUKI}={ling.kuki[A.id]}", "Content-Type": "application/json"},
    )
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_PROFIL_TIDAK_SAH)
