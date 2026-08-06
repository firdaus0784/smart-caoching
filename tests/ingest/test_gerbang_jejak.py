"""Uji penyambungan jejak ke gerbang — R-11, R-12.

Modul jejak yang tidak dipanggil siapa pun adalah gerbang yang lulus karena
tidak memeriksa apa pun — pelajaran T-7 fitur 014, dan alasan berkas uji ini
ada terpisah dari `test_jejak.py`.
"""

import pytest
from src.ingest.dokumen import Dokumen, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.gerbang import Gerbang
from src.ingest.jejak import GalatJejak
from src.ingest.peringkat import JenisSumber
from src.penyimpanan.area import Area
from src.penyimpanan.kredensial_baku import VERIFIKASI
from src.penyimpanan.tiruan import PenyimpanTiruan

ID = "vrf_001"
BERSIH = "Kepala sekolah menugaskan wakil kurikulum menyusun jadwal supervisi."


def _dokumen() -> Dokumen:
    return Dokumen(
        id="dok_001",
        judul="Notulen rapat pleno",
        jenis=JenisSumber.DOKUMEN_SEKOLAH,
        penerbit="SDN Sukamaju",
        tahun=2026,
        tingkat_kerahasiaan=TingkatKerahasiaan.INTERNAL_SEKOLAH,
        status_persetujuan_pemilik=StatusPersetujuan.DIBERIKAN,
    )


def _gerbang() -> Gerbang:
    gerbang = Gerbang(PenyimpanTiruan())
    gerbang.terima(_dokumen(), BERSIH)
    return gerbang


def test_persetujuan_menghasilkan_satu_baris_jejak() -> None:
    """R-11 — perpindahan karantina ke korpus tercatat lengkap."""
    gerbang = _gerbang()
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID, alasan="anonimisasi terverifikasi")
    baris = gerbang.jejak.baris()
    assert len(baris) == 1
    assert baris[0].id_pelaku == ID
    assert baris[0].dari_area is Area.KARANTINA
    assert baris[0].ke_area is Area.KORPUS


def test_penolakan_juga_tercatat() -> None:
    """Putusan menahan sama perlu ditelusuri dengan putusan memindahkan.

    Jejak yang hanya mencatat yang berpindah membuat dokumen yang ditolak
    berulang kali tidak terlihat sama sekali.
    """
    gerbang = _gerbang()
    gerbang.tolak(VERIFIKASI, "dok_001", id_verifikator=ID, alasan="anonimisasi belum lengkap")
    baris = gerbang.jejak.baris()
    assert len(baris) == 1
    assert baris[0].dari_area is Area.KARANTINA
    assert baris[0].ke_area is Area.KARANTINA


def test_penarikan_persetujuan_tercatat() -> None:
    """Dokumen yang keluar dari korpus tanpa jejak adalah korpus yang menyusut
    tanpa penjelasan."""
    gerbang = _gerbang()
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID, alasan="anonimisasi terverifikasi")
    gerbang.cabut_persetujuan(
        "dok_001", id_pemohon="ops_001", alasan="pemilik menarik persetujuannya"
    )
    baris = gerbang.jejak.baris()
    assert len(baris) == 2
    assert baris[1].dari_area is Area.KORPUS
    assert baris[1].ke_area is Area.KARANTINA


def test_alasan_bermuatan_data_pribadi_membatalkan_penolakan() -> None:
    """R-12 — **seluruh putusannya batal, bukan hanya jejaknya.**

    Menulis putusan lalu gagal menjejakkannya menghasilkan perubahan keadaan
    yang tidak tercatat — persis yang R-11 larang. Verifikator menulis ulang
    alasannya, dan itu memang yang diinginkan.
    """
    gerbang = _gerbang()
    with pytest.raises(GalatJejak):
        gerbang.tolak(
            VERIFIKASI,
            "dok_001",
            id_verifikator=ID,
            alasan="memuat NIK 3211012509870001 pada halaman 3",
        )
    assert gerbang.jejak.baris() == []
    assert gerbang.alasan_terakhir(VERIFIKASI, "dok_001") == ""


def test_alasan_bermuatan_data_pribadi_membatalkan_persetujuan() -> None:
    """Sisi yang sama pada arah sebaliknya: dokumen tetap di karantina."""
    gerbang = _gerbang()
    with pytest.raises(GalatJejak):
        gerbang.setujui(
            VERIFIKASI,
            "dok_001",
            id_verifikator=ID,
            alasan="pemilik dihubungi di 081234567890",
        )
    assert gerbang.area(VERIFIKASI, "dok_001") is Area.KARANTINA
    assert gerbang.jejak.baris() == []


def test_jejak_tidak_memuat_kutipan_isi_dokumen() -> None:
    """Sifat, bukan satu kasus — D-14 Bagian 5.1.

    Jalur sah dijalankan sepenuhnya, lalu seluruh baris diperiksa terhadap isi
    dokumen. Uji yang hanya memeriksa satu alasan akan lolos pada versi yang
    menyalin isi lewat bidang lain.
    """
    gerbang = _gerbang()
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID, alasan="anonimisasi terverifikasi")
    gerbang.cabut_persetujuan(
        "dok_001", id_pemohon="ops_001", alasan="pemilik menarik persetujuannya"
    )
    for baris in gerbang.jejak.baris():
        for potongan in BERSIH.split():
            if len(potongan) > 6:
                assert potongan not in baris.alasan
