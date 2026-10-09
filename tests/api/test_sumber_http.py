"""Pembaca sumber — T-4 fitur 032, R-04 s.d. R-07; K-3, K-5; D-14 Bagian 4.10.

Akun bersesi sungguhan; isi korpus ditanam pada pembaca memori. Uji membaca
tanggapan HTTP dan peristiwa yang tersimpan, bukan fungsi di baliknya — aturan
tampil dan urutannya adalah perilaku yang dilihat kepala sekolah.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import MASA_SESI, NAMA_KUKI, PenentuSesi
from src.api.sumber import PESAN_BAGIAN_TIDAK_SAH, PESAN_SUMBER_TIDAK_ADA
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.pengguna import PenggunaMemori
from src.penyimpanan.riwayat import RiwayatMemori
from src.penyimpanan.sumber import SegmenBagian, SumberMemori
from src.penyimpanan.telemetri import TelemetriMemori
from tests.api.test_penemuan_http import T0, A, K
from tests.api.test_riwayat_http import JalurPencatat
from tests.konftes_asinkron import jalankan

VERSI_NASKAH = "ET02-uji"
DOK = "doc_permen_1_2026"
BAGIAN = "Pasal 7 ayat (2)"
TEKS = "Kepala sekolah menyusun rencana kerja tahunan bersama guru."


def _meta(jenis: str = "regulasi_resmi", tingkat: str = "publik") -> MetadataDokumen:
    return MetadataDokumen(
        judul="Permendikdasmen Nomor 1 Tahun 2026",
        jenis=jenis,
        penerbit="Kemendikdasmen",
        tahun=2026,
        tingkat_kerahasiaan=tingkat,
    )


def _segmen(teks: str = TEKS, *, lisensi: str = "terbuka", terverifikasi: bool = True) -> Any:
    return SegmenBagian(teks=teks, lisensi=lisensi, anonimisasi_terverifikasi=terverifikasi)


class Lingkungan:
    def __init__(self) -> None:
        self.akun = AkunMemori()
        for satu in (A, K):
            self.akun.pasang_akun(satu)
        self.sumber = SumberMemori()
        self.pengguna = PenggunaMemori()
        self.telemetri = TelemetriMemori()
        self.jalur = JalurPencatat()
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=lambda: T0),
                riwayat=RiwayatMemori(),
                pengguna=self.pengguna,
                versi_naskah=VERSI_NASKAH,
                telemetri=self.telemetri,
                versi_aplikasi="uji-032",
                sumber=self.sumber,
                sekarang=lambda: T0,
            ),
            base_url="https://testserver",
            raise_server_exceptions=False,
        )
        self.kuki: dict[str, str] = {}
        for satu in (A, K):
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
        jalankan(
            self.pengguna.catat_persetujuan(
                A.pseudonim, versi_naskah=VERSI_NASKAH, disetujui=True, sekarang=T0
            )
        )

    def dokumen(
        self,
        meta: MetadataDokumen | None = None,
        *,
        status: str | None = "berlaku",
        pengganti: str | None = None,
        segmen: tuple[Any, ...] = (),
        id_dokumen: str = DOK,
    ) -> None:
        self.sumber.tanam_dokumen(id_dokumen)
        self.sumber.tanam_metadata(id_dokumen, meta or _meta())
        if status is not None:
            self.sumber.tanam_status(id_dokumen, status, pengganti)
        for nomor, satu in enumerate(segmen or (_segmen(),)):
            self.sumber.tanam_segmen(f"{id_dokumen}-{nomor:02d}", id_dokumen, BAGIAN, satu)

    def baca(
        self, id_dokumen: str = DOK, bagian: str | None = BAGIAN, siapa: BarisAkun | None = A
    ) -> Any:
        tajuk = {"Cookie": f"{NAMA_KUKI}={self.kuki[siapa.id]}"} if siapa is not None else {}
        params = {} if bagian is None else {"bagian": bagian}
        return self.klien.get(f"/api/v1/sumber/{id_dokumen}", headers=tajuk, params=params)

    def dibuka(self) -> list[Any]:
        return [
            p for p in jalankan(self.telemetri.milik(A.pseudonim)) if p.jenis == "citation_opened"
        ]


def _galat(tanggapan: Any) -> tuple[int, str, str]:
    g = tanggapan.json()["galat"]
    return tanggapan.status_code, g["kode"], g["pesan_pengguna"]


def test_regulasi_publik_berlaku_berbentuk_d14() -> None:
    ling = Lingkungan()
    ling.dokumen()
    tanggapan = ling.baca()
    assert tanggapan.status_code == 200, tanggapan.text
    assert tanggapan.json() == {
        "id_dokumen": DOK,
        "judul": "Permendikdasmen Nomor 1 Tahun 2026",
        "jenis": "regulasi_resmi",
        "penerbit": "Kemendikdasmen",
        "tahun": 2026,
        "status_keberlakuan": "berlaku",
        "rujukan_pengganti": None,
        "bagian": BAGIAN,
        "teks_bagian": [TEKS],
        "tanpa_teks": None,
    }


def test_diubah_tetap_berteks_beserta_penggantinya() -> None:
    """R-07, FR-F14: status dan rujukan dikirim; layar menaruhnya sebelum teks."""
    ling = Lingkungan()
    ling.dokumen(status="diubah", pengganti="Permendikdasmen Nomor 2 Tahun 2027")
    isi = ling.baca().json()
    assert (isi["status_keberlakuan"], isi["rujukan_pengganti"]) == (
        "diubah",
        "Permendikdasmen Nomor 2 Tahun 2027",
    )
    assert isi["teks_bagian"] == [TEKS] and isi["tanpa_teks"] is None


@pytest.mark.parametrize(
    ("meta", "status"),
    [
        # M-6: dokumen sekolah pada tingkat publik tetap tanpa teks (ET-04).
        (_meta("dokumen_sekolah", "publik"), None),
        (_meta("dokumen_sekolah", "internal_sekolah"), None),
        (_meta("artikel_lisensi_terbuka", "terbatas"), None),
        # Aturan pertama menang atas `dicabut`.
        (_meta("dokumen_sekolah", "publik"), "dicabut"),
    ],
)
def test_dokumen_tidak_publik_tanpa_teks(meta: MetadataDokumen, status: str | None) -> None:
    """P-2 A, R-06."""
    ling = Lingkungan()
    ling.dokumen(meta, status=status)
    isi = ling.baca().json()
    assert (isi["teks_bagian"], isi["tanpa_teks"]) == ([], "dokumen_tidak_publik")
    assert isi["judul"] == meta.judul, "metadata tetap tampil"


def test_regulasi_tanpa_status_tanpa_teks() -> None:
    """TK-81 A; M-7. Sumber bukan regulasi tanpa status tetap berteks."""
    ling = Lingkungan()
    ling.dokumen(status=None)
    isi = ling.baca().json()
    assert (isi["status_keberlakuan"], isi["teks_bagian"], isi["tanpa_teks"]) == (
        None,
        [],
        "status_belum_tercatat",
    )

    ling = Lingkungan()
    ling.dokumen(_meta("artikel_lisensi_terbuka"), status=None)
    isi = ling.baca().json()
    assert (isi["teks_bagian"], isi["tanpa_teks"]) == ([TEKS], None)


@pytest.mark.parametrize("jenis", ["regulasi_resmi", "artikel_lisensi_terbuka"])
def test_dicabut_dinyatakan_dan_tanpa_teks(jenis: str) -> None:
    """R-07, C-07; M-8."""
    ling = Lingkungan()
    ling.dokumen(_meta(jenis), status="dicabut", pengganti="Permendikdasmen Nomor 2 Tahun 2027")
    isi = ling.baca().json()
    assert (isi["status_keberlakuan"], isi["teks_bagian"], isi["tanpa_teks"]) == (
        "dicabut",
        [],
        "dokumen_dicabut",
    )
    assert isi["rujukan_pengganti"] == "Permendikdasmen Nomor 2 Tahun 2027"


def test_segmen_yang_tidak_memenuhi_syarat_disaring() -> None:
    """R-04, R-06; M-9. Disaring satu per satu, bukan menggugurkan dokumen."""
    ling = Lingkungan()
    ling.dokumen(
        segmen=(
            _segmen("Kalimat bersih."),
            _segmen("Kalimat belum diverifikasi.", terverifikasi=False),
            _segmen("Kalimat berlisensi tertutup.", lisensi="tertutup"),
            _segmen("Kalimat lisensi tak dikenal.", lisensi="cc-by"),
        )
    )
    assert ling.baca().json()["teks_bagian"] == ["Kalimat bersih."]

    ling = Lingkungan()
    ling.dokumen(segmen=(_segmen(terverifikasi=False),))
    isi = ling.baca().json()
    assert (isi["teks_bagian"], isi["tanpa_teks"]) == ([], "bagian_tidak_tersedia")


def test_bagian_lain_tidak_dikirim() -> None:
    ling = Lingkungan()
    ling.dokumen()
    isi = ling.baca(bagian="Pasal 8").json()
    assert (isi["bagian"], isi["teks_bagian"], isi["tanpa_teks"]) == (
        "Pasal 8",
        [],
        "bagian_tidak_tersedia",
    )


def test_satu_bentuk_404_dan_tidak_direkam(caplog: pytest.LogCaptureFixture) -> None:
    """R-04: tidak dikenal, tidak di korpus, dan metadata yang tidak terbaca."""
    ling = Lingkungan()
    ling.sumber.tanam_metadata("doc_karantina", _meta())  # catatan tanpa dokumen korpus
    ling.dokumen(_meta(jenis="buku"), id_dokumen="doc_rusak")
    with caplog.at_level(logging.WARNING):
        bentuk = {_galat(ling.baca(d)) for d in ("doc_tak_ada", "doc_karantina", "doc_rusak")}
    assert bentuk == {(404, "SUMBER_TIDAK_ADA", PESAN_SUMBER_TIDAK_ADA)}
    assert "Permendikdasmen" not in caplog.text, "isi metadata tidak dikutip ke log"
    assert ling.dibuka() == []


@pytest.mark.parametrize("bagian", [None, "", "   "])
def test_bagian_wajib(bagian: str | None) -> None:
    ling = Lingkungan()
    ling.dokumen()
    assert _galat(ling.baca(bagian=bagian)) == (400, "VALIDASI_GAGAL", PESAN_BAGIAN_TIDAK_SAH)
    assert ling.dibuka() == []


def test_hanya_bagi_pengguna_bersesi() -> None:
    ling = Lingkungan()
    ling.dokumen()
    assert ling.baca(siapa=None).status_code == 401
    assert ling.baca(siapa=K).status_code == 403


def test_citation_opened_dua_properti_d01() -> None:
    """P-3 A: properti D-01 apa adanya, juga ketika teks tidak tampil."""
    ling = Lingkungan()
    ling.dokumen()
    ling.dokumen(_meta("dokumen_sekolah", "terbatas"), id_dokumen="doc_sekolah")
    ling.baca()
    ling.baca("doc_sekolah")
    pertama, kedua = ling.dibuka()
    assert pertama.properti == {"id_sumber": DOK, "jenis_sumber": "regulasi_resmi"}
    assert kedua.properti == {"id_sumber": "doc_sekolah", "jenis_sumber": "dokumen_sekolah"}
    assert pertama.versi_model == "tanpa_model"


def test_tanpa_persetujuan_tidak_direkam() -> None:
    ling = Lingkungan()
    jalankan(
        ling.pengguna.catat_persetujuan(
            A.pseudonim, versi_naskah=VERSI_NASKAH, disetujui=False, sekarang=T0
        )
    )
    ling.dokumen()
    assert ling.baca().status_code == 200
    assert ling.dibuka() == []


def test_pembaca_tidak_memanggil_jalur_penjawab() -> None:
    """R-05, C-08, C-17."""
    ling = Lingkungan()
    ling.dokumen()
    ling.baca()
    assert ling.jalur.panggilan == []
