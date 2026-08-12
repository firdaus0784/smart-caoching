"""Uji kontrak kandidat dan sumbernya — B-1 fitur 007, R-01, R-02, R-03.

Tiga sifat diuji di sini, dan yang ketiga paling mudah dianggap berlebihan.

**Pengambilan berjalan atas segmen** (R-01, D-07 Bagian 3.2). Kandidat membawa
`id_segmen`, bukan `id_dokumen`. Dokumen yang dikembalikan utuh membanjiri
konteks dan menghilangkan penanda bagian yang FR-F11 tuntut.

**Peringkat sama pada masukan sama** (R-02). Tanpanya, satu percobaan tidak
dapat diulang, dan D-10 L1 mencatat percobaan yang hasilnya tidak dapat
diperiksa siapa pun.

**Seri diputus secara tetap** (R-03). Dua segmen berskor identik lazim pada
korpus kecil — dan pada BM25, dua segmen yang memuat kata kueri dengan
frekuensi sama menghasilkan skor yang persis sama, bukan hampir sama. Urutan
sisipan bergantung pada urutan pembacaan berkas, sehingga hasil yang
mengikutinya berubah ketika berkas dibaca dengan urutan lain. R-02 gugur tanpa
satu galat pun.
"""

import pytest
from pydantic import ValidationError
from src.kamus.segmen import IndeksTujuan
from src.rag.pengambilan.kandidat import HasilSumber, Kandidat, urutkan_kandidat
from tests.rag.pengambilan.sumber_tiruan import SumberTiruan


def test_kandidat_membawa_id_segmen_bukan_id_dokumen() -> None:
    """**R-01.** D-07 Bagian 3.2 menetapkan pengambilan atas segmen.

    Sifat, bukan kasus: bidang `id_dokumen` yang ditambahkan kelak akan
    mengundang pemanggil mengembalikan dokumen utuh ketika hasilnya terasa
    kurang.
    """
    assert "id_segmen" in Kandidat.model_fields
    assert "id_dokumen" not in Kandidat.model_fields


def test_kandidat_beku() -> None:
    kandidat = Kandidat(id_segmen="SEG-001", skor=1.5)
    with pytest.raises(ValidationError):
        kandidat.skor = 9.0  # type: ignore[misc]


def test_id_segmen_kosong_ditolak() -> None:
    with pytest.raises(ValidationError):
        Kandidat(id_segmen="", skor=1.0)


def test_skor_negatif_ditolak() -> None:
    """BM25 dan RRF keduanya menghasilkan skor tak-negatif. Skor negatif berarti
    perhitungannya keliru, dan menerimanya membuat kekeliruan itu terurut
    seperti hasil yang sah — di paling bawah, tanpa ada yang melihat."""
    with pytest.raises(ValidationError):
        Kandidat(id_segmen="SEG-001", skor=-0.1)


# ------------------------------------------------------------------ R-02, R-03


def test_urutan_menurun_menurut_skor() -> None:
    hasil = urutkan_kandidat(
        [
            Kandidat(id_segmen="SEG-B", skor=0.5),
            Kandidat(id_segmen="SEG-A", skor=2.0),
            Kandidat(id_segmen="SEG-C", skor=1.0),
        ]
    )
    assert [k.id_segmen for k in hasil] == ["SEG-A", "SEG-C", "SEG-B"]


def test_seri_diputus_id_segmen_bukan_urutan_sisipan() -> None:
    """**Uji terpenting B-1.**

    Dua daftar dengan isi sama tetapi urutan sisipan berbeda wajib menghasilkan
    peringkat yang sama. Versi yang mengandalkan kestabilan `sorted` akan
    mengembalikan urutan sisipan pada skor yang seri — dan urutan sisipan
    datang dari urutan pembacaan berkas.
    """
    maju = urutkan_kandidat(
        [
            Kandidat(id_segmen="SEG-C", skor=1.0),
            Kandidat(id_segmen="SEG-A", skor=1.0),
            Kandidat(id_segmen="SEG-B", skor=1.0),
        ]
    )
    mundur = urutkan_kandidat(
        [
            Kandidat(id_segmen="SEG-B", skor=1.0),
            Kandidat(id_segmen="SEG-A", skor=1.0),
            Kandidat(id_segmen="SEG-C", skor=1.0),
        ]
    )
    assert [k.id_segmen for k in maju] == ["SEG-A", "SEG-B", "SEG-C"]
    assert maju == mundur


