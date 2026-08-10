"""Uji metrik per kelas — B-1 dan B-2 fitur 004, R-07 s.d. R-09, FR-D04.

FR-D04 menuntut metrik dilaporkan **per kelas, bukan hanya rerata**, dengan
alasan yang tertulis: mendeteksi kelas berperforma rendah. Rerata menyembunyikan
persis apa yang perlu dilihat — korpus manajerial hampir pasti tidak seimbang,
sebab D-03 menempatkan K5 dan K7 sebagai kategori yang mendominasi.

Seluruh nilai yang diharapkan **dihitung tangan**, dan perhitungannya ditulis
pada uraian tiap uji. Uji regresi hanya membuktikan hasilnya tidak berubah,
termasuk ketika ia salah sejak awal.

Dua hal yang lebih mudah luput daripada rumusnya:

1. **Kelas tanpa contoh dilaporkan belum terhitung**, bukan 0,0. Bentuk yang
   sudah tiga kali terbukti pada proyek ini. F1 = 0,0 terbaca sebagai kelas
   yang modelnya gagal total, dan tindak lanjutnya menjadi melatih ulang
   padahal yang diperlukan menambah data.

2. **Rerata dinyatakan jenisnya.** Makro dan mikro berbeda tajam pada kelas
   tidak seimbang, dan rerata tanpa nama jenisnya adalah angka yang dua
   pembaca tafsirkan berbeda — keduanya merasa benar.
"""

import pytest
from src.nlp.pelatihan.metrik import hitung_metrik

# Empat kelas, dan susunannya dipilih agar tiap uji punya kelas yang tepat.
ACUAN = ["K1", "K1", "K1", "K1", "K2", "K2", "K3", "K3"]


def test_prediksi_sempurna_bernilai_satu() -> None:
    """Batas atas. Seluruh kelas 1,0, dan kedua rerata 1,0."""
    hasil = hitung_metrik(acuan=ACUAN, prediksi=list(ACUAN))
    for kelas in ("K1", "K2", "K3"):
        assert hasil.per_kelas[kelas].f1.nilai == pytest.approx(1.0)
    assert hasil.f1_makro.nilai == pytest.approx(1.0)
    assert hasil.f1_mikro.nilai == pytest.approx(1.0)


def test_presisi_dan_recall_dihitung_tangan() -> None:
    """Acuan: K1 empat, K2 dua, K3 dua. Prediksi menukar dua K1 menjadi K2.

    Prediksi: K1 K1 K2 K2 | K2 K2 | K3 K3

    K1 — benar 2, prediksi 2, acuan 4 → presisi 2/2 = 1,0; recall 2/4 = 0,5
         F1 = 2·1,0·0,5 / 1,5 = 0,6667
    K2 — benar 2, prediksi 4, acuan 2 → presisi 2/4 = 0,5; recall 2/2 = 1,0
         F1 = 2·0,5·1,0 / 1,5 = 0,6667
    K3 — benar 2, prediksi 2, acuan 2 → presisi 1,0; recall 1,0; F1 = 1,0
    """
    prediksi = ["K1", "K1", "K2", "K2", "K2", "K2", "K3", "K3"]
    hasil = hitung_metrik(acuan=ACUAN, prediksi=prediksi)

    k1 = hasil.per_kelas["K1"]
    assert k1.presisi.nilai == pytest.approx(1.0)
    assert k1.recall.nilai == pytest.approx(0.5)
    assert k1.f1.nilai == pytest.approx(2 / 3)

    k2 = hasil.per_kelas["K2"]
    assert k2.presisi.nilai == pytest.approx(0.5)
    assert k2.recall.nilai == pytest.approx(1.0)
    assert k2.f1.nilai == pytest.approx(2 / 3)

    assert hasil.per_kelas["K3"].f1.nilai == pytest.approx(1.0)


