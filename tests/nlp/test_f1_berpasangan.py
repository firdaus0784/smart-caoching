"""Uji F1 berpasangan — B-4 fitur 003, R-08, D-03 Bagian 11.

Dua tingkat ketat, dan pembedaannya yang menjadi gunanya:

| Tingkat | Cocok bila | Ambang D-03 |
|---|---|---|
| Tepat | batas rentang **dan** label sama persis | 0,75 |
| Longgar | rentang bertumpang tindih **dan** label sama | 0,85 |

Seluruh nilai yang diharapkan dihitung tangan, dan perhitungannya ditulis pada
uraian tiap uji.

**Satu bahaya yang tidak terlihat dari rumusnya**: pada pencocokan longgar,
satu rentang panjang milik A dapat bertumpang tindih dengan tiga rentang
pendek milik B. Tanpa pemasangan satu-lawan-satu, ketiganya terhitung cocok
dan F1 melampaui satu — atau lebih buruk, berhenti di bawah satu tetapi tetap
lebih tinggi daripada yang sebenarnya.
"""

import pytest
from src.nlp.anotasi.kesepakatan import f1_rentang
from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas
from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema

VERSI = VersiSkema(mayor=1, minor=0)
TEKS = "Kepala sekolah menyusun RKAS tahun anggaran 2026 bersama komite sekolah."


def _r(mulai: int, akhir: int, label: LabelEntitas, anotator: str = "ant_a") -> RentangEntitas:
    return RentangEntitas(
        teks_kanonik=TEKS,
        mulai=mulai,
        akhir=akhir,
        label=label,
        versi_skema=VERSI,
        id_anotator=anotator,
    )


DOKUMEN = LabelEntitas.DOKUMEN
ANGGARAN = LabelEntitas.ANGGARAN
INSTANSI = LabelEntitas.INSTANSI


def test_rentang_identik_cocok_pada_kedua_tingkat() -> None:
    """Satu rentang, sama persis. Presisi 1, recall 1, F1 1."""
    a = [_r(24, 28, DOKUMEN)]
    b = [_r(24, 28, DOKUMEN, "ant_b")]
    hasil = f1_rentang(a, b)
    assert hasil.tepat.nilai == pytest.approx(1.0)
    assert hasil.longgar.nilai == pytest.approx(1.0)


def test_bertumpang_tindih_label_sama_hanya_cocok_pada_longgar() -> None:
    """**Uji yang membuat kedua tingkat berarti.**

    A menandai "RKAS", B menandai "RKAS tahun" — batasnya berbeda, labelnya
    sama. Pada pencocokan tepat tidak ada yang cocok; pada longgar keduanya
    cocok.

    tepat:   0 cocok dari 1 dan 1 → F1 = 0
    longgar: 1 cocok dari 1 dan 1 → F1 = 1
    """
    a = [_r(24, 28, DOKUMEN)]
    b = [_r(24, 34, DOKUMEN, "ant_b")]
    hasil = f1_rentang(a, b)
    assert hasil.tepat.nilai == pytest.approx(0.0)
    assert hasil.longgar.nilai == pytest.approx(1.0)


def test_rentang_identik_label_berbeda_tidak_cocok_pada_keduanya() -> None:
    """Label yang berbeda berarti anotator tidak sepaham tentang **apa** yang
    ditandai, dan itu ketidaksepakatan pada tingkat mana pun.

    Longgar melonggarkan batas rentang, **bukan** label. Melonggarkan label
    akan membuat ukuran ini berhenti menilai skema label sama sekali.
    """
    a = [_r(24, 28, DOKUMEN)]
    b = [_r(24, 28, ANGGARAN, "ant_b")]
    hasil = f1_rentang(a, b)
    assert hasil.tepat.nilai == pytest.approx(0.0)
    assert hasil.longgar.nilai == pytest.approx(0.0)


def test_rentang_yang_tidak_bertemu_tidak_cocok() -> None:
    a = [_r(0, 6, INSTANSI)]
    b = [_r(24, 28, INSTANSI, "ant_b")]
    assert f1_rentang(a, b).longgar.nilai == pytest.approx(0.0)


def test_f1_dihitung_tangan_pada_kesepakatan_sebagian() -> None:
    """A menandai tiga rentang, B menandai dua; satu cocok persis.

    A: (0,6) INSTANSI, (24,28) DOKUMEN, (35,43) ANGGARAN
    B: (24,28) DOKUMEN, (57,71) INSTANSI

    tepat: 1 cocok
    presisi = 1 / 2 = 0,50   (dari sisi B sebagai prediksi)
    recall  = 1 / 3 = 0,3333 (dari sisi A sebagai acuan)
    F1 = 2 * 0,5 * 0,3333 / (0,5 + 0,3333) = 0,3333 / 0,8333 = 0,40
    """
    a = [_r(0, 6, INSTANSI), _r(24, 28, DOKUMEN), _r(35, 43, ANGGARAN)]
    b = [_r(24, 28, DOKUMEN, "ant_b"), _r(57, 71, INSTANSI, "ant_b")]
    assert f1_rentang(a, b).tepat.nilai == pytest.approx(0.40)


