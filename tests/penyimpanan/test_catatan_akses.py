"""Uji catatan percobaan akses — R-02, R-12, C-03, AP-04.

Penolakan tanpa catatan membuat percobaan berulang tidak terlihat, dan
percobaan berulang adalah satu-satunya tanda yang tersedia bahwa ada jalur yang
salah arah.

Catatan itu sendiri menjadi sasaran R-12: yang dicatat adalah **percobaannya,
bukan sasarannya**. Id dokumen pada catatan akses menghasilkan daftar dokumen
karantina — kebocoran yang sama dengan yang A-6 tutup, lewat pintu belakang.
"""

import pytest
from src.penyimpanan.area import Area
from src.penyimpanan.catatan_akses import CatatanAkses
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PENJAWABAN, VERIFIKASI
from src.penyimpanan.tiruan import PenyimpanTiruan


def _dengan_catatan() -> tuple[PenyimpanTiruan, CatatanAkses]:
    catatan = CatatanAkses()
    penyimpan = PenyimpanTiruan(catatan=catatan)
    penyimpan.tanam(Area.KARANTINA, "dok_karantina", {"isi": "notulen rapat"})
    return penyimpan, catatan


def _tolak(penyimpan: PenyimpanTiruan) -> None:
    with pytest.raises(GalatAksesDitolak):
        penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_karantina")


def test_penolakan_tercatat() -> None:
    penyimpan, catatan = _dengan_catatan()
    _tolak(penyimpan)
    assert len(catatan.baris()) == 1


def test_catatan_memuat_kredensial_operasi_dan_area() -> None:
    penyimpan, catatan = _dengan_catatan()
    _tolak(penyimpan)
    baris = catatan.baris()[0]
    assert baris.kredensial == PENJAWABAN.nama
    assert baris.operasi == "baca"
    assert baris.area is Area.KARANTINA


def test_catatan_tidak_memuat_id_dokumen() -> None:
    """R-12 — kebocoran A-6 lewat pintu belakang."""
    penyimpan, catatan = _dengan_catatan()
    _tolak(penyimpan)
    assert "dok_karantina" not in repr(catatan.baris()[0])


def test_catatan_tidak_memuat_isi_dokumen() -> None:
    penyimpan, catatan = _dengan_catatan()
    _tolak(penyimpan)
    assert "notulen" not in repr(catatan.baris()[0])


def test_akses_yang_diizinkan_tidak_dicatat() -> None:
    """Mencatat seluruh pembacaan korpus menghasilkan jejak perilaku pengguna,
    dan itu urusan telemetri yang tunduk C-04 — bukan urusan lapisan
    penyimpanan (AP-04)."""
    penyimpan, catatan = _dengan_catatan()
    penyimpan.baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina")
    assert catatan.baris() == []


def test_catatan_tambah_saja() -> None:
    """Catatan yang dapat dikosongkan dari luar tidak menjaga apa pun."""
    penyimpan, catatan = _dengan_catatan()
    _tolak(penyimpan)
    catatan.baris().clear()
    assert len(catatan.baris()) == 1


def test_penyimpan_tanpa_catatan_tetap_menolak() -> None:
    """Penolakan tidak boleh bergantung pada tersedianya tempat mencatat."""
    penyimpan = PenyimpanTiruan()
    penyimpan.tanam(Area.KARANTINA, "dok_karantina", {"isi": "x"})
    _tolak(penyimpan)


def test_percobaan_berulang_tercatat_seluruhnya() -> None:
    """Meringkasnya menjadi satu baris berhitung menghapus waktu, dan waktu
    yang membedakan percobaan iseng dari percobaan berulang."""
    penyimpan, catatan = _dengan_catatan()
    for _ in range(3):
        _tolak(penyimpan)
    assert len(catatan.baris()) == 3
