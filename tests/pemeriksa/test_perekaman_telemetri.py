"""Uji pemeriksa perekaman telemetri — C-2 fitur 012, C-04.

Diuji terhadap **pohon yang sengaja dirusak**, masing-masing aturan terpisah.
Pemeriksa yang hanya dijalankan atas pohon yang sehat membuktikan ia tidak
mengeluh; ia tidak membuktikan ia menemukan apa pun (TA-01).
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.perekaman_telemetri import (
    BERKAS_GERBANG,
    BERKAS_PERISTIWA,
    periksa_perekaman_telemetri,
)

AKAR = Path(__file__).resolve().parents[2]

PERISTIWA_BERSIH = '''"""Peristiwa tiruan."""

from pydantic import BaseModel


class Peristiwa(BaseModel):
    pseudonim: str
    jenis: str
'''

GERBANG_BERSIH = '''"""Gerbang tiruan."""

from src.pengguna.persetujuan import KeadaanPersetujuan
from src.telemetri.peristiwa import Peristiwa


def rekam(*, keadaan: KeadaanPersetujuan, pseudonim: str) -> Peristiwa | None:
    if not keadaan.boleh_merekam:
        return None
    return Peristiwa(pseudonim=pseudonim, jenis="x")
'''

MODUL_BIASA = '''"""Modul tiruan."""


def layani() -> None:
    return None
'''


def _pohon(
    tmp_path: Path,
    *,
    peristiwa: str = PERISTIWA_BERSIH,
    gerbang: str = GERBANG_BERSIH,
    modul: str = MODUL_BIASA,
) -> Path:
    akar = tmp_path / "pohon"
    (akar / BERKAS_GERBANG).parent.mkdir(parents=True)
    (akar / BERKAS_PERISTIWA).write_text(peristiwa, encoding="utf-8")
    (akar / BERKAS_GERBANG).write_text(gerbang, encoding="utf-8")
    (akar / "src" / "api").mkdir(parents=True)
    (akar / "src" / "api" / "layanan.py").write_text(modul, encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_perekaman_telemetri(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    """Pernyataan yang **paling lemah** pada berkas ini; uji lain di bawahnya
    yang membuatnya berarti."""
    assert periksa_perekaman_telemetri(AKAR) == []


# ------------------------------------------------------------------- aturan 1


def test_pembentukan_di_luar_gerbang_ditemukan(tmp_path: Path) -> None:
    """**Aturan 1.** Peristiwa yang dapat dibentuk di mana saja adalah
    peristiwa yang dapat terekam tanpa persetujuan."""
    rusak = MODUL_BIASA + '\n\ndef curang() -> None:\n    Peristiwa(pseudonim="P", jenis="x")\n'
    temuan = periksa_perekaman_telemetri(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert "di luar gerbang" in str(temuan[0])


def test_pembentukan_pada_gerbang_tidak_ditemukan(tmp_path: Path) -> None:
    assert periksa_perekaman_telemetri(_pohon(tmp_path)) == []


# ------------------------------------------------------------------- aturan 2


def test_bidang_beridentitas_ditemukan(tmp_path: Path) -> None:
    """**Aturan 2.** FR-J02 menulis "id pengguna **terpseudonim**"; bidang
    beridentitas membuat pseudonimisasi menjadi kebiasaan pemanggil alih-alih
    sifat tipenya."""
    rusak = PERISTIWA_BERSIH + "    id_pengguna: str\n"
    temuan = periksa_perekaman_telemetri(_pohon(tmp_path, peristiwa=rusak))
    assert temuan
    assert "id_pengguna" in str(temuan[0])


def test_tipe_peristiwa_yang_dihapus_ditemukan(tmp_path: Path) -> None:
    rusak = PERISTIWA_BERSIH.replace("class Peristiwa(BaseModel):", "class Lain(BaseModel):")
    assert periksa_perekaman_telemetri(_pohon(tmp_path, peristiwa=rusak))


# ------------------------------------------------------------------- aturan 3


def test_parameter_keadaan_berbawaan_ditemukan(tmp_path: Path) -> None:
    """**Aturan 3, dan ia menutup dua yang pertama.**

    Gerbang yang parameternya berbawaan memuaskan aturan 1 dan 2 sambil
    membatalkan C-04 pada setiap pemanggilan yang lupa mengisinya — dan tidak
    satu uji perilaku pun gagal karenanya, sebab uji selalu mengisinya.
    """
    rusak = GERBANG_BERSIH.replace(
        "keadaan: KeadaanPersetujuan,",
        "keadaan: KeadaanPersetujuan = KeadaanPersetujuan.DIBERIKAN,",
    )
    temuan = periksa_perekaman_telemetri(_pohon(tmp_path, gerbang=rusak))
    assert temuan
    assert "nilai bawaan" in str(temuan[0])


def test_parameter_keadaan_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Gerbang yang tidak menanyakan persetujuan bukan gerbang."""
    rusak = GERBANG_BERSIH.replace(
        "*, keadaan: KeadaanPersetujuan, pseudonim: str", "*, pseudonim: str"
    )
    rusak = rusak.replace("    if not keadaan.boleh_merekam:\n        return None\n", "")
    temuan = periksa_perekaman_telemetri(_pohon(tmp_path, gerbang=rusak))
    assert temuan
    assert "tidak menerima parameter" in str(temuan[0])


def test_keadaan_berupa_boolean_ditemukan(tmp_path: Path) -> None:
    """Bendera boolean dapat diisi `True` oleh pemanggil yang lelah, sedangkan
    keadaan menuntut dibaca dari catatan persetujuan."""
    rusak = GERBANG_BERSIH.replace("keadaan: KeadaanPersetujuan,", "keadaan: bool,")
    rusak = rusak.replace("if not keadaan.boleh_merekam:", "if not keadaan:")
    temuan = periksa_perekaman_telemetri(_pohon(tmp_path, gerbang=rusak))
    assert temuan
    assert "bendera boolean" in str(temuan[0])


def test_gerbang_yang_dihapus_ditemukan(tmp_path: Path) -> None:
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    temuan = periksa_perekaman_telemetri(akar)
    assert temuan
    assert any("tidak ditemukan" in str(t) for t in temuan)


def test_fungsi_rekam_yang_hilang_ditemukan(tmp_path: Path) -> None:
    rusak = GERBANG_BERSIH.replace("def rekam(", "def simpan(")
    temuan = periksa_perekaman_telemetri(_pohon(tmp_path, gerbang=rusak))
    assert temuan
    assert "rekam()" in str(temuan[0])


# ---------------------------------------------------------------- pendaftaran


def test_c04_terdaftar_dengan_pemeriksa_bukan_fitur_pengunci() -> None:
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-04")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None


def test_c04_pasal_terakhir_yang_berpindah_bersama_fiturnya() -> None:
    """C-04 adalah pasal terakhir yang berpindah **karena sebuah fitur
    dibangun**. Sesudahnya tinggal C-10, yang berpindah tanpa fitur baru —
    kodenya sudah ada sejak fitur 003, hanya pemeriksanya yang belum.

    Uji ini semula berbunyi "empat pasal tersisa" dan benar ketika ditulis.
    Ia diganti, bukan dihapus: yang tetap berlaku adalah pembedaan antara
    pasal yang menunggu kode dan pasal yang hanya menunggu pemeriksanya.
    """
    belum = {p.kode for p in DAFTAR_PASAL if p.pemeriksa is None}
    assert belum == {"C-01", "C-13", "C-14"}
    assert next(p for p in DAFTAR_PASAL if p.kode == "C-10").pemeriksa is not None
