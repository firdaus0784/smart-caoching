"""Metadata asal ikut tercatat saat dokumen masuk korpus — T-3 fitur 032, TK-82 A.

Metadata `Dokumen` semula hanya hidup pada memori gerbang ingesti. Sejak putusan
TK-82 A (KB-243) gerbang menyerahkannya kepada pemindahan ke korpus, dan
penyimpan mencatatnya dalam pernyataan yang sama. Aturan gerbang tidak berubah
(K-8): yang diuji di sini hanya penyerahannya.
"""

from src.ingest.dokumen import Dokumen, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.gerbang import Gerbang
from src.ingest.peringkat import JenisSumber
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.kredensial_baku import VERIFIKASI
from src.penyimpanan.tiruan import PenyimpanTiruan
from tests.konftes_asinkron import jalankan


def _dokumen(**ubah: object) -> Dokumen:
    bidang: dict[str, object] = {
        "id": "dok_032",
        "judul": "Permendikdasmen Nomor 1 Tahun 2026",
        "jenis": JenisSumber.REGULASI_RESMI,
        "penerbit": "Kemendikdasmen",
        "tahun": 2026,
        "tingkat_kerahasiaan": TingkatKerahasiaan.PUBLIK,
        "status_persetujuan_pemilik": StatusPersetujuan.BELUM_DIMINTA,
    }
    bidang.update(ubah)
    return Dokumen(**bidang)  # type: ignore[arg-type]


def _diterima(dokumen: Dokumen) -> tuple[Gerbang, PenyimpanTiruan]:
    penyimpan = PenyimpanTiruan()
    gerbang = Gerbang(penyimpan)
    jalankan(gerbang.terima(dokumen, "Pasal 7 mengatur rencana kerja sekolah."))
    return gerbang, penyimpan


def test_persetujuan_mencatat_metadata_dokumen_apa_adanya() -> None:
    gerbang, penyimpan = _diterima(_dokumen())
    jalankan(gerbang.setujui(VERIFIKASI, "dok_032", id_verifikator="vrf_001", alasan="bersih"))
    assert penyimpan.metadata_tercatat("dok_032") == (
        MetadataDokumen(
            judul="Permendikdasmen Nomor 1 Tahun 2026",
            jenis="regulasi_resmi",
            penerbit="Kemendikdasmen",
            tahun=2026,
            tingkat_kerahasiaan="publik",
        ),
    )


def test_dokumen_sekolah_tercatat_dengan_tingkat_kerahasiaannya() -> None:
    """Tingkat yang dicatat adalah yang diperiksa gerbang ET-04, bukan salinan
    yang diketik ulang (TK-82 B ditolak)."""
    gerbang, penyimpan = _diterima(
        _dokumen(
            jenis=JenisSumber.DOKUMEN_SEKOLAH,
            tingkat_kerahasiaan=TingkatKerahasiaan.INTERNAL_SEKOLAH,
            status_persetujuan_pemilik=StatusPersetujuan.DIBERIKAN,
        )
    )
    jalankan(gerbang.setujui(VERIFIKASI, "dok_032", id_verifikator="vrf_001", alasan="bersih"))
    (satu,) = penyimpan.metadata_tercatat("dok_032")
    assert (satu.jenis, satu.tingkat_kerahasiaan) == ("dokumen_sekolah", "internal_sekolah")


def test_penolakan_dan_penarikan_tidak_mencatat_metadata() -> None:
    gerbang, penyimpan = _diterima(_dokumen())
    jalankan(gerbang.tolak(VERIFIKASI, "dok_032", id_verifikator="vrf_001", alasan="NIK hal. 2"))
    assert penyimpan.metadata_tercatat("dok_032") == ()

    gerbang, penyimpan = _diterima(
        _dokumen(
            jenis=JenisSumber.DOKUMEN_SEKOLAH,
            status_persetujuan_pemilik=StatusPersetujuan.DIBERIKAN,
        )
    )
    jalankan(gerbang.setujui(VERIFIKASI, "dok_032", id_verifikator="vrf_001", alasan="bersih"))
    jalankan(gerbang.cabut_persetujuan("dok_032", id_pemohon="tim_etik", alasan="ditarik"))
    assert len(penyimpan.metadata_tercatat("dok_032")) == 1, "penarikan tidak menambah catatan"
