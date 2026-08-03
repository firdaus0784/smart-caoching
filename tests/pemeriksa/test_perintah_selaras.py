"""Uji keselarasan bagian Perintah AGENTS.md dengan sasaran Makefile — R-03.

Perluasan B-4 yang disetujui: menghapus penanda placeholder tidak mencegah
kedua berkas menyimpang enam bulan kemudian. Penyimpangannya baru terasa
ketika agen menjalankan perintah yang tidak ada — persis kegagalan diam-diam
yang BACADULU peringatkan, dengan sebab yang berbeda.

Diperiksa dua arah. Perintah terdokumentasi yang tidak ada adalah kegagalan
yang jelas. Sasaran yang ada tetapi tidak terdokumentasi juga kegagalan: agen
membaca AGENTS.md untuk mengetahui apa yang harus dijalankan, dan sasaran yang
tidak disebut di sana tidak akan pernah dijalankan.
"""

from pathlib import Path

from perkakas.pemeriksa.perintah_selaras import periksa_perintah_selaras

AGENTS_BERSIH = """# AGENTS.md

## Perintah

```bash
make setup        # pasang
make check        # gerbang
```

## Batas
"""

MAKEFILE_BERSIH = """.PHONY: setup check

setup:
\t@echo a

check:
\t@echo b
"""


def _tulis(tmp_path: Path, agents: str, makefile: str) -> Path:
    (tmp_path / "AGENTS.md").write_text(agents, encoding="utf-8")
    (tmp_path / "Makefile").write_text(makefile, encoding="utf-8")
    return tmp_path


def test_selaras_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    akar = _tulis(tmp_path, AGENTS_BERSIH, MAKEFILE_BERSIH)
    assert periksa_perintah_selaras(akar) == []


def test_perintah_terdokumentasi_tanpa_sasaran_tertangkap(tmp_path: Path) -> None:
    agents = AGENTS_BERSIH.replace("make check", "make hantu")
    akar = _tulis(tmp_path, agents, MAKEFILE_BERSIH)
    temuan = periksa_perintah_selaras(akar)
    assert len(temuan) == 2, f"diharapkan dua arah penyimpangan: {temuan}"
    assert any("hantu" in t.pesan for t in temuan)


def test_sasaran_tanpa_dokumentasi_tertangkap(tmp_path: Path) -> None:
    makefile = MAKEFILE_BERSIH.replace(".PHONY: setup check", ".PHONY: setup check lint")
    makefile += "\nlint:\n\t@echo c\n"
    akar = _tulis(tmp_path, AGENTS_BERSIH, makefile)
    temuan = periksa_perintah_selaras(akar)
    assert len(temuan) == 1, f"sasaran tak terdokumentasi lolos: {temuan}"
    assert "lint" in temuan[0].pesan


def test_repositori_nyata_selaras() -> None:
    """Terhadap AGENTS.md dan Makefile yang sebenarnya."""
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_perintah_selaras(akar)
    assert temuan == [], "AGENTS.md dan Makefile menyimpang: " + "; ".join(
        str(t) for t in temuan
    )
