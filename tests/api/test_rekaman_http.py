"""Perekaman peristiwa lewat HTTP — fitur 034, R-01 s.d. R-04, R-07, R-08; K-2, K-4, K-5.

Peristiwa dibaca dari penyimpan telemetri yang **sama** dengan yang dipakai
rute, bukan dari tiruan perekam: uji yang memeriksa bahwa perekam dipanggil
tidak memeriksa bahwa sesuatu tersimpan, dan C-04 berbicara tentang yang
tersimpan.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api import sandi
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import NAMA_KUKI, PenentuSesi, PenjagaMasuk
from src.api.galat import LOG_OPERASIONAL
from src.api.rekaman import TANPA_MODEL, Perekam
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.kurasi import KurasiMemori
from src.penyimpanan.penemuan import PenemuanMemori
from src.penyimpanan.pengguna import PenggunaMemori
from src.penyimpanan.riwayat import RiwayatMemori
from src.penyimpanan.telemetri import BarisPeristiwa, TelemetriMemori
from src.telemetri.peristiwa import JenisPeristiwa
from tests.api.test_saya_http import JalurPencatat
from tests.konftes_asinkron import jalankan

MURAH = sandi.ParameterScrypt(n=2**4, r=8, p=1)
SANDI = "abcd-efgh-jkmn-pqrs"
VERSI_APLIKASI = "uji-034"
VERSI_NASKAH = "ET02-uji"
# 6 Oktober 2026, 08.00 WIB.
T0 = datetime(2026, 10, 6, 1, 0, tzinfo=UTC)

A = BarisAkun(
    id="ks-017",
    pseudonim="psd_aaaaaaaaaaaaaaaa",
    peran="pengguna",
    status_aktif=True,
    turunan_sandi=sandi.turunkan(SANDI, parameter=MURAH),
    gagal_beruntun=0,
    ditahan_sampai=None,
)


class TelemetriRusak(TelemetriMemori):
    """Penyimpan yang selalu gagal — R-07."""

    async def tambah(self, baris: BarisPeristiwa) -> None:
        raise RuntimeError("sambungan putus")

    async def terakhir(self, pemilik: str, jenis: str) -> datetime | None:
        raise RuntimeError("sambungan putus")


class Lingkungan:
    def __init__(
        self,
        *,
        telemetri: TelemetriMemori | None = None,
        rekam: bool = True,
    ) -> None:
        self.kini = T0
        self.akun = AkunMemori()
        self.akun.pasang_akun(A)
        self.pengguna = PenggunaMemori()
        self.kurasi = KurasiMemori()
        self.penemuan = PenemuanMemori(self.kurasi)
        self.telemetri = telemetri if telemetri is not None else TelemetriMemori()
        self.jalur = JalurPencatat()
        jam = lambda: self.kini  # noqa: E731
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=jam),
                riwayat=RiwayatMemori(),
                masuk=PenjagaMasuk(
                    self.akun,
                    sekarang=jam,
                    turunan_tiruan=sandi.turunkan("tiruan", parameter=MURAH),
                ),
                pengguna=self.pengguna,
                versi_naskah=VERSI_NASKAH,
                kurasi=self.kurasi,
                penemuan=self.penemuan,
                telemetri=self.telemetri if rekam else None,
                versi_aplikasi=VERSI_APLIKASI if rekam else None,
                sekarang=jam,
            ),
            base_url="https://testserver",
        )
        self.kuki = ""

    def setuju(self, disetujui: bool = True) -> None:
        jalankan(
            self.pengguna.catat_persetujuan(
                A.pseudonim, versi_naskah=VERSI_NASKAH, disetujui=disetujui, sekarang=self.kini
            )
        )

    def masuk(self, kata: str = SANDI) -> Any:
        tanggapan = self.klien.post(
            "/api/v1/auth/masuk", json={"nama_pengguna": A.id, "sandi": kata}
        )
        self.klien.cookies.clear()
        if tanggapan.status_code == 204:
            self.kuki = tanggapan.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]
        return tanggapan

    def minta(self, metode: str, jalur: str, **lain: Any) -> Any:
        tanggapan = self.klien.request(
            metode, jalur, headers={"Cookie": f"{NAMA_KUKI}={self.kuki}"}, **lain
        )
        self.klien.cookies.clear()
        return tanggapan

    def keluar(self) -> Any:
        return self.minta("POST", "/api/v1/auth/keluar", json={})

    def cabut(self) -> None:
        tanggapan = self.minta("POST", "/api/v1/saya/persetujuan", json={"cabut": True})
        assert tanggapan.json()["persetujuan"] == "dicabut", tanggapan.text

    def peristiwa(self) -> list[BarisPeristiwa]:
        return list(jalankan(self.telemetri.milik(A.pseudonim)))

    def jenis(self) -> list[str]:
        return [p.jenis for p in self.peristiwa()]


def _bentuk(tanggapan: Any) -> tuple[int, bytes, list[str]]:
    """Status, badan, dan atribut kuki — tanpa nilai pengenal yang acak."""
    kuki = tanggapan.headers.get("set-cookie", "")
    return tanggapan.status_code, tanggapan.content, kuki.split(";")[1:]


# ── C-04 · tanpa persetujuan, nol ───────────────────────────────────


@pytest.mark.parametrize("keadaan", ["belum_diminta", "ditolak", "dicabut"])
def test_tanpa_persetujuan_masuk_dan_keluar_tidak_menyimpan_apa_pun(keadaan: str) -> None:
    """M-2: perekam yang melewati persetujuan menyimpan `session_start`."""
    ling = Lingkungan()
    if keadaan == "ditolak":
        ling.setuju(disetujui=False)
    if keadaan == "dicabut":
        ling.setuju()
        ling.kini += timedelta(minutes=1)
        assert jalankan(ling.pengguna.cabut_persetujuan(A.pseudonim, sekarang=ling.kini))
    ling.masuk()
    ling.kini += timedelta(minutes=10)
    ling.keluar()
    ling.kini += timedelta(days=2)
    ling.masuk()
    assert ling.peristiwa() == []


def test_penolakan_masuk_tidak_merekam() -> None:
    ling = Lingkungan()
    ling.setuju()
    assert ling.masuk(kata="salah-sama-sekali").status_code == 401
    assert ling.peristiwa() == []


# ── K-6 · peristiwa sesi ────────────────────────────────────────────


def test_dengan_persetujuan_masuk_dan_keluar_tercatat_beserta_durasinya() -> None:
    ling = Lingkungan()
    ling.setuju()
    ling.masuk()
    ling.kini += timedelta(minutes=24, seconds=50)
    assert ling.keluar().status_code == 204
    awal, akhir = ling.peristiwa()
    assert (awal.jenis, awal.properti, awal.waktu) == ("session_start", {}, T0)
    assert (akhir.jenis, akhir.properti) == ("session_end", {"durasi_menit": 24})
    assert akhir.waktu == T0 + timedelta(minutes=24, seconds=50)


def test_peristiwa_sesi_membawa_versi_aplikasi_dan_tanpa_model() -> None:
    """R-08, K-4."""
    ling = Lingkungan()
    ling.setuju()
    ling.masuk()
    ling.keluar()
    for p in ling.peristiwa():
        assert (p.versi_aplikasi, p.versi_model) == (VERSI_APLIKASI, TANPA_MODEL)
        assert p.waktu.utcoffset() == timedelta(0)
    assert TANPA_MODEL == "tanpa_model"


def test_keluar_tanpa_awal_sesi_terekam_tanpa_durasi() -> None:
    """Persetujuan diberikan di tengah sesi: awalnya tidak terekam, durasi tidak ditebak."""
    ling = Lingkungan()
    ling.masuk()
    ling.setuju()
    ling.kini += timedelta(minutes=5)
    ling.keluar()
    (akhir,) = ling.peristiwa()
    assert (akhir.jenis, akhir.properti) == ("session_end", {})


def test_durasi_tidak_dihitung_dari_awal_sesi_yang_lebih_tua_dari_masa_sesi() -> None:
    """Sesi paling lama delapan jam; awal yang lebih tua milik sesi lain."""
    ling = Lingkungan()
    ling.setuju()
    ling.masuk()
    ling.setuju(disetujui=False)
    ling.kini += timedelta(hours=9)
    ling.masuk()
    ling.setuju()
    ling.kini += timedelta(minutes=3)
    ling.keluar()
    assert [(p.jenis, p.properti) for p in ling.peristiwa()] == [
        ("session_start", {}),
        ("session_end", {}),
    ]


def test_kunjungan_ulang_hanya_sesudah_lebih_dari_dua_puluh_empat_jam() -> None:
    """M-8: tanpa ambang, masuk kedua di hari yang sama terhitung kunjungan ulang."""
    ling = Lingkungan()
    ling.setuju()
    ling.masuk()
    ling.kini += timedelta(hours=3)
    ling.masuk()
    ling.kini += timedelta(hours=24)
    ling.masuk()
    assert ling.jenis() == ["session_start", "session_start", "session_start"]

    ling.kini += timedelta(hours=30, minutes=59)
    ling.masuk()
    *_, ulang, awal = ling.peristiwa()
    assert (ulang.jenis, ulang.properti) == ("return_visit", {"jeda_jam": 30})
    assert (awal.jenis, awal.properti) == ("session_start", {})
    assert ulang.waktu == awal.waktu == ling.kini


# ── R-02 · seketika ─────────────────────────────────────────────────


def test_pencabutan_berlaku_pada_permintaan_berikutnya() -> None:
    """M-1: perekam yang menyimpan keadaan persetujuan masih merekam `session_end`."""
    ling = Lingkungan()
    ling.setuju()
    ling.masuk()
    ling.kini += timedelta(minutes=2)
    ling.cabut()
    ling.kini += timedelta(minutes=2)
    ling.keluar()
    assert ling.jenis() == ["session_start"]


def test_persetujuan_yang_diberikan_di_tengah_sesi_berlaku_seketika() -> None:
    ling = Lingkungan()
    ling.masuk()
    assert ling.peristiwa() == []
    ling.minta(
        "POST", "/api/v1/saya/persetujuan", json={"versi_naskah": VERSI_NASKAH, "disetujui": True}
    )
    ling.keluar()
    assert ling.jenis() == ["session_end"]


# ── C-05 · pseudonim ────────────────────────────────────────────────


def test_pemilik_peristiwa_pseudonim_bukan_id_akun() -> None:
    """M-3: pemilik `pengguna.id` tidak sampai ke tabel sebagai pemilik apa pun."""
    ling = Lingkungan()
    ling.setuju()
    ling.masuk()
    ling.keluar()
    tersimpan = ling.telemetri._baris
    assert [b.jenis for b in tersimpan] == ["session_start", "session_end"]
    assert {b.pseudonim for b in tersimpan} == {A.pseudonim}
    assert all(A.id not in repr(b) for b in tersimpan)


# ── R-03 · tanggapan sama ───────────────────────────────────────────


def test_tanggapan_masuk_dan_keluar_sama_dengan_dan_tanpa_persetujuan() -> None:
    bentuk = []
    for setuju in (True, False):
        ling = Lingkungan()
        if setuju:
            ling.setuju()
        bentuk.append((_bentuk(ling.masuk()), _bentuk(ling.keluar())))
    assert bentuk[0] == bentuk[1]


def test_tanpa_penyimpan_telemetri_tanggapan_sama_dan_tidak_ada_yang_tersimpan() -> None:
    dengan, tanpa = Lingkungan(), Lingkungan(rekam=False)
    for ling in (dengan, tanpa):
        ling.setuju()
    assert _bentuk(dengan.masuk()) == _bentuk(tanpa.masuk())
    assert _bentuk(dengan.keluar()) == _bentuk(tanpa.keluar())
    assert tanpa.peristiwa() == []


# ── R-07 · galat penyimpan ditelan ──────────────────────────────────


def test_penyimpan_rusak_tidak_mengubah_tanggapan_dan_log_tanpa_muatan(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """M-7: galat yang diteruskan menjadi 500 pada rute masuk."""
    utuh, rusak = Lingkungan(), Lingkungan(telemetri=TelemetriRusak())
    for ling in (utuh, rusak):
        ling.setuju()
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        assert _bentuk(rusak.masuk()) == _bentuk(utuh.masuk())
        rusak.kini += timedelta(minutes=7)
        assert _bentuk(rusak.keluar()) == _bentuk(utuh.keluar())
    catatan = [r.getMessage() for r in caplog.records if r.name == LOG_OPERASIONAL.name]
    assert any("session_start" in c and "RuntimeError" in c for c in catatan), catatan
    assert any("session_end" in c and "RuntimeError" in c for c in catatan), catatan
    for c in catatan:
        assert A.pseudonim not in c
        assert A.id not in c
        assert "durasi" not in c
        assert "sambungan putus" not in c


# ── penyusunan ──────────────────────────────────────────────────────


def test_penyimpan_telemetri_menuntut_penyimpan_pengguna_dan_versi_aplikasi() -> None:
    dasar: dict[str, Any] = {
        "jalur": JalurPencatat(),
        "identitas": PenentuSesi(AkunMemori()),
        "riwayat": RiwayatMemori(),
        "telemetri": TelemetriMemori(),
    }
    with pytest.raises(ValueError, match="persetujuan"):
        susun_aplikasi(**dasar, versi_aplikasi=VERSI_APLIKASI)
    for versi in (None, "", "  "):
        with pytest.raises(ValueError, match="versi"):
            susun_aplikasi(**dasar, pengguna=PenggunaMemori(), versi_aplikasi=versi)


def test_pemilik_sesi_membaca_pseudonim_dari_sesi_yang_baru_terbit() -> None:
    """K-5."""
    akun = AkunMemori()
    akun.pasang_akun(A)
    penjaga = PenjagaMasuk(
        akun, sekarang=lambda: T0, turunan_tiruan=sandi.turunkan("t", parameter=MURAH)
    )
    pengenal = jalankan(penjaga.masuk(A.id, SANDI))
    assert pengenal is not None
    assert jalankan(penjaga.pemilik_sesi(pengenal)) == A.pseudonim
    assert jalankan(penjaga.pemilik_sesi("tidak-dikenal")) is None
    jalankan(penjaga.keluar(pengenal))
    assert jalankan(penjaga.pemilik_sesi(pengenal)) is None


# ── Perekam di luar rute ────────────────────────────────────────────


def _perekam(telemetri: TelemetriMemori | None = None) -> tuple[Perekam, PenggunaMemori]:
    pengguna = PenggunaMemori()
    return Perekam(pengguna, telemetri or TelemetriMemori(), versi_aplikasi=VERSI_APLIKASI), (
        pengguna
    )


def test_perekam_tanpa_persetujuan_tidak_menyimpan() -> None:
    telemetri = TelemetriMemori()
    perekam, _ = _perekam(telemetri)
    jalankan(perekam.rekam(A.pseudonim, JenisPeristiwa.QUESTION_ASKED, {}, sekarang=T0))
    assert telemetri._baris == []


def test_properti_beridentitas_ditolak_dan_dicatat_tanpa_muatan(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Kekeliruan pemanggil terlihat di log, tetapi isinya tidak (KM-03)."""
    telemetri = TelemetriMemori()
    perekam, pengguna = _perekam(telemetri)
    jalankan(
        pengguna.catat_persetujuan(
            A.pseudonim, versi_naskah=VERSI_NASKAH, disetujui=True, sekarang=T0
        )
    )
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        jalankan(
            perekam.rekam(
                A.pseudonim,
                JenisPeristiwa.QUESTION_ASKED,
                {"nama_sekolah": "SD Negeri Contoh"},
                sekarang=T0,
            )
        )
    assert telemetri._baris == []
    (catatan,) = [r.getMessage() for r in caplog.records]
    assert "properti ditolak" in catatan and "question_asked" in catatan
    assert "Contoh" not in catatan and "nama" not in catatan


