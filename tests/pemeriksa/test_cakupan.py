"""Uji penanda cakupan dan pemeriksa penurunan — R-17, C-11, NFR-16.

Dua hal berbeda diperiksa dan sengaja dipisah:

- **C-11** cakupan tidak turun — relatif terhadap penanda tersimpan
- **NFR-16** cakupan modul inti tidak di bawah 60% — mutlak

Sistem dapat memenuhi yang pertama sambil melanggar yang kedua selamanya bila
penandanya rendah sejak awal. Menggabungkan keduanya menyembunyikan hal itu.
"""

from pathlib import Path

import pytest

from perkakas.pemeriksa.cakupan import (
    LANTAI_NFR16,
    baca_penanda,
    periksa_cakupan,
    periksa_lantai,
    periksa_penurunan,
)

BERKAS = Path("penanda-cakupan.toml")


def test_naik_tidak_menghasilkan_temuan() -> None:
    assert periksa_penurunan(penanda=70.0, sekarang=75.0, berkas=BERKAS) == []


def test_sama_tidak_menghasilkan_temuan() -> None:
    assert periksa_penurunan(penanda=70.0, sekarang=70.0, berkas=BERKAS) == []


def test_turun_tertangkap() -> None:
    temuan = periksa_penurunan(penanda=70.0, sekarang=69.9, berkas=BERKAS)
    assert len(temuan) == 1, "penurunan lolos"
    assert "70.0" in temuan[0].pesan and "69.9" in temuan[0].pesan


def test_penanda_hilang_adalah_kegagalan(tmp_path: Path) -> None:
    """Menghapus penanda bukan cara sah meloloskan pemeriksa."""
    with pytest.raises(FileNotFoundError):
        baca_penanda(tmp_path)


def test_penanda_terbaca(tmp_path: Path) -> None:
    (tmp_path / "penanda-cakupan.toml").write_text(
        "tercatat = 61.5\npernyataan = 120\n", encoding="utf-8"
    )
    assert baca_penanda(tmp_path) == 61.5


def test_lantai_nfr16_tidak_berlaku_bila_belum_ada_pernyataan() -> None:
    """Pada fitur 001 src/ nyaris kosong; lantai belum bermakna."""
    assert periksa_lantai(sekarang=0.0, pernyataan=0, berkas=BERKAS) == []


def test_lantai_nfr16_ditegakkan_bila_sudah_ada_pernyataan() -> None:
    temuan = periksa_lantai(sekarang=45.0, pernyataan=200, berkas=BERKAS)
    assert len(temuan) == 1, "cakupan di bawah lantai lolos"
    assert str(LANTAI_NFR16) in temuan[0].pesan


def test_lantai_nfr16_lolos_di_atas_ambang() -> None:
    assert periksa_lantai(sekarang=60.0, pernyataan=200, berkas=BERKAS) == []


# ----------------------------------- `periksa_cakupan` · gabungan kedua aturan


def test_penanda_hilang_menjadi_temuan_bukan_pengecualian(tmp_path: Path) -> None:
    """**Uji yang seharusnya ada sejak fitur 001.**

    `periksa_cakupan` adalah yang V-01 dan pasal C-11 sungguh panggil; kedua
    aturan di atas hanya bagiannya. Sampai hari ini ia tidak memiliki satu uji
    pun — ditemukan lewat sapuan atas seluruh pemeriksa (KB-057).

    Yang diuji cabang paling awalnya: penanda yang hilang wajib menjadi
    **temuan**, bukan pengecualian. `baca_penanda` melempar `FileNotFoundError`,
    dan pengecualian yang lolos ke atas menghentikan `make check` dengan jejak
    tumpukan alih-alih laporan gerbang — pembacanya kemudian melihat perkakas
    yang rusak, bukan penanda yang hilang, dan yang paling mungkin ia lakukan
    adalah melewati gerbangnya.
    """
    temuan = periksa_cakupan(tmp_path)
    assert len(temuan) == 1
    assert "penanda-cakupan.toml" in str(temuan[0].berkas)


def test_jalur_bahagia_sengaja_tidak_diuji_di_sini() -> None:
    """**Batas yang dinyatakan, bukan yang dilewatkan.**

    `periksa_cakupan` memanggil `ukur_cakupan`, yang menjalankan seluruh
    rangkaian uji lewat subproses. Memanggilnya dari dalam rangkaian uji berarti
    rangkaian menjalankan dirinya sendiri — dan uji yang berbiaya demikian akan
    dimatikan orang.

    Yang menjaga jalur itu tetap benar adalah `make check` sendiri, yang
    memanggilnya tiap kali. Dinyatakan di sini agar ketiadaannya terbaca sebagai
    keputusan, bukan sebagai kelalaian yang berikutnya.
    """
    naskah = (
        Path(__file__).resolve().parents[2] / "perkakas" / "pemeriksa" / "cakupan.py"
    ).read_text(encoding="utf-8")
    assert "subprocess.run" in naskah, "bila pengukurannya tidak lagi subproses, uji ini usang"
