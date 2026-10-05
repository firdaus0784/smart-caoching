"""Rute kurasi — T-5 fitur 013, R-04, R-09, R-10; K-5, K-6; D-14 Bagian 4.7.

Identitas dari `PenentuSesi` sungguhan atas `AkunMemori`, sehingga pemutus yang
tercatat benar-benar pseudonim dari sesi kurator — bukan identitas tetap.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import MASA_SESI, NAMA_KUKI, PenentuSesi
from src.api.kurasi import (
    PESAN_BUTIR_TIDAK_ADA,
    PESAN_PUTUSAN_TIDAK_SAH,
    PESAN_REGULASI_TIDAK_BERLAKU,
    PESAN_TARIK_TIDAK_SAH,
)
from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.llm.galat import kalimat_terlalu_panjang
from src.nlp.anotasi.skema import KategoriMasalah
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.kurasi import BarisKandidat, KurasiMemori
from src.penyimpanan.pengguna import PenggunaMemori
from src.penyimpanan.riwayat import RiwayatMemori
from tests.api.test_saya_http import JalurPencatat
from tests.konftes_asinkron import jalankan

T0 = datetime(2026, 10, 5, 1, 0, tzinfo=UTC)
NIK = "3201234567890001"


def _akun(id_akun: str, pseudonim: str, peran: str) -> BarisAkun:
    return BarisAkun(
        id=id_akun,
        pseudonim=pseudonim,
        peran=peran,
        status_aktif=True,
        turunan_sandi="scrypt$16$8$1$AAAA$AAAA",
        gagal_beruntun=0,
        ditahan_sampai=None,
    )


K = _akun("kr-001", "psd_kkkkkkkkkkkkkkkk", "kurator")
A = _akun("ks-017", "psd_aaaaaaaaaaaaaaaa", "pengguna")


def butir(
    id_butir: str,
    *,
    kategori: str = "K1",
    jenis: str = "riset",
    status: str | None = None,
    lisensi: str = "CC-BY",
    dokumen: str | None = None,
) -> ButirPengetahuan:
    return ButirPengetahuan(
        id_butir=id_butir,
        jenis_sumber=JenisSumberButir(jenis),
        judul="Supervisi akademik terjadwal",
        alasan_relevansi="Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
        inti_temuan="Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
        implikasi_tindakan=("Susun jadwal supervisi satu semester.",),
        perkiraan_waktu_baca=4,
        kategori=KategoriMasalah(kategori),
        id_dokumen_sumber=dokumen or "dok-" + id_butir,
        lisensi=lisensi,
        status_keberlakuan=None if status is None else status,  # type: ignore[arg-type]
        tanggal_akses=date(2026, 10, 1),
    )


SUMBER = {"judul": "Laporan", "penerbit": "Penerbit", "tahun": 2025, "tautan": None}


class Lingkungan:
    def __init__(self) -> None:
        self.kini = T0
        self.akun = AkunMemori()
        for satu in (K, A):
            self.akun.pasang_akun(satu)
        self.kurasi = KurasiMemori()
        self.klien = TestClient(
            susun_aplikasi(
                jalur=JalurPencatat(),
                identitas=PenentuSesi(self.akun, sekarang=lambda: self.kini),
                riwayat=RiwayatMemori(),
                pengguna=PenggunaMemori(),
                kurasi=self.kurasi,
                sekarang=lambda: self.kini,
            ),
            base_url="https://testserver",
        )
        self.kuki = {akun.id: self._sesi(akun) for akun in (K, A)}

    def _sesi(self, akun: BarisAkun) -> str:
        pengenal = secrets.token_urlsafe(32)
        jalankan(
            self.akun.buat_sesi(
                hashlib.sha256(pengenal.encode()).digest(),
                akun.id,
                sekarang=self.kini,
                kedaluwarsa_pada=self.kini + MASA_SESI,
            )
        )
        return pengenal

    def masukkan(self, b: ButirPengetahuan) -> str:
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
                    masuk_pada=T0,
                )
            )
        )
        return b.id_butir

    def minta(self, metode: str, jalur: str, siapa: BarisAkun | None = K, **lain: Any) -> Any:
        tajuk = {"Cookie": f"{NAMA_KUKI}={self.kuki[siapa.id]}"} if siapa is not None else {}
        return self.klien.request(metode, jalur, headers=tajuk, **lain)

    def putuskan(self, id_butir: str, badan: object, **lain: Any) -> Any:
        return self.minta("POST", f"/api/v1/kurasi/{id_butir}/putusan", json=badan, **lain)

    def tarik(self, id_butir: str, badan: object) -> Any:
        return self.minta("POST", f"/api/v1/kurasi/{id_butir}/tarik", json=badan)


def _galat(tanggapan: Any) -> tuple[int, str, str]:
    g = tanggapan.json()["galat"]
    return tanggapan.status_code, g["kode"], g["pesan_pengguna"]


SETUJUI = {"jenis": "setujui", "catatan": "Layak tayang"}


# ── antrean ──────────────────────────────────────────────────────────


def test_antrean_berbentuk_d14() -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1", jenis="regulasi", status="berlaku"))
    tanggapan = ling.minta("GET", "/api/v1/kurasi/antrean")
    assert tanggapan.status_code == 200
    isi = tanggapan.json()
    assert isi["tayang"] == []
    assert isi["menunggu"] == [
        {
            "id_butir": "b-1",
            "kategori": "K1",
            "jenis_sumber": "regulasi",
            "judul": "Supervisi akademik terjadwal",
            "alasan_relevansi": "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
            "inti_temuan": "Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
            "implikasi_tindakan": ["Susun jadwal supervisi satu semester."],
            "perkiraan_waktu_baca": 4,
            "tenggat_terkait": None,
            "lisensi": "CC-BY",
            "status_keberlakuan": "berlaku",
            "sumber": SUMBER,
            "masuk_pada": "2026-10-05T01:00:00Z",
        }
    ]


def test_rute_kurasi_hanya_bagi_kurator() -> None:
    """R-09."""
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    for metode, jalur, badan in (
        ("GET", "/api/v1/kurasi/antrean", None),
        ("POST", "/api/v1/kurasi/b-1/putusan", SETUJUI),
        ("POST", "/api/v1/kurasi/b-1/tarik", {"pemicu": "kekeliruan_isi_dilaporkan"}),
    ):
        assert _galat(ling.minta(metode, jalur, siapa=A, json=badan))[:2] == (
            403,
            "TIDAK_BERWENANG",
        )
        assert _galat(ling.minta(metode, jalur, siapa=None, json=badan))[:2] == (
            401,
            "TIDAK_TERAUTENTIKASI",
        )
    assert ling.minta("GET", "/api/v1/kurasi/antrean").json()["menunggu"][0]["id_butir"] == "b-1"


# ── putusan ──────────────────────────────────────────────────────────


def test_setujui_menayangkan_dan_mencatat_pseudonim_kurator() -> None:
    """C-06, K-5, M-10: pemutus adalah pseudonim sesi, bukan nama akun."""
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    tanggapan = ling.putuskan("b-1", SETUJUI)
    assert tanggapan.status_code == 200
    isi = tanggapan.json()
    assert isi["menunggu"] == []
    assert [t["id_butir"] for t in isi["tayang"]] == ["b-1"]
    assert isi["tayang"][0] == {
        "id_butir": "b-1",
        "kategori": "K1",
        "jenis_sumber": "riset",
        "judul": "Supervisi akademik terjadwal",
        "lisensi": "CC-BY",
        "status_keberlakuan": None,
        "tayang_pada": "2026-10-05T01:00:00Z",
        "perlu_tinjauan": False,
    }
    jejak = ling.kurasi.jejak()[-1]
    assert (jejak.peran, jejak.pseudonim_kurator, jejak.alasan) == (
        "kurator",
        K.pseudonim,
        "Layak tayang",
    )
    assert K.pseudonim not in tanggapan.text and K.id not in tanggapan.text


def test_sunting_lalu_setujui_menayangkan_suntingan() -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    suntingan = {
        "judul": "Jadwal supervisi akademik",
        "alasan_relevansi": "Sekolah Anda memprioritaskan supervisi akademik semester ini.",
        "inti_temuan": "Supervisi terjadwal memperbanyak umpan balik kepada guru kelas.",
        "implikasi_tindakan": ["Tetapkan jadwal supervisi.", "Bagikan jadwal kepada guru."],
    }
    tanggapan = ling.putuskan(
        "b-1",
        {
            "jenis": "sunting_lalu_setujui",
            "catatan": "Parafrase diperbaiki",
            "suntingan": suntingan,
        },
    )
    assert tanggapan.status_code == 200
    assert tanggapan.json()["tayang"][0]["judul"] == "Jadwal supervisi akademik"
    tayang = ling.kurasi.baris_tayang()["b-1"]
    assert tayang.butir["implikasi_tindakan"] == suntingan["implikasi_tindakan"]
    assert tayang.butir["lisensi"] == "CC-BY"


@pytest.mark.parametrize(
    ("bidang", "nilai"),
    [
        ("lisensi", "Hak cipta dilindungi"),
        ("kategori", "K8"),
        ("jenis_sumber", "praktik_baik"),
        ("id_dokumen_sumber", "dok-lain"),
        ("perkiraan_waktu_baca", 2),
    ],
)
def test_suntingan_tidak_dapat_mengganti_selain_parafrase(bidang: str, nilai: object) -> None:
    """M-11. Badannya lengkap dan sah kecuali satu bidang yang bukan parafrase —
    penolakannya karena bidang itu, bukan karena badan yang kurang (KB-098)."""
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    sah = {
        "judul": "Judul baru",
        "alasan_relevansi": "Sekolah Anda memprioritaskan supervisi akademik.",
        "inti_temuan": "Supervisi terjadwal memperbanyak umpan balik.",
        "implikasi_tindakan": ["Tetapkan jadwal supervisi."],
    }
    badan = {"jenis": "sunting_lalu_setujui", "catatan": "x", "suntingan": sah}
    assert ling.putuskan("b-1", {**badan, "suntingan": {**sah, bidang: nilai}}).status_code == 400
    assert ling.kurasi.baris_tayang() == {}
    assert ling.putuskan("b-1", badan).status_code == 200
    assert ling.kurasi.baris_tayang()["b-1"].butir[bidang] != nilai


def test_tolak_dengan_kode_tl() -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    tanggapan = ling.putuskan("b-1", {"jenis": "tolak", "alasan_tolak": "TL-09"})
    assert tanggapan.status_code == 200
    assert tanggapan.json() == {"menunggu": [], "tayang": []}
    assert ling.kurasi.jejak()[-1].alasan == "TL-09"


def test_tunda_sampai_tanggal_kembali() -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    tanggapan = ling.putuskan(
        "b-1", {"jenis": "tunda", "catatan": "Tunggu juknis", "kembali_pada": "2026-10-12"}
    )
    assert tanggapan.status_code == 200
    assert tanggapan.json()["menunggu"] == []
    ling.kini = datetime(2026, 10, 11, 16, 59, tzinfo=UTC)  # 11 Oktober 23.59 WIB
    ling.kuki[K.id] = ling._sesi(K)
    assert ling.minta("GET", "/api/v1/kurasi/antrean").json()["menunggu"] == []
    ling.kini = datetime(2026, 10, 11, 17, 0, tzinfo=UTC)  # 12 Oktober 00.00 WIB
    assert [
        k["id_butir"] for k in ling.minta("GET", "/api/v1/kurasi/antrean").json()["menunggu"]
    ] == ["b-1"]


@pytest.mark.parametrize(
    "badan",
    [
        {"jenis": "setujui"},
        {"jenis": "setujui", "catatan": "  "},
        {"jenis": "setujui", "catatan": "x", "alasan_tolak": "TL-01"},
        {"jenis": "tolak"},
        {"jenis": "tolak", "alasan_tolak": "TL-12"},
        {"jenis": "tolak", "alasan_tolak": "TL-01", "catatan": "rincian bebas"},
        {"jenis": "tunda", "catatan": "x"},
        {"jenis": "tunda", "catatan": "x", "kembali_pada": "2026-10-01"},
        {"jenis": "tarik", "catatan": "x"},
        {"jenis": "sunting_lalu_setujui", "catatan": "x"},
        {"jenis": "setujui", "catatan": f"Hubungi {NIK}"},
        ["setujui"],
        "setujui",
    ],
)
def test_putusan_berbentuk_salah_ditolak(badan: object) -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    tanggapan = ling.putuskan("b-1", badan)
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_PUTUSAN_TIDAK_SAH)
    assert NIK not in tanggapan.text
    assert ling.kurasi.jejak() == ()


def test_putusan_menuntut_json() -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    tanggapan = ling.minta(
        "POST", "/api/v1/kurasi/b-1/putusan", content='{"jenis": "setujui", "catatan": "x"}'
    )
    assert _galat(tanggapan)[:2] == (400, "VALIDASI_GAGAL")


def test_regulasi_dicabut_selama_menunggu_ditolak_tl04() -> None:
    """R-04, K-4, M-5: status diperbarui perkakas sesudah kandidat masuk antrean;
    rute memakai status terkini, bukan salinan saat masuk."""
    ling = Lingkungan()
    ling.masukkan(butir("b-1", jenis="regulasi", status="berlaku", dokumen="permen-1"))
    jalankan(ling.kurasi.perbarui_status("permen-1", "dicabut"))
    tanggapan = ling.putuskan("b-1", SETUJUI)
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_REGULASI_TIDAK_BERLAKU)
    assert ling.kurasi.baris_tayang() == {}
    # Tolak TL-04 tetap dapat diambil.
    assert ling.putuskan("b-1", {"jenis": "tolak", "alasan_tolak": "TL-04"}).status_code == 200


def test_putusan_atas_butir_yang_tidak_menunggu() -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    assert _galat(ling.putuskan("b-tak-ada", SETUJUI)) == (
        404,
        "SUMBER_TIDAK_ADA",
        PESAN_BUTIR_TIDAK_ADA,
    )
    assert ling.putuskan("b-1", SETUJUI).status_code == 200
    assert _galat(ling.putuskan("b-1", {"jenis": "tolak", "alasan_tolak": "TL-01"}))[0] == 404


# ── penarikan ────────────────────────────────────────────────────────


def _tayang(ling: Lingkungan, *b: ButirPengetahuan) -> None:
    for satu in b:
        ling.masukkan(satu)
        assert ling.putuskan(satu.id_butir, SETUJUI).status_code == 200


def test_tarik_karena_regulasi_dan_kekeliruan() -> None:
    ling = Lingkungan()
    _tayang(ling, butir("b-1", jenis="regulasi", status="berlaku"), butir("b-2"))
    pertama = ling.tarik(
        "b-1",
        {
            "pemicu": "regulasi_sumber_berubah",
            "catatan": "Permen dicabut",
            "status_terkini": "dicabut",
        },
    )
    assert pertama.status_code == 200
    kedua = ling.tarik("b-2", {"pemicu": "kekeliruan_isi_dilaporkan", "catatan": "Angka keliru"})
    assert kedua.json()["tayang"] == []
    assert ling.kurasi.baris_tayang()["b-1"].ditarik_pada == T0


def test_pembaruan_data_tanpa_perubahan_bermakna_tetap_tayang() -> None:
    ling = Lingkungan()
    _tayang(ling, butir("b-1"))
    tanggapan = ling.tarik(
        "b-1", {"pemicu": "data_sumber_diperbarui", "catatan": "Data 2026 terbit"}
    )
    assert tanggapan.status_code == 200
    assert tanggapan.json()["tayang"][0]["perlu_tinjauan"] is True
    bermakna = ling.tarik(
        "b-1",
        {
            "pemicu": "data_sumber_diperbarui",
            "catatan": "Angka berubah",
            "angka_berubah_bermakna": True,
        },
    )
    # Sudah ditandai — penarikan kedua atas butir yang masih tayang tetap boleh.
    assert bermakna.status_code == 200
    assert bermakna.json()["tayang"] == []


@pytest.mark.parametrize(
    "badan",
    [
        {"pemicu": "regulasi_sumber_berubah", "catatan": "x"},
        {"pemicu": "regulasi_sumber_berubah", "catatan": "x", "status_terkini": "berlaku"},
        {
            "pemicu": "regulasi_sumber_berubah",
            "catatan": "x",
            "status_terkini": "dicabut",
            "angka_berubah_bermakna": True,
        },
        {"pemicu": "kekeliruan_isi_dilaporkan", "catatan": "x", "status_terkini": "dicabut"},
        {"pemicu": "kekeliruan_isi_dilaporkan", "catatan": " "},
        {"pemicu": "kekeliruan_isi_dilaporkan", "catatan": f"Pelapor {NIK}"},
        {"pemicu": "bosan", "catatan": "x"},
        {"pemicu": "kekeliruan_isi_dilaporkan", "catatan": "x", "lain": 1},
    ],
)
def test_tarik_berbentuk_salah_ditolak(badan: dict[str, object]) -> None:
    ling = Lingkungan()
    _tayang(ling, butir("b-1", jenis="regulasi", status="berlaku"))
    tanggapan = ling.tarik("b-1", badan)
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_TARIK_TIDAK_SAH)
    assert NIK not in tanggapan.text
    assert ling.kurasi.baris_tayang()["b-1"].ditarik_pada is None


def test_tarik_butir_yang_tidak_tayang() -> None:
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    badan = {"pemicu": "kekeliruan_isi_dilaporkan", "catatan": "x"}
    assert _galat(ling.tarik("b-1", badan))[0] == 404
    assert _galat(ling.tarik("b-tak-ada", badan))[0] == 404


def test_pesan_kurasi_memenuhi_c13() -> None:
    for pesan in (
        PESAN_BUTIR_TIDAK_ADA,
        PESAN_PUTUSAN_TIDAK_SAH,
        PESAN_REGULASI_TIDAK_BERLAKU,
        PESAN_TARIK_TIDAK_SAH,
    ):
        assert not kalimat_terlalu_panjang(pesan), pesan


def test_tanggal_wib_bagi_tunda() -> None:
    """Pukul 23.30 UTC tanggal 11 sudah tanggal 12 WIB."""
    from src.api.hari import tanggal_wib

    assert tanggal_wib(datetime(2026, 10, 11, 23, 30, tzinfo=UTC)) == date(2026, 10, 12)
    assert tanggal_wib(datetime(2026, 10, 11, 16, 59, tzinfo=UTC)) == date(2026, 10, 11)
    with pytest.raises(ValueError):
        tanggal_wib(datetime(2026, 10, 11))
    assert (
        timedelta(hours=7)
        == datetime(2026, 1, 1, tzinfo=UTC)
        .astimezone(__import__("src.api.hari", fromlist=["WIB"]).WIB)
        .utcoffset()
    )


# ── keadaan antara dan penyimpan rusak ───────────────────────────────


class _Didahului(KurasiMemori):
    """Kurator lain memutus atau menarik di antara pembacaan dan penulisan."""

    async def setujui(self, catatan: Any, *, butir: dict[str, Any]) -> bool:
        return False

    async def tarik(self, id_butir: str, **lain: Any) -> bool:
        return False


def test_didahului_kurator_lain_menjadi_tidak_ada() -> None:
    from src.api.kurasi import ButirTidakAda, putuskan
    from src.api.kurasi import tarik as tarik_butir

    simpan = _Didahului()
    b = butir("b-1")
    jalankan(
        simpan.tambah_kandidat(
            BarisKandidat(
                id_butir="b-1",
                butir=b.model_dump(mode="json"),
                sumber=SUMBER,
                id_dokumen_sumber=b.id_dokumen_sumber,
                kategori="K1",
                status_keberlakuan=None,
                masuk_pada=T0,
            )
        )
    )
    with pytest.raises(ButirTidakAda):
        jalankan(putuskan(simpan, "b-1", SETUJUI, pseudonim=K.pseudonim, sekarang=T0))
    jalankan(KurasiMemori.setujui(simpan, _catatan("b-1"), butir=b.model_dump(mode="json")))
    with pytest.raises(ButirTidakAda):
        jalankan(
            tarik_butir(
                simpan,
                "b-1",
                {"pemicu": "kekeliruan_isi_dilaporkan", "catatan": "x"},
                pseudonim=K.pseudonim,
                sekarang=T0,
            )
        )


def _catatan(id_butir: str, jenis: str = "setujui") -> Any:
    from src.penyimpanan.kurasi import CatatanPutusan

    return CatatanPutusan(
        id_butir=id_butir,
        jenis=jenis,
        peran="kurator",
        pseudonim_kurator=K.pseudonim,
        alasan="Layak tayang",
        waktu=T0,
    )


@pytest.mark.parametrize("putusan", [None, ("tolak", "kurator")])
def test_baris_tayang_tanpa_putusan_setuju_adalah_kerusakan(putusan: Any) -> None:
    """Penyimpan yang menyerahkan butir tayang tanpa persetujuan tidak dibaca
    sebagai butir yang boleh ditinjau — ia kerusakan, dan berhenti terang."""
    from src.api.kurasi import _butir_tayang
    from src.penyimpanan.kurasi import BarisTayang, PutusanTayang

    b = butir("b-1")
    baris = BarisTayang(
        id_butir="b-1",
        butir=b.model_dump(mode="json"),
        sumber=SUMBER,
        id_dokumen_sumber=b.id_dokumen_sumber,
        kategori="K1",
        status_keberlakuan=None,
        tayang_pada=T0,
        putusan=None if putusan is None else PutusanTayang(*putusan, waktu=T0),
    )
    with pytest.raises(RuntimeError):
        _butir_tayang(baris)


def test_persetujuan_tanpa_butir_tayang_dihentikan() -> None:
    from src.api.kurasi import _wajib

    with pytest.raises(RuntimeError):
        _wajib(None)
