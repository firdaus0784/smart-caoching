"""Uji kualifikasi anotator — C-1 fitur 003, R-14, FR-C09, D-03 Bagian 13.

D-03 Bagian 13 menetapkan syaratnya dalam satu kalimat: 20 dokumen berkunci
jawaban yang disusun adjudikator, dan anotator lulus bila mencapai F1
pencocokan longgar ≥ 0,80 terhadap kunci **dan** Kappa kategori ≥ 0,70.
Kalimat berikutnya yang menentukan taruhannya — "tidak ada anotasi produksi
sebelum lulus".

Tiga hal diuji di sini, dan hanya yang pertama terbaca dari kebutuhannya:

1. **Kedua syarat wajib terpenuhi bersama.** Kata "dan" pada D-03 mudah
   berubah menjadi "atau" ketika seseorang menyusun ulang percabangannya, dan
   perubahan itu tidak menjatuhkan uji mana pun yang hanya memeriksa anotator
   yang memang lulus.

2. **Kualifikasi yang tidak dapat dinilai bukan kelulusan, dan bukan pula
   kegagalan.** Anotator yang tidak menandai apa pun menghasilkan F1 yang
   belum terhitung; melaporkannya "tidak lulus" menyalahkan orang atas
   keadaan yang mungkin berupa berkas yang gagal termuat. Melaporkannya
   "lulus" jauh lebih buruk — ia melepas anotator ke anotasi produksi tanpa
   satu pun bukti. Bentuk yang sama dengan `HasilSistem` fitur 015 dan
   `HasilKesepakatan` pada B-1.

3. **Jumlah dokumennya diperiksa.** Anotator yang lulus atas tiga dokumen
   bukan anotator yang lulus. Ini yang paling mudah luput, sebab ia lolos
   seluruh uji ambang: angkanya benar, bahannya yang tidak cukup.

Ambang diambil dari `src/nlp/anotasi/ambang.py` (B-6), tidak ditulis di sini.
Uji yang menyalin ambangnya akan tetap lulus ketika ambang pada kode disetel.
"""

import pytest
from src.nlp.anotasi.ambang import (
    AMBANG_KUALIFIKASI_F1_LONGGAR,
    AMBANG_KUALIFIKASI_KAPPA,
    JUMLAH_DOKUMEN_KUALIFIKASI,
)
from src.nlp.anotasi.kesepakatan import HasilKesepakatan
from src.nlp.anotasi.kualifikasi import HasilKualifikasi, uji_kualifikasi
from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas
from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema

VERSI = VersiSkema(mayor=1, minor=0)
TEKS = "Kepala sekolah menyusun RKAS tahun anggaran 2026 bersama komite sekolah."

KUNCI = "adjudikator"
CALON = "calon_anotator"

DOKUMEN = LabelEntitas.DOKUMEN
JABATAN = LabelEntitas.JABATAN_PERAN
ANGGARAN = LabelEntitas.ANGGARAN

K1 = KategoriMasalah.K1
K5 = KategoriMasalah.K5


def _r(mulai: int, akhir: int, label: LabelEntitas, anotator: str) -> RentangEntitas:
    return RentangEntitas(
        teks_kanonik=TEKS,
        mulai=mulai,
        akhir=akhir,
        label=label,
        versi_skema=VERSI,
        id_anotator=anotator,
    )


def _p(id_dokumen: str, kategori: KategoriMasalah, anotator: str) -> PutusanKategori:
    return PutusanKategori(
        id_dokumen=id_dokumen,
        kategori_utama=kategori,
        versi_skema=VERSI,
        id_anotator=anotator,
    )


def _kategori_sepakat(jumlah: int) -> tuple[list[PutusanKategori], list[PutusanKategori]]:
    """Putusan yang menghasilkan Kappa tinggi atas `jumlah` dokumen.

    Dua kategori dipakai bergantian dengan sengaja. Satu kategori saja
    menghasilkan pe = 1 dan Kappa yang belum terhitung — keadaan sah yang
    diuji terpisah, dan yang di sini justru akan menyamarkan ujinya.
    """
    kunci = [_p(f"dok{i}", K1 if i % 2 else K5, KUNCI) for i in range(jumlah)]
    calon = [_p(f"dok{i}", K1 if i % 2 else K5, CALON) for i in range(jumlah)]
    return kunci, calon


def _rentang_sepakat() -> tuple[list[RentangEntitas], list[RentangEntitas]]:
    kunci = [_r(24, 28, DOKUMEN, KUNCI), _r(0, 14, JABATAN, KUNCI)]
    calon = [_r(24, 28, DOKUMEN, CALON), _r(0, 14, JABATAN, CALON)]
    return kunci, calon