def test_seri_sebagian_tetap_menghormati_skor_lebih_dulu() -> None:
    """Pemutus seri berlaku **di dalam** kelompok berskor sama, bukan
    menggantikan urutan skor. Versi yang mengurutkan `id_segmen` lebih dulu
    lolos uji sebelumnya dan gagal di sini."""
    hasil = urutkan_kandidat(
        [
            Kandidat(id_segmen="SEG-Z", skor=9.0),
            Kandidat(id_segmen="SEG-A", skor=1.0),
            Kandidat(id_segmen="SEG-B", skor=1.0),
        ]
    )
    assert [k.id_segmen for k in hasil] == ["SEG-Z", "SEG-A", "SEG-B"]


def test_peringkat_sama_pada_masukan_sama() -> None:
    """**R-02.** Dijalankan dua kali pada sumber yang sama."""
    sumber = SumberTiruan("tiruan", {"SEG-A": 1.0, "SEG-B": 2.0, "SEG-C": 2.0})
    pertama = sumber.cari("kepala sekolah", batas=10)
    kedua = sumber.cari("kepala sekolah", batas=10)
    assert pertama.peringkat == kedua.peringkat


# ------------------------------------------------------------------ HasilSumber


def test_hasil_sumber_membawa_versi_indeks() -> None:
    """D-07 Bagian 3.3: "Setiap pembangunan ulang menghasilkan nomor versi;
    tercatat pada setiap jawaban (RT-05)."

    Tanpanya, dua percobaan atas indeks berbeda tidak dapat dibedakan pada
    catatan D-10 L1, dan perbandingan antarpercobaan menjadi perbandingan yang
    tidak diketahui apa yang berubah.
    """
    hasil = SumberTiruan("bm25", {"SEG-A": 1.0}, versi_indeks="indeks-2026-08-12").cari(
        "kueri", batas=5
    )
    assert hasil.versi_indeks == "indeks-2026-08-12"


def test_hasil_sumber_menyatakan_peringkat_setiap_kandidat() -> None:
    """Peringkat dihitung dari posisinya, bukan disimpan terpisah.

    Dua sumber kebenaran bagi hal yang sama akan berbeda ketika salah satunya
    disunting, dan yang berbeda adalah yang tidak diperbarui.
    """
    hasil = SumberTiruan("bm25", {"SEG-A": 3.0, "SEG-B": 2.0, "SEG-C": 1.0}).cari("q", batas=5)
    assert hasil.peringkat_dari("SEG-A") == 1
    assert hasil.peringkat_dari("SEG-C") == 3
    assert hasil.peringkat_dari("SEG-TIDAK-ADA") is None


def test_batas_memangkas_bukan_mengisi() -> None:
    """Kandidat yang lebih sedikit daripada batas diteruskan seluruhnya.

    Mengisi sampai penuh dengan segmen berskor nol memberi penyusun jawaban
    bahan yang tidak relevan, dan penilaian kecukupan bukti kemudian menghitung
    bahan itu sebagai bukti.
    """
    sumber = SumberTiruan("bm25", {"SEG-A": 3.0, "SEG-B": 2.0})
    assert len(sumber.cari("q", batas=10).peringkat) == 2
    assert len(sumber.cari("q", batas=1).peringkat) == 1


def test_sumber_menyatakan_indeks_tujuannya() -> None:
    """Dipakai C-1: kredensial diperiksa terhadap indeks tujuan sumber
    **sebelum** sumber dijalankan."""
    assert SumberTiruan("m", {}, indeks_tujuan=IndeksTujuan.METADATA).indeks_tujuan is (
        IndeksTujuan.METADATA
    )


def test_hasil_sumber_beku() -> None:
    hasil = HasilSumber(nama_sumber="bm25", versi_indeks="v1", peringkat=())
    with pytest.raises(ValidationError):
        hasil.nama_sumber = "lain"  # type: ignore[misc]


def test_hasil_sumber_menolak_id_segmen_kembar() -> None:
    """Satu segmen dua kali pada satu daftar peringkat membuat RRF
    menjumlahkan sumbangannya dua kali dari sumber yang sama — segmen itu naik
    tanpa satu pun sumber kedua menyetujuinya."""
    with pytest.raises(ValidationError) as galat:
        HasilSumber(
            nama_sumber="bm25",
            versi_indeks="v1",
            peringkat=(
                Kandidat(id_segmen="SEG-A", skor=2.0),
                Kandidat(id_segmen="SEG-A", skor=1.0),
            ),
        )
    assert "kembar" in str(galat.value).lower() or "ganda" in str(galat.value).lower()
