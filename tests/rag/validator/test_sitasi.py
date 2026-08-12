"""Uji pemeriksaan sitasi — B-1 s.d. B-3 fitur 008, R-01 s.d. R-05.

Lima pemeriksaan, dan **dua di antaranya berakibat berbeda dari yang lain**.

D-07 Bagian 6.2 membedakan VS-01/02/03 dari VS-04/06, dan pembedaannya bukan
gradasi keparahan. VS-01 s.d. VS-03 gagal ketika model menyusun klaim yang
tidak tertopang — kekeliruan **penyusunan**, dan klaimnya dibuang. VS-04 dan
VS-06 gagal ketika segmen yang tidak boleh terjangkau ternyata terjangkau —
**gerbang yang bocor**, dan seluruh jawaban dibuang serta dicatat sebagai
insiden kepatuhan.

Membuang klaimnya saja pada kasus kedua akan menghasilkan jawaban yang tampak
sehat di atas gerbang yang rusak.

**Uji VS-08 yang paling mudah keliru** ada di bagian terakhir. "T3 saja
ditolak" dipenuhi juga oleh validator yang menolak setiap klaim yang menyentuh
T3 — dan validator semacam itu membuang jawaban yang sah, lalu dilonggarkan
orang. D-13 Bagian 6 mewajibkan klaim campuran.
"""

import pytest
from src.kamus.segmen import IndeksTujuan, Peringkat, StatusKeberlakuan
from src.rag.validator.keluaran import Klaim, KeluaranModel, SegmenRujukan
from src.rag.validator.pemeriksaan import KodePemeriksaan, Status
from src.rag.validator.sitasi import (
    periksa_dasar_klaim,
    periksa_indeks_metadata,
    periksa_keberlakuan,
    periksa_peringkat_klaim,
    periksa_rujukan_nyata,
)


def _segmen(
    id_segmen: str,
    *,
    peringkat: Peringkat = Peringkat.T1,
    indeks: IndeksTujuan = IndeksTujuan.UTAMA,
    keberlakuan: StatusKeberlakuan = StatusKeberlakuan.BERLAKU,
    tautan: str | None = None,
) -> SegmenRujukan:
    return SegmenRujukan(
        id_segmen=id_segmen,
        peringkat_kepercayaan=peringkat,
        indeks_asal=indeks,
        status_keberlakuan=keberlakuan,
        tautan=tautan,
    )


def _klaim(id_klaim: str, *id_segmen: str) -> Klaim:
    return Klaim(id_klaim=id_klaim, teks=f"Klaim {id_klaim}.", id_segmen=id_segmen)


def _keluaran(*klaim: Klaim) -> KeluaranModel:
    return KeluaranModel(ringkasan_tindakan=("Susun RKAS.",), klaim=klaim)


# ------------------------------------------------------------- B-1, VS-01, R-01


def test_vs01_lulus_ketika_setiap_klaim_membawa_rujukan() -> None:
    hasil = periksa_dasar_klaim(_keluaran(_klaim("K1", "SEG-A")))
    assert hasil.status is Status.LULUS
    assert hasil.kode is KodePemeriksaan.VS_01


def test_vs01_lulus_pada_keluaran_tanpa_klaim() -> None:
    """Jawaban tanpa klaim adalah bentuk sah `tidak_ditemukan` (D-14 Bagian
    4.1). VS-01 tidak boleh menggagalkannya — penolakan yang sah bukan
    kegagalan validator."""
    assert periksa_dasar_klaim(KeluaranModel()).status is Status.LULUS


# ------------------------------------------------------------- B-1, VS-02, R-02


def test_vs02_menolak_rujukan_yang_mengada_ada() -> None:
    """D-07 Bagian 6.1: kegagalan VS-02 berarti "rujukan mengada-ada"."""
    hasil = periksa_rujukan_nyata(
        _keluaran(_klaim("K1", "SEG-TIDAK-ADA")), segmen=(_segmen("SEG-A"),)
    )
    assert hasil.status is Status.GAGAL
    assert hasil.id_klaim_bermasalah == ("K1",)


