"""Uji skema ontologi — A-1 dan A-2 fitur 005, R-01 s.d. R-06.

D-06 Bagian 11.2 menyatakan alasan seluruh fitur ini dalam satu kalimat:
*"Tanpa aturan ini, target 500 dapat dipenuhi dengan konsep yang tidak
berguna, dan angka MK-06 menjadi angka tanpa isi."*

Godaannya nyata dan tidak menuntut niat buruk: MK-06 adalah syarat Definisi
Selesai dengan tenggat bulan 8, dan menambah baris tabel jauh lebih cepat
daripada menyusun definisi.
"""

import pytest
from pydantic import ValidationError
from src.rag.ontologi.skema import JenisRelasi, Konsep, Ontologi, Relasi

DOK = frozenset({"DOC-001"})


def _konsep(id_konsep: str = "K1", **ganti: object) -> Konsep:
    argumen: dict[str, object] = {
        "id_konsep": id_konsep,
        "label": "Rencana Kegiatan dan Anggaran Sekolah",
        "definisi": "Dokumen perencanaan tahunan yang memuat program dan anggaran sekolah.",
        "id_dokumen_rujukan": DOK,
        "sumber_terkurasi": True,
    }
    argumen.update(ganti)
    return Konsep(**argumen)  # type: ignore[arg-type]


def _relasi(**ganti: object) -> Relasi:
    argumen: dict[str, object] = {
        "id_relasi": "R1",
        "konsep_asal": "K1",
        "konsep_tujuan": "K2",
        "jenis": JenisRelasi.MENGATUR,
        "id_dokumen_rujukan": DOK,
    }
    argumen.update(ganti)
    return Relasi(**argumen)  # type: ignore[arg-type]


# ------------------------------------------------------------- A-1, R-01


def test_tujuh_jenis_relasi_persis_fr_e02() -> None:
    """FR-E02 menyebut tujuh dengan namanya. Jenis kedelapan menuntut D-01
    diubah lebih dulu — AG-04 melarang agen mengubah daftar nilai enum."""
    assert {j.value for j in JenisRelasi} == {
        "mengatur",
        "bagian_dari",
        "prasyarat",
        "berdampak_pada",
        "diukur_oleh",
        "bertanggung_jawab_atas",
        "bertentangan_dengan",
    }


def test_jenis_di_luar_tujuh_ditolak() -> None:
    with pytest.raises(ValidationError):
        _relasi(jenis="meregulasi")


# ------------------------------------------------------------- A-1, R-02


def test_konsep_tanpa_dokumen_sumber_tidak_dapat_dibentuk() -> None:
    """**FR-E03.** Konsep tanpa sumber adalah konsep yang tidak dapat
    diperiksa siapa pun — dan D-06 Bagian 11.2 tidak menghitungnya."""
    with pytest.raises(ValidationError):
        _konsep(id_dokumen_rujukan=frozenset())


def test_konsep_tanpa_label_tidak_dapat_dibentuk() -> None:
    with pytest.raises(ValidationError):
        _konsep(label="")


def test_konsep_tanpa_definisi_tetap_dapat_dibentuk() -> None:
    """**Pembedaan yang menentukan, dan ia mudah dibalik.**

    Konsep yang masih disusun definisinya adalah keadaan kerja yang wajar;
    menolaknya membuat pekerjaan penyusunan mustahil. Yang tidak boleh adalah
    ia ikut terhitung pada angka MK-06 — dan itu urusan `hitung.py`.
    """
    konsep = _konsep(definisi="")
    assert not konsep.berdefinisi


def test_definisi_berisi_spasi_saja_bukan_definisi() -> None:
    """Bentuk pengelakan yang paling murah: satu spasi memenuhi "tidak
    kosong" dan tidak menerangkan apa pun."""
    assert not _konsep(definisi="   \n  ").berdefinisi


def test_sumber_terkurasi_wajib_tanpa_nilai_bawaan() -> None:
    """**R-06, dan ini C-03 yang merambat.**

    Nilai bawaan apa pun akan menjadi jawaban bagi konsep yang asalnya
    sebenarnya tidak diketahui — dan ontologi diekspor untuk HKI dan
    publikasi.
    """
    assert Konsep.model_fields["sumber_terkurasi"].is_required()


def test_konsep_beku() -> None:
    with pytest.raises(ValidationError):
        _konsep().definisi = "lain"  # type: ignore[misc]


# ------------------------------------------------------------- A-1, R-04


def test_relasi_tanpa_dokumen_rujukan_sendiri_tidak_dapat_dibentuk() -> None:
    """**R-04, dan menghemat bidang ini terasa rapi.**

    Relasi "bertentangan dengan" antara dua konsep yang masing-masing
    bersumber dokumen berbeda tidak punya dokumen yang menyatakan
    **pertentangannya**. Klaim relasi menjadi klaim tanpa sumber — persis yang
    C-01 larang pada jawaban, dan ontologi ini diekspor untuk publikasi.
    """
    with pytest.raises(ValidationError):
        _relasi(id_dokumen_rujukan=frozenset())


def test_relasi_ke_dirinya_sendiri_ditolak() -> None:
    """Tidak menerangkan apa pun, dan pada penelusuran graf menjadi putaran
    tak berujung."""
    with pytest.raises(ValidationError):
        _relasi(konsep_tujuan="K1")


# ------------------------------------------------------------- A-2, R-05


def test_ontologi_terbentuk() -> None:
    onto = Ontologi(konsep=(_konsep("K1"), _konsep("K2")), relasi=(_relasi(),))
    assert len(onto.konsep) == 2
    assert len(onto.relasi) == 1


def test_relasi_ke_konsep_yang_tidak_ada_ditolak() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-05.**

    Diperiksa saat ontologi dibentuk, bukan saat ditelusuri. Relasi
    menggantung yang baru ketahuan saat penelusuran menghasilkan graf yang
    sebagian jalurnya buntu — dan buntu itu terbaca sebagai "tidak ada
    hubungan", bukan sebagai cacat data.
    """
    with pytest.raises(ValidationError) as galat:
        Ontologi(konsep=(_konsep("K1"),), relasi=(_relasi(),))
    assert "K2" in str(galat.value)


def test_konsep_asal_yang_tidak_ada_juga_ditolak() -> None:
    """Kedua ujung diperiksa. Memeriksa satu ujung saja meloloskan separuh
    relasi menggantung, dan separuh yang lolos adalah yang arahnya kebetulan
    tidak diuji."""
    with pytest.raises(ValidationError):
        Ontologi(konsep=(_konsep("K2"),), relasi=(_relasi(),))


def test_konsep_berulang_ditolak() -> None:
    """Pengulangan menggandakan hitungan MK-06 tanpa menambah satu konsep pun
    — bentuk pengelakan yang tidak menuntut niat buruk, hanya impor yang
    dijalankan dua kali."""
    with pytest.raises(ValidationError) as galat:
        Ontologi(konsep=(_konsep("K1"), _konsep("K1")), relasi=())
    assert "K1" in str(galat.value)


def test_ontologi_kosong_dapat_dibentuk() -> None:
    """Ontologi kosong adalah keadaan awal yang sah; yang ditolak adalah
    **mengekspornya** (B-2). Menolaknya di sini akan membuat pembangunan
    bertahap mustahil."""
    assert Ontologi(konsep=(), relasi=()).konsep == ()
