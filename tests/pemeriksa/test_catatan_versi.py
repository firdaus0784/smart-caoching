"""Uji pemeriksa kelengkapan catatan versi — C-09, R-11, R-12.

Pemeriksa membaca baris yang **sudah tercatat** pada `logbook/L1`. Ia tidak
dapat memaksa percobaan dicatat — itu kedisiplinan manusia — tetapi ia dapat
memastikan setiap yang tercatat membawa jejak versinya utuh.
"""

import json
from pathlib import Path

from perkakas.pemeriksa.catatan_versi import periksa_catatan_versi

BIDANG = (
    "versi_kode",
    "versi_model",
    "versi_indeks",
    "versi_skema_anotasi",
    "pembagian_data",
)
LENGKAP = dict.fromkeys(BIDANG, "belum-berlaku") | {"id_percobaan": "EXP-2026-001"}


def _tulis_l1(akar: Path, *catatan: dict[str, object]) -> None:
    berkas = akar / "logbook" / "L1-percobaan.jsonl"
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in catatan),
        encoding="utf-8",
    )


def test_logbook_belum_ada_bukan_pelanggaran(tmp_path: Path) -> None:
    """Belum ada percobaan bukan pelanggaran; pencatatan palsu yang pelanggaran."""
    assert periksa_catatan_versi(tmp_path) == []


def test_catatan_lengkap_lolos(tmp_path: Path) -> None:
    _tulis_l1(tmp_path, LENGKAP)
    assert periksa_catatan_versi(tmp_path) == []


def test_bidang_versi_hilang_tertangkap(tmp_path: Path) -> None:
    for bidang in BIDANG:
        akar = tmp_path / bidang
        _tulis_l1(akar, {k: v for k, v in LENGKAP.items() if k != bidang})
        temuan = periksa_catatan_versi(akar)
        assert len(temuan) == 1, f"{bidang} hilang tetapi lolos"
        assert bidang in temuan[0].pesan


def test_bidang_versi_kosong_tertangkap(tmp_path: Path) -> None:
    """R-12 — dikosongkan bukan pilihan yang sah."""
    _tulis_l1(tmp_path, {**LENGKAP, "versi_kode": ""})
    assert len(periksa_catatan_versi(tmp_path)) == 1


def test_baris_rusak_tertangkap(tmp_path: Path) -> None:
    berkas = tmp_path / "logbook" / "L1-percobaan.jsonl"
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text("{bukan json}\n", encoding="utf-8")
    temuan = periksa_catatan_versi(tmp_path)
    assert len(temuan) == 1
    assert "tidak dapat diurai" in temuan[0].pesan


def test_nomor_baris_dilaporkan(tmp_path: Path) -> None:
    _tulis_l1(tmp_path, LENGKAP, {k: v for k, v in LENGKAP.items() if k != "versi_kode"})
    temuan = periksa_catatan_versi(tmp_path)
    assert temuan[0].baris == 2
