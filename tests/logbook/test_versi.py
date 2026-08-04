"""Uji lima bidang versi wajib — R-11, R-12, C-09, NFR-15.

NFR-15 menjanjikan hasil dapat diulang. Janji itu bersandar pada lima bidang
yang wajib ada pada setiap catatan percobaan, dan pada satu aturan yang mudah
diabaikan: bidang yang belum berlaku **diisi penanda**, tidak dikosongkan.

Bidang kosong tidak dapat dibedakan antara "belum ada" dan "lupa dicatat", dan
selisih itu baru terasa pada Bulan 8 ketika naskah disusun — saat tidak ada
lagi yang mengingat mana yang mana.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.logbook.penulis import Buku, tambah_percobaan
from src.logbook.versi import BELUM_BERLAKU, Versi

LENGKAP = {
    "versi_kode": "abc1234",
    "versi_model": BELUM_BERLAKU,
    "versi_indeks": BELUM_BERLAKU,
    "versi_skema_anotasi": BELUM_BERLAKU,
    "pembagian_data": BELUM_BERLAKU,
}


def test_lima_bidang_lengkap_diterima() -> None:
    versi = Versi(**LENGKAP)
    assert versi.versi_kode == "abc1234"


def test_bidang_hilang_ditolak() -> None:
    for bidang in LENGKAP:
        kurang = {k: v for k, v in LENGKAP.items() if k != bidang}
        with pytest.raises(ValidationError):
            Versi(**kurang)


def test_bidang_kosong_ditolak() -> None:
    """R-12 — dikosongkan bukan pilihan yang sah."""
    for bidang in LENGKAP:
        rusak = {**LENGKAP, bidang: ""}
        with pytest.raises(ValidationError):
            Versi(**rusak)


def test_bidang_berisi_spasi_saja_ditolak() -> None:
    rusak = {**LENGKAP, "versi_kode": "   "}
    with pytest.raises(ValidationError):
        Versi(**rusak)


def test_penanda_belum_berlaku_diterima() -> None:
    """Pada fitur 001 indeks dan skema anotasi memang belum ada."""
    versi = Versi(**LENGKAP)
    assert versi.versi_indeks == BELUM_BERLAKU


def test_tambah_percobaan_menulis_kelima_bidang(tmp_path: Path) -> None:
    tambah_percobaan(
        tmp_path,
        id_percobaan="EXP-2026-001",
        tujuan="menguji adaptor tiruan",
        versi=Versi(**LENGKAP),
        hasil={"status": "berhasil"},
    )
    baris = json.loads((tmp_path / Buku.L1.value).read_text(encoding="utf-8").strip())
    for bidang in LENGKAP:
        assert bidang in baris, f"bidang versi {bidang} tidak tercatat"


def test_tambah_percobaan_menyimpan_tujuan_dan_hasil(tmp_path: Path) -> None:
    """D-10 Bagian 3 mensyaratkan tujuan satu kalimat dan hasil."""
    tambah_percobaan(
        tmp_path,
        id_percobaan="EXP-2026-002",
        tujuan="menguji pemisahan instruksi dan data",
        versi=Versi(**LENGKAP),
        hasil={"status": "gagal", "sebab": "ambang belum dikalibrasi"},
    )
    baris = json.loads((tmp_path / Buku.L1.value).read_text(encoding="utf-8").strip())
    assert baris["tujuan"]
    assert baris["hasil"]["status"] == "gagal"


def test_percobaan_gagal_tetap_dicatat(tmp_path: Path) -> None:
    """D-10 Bagian 3: percobaan yang gagal WAJIB dicatat, bukan hanya berhasil."""
    tambah_percobaan(
        tmp_path,
        id_percobaan="EXP-2026-003",
        tujuan="menguji ambang",
        versi=Versi(**LENGKAP),
        hasil={"status": "gagal"},
    )
    assert (tmp_path / Buku.L1.value).is_file()
