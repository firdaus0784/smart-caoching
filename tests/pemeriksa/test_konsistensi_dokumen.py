"""Uji pemeriksa konsistensi dokumen — R-01 s.d. R-08, TK-45.

Register `docs/D00.md` Bagian 2 tertinggal pada tujuh dokumen tanpa satu pun
aturan dilanggar: D-00 Bagian 6 mewajibkan riwayat revisi diperbarui, dan itu
selalu dipenuhi. Kewajiban memperbarui register tidak pernah dinyatakan.

Pemeriksa ini memeriksa **bentuk**, bukan makna. Lima dari tujuh pertanyaan
pada D-00 Bagian 5 tetap di luar jangkauannya (RQ-03).
"""

from pathlib import Path

import pytest

from perkakas.pemeriksa.konsistensi_dokumen import baca_register, versi_kepala

REGISTER = """# D-00

## 2. Register Dokumen

| Kode | Dokumen | Versi | Status |
|---|---|---|---|
| D-00 | Kendali | 2.4 | Aktif |
| D-01 | BRD/PRD | 1.2 | Siap |

## 3. Lain
"""


def test_register_terbaca(tmp_path: Path) -> None:
    (tmp_path / "D00.md").write_text(REGISTER, encoding="utf-8")
    assert baca_register(tmp_path) == {"D-00": "2.4", "D-01": "1.2"}


def test_register_tak_terbaca_gagal_bukan_bersih(tmp_path: Path) -> None:
    """R-08 — pemeriksa yang tidak dapat membaca bahannya lalu melapor bersih
    adalah laporan palsu, dan laporan palsu menghentikan kewaspadaan."""
    (tmp_path / "D00.md").write_text("# D-00\n\nTanpa register.\n", encoding="utf-8")
    with pytest.raises(ValueError):
        baca_register(tmp_path)


def test_register_hilang_gagal(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        baca_register(tmp_path)


@pytest.mark.parametrize(
    ("baris", "diharapkan"),
    [
        ("| Versi | 0.1 |", "0.1"),
        ("| Versi | 2.4 |", "2.4"),
        ("| Versi dokumen | 1.2 — Penutupan celah keamanan |", "1.2"),
        ("| Versi | 0.5 — Penambahan ADR-12 dan ADR-13 |", "0.5"),
        ("| Versi | **2.1** |", "2.1"),
        ("| Versi | 0.3 — Koreksi kalender manajerial |", "0.3"),
    ],
)
def test_enam_bentuk_kepala_yang_dipakai_docs(tmp_path: Path, baris: str, diharapkan: str) -> None:
    """RQ-01 — keragaman bentuk kepala diuji, bukan diasumsikan.

    Pengurai yang terlalu ketat akan menyalak pada dokumen yang benar, dan
    pemeriksa yang menyalak pada keadaan sah akan dimatikan orang.
    """
    berkas = tmp_path / "Dxx.md"
    berkas.write_text(f"# Judul\n\n| Item | Keterangan |\n|---|---|\n{baris}\n", encoding="utf-8")
    assert versi_kepala(berkas) == diharapkan


def test_kepala_tanpa_versi_gagal(tmp_path: Path) -> None:
    berkas = tmp_path / "Dxx.md"
    berkas.write_text("# Judul\n\nTanpa baris versi.\n", encoding="utf-8")
    with pytest.raises(ValueError):
        versi_kepala(berkas)


def test_seluruh_dokumen_nyata_punya_versi_terbaca() -> None:
    """Enam bentuk di atas berasal dari `docs/` yang sebenarnya."""
    docs = Path(__file__).resolve().parents[2] / "docs"
    gagal = []
    for berkas in sorted(docs.glob("D*.md")):
        try:
            versi_kepala(berkas)
        except ValueError:
            gagal.append(berkas.name)
    assert not gagal, f"versi tidak terbaca pada: {gagal}"


# --- T-3 s.d. T-5: perbandingan -------------------------------------------

from perkakas.pemeriksa.konsistensi_dokumen import (  # noqa: E402
    periksa_konsistensi_dokumen,
    versi_riwayat_tertinggi,
)

DOKUMEN = """# D-99 · Contoh

| Item | Keterangan |
|---|---|
| Versi | 0.2 |

## 9. Riwayat Revisi

| Tanggal | Versi | Perubahan | Pemicu |
|---|---|---|---|
| 1 Agustus 2026 | 0.1 | Dibuat | — |
| 2 Agustus 2026 | 0.2 | Diperbarui | — |
"""

REGISTER_DUA = """# D-00

## 2. Register Dokumen

| Kode | Dokumen | Versi | Status |
|---|---|---|---|
| D-00 | Kendali | 1.0 | Aktif |
| D-99 | Contoh | 0.2 | Aktif |

## 3. Lain
"""

KEPALA_D00 = (
    "# D-00\n\n| Item | Keterangan |\n|---|---|\n| Versi | 1.0 |\n\n"
    "## 9. Riwayat Revisi\n\n| Tanggal | Versi | Perubahan |\n|---|---|---|\n"
    "| 1 Agustus 2026 | 1.0 | Dibuat |\n\n"
)


def _susun(tmp_path: Path, dokumen: str = DOKUMEN, register: str = REGISTER_DUA) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "D00.md").write_text(KEPALA_D00 + register.split("# D-00\n", 1)[1], encoding="utf-8")
    (docs / "D99.md").write_text(dokumen, encoding="utf-8")
    return tmp_path


