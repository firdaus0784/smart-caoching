"""Uji pemeriksa peringkat klaim — C-3 fitur 008, R-05, R-09, C-19.

Pelajaran fitur 006 dan 007 berlaku sama: pemeriksa yang terdaftar tetapi tidak
memeriksa apa pun melapor LULUS dengan cara yang persis sama dengan pemeriksa
yang benar. Repositori ini sudah bersih terhadap ketiga aturan pada hari
pemeriksanya ditulis.

Ketiga aturan **bertingkat**, dan urutan uji di bawah mengikuti tingkatannya:
aturan 3 menutup aturan 2, aturan 2 menutup aturan 1. Menguji satu tanpa dua
lainnya menghasilkan penjagaan yang dapat dilewati satu langkah ke samping.
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.peringkat_klaim import periksa_peringkat_klaim

AKAR = Path(__file__).resolve().parents[2]

VALIDATOR_BERSIH = '''"""Validator."""

from src.rag.validator.pemeriksaan import KodePemeriksaan

_MENUNGGU_FITUR_020 = {
    KodePemeriksaan.VS_03: "menunggu 019",
    KodePemeriksaan.VS_05: "menunggu BT-29",
    KodePemeriksaan.VS_07: "menunggu 017",
}


def _pemeriksaan_yang_dapat_dijalankan(keluaran, *, segmen):
    return {
        KodePemeriksaan.VS_01: None,
        KodePemeriksaan.VS_02: None,
        KodePemeriksaan.VS_04: None,
        KodePemeriksaan.VS_06: None,
        KodePemeriksaan.VS_08: None,
        KodePemeriksaan.VS_09: None,
    }


def validasi(keluaran, *, segmen):
    return JawabanTervalidasi()
'''

PEMERIKSAAN_BERSIH = '''"""Kode pemeriksaan."""

from enum import Enum


class KodePemeriksaan(Enum):
    VS_01 = "VS-01"
    VS_02 = "VS-02"
    VS_03 = "VS-03"
    VS_04 = "VS-04"
    VS_05 = "VS-05"
    VS_06 = "VS-06"
    VS_07 = "VS-07"
    VS_08 = "VS-08"
    VS_09 = "VS-09"
'''


def _pohon(
    tmp_path: Path,
    *,
    validator: str = VALIDATOR_BERSIH,
    pemeriksaan: str = PEMERIKSAAN_BERSIH,
    lain: str = '"""Modul lain."""\n',
) -> Path:
    akar = tmp_path / "pohon"
    (akar / "src" / "rag" / "validator").mkdir(parents=True)
    (akar / "src" / "rag" / "validator" / "validator.py").write_text(validator, encoding="utf-8")
    (akar / "src" / "rag" / "validator" / "pemeriksaan.py").write_text(
        pemeriksaan, encoding="utf-8"
    )
    (akar / "src" / "api").mkdir(parents=True)
    (akar / "src" / "api" / "tanya.py").write_text(lain, encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_peringkat_klaim(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    assert periksa_peringkat_klaim(AKAR) == []


# ------------------------------------------------------------------- aturan 1


def test_jawaban_tervalidasi_dibentuk_di_luar_validator_ditemukan(tmp_path: Path) -> None:
    """**Aturan 1, dan bentuk yang paling mungkin terjadi.**

    Fitur 009 menyusun tanggapan `/api/v1/tanya`. Seseorang yang ingin
    "sekadar menampilkannya dulu" akan menuliskan tepat ini pada `src/api/`,
    dan ia akan berjalan.
    """
    rusak = '"""Rute tanya."""\n\ndef tanya():\n    return JawabanTervalidasi()\n'
    temuan = periksa_peringkat_klaim(_pohon(tmp_path, lain=rusak))
    assert temuan
    assert any("JawabanTervalidasi" in str(t) for t in temuan)


# ------------------------------------------------------------------- aturan 2


def test_kode_yang_jatuh_dari_pemetaan_ditemukan(tmp_path: Path) -> None:
    """**Aturan 2.** Menjatuhkan VS-08 dari daftar jalannya melanggar C-19
    tanpa menyentuh satu baris logika pun, dan tidak satu uji perilaku pun
    gagal karenanya."""
    rusak = VALIDATOR_BERSIH.replace("        KodePemeriksaan.VS_08: None,\n", "")
    temuan = periksa_peringkat_klaim(_pohon(tmp_path, validator=rusak))
    assert any("VS-08" in str(t) for t in temuan)


def test_vs08_yang_dipindahkan_ke_daftar_menunggu_ditemukan(tmp_path: Path) -> None:
    """**Lubang yang aturan 2 sendiri buka, dan ditutup di sini.**

    Memindahkan VS-08 ke daftar yang menunggu model memuaskan kelengkapan: ia
    hadir pada hasil, berstatus belum-dapat-diperiksa, dan tidak pernah
    dijalankan. Bagi delapan kode lain itu keadaan yang jujur; bagi VS-08 itu
    pembatalan C-19 yang **terbaca seperti kejujuran**.
    """
    rusak = VALIDATOR_BERSIH.replace("        KodePemeriksaan.VS_08: None,\n", "").replace(
        '    KodePemeriksaan.VS_07: "menunggu 017",',
        '    KodePemeriksaan.VS_07: "menunggu 017",\n    KodePemeriksaan.VS_08: "menunggu 019",',
    )
    temuan = periksa_peringkat_klaim(_pohon(tmp_path, validator=rusak))
    assert any("VS-08" in str(t) for t in temuan)


def test_validator_yang_hilang_ditemukan(tmp_path: Path) -> None:
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    assert periksa_peringkat_klaim(akar)


# ------------------------------------------------------------------- aturan 3


def test_kode_yang_dihapus_dari_enum_ditemukan(tmp_path: Path) -> None:
    """**Aturan 3, yang menutup aturan 2.**

    Tanpa aturan ini, menghapus VS-08 dari enumnya sekaligus dari pemetaannya
    memuaskan aturan 2 — kelengkapan diukur terhadap enum yang sudah menyusut.
    """
    rusak_enum = PEMERIKSAAN_BERSIH.replace('    VS_08 = "VS-08"\n', "")
    rusak_val = VALIDATOR_BERSIH.replace("        KodePemeriksaan.VS_08: None,\n", "")
    temuan = periksa_peringkat_klaim(_pohon(tmp_path, validator=rusak_val, pemeriksaan=rusak_enum))
    assert any("VS-08" in str(t) for t in temuan)


def test_kode_tambahan_pada_enum_ditemukan(tmp_path: Path) -> None:
    """Enum yang bertambah nilai juga temuan. AG-04 melarang agen mengubah
    daftar nilai enum, dan menambah lebih mudah luput daripada menghapus."""
    rusak = PEMERIKSAAN_BERSIH.replace(
        '    VS_09 = "VS-09"\n', '    VS_09 = "VS-09"\n    VS_10 = "VS-10"\n'
    )
    assert periksa_peringkat_klaim(_pohon(tmp_path, pemeriksaan=rusak))


def test_enum_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Menghapus enumnya membuat aturan 2 tidak memeriksa apa pun."""
    assert periksa_peringkat_klaim(_pohon(tmp_path, pemeriksaan='"""Kosong."""\n'))


# ---------------------------------------------------------------- pendaftaran


def test_c19_terdaftar_dengan_pemeriksa() -> None:
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-19")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None


def test_c01_masih_tertahan_dan_alasannya_menyebut_fitur_020() -> None:
    """**Koreksi, bukan penundaan.**

    Alasan tunggu C-01 semula menyebut fitur 008. Verifikasi yang C-01 tuntut
    mencakup VS-03 — dukungan isi klaim, bukan sekadar keberadaan id — dan
    VS-03 menunggu model sematan serta BT-29.

    Menandai C-01 lulus tanpa VS-03 akan membuat MK-07 berarti "100% klaim
    menyebut id yang ada", persis angka yang D-07 PR-03a peringatkan.
    """
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-01")
    assert pasal.pemeriksa is None
    assert pasal.fitur_pengunci is not None
    assert "020" in pasal.fitur_pengunci
    assert "VS-03" in pasal.fitur_pengunci
