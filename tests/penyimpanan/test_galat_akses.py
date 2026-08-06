"""Uji galat akses penyimpanan — R-02, R-12, C-03, C-13, D-14 Bagian 4.2.

Galat ini menyentuh C-03 dari arah yang tidak terduga. Pesan yang menyebut area
akan memberi tahu pemanggil bahwa dokumen yang dimintanya berada di karantina —
keterangan yang tidak berhak diketahui jalur penjawaban.

Namanya `test_galat_akses.py`, bukan `test_galat.py`: sudah ada
`tests/llm/test_galat.py`, dan pytest tanpa `__init__.py` memakai nama dasar
berkas sebagai nama modul, sehingga nama kembar menggagalkan pengumpulan
seluruh rangkaian.
"""

from src.llm.galat import KodeGalat, kalimat_terlalu_panjang
from src.penyimpanan.area import Area
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PENJAWABAN


def _galat() -> GalatAksesDitolak:
    return GalatAksesDitolak(kredensial=PENJAWABAN, area=Area.KARANTINA, operasi="baca")


def test_pesan_pengguna_tidak_menyebut_area() -> None:
    """Pesan yang menyebut "karantina" memberi tahu pemanggil bahwa dokumen
    itu ada dan sedang menunggu verifikasi — keterangan yang justru dijaga."""
    pesan = _galat().tanggapan().galat.pesan_pengguna.lower()
    for area in Area:
        assert area.value not in pesan


def test_pesan_pengguna_tidak_menyebut_nama_kredensial() -> None:
    """Nama kredensial rincian teknis; D-14 Bagian 4.2 menaruhnya di log."""
    assert PENJAWABAN.nama not in _galat().tanggapan().galat.pesan_pengguna.lower()


def test_pesan_pengguna_memenuhi_batas_kata() -> None:
    """C-13, NFR-19."""
    assert kalimat_terlalu_panjang(_galat().tanggapan().galat.pesan_pengguna) == []


def test_kode_galat_tidak_berwenang() -> None:
    """Bukan SUMBER_TIDAK_ADA. Yang kedua menyembunyikan lebih banyak tetapi
    berbohong tentang sesuatu yang tidak diperiksa: kredensial diperiksa
    sebelum data disentuh (A-6), sehingga penyimpan memang tidak tahu apakah
    dokumen itu ada."""
    assert _galat().tanggapan().galat.kode is KodeGalat.TIDAK_BERWENANG


def test_rincian_teknis_tersedia_untuk_log() -> None:
    """Menyembunyikan dari pengguna bukan berarti membuang."""
    catatan = _galat().untuk_log()
    assert PENJAWABAN.nama in catatan
    assert Area.KARANTINA.value in catatan
    assert "baca" in catatan


def test_catatan_log_tidak_memuat_id_dokumen() -> None:
    """R-12 — yang dicatat percobaannya, bukan sasarannya."""
    assert "dok_" not in _galat().untuk_log()


def test_id_jejak_ada_dan_berbeda_tiap_kejadian() -> None:
    a, b = _galat(), _galat()
    assert a.id_jejak.startswith("trc_")
    assert a.id_jejak != b.id_jejak
