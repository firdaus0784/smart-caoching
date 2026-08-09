"""Uji skema label dan kategori — A-1 s.d. A-3 fitur 003, R-01 s.d. R-04.

Skema ditetapkan **dari D-03**, bukan dari bentuk ekspor perangkat mana pun
(KB-021). Itu yang menjaga tipe kita tetap milik kita ketika Label Studio
naik versi.
"""

import pytest
from pydantic import ValidationError
from src.nlp.anotasi.skema import (
    KATEGORI_URUTAN_PEMUTUS,
    KategoriMasalah,
    LabelEntitas,
    VersiSkema,
)


def test_delapan_label_entitas_sesuai_fr_c04() -> None:
    assert {a.name for a in LabelEntitas} == {
        "REGULASI",
        "PROGRAM",
        "ANGGARAN",
        "JABATAN_PERAN",
        "INDIKATOR_MUTU",
        "TENGGAT_WAKTU",
        "INSTANSI",
        "DOKUMEN",
    }


def test_label_di_luar_daftar_ditolak() -> None:
    """Label sebagai untai bebas berarti dua anotator dapat menuliskan hal
    yang sama dengan dua ejaan, dan kesepakatan mereka terhitung nol."""
    with pytest.raises(ValueError):
        LabelEntitas("SARANA")


def test_delapan_kategori_dengan_kode_persis_d03() -> None:
    assert [k.value for k in KategoriMasalah] == ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"]


def test_urutan_pemutus_sesuai_d03_a04() -> None:
    """D-03 A-04 menetapkan urutannya, dan urutannya bukan K1 sampai K8.

    K5 didahulukan karena konsekuensi kepatuhannya tertinggi; K8 diletakkan
    terakhir karena hampir semua dokumen manajerial dapat dipaksa masuk ke
    sana, sehingga ia menjadi keranjang serba-boleh bila tidak dibatasi.
    """
    assert [k.value for k in KATEGORI_URUTAN_PEMUTUS] == [
        "K5",
        "K7",
        "K2",
        "K1",
        "K3",
        "K4",
        "K6",
        "K8",
    ]


def test_urutan_pemutus_memuat_seluruh_kategori() -> None:
    """Urutan yang kehilangan satu kategori membuat dokumen pada kategori itu
    tidak pernah terputuskan ketika nilainya seimbang."""
    assert set(KATEGORI_URUTAN_PEMUTUS) == set(KategoriMasalah)


def test_versi_skema_beku() -> None:
    with pytest.raises(ValidationError):
        VersiSkema(mayor=1, minor=0).mayor = 2  # type: ignore[misc]


def test_versi_skema_terurut() -> None:
    """FR-C08 menuntut batch terdampak ditandai ketika versi naik; "naik"
    menuntut perbandingan yang terdefinisi."""
    assert VersiSkema(mayor=1, minor=0) < VersiSkema(mayor=1, minor=1)
    assert VersiSkema(mayor=1, minor=9) < VersiSkema(mayor=2, minor=0)


def test_kenaikan_mayor_menandai_perlu_anotasi_ulang() -> None:
    """**Uji terpenting berkas ini** — R-04.

    Kenaikan mayor berarti arti label berubah, sehingga anotasi lama tidak
    lagi berarti hal yang sama. Kenaikan minor menambah tanpa mengubah arti.
    Membedakan keduanya mencegah seluruh korpus dianotasi ulang setiap kali
    satu label ditambahkan.
    """
    lama = VersiSkema(mayor=1, minor=0)
    assert VersiSkema(mayor=2, minor=0).menuntut_anotasi_ulang(lama)
    assert not VersiSkema(mayor=1, minor=1).menuntut_anotasi_ulang(lama)


def test_versi_yang_sama_tidak_menuntut_apa_pun() -> None:
    versi = VersiSkema(mayor=1, minor=0)
    assert not versi.menuntut_anotasi_ulang(versi)


def test_versi_lebih_lama_tidak_menuntut_anotasi_ulang() -> None:
    """Perbandingan mundur adalah tanda pemanggil keliru, bukan alasan
    menandai batch — dan menandainya akan membuat batch terbaru dianggap
    usang."""
    assert not VersiSkema(mayor=1, minor=0).menuntut_anotasi_ulang(VersiSkema(mayor=2, minor=0))


def test_versi_sebagai_untai_terbaca_manusia() -> None:
    """Versi masuk ke berkas ekspor dan ke catatan batch; bentuk yang dibaca
    manusia mencegah dua penulisan berbeda untuk versi yang sama."""
    assert str(VersiSkema(mayor=1, minor=2)) == "1.2"
