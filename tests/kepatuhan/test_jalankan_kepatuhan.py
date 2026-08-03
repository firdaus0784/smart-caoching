"""Uji pelaksana make compliance — R-15, R-16.

Tiga keadaan wajib, dan tidak ada keadaan keempat: LULUS, GAGAL, dan
BELUM-DAPAT-DIPERIKSA. Dua aturan membuatnya tidak dapat berbohong:

- kedua puluh pasal wajib muncul tepat sekali; daftar yang tidak lengkap
  menggagalkan pelaksana, bukan menghasilkan laporan yang lebih pendek
- keluaran kosong diperlakukan sebagai kegagalan — diam bukan lulus (R-16)

Seluruh uji memakai daftar suntikan. Daftar sebenarnya memuat pemeriksa C-11
yang menjalankan pytest sebagai subproses, dan memanggilnya dari dalam pytest
akan berulang tanpa henti.
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import Pasal
from perkakas.kepatuhan.jalankan import Keadaan, susun_laporan
from perkakas.pemeriksa.ast_aturan import Temuan


def _bersih(akar: Path) -> list[Temuan]:
    return []


def _kotor(akar: Path) -> list[Temuan]:
    return [Temuan(Path("x.py"), 1, "pelanggaran buatan")]


def _daftar_penuh(pemeriksa_c01: object = None) -> tuple[Pasal, ...]:
    """Dua puluh pasal; C-01 dapat diberi pemeriksa, sisanya menunggu."""
    butir: list[Pasal] = []
    for n in range(1, 21):
        kode = f"C-{n:02d}"
        if n == 1 and pemeriksa_c01 is not None:
            butir.append(Pasal(kode, "uji", pemeriksa=pemeriksa_c01))  # type: ignore[arg-type]
        else:
            butir.append(Pasal(kode, "uji", fitur_pengunci="00X"))
    return tuple(butir)


def test_dua_puluh_baris_dihasilkan(tmp_path: Path) -> None:
    laporan = susun_laporan(tmp_path, _daftar_penuh())
    assert len(laporan) == 20


def test_pasal_hilang_menggagalkan(tmp_path: Path) -> None:
    """Daftar tak lengkap menggagalkan pelaksana, bukan memperpendek laporan."""
    kurang = _daftar_penuh()[:-1]
    laporan = susun_laporan(tmp_path, kurang)
    gagal = [b for b in laporan if b.keadaan is Keadaan.GAGAL]
    assert gagal, "daftar tak lengkap lolos"
    assert any("C-20" in b.keterangan for b in gagal)


def test_daftar_kosong_menggagalkan(tmp_path: Path) -> None:
    """R-16 — diam bukan lulus."""
    laporan = susun_laporan(tmp_path, ())
    assert any(b.keadaan is Keadaan.GAGAL for b in laporan), "keluaran kosong lolos"


def test_pemeriksa_bersih_menghasilkan_lulus(tmp_path: Path) -> None:
    laporan = susun_laporan(tmp_path, _daftar_penuh(_bersih))
    baris = next(b for b in laporan if b.kode == "C-01")
    assert baris.keadaan is Keadaan.LULUS


def test_pemeriksa_kotor_menghasilkan_gagal(tmp_path: Path) -> None:
    laporan = susun_laporan(tmp_path, _daftar_penuh(_kotor))
    baris = next(b for b in laporan if b.kode == "C-01")
    assert baris.keadaan is Keadaan.GAGAL
    assert "pelanggaran buatan" in baris.keterangan


def test_pasal_menunggu_menyebut_fitur_penguncinya(tmp_path: Path) -> None:
    laporan = susun_laporan(tmp_path, _daftar_penuh())
    baris = next(b for b in laporan if b.kode == "C-05")
    assert baris.keadaan is Keadaan.BELUM
    assert "00X" in baris.keterangan


def test_tidak_ada_keadaan_keempat(tmp_path: Path) -> None:
    laporan = susun_laporan(tmp_path, _daftar_penuh(_bersih))
    assert {b.keadaan for b in laporan} <= {Keadaan.LULUS, Keadaan.GAGAL, Keadaan.BELUM}


def test_pemeriksa_yang_meledak_dihitung_gagal(tmp_path: Path) -> None:
    """Pemeriksa rusak tidak boleh dianggap lulus."""

    def _meledak(akar: Path) -> list[Temuan]:
        raise RuntimeError("pemeriksa rusak")

    laporan = susun_laporan(tmp_path, _daftar_penuh(_meledak))
    baris = next(b for b in laporan if b.kode == "C-01")
    assert baris.keadaan is Keadaan.GAGAL
    assert "rusak" in baris.keterangan
