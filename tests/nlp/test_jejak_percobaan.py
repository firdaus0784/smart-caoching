"""Uji catatan percobaan — C-1 fitur 004, R-10, R-11, C-09, D-10 Bagian 3.

D-10 Bagian 3 menutup daftar bidangnya dengan satu kalimat yang menentukan
seluruh berkas ini: **pencatatan seed acak dan pembagian data bersifat wajib.**
Tanpa keduanya, angka yang dilaporkan tidak dapat diulang oleh siapa pun,
termasuk oleh tim sendiri tiga bulan kemudian.

Dua hal yang lebih mudah luput daripada daftar bidangnya:

1. **Percobaan yang gagal wajib tercatat.** D-10 menuliskannya tegas, dan
   alasannya bukan kerapian: rangkaian percobaan gagal adalah bukti bahwa
   konfigurasi akhir dipilih berdasarkan pengujian, bukan kebetulan. Catatan
   yang hanya memuat keberhasilan terbaca seperti penelitian yang tidak pernah
   salah — dan tidak ada penelitian seperti itu.

2. **Hitungan pembukaan himpunan uji ikut.** KB-028 pilihan C. Angka yang
   dilaporkan bersama "himpunan uji dibuka empat kali" adalah angka yang
   pembacanya dapat nilai sendiri.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from src.nlp.pelatihan.jejak_percobaan import catat_percobaan
from src.nlp.pelatihan.lemari_uji import LemariUji
from src.nlp.pelatihan.metrik import hitung_metrik
from src.nlp.pelatihan.pembagian import buat_pembagian

BIDANG_D10 = (
    "id_percobaan",
    "tujuan",
    "tugas",
    "model_dasar",
    "versi_korpus",
    "id_pembagian_data",
    "konfigurasi",
    "perangkat_keras",
    "durasi_detik",
    "hasil",
    "status",
    "catatan",
    "versi_kode",
    "seed",
)


def _lemari() -> LemariUji:
    bagi = buat_pembagian(
        [f"dok{i:04d}" for i in range(100)], seed=7, versi_korpus="1.0", id_pembagian="B1"
    )
    return LemariUji(bagi)


def _catat(tmp: Path, lemari: LemariUji | None = None, **ganti: Any) -> dict[str, Any]:
    lemari = lemari if lemari is not None else _lemari()
    acuan = ["K1", "K1", "K2"]
    argumen: dict[str, Any] = {
        "id_percobaan": "EXP-2026-001",
        "tujuan": "menguji model dasar IndoBERT pada tugas klasifikasi",
        "tugas": "klasifikasi",
        "model_dasar": "indobert-base-p1 v1.0",
        "lemari": lemari,
        "konfigurasi": {"epoch": 3, "ukuran_batch": 16, "laju_belajar": 2e-5},
        "perangkat_keras": "CPU 8 inti, 32 GB",
        "durasi_detik": 4200,
        "metrik": hitung_metrik(acuan=acuan, prediksi=list(acuan)),
        "status": "berhasil",
        "catatan": "",
        "versi_kode": "abc1234",
    }
    argumen.update(ganti)
    catat_percobaan(tmp, **argumen)
    baris = (tmp / "L1-percobaan.jsonl").read_text(encoding="utf-8").splitlines()
    hasil: dict[str, Any] = json.loads(baris[-1])
    return hasil


@pytest.mark.parametrize("bidang", BIDANG_D10)
def test_setiap_bidang_d10_ada(tmp_path: Path, bidang: str) -> None:
    """Diuji sebagai daftar, bukan satu per satu pada uji terpisah, supaya
    bidang yang ditambahkan D-10 kelak menjatuhkan satu uji yang jelas."""
    assert bidang in _catat(tmp_path)


def test_seed_dan_id_pembagian_diambil_dari_lemari(tmp_path: Path) -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-10.**

    Keduanya tidak diminta sebagai argumen terpisah: argumen terpisah dapat
    diisi angka yang bukan milik pembagian yang benar-benar dipakai, dan
    catatan yang menyebut seed yang salah lebih buruk daripada catatan tanpa
    seed — ia menuntun orang mengulang dengan angka yang keliru.
    """
    catatan = _catat(tmp_path)
    assert catatan["seed"] == 7
    assert catatan["id_pembagian_data"] == "B1"


