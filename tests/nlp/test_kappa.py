"""Uji Cohen's Kappa — B-2 fitur 003, R-07, D-03 Bagian 11.

**Seluruh nilai yang diharapkan pada berkas ini dihitung tangan**, dan
perhitungannya ditulis pada uraian tiap uji. Uji yang membandingkan keluaran
dengan keluaran hanya membuktikan hasilnya tidak berubah — termasuk ketika ia
salah sejak awal.
"""

import pytest
from src.nlp.anotasi.kesepakatan import kappa_kategori
from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas
from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema

VERSI = VersiSkema(mayor=1, minor=0)


def _putusan(id_dokumen: str, kategori: KategoriMasalah, anotator: str) -> PutusanKategori:
    return PutusanKategori(
        id_dokumen=id_dokumen,
        kategori_utama=kategori,
        versi_skema=VERSI,
        id_anotator=anotator,
    )


def _pasangan(pola: list[tuple[KategoriMasalah, KategoriMasalah]]):
    a = [_putusan(f"dok_{i}", x, "ant_a") for i, (x, _) in enumerate(pola)]
    b = [_putusan(f"dok_{i}", y, "ant_b") for i, (_, y) in enumerate(pola)]
    return a, b


K1, K5 = KategoriMasalah.K1, KategoriMasalah.K5


def test_kesepakatan_sempurna_menghasilkan_satu() -> None:
    """po = 1, sehingga (po - pe) / (1 - pe) = 1 berapa pun pe."""
    a, b = _pasangan([(K1, K1)] * 30 + [(K5, K5)] * 30)
    assert kappa_kategori(a, b).nilai == pytest.approx(1.0)


def test_kesepakatan_setara_kebetulan_menghasilkan_nol() -> None:
    """po = pe, sehingga pembilangnya nol.

    Tabel: 25 / 25 / 25 / 25 atas 100 dokumen.
    po = (25 + 25) / 100 = 0,50
    pe = 0,5 * 0,5 + 0,5 * 0,5 = 0,50
    kappa = (0,50 - 0,50) / (1 - 0,50) = 0
    """
    a, b = _pasangan([(K1, K1)] * 25 + [(K1, K5)] * 25 + [(K5, K1)] * 25 + [(K5, K5)] * 25)
    assert kappa_kategori(a, b).nilai == pytest.approx(0.0)


def test_kesetujuan_tinggi_dengan_kappa_nol() -> None:
    """**Uji terpenting berkas ini**, dan yang paling mudah luput.

    Dua anotator sepakat pada 82 dari 100 dokumen — angka yang terdengar
    baik — tetapi seluruhnya dijelaskan oleh satu kategori yang mendominasi.

    Tabel: 81 / 9 / 9 / 1 atas 100 dokumen.
    po = (81 + 1) / 100 = 0,82
    pe = 0,9 * 0,9 + 0,1 * 0,1 = 0,81 + 0,01 = 0,82
    kappa = (0,82 - 0,82) / (1 - 0,82) = 0

    Inilah keadaan yang D-03 Bagian 11 cari, dan modul yang keliru akan
    melaporkan 0,82 di sini. Uji terhadap kesepakatan sempurna saja tidak akan
    menangkapnya.
    """
    a, b = _pasangan([(K1, K1)] * 81 + [(K1, K5)] * 9 + [(K5, K1)] * 9 + [(K5, K5)] * 1)
    assert kappa_kategori(a, b).nilai == pytest.approx(0.0)


def test_tabel_dua_kali_dua_dihitung_tangan() -> None:
    """Tabel: 40 / 10 / 15 / 35 atas 100 dokumen.

    po = (40 + 35) / 100 = 0,75
    Sisi A: K1 = 50, K5 = 50 → 0,50 dan 0,50
    Sisi B: K1 = 55, K5 = 45 → 0,55 dan 0,45
    pe = 0,50 * 0,55 + 0,50 * 0,45 = 0,275 + 0,225 = 0,50
    kappa = (0,75 - 0,50) / (1 - 0,50) = 0,50
    """
    a, b = _pasangan([(K1, K1)] * 40 + [(K1, K5)] * 10 + [(K5, K1)] * 15 + [(K5, K5)] * 35)
    assert kappa_kategori(a, b).nilai == pytest.approx(0.50)