CUKUP = JUMLAH_DOKUMEN_KUALIFIKASI


def test_anotator_yang_memenuhi_keduanya_lulus() -> None:
    kunci_k, calon_k = _kategori_sepakat(CUKUP)
    kunci_r, calon_r = _rentang_sepakat()
    hasil = uji_kualifikasi(
        rentang_calon=calon_r,
        rentang_kunci=kunci_r,
        kategori_calon=calon_k,
        kategori_kunci=kunci_k,
    )
    assert hasil.dapat_dinilai
    assert hasil.lulus


def test_lulus_f1_saja_tidak_cukup() -> None:
    """**Uji terpenting berkas ini**, bersama pasangannya di bawah.

    Rentang sepakat sempurna sehingga F1 longgar 1,0; kategori dibuat
    setengah bertentangan sehingga Kappa jatuh di bawah ambang. "Dan" yang
    berubah menjadi "atau" meloloskan orang ini.
    """
    kunci_k = [_p(f"dok{i}", K1 if i % 2 else K5, KUNCI) for i in range(CUKUP)]
    calon_k = [_p(f"dok{i}", K5, CALON) for i in range(CUKUP)]
    kunci_r, calon_r = _rentang_sepakat()
    hasil = uji_kualifikasi(
        rentang_calon=calon_r,
        rentang_kunci=kunci_r,
        kategori_calon=calon_k,
        kategori_kunci=kunci_k,
    )
    assert hasil.f1_longgar.nilai == pytest.approx(1.0)
    assert hasil.kappa.nilai is not None
    assert hasil.kappa.nilai < AMBANG_KUALIFIKASI_KAPPA
    assert hasil.dapat_dinilai
    assert not hasil.lulus


def test_lulus_kappa_saja_tidak_cukup() -> None:
    """Sisi lain dari uji sebelumnya: kategori sepakat sempurna, rentang tidak
    bertemu sama sekali sehingga F1 nol."""
    kunci_k, calon_k = _kategori_sepakat(CUKUP)
    kunci_r = [_r(24, 28, DOKUMEN, KUNCI)]
    calon_r = [_r(0, 6, JABATAN, CALON)]
    hasil = uji_kualifikasi(
        rentang_calon=calon_r,
        rentang_kunci=kunci_r,
        kategori_calon=calon_k,
        kategori_kunci=kunci_k,
    )
    assert hasil.kappa.nilai == pytest.approx(1.0)
    assert hasil.f1_longgar.nilai == pytest.approx(0.0)
    assert hasil.dapat_dinilai
    assert not hasil.lulus


def test_tepat_pada_ambang_lulus() -> None:
    """`≥` pada D-03, bukan `>`. Selisih satu tanda menolak orang yang tepat
    memenuhi syarat, dan penolakannya tidak akan terlihat sebagai cacat."""
    hasil = HasilKualifikasi.dari_angka(
        f1_longgar=AMBANG_KUALIFIKASI_F1_LONGGAR,
        kappa=AMBANG_KUALIFIKASI_KAPPA,
        jumlah_dokumen=CUKUP,
    )
    assert hasil.lulus


def test_sedikit_di_bawah_ambang_tidak_lulus() -> None:
    hasil = HasilKualifikasi.dari_angka(
        f1_longgar=AMBANG_KUALIFIKASI_F1_LONGGAR - 0.01,
        kappa=AMBANG_KUALIFIKASI_KAPPA,
        jumlah_dokumen=CUKUP,
    )
    assert hasil.dapat_dinilai
    assert not hasil.lulus


def test_dokumen_kurang_dari_yang_dituntut_belum_dapat_dinilai() -> None:
    """Anotator yang lulus atas tiga dokumen bukan anotator yang lulus.

    Dan ia bukan pula anotator yang gagal — bahannya yang kurang, bukan
    kerjanya. Membedakannya menentukan tindakan berikutnya: menambah dokumen
    uji, bukan mengulang pendampingan.
    """
    kunci_k, calon_k = _kategori_sepakat(4)
    kunci_r, calon_r = _rentang_sepakat()
    hasil = uji_kualifikasi(
        rentang_calon=calon_r,
        rentang_kunci=kunci_r,
        kategori_calon=calon_k,
        kategori_kunci=kunci_k,
    )
    assert not hasil.dapat_dinilai
    assert not hasil.lulus
    assert "dokumen" in hasil.alasan