def test_riwayat_tertinggi_terbaca(tmp_path: Path) -> None:
    berkas = tmp_path / "D99.md"
    berkas.write_text(DOKUMEN, encoding="utf-8")
    assert versi_riwayat_tertinggi(berkas) == "0.2"


def test_riwayat_urutan_menurun_tetap_terbaca(tmp_path: Path) -> None:
    """Urutan riwayat tidak seragam antardokumen. Yang diambil versi
    tertinggi, bukan baris pertama maupun terakhir — RQ-01."""
    terbalik = DOKUMEN.replace(
        "| 1 Agustus 2026 | 0.1 | Dibuat | — |\n| 2 Agustus 2026 | 0.2 | Diperbarui | — |",
        "| 2 Agustus 2026 | 0.2 | Diperbarui | — |\n| 1 Agustus 2026 | 0.1 | Dibuat | — |",
    )
    berkas = tmp_path / "D99.md"
    berkas.write_text(terbalik, encoding="utf-8")
    assert versi_riwayat_tertinggi(berkas) == "0.2"


def test_keadaan_selaras_bersih(tmp_path: Path) -> None:
    assert periksa_konsistensi_dokumen(_susun(tmp_path)) == []


def test_versi_kepala_menyimpang_dari_register_tertangkap(tmp_path: Path) -> None:
    """R-01 — inilah TK-45 yang sebenarnya terjadi."""
    akar = _susun(tmp_path, dokumen=DOKUMEN.replace("| Versi | 0.2 |", "| Versi | 0.3 |"))
    temuan = periksa_konsistensi_dokumen(akar)
    assert any("register" in t.pesan for t in temuan), f"penyimpangan register lolos: {temuan}"


def test_riwayat_tertinggal_dari_kepala_tertangkap(tmp_path: Path) -> None:
    """R-02 — versi dinaikkan tanpa riwayat revisinya ditulis."""
    kurang = DOKUMEN.replace("| 2 Agustus 2026 | 0.2 | Diperbarui | — |\n", "")
    akar = _susun(tmp_path, dokumen=kurang)
    temuan = periksa_konsistensi_dokumen(akar)
    assert any("riwayat" in t.pesan for t in temuan), f"riwayat tertinggal lolos: {temuan}"


def test_dokumen_terdaftar_tetapi_hilang_tertangkap(tmp_path: Path) -> None:
    """R-03 — register menunjuk berkas yang tidak ada."""
    akar = _susun(tmp_path)
    (akar / "docs" / "D99.md").unlink()
    temuan = periksa_konsistensi_dokumen(akar)
    assert any("tidak ada" in t.pesan for t in temuan)


def test_berkas_tidak_terdaftar_tertangkap(tmp_path: Path) -> None:
    """R-04 — dokumen ada tetapi register tidak mengetahuinya."""
    akar = _susun(tmp_path)
    (akar / "docs" / "D98.md").write_text(DOKUMEN.replace("D-99", "D-98"), encoding="utf-8")
    temuan = periksa_konsistensi_dokumen(akar)
    assert any("tidak terdaftar" in t.pesan for t in temuan)


def test_docs_nyata_bersih() -> None:
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_konsistensi_dokumen(akar)
    assert temuan == [], "; ".join(str(t) for t in temuan)


# --- T-6: kode dirujuk tanpa definisi -------------------------------------

from perkakas.pemeriksa.konsistensi_dokumen import periksa_kode_menggantung  # noqa: E402

DENGAN_DEFINISI = """# D-99

| Kode | Temuan | Tindakan |
|---|---|---|
| TK-01 | Sesuatu | Selesai |
| **TK-02** | Sesuatu lain | Selesai |

### ADR-01 · Contoh keputusan

Isi.
"""


def test_kode_terdefinisi_tidak_dianggap_menggantung(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "D99.md").write_text(
        DENGAN_DEFINISI + "\nMerujuk TK-01, TK-02, dan ADR-01.\n", encoding="utf-8"
    )
    assert periksa_kode_menggantung(tmp_path) == []


def test_kode_dirujuk_tanpa_definisi_tertangkap(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "D99.md").write_text(DENGAN_DEFINISI + "\nMerujuk TK-99.\n", encoding="utf-8")
    temuan = periksa_kode_menggantung(tmp_path)
    assert len(temuan) == 1, f"kode menggantung lolos: {temuan}"
    assert "TK-99" in temuan[0].pesan


def test_definisi_di_dokumen_lain_tetap_dikenali(tmp_path: Path) -> None:
    """Kutipan sejarah lintas dokumen sah — RQ-02."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "D99.md").write_text(DENGAN_DEFINISI, encoding="utf-8")
    (docs / "D98.md").write_text("# D-98\n\nPelajaran TK-01 berlaku di sini.\n", encoding="utf-8")
    assert periksa_kode_menggantung(tmp_path) == []


def test_rentang_kode_tidak_dianggap_menggantung(tmp_path: Path) -> None:
    """ "TK-01 s.d. TK-02" merujuk ujungnya, dan keduanya ada."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "D99.md").write_text(
        DENGAN_DEFINISI + "\nTemuan TK-01 s.d. TK-02 sudah selesai.\n", encoding="utf-8"
    )
    assert periksa_kode_menggantung(tmp_path) == []


def test_nomor_baris_dilaporkan(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "D99.md").write_text("# D-99\n\n\nMerujuk ADR-99.\n", encoding="utf-8")
    temuan = periksa_kode_menggantung(tmp_path)
    assert temuan[0].baris == 4


def test_docs_nyata_tanpa_kode_menggantung() -> None:
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_kode_menggantung(akar)
    assert temuan == [], "; ".join(str(t) for t in temuan[:8])
