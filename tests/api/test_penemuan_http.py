"""Rute penemuan — T-6 fitur 013, R-02, R-05 s.d. R-08; K-2; D-14 Bagian 4.6.

Butir disetujui lewat rute kurator sungguhan, sehingga C-06 diuji dari ujung ke
ujung: kandidat yang belum diputus tidak pernah tampil pada beranda.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import MASA_SESI, NAMA_KUKI, PenentuSesi
from src.api.kurasi import PESAN_BUTIR_TIDAK_ADA
from src.api.penemuan import PESAN_ALASAN_TIDAK_SAH
from src.ingest.kurasi.butir import ButirPengetahuan
from src.llm.galat import kalimat_terlalu_panjang
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.kurasi import BarisKandidat, KurasiMemori
from src.penyimpanan.penemuan import PenemuanMemori
from src.penyimpanan.pengguna import PenggunaMemori
from src.penyimpanan.riwayat import RiwayatMemori
from tests.api.test_aplikasi import ID_PERCAKAPAN
from tests.api.test_kurasi_http import SUMBER, butir
from tests.api.test_saya_http import JalurPencatat
from tests.konftes_asinkron import jalankan

# 5 Oktober 2026, 08.00 WIB.
T0 = datetime(2026, 10, 5, 1, 0, tzinfo=UTC)
NIK = "3201234567890001"


def _akun(id_akun: str, pseudonim: str, peran: str = "pengguna") -> BarisAkun:
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
A = _akun("ks-017", "psd_aaaaaaaaaaaaaaaa")
B = _akun("ks-018", "psd_bbbbbbbbbbbbbbbb")
C = _akun("ks-019", "psd_cccccccccccccccc")


class Lingkungan:
    def __init__(self) -> None:
        self.kini = T0
        self.akun = AkunMemori()
        for satu in (K, A, B, C):
            self.akun.pasang_akun(satu)
        self.kurasi = KurasiMemori()
        self.pengguna = PenggunaMemori()
        self.jalur = JalurPencatat()
        self.penemuan = PenemuanMemori(self.kurasi)
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=lambda: self.kini),
                riwayat=RiwayatMemori(),
                pengguna=self.pengguna,
                kurasi=self.kurasi,
                penemuan=self.penemuan,
                sekarang=lambda: self.kini,
            ),
            base_url="https://testserver",
        )
        self.kuki: dict[str, str] = {}
        self.segarkan()
        jalankan(self.pengguna.tetapkan_prioritas(A.pseudonim, ("K1", "K2", "K3"), sekarang=T0))
        jalankan(self.pengguna.tetapkan_prioritas(C.pseudonim, ("K1", "K2", "K3"), sekarang=T0))
        jalankan(self.pengguna.tetapkan_prioritas(B.pseudonim, ("K6", "K7", "K8"), sekarang=T0))

    def segarkan(self) -> None:
        """Sesi baru pada jam sekarang — sesi lama mati sesudah 30 menit diam."""
        for akun in (K, A, B, C):
            pengenal = secrets.token_urlsafe(32)
            jalankan(
                self.akun.buat_sesi(
                    hashlib.sha256(pengenal.encode()).digest(),
                    akun.id,
                    sekarang=self.kini,
                    kedaluwarsa_pada=self.kini + MASA_SESI,
                )
            )
            self.kuki[akun.id] = pengenal

    def pada(self, waktu: datetime) -> None:
        self.kini = waktu
        self.segarkan()

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
                    masuk_pada=self.kini,
                )
            )
        )
        return b.id_butir

    def setujui(self, *b: ButirPengetahuan) -> None:
        """Lewat rute kurator sungguhan — C-06 dari ujung ke ujung."""
        for satu in b:
            self.masukkan(satu)
            hasil = self.minta(
                "POST",
                f"/api/v1/kurasi/{satu.id_butir}/putusan",
                siapa=K,
                json={"jenis": "setujui", "catatan": "Layak tayang"},
            )
            assert hasil.status_code == 200, hasil.text

    def minta(self, metode: str, jalur: str, siapa: BarisAkun | None = A, **lain: Any) -> Any:
        tajuk = {"Cookie": f"{NAMA_KUKI}={self.kuki[siapa.id]}"} if siapa is not None else {}
        return self.klien.request(metode, jalur, headers=tajuk, **lain)

    def beranda(self, siapa: BarisAkun = A) -> Any:
        tanggapan = self.minta("GET", "/api/v1/beranda", siapa=siapa)
        assert tanggapan.status_code == 200, tanggapan.text
        return tanggapan.json()

    def ids(self, siapa: BarisAkun = A) -> list[str]:
        return [b["id_butir"] for b in self.beranda(siapa)["butir"]]


def _galat(tanggapan: Any) -> tuple[int, str, str]:
    g = tanggapan.json()["galat"]
    return tanggapan.status_code, g["kode"], g["pesan_pengguna"]


# ── keadaan ──────────────────────────────────────────────────────────


def test_tanpa_prioritas_beranda_kosong_beserta_sebabnya() -> None:
    ling = Lingkungan()
    jalankan(ling.pengguna.tetapkan_prioritas(A.pseudonim, ("K1", "K2", "K3"), sekarang=T0))
    baru = _akun("ks-020", "psd_dddddddddddddddd")
    ling.akun.pasang_akun(baru)
    ling.setujui(butir("b-1"))
    pengenal = secrets.token_urlsafe(32)
    jalankan(
        ling.akun.buat_sesi(
            hashlib.sha256(pengenal.encode()).digest(),
            baru.id,
            sekarang=T0,
            kedaluwarsa_pada=T0 + MASA_SESI,
        )
    )
    ling.kuki[baru.id] = pengenal
    assert ling.beranda(baru) == {"keadaan": "belum_ada_prioritas", "butir": []}


def test_belum_ada_butir() -> None:
    assert Lingkungan().beranda() == {"keadaan": "belum_ada_butir", "butir": []}


def test_kandidat_tidak_tampil_sebelum_disetujui_kurator() -> None:
    """C-06 ujung ke ujung, M-1."""
    ling = Lingkungan()
    ling.masukkan(butir("b-1"))
    assert ling.beranda() == {"keadaan": "belum_ada_butir", "butir": []}
    hasil = ling.minta(
        "POST",
        "/api/v1/kurasi/b-1/putusan",
        siapa=K,
        json={"jenis": "setujui", "catatan": "Layak tayang"},
    )
    assert hasil.status_code == 200
    assert ling.ids() == ["b-1"]


def test_bentuk_ringkas_d14() -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    assert ling.beranda() == {
        "keadaan": "berisi",
        "butir": [
            {
                "id_butir": "b-1",
                "kategori": "K1",
                "jenis_sumber": "riset",
                "judul": "Supervisi akademik terjadwal",
                "alasan_relevansi": "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
                "perkiraan_waktu_baca": 4,
            }
        ],
    }


# ── penyaringan dan pagu ─────────────────────────────────────────────


def test_hanya_prioritas_pengguna_dan_urutannya() -> None:
    """R-05, FR-G01: B berprioritas lain tidak melihatnya; urutan mengikuti prioritas."""
    ling = Lingkungan()
    jalankan(ling.pengguna.tetapkan_prioritas(A.pseudonim, ("K3", "K1", "K2"), sekarang=T0))
    ling.setujui(
        butir("b-k1", kategori="K1"), butir("b-k3", kategori="K3"), butir("b-k8", kategori="K8")
    )
    assert ling.ids() == ["b-k3", "b-k1"]
    assert ling.ids(B) == ["b-k8"]


def test_pagu_tiga_tetap_saat_dimuat_ulang_dan_berganti_pada_tengah_malam_wib() -> None:
    """R-05, K-2, M-6, M-7."""
    ling = Lingkungan()
    ling.setujui(*(butir(f"b-{i}") for i in range(1, 5)))
    hari_ini = ling.ids()
    assert hari_ini == ["b-1", "b-2", "b-3"]
    assert ling.ids() == hari_ini
    # 23.59 WIB — masih tanggal yang sama, meski UTC sudah lewat 16.00.
    ling.pada(datetime(2026, 10, 5, 16, 59, tzinfo=UTC))
    assert ling.ids() == hari_ini
    # 00.00 WIB tanggal 6 — butir baru, bukan yang diulang.
    ling.pada(datetime(2026, 10, 5, 17, 0, tzinfo=UTC))
    assert ling.ids() == ["b-4"]
    ling.pada(datetime(2026, 10, 6, 17, 0, tzinfo=UTC))
    assert ling.beranda() == {"keadaan": "habis", "butir": []}


def test_butir_yang_menyusul_mengisi_sisa_pagu_hari_itu() -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    assert ling.ids() == ["b-1"]
    ling.setujui(butir("b-2"), butir("b-3"), butir("b-4"))
    assert ling.ids() == ["b-1", "b-2", "b-3"]


def test_pemilihan_tidak_bergantung_pada_yang_dibuka() -> None:
    """C-14, R-08: membuka butir tidak mengubah apa yang dipilih esok hari."""
    ling = Lingkungan()
    ling.setujui(*(butir(f"b-{i}") for i in range(1, 7)))
    assert ling.ids(A) == ling.ids(C)
    for id_butir in ("b-1", "b-2"):
        assert ling.minta("GET", f"/api/v1/butir/{id_butir}").status_code == 200
    ling.pada(datetime(2026, 10, 6, 1, 0, tzinfo=UTC))
    assert ling.ids(A) == ling.ids(C) == ["b-4", "b-5", "b-6"]


def test_jalur_penjawab_tidak_menerima_prioritas_maupun_butir() -> None:
    """C-14: beranda tidak menyentuh jalur penjawaban."""
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    ling.beranda()
    ling.minta(
        "POST",
        "/api/v1/tanya",
        json={
            "pertanyaan": "Bagaimana menyusun jadwal supervisi?",
            "id_percakapan": str(ID_PERCAKAPAN),
        },
    )
    assert ling.jalur.panggilan == [("Bagaimana menyusun jadwal supervisi?", {})]


# ── penarikan dan C-07 ───────────────────────────────────────────────


def test_butir_ditarik_keluar_dari_beranda_hari_itu() -> None:
    """R-02, M-13."""
    ling = Lingkungan()
    ling.setujui(butir("b-1"), butir("b-2"))
    assert ling.ids() == ["b-1", "b-2"]
    hasil = ling.minta(
        "POST",
        "/api/v1/kurasi/b-1/tarik",
        siapa=K,
        json={"pemicu": "kekeliruan_isi_dilaporkan", "catatan": "Angka keliru"},
    )
    assert hasil.status_code == 200
    assert ling.ids() == ["b-2"]
    assert _galat(ling.minta("GET", "/api/v1/butir/b-1"))[0] == 404


def test_regulasi_tak_berlaku_tidak_tampil_meski_belum_ditarik() -> None:
    """C-07 lapis penayangan: salinan status yang dicabut menahan butir pada
    beranda dan detail, sekalipun penarikannya belum berjalan."""
    ling = Lingkungan()
    ling.setujui(butir("b-1", jenis="regulasi", status="berlaku", dokumen="permen-1"), butir("b-2"))
    assert ling.ids() == ["b-1", "b-2"]
    # Hanya status diperbarui, penarikan tidak dijalankan.
    jalankan(ling.kurasi.perbarui_status("permen-1", "dicabut"))
    assert ling.ids() == ["b-2"]
    assert _galat(ling.minta("GET", "/api/v1/butir/b-1"))[0] == 404


# ── detail ───────────────────────────────────────────────────────────


def test_detail_berbentuk_d14() -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    ling.beranda()
    tanggapan = ling.minta("GET", "/api/v1/butir/b-1")
    assert tanggapan.status_code == 200
    assert tanggapan.json() == {
        "id_butir": "b-1",
        "kategori": "K1",
        "jenis_sumber": "riset",
        "judul": "Supervisi akademik terjadwal",
        "alasan_relevansi": "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
        "perkiraan_waktu_baca": 4,
        "inti_temuan": "Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
        "implikasi_tindakan": ["Susun jadwal supervisi satu semester."],
        "tenggat_terkait": None,
        "boleh_teks_penuh": True,
        "sumber": SUMBER,
    }
    assert K.pseudonim not in tanggapan.text and "Layak tayang" not in tanggapan.text


def test_lisensi_tertutup_tanpa_teks_penuh() -> None:
    """C-02, M-9: ditetapkan peladen, bukan disimpulkan layar."""
    ling = Lingkungan()
    ling.setujui(butir("b-1", lisensi="Hak cipta dilindungi"))
    ling.beranda()
    assert ling.minta("GET", "/api/v1/butir/b-1").json()["boleh_teks_penuh"] is False


def test_detail_hanya_bagi_butir_yang_pernah_tayang_baginya() -> None:
    """M-12: satu bentuk 404 bagi tak dikenal, belum tayang baginya, dan kandidat."""
    ling = Lingkungan()
    ling.setujui(butir("b-1"), butir("b-k8", kategori="K8"))
    ling.masukkan(butir("b-kandidat"))
    ling.beranda()
    for id_butir in ("b-tak-ada", "b-k8", "b-kandidat"):
        assert _galat(ling.minta("GET", f"/api/v1/butir/{id_butir}")) == (
            404,
            "SUMBER_TIDAK_ADA",
            PESAN_BUTIR_TIDAK_ADA,
        )


# ── belum relevan ────────────────────────────────────────────────────


def test_belum_relevan_mengeluarkan_butir_untuk_seterusnya() -> None:
    """R-07, M-8."""
    ling = Lingkungan()
    ling.setujui(*(butir(f"b-{i}") for i in range(1, 4)))
    ling.beranda()
    tanggapan = ling.minta(
        "POST", "/api/v1/butir/b-2/tolak", json={"alasan": "Belum menjadi prioritas semester ini"}
    )
    assert tanggapan.status_code == 200
    assert [b["id_butir"] for b in tanggapan.json()["butir"]] == ["b-1", "b-3"]
    assert ling.ids() == ["b-1", "b-3"]
    assert jalankan(ling.penemuan.ditolak(A.pseudonim)) == {"b-2"}


def test_seluruh_butir_hari_ini_ditolak_berarti_habis() -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    ling.beranda()
    tanggapan = ling.minta("POST", "/api/v1/butir/b-1/tolak", json={"alasan": "Tidak sesuai"})
    assert tanggapan.json() == {"keadaan": "habis", "butir": []}


@pytest.mark.parametrize(
    "badan",
    [{"alasan": "  "}, {"alasan": f"Hubungi {NIK}"}, {}, {"alasan": "x", "lain": 1}, ["x"]],
)
def test_alasan_berbentuk_salah_ditolak(badan: object) -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    ling.beranda()
    tanggapan = ling.minta("POST", "/api/v1/butir/b-1/tolak", json=badan)
    assert _galat(tanggapan) == (400, "VALIDASI_GAGAL", PESAN_ALASAN_TIDAK_SAH)
    assert NIK not in tanggapan.text
    assert ling.ids() == ["b-1"]


def test_tolak_menuntut_json_dan_butir_yang_tayang_baginya() -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"), butir("b-k8", kategori="K8"))
    ling.beranda()
    assert (
        _galat(ling.minta("POST", "/api/v1/butir/b-1/tolak", content='{"alasan": "x"}'))[0] == 400
    )
    assert _galat(ling.minta("POST", "/api/v1/butir/b-k8/tolak", json={"alasan": "x"}))[0] == 404


# ── peran ────────────────────────────────────────────────────────────


def test_rute_penemuan_hanya_bagi_pengguna() -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    for metode, jalur, badan in (
        ("GET", "/api/v1/beranda", None),
        ("GET", "/api/v1/butir/b-1", None),
        ("POST", "/api/v1/butir/b-1/tolak", {"alasan": "x"}),
    ):
        assert _galat(ling.minta(metode, jalur, siapa=K, json=badan))[:2] == (
            403,
            "TIDAK_BERWENANG",
        )
        assert _galat(ling.minta(metode, jalur, siapa=None, json=badan))[:2] == (
            401,
            "TIDAK_TERAUTENTIKASI",
        )


def test_penemuan_tanpa_penyimpan_pengguna_tidak_dapat_disusun() -> None:
    kurasi = KurasiMemori()
    with pytest.raises(ValueError):
        susun_aplikasi(
            jalur=JalurPencatat(),
            identitas=PenentuSesi(AkunMemori()),
            riwayat=RiwayatMemori(),
            penemuan=PenemuanMemori(kurasi),
        )


def test_pesan_penemuan_memenuhi_c13() -> None:
    assert not kalimat_terlalu_panjang(PESAN_ALASAN_TIDAK_SAH)


def test_badan_json_rusak_ditolak() -> None:
    ling = Lingkungan()
    ling.setujui(butir("b-1"))
    ling.beranda()
    for jalur, siapa, pesan in (
        ("/api/v1/butir/b-1/tolak", A, PESAN_ALASAN_TIDAK_SAH),
        ("/api/v1/kurasi/b-1/tarik", K, None),
    ):
        tajuk = {"Cookie": f"{NAMA_KUKI}={ling.kuki[siapa.id]}", "Content-Type": "application/json"}
        tanggapan = ling.klien.request("POST", jalur, headers=tajuk, content="{rusak")
        status, kode, isi = _galat(tanggapan)
        assert (status, kode) == (400, "VALIDASI_GAGAL")
        if pesan is not None:
            assert isi == pesan
