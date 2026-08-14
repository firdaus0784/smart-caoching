"""Uji kontrak keluaran dan hasil pemeriksaan — A-2 dan A-3 fitur 008.

Dua hal diuji di sini, dan yang kedua adalah inti fitur ini.

**VS-01 ditegakkan tipe** (A-2). Klaim tanpa `id_segmen` tidak dapat dibentuk.
Bentuk yang sama dengan `penanda_bagian` fitur 007: yang dapat ditegakkan tipe
tidak diserahkan kepada pemeriksaan saat jalan.

**Tiga keadaan, bukan dua** (A-3). Tiga dari sembilan pemeriksaan D-07 Bagian
6.1 tidak dapat dibangun hari ini. Validator yang mengembalikan `True` atas
kesembilannya tidak dapat dibedakan dari validator yang benar — dan ia tinggal
di komponen yang D-04 ADR-04 sebut terpenting dalam sistem.
"""

import pytest
from pydantic import ValidationError
from src.kamus.segmen import IndeksTujuan, Peringkat, StatusKeberlakuan
from src.rag.validator.keluaran import KeluaranModel, Klaim, SegmenRujukan
from src.rag.validator.pemeriksaan import (
    HasilPemeriksaan,
    KodePemeriksaan,
    Status,
)

# ------------------------------------------------------------------ A-2, R-01


def test_klaim_tanpa_id_segmen_tidak_dapat_dibentuk() -> None:
    """**VS-01 sebagai bentuk.**

    D-07 Bagian 5.1: struktur `klaim` inilah yang memungkinkan validasi.
    Klaim tanpa rujukan adalah klaim tanpa dasar, dan membiarkannya terbentuk
    berarti mengandalkan setiap pemanggil memeriksanya.
    """
    with pytest.raises(ValidationError):
        Klaim(id_klaim="K1", teks="Kepala sekolah menyusun RKAS.", id_segmen=())


def test_klaim_dengan_satu_segmen_diterima() -> None:
    klaim = Klaim(id_klaim="K1", teks="Kepala sekolah menyusun RKAS.", id_segmen=("SEG-A",))
    assert klaim.id_segmen == ("SEG-A",)


def test_klaim_beku_dan_daftar_segmennya_tidak_dapat_ditambah() -> None:
    """`tuple`, bukan `list`. `kredensial.py` menyatakannya bagi seluruh
    proyek: objek beku yang memuat himpunan yang dapat ditambah anggotanya
    tidak beku dalam arti yang berguna."""
    klaim = Klaim(id_klaim="K1", teks="isi", id_segmen=("SEG-A",))
    assert isinstance(klaim.id_segmen, tuple)
    with pytest.raises(ValidationError):
        klaim.teks = "lain"  # type: ignore[misc]


def test_klaim_tidak_membawa_peringkat_kepercayaan() -> None:
    """**Bidang yang sengaja tidak ada.**

    `docs/D14.md` Bagian 4.1 menyatakan arti `klaim[].peringkat_kepercayaan`
    pada klaim campuran adalah **keputusan BT-64, bukan keputusan pelaksana**,
    dan ketiga pilihan yang mungkin mengubah apa yang dilihat kepala sekolah
    pada klaim yang sama.

    Memodelkannya sekarang berarti memilih salah satunya diam-diam. VS-08
    dirumuskan agar tidak membutuhkannya.
    """
    assert "peringkat_kepercayaan" not in Klaim.model_fields


def test_keluaran_kosong_sah() -> None:
    """D-14 Bagian 4.1: keadaan `tidak_ditemukan` dan `di_luar_domain` memakai
    bentuk yang sama dengan ringkasan dan klaim kosong.

    "Bentuk yang seragam inilah yang membuat layar D-05 dapat menampilkannya
    sebagai jawaban sah, bukan pesan galat."
    """
    keluaran = KeluaranModel()
    assert keluaran.klaim == ()
    assert keluaran.ringkasan_tindakan == ()


def test_keluaran_menolak_bidang_tambahan() -> None:
    """AG-03 melarang agen menambah bidang pada tanggapan `/tanya`.

    `extra="forbid"` membuat bidang yang diselundupkan keluaran model tertolak
    saat diurai, bukan diteruskan diam-diam ke penyusun tanggapan.
    """
    with pytest.raises(ValidationError):
        KeluaranModel(skor_keyakinan=0.9)  # type: ignore[call-arg]


def test_segmen_rujukan_membawa_keempat_sifat_yang_diperiksa() -> None:
    """Peringkat (VS-08), indeks asal (VS-04), status keberlakuan (VS-06), dan
    tautan (VS-09). Segmen yang kehilangan salah satunya membuat pemeriksaannya
    tidak dapat dijalankan sama sekali."""
    for bidang in ("peringkat_kepercayaan", "indeks_asal", "status_keberlakuan", "tautan"):
        assert bidang in SegmenRujukan.model_fields


