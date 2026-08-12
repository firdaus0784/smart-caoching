"""Uji metadata asal dokumen — R-06, FR-B06, ET-04, D-04 Bagian 7.2.

FR-B06 menyebut lima bidang: jenis, tahun, unit penerbit, tingkat kerahasiaan,
dan status persetujuan pemilik. Dua yang terakhir tidak pernah ada pada model
data sampai KB-013; nilainya ditetapkan pemegang gerbang sebagai penetapan tim
tanpa dasar literatur (SI-01).

Aturan etik yang ditegakkan berkas ini, ditetapkan pemegang gerbang:
**dokumen rahasia hanya boleh masuk korpus atas persetujuan pemiliknya.**
Itu yang memberi `tingkat_kerahasiaan` gigi — tanpanya ia hanya catatan yang
terbaca seperti perlindungan.

Dokumen sekolah menuntut persetujuan **pada tingkat kerahasiaan mana pun**,
termasuk `publik`. ET-04 berbunyi "persetujuan sekolah atas penggunaan dokumen
manajerial untuk korpus" tanpa syarat tingkat, dan tanpa aturan itu sebuah
dokumen sekolah dapat ditandai `publik` untuk melewati gerbang persetujuan.
"""

import pytest
from pydantic import ValidationError
from src.ingest.dokumen import Dokumen, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.peringkat import JenisSumber
from src.kamus.segmen import Peringkat


def _dokumen(**ubah: object) -> Dokumen:
    bidang: dict[str, object] = {
        "id": "dok_001",
        "judul": "Notulen rapat pleno",
        "jenis": JenisSumber.DOKUMEN_SEKOLAH,
        "penerbit": "SDN Sukamaju",
        "tahun": 2026,
        "tingkat_kerahasiaan": TingkatKerahasiaan.INTERNAL_SEKOLAH,
        "status_persetujuan_pemilik": StatusPersetujuan.DIBERIKAN,
    }
    bidang.update(ubah)
    return Dokumen(**bidang)  # type: ignore[arg-type]


def test_kelima_bidang_fr_b06_ada() -> None:
    dokumen = _dokumen()
    assert dokumen.jenis is JenisSumber.DOKUMEN_SEKOLAH
    assert dokumen.tahun == 2026
    assert dokumen.penerbit == "SDN Sukamaju"
    assert dokumen.tingkat_kerahasiaan is TingkatKerahasiaan.INTERNAL_SEKOLAH
    assert dokumen.status_persetujuan_pemilik is StatusPersetujuan.DIBERIKAN


@pytest.mark.parametrize("bidang", ["jenis", "tingkat_kerahasiaan", "status_persetujuan_pemilik"])
def test_bidang_fr_b06_wajib_diisi(bidang: str) -> None:
    """Tanpa nilai bawaan. Bidang persetujuan yang punya bawaan akan terisi
    sendiri pada dokumen yang persetujuannya tidak pernah diminta."""
    bidang_lain = {
        "id": "dok_001",
        "judul": "Notulen",
        "jenis": JenisSumber.DOKUMEN_SEKOLAH,
        "penerbit": "SDN Sukamaju",
        "tahun": 2026,
        "tingkat_kerahasiaan": TingkatKerahasiaan.PUBLIK,
        "status_persetujuan_pemilik": StatusPersetujuan.DIBERIKAN,
    }
    del bidang_lain[bidang]
    with pytest.raises(ValidationError):
        Dokumen(**bidang_lain)  # type: ignore[arg-type]


def test_tiga_tingkat_kerahasiaan() -> None:
    """Penetapan tim KB-013; nilainya mengikuti D-14 Bagian 5.1."""
    assert {t.value for t in TingkatKerahasiaan} == {"publik", "internal_sekolah", "terbatas"}


def test_empat_status_persetujuan() -> None:
    assert {s.value for s in StatusPersetujuan} == {
        "belum_diminta",
        "diberikan",
        "ditolak",
        "dicabut",
    }


def test_hanya_persetujuan_diberikan_yang_boleh_masuk_korpus() -> None:
    """ET-04 dan D-03 Bagian 3 — dokumen tanpa persetujuan pemilik dikeluarkan.

    Dinyatakan sebagai sifat seluruh daftar: nilai kelima yang ditambahkan
    kelak tidak akan diam-diam ikut lolos.
    """
    boleh = {s for s in StatusPersetujuan if Dokumen.persetujuan_mengizinkan_korpus(s)}
    assert boleh == {StatusPersetujuan.DIBERIKAN}


