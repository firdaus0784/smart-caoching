"""Uji pemeriksa penanda placeholder pada AGENTS.md — R-03.

BACADULU memperingatkan secara khusus: "Placeholder yang dibiarkan lebih buruk
daripada tidak ada bagian itu sama sekali — agen akan menjalankannya dan gagal
diam-diam." R-03 mengubah peringatan itu menjadi kegagalan pembangunan.
"""

from pathlib import Path

from perkakas.pemeriksa.placeholder import periksa_placeholder

BERSIH = """# AGENTS.md

## Perintah

```bash
make setup
make check
```

## Batas

- sesuatu
"""


def _tulis(tmp_path: Path, isi: str) -> Path:
    berkas = tmp_path / "AGENTS.md"
    berkas.write_text(isi, encoding="utf-8")
    return berkas


def test_bagian_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_placeholder(_tulis(tmp_path, BERSIH)) == []


def test_komentar_tim_tertangkap(tmp_path: Path) -> None:
    isi = BERSIH.replace(
        "## Perintah\n",
        "## Perintah\n\n<!-- TIM: isi setelah tumpukan terpasang. -->\n",
    )
    temuan = periksa_placeholder(_tulis(tmp_path, isi))
    assert len(temuan) == 1, f"penanda TIM lolos: {temuan}"
    assert temuan[0].baris == 5


def test_todo_tertangkap(tmp_path: Path) -> None:
    isi = BERSIH.replace("make setup\n", "make setup  # TODO lengkapi\n")
    assert len(periksa_placeholder(_tulis(tmp_path, isi))) == 1


def test_fixme_dan_xxx_tertangkap(tmp_path: Path) -> None:
    isi = BERSIH.replace("make setup\n", "FIXME\nXXX\n")
    assert len(periksa_placeholder(_tulis(tmp_path, isi))) == 2


def test_penanda_di_bagian_lain_tidak_dihitung(tmp_path: Path) -> None:
    """R-03 menyebut bagian Perintah. Bagian lain bukan urusan aturan ini."""
    isi = BERSIH.replace("- sesuatu\n", "- sesuatu <!-- TIM: nanti -->\n")
    assert periksa_placeholder(_tulis(tmp_path, isi)) == []


def test_bagian_perintah_hilang_adalah_kegagalan(tmp_path: Path) -> None:
    """Menghapus bagiannya bukan cara sah untuk meloloskan pemeriksa."""
    isi = "# AGENTS.md\n\n## Batas\n\n- sesuatu\n"
    temuan = periksa_placeholder(_tulis(tmp_path, isi))
    assert len(temuan) == 1
    assert "tidak ditemukan" in temuan[0].pesan.lower()


def test_bagian_perintah_kosong_adalah_kegagalan(tmp_path: Path) -> None:
    isi = "# AGENTS.md\n\n## Perintah\n\n## Batas\n\n- sesuatu\n"
    temuan = periksa_placeholder(_tulis(tmp_path, isi))
    assert len(temuan) == 1, f"bagian kosong lolos: {temuan}"
