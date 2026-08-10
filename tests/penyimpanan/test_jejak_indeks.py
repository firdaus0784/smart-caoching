"""Uji pencatatan penempatan indeks — B-2 fitur 006, R-08, C-09."""

import json
from pathlib import Path
from typing import Any

from src.penyimpanan.indeks import IndeksTujuan, SegmenTerindeks, StatusLisensi
from src.penyimpanan.jejak_indeks import catat_penempatan

TEKS = "Kepala sekolah menyusun RKAS bersama komite sekolah."


def _catat(tmp: Path, **ganti: Any) -> dict[str, Any]:
    argumen: dict[str, Any] = {
        "id_segmen": "SEG-001",
        "id_dokumen": "DOC-001",
        "teks": TEKS,
        "lisensi": StatusLisensi.TERBUKA,
        "indeks_tujuan": IndeksTujuan.UTAMA,
        "anonimisasi_terverifikasi": True,
    }
    argumen.update(ganti)
    catat_penempatan(tmp, SegmenTerindeks(**argumen), sumber_lisensi="CC-BY-4.0")
    baris = (tmp / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()
    hasil: dict[str, Any] = json.loads(baris[-1])
    return hasil


def test_lisensi_yang_mendasari_ikut_tercatat(tmp_path: Path) -> None:
    """**Inti R-08.**

    Audit lisensi menanyakan satu hal: atas dasar apa segmen ini ditempatkan
    di indeks utama? Indeks tujuan saja tidak menjawabnya.
    """
    catatan = _catat(tmp_path)
    assert catatan["lisensi"] == "terbuka"
    assert catatan["indeks_tujuan"] == "utama"


def test_keterangan_lisensi_mentah_ikut_bukan_hanya_hasil_pembacaannya(
    tmp_path: Path,
) -> None:
    """Menyimpan hasilnya saja membuat kekeliruan pembacaan tidak dapat
    ditelusuri: yang tercatat akan selalu tampak konsisten dengan indeks
    tujuannya, sebab keduanya berasal dari fungsi yang sama."""
    assert _catat(tmp_path)["sumber_lisensi"] == "CC-BY-4.0"


def test_isi_segmen_tidak_masuk_catatan(tmp_path: Path) -> None:
    """Segmen dapat memuat teks sekolah sungguhan."""
    catatan = _catat(tmp_path)
    assert TEKS not in json.dumps(catatan, ensure_ascii=False)
    assert catatan["panjang_karakter"] == len(TEKS)


def test_penempatan_metadata_juga_tercatat(tmp_path: Path) -> None:
    catatan = _catat(tmp_path, lisensi=StatusLisensi.TERTUTUP, indeks_tujuan=IndeksTujuan.METADATA)
    assert catatan["indeks_tujuan"] == "metadata"
    assert catatan["lisensi"] == "tertutup"


def test_satu_baris_per_penempatan(tmp_path: Path) -> None:
    _catat(tmp_path)
    _catat(tmp_path)
    baris = (tmp_path / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(baris) == 2
