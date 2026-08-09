"""Uji ambang kesepakatan — B-6 fitur 003, C-16, D-03 Bagian 11 dan 13.

**C-16 melarang menyetel ambang di luar prosedur kalibrasi D-07 BT-29, dan
larangan itu tidak dapat ditegakkan atas angka yang tersebar.** Ambang yang
tertulis di tiga tempat akan disetel di salah satunya, dan yang menyetelnya
tidak akan merasa sedang menyetel ambang — ia merasa sedang memperbaiki satu
uji yang gagal.

Berkas ini menegakkan dua hal yang berbeda, dan keduanya perlu:

1. **Angkanya sama dengan D-03.** Diperiksa dengan membaca `docs/D03.md`
   sungguhan, bukan dengan menyalin angkanya ke sini. Uji yang menyalin
   angkanya hanya membuktikan dua salinan sama, termasuk ketika keduanya
   sudah menyimpang dari pemiliknya.
2. **Angkanya hanya ada di satu tempat.** Disapu atas seluruh `src/` pada
   tingkat AST, sehingga yang tertangkap adalah angka pada kode — bukan angka
   pada uraian yang memang menjelaskan.

Pembedaan itu disengaja. Uraian boleh menyebut ambangnya sebagai keterangan;
yang tidak boleh adalah **kode yang membandingkan terhadap angka tertulis**,
sebab hanya yang kedua mengubah perilaku ketika disetel.

**Catatan yang wajib dibaca sebelum C-1.** `spec.md` R-14 dan `tasks.md` C-1
menyebut ambang kualifikasi berada pada **D-03 Bagian 12**. Ia tidak di sana.
Bagian 12 memuat beban kerja dan jadwal; ambang kualifikasi berada pada
**Bagian 13**, dan angkanya — F1 longgar ≥ 0,80 terhadap kunci, Kappa kategori
≥ 0,70 — persis seperti yang disebut keduanya. Yang keliru rujukannya, bukan
nilainya. Berkas ini membaca dari Bagian 13 karena di sanalah angkanya berada;
pembetulan `spec.md` diajukan terpisah dan tidak dilakukan diam-diam saat
implementasi.
"""

import ast
import re
from pathlib import Path

import pytest
import src.nlp.anotasi.ambang as modul_ambang

AKAR = Path(__file__).resolve().parents[2]
D03 = (AKAR / "docs" / "D03.md").read_text(encoding="utf-8")


def _angka(teks: str) -> list[float]:
    """Angka berkoma Bahasa Indonesia menjadi float."""
    return [float(a.replace(",", ".")) for a in re.findall(r"\d,\d{2}", teks)]


def _baris_memuat(*penanda: str) -> str:
    for baris in D03.splitlines():
        if all(p in baris for p in penanda):
            return baris
    raise AssertionError(f"baris yang memuat {penanda} tidak ditemukan pada D-03")


def test_ambang_kappa_sama_dengan_d03_bagian_11() -> None:
    """Baris "ambang minimum" pada tabel tafsiran Kappa D-03 Bagian 11.1."""
    baris = _baris_memuat("ambang minimum")
    assert _angka(baris)[0] == modul_ambang.AMBANG_KAPPA


def test_ambang_f1_tepat_sama_dengan_d03_bagian_11() -> None:
    baris = _baris_memuat("F1 pencocokan tepat", "Batas rentang")
    assert _angka(baris)[-1] == modul_ambang.AMBANG_F1_TEPAT


def test_ambang_f1_longgar_sama_dengan_d03_bagian_11() -> None:
    baris = _baris_memuat("F1 pencocokan longgar", "bertumpang tindih")
    assert _angka(baris)[-1] == modul_ambang.AMBANG_F1_LONGGAR


def test_ambang_kualifikasi_sama_dengan_d03_bagian_13() -> None:
    """Bagian 13, bukan Bagian 12 — lihat catatan pada uraian berkas ini."""
    baris = _baris_memuat("Uji kualifikasi", "kunci jawaban")
    longgar, kappa = _angka(baris)
    assert longgar == modul_ambang.AMBANG_KUALIFIKASI_F1_LONGGAR
    assert kappa == modul_ambang.AMBANG_KUALIFIKASI_KAPPA


