"""Uji penyusun pengambilan hibrida — C-1 fitur 007, R-07, R-14, C-02, C-17.

**Di sinilah C-02 berhenti menjadi pernyataan dan menjadi perilaku.** Fitur 006
memisahkan indeks dan memberi setiap kredensial daftar indeks yang
dijangkaunya; berkas ini adalah tempat pertama daftar itu benar-benar
membatasi sesuatu.

Yang diuji bukan "hasilnya tidak memuat segmen metadata". Itu pernyataan yang
lebih lemah daripada kelihatannya — ia dipenuhi juga oleh penyaringan sesudah
pencarian, dan C-02 kalimat kedua menolak penyaringan: *"Pemisahan pada tingkat
indeks, bukan penyaringan saat kueri."*

Yang diuji: **sumber pada indeks yang tidak dijangkau kredensial tidak
dijalankan sama sekali.** `SumberTiruan.dipanggil` yang membuat pernyataan itu
dapat dibuat.
"""

import pytest
from pydantic import ValidationError
from src.penyimpanan.indeks import IndeksTujuan
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, VERIFIKASI
from src.rag.pengambilan.hibrida import ambil_hibrida
from src.rag.pengambilan.tetapan import (
    JUMLAH_KANDIDAT_PER_SUMBER,
    JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM,
)
from tests.rag.pengambilan.sumber_tiruan import SumberTiruan


def _pasangan() -> tuple[SumberTiruan, SumberTiruan]:
    """Dua sumber pada indeks utama — susunan lazim jalur penjawaban."""
    return (
        SumberTiruan("bm25", {"SEG-A": 3.0, "SEG-B": 2.0}),
        SumberTiruan("vektor", {"SEG-B": 5.0, "SEG-C": 1.0}),
    )


# ------------------------------------------------------------- R-07, C-02


def test_pemanggil_llm_tidak_pernah_menerima_segmen_metadata() -> None:
    """**Uji terpenting fitur 007 bagi kepatuhan.**

    `PEMANGGIL_LLM` menjangkau indeks utama saja (fitur 006). Konteks yang
    dikirim ke LLM disusun jalur ini, dan segmen berlisensi tertutup tinggal di
    indeks metadata.
    """
    leksikal = SumberTiruan("bm25", {"SEG-A": 3.0})
    metadata = SumberTiruan(
        "vektor", {"SEG-M": 9.0}, indeks_tujuan=IndeksTujuan.METADATA
    )
    with pytest.raises(ValueError):
        ambil_hibrida("kepala sekolah", kredensial=PEMANGGIL_LLM, sumber=[leksikal, metadata])
    assert metadata.dipanggil == 0


def test_sumber_yang_tidak_dijangkau_tidak_dijalankan_sama_sekali() -> None:
    """**Lebih kuat daripada "hasilnya kosong".**

    Hasil kosong dapat berarti pencarian yang berjalan lalu disaring, dan
    penyaringan sesudah pencarian adalah bentuk yang C-02 kalimat kedua tolak.
    Yang dinyatakan di sini: sumbernya tidak pernah dipanggil.
    """
    utama_a = SumberTiruan("bm25", {"SEG-A": 3.0})
    utama_b = SumberTiruan("vektor", {"SEG-B": 2.0})
    metadata = SumberTiruan("bacaan", {"SEG-M": 9.0}, indeks_tujuan=IndeksTujuan.METADATA)

    hasil = ambil_hibrida(
        "kepala sekolah", kredensial=PEMANGGIL_LLM, sumber=[utama_a, utama_b, metadata]
    )

    assert metadata.dipanggil == 0
    assert utama_a.dipanggil == 1
    assert utama_b.dipanggil == 1
    assert all(h.id_segmen != "SEG-M" for h in hasil.segmen)