def test_awal_sesi_tanpa_pemilik_tidak_merekam_dan_pencari_rusak_ditelan() -> None:
    """Sesi yang sudah tidak sah saat dibaca ulang tidak memiliki pemilik."""
    telemetri = TelemetriMemori()
    perekam, _ = _perekam(telemetri)

    async def tanpa() -> str | None:
        return None

    async def rusak() -> str | None:
        raise RuntimeError("akun tidak terjangkau")

    jalankan(perekam.mulai_sesi(tanpa, sekarang=T0))
    jalankan(perekam.mulai_sesi(rusak, sekarang=T0))
    assert telemetri._baris == []


def test_perekam_menolak_versi_aplikasi_kosong() -> None:
    with pytest.raises(ValueError, match="versi"):
        Perekam(PenggunaMemori(), TelemetriMemori(), versi_aplikasi=" ")


def test_rekam_atas_penyimpan_rusak_tidak_melempar(caplog: pytest.LogCaptureFixture) -> None:
    """R-07 pada jalur `rekam` — M-7."""
    perekam, pengguna = _perekam(TelemetriRusak())
    jalankan(
        pengguna.catat_persetujuan(
            A.pseudonim, versi_naskah=VERSI_NASKAH, disetujui=True, sekarang=T0
        )
    )
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        jalankan(perekam.rekam(A.pseudonim, JenisPeristiwa.QUESTION_ASKED, {}, sekarang=T0))
    (catatan,) = [r.getMessage() for r in caplog.records]
    assert "question_asked" in catatan and "RuntimeError" in catatan
    assert A.pseudonim not in catatan
