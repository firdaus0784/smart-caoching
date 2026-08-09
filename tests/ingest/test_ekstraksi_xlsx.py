"""Uji pengekstrak XLSX — B-4 fitur 015, R-01, R-02.

`spec.md` menuntut "nilai terhitung yang diambil, bukan rumusnya". Kalimat itu
mengandaikan nilai terhitungnya ada, dan pada berkas XLSX **tidak selalu ada**:
yang menyimpan hasil hitungan adalah aplikasi lembar sebar, bukan formatnya.
Berkas yang ditulis pustaka atau dihasilkan sistem lain memuat rumus tanpa
nilai tersimpan.

Karena itu ada tiga keadaan, bukan dua — dan yang ketiga tidak disebut
`spec.md`. Ditemukan pada B-1, diuji di sini.
"""

from pathlib import Path

import pytest
from src.ingest.ekstraksi.galat import GalatEkstraksi
from src.ingest.ekstraksi.xlsx import PengekstrakXlsx

BAHAN = Path(__file__).resolve().parents[1] / "bahan"


def _ekstrak(nama: str) -> str:
    return PengekstrakXlsx().ekstrak(BAHAN / nama).isi


def test_nilai_sel_biasa_terekstrak() -> None:
    isi = _ekstrak("serapan.xlsx")
    assert "Honor guru" in isi
    assert "12000000" in isi


def test_rumus_tidak_pernah_masuk_teks() -> None:
    """**Uji terpenting berkas ini.**

    `=B2-C2` pada korpus bukan sekadar sampah: ia rangkaian karakter yang akan
    diindeks, dicari, dan mungkin dikutip sebagai bukti pada jawaban. Menulis
    rumus adalah jalan pintas yang paling menggoda karena ia selalu tersedia
    ketika nilainya tidak.
    """
    assert "=B2-C2" not in _ekstrak("serapan.xlsx")
    assert "=" not in _ekstrak("serapan.xlsx")


def test_sel_berumus_tanpa_nilai_tersimpan_dilewati_bukan_dikosongkan_diam_diam() -> None:
    """Keadaan ketiga: rumus ada, nilainya tidak.

    Yang dituntut bukan sekadar "jangan tulis rumus" melainkan **jangan
    berpura-pura selnya kosong**. Sel yang dilewati diam-diam menghasilkan
    laporan anggaran yang kehilangan kolom sisa tanpa seorang pun tahu, dan
    verifikator membaca tabel yang tampak lengkap.
    """
    isi = _ekstrak("serapan.xlsx")
    assert "Sisa" in isi
    assert PengekstrakXlsx().ekstrak(BAHAN / "serapan.xlsx").sel_tak_terhitung == 3


def test_berkas_bukan_xlsx_ditolak() -> None:
    with pytest.raises(GalatEkstraksi):
        PengekstrakXlsx().ekstrak(BAHAN / "rusak.pdf")


def test_berkas_tidak_ada_ditolak() -> None:
    with pytest.raises(GalatEkstraksi):
        PengekstrakXlsx().ekstrak(BAHAN / "tidak-ada.xlsx")


def test_menangani_hanya_xlsx() -> None:
    pengekstrak = PengekstrakXlsx()
    assert pengekstrak.menangani(Path("a.xlsx"))
    assert pengekstrak.menangani(Path("a.XLSX"))
    assert not pengekstrak.menangani(Path("a.xls"))
    assert not pengekstrak.menangani(Path("a.docx"))


def test_nama_lembar_ikut_terbawa() -> None:
    """Satu berkas dapat memuat beberapa lembar dengan judul kolom yang sama.

    Tanpa nama lembar, "Honor guru" pada lembar anggaran dan pada lembar
    realisasi menjadi dua baris yang tidak dapat dibedakan siapa pun.
    """
    assert "Serapan" in _ekstrak("serapan.xlsx")


def test_asal_dan_pengekstrak_terisi() -> None:
    teks = PengekstrakXlsx().ekstrak(BAHAN / "serapan.xlsx")
    assert teks.asal == "serapan.xlsx"
    assert teks.pengekstrak


def test_uraian_modul_menyatakan_keadaan_rumus_tanpa_nilai() -> None:
    """Pembaca berikutnya yang melihat penghitungan sel tak terhitung akan
    bertanya mengapa; jawabannya harus ada di sana."""
    import src.ingest.ekstraksi.xlsx as modul

    uraian = (modul.__doc__ or "").lower()
    assert "rumus" in uraian
    assert "tidak" in uraian


def test_xlsx_terbuka_tetapi_tanpa_isi_ditolak() -> None:
    """Lembar sebar sah yang seluruh selnya kosong.

    Nama lembar saja bukan isi. Menerimanya berarti korpus memuat dokumen
    yang seluruh muatannya adalah kata "Kosong".
    """
    with pytest.raises(GalatEkstraksi):
        PengekstrakXlsx().ekstrak(BAHAN / "kosong.xlsx")


def test_baris_kosong_di_tengah_tabel_tidak_menjadi_baris_teks() -> None:
    """Lembar sebar sekolah penuh baris pemisah kosong.

    Menuliskannya sebagai baris kosong menggeser indeks karakter setiap
    temuan sesudahnya tanpa menambah satu kata pun yang berarti.
    """
    assert "\n\n" not in _ekstrak("serapan.xlsx")


def test_lembar_kosong_tidak_menyumbang_namanya() -> None:
    """Berbeda dari uji berkas kosong: di sini **berkasnya berisi**, hanya
    salah satu lembarnya yang tidak.

    Nama lembar kosong yang ikut terbawa akan terbaca sebagai judul bagian
    yang isinya hilang, dan pembaca akan mencari isi yang tidak pernah ada.
    """
    assert "Lampiran Kosong" not in _ekstrak("serapan.xlsx")
    assert "Perjalanan dinas" in _ekstrak("serapan.xlsx")
