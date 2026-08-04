"""Uji penulis logbook tambah-saja — R-11, R-13, C-09.

`AGENTS.md` bagian Batas melarang menyentuh `logbook/` selain menambah baris.
Larangan itu prosedural bagi manusia; bagi kode ia ditegakkan di sini dengan
cara yang lebih tegas — **permukaan modul tidak menyediakan cara lain.**

Fungsi ubah dan hapus tidak ada, bukan ada tetapi dilarang. Yang tidak
disediakan tidak dapat dipanggil karena lupa.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

import src.logbook.penulis as modul
from src.logbook.penulis import Buku, tambah_baris


def test_menambah_satu_baris(tmp_path: Path) -> None:
    tambah_baris(tmp_path, Buku.L1, {"id_percobaan": "EXP-2026-001"})
    berkas = tmp_path / Buku.L1.value
    assert len(berkas.read_text(encoding="utf-8").strip().splitlines()) == 1


def test_menambah_tidak_menghapus_baris_sebelumnya(tmp_path: Path) -> None:
    tambah_baris(tmp_path, Buku.L1, {"id_percobaan": "EXP-2026-001"})
    tambah_baris(tmp_path, Buku.L1, {"id_percobaan": "EXP-2026-002"})

    baris = (tmp_path / Buku.L1.value).read_text(encoding="utf-8").strip().splitlines()
    assert len(baris) == 2
    assert json.loads(baris[0])["id_percobaan"] == "EXP-2026-001"


def test_berkas_dibuat_bila_belum_ada(tmp_path: Path) -> None:
    tambah_baris(tmp_path, Buku.L2, {"artefak": "kode"})
    assert (tmp_path / Buku.L2.value).is_file()


def test_stempel_waktu_utc_ditambahkan(tmp_path: Path) -> None:
    """KM-01 pada D-14: seluruh waktu disimpan dalam UTC."""
    tambah_baris(tmp_path, Buku.L1, {"id_percobaan": "EXP-2026-001"})
    baris = json.loads((tmp_path / Buku.L1.value).read_text(encoding="utf-8").strip())
    waktu = datetime.fromisoformat(baris["dicatat_pada"])
    assert waktu.tzinfo is not None, "stempel waktu tanpa zona"
    assert waktu.utcoffset() == UTC.utcoffset(None), "stempel waktu bukan UTC"


def test_permukaan_modul_tidak_menyediakan_ubah_atau_hapus() -> None:
    """R-13 — yang tidak disediakan tidak dapat dipanggil karena lupa."""
    terlarang = ("ubah", "hapus", "tulis_ulang", "kosongkan", "ganti", "timpa")
    ada = [
        nama
        for nama in dir(modul)
        if not nama.startswith("_") and any(k in nama.lower() for k in terlarang)
    ]
    assert not ada, f"permukaan modul menyediakan cara mengubah logbook: {ada}"


def test_baris_berbentuk_jsonl_satu_baris_per_catatan(tmp_path: Path) -> None:
    tambah_baris(tmp_path, Buku.L1, {"catatan": "berisi\nbaris baru"})
    isi = (tmp_path / Buku.L1.value).read_text(encoding="utf-8")
    assert len(isi.strip().splitlines()) == 1, "baris baru merusak bentuk JSONL"


def test_catatan_kosong_ditolak(tmp_path: Path) -> None:
    """Baris kosong pada rekaman penelitian tidak membawa informasi."""
    try:
        tambah_baris(tmp_path, Buku.L1, {})
    except ValueError:
        return
    raise AssertionError("catatan kosong diterima")
