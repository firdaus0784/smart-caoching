"""Uji pengambilan leksikal BM25 — B-2 fitur 007, R-09, R-13.

ADR-03 memilih BM25 untuk sisi leksikal dengan alasan yang tajam: *"Pertanyaan
manajerial sering memuat istilah regulasi yang harus cocok persis
('Permendikbudristek Nomor 21 Tahun 2022')"*, dan pencarian vektor *"gagal pada
nomor regulasi, justru pada kasus yang paling menuntut ketepatan"*.

**Skor diuji terhadap contoh yang dihitung tangan.** Menguji implementasi
terhadap keluaran implementasi itu sendiri hanya membuktikan ia tetap seperti
kemarin. Rumus BM25 diambil dari Robertson & Zaragoza, sumber yang
`docs/D07.md` Bagian 4.4 kutip, dan diturunkan ulang di sini langkah demi
langkah.

**Pencocokan atas `stem`, bukan `permukaan`** (R-09). Versi yang mencocokkan
permukaan bekerja pada sebagian besar uji — "sekolah" tetap "sekolah" — dan
gagal justru pada kata berimbuhan yang menjadi inti pertanyaan manajerial.
Kegagalannya berupa hasil yang sepi, bukan galat.
"""

import math

import pytest
from src.penyimpanan.indeks import IndeksTujuan, SegmenTerindeks, StatusLisensi
from src.rag.pengambilan.bm25 import SumberBM25, bangun_indeks
from src.rag.pengambilan.tetapan import BM25_B, BM25_K1


def _segmen(
    id_segmen: str, teks: str, *, tujuan: IndeksTujuan = IndeksTujuan.UTAMA
) -> SegmenTerindeks:
    return SegmenTerindeks(
        id_segmen=id_segmen,
        id_dokumen="DOC-" + id_segmen,
        teks=teks,
        lisensi=StatusLisensi.TERBUKA,
        indeks_tujuan=tujuan,
        anonimisasi_terverifikasi=True,
        penanda_bagian="Pasal 1",
    )


KORPUS = (
    _segmen("SEG-A", "Kepala sekolah menyusun RKAS"),
    _segmen("SEG-B", "Kepala sekolah"),
    _segmen("SEG-C", "Guru mengajar kelas satu"),
)
"""Tiga segmen dengan stem yang sudah diperiksa.

`SEG-A` → kepala, sekolah, susun, rkas (4) · `SEG-B` → kepala, sekolah (2) ·
`SEG-C` → guru, ajar, kelas (3). Panjang rata-rata 9/3 = **3,0** — dipilih
bulat agar penurunan tangan di bawah dapat dibaca tanpa kalkulator.
"""


def _sumber(korpus: tuple[SegmenTerindeks, ...] = KORPUS, versi: str = "uji-1") -> SumberBM25:
    return SumberBM25(bangun_indeks(korpus, versi=versi, indeks_tujuan=IndeksTujuan.UTAMA))


# --------------------------------------------------------- skor hitung tangan


def test_skor_terhadap_contoh_yang_dihitung_tangan() -> None:
    """**Uji terpenting B-2.**

    Kueri `RKAS` → satu stem `rkas`, muncul pada satu segmen dari tiga.

    ```
    IDF  = ln(1 + (N - n + 0,5) / (n + 0,5))
         = ln(1 + (3 - 1 + 0,5) / (1 + 0,5))
         = ln(1 + 2,5 / 1,5)
         = ln(2,666…)

    tf   = f · (k1 + 1) / ( f + k1 · (1 - b + b · |D| / avgdl) )
         = 1 · 2,2      / ( 1  + 1,2 · (0,25 + 0,75 · 4 / 3)   )
         = 2,2          / ( 1  + 1,2 · 1,25 )
         = 2,2 / 2,5
         = 0,88

    skor = ln(2,666…) · 0,88  ≈  0,8631
    ```

    Ditulis sebagai ungkapan, bukan sebagai satu bilangan: bilangan tunggal
    yang salah tetap terbaca meyakinkan, sedangkan ungkapan yang salah terbaca
    salah pada langkah tempat kekeliruannya berada.
    """
    hasil = _sumber().cari("RKAS", batas=10)
    diharapkan = math.log(1 + 2.5 / 1.5) * (2.2 / 2.5)

    assert len(hasil.peringkat) == 1
    assert hasil.peringkat[0].id_segmen == "SEG-A"
    assert hasil.peringkat[0].skor == pytest.approx(diharapkan)
    assert hasil.peringkat[0].skor == pytest.approx(0.8631, abs=1e-4)


