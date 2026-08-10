"""Uji ekspor CoNLL — B-2 fitur 016, R-10, R-11, FR-C06.

**Di sinilah C-10 diuji sampai ke ujungnya.** Seluruh sistem memakai indeks
karakter; CoNLL berbaris per token. Pemetaan di antara keduanya tidak dapat
dihindari, dan di situlah rentang bergeser satu karakter tanpa satu galat pun.

Yang dijaga: **rentang yang tidak jatuh pada batas token dilaporkan, dan
dokumennya dilewati.** Menggesernya ke batas terdekat menghasilkan berkas
pelatihan yang benar bentuknya dan salah isinya — dan model yang dilatih
atasnya akan belajar batas entitas yang tidak pernah ditandai siapa pun.

R-11 diuji bersama: berkas pedoman anotasi wajib menyertai ekspornya. Korpus
tanpa pedoman tidak dapat ditafsirkan orang di luar tim, dan FR-C06 menuntut
keduanya berjalan bersama.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from src.nlp.anotasi.ekspor import GalatEkspor, ekspor_conll
from src.nlp.anotasi.impor_ls import impor
from src.nlp.anotasi.skema import VersiSkema

BAHAN = Path(__file__).resolve().parents[1] / "bahan" / "ekspor-label-studio-1.23.json"
VERSI = VersiSkema(mayor=1, minor=0)
KODE = {1: "A01", 2: "A02"}


def _muat() -> list[dict[str, Any]]:
    isi: list[dict[str, Any]] = json.loads(BAHAN.read_text(encoding="utf-8"))
    return isi


def _hasil(isi: list[dict[str, Any]] | None = None) -> Any:  # noqa: ANN401
    return impor(
        isi if isi is not None else _muat(),
        versi_skema=VERSI,
        kode_anotator=KODE,
        bendera_terkumpul=True,
    )


def _pedoman(tmp: Path) -> Path:
    berkas = tmp / "pedoman-anotasi-1.0.md"
    berkas.write_text("# Pedoman anotasi versi 1.0\n\nAturan rentang: D-03 Bagian 6.\n", "utf-8")
    return berkas


def test_baris_conll_berbentuk_token_dan_tag(tmp_path: Path) -> None:
    hasil = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    assert hasil.baris
    for baris in hasil.baris:
        if baris:
            bagian = baris.split("\t")
            assert len(bagian) == 2


def test_dokumen_dipisahkan_baris_kosong(tmp_path: Path) -> None:
    """Aturan CoNLL. Tanpa pemisah, dua dokumen terbaca sebagai satu kalimat
    panjang dan model belajar hubungan yang tidak ada."""
    hasil = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    assert "" in hasil.baris


def test_penandaan_bio_dipakai(tmp_path: Path) -> None:
    """`B-` pada token pertama entitas, `I-` pada lanjutannya, `O` di luar."""
    hasil = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    tag = {b.split("\t")[1] for b in hasil.baris if b}
    assert "O" in tag
    assert any(t.startswith("B-") for t in tag)
    assert any(t.startswith("I-") for t in tag)


def test_tag_memakai_label_d03(tmp_path: Path) -> None:
    hasil = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    tag = {b.split("\t")[1] for b in hasil.baris if b}
    assert "B-JABATAN_PERAN" in tag


def test_token_pertama_dokumen_pertama_sesuai_bahan(tmp_path: Path) -> None:
    """Nilai tertulis. Kalimat pertama bahan dimulai "Kepala sekolah", dan
    keduanya ditandai JABATAN_PERAN pada rentang (0, 14).

    **Permukaan ditulis apa adanya, bukan hasil normalisasi.** "Kepala"
    dengan huruf besar, sebab CoNLL adalah bahan pelatihan model dan huruf
    besar adalah petunjuk yang dipakai pengenal entitas. Normalisasi pada
    fitur 015 dinyatakan untuk pencarian, bukan untuk bahan anotasi."""
    hasil = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    assert hasil.baris[0] == "Kepala\tB-JABATAN_PERAN"
    assert hasil.baris[1] == "sekolah\tI-JABATAN_PERAN"


def test_rentang_tak_sejajar_batas_token_dilaporkan_bukan_digeser(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini, dan inti R-10.**

    Rentang dipersempit menjadi (0, 6) — "Kepala" saja tanpa spasi berikutnya
    tetap sejajar, sehingga yang dipakai adalah (1, 14): mulai di tengah kata.

    Menggesernya ke batas terdekat menghasilkan berkas pelatihan yang benar
    bentuknya dan salah isinya, dan tidak ada satu pun galat yang menandainya.
    """
    isi = _muat()
    nilai = isi[0]["annotations"][0]["result"][0]["value"]
    nilai["start"] = 1
    nilai["end"] = 14
    nilai["text"] = isi[0]["data"]["teks"][1:14]

    hasil = ekspor_conll(_hasil(isi), pedoman=_pedoman(tmp_path))
    assert hasil.tak_sejajar_token
    assert "3" in hasil.tak_sejajar_token


def test_dokumen_tak_sejajar_tidak_masuk_keluaran(tmp_path: Path) -> None:
    """Dilaporkan **dan** dilewati. Melaporkannya sambil tetap menuliskannya
    berarti laporan yang tidak mengubah apa pun."""
    isi = _muat()
    nilai = isi[0]["annotations"][0]["result"][0]["value"]
    nilai["start"] = 1
    nilai["end"] = 14
    nilai["text"] = isi[0]["data"]["teks"][1:14]

    utuh = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    rusak = ekspor_conll(_hasil(isi), pedoman=_pedoman(tmp_path))
    assert len(rusak.baris) < len(utuh.baris)


def test_pedoman_wajib_ada(tmp_path: Path) -> None:
    """**R-11.** Korpus tanpa pedoman tidak dapat ditafsirkan orang di luar
    tim, dan FR-C06 menuntut keduanya berjalan bersama."""
    with pytest.raises(GalatEkspor) as galat:
        ekspor_conll(_hasil(), pedoman=tmp_path / "tidak-ada.md")
    assert "pedoman" in str(galat.value)


def test_isi_pedoman_ikut_dibawa(tmp_path: Path) -> None:
    """Dibawa bersama, bukan sekadar diperiksa keberadaannya.

    Pedoman yang hanya diperiksa ada akan berpisah dari korpusnya pada
    penyalinan berikutnya, dan korpus yang berpisah dari pedomannya adalah
    korpus yang ditafsirkan menurut ingatan.
    """
    hasil = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    assert "Pedoman anotasi versi 1.0" in hasil.pedoman


def test_modul_tidak_menulis_berkas(tmp_path: Path) -> None:
    """Sama dengan B-1: C-17 melarang akses tulis dari `src/nlp`."""
    hasil = ekspor_conll(_hasil(), pedoman=_pedoman(tmp_path))
    with pytest.raises(NotImplementedError):
        hasil.tulis(tmp_path / "korpus.conll")
