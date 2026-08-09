"""Uji uraian modul kesepakatan — B-5 fitur 003, R-09, D-03 Bagian 11.

**Berkas ini menjaga satu kalimat, dan kalimat itu yang paling mahal bila
hilang.**

R-08 sudah ditegakkan tanda tangan: `kappa_kategori` menerima
`PutusanKategori`, `f1_rentang` menerima `RentangEntitas`, dan keduanya
menolak yang lain. Penjagaan itu bekerja — tetapi ia hanya menghentikan
seseorang, tidak menjelaskan apa pun kepadanya.

Yang terjadi tanpa penjelasannya sudah dapat diperkirakan. Pembaca berikutnya
menemukan dua fungsi yang menghitung dua ukuran berbeda untuk dua jenis tugas
yang tampak serupa, menyimpulkan bahwa itu warisan yang belum sempat
dirapikan, dan **mengubah tipenya** — karena mengubah tipe adalah hambatan
kecil bagi orang yang yakin sedang merapikan. Angka yang dihasilkannya akan
terlihat meyakinkan, tidak akan menjatuhkan satu uji pun selain uji tanda
tangan, dan akan masuk naskah sebagai bukti mutu anotasi.

Karena itu R-09 menuntut **alasannya**, bukan aturannya. Aturan yang
dinyatakan tanpa alasan adalah aturan yang akan dilanggar oleh orang yang
mengira ia usang.

Rujukannya ikut diuji karena D-00 Bagian 3 melarang dokumen lain menyalin
milik pemiliknya. Alasan penolakan Kappa dimiliki D-03 Bagian 11 dan
landasan literaturnya D-11 Bagian 3.2; uraian yang menyalinnya akan tertinggal
ketika keduanya berubah, dan uraian yang tertinggal lebih buruk daripada
uraian yang tidak ada.
"""

import src.nlp.anotasi.kesepakatan as modul_kesepakatan
import src.nlp.anotasi.rentang as modul_rentang


def _uraian(modul: object) -> str:
    return (modul.__doc__ or "").lower()


def test_uraian_menyatakan_kappa_tidak_dipakai_bagi_rentang() -> None:
    """Kesimpulannya. Ia yang paling mudah dibaca, dan paling sedikit gunanya
    sendirian — uji berikutnya yang menjaga bagian yang sesungguhnya."""
    uraian = _uraian(modul_kesepakatan)
    assert "kappa" in uraian
    assert "tidak dipakai bagi anotasi rentang" in uraian


def test_uraian_menyatakan_alasannya_bukan_hanya_aturannya() -> None:
    """**Uji terpenting berkas ini.**

    Tiga kata yang diperiksa adalah tiga langkah alasannya, dan ketiganya
    dituntut ada bersama:

    - *kesempatan* — satuan yang jumlahnya tidak terdefinisi pada rentang
    - *acak* — peluang kesepakatan kebetulan, yang karena itu tidak terhitung
    - *bermakna* — akibatnya pada angka yang dihasilkan

    Uraian yang hanya menyebut kesimpulannya lolos uji sebelumnya dan gagal di
    sini, dan itu memang pembedaan yang dituju.
    """
    uraian = _uraian(modul_kesepakatan)
    assert "kesempatan" in uraian
    assert "acak" in uraian
    assert "bermakna" in uraian


def test_alasannya_dirujuk_ke_pemiliknya_bukan_disalin() -> None:
    """D-03 Bagian 11 memiliki aturannya; D-11 Bagian 3.2 memuat landasan
    literaturnya. Keduanya disebut agar pembaca dapat memeriksa sendiri."""
    uraian = modul_kesepakatan.__doc__ or ""
    assert "D-03 Bagian 11" in uraian
    assert "D-11 Bagian 3.2" in uraian


def test_rujukan_literaturnya_disebut_dengan_nama() -> None:
    """Dua rujukan yang D-03 Bagian 11 pakai untuk menolak Kappa.

    Nomor bagian saja menuntut pembacanya membuka dokumen lain sebelum tahu
    bahwa penolakan ini punya landasan di luar pendapat tim. Nama penulisnya
    menyampaikan itu pada baris yang sedang dibacanya.
    """
    uraian = modul_kesepakatan.__doc__ or ""
    assert "Artstein" in uraian
    assert "Hripcsak" in uraian


def test_alasannya_juga_ada_pada_modul_tipenya() -> None:
    """Ditulis dua kali dengan sengaja, dan itu bukan pengulangan yang lalai.

    Orang yang hendak menyeragamkan dua ukuran akan membuka **modul tipenya**
    lebih dulu — di sanalah pemisahan yang menghalanginya berada, dan di sana
    pula ia akan mengubahnya. Uraian yang hanya ada pada modul perhitungan
    tidak terbaca olehnya sampai sesudah perubahannya dibuat.
    """
    uraian = _uraian(modul_rentang)
    assert "kappa" in uraian
    assert "kesempatan" in uraian
    assert "D-03 Bagian 11" in (modul_rentang.__doc__ or "")


def test_godaan_penyeragamannya_dinamai() -> None:
    """Menamai godaannya membuat pembaca mengenali dirinya sendiri di dalamnya.

    Uraian yang hanya melarang tidak melakukan itu — ia berbicara kepada orang
    lain, dan setiap pembaca menganggap dirinya bukan orang lain itu.
    """
    assert "kerapian" in _uraian(modul_rentang)


def test_tanda_tangan_dinyatakan_sebagai_yang_menegakkannya() -> None:
    """Uraian yang menyatakan dirinya sebagai penjaga adalah uraian yang
    menyesatkan: ia tidak menjatuhkan apa pun.

    Yang menjatuhkan adalah tipenya, dan itu perlu tertulis supaya pembaca
    tahu ke mana harus melihat — dan supaya ia tahu bahwa menghapus uraian ini
    tidak melonggarkan penjagaannya."""
    for modul in (modul_kesepakatan, modul_rentang):
        assert "tanda tangan" in _uraian(modul), modul.__name__


def test_fungsi_f1_menyebut_sisi_lain_dari_penjagaannya() -> None:
    """`f1_rentang` menolak `PutusanKategori`, dan alasannya bukan simetri
    belaka: F1 atas satuan analisis yang tetap salah dengan cara yang
    berlawanan. Tanpa itu penolakannya terbaca sebagai kerapian tipe."""
    uraian = (modul_kesepakatan.f1_rentang.__doc__ or "").lower()
    assert "kappa" in uraian
    assert "putusankategori" in uraian


def test_fungsi_kappa_menyatakan_apa_yang_ditegakkan_tanda_tangannya() -> None:
    """Yang membuka `kappa_kategori` mungkin tidak membaca uraian modulnya —
    ia mencari satu fungsi dan langsung menuju ke sana."""
    uraian = modul_kesepakatan.kappa_kategori.__doc__ or ""
    assert "RentangEntitas" in uraian
    assert "D-03 Bagian 11" in uraian
