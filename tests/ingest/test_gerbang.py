"""Uji gerbang karantina — R-03, R-04, R-05, FR-B05, FR-B07, ET-04, KD-02.

Tiga gerbang berdiri sendiri dan ketiganya wajib dilewati: persetujuan pemilik
(ET-04), verifikasi anonimisasi (FR-B05), dan kelak pemeriksa pola adversarial
(FR-B08). Menggabungkannya menjadi satu pemeriksaan akan membuat satu
kelonggaran membuka ketiganya.

Penarikan persetujuan **mengeluarkan** dokumen dari korpus, bukan sekadar
mencegahnya masuk (KB-014). Persetujuan yang ditarik tetapi dokumennya tetap
dipakai bukan penarikan.
"""

import pytest
from src.ingest.dokumen import Dokumen, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.gerbang import GalatGerbang, Gerbang
from src.ingest.peringkat import JenisSumber
from src.penyimpanan.area import Area
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PENJAWABAN, VERIFIKASI
from src.penyimpanan.tiruan import GalatDokumenTidakAda, PenyimpanTiruan

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


def _gerbang() -> Gerbang:
    return Gerbang(PenyimpanTiruan())


# --- B-3: masuk selalu ke karantina -----------------------------------------


def test_dokumen_baru_masuk_karantina() -> None:
    """R-03."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    assert gerbang.area(_dokumen().id) is Area.KARANTINA


def test_tidak_ada_jalan_menaruh_dokumen_langsung_di_korpus() -> None:
    """R-03 dinyatakan sebagai sifat antarmukanya, bukan sebagai satu jalur
    yang kebetulan benar. Metode `terima` tidak menerima parameter area."""
    import inspect

    assert "area" not in inspect.signature(Gerbang.terima).parameters


def test_dokumen_di_karantina_tidak_terbaca_jalur_penjawaban() -> None:
    """C-03 lewat gerbang."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    with pytest.raises(GalatAksesDitolak):
        gerbang.penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_001")


# --- B-4: perpindahan menuntut persetujuan verifikator -----------------------


def test_pindah_dengan_persetujuan_verifikator() -> None:
    """R-04 — sisi positif."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    gerbang.setujui(
        VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="anonimisasi bersih"
    )
    assert gerbang.area("dok_001") is Area.KORPUS


def test_pindah_tanpa_id_verifikator_ditolak() -> None:
    """Persetujuan tanpa nama bukan persetujuan; ia tidak dapat ditelusuri."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    with pytest.raises(GalatGerbang):
        gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator="", alasan="bersih")


def test_pindah_dengan_kredensial_penjawaban_ditolak() -> None:
    """R-04 — kredensial diperiksa, bukan hanya niat pemanggil."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    with pytest.raises(GalatAksesDitolak):
        gerbang.setujui(PENJAWABAN, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")


def test_dokumen_tanpa_persetujuan_pemilik_tidak_dapat_disetujui() -> None:
    """ET-04 — verifikator tidak dapat menggantikan persetujuan pemilik.

    Keduanya gerbang yang berbeda: verifikator menilai anonimisasi, pemilik
    mengizinkan pemakaian. Satu tidak menggantikan yang lain.
    """
    gerbang = _gerbang()
    gerbang.terima(
        _dokumen(status_persetujuan_pemilik=StatusPersetujuan.BELUM_DIMINTA), isi={"teks": "..."}
    )
    with pytest.raises(GalatGerbang):
        gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")


# --- B-5: penolakan menahan, penarikan mengeluarkan --------------------------


def test_penolakan_menahan_dokumen_beserta_alasan() -> None:
    """R-05, FR-B07."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    gerbang.tolak(
        VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="halaman 3 belum bersih"
    )
    assert gerbang.area("dok_001") is Area.KARANTINA
    assert gerbang.alasan_terakhir("dok_001") == "halaman 3 belum bersih"


def test_penolakan_tanpa_alasan_ditolak() -> None:
    """Penolakan tanpa alasan tidak dapat ditindaklanjuti pengunggahnya."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    with pytest.raises(GalatGerbang):
        gerbang.tolak(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="")


def test_penarikan_tidak_menuntut_kredensial() -> None:
    """Mencabut akses selalu aman: ia hanya mengurangi apa yang terjangkau.

    Menuntut izin untuk menarik izin adalah rintangan yang hanya menghambat
    pihak yang berhak.
    """
    import inspect

    assert "kredensial" not in inspect.signature(Gerbang.cabut_persetujuan).parameters


def test_penarikan_persetujuan_mengeluarkan_dokumen_dari_korpus() -> None:
    """**Uji terpenting berkas ini** — KB-014.

    Persetujuan yang ditarik tetapi dokumennya tetap dipakai bukan penarikan.
    """
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
    assert gerbang.area("dok_001") is Area.KORPUS

    gerbang.cabut_persetujuan("dok_001", alasan="pemilik menarik izin")
    assert gerbang.area("dok_001") is Area.KARANTINA


def test_dokumen_yang_ditarik_tidak_terbaca_jalur_penjawaban() -> None:
    """Berpindah areanya bukan sekadar berganti penanda.

    Galatnya `GalatDokumenTidakAda`, bukan `GalatAksesDitolak`: jalur
    penjawaban memang berhak membaca korpus, dan dokumennya yang sudah tidak
    ada di sana. Justru itu bentuk yang benar — penarikan memindahkan
    dokumennya, tidak mencabut hak baca korpus dari siapa pun.
    """
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
    gerbang.cabut_persetujuan("dok_001", alasan="pemilik menarik izin")
    with pytest.raises(GalatDokumenTidakAda):
        gerbang.penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_001")

    # Dan karantina tetap tertutup bagi jalur penjawaban.
    with pytest.raises(GalatAksesDitolak):
        gerbang.penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_001")


def test_dokumen_yang_ditarik_tidak_dapat_disetujui_ulang_tanpa_izin_baru() -> None:
    """Penarikan yang dapat dibatalkan verifikator sendiri bukan penarikan."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
    gerbang.cabut_persetujuan("dok_001", alasan="pemilik menarik izin")
    with pytest.raises(GalatGerbang):
        gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")


def test_penolakan_tanpa_nama_verifikator_ditolak() -> None:
    """Sepadan dengan `setujui`. Penolakan yang tidak dapat ditelusuri sama
    tidak dapat dipertanggungjawabkannya dengan persetujuan yang begitu."""
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    with pytest.raises(GalatGerbang):
        gerbang.tolak(VERIFIKASI, "dok_001", id_verifikator="", alasan="halaman 3")


def test_penarikan_pada_dokumen_yang_masih_di_karantina() -> None:
    """Tidak ada yang dipindahkan, tetapi statusnya tetap berubah.

    Itu yang menutup jalan persetujuan menyusul: dokumen yang izinnya ditarik
    sebelum sempat diverifikasi tidak boleh lolos hanya karena ia kebetulan
    belum berpindah.
    """
    gerbang = _gerbang()
    gerbang.terima(_dokumen(), isi={"teks": "..."})
    gerbang.cabut_persetujuan("dok_001", alasan="pemilik menarik izin")
    assert gerbang.area("dok_001") is Area.KARANTINA
    with pytest.raises(GalatGerbang):
        gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
