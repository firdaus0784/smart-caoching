"""Uji penyambungan pemeriksa konsistensi dokumen ke V-03 — R-06, R-07.

Pemeriksa yang benar tetapi tidak tersambung ke gerbang tidak menjaga apa pun.
Uji di sini menanyakan satu hal yang tidak ditanyakan uji pemeriksanya sendiri:
apakah `make check` benar-benar menjalankannya.

Cara bertanyanya sengaja lewat perilaku, bukan lewat pembacaan daftar
pemanggilan. Menegaskan bahwa `_v03` memuat nama fungsi tertentu akan tetap
lulus meski hasil fungsi itu dibuang; yang diuji di sini adalah pelanggaran
buatan pada dokumen benar-benar menjatuhkan gerbang.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from perkakas.pemeriksa.jalankan import _v03

AKAR = Path(__file__).resolve().parents[2]

DOKUMEN = """# D-99 · Contoh

| Item | Keterangan |
|---|---|
| Versi | 0.2 |

## 9. Riwayat Revisi

| Tanggal | Versi | Perubahan | Pemicu |
|---|---|---|---|
| 1 Agustus 2026 | 0.1 | Dibuat | — |
| 2 Agustus 2026 | 0.2 | Diperbarui | — |
"""

D00 = """# D-00

| Item | Keterangan |
|---|---|
| Versi | 1.0 |

## 2. Register Dokumen

| Kode | Dokumen | Versi | Status |
|---|---|---|---|
| D-00 | Kendali | 1.0 | Aktif |
| D-99 | Contoh | 0.2 | Aktif |

## 9. Riwayat Revisi

| Tanggal | Versi | Perubahan |
|---|---|---|
| 1 Agustus 2026 | 1.0 | Dibuat |
"""


def _akar_tiruan(tmp_path: Path, dokumen: str = DOKUMEN) -> Path:
    """Akar sekadar-cukup bagi V-03.

    `AGENTS.md` dan `Makefile` disalin dari repositori sebenarnya agar dua
    pemeriksa V-03 yang lain diam — bila keduanya ikut menyalak, uji ini akan
    lulus karena sebab yang salah.

    `src/api/tanya.py` ikut disalin dengan alasan yang sama, dan alasannya
    bukan kerapian: pemeriksa `hasil_jalur` fitur 021 **berbunyi ketika modul
    yang dijaganya hilang**, sebab pemeriksa yang diam pada pohon yang
    kehilangan seluruh penjagaannya melaporkan bersih pada keadaan terburuk.
    Akar tiruan yang tidak memuatnya karena itu bukan akar yang selaras.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "D00.md").write_text(D00, encoding="utf-8")
    (docs / "D99.md").write_text(dokumen, encoding="utf-8")
    for nama in ("AGENTS.md", "Makefile"):
        shutil.copy2(AKAR / nama, tmp_path / nama)
    api = tmp_path / "src" / "api"
    api.mkdir(parents=True)
    shutil.copy2(AKAR / "src" / "api" / "tanya.py", api / "tanya.py")
    return tmp_path


def test_akar_tiruan_selaras_lulus(tmp_path: Path) -> None:
    """Dasar pembanding: tanpa ini, uji berikutnya tidak membuktikan apa pun."""
    hasil = _v03(_akar_tiruan(tmp_path))
    assert hasil.lulus, "; ".join(str(t) for t in hasil.temuan)


def test_v03_gagal_saat_versi_menyimpang_dari_register(tmp_path: Path) -> None:
    """R-01 lewat gerbang — inilah uji mutasi dalam bentuk terkecilnya."""
    akar = _akar_tiruan(tmp_path, DOKUMEN.replace("| Versi | 0.2 |", "| Versi | 0.3 |"))
    hasil = _v03(akar)
    assert not hasil.lulus
    assert any("register" in t.pesan for t in hasil.temuan)


def test_v03_gagal_saat_riwayat_tertinggal(tmp_path: Path) -> None:
    """R-02 lewat gerbang."""
    kurang = DOKUMEN.replace("| 2 Agustus 2026 | 0.2 | Diperbarui | — |\n", "")
    hasil = _v03(_akar_tiruan(tmp_path, kurang))
    assert not hasil.lulus
    assert any("riwayat" in t.pesan for t in hasil.temuan)


def test_v03_gagal_saat_berkas_tidak_terdaftar(tmp_path: Path) -> None:
    """R-04 lewat gerbang."""
    akar = _akar_tiruan(tmp_path)
    (akar / "docs" / "D98.md").write_text(DOKUMEN.replace("D-99", "D-98"), encoding="utf-8")
    hasil = _v03(akar)
    assert not hasil.lulus
    assert any("tidak terdaftar" in t.pesan for t in hasil.temuan)


def test_v03_gagal_saat_kode_menggantung(tmp_path: Path) -> None:
    """R-05 lewat gerbang."""
    akar = _akar_tiruan(tmp_path, DOKUMEN + "\nTemuan TK-99 belum ditutup.\n")
    hasil = _v03(akar)
    assert not hasil.lulus
    assert any("TK-99" in t.pesan for t in hasil.temuan)


def test_setiap_temuan_menyebut_berkas(tmp_path: Path) -> None:
    """R-06 — temuan tanpa tempat menyuruh pembacanya mencari sendiri."""
    akar = _akar_tiruan(tmp_path, DOKUMEN.replace("| Versi | 0.2 |", "| Versi | 0.3 |"))
    hasil = _v03(akar)
    assert hasil.temuan
    for temuan in hasil.temuan:
        assert temuan.berkas.name, str(temuan)
        assert temuan.baris >= 0


def test_v03_tidak_mengubah_berkas() -> None:
    """R-07 — pemeriksa melapor, tidak memperbaiki.

    Diuji terhadap `docs/` yang sebenarnya, bukan salinan: kekeliruan yang
    ingin ditangkap adalah pemeriksa yang menulis balik ke dokumen asli.
    """
    docs = AKAR / "docs"
    sebelum = {
        b.name: hashlib.sha256(b.read_bytes()).hexdigest() for b in sorted(docs.glob("*.md"))
    }
    _v03(AKAR)
    sesudah = {
        b.name: hashlib.sha256(b.read_bytes()).hexdigest() for b in sorted(docs.glob("*.md"))
    }
    assert sebelum == sesudah


def test_v03_bersih_pada_akar_sebenarnya() -> None:
    hasil = _v03(AKAR)
    assert hasil.lulus, "; ".join(str(t) for t in hasil.temuan)