def test_calon_yang_tidak_menandai_apa_pun_belum_dapat_dinilai() -> None:
    """**Keadaan yang paling berbahaya bila keliru.**

    F1 satu daftar kosong bernilai 0,0 — itu ketidaksepakatan sungguhan
    (B-4). Yang belum terhitung di sini adalah Kappa-nya, sebab tidak ada
    dokumen yang keduanya putuskan. Hasil yang membawa satu ukuran terhitung
    dan satu belum **tidak boleh** dibaca sebagai putusan.
    """
    kunci_k, _ = _kategori_sepakat(CUKUP)
    kunci_r, _ = _rentang_sepakat()
    hasil = uji_kualifikasi(
        rentang_calon=[],
        rentang_kunci=kunci_r,
        kategori_calon=[],
        kategori_kunci=kunci_k,
    )
    assert not hasil.dapat_dinilai
    assert not hasil.lulus


def test_satu_kategori_saja_membuat_kappa_belum_terhitung_dan_hasil_tak_dinilai() -> None:
    """pe = 1 pada B-2: seluruh dokumen satu kategori.

    Kappa yang belum terhitung membuat separuh syarat hilang, dan separuh
    syarat bukan syarat. Bila ini terbaca lulus, anotator yang diuji dengan
    set kalibrasi yang timpang lolos tanpa Kappa pernah diperiksa.
    """
    kunci_k = [_p(f"dok{i}", K5, KUNCI) for i in range(CUKUP)]
    calon_k = [_p(f"dok{i}", K5, CALON) for i in range(CUKUP)]
    kunci_r, calon_r = _rentang_sepakat()
    hasil = uji_kualifikasi(
        rentang_calon=calon_r,
        rentang_kunci=kunci_r,
        kategori_calon=calon_k,
        kategori_kunci=kunci_k,
    )
    assert not hasil.kappa.terhitung
    assert not hasil.dapat_dinilai
    assert not hasil.lulus


def test_hasil_membawa_alasan_ketika_belum_dapat_dinilai() -> None:
    """Hasil tanpa alasan menuntut pembacanya menebak, dan tebakan yang paling
    mudah adalah "anotatornya kurang cakap"."""
    kunci_k, calon_k = _kategori_sepakat(3)
    kunci_r, calon_r = _rentang_sepakat()
    hasil = uji_kualifikasi(
        rentang_calon=calon_r,
        rentang_kunci=kunci_r,
        kategori_calon=calon_k,
        kategori_kunci=kunci_k,
    )
    assert hasil.alasan


def test_alasan_menahan_kelulusan_meskipun_kedua_angka_memenuhi() -> None:
    """**Uji ini lahir dari uji mutasi yang tidak menyala, dan itu sebabnya ia
    ada.**

    Menghapus penjagaan `dapat_dinilai` pada `lulus` semula tidak menjatuhkan
    satu uji pun. Sebabnya bukan penjagaannya berlebihan melainkan seluruh
    keadaan yang diuji kebetulan juga membawa ukuran yang belum terhitung,
    sehingga `memenuhi()` sudah menahannya lebih dulu.

    Yang tidak tertutup: hasil yang dibentuk dengan **kedua angka terhitung
    dan memenuhi ambang, tetapi membawa alasan**. Tanpa penjagaannya, hasil
    seperti itu terbaca lulus — dan hasil seperti itu justru yang muncul
    ketika bahannya kurang tetapi angka yang sempat terhitung tampak baik.
    """
    hasil = HasilKualifikasi(
        f1_longgar=HasilKesepakatan(nilai=0.95, jumlah_satuan=CUKUP),
        kappa=HasilKesepakatan(nilai=0.95, jumlah_satuan=CUKUP),
        jumlah_dokumen=CUKUP,
        alasan="set kalibrasi ditarik kembali oleh adjudikator",
    )
    assert not hasil.dapat_dinilai
    assert not hasil.lulus


def test_hasil_kualifikasi_beku() -> None:
    """Hasil yang dapat diubah setelah dibentuk adalah hasil yang dapat
    dinaikkan menjadi lulus tanpa satu perhitungan pun diulang."""
    hasil = HasilKualifikasi.dari_angka(f1_longgar=0.9, kappa=0.9, jumlah_dokumen=CUKUP)
    with pytest.raises(Exception):  # noqa: B017 — pydantic tidak menjanjikan satu tipe
        hasil.jumlah_dokumen = 1  # type: ignore[misc]


# Kecocokan `JUMLAH_DOKUMEN_KUALIFIKASI` dengan D-03 Bagian 13 diuji pada
# `test_ambang_kesepakatan.py`, tempat pembacaan `docs/D03.md` berada.
# Menyalinnya ke sini hanya akan membuktikan dua salinan sama.
