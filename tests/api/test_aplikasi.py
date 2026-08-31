"""Uji lapisan HTTP — fitur 023, R-01 s.d. R-07.

## Yang diuji di sini, dan yang sengaja tidak

Yang diuji: **penerjemahannya**. Permintaan menjadi panggilan, hasil menjadi
tanggapan, peran menjadi tolakan. Jalur penjawabannya sendiri sudah diuji
fitur 021 dan tidak diulang di sini — mengulangnya menghasilkan uji yang lulus
karena kolaboratornya palsu, bukan karena perilakunya benar.

Kolaborator karena itu dipalsukan pada tingkat `Jalur`, bukan pada tingkat
HTTP. `JalurPalsu` mencatat berapa kali ia dipanggil, dan hitungan itulah yang
membuat R-01 dapat diuji: "ditolak sebelum jalur tersentuh" adalah pernyataan
tentang **urutan**, dan urutan hanya terlihat bila ada yang menghitung.

## Mengapa `TestClient`, bukan peladen sungguhan

Prinsip fitur 021 tetap berlaku: uji yang menuntut peladen berjalan dan porta
terbuka adalah uji yang dilewati orang ketika sedang buru-buru. `TestClient`
memanggil aplikasi di dalam proses yang sama.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.api.aplikasi import PenentuIdentitas, susun_aplikasi
from src.api.peran import PETA_RUTE, Peran
from src.api.tanya import AlasanBerhenti, HasilTanya
from src.rag.jawaban.tanggapan import StatusDasar, Tanggapan, Versi

VERSI = Versi(model="uji-1", indeks="uji-1", kode="uji-1")
PENAFIAN = "Jawaban ini bukan pengganti keputusan Anda sebagai kepala sekolah."


def _tanggapan(status: StatusDasar = StatusDasar.KUAT, id_pesan: str = "p1") -> Tanggapan:
    return Tanggapan(
        id_pesan=id_pesan,
        status_dasar=status,
        penjelasan="Contoh penjelasan singkat." if status is StatusDasar.KUAT else "",
        penafian=PENAFIAN,
        versi=VERSI,
    )


class JalurPalsu:
    """Mencatat berapa kali dipanggil — itulah yang membuat R-01 dapat diuji."""

    def __init__(self, hasil: HasilTanya) -> None:
        self._hasil = hasil
        self.jumlah_panggilan = 0
        self.pertanyaan_terakhir: str | None = None

    def jawab(self, pertanyaan: str, **_: object) -> HasilTanya:
        self.jumlah_panggilan += 1
        self.pertanyaan_terakhir = pertanyaan
        return self._hasil


class IdentitasTetap:
    """Penentu identitas paling sederhana yang memenuhi `PenentuIdentitas`."""

    def __init__(self, peran: Peran) -> None:
        self._peran = peran

    def peran(self, _permintaan: object) -> Peran:
        return self._peran


def _aplikasi(
    *,
    hasil: HasilTanya | None = None,
    peran: Peran = Peran.PENGGUNA,
    percakapan: dict[str, object] | None = None,
) -> tuple[FastAPI, JalurPalsu]:
    jalur = JalurPalsu(hasil or HasilTanya(tanggapan=_tanggapan()))
    aplikasi = susun_aplikasi(
        jalur=jalur,
        identitas=IdentitasTetap(peran),
        percakapan=percakapan if percakapan is not None else {},
    )
    return aplikasi, jalur


# ── A-1 · penyusun aplikasi ─────────────────────────────────────────


def test_aplikasi_tanpa_penentu_identitas_gagal_disusun() -> None:
    """R-04. Bukan ditolak saat jalan — tidak dapat disusun sama sekali."""
    with pytest.raises(TypeError):
        susun_aplikasi(jalur=JalurPalsu(HasilTanya(tanggapan=_tanggapan())), percakapan={})  # type: ignore[call-arg]


def test_rute_bawaan_kerangka_seluruhnya_mati() -> None:
    """R-07. Ketiganya menyala secara baku pada FastAPI.

    Rute yang menyala tanpa seorang pun mendaftarkannya adalah pelanggaran
    AG-02 yang paling mungkin luput — tidak ada baris kode yang dapat dibaca
    sebagai penyebabnya.
    """
    aplikasi, _ = _aplikasi()
    klien = TestClient(aplikasi)
    for jalur in ("/docs", "/redoc", "/openapi.json"):
        assert klien.get(jalur).status_code == 404, jalur


def test_setiap_rute_terdaftar_ada_pada_peta_rute_d14() -> None:
    """R-07. Peta rute `peran.py` yang berlaku, bukan untai pada dekorator."""
    aplikasi, _ = _aplikasi()
    d14 = {(r.metode, r.jalur) for r in PETA_RUTE}
    terdaftar = {
        (metode, rute.path)
        for rute in aplikasi.routes
        for metode in getattr(rute, "methods", set()) or set()
        if metode != "HEAD"
    }
    assert terdaftar, "aplikasi tidak mendaftarkan rute apa pun"
    assert terdaftar <= d14, f"rute di luar D-14: {sorted(terdaftar - d14)}"


# ── A-2 · gerbang peran ─────────────────────────────────────────────


def test_peran_tidak_berhak_ditolak() -> None:
    """R-01."""
    aplikasi, _ = _aplikasi(peran=Peran.ANOTATOR)
    tanggapan = TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "Apa itu RKAS?"})
    assert tanggapan.status_code == 403


def test_jalur_tidak_tersentuh_ketika_peran_ditolak() -> None:
    """R-01 — pernyataan tentang **urutan**, bukan tentang hasil.

    Tanpa uji ini, memanggil `boleh()` sesudah `Jalur.jawab()` akan lulus
    seluruh uji lain: tanggapannya tetap 403.
    """
    aplikasi, jalur = _aplikasi(peran=Peran.ANOTATOR)
    TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "Apa itu RKAS?"})
    assert jalur.jumlah_panggilan == 0


def test_pesan_tolakan_peran_ringkas_dan_tanpa_istilah_teknis() -> None:
    """R-06."""
    aplikasi, _ = _aplikasi(peran=Peran.ANOTATOR)
    pesan = TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "x y z"}).json()["pesan"]
    assert len(pesan.split()) <= 20
    for istilah in ("403", "forbidden", "role", "endpoint", "HTTP"):
        assert istilah.lower() not in pesan.lower()


# ── B-1 · POST /api/v1/tanya ────────────────────────────────────────


def test_jawaban_sah_dikembalikan_utuh() -> None:
    """R-02. Tanpa satu bidang pun berubah."""
    aplikasi, jalur = _aplikasi()
    isi = TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "Apa itu RKAS?"}).json()
    assert isi["id_pesan"] == "p1"
    assert isi["status_dasar"] == "kuat"
    assert isi["penafian"] == PENAFIAN
    assert jalur.jumlah_panggilan == 1
    assert jalur.pertanyaan_terakhir == "Apa itu RKAS?"


def test_jalur_berhenti_tanpa_jawaban_tetap_200() -> None:
    """R-03, dan baris yang paling mudah keliru pada seluruh fitur ini.

    D-14 menetapkan `tidak_ditemukan` memakai bentuk yang sama dengan jawaban
    yang sah. Status galat akan membuat layar menampilkannya sebagai kegagalan
    sistem, sedangkan D-02 titik kritis T3 menuntut sebaliknya: sistem yang
    mengaku tidak tahu adalah jawaban yang sah.
    """
    hasil = HasilTanya(
        tanggapan=_tanggapan(StatusDasar.TIDAK_DITEMUKAN),
        alasan_berhenti=AlasanBerhenti.BUKTI_TIDAK_CUKUP,
    )
    aplikasi, _ = _aplikasi(hasil=hasil)
    tanggapan = TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "Apa itu RKAS?"})
    assert tanggapan.status_code == 200
    assert tanggapan.json()["status_dasar"] == "tidak_ditemukan"


def test_pertanyaan_kosong_ditolak_dengan_pesan_ringkas() -> None:
    """R-06."""
    aplikasi, jalur = _aplikasi()
    tanggapan = TestClient(aplikasi).post("/api/v1/tanya", json={"pertanyaan": "   "})
    assert tanggapan.status_code == 400
    assert len(tanggapan.json()["pesan"].split()) <= 20
    assert jalur.jumlah_panggilan == 0


def test_pesan_galat_tidak_memuat_kembali_nilai_yang_ditolak() -> None:
    """R-06. Bentuk yang sama dengan `hide_input_in_errors` pada KB-049.

    Uji ini semula dibungkus `if tanggapan.status_code != 200`, dan permintaan
    yang dikirimnya **selalu** berhasil — sehingga badannya tidak pernah
    dijalankan sekali pun. Ia lulus tanpa menguji apa pun, dan uji mutasi M-8
    yang menemukannya, bukan pembacaan. Ditulis ulang agar permintaannya pasti
    ditolak dan nilai rahasianya pasti terbawa masuk.
    """
    aplikasi, _ = _aplikasi()
    rahasia = "0812RAHASIA9988"
    tanggapan = TestClient(aplikasi).post(
        "/api/v1/tanya", json={"pertanyaan": "Apa itu RKAS?", "nomor": rahasia}
    )
    assert tanggapan.status_code == 400
    assert rahasia not in tanggapan.text


def test_bidang_tambahan_pada_permintaan_ditolak() -> None:
    """Bentuk berpagar pada permintaan, bukan hanya pada tanggapan."""
    aplikasi, jalur = _aplikasi()
    tanggapan = TestClient(aplikasi).post(
        "/api/v1/tanya", json={"pertanyaan": "Apa itu RKAS?", "peran": "admin"}
    )
    assert tanggapan.status_code == 400
    assert jalur.jumlah_panggilan == 0


# ── B-2 · riwayat percakapan ────────────────────────────────────────


def _percakapan_contoh() -> dict[str, object]:
    from src.api.percakapan import Percakapan

    percakapan = Percakapan("c1")
    percakapan.catat(pertanyaan="Apa itu RKAS?", id_pesan="p1", waktu=datetime.now(UTC))
    return {"c1": percakapan}


def test_daftar_percakapan_dikembalikan() -> None:
    aplikasi, _ = _aplikasi(percakapan=_percakapan_contoh())
    isi = TestClient(aplikasi).get("/api/v1/percakapan").json()
    assert isi["percakapan"] == ["c1"]


def test_giliran_dikembalikan_tanpa_bidang_tanggapan() -> None:
    """R-05. `Giliran` memang tidak memilikinya, dan itu yang menjaga C-07."""
    aplikasi, _ = _aplikasi(percakapan=_percakapan_contoh())
    isi = TestClient(aplikasi).get("/api/v1/percakapan/c1").json()
    assert isi["giliran"][0]["pertanyaan"] == "Apa itu RKAS?"
    assert "tanggapan" not in isi["giliran"][0]


def test_gerbang_peran_berlaku_pada_setiap_penangan() -> None:
    """R-01 berlaku pada **setiap** rute, bukan pada `/tanya` saja.

    Ditemukan lewat cakupan, bukan pembacaan: kedua cabang tolakan pada rute
    percakapan tidak tersentuh satu uji pun, sehingga gerbang yang dihapus dari
    keduanya akan lolos seluruh uji lain.
    """
    aplikasi, _ = _aplikasi(peran=Peran.ANOTATOR, percakapan=_percakapan_contoh())
    klien = TestClient(aplikasi)
    for jalur in ("/api/v1/percakapan", "/api/v1/percakapan/c1"):
        tanggapan = klien.get(jalur)
        assert tanggapan.status_code == 403, jalur
        assert len(tanggapan.json()["pesan"].split()) <= 20


def test_percakapan_tak_dikenal_ditolak() -> None:
    aplikasi, _ = _aplikasi(percakapan=_percakapan_contoh())
    tanggapan = TestClient(aplikasi).get("/api/v1/percakapan/tidak-ada")
    assert tanggapan.status_code == 404
    assert len(tanggapan.json()["pesan"].split()) <= 20


# ── Bentuk yang menegakkan R-04 pada tingkat tipe ───────────────────


def test_penentu_identitas_adalah_protokol_bukan_kelas_beton() -> None:
    """Fitur autentikasi kelak mengisinya tanpa menyentuh berkas ini."""
    assert IdentitasTetap(Peran.PENGGUNA) is not None
    assert isinstance(IdentitasTetap(Peran.PENGGUNA), PenentuIdentitas)