def test_jumlah_dokumen_kualifikasi_sama_dengan_d03_bagian_13() -> None:
    """Bukan ambang, dan tetap di sini.

    Ia angka milik D-03 yang menentukan apakah sebuah penilaian sah, dan
    menaruhnya di tempat lain berarti ada dua tempat angka D-03 disalin.
    """
    baris = _baris_memuat("Uji kualifikasi", "kunci jawaban")
    jumlah = int(re.search(r"\*\*\s*(\d+) dokumen", baris).group(1))  # type: ignore[union-attr]
    assert jumlah == modul_ambang.JUMLAH_DOKUMEN_KUALIFIKASI


def test_ambang_kualifikasi_lebih_rendah_daripada_ambang_batch() -> None:
    """Bukan kelalaian D-03, dan perlu dinyatakan supaya tidak "dirapikan".

    Kualifikasi menilai satu anotator terhadap **kunci jawaban** yang disusun
    adjudikator; ambang batch menilai **dua anotator terhadap satu sama lain**.
    Menyamakan keduanya akan menaikkan syarat masuk atas dasar yang tidak
    pernah dinyatakan siapa pun.
    """
    assert modul_ambang.AMBANG_KUALIFIKASI_F1_LONGGAR < modul_ambang.AMBANG_F1_LONGGAR


TETAPAN = (
    "AMBANG_KAPPA",
    "AMBANG_F1_TEPAT",
    "AMBANG_F1_LONGGAR",
    "AMBANG_KUALIFIKASI_F1_LONGGAR",
    "AMBANG_KUALIFIKASI_KAPPA",
)


@pytest.mark.parametrize("nama", TETAPAN)
def test_setiap_ambang_bernilai_pecahan_wajar(nama: str) -> None:
    nilai = getattr(modul_ambang, nama)
    assert isinstance(nilai, float)
    assert 0.0 < nilai <= 1.0


def _berkas_sumber() -> list[Path]:
    return sorted((AKAR / "src").rglob("*.py"))


def test_tidak_ada_angka_ambang_tertulis_di_luar_satu_tempat() -> None:
    """**Uji terpenting berkas ini**, dan satu-satunya yang menegakkan C-16.

    Disapu pada tingkat AST, sehingga yang tertangkap hanya angka pada kode.
    Uraian yang menyebut "≥ 0,70" sebagai keterangan tidak tertangkap, dan
    memang tidak seharusnya — ia tidak mengubah perilaku apa pun.

    Yang tertangkap: perbandingan terhadap angka tertulis, nilai bawaan
    parameter, dan tetapan kedua yang menyalin nilai yang sama. Ketiganya
    adalah tempat ambang disetel tanpa ada yang menyadarinya.
    """
    nilai_ambang = {getattr(modul_ambang, n) for n in TETAPAN}
    sah = (AKAR / "src" / "nlp" / "anotasi" / "ambang.py").resolve()
    pelanggaran: list[str] = []
    for berkas in _berkas_sumber():
        if berkas.resolve() == sah:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Constant)
                and isinstance(simpul.value, float)
                and simpul.value in nilai_ambang
            ):
                pelanggaran.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno}: {simpul.value}")
    assert not pelanggaran, "angka ambang di luar ambang.py: " + "; ".join(pelanggaran)


def test_uraian_menyebut_pasal_yang_melarang_penyetelannya() -> None:
    """Tetapan tanpa alasan adalah tetapan yang akan disetel oleh orang yang
    mengira ia sekadar nilai bawaan."""
    uraian = modul_ambang.__doc__ or ""
    assert "C-16" in uraian
    assert "BT-29" in uraian
    assert "D-03" in uraian


def test_uraian_menyebut_letak_ambang_kualifikasi_yang_sebenarnya() -> None:
    """Rujukan keliru pada `spec.md` R-14 akan disalin pembaca berikutnya bila
    tidak ada yang menyatakan letak sebenarnya di tempat angkanya berada."""
    uraian = modul_ambang.__doc__ or ""
    assert "Bagian 13" in uraian