def test_satu_rentang_panjang_tidak_cocok_dengan_banyak_rentang_pendek() -> None:
    """**Uji terpenting berkas ini.**

    A menandai satu rentang panjang; B memecahnya menjadi tiga rentang pendek
    berlabel sama. Ketiganya bertumpang tindih dengan milik A.

    Tanpa pemasangan satu-lawan-satu, ketiganya terhitung cocok:
    presisi = 3/3 = 1, recall = 3/1 = 3 — dan F1 melampaui satu, atau
    dipangkas diam-diam menjadi angka yang lebih tinggi daripada semestinya.

    Dengan pemasangan satu-lawan-satu, hanya satu pasangan yang sah:
    presisi = 1 / 3 = 0,3333
    recall  = 1 / 1 = 1
    F1 = 2 * 0,3333 * 1 / 1,3333 = 0,50
    """
    a = [_r(24, 47, DOKUMEN)]
    b = [
        _r(24, 28, DOKUMEN, "ant_b"),
        _r(29, 34, DOKUMEN, "ant_b"),
        _r(35, 43, DOKUMEN, "ant_b"),
    ]
    hasil = f1_rentang(a, b)
    assert hasil.longgar.nilai is not None
    assert hasil.longgar.nilai <= 1.0
    assert hasil.longgar.nilai == pytest.approx(0.50)


def test_f1_tidak_pernah_melampaui_satu() -> None:
    """Dinyatakan sebagai sifat, bukan sebagai satu kasus.

    Nilai di atas satu adalah tanda rumusnya keliru, dan `HasilKesepakatan`
    sudah menolaknya — tetapi menolak saat membentuk hasil berarti seluruh
    perhitungan gagal, bukan hasilnya yang salah. Yang diuji di sini rumusnya.
    """
    a = [_r(24, 47, DOKUMEN)]
    b = [_r(24 + i, 26 + i, DOKUMEN, "ant_b") for i in range(0, 20, 3)]
    for hasil in (f1_rentang(a, b), f1_rentang(b, a)):
        for tingkat in (hasil.tepat, hasil.longgar):
            assert tingkat.nilai is not None
            assert 0.0 <= tingkat.nilai <= 1.0


def test_kedua_daftar_kosong_belum_terhitung() -> None:
    """Bukan 1,0. Dua anotator yang sama-sama tidak menandai apa pun **mungkin**
    sepaham, tetapi tidak ada bukti apa pun untuk itu."""
    hasil = f1_rentang([], [])
    assert not hasil.tepat.terhitung
    assert not hasil.longgar.terhitung


def test_satu_daftar_kosong_bernilai_nol_bukan_belum_terhitung() -> None:
    """Berbeda dari keadaan di atas, dan pembedaannya penting.

    Satu anotator menandai sesuatu, yang lain tidak menandai apa pun — itu
    ketidaksepakatan yang sesungguhnya, dan bahannya ada. Melaporkannya
    "belum terhitung" akan menyembunyikan anotator yang melewatkan seluruh
    dokumen.
    """
    hasil = f1_rentang([_r(24, 28, DOKUMEN)], [])
    assert hasil.tepat.terhitung
    assert hasil.tepat.nilai == pytest.approx(0.0)


def test_versi_skema_berbeda_belum_terhitung() -> None:
    """Perlakuan yang sama dengan Kappa — bukan sebagian dihitung."""
    lain = VersiSkema(mayor=2, minor=0)
    a = [_r(24, 28, DOKUMEN)]
    b = [
        RentangEntitas(
            teks_kanonik=TEKS,
            mulai=24,
            akhir=28,
            label=DOKUMEN,
            versi_skema=lain,
            id_anotator="ant_b",
        )
    ]
    hasil = f1_rentang(a, b)
    assert not hasil.tepat.terhitung
    assert "versi" in hasil.tepat.alasan.lower()


def test_f1_menolak_putusan_kategori() -> None:
    """**Sisi lain dari sifat A-5** — R-08.

    Sebagaimana Kappa tidak menerima rentang, F1 tidak menerima putusan
    kategori. F1 atas satuan analisis yang tetap adalah ukuran yang salah
    dengan cara yang berlawanan dari Kappa atas rentang.
    """
    putusan = PutusanKategori(
        id_dokumen="dok_0",
        kategori_utama=KategoriMasalah.K5,
        versi_skema=VERSI,
        id_anotator="ant_a",
    )
    with pytest.raises((TypeError, AttributeError)):
        f1_rentang([putusan], [putusan])  # type: ignore[list-item]
