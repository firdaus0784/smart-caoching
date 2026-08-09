"""Uji pencatatan keluaran OCR — D-3 fitur 015, R-05, C-09.

C-09 menuntut setiap keluaran mencatat versinya. Pada OCR yang wajib tercatat
bukan versi kode melainkan **versi mesin dan sidik berkas model**: keduanya
berada di luar `uv.lock`, dan keduanya menentukan isi korpus.

Satu baris per keluaran, bukan satu baris per berkas ataupun ringkasan per
kelompok. Ringkasan menghapus waktu, dan waktu yang membedakan dokumen yang
diproses sebelum mesin diganti dari yang sesudahnya.
"""

import json
from pathlib import Path

import pytest
from src.ingest.ekstraksi.jejak_ocr import catat_keluaran_ocr
from src.ingest.ekstraksi.ocr import HasilMesin, PengekstrakOcr

BAHAN = Path(__file__).resolve().parents[1] / "bahan"


def _mesin(_: Path) -> HasilMesin:
    return HasilMesin(
        teks="Notulen rapat pleno hasil pindaian.",
        versi_mesin="5.3.4",
        sidik_model="sha256:abc123",
    )


def _hasil() -> object:
    return PengekstrakOcr(mesin=_mesin).ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")


def _baris(akar: Path) -> list[dict[str, object]]:
    berkas = akar / "L2-versi-artefak.jsonl"
    return [json.loads(b) for b in berkas.read_text(encoding="utf-8").splitlines() if b.strip()]


def test_satu_keluaran_menghasilkan_satu_baris(tmp_path: Path) -> None:
    catat_keluaran_ocr(tmp_path, _hasil())  # type: ignore[arg-type]
    assert len(_baris(tmp_path)) == 1


def test_baris_memuat_versi_mesin_dan_sidik_model(tmp_path: Path) -> None:
    """**Sifat terpenting berkas ini** — tanpa keduanya keluaran tidak dapat
    diulang, dan yang tidak dapat diulang tidak dapat dipertanggungjawabkan
    pada naskah."""
    catat_keluaran_ocr(tmp_path, _hasil())  # type: ignore[arg-type]
    baris = _baris(tmp_path)[0]
    assert baris["versi_mesin"] == "5.3.4"
    assert baris["sidik_model"] == "sha256:abc123"


def test_baris_memuat_asal_berkas_bukan_isinya(tmp_path: Path) -> None:
    """Nama berkas menelusuri; isinya tidak pernah dibutuhkan di logbook, dan
    dokumen pindaian sekolah memuat data pribadi yang belum diverifikasi."""
    catat_keluaran_ocr(tmp_path, _hasil())  # type: ignore[arg-type]
    baris = _baris(tmp_path)[0]
    assert baris["asal"] == "pindaian-tanpa-teks.pdf"
    assert "Notulen" not in json.dumps(baris)


def test_dua_keluaran_menghasilkan_dua_baris(tmp_path: Path) -> None:
    """Tambah saja: yang kedua tidak menimpa yang pertama."""
    catat_keluaran_ocr(tmp_path, _hasil())  # type: ignore[arg-type]
    catat_keluaran_ocr(tmp_path, _hasil())  # type: ignore[arg-type]
    assert len(_baris(tmp_path)) == 2


def test_waktu_tercatat(tmp_path: Path) -> None:
    """Ringkasan per kelompok akan menghapus waktu, dan waktu yang membedakan
    dokumen sebelum mesin diganti dari yang sesudahnya."""
    catat_keluaran_ocr(tmp_path, _hasil())  # type: ignore[arg-type]
    assert _baris(tmp_path)[0]["dicatat_pada"]


def test_panjang_teks_dicatat_bukan_teksnya(tmp_path: Path) -> None:
    """Panjang cukup untuk menyadari pindaian yang hasilnya tiba-tiba jauh
    lebih pendek daripada biasanya, tanpa menyalin isinya."""
    catat_keluaran_ocr(tmp_path, _hasil())  # type: ignore[arg-type]
    assert _baris(tmp_path)[0]["panjang_karakter"] == len("Notulen rapat pleno hasil pindaian.")


def test_keluaran_bukan_ocr_ditolak(tmp_path: Path) -> None:
    """Pencatat yang menerima apa pun akan menuliskan baris tanpa versi mesin,
    dan baris tanpa versi lebih buruk daripada tidak ada baris — ia terbaca
    seperti catatan yang lengkap."""
    from src.ingest.ekstraksi.docx import PengekstrakDocx

    with pytest.raises(TypeError):
        catat_keluaran_ocr(tmp_path, PengekstrakDocx().ekstrak(BAHAN / "notulen.docx"))  # type: ignore[arg-type]