def test_kesepakatan_lebih_buruk_daripada_kebetulan_bernilai_negatif() -> None:
    """Kappa berkisar -1 sampai 1, dan nilai negatif bukan kekeliruan.

    Tabel: 10 / 40 / 40 / 10 atas 100 dokumen.
    po = 0,20; pe = 0,5 * 0,5 + 0,5 * 0,5 = 0,50
    kappa = (0,20 - 0,50) / 0,50 = -0,60

    Nilai negatif menandakan anotator sistematis berbeda — misalnya salah satu
    membaca pedoman terbalik — dan itu keterangan yang berguna, bukan galat.
    """
    a, b = _pasangan([(K1, K1)] * 10 + [(K1, K5)] * 40 + [(K5, K1)] * 40 + [(K5, K5)] * 10)
    assert kappa_kategori(a, b).nilai == pytest.approx(-0.60)


def test_daftar_kosong_belum_terhitung() -> None:
    """Bukan 0,0 dan bukan 1,0 — B-1."""
    hasil = kappa_kategori([], [])
    assert not hasil.terhitung
    assert hasil.alasan


def test_dokumen_yang_hanya_dianotasi_satu_pihak_dilewati() -> None:
    """Anotasi ganda 15% berarti 85% dokumen hanya punya satu anotator.

    Memasukkan dokumen berpihak tunggal sebagai ketidaksepakatan akan
    menurunkan Kappa atas hal yang bukan ketidaksepakatan.
    """
    a = [
        _putusan("dok_0", K1, "ant_a"),
        _putusan("dok_1", K5, "ant_a"),
        _putusan("dok_2", K1, "ant_a"),
    ]
    b = [_putusan("dok_0", K1, "ant_b"), _putusan("dok_1", K5, "ant_b")]
    hasil = kappa_kategori(a, b)
    assert hasil.jumlah_satuan == 2, "dok_2 hanya dianotasi satu pihak dan wajib dilewati"


def test_tanpa_dokumen_bersama_belum_terhitung() -> None:
    """Dua anotator yang tidak pernah menganotasi dokumen yang sama tidak
    memiliki kesepakatan untuk dihitung — dan itu bukan kesepakatan nol."""
    a = [_putusan("dok_0", K1, "ant_a")]
    b = [_putusan("dok_1", K1, "ant_b")]
    assert not kappa_kategori(a, b).terhitung


def test_versi_skema_berbeda_dikeluarkan_dan_ditandai() -> None:
    """Keadaan yang `spec.md` tuntut: dua anotator, satu dokumen, versi skema
    berbeda.

    Menghitungnya seolah setara berarti membandingkan label yang artinya sudah
    berubah — dan angkanya akan tampak sebagai ketidaksepakatan anotator,
    bukan sebagai perubahan skema.
    """
    lain = VersiSkema(mayor=2, minor=0)
    a = [_putusan("dok_0", K1, "ant_a")]
    b = [
        PutusanKategori(
            id_dokumen="dok_0", kategori_utama=K1, versi_skema=lain, id_anotator="ant_b"
        )
    ]
    hasil = kappa_kategori(a, b)
    assert not hasil.terhitung
    assert "versi" in hasil.alasan.lower()


def test_satu_kategori_saja_belum_terhitung() -> None:
    """Ketika kedua anotator hanya memakai satu kategori, pe = 1 dan
    pembaginya nol.

    Membaginya menghasilkan galat pembagian; melaporkannya 1,0 lebih buruk —
    kesepakatan sempurna atas tugas yang tidak memiliki pilihan bukan bukti
    apa pun.
    """
    a, b = _pasangan([(K1, K1)] * 20)
    hasil = kappa_kategori(a, b)
    assert not hasil.terhitung
    assert hasil.alasan


def test_kappa_menolak_anotasi_rentang() -> None:
    """**Sifat yang menegakkan D-03 Bagian 11** — R-08.

    Bukan uji nilai melainkan uji bentuk. Fungsi ini tidak boleh menerima
    `RentangEntitas` sama sekali, sehingga penyeragaman dua ukuran menuntut
    mengubah tanda tangannya.
    """
    teks = "Kepala sekolah menyusun RKAS."
    rentang = RentangEntitas(
        teks_kanonik=teks,
        mulai=24,
        akhir=28,
        label=LabelEntitas.DOKUMEN,
        versi_skema=VERSI,
        id_anotator="ant_a",
    )
    with pytest.raises((TypeError, AttributeError)):
        kappa_kategori([rentang], [rentang])  # type: ignore[list-item]