def test_vs02_diperiksa_terhadap_segmen_terambil_bukan_terhadap_klaimnya() -> None:
    """**Uji terpenting B-1**, dan yang paling mudah keliru.

    Versi yang memeriksa apakah id pada sebuah klaim juga muncul pada klaim
    lain akan lulus pada seluruh uji lain di berkas ini — dan meloloskan model
    yang mengarang id lalu memakainya dua kali. Yang dituntut D-07 adalah
    "benar-benar ada di antara **segmen yang diambil**".
    """
    keluaran = _keluaran(_klaim("K1", "SEG-KARANGAN"), _klaim("K2", "SEG-KARANGAN"))
    hasil = periksa_rujukan_nyata(keluaran, segmen=(_segmen("SEG-A"),))
    assert hasil.status is Status.GAGAL
    assert set(hasil.id_klaim_bermasalah) == {"K1", "K2"}


def test_vs02_lulus_ketika_seluruh_rujukan_ada() -> None:
    hasil = periksa_rujukan_nyata(
        _keluaran(_klaim("K1", "SEG-A", "SEG-B")),
        segmen=(_segmen("SEG-A"), _segmen("SEG-B")),
    )
    assert hasil.status is Status.LULUS


def test_vs02_menandai_klaim_yang_sebagian_rujukannya_karangan() -> None:
    """Satu rujukan karangan sudah cukup. Klaim yang separuh benar tetap klaim
    yang menyebut sumber yang tidak ada."""
    hasil = periksa_rujukan_nyata(
        _keluaran(_klaim("K1", "SEG-A", "SEG-KARANGAN")), segmen=(_segmen("SEG-A"),)
    )
    assert hasil.status is Status.GAGAL


# ------------------------------------------------------- B-2, VS-04, R-03


def test_vs04_menolak_segmen_metadata_sebagai_dasar_klaim() -> None:
    """D-07 Bagian 3.1: segmen `indeks_metadata` hanya boleh muncul sebagai
    rujukan bacaan lanjutan, **tidak pernah** sebagai bahan penyusunan.

    Kegagalannya berarti pelanggaran KL-01 dan C-02.
    """
    hasil = periksa_indeks_metadata(
        _keluaran(_klaim("K1", "SEG-M")),
        segmen=(_segmen("SEG-M", indeks=IndeksTujuan.METADATA),),
    )
    assert hasil.status is Status.GAGAL


def test_vs04_tidak_menunjuk_klaim_tertentu() -> None:
    """**Uji terpenting B-2.**

    D-07 Bagian 6.2 menetapkan VS-04 membuang **seluruh** jawaban tanpa
    perbaikan. Menunjuk klaim tertentu akan menyesatkan ke arah perbaikan
    sebagian — dan perbaikan sebagian menghasilkan jawaban yang tampak sehat di
    atas gerbang yang bocor.
    """
    hasil = periksa_indeks_metadata(
        _keluaran(_klaim("K1", "SEG-M"), _klaim("K2", "SEG-A")),
        segmen=(_segmen("SEG-M", indeks=IndeksTujuan.METADATA), _segmen("SEG-A")),
    )
    assert hasil.status is Status.GAGAL
    assert hasil.id_klaim_bermasalah == ()


def test_vs04_lulus_ketika_seluruh_dasar_dari_indeks_utama() -> None:
    hasil = periksa_indeks_metadata(
        _keluaran(_klaim("K1", "SEG-A")), segmen=(_segmen("SEG-A"),)
    )
    assert hasil.status is Status.LULUS