def test_persetujuan_dapat_ditarik() -> None:
    """Persetujuan yang tidak dapat ditarik bukan persetujuan.

    FR-A05 dan NFR-09 sudah memberi hak itu kepada pengguna; pemilik dokumen
    tidak pantas dapat kurang.
    """
    assert not Dokumen.persetujuan_mengizinkan_korpus(StatusPersetujuan.DICABUT)


def test_dokumen_rahasia_menuntut_persetujuan_pemilik() -> None:
    """**Uji terpenting berkas ini.** Aturan etik yang ditetapkan pemegang
    gerbang: dokumen rahasia hanya masuk korpus atas persetujuan pemiliknya."""
    for tingkat in (TingkatKerahasiaan.INTERNAL_SEKOLAH, TingkatKerahasiaan.TERBATAS):
        rahasia = _dokumen(
            jenis=JenisSumber.LAPORAN_LEMBAGA,
            tingkat_kerahasiaan=tingkat,
            status_persetujuan_pemilik=StatusPersetujuan.BELUM_DIMINTA,
        )
        assert not rahasia.boleh_masuk_korpus(), tingkat


def test_dokumen_sekolah_menuntut_persetujuan_meski_ditandai_publik() -> None:
    """Menutup jalan pencucian: dokumen sekolah yang ditandai `publik` akan
    melewati gerbang persetujuan bila aturannya hanya bersandar pada tingkat.

    ET-04 berbunyi "persetujuan sekolah atas penggunaan dokumen manajerial
    untuk korpus" — tanpa syarat tingkat kerahasiaan.
    """
    dokumen = _dokumen(
        jenis=JenisSumber.DOKUMEN_SEKOLAH,
        tingkat_kerahasiaan=TingkatKerahasiaan.PUBLIK,
        status_persetujuan_pemilik=StatusPersetujuan.BELUM_DIMINTA,
    )
    assert not dokumen.boleh_masuk_korpus()


def test_regulasi_publik_tidak_menuntut_persetujuan() -> None:
    """Permendikdasmen tidak punya pemilik yang dimintai persetujuan.

    Aturan yang menuntutnya akan menghentikan kanal K-A seluruhnya, dan
    kendali yang menghentikan pekerjaan sah akan dimatikan orang.
    """
    dokumen = _dokumen(
        jenis=JenisSumber.REGULASI_RESMI,
        tingkat_kerahasiaan=TingkatKerahasiaan.PUBLIK,
        status_persetujuan_pemilik=StatusPersetujuan.BELUM_DIMINTA,
    )
    assert dokumen.boleh_masuk_korpus()


def test_penarikan_persetujuan_mengeluarkan_dokumen_rahasia() -> None:
    """Persetujuan yang ditarik berlaku seketika, bukan menunggu peninjauan."""
    dokumen = _dokumen(status_persetujuan_pemilik=StatusPersetujuan.DICABUT)
    assert not dokumen.boleh_masuk_korpus()


def test_dokumen_tidak_dapat_diubah_setelah_dibentuk() -> None:
    dokumen = _dokumen()
    with pytest.raises(ValidationError):
        dokumen.status_persetujuan_pemilik = StatusPersetujuan.DIBERIKAN  # type: ignore[misc]


def test_peringkat_diturunkan_dari_jenis_bukan_diisi_pemanggil() -> None:
    """R-07, R-08 — peringkat yang dapat diisi pemanggil dapat dinaikkan
    pemanggil."""
    assert _dokumen().peringkat is Peringkat.T3
    with pytest.raises(ValidationError):
        _dokumen(peringkat=Peringkat.T1)


@pytest.mark.parametrize("bidang", ["id", "judul", "penerbit"])
def test_bidang_teks_tidak_boleh_kosong(bidang: str) -> None:
    with pytest.raises(ValidationError):
        _dokumen(**{bidang: ""})


def test_tahun_wajib_masuk_akal() -> None:
    with pytest.raises(ValidationError):
        _dokumen(tahun=1800)
