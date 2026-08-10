"""Uji pemeriksa patokan Label Studio — C-1 fitur 016, R-13.

**Diperiksa dengan cara yang berbeda dari Tesseract, dan sengaja.** Label
Studio bukan paket Python dan tidak terpasang pada lingkungan mana pun yang
menjalankan `make check`; memeriksa versi terpasangnya akan selalu
menghasilkan "belum dapat diperiksa", yaitu pemeriksa yang tidak pernah
memeriksa apa pun — pelajaran TA-01 pada bentuknya yang paling sia-sia.

Yang diperiksa: **sidik berkas contoh ekspornya.** Berkas itu satu-satunya
bukti tentang bentuk ekspor Label Studio yang dimiliki proyek ini, dan seluruh
uji `impor_ls` bersandar padanya. Bahan yang berubah tanpa catatan membuat uji
yang lulus berhenti membuktikan apa pun — dan perubahannya tidak akan terlihat
dari hasil ujinya, sebab ujinya ikut berubah bersamanya.
"""

import tomllib
from pathlib import Path

from perkakas.pemeriksa.ketergantungan_sistem import periksa_ketergantungan_sistem

AKAR = Path(__file__).resolve().parents[2]


def _salin(tmp: Path, ubah_berkas: bytes | None = None, ubah_sidik: str | None = None) -> Path:
    """Salinan akar yang cukup bagi pemeriksa: satu berkas patokan, satu bahan."""
    isi = (AKAR / "ketergantungan-disetujui.toml").read_text(encoding="utf-8")
    if ubah_sidik is not None:
        tercatat = tomllib.loads(isi)["sistem"]["label_studio"]["sidik"]
        isi = isi.replace(tercatat, ubah_sidik)
    (tmp / "ketergantungan-disetujui.toml").write_text(isi, encoding="utf-8")

    bahan = tmp / "tests" / "bahan"
    bahan.mkdir(parents=True)
    asli = AKAR / "tests" / "bahan" / "ekspor-label-studio-1.23.json"
    (bahan / asli.name).write_bytes(ubah_berkas if ubah_berkas is not None else asli.read_bytes())
    return tmp


def test_bahan_yang_tidak_berubah_lulus(tmp_path: Path) -> None:
    hasil = periksa_ketergantungan_sistem(_salin(tmp_path), versi_mesin=lambda: None)
    assert [t for t in hasil.temuan if "Label Studio" in t.pesan] == []


def test_bahan_yang_berubah_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini.**

    Satu bita diubah. Bahan uji yang berubah diam-diam adalah bahan yang
    kelak dipercayai tanpa seorang pun tahu asalnya.
    """
    asli = (AKAR / "tests" / "bahan" / "ekspor-label-studio-1.23.json").read_bytes()
    hasil = periksa_ketergantungan_sistem(
        _salin(tmp_path, ubah_berkas=asli + b" "), versi_mesin=lambda: None
    )
    assert any("sidik berkas contoh" in t.pesan for t in hasil.temuan)


def test_bahan_yang_hilang_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """Menghapus bahannya bukan cara sah meloloskan pemeriksa ini — bentuk
    yang sama dengan menghapus berkas patokan pada pemeriksa Tesseract."""
    isi = (AKAR / "ketergantungan-disetujui.toml").read_text(encoding="utf-8")
    (tmp_path / "ketergantungan-disetujui.toml").write_text(isi, encoding="utf-8")
    hasil = periksa_ketergantungan_sistem(tmp_path, versi_mesin=lambda: None)
    assert any("tidak ditemukan" in t.pesan for t in hasil.temuan)


def test_bagian_label_studio_yang_tidak_ada_tidak_menyalakan_apa_pun(tmp_path: Path) -> None:
    """Riwayat sebelum fitur 016 tidak memiliki bagian ini.

    Pemeriksa yang menyala atas ketiadaannya akan menyala atas seluruh riwayat
    itu, dan pemeriksa yang menyala atas hal yang benar akan dimatikan orang.
    """
    (tmp_path / "ketergantungan-disetujui.toml").write_text(
        'langsung = ["pydantic"]\nterkunci = {}\n', encoding="utf-8"
    )
    hasil = periksa_ketergantungan_sistem(tmp_path, versi_mesin=lambda: None)
    assert hasil.temuan == []


def test_sidik_tercatat_cocok_dengan_bahan_nyata() -> None:
    """Dijalankan atas repositori sungguhan, bukan atas salinan.

    Salinan hanya membuktikan pemeriksanya bekerja; ini membuktikan patokan
    yang tercatat memang cocok dengan bahan yang ada hari ini.
    """
    hasil = periksa_ketergantungan_sistem(AKAR, versi_mesin=lambda: None)
    assert [t for t in hasil.temuan if "Label Studio" in t.pesan] == []