def test_vs04_mengabaikan_segmen_metadata_yang_tidak_menjadi_dasar_klaim() -> None:
    """Segmen metadata **boleh** ada di antara segmen terambil — ia bahan
    `bacaan_lanjutan` (D-14 Bagian 6). Yang dilarang adalah ia menjadi dasar
    klaim.

    Validator yang menolak keberadaannya akan menutup pekerjaan yang D-14
    tuntut, lalu dimatikan orang.
    """
    hasil = periksa_indeks_metadata(
        _keluaran(_klaim("K1", "SEG-A")),
        segmen=(_segmen("SEG-A"), _segmen("SEG-M", indeks=IndeksTujuan.METADATA)),
    )
    assert hasil.status is Status.LULUS


# ------------------------------------------------------- B-2, VS-06, R-04


def test_vs06_menolak_segmen_dari_regulasi_dicabut() -> None:
    """D-07 Bagian 4.5: "Menjawab berdasarkan aturan yang sudah dicabut adalah
    bentuk kekeliruan yang paling merugikan, **karena jawabannya terdengar
    berdasar**." (C-07, KL-07)
    """
    hasil = periksa_keberlakuan(
        _keluaran(_klaim("K1", "SEG-C")),
        segmen=(_segmen("SEG-C", keberlakuan=StatusKeberlakuan.DICABUT),),
    )
    assert hasil.status is Status.GAGAL
    assert hasil.id_klaim_bermasalah == ()


def test_vs06_menerima_segmen_berstatus_diubah() -> None:
    """**Diubah bukan dicabut.** D-07 Bagian 4.5: segmen berstatus `diubah`
    "dipakai, tetapi jawaban wajib menampilkan penanda dan rujukan
    pengubahnya".

    Validator yang menolak keduanya akan membuang jawaban yang sah — dan
    penanda keberlakuan FR-F14 justru dibangun untuk keadaan ini.
    """
    hasil = periksa_keberlakuan(
        _keluaran(_klaim("K1", "SEG-D")),
        segmen=(_segmen("SEG-D", keberlakuan=StatusKeberlakuan.DIUBAH),),
    )
    assert hasil.status is Status.LULUS


def test_vs06_mengabaikan_segmen_dicabut_yang_tidak_menjadi_dasar_klaim() -> None:
    hasil = periksa_keberlakuan(
        _keluaran(_klaim("K1", "SEG-A")),
        segmen=(_segmen("SEG-A"), _segmen("SEG-C", keberlakuan=StatusKeberlakuan.DICABUT)),
    )
    assert hasil.status is Status.LULUS


# ------------------------------------------------------- B-3, VS-08, R-05, C-19


def test_vs08_menerima_klaim_yang_ditopang_t1_dan_t3_sekaligus() -> None:
    """**Uji terpenting fitur ini bagi C-19.**

    D-13 Bagian 6 menyatakan T3 *"boleh menopang, tetapi klaim memerlukan
    segmen T1 atau T2"*. Klaim campuran karena itu adalah bentuk yang **benar**,
    bukan pengecualian — dan D-14 Bagian 4.1 menyebutnya "bukan keadaan
    langka".

    Uji "T3 saja ditolak" dipenuhi juga oleh validator yang menolak setiap
    klaim yang menyentuh T3. Validator semacam itu membuang jawaban yang sah,
    lalu dilonggarkan orang — dan yang longgar bersamanya adalah VS-08.
    """
    hasil = periksa_peringkat_klaim(
        _keluaran(_klaim("K1", "SEG-A", "SEG-C")),
        segmen=(
            _segmen("SEG-A", peringkat=Peringkat.T1),
            _segmen("SEG-C", peringkat=Peringkat.T3),
        ),
    )
    assert hasil.status is Status.LULUS


def test_vs08_menolak_klaim_yang_seluruh_penopangnya_lemah() -> None:
    hasil = periksa_peringkat_klaim(
        _keluaran(_klaim("K1", "SEG-C", "SEG-D")),
        segmen=(
            _segmen("SEG-C", peringkat=Peringkat.T3),
            _segmen("SEG-D", peringkat=Peringkat.T4),
        ),
    )
    assert hasil.status is Status.GAGAL
    assert hasil.id_klaim_bermasalah == ("K1",)


