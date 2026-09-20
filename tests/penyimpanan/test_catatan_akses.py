"""Uji catatan percobaan akses — R-02, R-12, C-03, AP-04.

Penolakan tanpa catatan membuat percobaan berulang tidak terlihat, dan
percobaan berulang adalah satu-satunya tanda yang tersedia bahwa ada jalur yang
salah arah.

Catatan itu sendiri menjadi sasaran R-12: yang dicatat adalah **percobaannya,
bukan sasarannya**. Id dokumen pada catatan akses menghasilkan daftar dokumen
karantina — kebocoran yang sama dengan yang A-6 tutup, lewat pintu belakang.
"""

import contextlib

import pytest
from src.penyimpanan.area import Area
from src.penyimpanan.catatan_akses import CatatanAkses
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PENJAWABAN, VERIFIKASI
from src.penyimpanan.tiruan import PenyimpanTiruan
from tests.konftes_asinkron import jalankan


def _dengan_catatan() -> tuple[PenyimpanTiruan, CatatanAkses]:
    catatan = CatatanAkses()
    penyimpan = PenyimpanTiruan(catatan=catatan)
    penyimpan.tanam(Area.KARANTINA, "dok_karantina", {"isi": "notulen rapat"})
    return penyimpan, catatan


def _tolak(penyimpan: PenyimpanTiruan) -> None:
    with pytest.raises(GalatAksesDitolak):
        jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_karantina"))


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
    jalankan(penyimpan.baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina"))
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


# ═══════════════════════════════════════════════════════════════════════
# T-7 · ketiga jalur, kedua pelaksana
#
# `tasks.md` T-7 menuntut catatan pada **setiap** jalur, termasuk jalur
# penolakan. Uji di atas menyentuh `baca_dokumen` pada satu pelaksana; enam
# gabungan sisanya tidak terjaga sama sekali sampai bagian ini ada.
#
# Tidak menuntut peladen, dan itu justru yang diuji: penolakan terjadi
# **sebelum** basis data disentuh. Sambungan yang melempar bila dipakai
# membuktikannya — bila pemeriksaan kredensial bergeser ke belakang kueri,
# uji gagal dengan galat sambungan alih-alih lulus diam-diam.
# ═══════════════════════════════════════════════════════════════════════


class SambunganYangMelarang:
    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        raise AssertionError("basis data disentuh sebelum kredensial diperiksa")

    async def execute(self, kueri: str, *argumen: object) -> object:
        raise AssertionError("basis data disentuh sebelum kredensial diperiksa")


def _pelaksana(nama: str, catatan: CatatanAkses) -> object:
    if nama == "tiruan":
        return PenyimpanTiruan(catatan=catatan)
    from src.penyimpanan.postgres import PenyimpanPostgres

    return PenyimpanPostgres(SambunganYangMelarang(), catatan=catatan)


JALUR = {
    "baca": lambda p: p.baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_rahasia"),
    "tulis": lambda p: p.tulis_dokumen(PENJAWABAN, Area.KORPUS, "dok_rahasia", {"a": 1}),
    "pindah": lambda p: p.pindahkan(PENJAWABAN, "dok_rahasia", Area.KARANTINA, Area.KORPUS, "uji"),
}


@pytest.mark.parametrize("pelaksana", ["tiruan", "postgres"])
@pytest.mark.parametrize("jalur", sorted(JALUR))
def test_setiap_jalur_mencatat_penolakannya(pelaksana: str, jalur: str) -> None:
    catatan = CatatanAkses()
    penyimpan = _pelaksana(pelaksana, catatan)

    with pytest.raises(GalatAksesDitolak):
        jalankan(JALUR[jalur](penyimpan))

    assert len(catatan.baris()) == 1, f"{pelaksana}/{jalur} tidak mencatat penolakannya"


@pytest.mark.parametrize("pelaksana", ["tiruan", "postgres"])
@pytest.mark.parametrize("jalur", sorted(JALUR))
def test_catatan_tidak_pernah_memuat_id_dokumen(pelaksana: str, jalur: str) -> None:
    """R-12. Id dokumen pada catatan menghasilkan daftar dokumen karantina
    bagi siapa pun yang dapat membaca catatan."""
    catatan = CatatanAkses()
    penyimpan = _pelaksana(pelaksana, catatan)

    with pytest.raises(GalatAksesDitolak):
        jalankan(JALUR[jalur](penyimpan))

    for baris in catatan.baris():
        assert "dok_rahasia" not in str(baris), str(baris)


@pytest.mark.parametrize("pelaksana", ["tiruan", "postgres"])
def test_pencatatan_mendahului_pelemparan(pelaksana: str) -> None:
    """Percobaan tetap tercatat meski pemanggil menangkap galatnya dan
    berpura-pura tidak terjadi apa-apa."""
    catatan = CatatanAkses()
    penyimpan = _pelaksana(pelaksana, catatan)

    with contextlib.suppress(GalatAksesDitolak):
        jalankan(JALUR["baca"](penyimpan))

    assert len(catatan.baris()) == 1
