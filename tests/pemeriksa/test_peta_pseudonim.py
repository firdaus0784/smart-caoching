"""Uji pemeriksa peta pseudonim — C-1 fitur 022, C-05.

Diuji terhadap **pohon yang sengaja dirusak**, masing-masing aturan terpisah.
Pemeriksa yang hanya dijalankan atas pohon yang sehat membuktikan ia tidak
mengeluh; ia tidak membuktikan ia menemukan apa pun (TA-01).
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.peta_pseudonim import (
    BERKAS_AREA,
    BERKAS_PSEUDONIM,
    periksa_peta_pseudonim,
)

AKAR = Path(__file__).resolve().parents[2]

PSEUDONIM_BERSIH = '''"""Peta pseudonim tiruan."""

from pydantic import BaseModel


class KredensialPseudonim(BaseModel):
    nama: str


class PetaPseudonim:
    def pseudonim_bagi(self, id_pengguna: str, *, kredensial: KredensialPseudonim) -> str:
        return id_pengguna
'''

AREA_BERSIH = '''"""Area tiruan."""

from enum import Enum


class Area(Enum):
    KARANTINA = "karantina"
    KORPUS = "korpus"
'''

MODUL_BIASA = '''"""Modul layanan tiruan."""


def layani() -> None:
    return None
'''


def _pohon(
    tmp_path: Path,
    *,
    pseudonim: str = PSEUDONIM_BERSIH,
    area: str = AREA_BERSIH,
    modul: str = MODUL_BIASA,
) -> Path:
    akar = tmp_path / "pohon"
    (akar / BERKAS_PSEUDONIM).parent.mkdir(parents=True)
    (akar / BERKAS_PSEUDONIM).write_text(pseudonim, encoding="utf-8")
    (akar / BERKAS_AREA).write_text(area, encoding="utf-8")
    (akar / "src" / "api").mkdir(parents=True)
    (akar / "src" / "api" / "layanan.py").write_text(modul, encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_peta_pseudonim(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    """Pernyataan yang **paling lemah** pada berkas ini, dan ia sengaja tidak
    berdiri sendiri: seluruh uji lain di bawahnya yang membuatnya berarti."""
    assert periksa_peta_pseudonim(AKAR) == []


# ------------------------------------------------------------------- aturan 1


def test_pembentukan_kredensial_pada_src_ditemukan(tmp_path: Path) -> None:
    """**Aturan 1.** Kredensial yang dibentuk layanan aplikasi adalah kredensial
    yang dimilikinya, betapa pun tipenya terpisah."""
    rusak = MODUL_BIASA + '\n\ndef curang() -> None:\n    KredensialPseudonim(nama="layanan")\n'
    temuan = periksa_peta_pseudonim(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert "KredensialPseudonim" in str(temuan[0])


def test_pembentukan_pada_modulnya_sendiri_juga_ditemukan(tmp_path: Path) -> None:
    """**Dilarang di mana pun pada `src/`, termasuk pada modulnya sendiri.**

    Ini yang membedakannya dari aturan `ButirTayang` C-06 dan `Instruksi`
    ADR-13: keduanya membatasi **di mana** boleh dibentuk, sedangkan ini
    melarang **di mana pun**. Modul yang membentuk kredensialnya sendiri
    menyediakan satu yang tinggal diambil.
    """
    rusak = PSEUDONIM_BERSIH + '\n\nBAKU = KredensialPseudonim(nama="baku")\n'
    temuan = periksa_peta_pseudonim(_pohon(tmp_path, pseudonim=rusak))
    assert temuan


def test_modul_pseudonim_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Menghapus tempat kunci dipisahkan bukan cara sah meloloskan pemeriksa.

    Bentuk yang sama dengan pemeriksa C-02 yang menemukan `kredensial_baku.py`
    hilang, dan C-16 yang menemukan rumah tetapan hilang.
    """
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    temuan = periksa_peta_pseudonim(akar)
    assert temuan
    assert any("tidak ditemukan" in str(t) for t in temuan)


# ------------------------------------------------------------------- aturan 2