def test_segmen_rujukan_menuntut_ketiga_enum_diisi() -> None:
    """Tanpa nilai bawaan. Bidang berbawaan `BERLAKU` akan membuat segmen yang
    statusnya belum diketahui lolos VS-06 sebagai segmen yang berlaku."""
    for bidang in ("peringkat_kepercayaan", "indeks_asal", "status_keberlakuan"):
        assert SegmenRujukan.model_fields[bidang].is_required()


def test_segmen_rujukan_dapat_dibentuk() -> None:
    segmen = SegmenRujukan(
        id_segmen="SEG-A",
        peringkat_kepercayaan=Peringkat.T1,
        indeks_asal=IndeksTujuan.UTAMA,
        status_keberlakuan=StatusKeberlakuan.BERLAKU,
    )
    assert segmen.tautan is None


# ------------------------------------------------------------ A-3, R-08, R-10


def test_status_bertiga_nilai_bukan_dua() -> None:
    """**Inti fitur ini.**

    Tiga dari sembilan pemeriksaan tidak dapat dibangun hari ini. `bool` akan
    memaksa ketiganya menjadi `True` atau `False`, dan keduanya berbohong:
    `True` melaporkan lulus atas yang tidak diperiksa, `False` melaporkan gagal
    atas yang tidak salah.
    """
    assert {s.value for s in Status} == {"lulus", "gagal", "belum_dapat_diperiksa"}


def test_kesembilan_kode_persis_d07_bagian_6_1() -> None:
    """Termasuk ketiga yang belum dapat dijalankan.

    Enum yang hanya memuat enam akan membuat "seluruhnya lulus" berarti
    "keenam yang kami pilih lulus", dan tidak ada yang dapat membaca ketiadaan
    ketiganya dari kode.
    """
    assert {k.value for k in KodePemeriksaan} == {
        "VS-01",
        "VS-02",
        "VS-03",
        "VS-04",
        "VS-05",
        "VS-06",
        "VS-07",
        "VS-08",
        "VS-09",
    }


def test_hasil_membawa_kodenya() -> None:
    """**R-08.** D-07 Bagian 6.2: setiap kegagalan memicu
    `answer_rejected_validator` **beserta kode pemeriksaan yang gagal**, dan
    itu yang membuat RT-02 terukur.

    Kegagalan tanpa kodenya hanya menghasilkan angka penolakan tanpa sebab —
    dan angka penolakan tanpa sebab akan dijawab dengan melonggarkan validator,
    yang persis dilarang D-07 Bagian 6.2.
    """
    hasil = HasilPemeriksaan(
        kode=KodePemeriksaan.VS_02,
        status=Status.GAGAL,
        alasan="id_segmen tidak ada di antara segmen terambil",
        id_klaim_bermasalah=("K1",),
    )
    assert hasil.kode is KodePemeriksaan.VS_02
    assert hasil.id_klaim_bermasalah == ("K1",)


def test_alasan_wajib_termasuk_pada_lulus() -> None:
    """Alasan yang hanya wajib saat gagal membuat `BELUM_DAPAT_DIPERIKSA`
    tidak terbaca sebabnya — dan sebab itulah yang menentukan fitur mana yang
    membukanya."""
    with pytest.raises(ValidationError):
        HasilPemeriksaan(kode=KodePemeriksaan.VS_01, status=Status.LULUS, alasan="")


def test_lulus_tidak_boleh_menunjuk_klaim_bermasalah() -> None:
    """Bila ia menunjuk, salah satu dari dua hal keliru: klaimnya sebenarnya
    bermasalah dan statusnya salah, atau daftarnya sisa dari pemanggilan
    sebelumnya. Keduanya menyesatkan."""
    with pytest.raises(ValidationError):
        HasilPemeriksaan(
            kode=KodePemeriksaan.VS_01,
            status=Status.LULUS,
            alasan="seluruh klaim membawa id_segmen",
            id_klaim_bermasalah=("K1",),
        )


@pytest.mark.parametrize(
    ("status", "menghalangi"),
    [
        (Status.LULUS, False),
        (Status.GAGAL, True),
        (Status.BELUM_DAPAT_DIPERIKSA, True),
    ],
)
def test_belum_dapat_diperiksa_menghalangi_sama_seperti_gagal(
    status: Status, menghalangi: bool
) -> None:
    """**Uji terpenting A-3.**

    Yang membedakan gagal dari belum-dapat-diperiksa bukan akibatnya melainkan
    tindak lanjutnya: yang gagal menuntut jawabannya diperbaiki, yang belum
    dapat diperiksa menuntut fiturnya dibangun. Pada pertanyaan "boleh
    ditayangkan?" keduanya menjawab tidak.
    """
    hasil = HasilPemeriksaan(kode=KodePemeriksaan.VS_03, status=status, alasan="alasan")
    assert hasil.menghalangi is menghalangi


def test_hasil_pemeriksaan_beku() -> None:
    hasil = HasilPemeriksaan(kode=KodePemeriksaan.VS_01, status=Status.LULUS, alasan="lulus")
    with pytest.raises(ValidationError):
        hasil.status = Status.GAGAL  # type: ignore[misc]