def test_kelas_tanpa_contoh_pada_acuan_belum_terhitung() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-08.**

    K4 tidak ada pada acuan maupun prediksi. Melaporkannya 0,0 menyatakan
    modelnya gagal total pada kelas itu — dan tindak lanjutnya menjadi melatih
    ulang, padahal yang diperlukan menambah data.
    """
    acuan = ["K1", "K1", "K2", "K4"]
    prediksi = ["K1", "K1", "K2", "K4"]
    hasil = hitung_metrik(acuan=acuan, prediksi=prediksi, kelas=("K1", "K2", "K3", "K4"))
    k3 = hasil.per_kelas["K3"]
    assert not k3.f1.terhitung
    assert k3.f1.nilai is None
    assert k3.f1.alasan


def test_kelas_hanya_pada_prediksi_dilaporkan() -> None:
    """**Halusinasi kelas**, dan ia berbeda dari kelas tanpa contoh.

    Model menandai K3 padahal acuan tidak pernah memuatnya. Presisinya 0,0 —
    terhitung, sebab bahannya ada — sedangkan recall-nya belum terhitung, sebab
    tidak ada satu pun contoh sungguhan untuk ditemukan.

    Menyeragamkan keduanya menjadi 0,0 menyembunyikan pembedaan yang menentukan
    tindak lanjutnya: yang pertama model terlalu berani, yang kedua data kurang.
    """
    acuan = ["K1", "K1", "K2", "K2"]
    prediksi = ["K1", "K3", "K2", "K2"]
    hasil = hitung_metrik(acuan=acuan, prediksi=prediksi, kelas=("K1", "K2", "K3"))
    k3 = hasil.per_kelas["K3"]
    assert k3.presisi.nilai == pytest.approx(0.0)
    assert not k3.recall.terhitung


def test_satu_kelas_kacau_menurunkan_makro_jauh_lebih_besar_daripada_mikro() -> None:
    """**Uji terpenting berkas ini, dan alasan R-09 ada.**

    Sembilan puluh K1 diprediksi sempurna; sepuluh K2 seluruhnya keliru
    diprediksi K1.

    Mikro — benar 90 dari 100 → 0,90. Pada tugas berkelas tunggal, F1 mikro
    sama dengan ketepatan.
    Makro — K1: presisi 90/100 = 0,9; recall 90/90 = 1,0; F1 = 0,947.
            K2: presisi belum terhitung (tidak ada prediksi K2);
                recall 0/10 = 0,0; F1 = 0,0.
            Rerata makro atas kelas yang terhitung = (0,947 + 0,0) / 2 = 0,474.

    Selisih 0,90 lawan 0,47 pada data yang sama. Rerata tanpa nama jenisnya
    adalah angka yang dua pembaca tafsirkan berbeda, dan keduanya merasa benar.
    """
    acuan = ["K1"] * 90 + ["K2"] * 10
    prediksi = ["K1"] * 100
    hasil = hitung_metrik(acuan=acuan, prediksi=prediksi, kelas=("K1", "K2"))

    assert hasil.f1_mikro.nilai == pytest.approx(0.90)
    assert hasil.f1_makro.nilai == pytest.approx(0.4736842, abs=1e-6)
    assert hasil.f1_makro.nilai is not None
    assert hasil.f1_mikro.nilai is not None
    assert hasil.f1_mikro.nilai - hasil.f1_makro.nilai > 0.4


def test_kedua_rerata_dinamai_terpisah() -> None:
    """R-09 sebagai sifat: tidak ada satu bidang bernama `f1` saja.

    Bidang tunggal bernama `f1` adalah bidang yang pembacanya tidak tahu
    jenisnya, dan ia akan disalin ke naskah tanpa keterangan.
    """
    hasil = hitung_metrik(acuan=ACUAN, prediksi=list(ACUAN))
    bidang = set(type(hasil).model_fields)
    assert "f1_makro" in bidang
    assert "f1_mikro" in bidang
    assert "f1" not in bidang


def test_panjang_acuan_dan_prediksi_wajib_sama() -> None:
    """Panjang yang berbeda berarti satu prediksi disandingkan dengan acuan
    yang salah, dan seluruh angka sesudahnya menerangkan hal lain."""
    with pytest.raises(ValueError, match="panjang"):
        hitung_metrik(acuan=["K1", "K2"], prediksi=["K1"])


def test_masukan_kosong_ditolak() -> None:
    """Metrik atas nol contoh bukan 0,0 dan bukan 1,0 — ia bukan metrik.

    Menolaknya di sini lebih baik daripada mengembalikan hasil yang seluruh
    kelasnya belum terhitung: yang kedua terbaca seperti evaluasi yang
    berjalan dan tidak menemukan apa-apa.
    """
    with pytest.raises(ValueError):
        hitung_metrik(acuan=[], prediksi=[])


def test_daftar_kelas_dari_acuan_bila_tidak_diberikan() -> None:
    """Kemudahan yang aman: kelas yang tidak muncul sama sekali tidak
    dilaporkan, sama dengan `kappa_per_kategori` fitur 003."""
    hasil = hitung_metrik(acuan=ACUAN, prediksi=list(ACUAN))
    assert set(hasil.per_kelas) == {"K1", "K2", "K3"}


def test_rerata_makro_melewati_kelas_yang_belum_terhitung() -> None:
    """Kelas tanpa contoh **tidak** dihitung sebagai 0,0 pada rerata makro.

    Memasukkannya menurunkan rerata atas kelas yang tidak pernah diuji, dan
    angka yang turun karena data yang tidak ada adalah angka yang menyesatkan
    ke arah pesimistis — yang sama buruknya dengan menyesatkan ke arah
    sebaliknya.
    """
    acuan = ["K1", "K1", "K2", "K2"]
    hasil = hitung_metrik(acuan=acuan, prediksi=list(acuan), kelas=("K1", "K2", "K9"))
    assert not hasil.per_kelas["K9"].f1.terhitung
    assert hasil.f1_makro.nilai == pytest.approx(1.0)


def test_uraian_menyebut_alasan_pelaporan_per_kelas() -> None:
    """FR-D04 menyebut alasannya — mendeteksi kelas berperforma rendah — dan
    alasan itu wajib tertulis pada modulnya, sebab rerata selalu lebih mudah
    dibaca dan akan menggantikan tabelnya bila tidak ada yang menjelaskan
    mengapa tabelnya ada."""
    import src.nlp.pelatihan.metrik as modul

    uraian = modul.__doc__ or ""
    assert "FR-D04" in uraian
    assert "makro" in uraian.lower()
    assert "mikro" in uraian.lower()


def test_nilai_belum_terhitung_wajib_menyebut_alasannya() -> None:
    """Bentuk yang sama dengan `HasilKesepakatan` fitur 003, dan alasannya
    sama: tanpa alasan pembacanya menebak, dan tebakan yang paling mudah
    adalah "modelnya gagal"."""
    from pydantic import ValidationError
    from src.nlp.pelatihan.metrik import Nilai

    with pytest.raises(ValidationError):
        Nilai(nilai=None)


def test_nilai_tidak_boleh_membawa_angka_sekaligus_alasan() -> None:
    """Dua cerita pada satu baris, dan pembaca akan memilih yang lebih
    menyenangkan."""
    from pydantic import ValidationError
    from src.nlp.pelatihan.metrik import Nilai

    with pytest.raises(ValidationError):
        Nilai(nilai=0.5, alasan="belum lengkap")
