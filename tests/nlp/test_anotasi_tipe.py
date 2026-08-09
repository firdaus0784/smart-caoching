"""Uji tipe anotasi — A-4 dan A-5 fitur 003, R-05 s.d. R-08, C-10.

Dua tipe, dan pemisahannya bukan kerapian melainkan **penjagaan**.

`PutusanKategori` dan `RentangEntitas` tidak dapat saling menggantikan, dan
itulah yang membuat Cohen's Kappa tidak dapat dipanggil atas anotasi rentang.
Tanpa pemisahan itu, menyeragamkan dua ukuran menjadi satu adalah perubahan
satu baris yang tampak seperti kerapian — dan itu persis kekeliruan yang D-03
Bagian 11 tolak dengan dua rujukan literatur.
"""

import pytest
from pydantic import ValidationError
from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas
from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema

TEKS = "Kepala sekolah menyusun RKAS tahun anggaran 2026 bersama bendahara."
VERSI = VersiSkema(mayor=1, minor=0)


def _rentang(mulai: int = 24, akhir: int = 28, label: LabelEntitas = LabelEntitas.DOKUMEN):
    return RentangEntitas(
        teks_kanonik=TEKS,
        mulai=mulai,
        akhir=akhir,
        label=label,
        versi_skema=VERSI,
        id_anotator="ant_01",
    )


def test_rentang_menyimpan_potongan_teksnya() -> None:
    assert _rentang().teks_rentang == "RKAS"


def test_rentang_yang_tidak_cocok_ditolak_bukan_diperbaiki() -> None:
    """**Uji terpenting berkas ini** — R-06.

    Rentang yang diperbaiki diam-diam menunjuk kata lain tanpa satu galat
    pun, dan kekeliruannya baru terlihat ketika korpusnya sudah terbangun.
    Bentuk kegagalan yang sama dengan stemming yang menimpa permukaan pada
    fitur 015.
    """
    with pytest.raises(ValidationError):
        RentangEntitas(
            teks_kanonik=TEKS,
            mulai=24,
            akhir=28,
            label=LabelEntitas.DOKUMEN,
            versi_skema=VERSI,
            id_anotator="ant_01",
            teks_rentang="ANGGARAN",
        )


def test_rentang_di_luar_panjang_teks_ditolak() -> None:
    with pytest.raises(ValidationError):
        _rentang(mulai=0, akhir=len(TEKS) + 5)


def test_rentang_terbalik_ditolak() -> None:
    with pytest.raises(ValidationError):
        _rentang(mulai=28, akhir=24)


def test_rentang_kosong_ditolak() -> None:
    """Rentang sepanjang nol karakter tidak menunjuk apa pun, dan dua rentang
    kosong pada tempat yang sama akan terhitung sepakat."""
    with pytest.raises(ValidationError):
        _rentang(mulai=24, akhir=24)


def test_rentang_beku() -> None:
    with pytest.raises(ValidationError):
        _rentang().mulai = 0  # type: ignore[misc]


def test_rentang_wajib_membawa_versi_skema() -> None:
    """R-03 — anotasi tanpa versi skema tidak dapat diperiksa ulang siapa pun
    ketika skemanya sudah berubah."""
    with pytest.raises(ValidationError):
        RentangEntitas(
            teks_kanonik=TEKS,
            mulai=24,
            akhir=28,
            label=LabelEntitas.DOKUMEN,
            id_anotator="ant_01",
        )  # type: ignore[call-arg]


def test_rentang_wajib_membawa_anotatornya() -> None:
    """Kesepakatan antar-anotator tidak dapat dihitung dari anotasi yang tidak
    diketahui siapa pembuatnya."""
    with pytest.raises(ValidationError):
        RentangEntitas(
            teks_kanonik=TEKS,
            mulai=24,
            akhir=28,
            label=LabelEntitas.DOKUMEN,
            versi_skema=VERSI,
        )  # type: ignore[call-arg]


def test_putusan_kategori_terbentuk() -> None:
    putusan = PutusanKategori(
        id_dokumen="dok_01",
        kategori_utama=KategoriMasalah.K5,
        versi_skema=VERSI,
        id_anotator="ant_01",
    )
    assert putusan.kategori_utama is KategoriMasalah.K5
    assert putusan.kategori_sekunder is None


def test_kategori_sekunder_tidak_boleh_sama_dengan_utama() -> None:
    """Dua kategori yang sama pada satu dokumen menghasilkan dokumen yang
    terhitung dua kali pada distribusi label."""
    with pytest.raises(ValidationError):
        PutusanKategori(
            id_dokumen="dok_01",
            kategori_utama=KategoriMasalah.K5,
            kategori_sekunder=KategoriMasalah.K5,
            versi_skema=VERSI,
            id_anotator="ant_01",
        )


def test_kedua_tipe_tidak_dapat_saling_menggantikan() -> None:
    """**Sifat yang menjaga seluruh Fase B** — A-5.

    Bukan uji nilai melainkan uji bentuk: keduanya tidak berbagi induk selain
    `BaseModel`, sehingga fungsi yang menerima salah satunya tidak akan
    menerima yang lain tanpa mengubah tanda tangannya.
    """
    assert not issubclass(RentangEntitas, PutusanKategori)
    assert not issubclass(PutusanKategori, RentangEntitas)


def test_putusan_kategori_tidak_memiliki_rentang() -> None:
    """Bidang rentang pada putusan kategori akan mengundang seseorang
    menghitung F1 atasnya, dan F1 atas satuan tetap adalah ukuran yang salah
    dengan cara yang berlawanan dari Kappa atas rentang."""
    assert not {"mulai", "akhir", "teks_rentang"} & set(PutusanKategori.model_fields)


def test_rentang_tidak_memiliki_kategori() -> None:
    assert not {"kategori_utama", "kategori_sekunder"} & set(RentangEntitas.model_fields)


def test_indeks_dihitung_dalam_karakter() -> None:
    """C-10 — diuji dengan teks ber-aksen agar perbedaan karakter dan bita
    benar-benar muncul."""
    teks = "Koordinasi lintas-jenjang di sekolah Kâmpung"
    rentang = RentangEntitas(
        teks_kanonik=teks,
        mulai=teks.index("Kâmpung"),
        akhir=teks.index("Kâmpung") + 7,
        label=LabelEntitas.INSTANSI,
        versi_skema=VERSI,
        id_anotator="ant_01",
    )
    assert rentang.teks_rentang == "Kâmpung"


def test_teks_rentang_yang_cocok_diterima_apa_adanya() -> None:
    """Sisi lain R-06: yang **cocok** diterima tanpa dihitung ulang.

    Penting bagi fitur 016, yang akan membawa `teks_rentang` dari berkas
    ekspor Label Studio. Bila yang cocok pun ditolak, tidak ada anotasi luar
    yang dapat masuk sama sekali.
    """
    rentang = RentangEntitas(
        teks_kanonik=TEKS,
        mulai=24,
        akhir=28,
        label=LabelEntitas.DOKUMEN,
        versi_skema=VERSI,
        id_anotator="ant_01",
        teks_rentang="RKAS",
    )
    assert rentang.teks_rentang == "RKAS"