def test_hitungan_pembukaan_himpunan_uji_ikut(tmp_path: Path) -> None:
    """**KB-028 pilihan C.** Angka yang dilaporkan bersama hitungan pembukaan
    adalah angka yang pembacanya dapat nilai sendiri."""
    lemari = _lemari()
    lemari.buka("evaluasi akhir model klasifikasi v1")
    lemari.buka("evaluasi diulang: perkakas metrik salah versi")
    catatan = _catat(tmp_path, lemari=lemari)
    assert catatan["pembukaan_himpunan_uji"] == 2


def test_alasan_pembukaan_ikut_bukan_hanya_hitungannya(tmp_path: Path) -> None:
    """Hitungan tanpa alasan tidak membedakan evaluasi akhir dari mengintip,
    dan pembedaan itu yang menentukan apakah PU-01 dilanggar."""
    lemari = _lemari()
    lemari.buka("evaluasi akhir model klasifikasi v1")
    catatan = _catat(tmp_path, lemari=lemari)
    assert "evaluasi akhir" in json.dumps(catatan["alasan_pembukaan"], ensure_ascii=False)


def test_percobaan_gagal_tetap_tercatat(tmp_path: Path) -> None:
    """**D-10 menuliskannya tegas.**

    Rangkaian percobaan gagal adalah bukti bahwa konfigurasi akhir dipilih
    berdasarkan pengujian, bukan kebetulan. Catatan yang hanya memuat
    keberhasilan terbaca seperti penelitian yang tidak pernah salah.
    """
    catatan = _catat(
        tmp_path,
        status="gagal",
        catatan="kehabisan memori pada epoch 2; dugaan ukuran batch terlalu besar",
        metrik=None,
    )
    assert catatan["status"] == "gagal"
    assert "memori" in catatan["catatan"]


def test_percobaan_gagal_tanpa_dugaan_penyebab_ditolak(tmp_path: Path) -> None:
    """D-10: catatan "terutama untuk percobaan yang gagal: apa dugaan
    penyebabnya".

    Percobaan gagal tanpa dugaan penyebab adalah baris yang tidak menghalangi
    siapa pun mengulangi jalan buntu yang sama.
    """
    with pytest.raises(ValueError, match="dugaan"):
        _catat(tmp_path, status="gagal", catatan="", metrik=None)


def test_status_di_luar_daftar_ditolak(tmp_path: Path) -> None:
    """D-10 menetapkan tiga: berhasil, gagal, dibatalkan. Untai bebas di sini
    berarti "sukses", "OK", dan "berhasil" hidup berdampingan, lalu jumlah
    percobaan berhasil dihitung atas salah satunya saja."""
    with pytest.raises(ValueError):
        _catat(tmp_path, status="sukses")


def test_metrik_tercatat_per_kelas_bukan_hanya_rerata(tmp_path: Path) -> None:
    """FR-D04 dijaga sampai ke catatannya, bukan hanya sampai ke tipenya.

    Catatan yang hanya memuat rerata membuat kelas berperforma rendah hilang
    justru pada berkas yang dibaca berbulan kemudian.
    """
    catatan = _catat(tmp_path)
    hasil = catatan["hasil"]
    assert "per_kelas" in hasil
    assert set(hasil["per_kelas"]) == {"K1", "K2"}
    assert "f1_makro" in hasil
    assert "f1_mikro" in hasil


def test_satu_baris_per_percobaan(tmp_path: Path) -> None:
    _catat(tmp_path)
    _catat(tmp_path)
    baris = (tmp_path / "L1-percobaan.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(baris) == 2


def test_ditulis_ke_l1_bukan_l2(tmp_path: Path) -> None:
    """L1 mencatat percobaan model; L2 mencatat versi artefak.

    Pembedaannya menentukan berkas mana yang dibaca saat menyusun bagian
    metode naskah.
    """
    _catat(tmp_path)
    assert (tmp_path / "L1-percobaan.jsonl").exists()
    assert not (tmp_path / "L2-versi-artefak.jsonl").exists()
