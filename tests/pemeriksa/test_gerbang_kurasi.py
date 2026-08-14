"""Uji pemeriksa gerbang kurasi — C-2 fitur 010, C-06, R-02.

Diuji terhadap **pohon yang sengaja dirusak**, bukan hanya terhadap repositori
ini. Pemeriksa yang hanya dijalankan atas pohon yang sehat membuktikan ia tidak
mengeluh; ia tidak membuktikan ia menemukan apa pun. Pelajaran TA-01: laporan
bersih yang tidak memeriksa apa pun adalah laporan yang keliru.
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.gerbang_kurasi import (
    BERKAS_PUTUSAN,
    periksa_gerbang_kurasi,
)

AKAR = Path(__file__).resolve().parents[2]

PUTUSAN_BERSIH = '''"""Gerbang putusan tiruan."""

from pydantic import BaseModel


class ButirTayang(BaseModel):
    butir: str
    putusan: str


def terapkan() -> ButirTayang:
    return ButirTayang(butir="a", putusan="b")
'''

MODUL_BIASA = '''"""Modul tiruan yang tidak membentuk butir tayang."""


def tayangkan() -> None:
    return None
'''


def _pohon(tmp_path: Path, *, putusan: str = PUTUSAN_BERSIH, modul: str = MODUL_BIASA) -> Path:
    akar = tmp_path / "pohon"
    (akar / BERKAS_PUTUSAN).parent.mkdir(parents=True)
    (akar / BERKAS_PUTUSAN).write_text(putusan, encoding="utf-8")
    (akar / "src" / "ingest" / "kurasi" / "feed.py").write_text(modul, encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_gerbang_kurasi(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    """Pernyataan yang **paling lemah** pada berkas ini, dan ia sengaja tidak
    berdiri sendiri: seluruh uji lain di bawahnya yang membuatnya berarti."""
    assert periksa_gerbang_kurasi(AKAR) == []


# ------------------------------------------------------------------- aturan 1


def test_pembentukan_di_luar_gerbang_ditemukan(tmp_path: Path) -> None:
    """**Aturan 1**, dan ia C-06 itu sendiri.

    Modul feed yang membentuk `ButirTayang` sendiri menayangkan butir yang
    tidak seorang kurator pun putuskan.
    """
    rusak = MODUL_BIASA + '\n\ndef curang() -> None:\n    ButirTayang(butir="a", putusan="b")\n'
    temuan = periksa_gerbang_kurasi(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert "ButirTayang" in str(temuan[0])


def test_pembentukan_pada_gerbang_tidak_ditemukan(tmp_path: Path) -> None:
    """Gerbangnya **boleh** membentuknya — itu gunanya."""
    assert periksa_gerbang_kurasi(_pohon(tmp_path)) == []


# ------------------------------------------------------------------- aturan 2


def test_bidang_putusan_berbawaan_ditemukan(tmp_path: Path) -> None:
    """**Aturan 2**, dan ia menutup lubang aturan 1.

    Pembentukan yang terbatas pada satu modul tetap menghasilkan butir yang
    tidak diputuskan bila bidang putusannya mengisi dirinya sendiri — dan tidak
    satu uji perilaku pun gagal karenanya.
    """
    rusak = PUTUSAN_BERSIH.replace("    putusan: str", '    putusan: str = "setujui"')
    temuan = periksa_gerbang_kurasi(_pohon(tmp_path, putusan=rusak))
    assert temuan
    assert "bawaan" in str(temuan[0])


def test_bidang_putusan_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Butir tayang yang tidak membawa putusannya tidak dapat ditelusuri kepada
    kurator mana pun — FR-I05 menanyakan justru itu."""
    rusak = PUTUSAN_BERSIH.replace("    putusan: str\n", "")
    temuan = periksa_gerbang_kurasi(_pohon(tmp_path, putusan=rusak))
    assert temuan
    assert "putusan" in str(temuan[0])


def test_tipe_yang_dihapus_ditemukan(tmp_path: Path) -> None:
    """Tipe yang hilang bukan tipe yang aman: ia tipe yang penjagaannya pindah
    entah ke mana."""
    rusak = PUTUSAN_BERSIH.replace("class ButirTayang(BaseModel):", "class Lain(BaseModel):")
    temuan = periksa_gerbang_kurasi(_pohon(tmp_path, putusan=rusak))
    assert temuan


def test_gerbang_yang_dihapus_ditemukan(tmp_path: Path) -> None:
    """Menghapus tempat butir diputuskan bukan cara sah meloloskan pemeriksa.

    Bentuk yang sama dengan pemeriksa C-02 yang menemukan `kredensial_baku.py`
    hilang, dan pemeriksa C-16 yang menemukan rumah tetapan hilang.
    """
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    temuan = periksa_gerbang_kurasi(akar)
    assert temuan
    assert "tidak ditemukan" in str(temuan[0])


# ---------------------------------------------------------------- pendaftaran


def test_c06_terdaftar_dengan_pemeriksa_bukan_fitur_pengunci() -> None:
    """C-06 berpindah dari `fitur_pengunci="010 …"` menjadi `pemeriksa=`."""
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-06")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None
