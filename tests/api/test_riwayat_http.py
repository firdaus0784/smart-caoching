"""`/tanya` mencatat giliran; kepemilikan; data pribadi — T-6 fitur 028.

R-01, R-02, R-03, R-07, R-15, R-16; TK-65, TK-67, TK-68.

**Dua identitas pada satu penyimpan.** Kepemilikan hanya dapat diuji bila ada
pemilik kedua: dengan satu pemilik, penyimpan yang mengembalikan seluruh
percakapan lulus setiap uji (bentuk TK-67 persis).

Penolakan diperiksa bentuknya, bukan hanya statusnya: "milik orang lain" dan
"tidak dikenal" wajib **sama persis** kecuali `id_jejak`.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from src.api.aplikasi import PESAN_DATA_PRIBADI, PESAN_TIDAK_ADA, susun_aplikasi
from src.api.galat import LOG_OPERASIONAL
from src.api.peran import Peran
from src.api.tanya import HasilTanya
from src.penyimpanan.riwayat import RiwayatMemori
from tests.api.test_aplikasi import IdentitasTetap, _tanggapan

T0 = datetime(2026, 9, 29, 7, 30, tzinfo=UTC)


class JalurPencatat:
    """Mencatat setiap panggilan beserta argumen kata kuncinya (R-07)."""

    def __init__(self) -> None:
        self.panggilan: list[tuple[str, dict[str, object]]] = []

    async def jawab(self, pertanyaan: str, **argumen: object) -> HasilTanya:
        self.panggilan.append((pertanyaan, argumen))
        return HasilTanya(tanggapan=_tanggapan(id_pesan=f"pesan-{len(self.panggilan)}"))


class Jam:
    def __init__(self) -> None:
        self.saat = T0

    def __call__(self) -> datetime:
        self.saat += timedelta(minutes=1)
        return self.saat


class Dunia:
    """Dua pengguna, satu penyimpan riwayat, satu jalur."""

    def __init__(self) -> None:
        self.riwayat = RiwayatMemori()
        self.jalur = JalurPencatat()
        jam = Jam()

        def klien(pemilik: str) -> TestClient:
            return TestClient(
                susun_aplikasi(
                    jalur=self.jalur,
                    identitas=IdentitasTetap(Peran.PENGGUNA, pemilik=pemilik),
                    riwayat=self.riwayat,
                    sekarang=jam,
                )
            )

        self.a = klien("ps_pengguna_a")
        self.b = klien("ps_pengguna_b")


def _tanya(klien: TestClient, id_percakapan: object, pertanyaan: str = "Bagaimana supervisi?"):  # type: ignore[no-untyped-def]
    return klien.post(
        "/api/v1/tanya", json={"pertanyaan": pertanyaan, "id_percakapan": str(id_percakapan)}
    )


def _tanpa_jejak(tanggapan) -> dict[str, object]:  # type: ignore[no-untyped-def]
    badan = tanggapan.json()
    badan["galat"].pop("id_jejak")
    return {"status": tanggapan.status_code, **badan}


# ── R-01 · jawaban tercatat ─────────────────────────────────────────────


def test_jawaban_tercatat_sebagai_giliran_dengan_id_pesannya() -> None:
    d = Dunia()
    p = uuid.uuid4()
    tanggapan = _tanya(d.a, p, "Bagaimana menyusun jadwal supervisi?")
    assert tanggapan.status_code == 200

    isi = d.a.get(f"/api/v1/percakapan/{p}").json()
    assert isi["id_percakapan"] == str(p)
    assert len(isi["giliran"]) == 1
    giliran = isi["giliran"][0]
    assert giliran["pertanyaan"] == "Bagaimana menyusun jadwal supervisi?"
    assert giliran["id_pesan"] == tanggapan.json()["id_pesan"]
    assert set(giliran) == {"pertanyaan", "id_pesan", "waktu"}, "tanpa salinan tanggapan (C-07)"


def test_tanggapan_terkirim_tercatat_sebagai_catatan_audit() -> None:
    """Fitur 036, P-1 A: yang tercatat persis yang terkirim — dan hanya itu."""
    d = Dunia()
    tanggapan = _tanya(d.a, uuid.uuid4())
    assert tanggapan.status_code == 200
    badan = tanggapan.json()
    baris = d.riwayat.baris_pesan()[badan["id_pesan"]]
    assert dict(baris.tanggapan) == badan
    assert "tingkat_keyakinan" not in baris.tanggapan


def test_jawaban_yang_ditolak_tidak_tercatat_sebagai_tanggapan() -> None:
    d = Dunia()
    p = uuid.uuid4()
    assert _tanya(d.a, p).status_code == 200
    assert _tanya(d.b, p).status_code == 404
    assert len(d.riwayat.baris_pesan()) == 1


def test_percakapan_berlanjut_dan_daftar_terbaru_lebih_dulu() -> None:
    d = Dunia()
    lama, baru = uuid.uuid4(), uuid.uuid4()
    _tanya(d.a, lama, "Pertama")
    _tanya(d.a, baru, "Kedua")
    _tanya(d.a, lama, "Lanjutan percakapan lama")

    assert d.a.get("/api/v1/percakapan").json() == {"percakapan": [str(baru), str(lama)]}
    giliran = d.a.get(f"/api/v1/percakapan/{lama}").json()["giliran"]
    assert [g["pertanyaan"] for g in giliran] == ["Pertama", "Lanjutan percakapan lama"]


# ── R-07 · jawaban tidak dipengaruhi riwayat ────────────────────────────


def test_jalur_hanya_menerima_pertanyaan_tanpa_giliran_sebelumnya() -> None:
    """C-14: jawaban yang menyesuaikan diri dengan riwayat pertanyaan
    seseorang adalah personalisasi berbasis riwayat."""
    d = Dunia()
    p = uuid.uuid4()
    _tanya(d.a, p, "Pertanyaan pertama")
    _tanya(d.a, p, "Pertanyaan kedua")

    assert d.jalur.panggilan == [("Pertanyaan pertama", {}), ("Pertanyaan kedua", {})]


# ── R-02, R-03 · kepemilikan (TK-67) ────────────────────────────────────


def test_pengguna_lain_tidak_melihat_daftar() -> None:
    d = Dunia()
    _tanya(d.a, uuid.uuid4())
    assert d.b.get("/api/v1/percakapan").json() == {"percakapan": []}


def test_membaca_percakapan_orang_lain_sama_dengan_tidak_dikenal() -> None:
    d = Dunia()
    p = uuid.uuid4()
    _tanya(d.a, p)

    orang_lain = d.b.get(f"/api/v1/percakapan/{p}")
    tidak_dikenal = d.b.get(f"/api/v1/percakapan/{uuid.uuid4()}")

    assert orang_lain.status_code == 404
    assert _tanpa_jejak(orang_lain) == _tanpa_jejak(tidak_dikenal)
    assert orang_lain.json()["galat"]["kode"] == "SUMBER_TIDAK_ADA"
    assert orang_lain.json()["galat"]["pesan_pengguna"] == PESAN_TIDAK_ADA


def test_menulis_ke_percakapan_orang_lain_ditolak_sebelum_menjawab() -> None:
    d = Dunia()
    p = uuid.uuid4()
    _tanya(d.a, p, "Milik A")
    panggilan_sebelum = len(d.jalur.panggilan)

    ditolak = _tanya(d.b, p, "Sisipan B")

    assert ditolak.status_code == 404
    assert _tanpa_jejak(ditolak) == _tanpa_jejak(d.b.get(f"/api/v1/percakapan/{uuid.uuid4()}"))
    assert len(d.jalur.panggilan) == panggilan_sebelum, "jalur tidak boleh dipanggil"
    giliran = d.a.get(f"/api/v1/percakapan/{p}").json()["giliran"]
    assert [g["pertanyaan"] for g in giliran] == ["Milik A"]


def test_pengenal_bukan_uuid_pada_rute_baca_sama_dengan_tidak_dikenal() -> None:
    d = Dunia()
    tanggapan = d.a.get("/api/v1/percakapan/bukan-uuid")
    assert _tanpa_jejak(tanggapan) == _tanpa_jejak(d.a.get(f"/api/v1/percakapan/{uuid.uuid4()}"))


# ── R-16 · bentuk pengenal ──────────────────────────────────────────────


def test_pengenal_wajib_uuid_versi_4() -> None:
    d = Dunia()
    for salah in ("1", "bukan-uuid", str(uuid.uuid1()), str(uuid.UUID(int=0))):
        tanggapan = _tanya(d.a, salah)
        assert tanggapan.status_code == 400, salah
        assert tanggapan.json()["galat"]["kode"] == "VALIDASI_GAGAL"
    tanpa = d.a.post("/api/v1/tanya", json={"pertanyaan": "x"})
    assert tanpa.status_code == 400
    assert d.jalur.panggilan == []


# ── R-15 · data pribadi (TK-68) ─────────────────────────────────────────


def test_pertanyaan_berdata_pribadi_ditolak_sebelum_jalur(caplog) -> None:  # type: ignore[no-untyped-def]
    d = Dunia()
    p = uuid.uuid4()
    with caplog.at_level(logging.DEBUG):
        tanggapan = _tanya(d.a, p, "NIK guru saya 3201234567890123, bagaimana mutasinya?")

    assert tanggapan.status_code == 400
    galat = tanggapan.json()["galat"]
    assert galat["kode"] == "VALIDASI_GAGAL"
    assert galat["pesan_pengguna"] == PESAN_DATA_PRIBADI
    assert "3201234567890123" not in tanggapan.text
    assert d.jalur.panggilan == [], "tidak sampai ke jalur maupun model"
    assert d.a.get("/api/v1/percakapan").json() == {"percakapan": []}, "tidak tercatat"
    assert "3201234567890123" not in caplog.text
    assert any(r.name == LOG_OPERASIONAL.name for r in caplog.records)


class RiwayatBalapan(RiwayatMemori):
    """Pemilik lain membuka pengenal yang sama **di antara** `dapat_ditulis`
    dan `catat` — keadaan yang hanya terjadi pada balapan, dan karena itu
    ditiru di sini alih-alih ditunggu terjadi."""

    async def dapat_ditulis(self, *, pemilik: str, id_percakapan: uuid.UUID) -> bool:
        hasil = await super().dapat_ditulis(pemilik=pemilik, id_percakapan=id_percakapan)
        await super().catat(
            pemilik="ps_penyela",
            id_percakapan=id_percakapan,
            pertanyaan="Penyela",
            id_pesan="pesan-penyela",
            waktu=T0,
            tanggapan={
                "id_pesan": "pesan-penyela",
                "status_dasar": "kuat",
                "versi": {"model": "m"},
            },
        )
        return hasil


def test_balapan_pemilik_tidak_mengirim_jawaban_yang_tak_tercatat() -> None:
    """Jawaban yang tampil tanpa tercatat membuat riwayat berbohong (R-01)."""
    jalur = JalurPencatat()
    klien = TestClient(
        susun_aplikasi(
            jalur=jalur,
            identitas=IdentitasTetap(Peran.PENGGUNA, pemilik="ps_pengguna_a"),
            riwayat=RiwayatBalapan(),
        )
    )
    tanggapan = _tanya(klien, uuid.uuid4())

    assert tanggapan.status_code == 404
    assert tanggapan.json()["galat"]["kode"] == "SUMBER_TIDAK_ADA"
    assert "id_pesan" not in tanggapan.text