def test_jalur_penjawaban_menjangkau_kedua_indeks() -> None:
    """`docs/D14.md` Bagian 6 menetapkan `bacaan_lanjutan` sebagai tempat
    satu-satunya bagi sumber `indeks_metadata`, dan blok itu disusun jalur
    penjawaban.

    Melarangnya di sini akan menutup pekerjaan yang D-14 tuntut — koreksi R-04
    fitur 006, tercatat pada KB-031.
    """
    utama = SumberTiruan("bm25", {"SEG-A": 3.0})
    metadata = SumberTiruan("bacaan", {"SEG-M": 9.0}, indeks_tujuan=IndeksTujuan.METADATA)
    hasil = ambil_hibrida("kepala sekolah", kredensial=PENJAWABAN, sumber=[utama, metadata])
    assert metadata.dipanggil == 1
    assert {h.id_segmen for h in hasil.segmen} == {"SEG-A", "SEG-M"}


def test_verifikasi_juga_menjangkau_kedua_indeks() -> None:
    utama = SumberTiruan("bm25", {"SEG-A": 3.0})
    metadata = SumberTiruan("bacaan", {"SEG-M": 9.0}, indeks_tujuan=IndeksTujuan.METADATA)
    ambil_hibrida("kepala sekolah", kredensial=VERIFIKASI, sumber=[utama, metadata])
    assert metadata.dipanggil == 1


def test_kredensial_diperiksa_sebelum_kueri_diproses() -> None:
    """Pemeriksaan yang berjalan sesudah pencarian membocorkan keberadaan
    segmen lewat waktu tanggap — bentuk yang sama dengan alasan `dasar.py`
    memeriksa kredensial sebelum menyentuh data.
    """
    metadata_a = SumberTiruan("m1", {"SEG-M": 1.0}, indeks_tujuan=IndeksTujuan.METADATA)
    metadata_b = SumberTiruan("m2", {"SEG-N": 1.0}, indeks_tujuan=IndeksTujuan.METADATA)
    with pytest.raises(ValueError):
        ambil_hibrida("kueri", kredensial=PEMANGGIL_LLM, sumber=[metadata_a, metadata_b])
    assert metadata_a.dipanggil == 0
    assert metadata_b.dipanggil == 0


# ------------------------------------------------------- R-05 lewat penyusun


def test_satu_sumber_terjangkau_ditolak() -> None:
    """R-05 ditegakkan **sesudah** penyaringan kredensial, bukan sebelumnya.

    Tiga sumber yang dua di antaranya tidak terjangkau adalah satu sumber yang
    sesungguhnya, dan hitungan sebelum penyaringan akan meloloskannya.
    """
    utama = SumberTiruan("bm25", {"SEG-A": 3.0})
    metadata = SumberTiruan("bacaan", {"SEG-M": 9.0}, indeks_tujuan=IndeksTujuan.METADATA)
    with pytest.raises(ValueError, match="ADR-03"):
        ambil_hibrida("kueri", kredensial=PEMANGGIL_LLM, sumber=[utama, metadata])


# ---------------------------------------------------------------- pemangkasan


def test_paling_banyak_delapan_segmen_diteruskan() -> None:
    """D-07 Bagian 4.4 dan Bagian 9: 5–8 segmen. "Batas konteks — 5–8 segmen;
    segmen dipangkas bila melampaui batas" (RT-03)."""
    banyak = {f"SEG-{i:02d}": float(30 - i) for i in range(30)}
    lain = {f"SEG-{i:02d}": float(i) for i in range(30)}
    hasil = ambil_hibrida(
        "kepala sekolah",
        kredensial=PEMANGGIL_LLM,
        sumber=[SumberTiruan("bm25", banyak), SumberTiruan("vektor", lain)],
    )
    assert len(hasil.segmen) == JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM


def test_setiap_sumber_diminta_dua_puluh_kandidat() -> None:
    """D-07 Bagian 4.4: "Kandidat BM25 — 20 teratas", "Kandidat vektor — 20
    teratas". Batasnya diterapkan **per sumber**, sebelum penggabungan."""
    banyak = {f"SEG-{i:02d}": float(30 - i) for i in range(30)}
    sumber = SumberTiruan("bm25", banyak)
    hasil = ambil_hibrida(
        "kueri",
        kredensial=PEMANGGIL_LLM,
        sumber=[sumber, SumberTiruan("vektor", {})],
    )
    asal = hasil.asal_dari("bm25")
    assert asal is not None
    assert asal.jumlah_kandidat == JUMLAH_KANDIDAT_PER_SUMBER