def test_tetapan_bm25_dari_robertson_dan_zaragoza() -> None:
    """`docs/D07.md` Bagian 4.4 menyebut Robertson & Zaragoza sebagai sumber
    BM25. Nilai k1 = 1,2 dan b = 0,75 adalah nilai baku pada sumber itu —
    dikutip, bukan disetel (C-16, sama dengan konstanta RRF)."""
    assert BM25_K1 == 1.2
    assert BM25_B == 0.75


def test_segmen_lebih_pendek_menang_pada_frekuensi_sama() -> None:
    """Penormalan panjang, dan ia yang membedakan BM25 dari hitungan kata.

    `kepala` muncul sekali pada SEG-A (4 kata) dan sekali pada SEG-B (2 kata).
    Segmen pendek yang memuat kata kueri lebih padat memuatnya, dan BM25
    mengunggulkannya.

    Versi dengan b = 0 lolos uji hitung tangan di atas — kebetulan, sebab di
    sana |D| dan avgdl tidak dibandingkan — dan gagal di sini.
    """
    hasil = _sumber().cari("kepala", batas=10)
    assert [k.id_segmen for k in hasil.peringkat] == ["SEG-B", "SEG-A"]


def test_kata_yang_tersebar_luas_menyumbang_lebih_sedikit() -> None:
    """IDF: `kepala` ada pada dua dari tiga segmen, `rkas` pada satu.

    Kata yang muncul di mana-mana tidak membedakan apa pun, dan pertanyaan
    manajerial penuh dengannya — "sekolah" ada pada hampir setiap segmen
    korpus ini.
    """
    skor_rkas = _sumber().cari("RKAS", batas=10).peringkat[0].skor
    skor_kepala = next(
        k.skor for k in _sumber().cari("kepala", batas=10).peringkat if k.id_segmen == "SEG-A"
    )
    assert skor_rkas > skor_kepala


# ------------------------------------------------------------------------ R-09


def test_pencocokan_atas_stem_bukan_permukaan() -> None:
    """**R-09.** `docs/D07.md` Bagian 3.3: BM25 "dengan penanganan morfologi
    Bahasa Indonesia sesuai modul praproses (FR-B03)".

    "ditugaskan" pada segmen dan "penugasan" pada kueri tidak memiliki satu pun
    permukaan yang sama; keduanya berstem `tugas`. Versi yang mencocokkan
    permukaan mengembalikan **nol** hasil di sini — dan nol hasil terbaca
    sebagai korpus yang tidak memuat jawabannya, bukan sebagai cacat.
    """
    korpus = (_segmen("SEG-T", "Guru ditugaskan kepala sekolah"),)
    hasil = SumberBM25(bangun_indeks(korpus, versi="uji-1", indeks_tujuan=IndeksTujuan.UTAMA)).cari(
        "penugasan", batas=10
    )
    assert [k.id_segmen for k in hasil.peringkat] == ["SEG-T"]


def test_tiga_imbuhan_berbeda_menemukan_segmen_yang_sama() -> None:
    """Sifat, bukan satu kasus."""
    korpus = (_segmen("SEG-T", "Guru ditugaskan kepala sekolah"),)
    sumber = SumberBM25(bangun_indeks(korpus, versi="uji-1", indeks_tujuan=IndeksTujuan.UTAMA))
    for kueri in ("menugaskan", "penugasan", "tugas"):
        assert [k.id_segmen for k in sumber.cari(kueri, batas=10).peringkat] == ["SEG-T"]


# ------------------------------------------------------------------ seri, R-03