@pytest.mark.parametrize("peringkat", [Peringkat.T3, Peringkat.T4])
def test_vs08_menolak_klaim_bersandar_tunggal_pada_peringkat_lemah(
    peringkat: Peringkat,
) -> None:
    hasil = periksa_peringkat_klaim(
        _keluaran(_klaim("K1", "SEG-X")), segmen=(_segmen("SEG-X", peringkat=peringkat),)
    )
    assert hasil.status is Status.GAGAL


@pytest.mark.parametrize("peringkat", [Peringkat.T1, Peringkat.T2])
def test_vs08_menerima_klaim_bersandar_tunggal_pada_peringkat_kuat(
    peringkat: Peringkat,
) -> None:
    hasil = periksa_peringkat_klaim(
        _keluaran(_klaim("K1", "SEG-X")), segmen=(_segmen("SEG-X", peringkat=peringkat),)
    )
    assert hasil.status is Status.LULUS


def test_vs08_menandai_hanya_klaim_yang_melanggar() -> None:
    """Berbeda dari VS-04 dan VS-06: VS-08 **menurunkan klaimnya**, bukan
    membuang jawabannya (D-07 Bagian 6.2). Klaim lain yang sehat tetap berdiri.
    """
    hasil = periksa_peringkat_klaim(
        _keluaran(_klaim("K1", "SEG-A"), _klaim("K2", "SEG-C")),
        segmen=(
            _segmen("SEG-A", peringkat=Peringkat.T1),
            _segmen("SEG-C", peringkat=Peringkat.T3),
        ),
    )
    assert hasil.id_klaim_bermasalah == ("K2",)


def test_vs08_tidak_membaca_bidang_peringkat_pada_klaim() -> None:
    """**VS-08 tidak menyentuh keputusan BT-64.**

    D-14 Bagian 4.1 menyatakan arti `klaim[].peringkat_kepercayaan` pada klaim
    campuran adalah keputusan BT-64, bukan keputusan pelaksana. VS-08 di sini
    dirumuskan atas **seluruh segmen penopang** — pernyataan yang benar pada
    ketiga pilihan BT-64.

    Diperiksa pada tingkat AST: pemeriksaan yang membaca bidang itu akan
    menetapkan artinya diam-diam.
    """
    import ast
    import inspect

    import src.rag.validator.sitasi as modul

    pohon = ast.parse(inspect.getsource(modul.periksa_peringkat_klaim))
    dibaca_dari_klaim = {
        simpul.attr
        for simpul in ast.walk(pohon)
        if isinstance(simpul, ast.Attribute)
        and isinstance(simpul.value, ast.Name)
        and simpul.value.id == "klaim"
    }
    assert dibaca_dari_klaim <= {"id_klaim", "id_segmen"}, (
        "VS-08 membaca bidang selain id dari klaim: " + ", ".join(sorted(dibaca_dari_klaim))
    )


def test_vs08_rujukan_yang_tidak_ada_tidak_dianggap_penopang_kuat() -> None:
    """Klaim yang menyebut id yang tidak ada di antara segmen terambil sudah
    gagal VS-02. VS-08 tidak boleh **menyelamatkannya** dengan menganggap
    rujukan tak dikenal sebagai penopang kuat.

    Bila ia menganggapnya kuat, model yang mengarang satu id dapat meloloskan
    klaim yang seluruh penopang nyatanya T3.
    """
    hasil = periksa_peringkat_klaim(
        _keluaran(_klaim("K1", "SEG-C", "SEG-KARANGAN")),
        segmen=(_segmen("SEG-C", peringkat=Peringkat.T3),),
    )
    assert hasil.status is Status.GAGAL
