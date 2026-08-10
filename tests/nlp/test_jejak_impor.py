"""Uji pencatatan impor ke logbook — C-1 fitur 016, R-14, C-09.

C-09 menuntut setiap keluaran mencatat versinya. Pada impor anotasi yang wajib
tercatat bukan versi kode melainkan **versi Label Studio, versi skema, dan
keadaan bendera** — ketiganya menentukan isi korpus dan tidak satu pun dapat
dipulihkan dari korpusnya kemudian.

Yang paling menentukan: **keadaan bendera ikut tercatat.** Korpus yang
diimpor dari proyek tanpa kendali bendera terbaca sama dengan korpus yang
bersih, dan satu-satunya tempat pembedaannya bertahan setelah berkasnya
disalin adalah catatan ini.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from src.nlp.anotasi.impor_ls import impor
from src.nlp.anotasi.jejak_impor import catat_impor
from src.nlp.anotasi.skema import VersiSkema

BAHAN = Path(__file__).resolve().parents[1] / "bahan" / "ekspor-label-studio-1.23.json"
VERSI = VersiSkema(mayor=1, minor=0)
KODE = {1: "A01", 2: "A02"}


def _hasil(bendera_terkumpul: bool = True) -> Any:
    isi = json.loads(BAHAN.read_text(encoding="utf-8"))
    return impor(isi, versi_skema=VERSI, kode_anotator=KODE, bendera_terkumpul=bendera_terkumpul)


def _catat(tmp: Path, bendera_terkumpul: bool = True) -> dict[str, Any]:
    catat_impor(tmp, _hasil(bendera_terkumpul), versi_label_studio="1.23.0")
    baris = (tmp / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()
    hasil: dict[str, Any] = json.loads(baris[-1])
    return hasil


BIDANG = (
    "versi_label_studio",
    "versi_skema",
    "jumlah_dokumen",
    "bendera_terkumpul",
    "jumlah_dilewati",
)


@pytest.mark.parametrize("bidang", BIDANG)
def test_setiap_bidang_wajib_ada(tmp_path: Path, bidang: str) -> None:
    assert bidang in _catat(tmp_path)


def test_versi_label_studio_tercatat(tmp_path: Path) -> None:
    """Tidak dapat dibaca dari berkas ekspornya — Label Studio tidak
    menuliskan versinya sendiri di sana (KB-023). Diberikan pemanggil, dan
    karena itu wajib dicatat: tanpa catatannya, tidak ada cara mengetahui
    bentuk apa yang diurai."""
    assert _catat(tmp_path)["versi_label_studio"] == "1.23.0"


def test_keadaan_bendera_tercatat(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini.**

    Korpus dari proyek tanpa kendali bendera terbaca sama dengan korpus yang
    bersih setelah berkasnya disalin beberapa kali. Catatan ini satu-satunya
    tempat pembedaannya bertahan.
    """
    assert _catat(tmp_path, bendera_terkumpul=False)["bendera_terkumpul"] is False
    assert _catat(tmp_path, bendera_terkumpul=True)["bendera_terkumpul"] is True


def test_jumlah_dilewati_tercatat(tmp_path: Path) -> None:
    """Jumlah dokumen saja tidak cukup: korpus yang lebih kecil daripada
    batchnya tidak dapat dibedakan dari batch yang memang kecil."""
    catatan = _catat(tmp_path)
    assert catatan["jumlah_dokumen"] == 2
    assert catatan["jumlah_dilewati"] == 0


def test_satu_baris_per_impor(tmp_path: Path) -> None:
    _catat(tmp_path)
    _catat(tmp_path)
    baris = (tmp_path / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(baris) == 2


def test_isi_dokumen_tidak_masuk_catatan(tmp_path: Path) -> None:
    """Dokumen anotasi memuat teks sekolah sungguhan. Catatan membawa angka
    dan versi, tidak membawa isi."""
    catatan = _catat(tmp_path)
    assert "Kepala sekolah" not in json.dumps(catatan, ensure_ascii=False)


def test_kode_anotator_tidak_masuk_catatan(tmp_path: Path) -> None:
    """Kode anotator anonim sekalipun tidak perlu ada di sini.

    Catatan L2 menerangkan bagaimana korpus terbentuk, bukan siapa yang
    mengerjakannya; yang kedua sudah ada pada korpusnya sendiri, dan
    mengulanginya di sini menambah satu tempat lagi yang wajib dijaga.
    """
    catatan = _catat(tmp_path)
    isi = json.dumps(catatan, ensure_ascii=False)
    assert "A01" not in isi
    assert "A02" not in isi


def test_versi_label_studio_kosong_ditolak(tmp_path: Path) -> None:
    """Baris tanpa versi lebih buruk daripada tidak ada baris — ia terbaca
    seperti catatan yang lengkap.

    Versi Label Studio tidak dapat dibaca dari berkas ekspornya, sehingga
    menerima untai kosong berarti mencatat versi yang tidak pernah diperiksa
    siapa pun.
    """
    with pytest.raises(ValueError, match="versi Label Studio"):
        catat_impor(tmp_path, _hasil(), versi_label_studio="")
    assert not (tmp_path / "L2-versi-artefak.jsonl").exists()