def test_seri_diputus_id_segmen() -> None:
    """Dua segmen dengan frekuensi dan panjang sama menghasilkan skor yang
    **persis** sama — bukan hampir sama. Bukan kasus tepi."""
    korpus = (
        _segmen("SEG-D", "Kepala sekolah menyusun RAPBS"),
        _segmen("SEG-A", "Kepala sekolah menyusun RKAS"),
    )
    hasil = SumberBM25(bangun_indeks(korpus, versi="uji-1", indeks_tujuan=IndeksTujuan.UTAMA)).cari(
        "menyusun", batas=10
    )
    assert [k.id_segmen for k in hasil.peringkat] == ["SEG-A", "SEG-D"]
    assert hasil.peringkat[0].skor == pytest.approx(hasil.peringkat[1].skor)


# ----------------------------------------------------------- keadaan tepi


def test_indeks_kosong_menghasilkan_hasil_kosong_bukan_galat() -> None:
    """Korpus kosong adalah keadaan sah — ia keadaan sistem ini hari ini.

    Galat di sini akan membuat setiap uji hulu memerlukan korpus tiruan, dan
    korpus tiruan yang disusun demi meloloskan galat adalah korpus yang tidak
    menguji apa pun.
    """
    hasil = SumberBM25(bangun_indeks((), versi="kosong", indeks_tujuan=IndeksTujuan.UTAMA)).cari(
        "kepala sekolah", batas=10
    )
    assert hasil.peringkat == ()
    assert hasil.versi_indeks == "kosong"


def test_kueri_kosong_ditolak() -> None:
    with pytest.raises(ValueError, match="kueri"):
        _sumber().cari("   ", batas=10)


def test_kueri_yang_seluruhnya_stop_word_menghasilkan_kosong_bukan_galat() -> None:
    """**Perbedaan yang menentukan.** Kueri kosong adalah pemanggilan yang
    keliru; kueri berisi hanya kata fungsi adalah pertanyaan sungguhan yang
    tidak memuat kata kunci.

    Yang kedua wajib berakhir pada balasan tidak-ditemukan (FR-F04), bukan pada
    pesan galat. D-05 memisahkan keduanya sebagai keadaan layar yang berbeda,
    dan pengguna yang menerima pesan galat menyimpulkan sistemnya rusak.
    """
    hasil = _sumber().cari("dan yang di", batas=10)
    assert hasil.peringkat == ()


def test_kueri_tanpa_kecocokan_menghasilkan_kosong() -> None:
    assert _sumber().cari("Dapodik", batas=10).peringkat == ()


def test_batas_memangkas_dari_atas() -> None:
    hasil = _sumber().cari("kepala sekolah", batas=1)
    assert [k.id_segmen for k in hasil.peringkat] == ["SEG-B"]


# ------------------------------------------------------- R-13 dan pemisahan indeks


def test_versi_indeks_ikut_pada_setiap_hasil() -> None:
    """**R-13**, D-07 Bagian 3.3 dan RT-05."""
    assert _sumber(versi="indeks-2026-08-12").cari("kepala", batas=5).versi_indeks == (
        "indeks-2026-08-12"
    )


def test_indeks_menolak_segmen_dari_indeks_tujuan_lain() -> None:
    """**Penjagaan yang menopang C-02.**

    Satu indeks melayani satu indeks tujuan. Indeks yang memuat keduanya
    membuat pemeriksaan kredensial pada C-1 tidak berarti apa pun: kredensial
    diperiksa terhadap indeks tujuan sumber, dan sumber yang mengaku `utama`
    tetapi memuat segmen `metadata` meloloskan keduanya.
    """
    with pytest.raises(ValueError, match="indeks tujuan"):
        bangun_indeks(
            (_segmen("SEG-M", "Abstrak artikel", tujuan=IndeksTujuan.METADATA),),
            versi="uji-1",
            indeks_tujuan=IndeksTujuan.UTAMA,
        )


def test_indeks_menolak_id_segmen_kembar() -> None:
    with pytest.raises(ValueError, match="kembar"):
        bangun_indeks(
            (_segmen("SEG-A", "Satu"), _segmen("SEG-A", "Dua")),
            versi="uji-1",
            indeks_tujuan=IndeksTujuan.UTAMA,
        )


def test_sumber_menyatakan_indeks_tujuan_indeksnya() -> None:
    sumber = SumberBM25(bangun_indeks((), versi="v", indeks_tujuan=IndeksTujuan.METADATA))
    assert sumber.indeks_tujuan is IndeksTujuan.METADATA
    assert sumber.nama == "bm25"
