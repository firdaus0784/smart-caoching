"""Uji penjagaan peringkat kepercayaan — R-07a, R-08, C-03, C-19, D-13 Bagian 6.

Dua kebutuhan yang paling mudah dianggap sudah dipenuhi kebutuhan lain, dan
justru itu sebabnya keduanya diuji tersendiri.

**R-07a.** D-13 Bagian 6 mendefinisikan T3 sebagai dokumen sekolah teranonimkan
**dan terverifikasi**. Selama dokumen masih di karantina, kata kedua belum
berlaku — sehingga peringkatnya belum sah dan tidak boleh terbaca jalur
penjawaban.

**R-08.** Peringkat yang dapat diubah pemanggil adalah peringkat yang dapat
dinaikkan pemanggil, dan C-19 bersandar padanya.
"""

import pytest
from pydantic import ValidationError
from src.ingest.dokumen import Dokumen, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.gerbang import Gerbang
from src.ingest.peringkat import JenisSumber
from src.llm.tipe import Peringkat
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, VERIFIKASI
from src.penyimpanan.tiruan import PenyimpanTiruan

ID_VERIFIKATOR = "vrf_001"


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


def _gerbang_terisi() -> Gerbang:
    gerbang = Gerbang(PenyimpanTiruan())
    gerbang.terima(_dokumen(), "Notulen rapat pleno bulan Maret.")
    return gerbang


# --- B-6: R-07a ---------------------------------------------------------------


def test_peringkat_dokumen_karantina_tidak_terbaca_jalur_penjawaban() -> None:
    """**Uji terpenting berkas ini.** Dokumen berperingkat T3 masih di
    karantina, sehingga kata "terverifikasi" pada D-13 Bagian 6 belum berlaku."""
    with pytest.raises(GalatAksesDitolak):
        _gerbang_terisi().peringkat(PENJAWABAN, "dok_001")


def test_peringkat_dokumen_karantina_tidak_terbaca_pemanggil_llm() -> None:
    """KD-10 menyebut pemanggil LLM terpisah, dan ia diuji terpisah."""
    with pytest.raises(GalatAksesDitolak):
        _gerbang_terisi().peringkat(PEMANGGIL_LLM, "dok_001")


def test_verifikasi_dapat_membaca_peringkat_di_karantina() -> None:
    """Verifikator perlu melihatnya justru untuk menilai."""
    assert _gerbang_terisi().peringkat(VERIFIKASI, "dok_001") is Peringkat.T3


def test_peringkat_terbaca_jalur_penjawaban_setelah_disetujui() -> None:
    """Gerbang R-04 yang menyahkannya, bukan berjalannya waktu."""
    gerbang = _gerbang_terisi()
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
    assert gerbang.peringkat(PENJAWABAN, "dok_001") is Peringkat.T3


def test_dokumen_tak_dikenal_dijawab_sama_dengan_dokumen_karantina() -> None:
    """Jawaban yang berbeda untuk dokumen ada dan tidak ada sudah cukup untuk
    menyusun daftar dokumen karantina — kebocoran yang sama dengan A-6."""
    gerbang = _gerbang_terisi()
    galat = []
    for id_dokumen in ("dok_001", "dok_tidak_pernah_ada"):
        with pytest.raises(GalatAksesDitolak) as tertangkap:
            gerbang.peringkat(PENJAWABAN, id_dokumen)
        galat.append(tertangkap.value.tanggapan().galat.pesan_pengguna)
    assert galat[0] == galat[1]


def test_peringkat_setelah_penarikan_tidak_terbaca_lagi() -> None:
    """Penarikan persetujuan mengembalikan dokumen ke karantina, dan
    peringkatnya ikut tertutup kembali."""
    gerbang = _gerbang_terisi()
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
    gerbang.cabut_persetujuan("dok_001", alasan="pemilik menarik izin")
    with pytest.raises(GalatAksesDitolak):
        gerbang.peringkat(PENJAWABAN, "dok_001")


# --- B-7: R-08 ----------------------------------------------------------------


def test_peringkat_tidak_dapat_disetel_pada_dokumen() -> None:
    """Peringkat diturunkan dari jenis, bukan disimpan sebagai bidang."""
    with pytest.raises(ValidationError):
        _dokumen().peringkat = Peringkat.T1  # type: ignore[misc]


def test_peringkat_tidak_dapat_diselundupkan_lewat_salinan() -> None:
    """`model_copy` melewati validasi, sehingga ia jalan yang paling mungkin
    dicoba. Peringkat tetap diturunkan dari jenis."""
    salinan = _dokumen().model_copy(update={"peringkat": Peringkat.T1})
    assert salinan.peringkat is Peringkat.T3


def test_gerbang_tidak_menyediakan_jalan_mengubah_peringkat() -> None:
    """Dinyatakan sebagai sifat antarmukanya. Metode yang tidak ada tidak
    dapat dipanggil keliru."""
    tersedia = {nama for nama in dir(Gerbang) if not nama.startswith("_")}
    assert not {nama for nama in tersedia if "peringkat" in nama} - {"peringkat"}


def test_mengubah_jenis_menuntut_dokumen_baru() -> None:
    """Satu-satunya jalan sah mengubah peringkat adalah mengganti jenis
    sumbernya, dan itu berarti dokumen lain — bukan dokumen yang sama
    dinaikkan peringkatnya."""
    lain = _dokumen(jenis=JenisSumber.REGULASI_RESMI)
    assert lain.peringkat is Peringkat.T1
    assert _dokumen().peringkat is Peringkat.T3