def test_kandidat_lebih_sedikit_diteruskan_seluruhnya() -> None:
    """Bukan diisi sampai penuh. Mengisi dengan segmen berskor rendah memberi
    penyusun jawaban bahan tidak relevan, dan penilaian kecukupan kemudian
    menghitung bahan itu sebagai bukti."""
    hasil = ambil_hibrida("kueri", kredensial=PEMANGGIL_LLM, sumber=list(_pasangan()))
    assert len(hasil.segmen) == 3


# ----------------------------------------------------------- R-13, R-14


def test_versi_setiap_indeks_ikut_pada_hasil() -> None:
    """**R-13.** Dua sumber, dua indeks, dua versi — seluruhnya tercatat.

    Satu bidang `versi_indeks` tunggal akan memaksa memilih salah satunya, dan
    percobaan yang tercatat pada D-10 L1 kemudian menyebut versi indeks yang
    separuh keliru.
    """
    hasil = ambil_hibrida(
        "kueri",
        kredensial=PEMANGGIL_LLM,
        sumber=[
            SumberTiruan("bm25", {"SEG-A": 1.0}, versi_indeks="leksikal-7"),
            SumberTiruan("vektor", {"SEG-B": 1.0}, versi_indeks="vektor-3"),
        ],
    )
    assert [(a.nama_sumber, a.versi_indeks) for a in hasil.asal] == [
        ("bm25", "leksikal-7"),
        ("vektor", "vektor-3"),
    ]


def test_pengambilan_tidak_menulis_apa_pun() -> None:
    """**R-14, C-17.** Jalur penjawaban tanpa akses tulis.

    Diperiksa pada tingkat AST, bukan dengan menjalankan lalu memeriksa
    berkas: pemanggilan tulis yang tidak dilewati satu kali uji tetap ada pada
    kodenya. Pemeriksa C-17 menyapu seluruh jalur penjawaban; uji ini
    menyatakannya untuk modul ini sendiri agar kegagalannya terbaca di sini.
    """
    import ast
    import inspect

    import src.rag.pengambilan.hibrida as modul

    pohon = ast.parse(inspect.getsource(modul))
    terlarang = {"write_text", "write_bytes", "open", "mkdir", "unlink"}
    dipanggil = {
        simpul.func.attr
        for simpul in ast.walk(pohon)
        if isinstance(simpul, ast.Call) and isinstance(simpul.func, ast.Attribute)
    }
    assert not (dipanggil & terlarang)


def test_hasil_beku() -> None:
    hasil = ambil_hibrida("kueri", kredensial=PEMANGGIL_LLM, sumber=list(_pasangan()))
    with pytest.raises(ValidationError):
        hasil.segmen = ()  # type: ignore[misc]


def test_asal_berupa_tuple_bukan_pemetaan() -> None:
    """`kredensial.py` menyatakannya bagi seluruh proyek: "Objek beku yang
    memuat himpunan yang dapat ditambah anggotanya tidak beku dalam arti yang
    berguna."

    Pemetaan pada model beku tetap dapat disunting isinya, dan hasil
    pengambilan yang asal-usulnya dapat disunting adalah hasil yang catatan
    percobaannya tidak membuktikan apa pun.
    """
    hasil = ambil_hibrida("kueri", kredensial=PEMANGGIL_LLM, sumber=list(_pasangan()))
    assert isinstance(hasil.asal, tuple)
    assert hasil.asal_dari("tidak-ada") is None


def test_kueri_kosong_ditolak_sebelum_sumber_dijalankan() -> None:
    sumber = list(_pasangan())
    with pytest.raises(ValueError, match="kueri"):
        ambil_hibrida("   ", kredensial=PEMANGGIL_LLM, sumber=sumber)
    assert all(s.dipanggil == 0 for s in sumber)