def test_impor_peta_di_luar_modulnya_ditemukan(tmp_path: Path) -> None:
    """**Aturan 2** menutup lubang aturan 1: modul yang mengimpor `PetaPseudonim`
    sudah cukup dekat untuk memanggilnya dengan kredensial yang diteruskan dari
    tempat lain."""
    rusak = (
        "from src.penyimpanan.pseudonim import PetaPseudonim\n\n" + MODUL_BIASA
    )
    temuan = periksa_peta_pseudonim(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert "diimpor di luar modulnya" in str(temuan[0])


def test_modulnya_sendiri_boleh_menyebut_petanya(tmp_path: Path) -> None:
    assert periksa_peta_pseudonim(_pohon(tmp_path)) == []


# ------------------------------------------------------------------- aturan 3


def test_area_bernilai_tiga_ditemukan(tmp_path: Path) -> None:
    """**Aturan 3, dan ia menutup dua aturan pertama.**

    Memindahkan peta pseudonim menjadi nilai ketiga pada `Area` memuaskan
    keduanya sambil membatalkan C-05 sepenuhnya. Bentuk yang sama dengan aturan
    VS-08 pada pemeriksa C-19.
    """
    rusak = AREA_BERSIH + '    PETA_PSEUDONIM = "peta_pseudonim"\n'
    temuan = periksa_peta_pseudonim(_pohon(tmp_path, area=rusak))
    assert temuan
    assert "peta_pseudonim" in str(temuan[0])


def test_area_yang_kehilangan_nilai_juga_ditemukan(tmp_path: Path) -> None:
    """Bukan hanya penambahan. Enum yang menyusut berarti `Area` berhenti
    mewujudkan D-14 Bagian 5.1, dan pemeriksa yang hanya melihat penambahan
    akan lulus atasnya."""
    rusak = AREA_BERSIH.replace('    KORPUS = "korpus"\n', "")
    assert periksa_peta_pseudonim(_pohon(tmp_path, area=rusak))


def test_enum_area_yang_dihapus_ditemukan(tmp_path: Path) -> None:
    rusak = AREA_BERSIH.replace("class Area(Enum):", "class Lain(Enum):")
    temuan = periksa_peta_pseudonim(_pohon(tmp_path, area=rusak))
    assert temuan
    assert "tidak ditemukan" in str(temuan[0])


def test_berkas_area_yang_hilang_ditemukan(tmp_path: Path) -> None:
    akar = _pohon(tmp_path)
    (akar / BERKAS_AREA).unlink()
    assert periksa_peta_pseudonim(akar)


def test_nilai_area_ditulis_pada_pemeriksa_bukan_dibaca_dari_enumnya() -> None:
    """Pemeriksa yang membaca daftar dari hal yang diperiksanya hanya
    membuktikan daftar sama dengan dirinya sendiri — dan akan tetap lulus
    ketika nilai ketiga ditambahkan ke keduanya."""
    isi = (AKAR / "perkakas" / "pemeriksa" / "peta_pseudonim.py").read_text(
        encoding="utf-8"
    )
    assert 'frozenset({"karantina", "korpus"})' in isi


# ---------------------------------------------------------------- pendaftaran


def test_c05_terdaftar_dengan_pemeriksa_bukan_fitur_pengunci() -> None:
    """C-05 berpindah dari `fitur_pengunci="012 telemetri"` menjadi `pemeriksa=`."""
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-05")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None


def test_c04_dan_c05_berpindah_pada_fitur_yang_berbeda() -> None:
    """Keduanya semula tertahan fitur 012, dan berpindah satu fitur terpisah.

    **C-05 pernyataan struktural** tentang di mana kunci berada, dan
    strukturnya dibangun fitur 022 — sehingga ia berpindah di sana, sebelum
    telemetri ada. **C-04 menuntut sebuah gerbang** yang belum ada sampai
    telemetri dibangun, sehingga ia menunggu fitur 012.

    Uji ini semula berbunyi "C-04 belum berpindah" dan benar ketika ditulis.
    Ia diganti — bukan dihapus — sebab pembedaannya tetap berlaku dan tetap
    menjelaskan mengapa dua pasal yang tertahan bersama tidak berpindah
    bersama.
    """
    for kode in ("C-04", "C-05"):
        pasal = next(p for p in DAFTAR_PASAL if p.kode == kode)
        assert pasal.pemeriksa is not None, kode
        assert pasal.fitur_pengunci is None, kode
