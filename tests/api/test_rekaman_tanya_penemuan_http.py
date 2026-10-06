"""Peristiwa Tanya dan penemuan lewat HTTP — T-5 fitur 034, R-03, R-06, R-08, R-09; K-6.

Lingkungannya milik `test_rekaman_http.py`; butir disetujui lewat rute kurator
sungguhan, sehingga yang tampil di beranda lahir dari gerbang kurasi (C-06).
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

import pytest
from src.api.autentikasi import MASA_SESI, NAMA_KUKI
from src.api.galat import LOG_OPERASIONAL
from src.api.tanya import AlasanBerhenti, HasilTanya
from src.kamus.segmen import StatusKeberlakuan
from src.penyimpanan.akun import BarisAkun
from src.penyimpanan.kurasi import BarisKandidat
from src.penyimpanan.telemetri import TelemetriMemori
from src.rag.jawaban.tanggapan import Sitasi, StatusDasar, Tanggapan
from tests.api.test_aplikasi import PENAFIAN, VERSI, JalurPalsu
from tests.api.test_kurasi_http import SUMBER, butir
from tests.api.test_rekaman_http import T0, A, Lingkungan, TelemetriRusak
from tests.konftes_asinkron import jalankan

K = BarisAkun(
    id="kr-001",
    pseudonim="psd_kkkkkkkkkkkkkkkk",
    peran="kurator",
    status_aktif=True,
    turunan_sandi="scrypt$16$8$1$AAAA$AAAA",
    gagal_beruntun=0,
    ditahan_sampai=None,
)
PERTANYAAN = "Bagaimana menyusun jadwal supervisi akademik yang adil bagi semua guru?"
ALASAN = "Sekolah kami sedang fokus pada akreditasi bulan ini."


def _sitasi(id_dokumen: str) -> Sitasi:
    return Sitasi(
        id_dokumen=id_dokumen,
        judul="Panduan Supervisi Akademik",
        penerbit="Kemendikdasmen",
        tahun=2025,
        bagian="Bab II",
        status_keberlakuan=StatusKeberlakuan.BERLAKU,
    )


def _jawaban(alasan: AlasanBerhenti | None = None) -> JalurPalsu:
    if alasan is None:
        tanggapan = Tanggapan(
            id_pesan="p1",
            status_dasar=StatusDasar.KUAT,
            penjelasan="Susun jadwal bergilir yang diumumkan sejak awal semester.",
            sitasi=(_sitasi("dok-1"), _sitasi("dok-2")),
            penafian=PENAFIAN,
            versi=VERSI,
        )
    else:
        tanggapan = Tanggapan(
            id_pesan="p1", status_dasar=StatusDasar.TIDAK_DITEMUKAN, penafian=PENAFIAN, versi=VERSI
        )
    return JalurPalsu(HasilTanya(tanggapan=tanggapan, alasan_berhenti=alasan))


class Alur(Lingkungan):
    """Lingkungan T-4 ditambah kurator dan langkah-langkah alur pengguna."""

    def __init__(self, **lain: Any) -> None:
        lain.setdefault("jalur", _jawaban())
        super().__init__(**lain)
        self.akun.pasang_akun(K)
        jalankan(self.pengguna.tetapkan_prioritas(A.pseudonim, ("K1", "K2", "K3"), sekarang=T0))

    def setujui(self, *id_butir: str) -> None:
        pengenal = secrets.token_urlsafe(32)
        jalankan(
            self.akun.buat_sesi(
                hashlib.sha256(pengenal.encode()).digest(),
                K.id,
                sekarang=self.kini,
                kedaluwarsa_pada=self.kini + MASA_SESI,
            )
        )
        for i in id_butir:
            b = butir(i)
            jalankan(
                self.kurasi.tambah_kandidat(
                    BarisKandidat(
                        id_butir=i,
                        butir=b.model_dump(mode="json"),
                        sumber=SUMBER,
                        id_dokumen_sumber=b.id_dokumen_sumber,
                        kategori=b.kategori.value,
                        status_keberlakuan=None,
                        masuk_pada=self.kini,
                    )
                )
            )
            hasil = self.klien.post(
                f"/api/v1/kurasi/{i}/putusan",
                json={"jenis": "setujui", "catatan": "Layak tayang"},
                headers={"Cookie": f"{NAMA_KUKI}={pengenal}"},
            )
            self.klien.cookies.clear()
            assert hasil.status_code == 200, hasil.text

    def tanya(self, pertanyaan: str = PERTANYAAN) -> Any:
        return self.minta(
            "POST",
            "/api/v1/tanya",
            json={"pertanyaan": pertanyaan, "id_percakapan": str(uuid.uuid4())},
        )

    def beranda(self) -> Any:
        return self.minta("GET", "/api/v1/beranda")

    def buka(self, id_butir: str) -> Any:
        return self.minta("GET", f"/api/v1/butir/{id_butir}")

    def tolak(self, id_butir: str, alasan: str = ALASAN) -> Any:
        return self.minta("POST", f"/api/v1/butir/{id_butir}/tolak", json={"alasan": alasan})

    def alur(self) -> list[Any]:
        """Masuk → tanya → beranda → butir → belum relevan → keluar."""
        self.setujui("btr-1", "btr-2")
        langkah = [self.masuk()]
        self.kini += timedelta(minutes=1)
        langkah.append(self.tanya())
        self.kini += timedelta(minutes=1)
        langkah.append(self.beranda())
        self.kini += timedelta(minutes=17)
        langkah.append(self.buka("btr-1"))
        self.kini += timedelta(minutes=1)
        langkah.append(self.tolak("btr-2"))
        self.kini += timedelta(minutes=1)
        langkah.append(self.keluar())
        return langkah

    def properti(self, jenis: str) -> list[dict[str, Any]]:
        return [p.properti for p in self.peristiwa() if p.jenis == jenis]


def _sama(tanggapan: Any) -> tuple[int, bytes]:
    return tanggapan.status_code, tanggapan.content


# ── C-04 ujung ke ujung ─────────────────────────────────────────────


@pytest.mark.parametrize("keadaan", ["belum_diminta", "ditolak", "dicabut"])
def test_alur_penuh_tanpa_persetujuan_menyimpan_nol_peristiwa(keadaan: str) -> None:
    ling = Alur(jalur=_jawaban(AlasanBerhenti.DITAHAN_VALIDATOR))
    if keadaan != "belum_diminta":
        ling.setuju(disetujui=keadaan == "dicabut")
    if keadaan == "dicabut":
        ling.kini += timedelta(minutes=1)
        assert jalankan(ling.pengguna.cabut_persetujuan(A.pseudonim, sekarang=ling.kini))
    for t in ling.alur():
        assert t.status_code in (200, 204), t.text
    assert jalankan(ling.telemetri.milik(A.pseudonim)) == ()
    assert ling.telemetri._baris == []


def test_alur_penuh_dengan_persetujuan_mencatat_sembilan_kode() -> None:
    ling = Alur(jalur=_jawaban(AlasanBerhenti.DITAHAN_VALIDATOR))
    ling.setuju()
    ling.masuk()
    ling.keluar()
    ling.kini += timedelta(hours=25)
    ling.alur()
    assert ling.jenis() == [
        "session_start",
        "session_end",
        "return_visit",
        "session_start",
        "question_asked",
        "answer_served",
        "answer_rejected_validator",
        "discovery_served",
        "discovery_served",
        "discovery_opened",
        "discovery_dismissed",
        "session_end",
    ]


def test_sesudah_mencabut_permintaan_berikutnya_tidak_menambah_peristiwa() -> None:
    ling = Alur()
    ling.setujui("btr-1")
    ling.setuju()
    ling.masuk()
    ling.tanya()
    sebelum = len(ling.peristiwa())
    ling.kini += timedelta(minutes=1)
    ling.cabut()
    ling.tanya()
    ling.beranda()
    ling.buka("btr-1")
    ling.tolak("btr-1")
    ling.keluar()
    assert len(ling.peristiwa()) == sebelum


# ── properti ────────────────────────────────────────────────────────


def test_peristiwa_tanya_membawa_ukuran_dan_versi_model_jawaban() -> None:
    """M-9: `answer_served` yang membawa `tanpa_model` kehilangan versi model."""
    ling = Alur()
    ling.setuju()
    ling.masuk()
    ling.kini += timedelta(minutes=1)
    assert ling.tanya().status_code == 200
    _, tanya, jawab = ling.peristiwa()
    assert (tanya.jenis, tanya.properti) == ("question_asked", {"panjang_pertanyaan": 71})
    assert len(PERTANYAAN) == 71
    assert tanya.versi_model == "tanpa_model"
    assert jawab.jenis == "answer_served"
    assert jawab.versi_model == VERSI.model
    waktu = jawab.properti.pop("waktu_tanggap_ms")
    assert isinstance(waktu, int) and waktu >= 0
    assert jawab.properti == {"status_dasar": "kuat", "jumlah_sitasi": 2}
    assert {tanya.waktu, jawab.waktu} == {ling.kini}


def test_ditahan_validator_mencatat_alasan_berhentinya() -> None:
    ling = Alur(jalur=_jawaban(AlasanBerhenti.DITAHAN_VALIDATOR))
    ling.setuju()
    ling.masuk()
    ling.tanya()
    (tolak,) = [p for p in ling.peristiwa() if p.jenis == "answer_rejected_validator"]
    assert tolak.properti == {"alasan_berhenti": "ditahan_validator"}
    assert tolak.versi_model == VERSI.model
    assert ling.properti("answer_served")[0]["status_dasar"] == "tidak_ditemukan"


@pytest.mark.parametrize(
    "alasan",
    [
        AlasanBerhenti.DI_LUAR_DOMAIN,
        AlasanBerhenti.BUKTI_TIDAK_CUKUP,
        AlasanBerhenti.KELUARAN_TIDAK_TERBACA,
        AlasanBerhenti.MENUNGGU_PEMERIKSAAN_MODEL,
    ],
)
def test_alasan_berhenti_lain_bukan_penolakan_validator(alasan: AlasanBerhenti) -> None:
    ling = Alur(jalur=_jawaban(alasan))
    ling.setuju()
    ling.masuk()
    ling.tanya()
    assert ling.jenis() == ["session_start", "question_asked", "answer_served"]


def test_teks_pertanyaan_dan_alasan_tidak_pernah_tersimpan() -> None:
    """R-06, M-6: yang tersimpan ukurannya, bukan isinya."""
    ling = Alur()
    ling.setuju()
    ling.alur()
    tersimpan = repr(ling.telemetri._baris)
    for teks in (PERTANYAAN, ALASAN):
        for penggal in (teks, teks[:20], teks.split()[1]):
            assert penggal not in tersimpan
    assert ling.properti("discovery_dismissed") == [
        {"id_butir": "btr-2", "panjang_alasan": len(ALASAN)}
    ]


def test_butir_baru_tercatat_sekali_beserta_jenis_dan_kategorinya() -> None:
    """M-10: muat ulang beranda tidak mencatat ulang butir yang sama."""
    ling = Alur()
    ling.setujui("btr-1", "btr-2")
    ling.setuju()
    ling.masuk()
    for _ in range(3):
        assert ling.beranda().status_code == 200
    ling.setujui("btr-3")
    ling.beranda()
    ling.beranda()
    assert ling.properti("discovery_served") == [
        {"id_butir": i, "jenis_sumber": "riset", "kategori": "K1"}
        for i in ("btr-1", "btr-2", "btr-3")
    ]


def test_butir_dibuka_mencatat_menit_sejak_tayang() -> None:
    ling = Alur()
    ling.setujui("btr-1")
    ling.setuju()
    ling.masuk()
    ling.beranda()
    ling.kini += timedelta(minutes=17, seconds=59)
    assert ling.buka("btr-1").status_code == 200
    ling.kini += timedelta(minutes=3)
    ling.buka("btr-1")
    assert ling.properti("discovery_opened") == [
        {"id_butir": "btr-1", "menit_sejak_tayang": 17},
        {"id_butir": "btr-1", "menit_sejak_tayang": 20},
    ]


def test_permintaan_yang_ditolak_tidak_merekam() -> None:
    ling = Alur()
    ling.setujui("btr-1")
    ling.setuju()
    ling.masuk()
    sebelum = ling.jenis()
    assert ling.tanya(pertanyaan="   ").status_code == 400
    assert ling.tanya(pertanyaan="NIK saya 3201234567890001, bagaimana?").status_code == 400
    assert ling.buka("btr-1").status_code == 404
    assert ling.tolak("btr-1").status_code == 404
    ling.beranda()
    assert ling.tolak("btr-1", alasan="NIK 3201234567890001").status_code == 400
    assert ling.jenis() == [*sebelum, "discovery_served"]


# ── R-03 · tanggapan sama ───────────────────────────────────────────


def test_tanggapan_setiap_langkah_sama_dengan_dan_tanpa_persetujuan() -> None:
    dengan, tanpa = Alur(), Alur()
    dengan.setuju()
    hasil_dengan = [_sama(t) for t in dengan.alur()]
    hasil_tanpa = [_sama(t) for t in tanpa.alur()]
    assert hasil_dengan == hasil_tanpa
    assert len(dengan.peristiwa()) == 8
    assert tanpa.peristiwa() == []


# ── R-07 · galat penyimpan ──────────────────────────────────────────


def test_penyimpan_rusak_tidak_mengubah_tanggapan_alur(caplog: pytest.LogCaptureFixture) -> None:
    utuh, rusak = Alur(), Alur(telemetri=TelemetriRusak())
    for ling in (utuh, rusak):
        ling.setuju()
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        assert [_sama(t) for t in rusak.alur()] == [_sama(t) for t in utuh.alur()]
    catatan = " ".join(r.getMessage() for r in caplog.records)
    for kode in ("question_asked", "answer_served", "discovery_served", "discovery_opened"):
        assert kode in catatan
    assert PERTANYAAN[:20] not in catatan
    assert A.pseudonim not in catatan


# ── R-09 · pemilihan tidak membaca peristiwa ────────────────────────


class TelemetriPengamat(TelemetriMemori):
    """Menghitung pembacaan — penulisan tetap berjalan."""

    def __init__(self) -> None:
        super().__init__()
        self.dibaca = 0

    async def terakhir(self, pemilik: str, jenis: str) -> datetime | None:
        self.dibaca += 1
        return await super().terakhir(pemilik, jenis)

    async def milik(self, pemilik: str) -> tuple[Any, ...]:
        self.dibaca += 1
        return await super().milik(pemilik)


def test_tanya_dan_penemuan_tidak_membaca_peristiwa() -> None:
    """C-14: telemetri direkam, tidak dipakai menyesuaikan beranda maupun jawaban."""
    telemetri = TelemetriPengamat()
    ling = Alur(telemetri=telemetri)
    ling.setujui("btr-1", "btr-2")
    ling.setuju()
    ling.masuk()
    dibaca_saat_masuk = telemetri.dibaca
    ling.tanya()
    ling.beranda()
    ling.buka("btr-1")
    ling.tolak("btr-2")
    assert telemetri.dibaca == dibaca_saat_masuk
    assert ling.jalur.pertanyaan_terakhir == PERTANYAAN


# ── K-7 · pengambilan latar bukan butir dibuka (KB-199, TK-74) ──────


@pytest.mark.parametrize(
    ("tajuk", "tercatat"),
    [
        ({"X-Tujuan": "salinan"}, 0),
        ({"x-tujuan": "salinan"}, 0),
        ({}, 1),
        ({"X-Tujuan": "lain"}, 1),
        ({"X-Tujuan": "Salinan"}, 1),
    ],
)
def test_pengambilan_latar_bagi_salinan_tidak_tercatat_dibuka(
    tajuk: dict[str, str], tercatat: int
) -> None:
    """M-11: peladen yang mengabaikan tajuk mencatat setiap muatan beranda sebagai dibuka."""
    ling = Alur()
    ling.setujui("btr-1")
    ling.setuju()
    ling.masuk()
    ling.beranda()
    tanggapan = ling.minta("GET", "/api/v1/butir/btr-1", headers_tambahan=tajuk)
    assert tanggapan.status_code == 200
    assert _sama(tanggapan) == _sama(ling.buka("btr-1"))
    assert len(ling.properti("discovery_opened")) == tercatat + 1
