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
