"""Uji pemeriksa penyetelan ambang — C-3 fitur 007, R-08, R-11, C-16.

**Tugas ini yang menyusutkan tagihan kepatuhan menjadi sepuluh** — separuh dari
dua puluh pasal.

Pelajaran fitur 006 berlaku sama di sini, dan lebih tajam: pemeriksa yang
terdaftar tetapi tidak memeriksa apa pun melapor LULUS dengan cara yang persis
sama dengan pemeriksa yang benar. Repositori ini **sudah** bersih terhadap
ketiga aturan C-16 pada hari pemeriksanya ditulis, sehingga menjalankannya di
sini tidak membuktikan satu pun aturan bekerja.

Karena itu setiap aturan diuji terhadap pohon yang **sengaja dirusak**, dan
setiap kerusakan dibuat menyerupai kekeliruan yang benar-benar mungkin terjadi
— bukan kekeliruan yang dibuat mudah ditangkap.
"""

from pathlib import Path

import pytest

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.ambang import periksa_ambang, rumah_tetapan

AKAR = Path(__file__).resolve().parents[2]

TETAPAN_BERSIH = '''"""Rumah tetapan."""

JUMLAH_KANDIDAT_PER_SUMBER = 20
"""Kandidat per sumber — docs/D07.md Bagian 4.4."""

TETAPAN_RRF_K = 60
"""Konstanta RRF — Cormack dkk. 2009, lewat D-07 Bagian 4.4."""
'''

MODUL_BIASA = '''"""Modul biasa."""

BATAS_HALAMAN = 50
'''


def _pohon(
    tmp_path: Path,
    *,
    tetapan: str = TETAPAN_BERSIH,
    modul: str = MODUL_BIASA,
) -> Path:
    """Pohon tiruan dengan satu rumah tetapan berisi dan satu modul biasa.

    Rumah tetapan **lain** diisi kosong, dan daftarnya dibaca dari
    `rumah_tetapan()` alih-alih disalin ke sini. Salinan daftar akan membuat
    setiap penambahan rumah tetapan menyalakan aturan 3 pada seluruh uji berkas
    ini — kegagalan yang benar isinya tetapi salah tempatnya, dan yang salah
    tempatnya diperbaiki dengan melonggarkan pemeriksa.
    """
    akar = tmp_path / "pohon"
    (akar / "src" / "rag" / "pengambilan").mkdir(parents=True)
    (akar / "src" / "rag" / "pengambilan" / "tetapan.py").write_text(tetapan, encoding="utf-8")
    (akar / "src" / "rag" / "pengambilan" / "kecukupan.py").write_text(modul, encoding="utf-8")
    for jalur in sorted(rumah_tetapan(akar)):
        if jalur.exists():
            continue
        jalur.parent.mkdir(parents=True, exist_ok=True)
        jalur.write_text('"""Kosong."""\n', encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_ambang(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    """Pernyataan yang **paling lemah** pada berkas ini, dan ia sengaja tidak
    berdiri sendiri: seluruh uji lain di bawahnya yang membuatnya berarti."""
    assert periksa_ambang(AKAR) == []


# ------------------------------------------------------------------- aturan 1


@pytest.mark.parametrize("nama", ["AMBANG_KECUKUPAN", "KECUKUPAN_AMBANG"])
def test_ambang_di_luar_rumah_tetapan_ditemukan(tmp_path: Path, nama: str) -> None:
    """**Aturan 1.** Kedua bentuk penamaan diuji — awalan dan akhiran."""
    rusak = MODUL_BIASA + f"\n{nama} = 0.62\n"
    temuan = periksa_ambang(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert any(nama in str(t) for t in temuan)


def test_ambang_pada_rumah_tetapan_tidak_ditemukan(tmp_path: Path) -> None:
    """Rumah tetapan **boleh** memuat ambang — itu gunanya. Yang dituntut di
    sana adalah asalnya tertulis, dan itu aturan 3."""
    tetapan = TETAPAN_BERSIH + '\nAMBANG_TINGGI = 0.62\n"""Ambang — D-07 BT-29."""\n'
    assert periksa_ambang(_pohon(tmp_path, tetapan=tetapan)) == []


def test_bilangan_bulat_bernama_ambang_tidak_ditemukan(tmp_path: Path) -> None:
    """Batas yang diakui: aturan 1 hanya menyapu pecahan.

    Ambang berupa bilangan bulat — jumlah minimum, panjang minimum — lolos, dan
    itu diterima. Menyapu seluruh bilangan bulat akan menandai indeks daftar
    dan panjang untai di mana-mana, lalu pemeriksanya dimatikan orang. Sapuan
    yang dimatikan tidak menjaga apa pun.
    """
    rusak = MODUL_BIASA + "\nAMBANG_JUMLAH = 3\n"
    assert periksa_ambang(_pohon(tmp_path, modul=rusak)) == []


# ------------------------------------------------------------------- aturan 2


def test_ambang_kecukupan_sebagai_tetapan_modul_ditemukan(tmp_path: Path) -> None:
    """**Aturan 2, dan bentuk yang paling mungkin terjadi.**

    Seseorang yang ingin "sekadar menjalankannya sekali" akan menuliskan
    tepat ini, dan ia akan berjalan.
    """
    rusak = (
        MODUL_BIASA
        + "\nAMBANG_BAKU = AmbangKecukupan(tinggi=0.03, menengah=0.02, kalibrasi=None)\n"
    )
    temuan = periksa_ambang(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert any("AmbangKecukupan" in str(t) for t in temuan)


def test_parameter_ambang_berbawaan_ditemukan(tmp_path: Path) -> None:
    """Bentuk kedua, dan lebih halus: bukan tetapan melainkan nilai bawaan.

    `kredensial.py` menamai akibatnya bagi kredensial, dan ia berlaku sama di
    sini — "parameter berbawaan `None` akan berubah menjadi 'tanpa kredensial
    berarti tanpa batas' pada pemanggilan pertama yang lupa mengisinya".
    """
    rusak = (
        MODUL_BIASA
        + "\ndef nilai(hasil: object, ambang: AmbangKecukupan = None) -> None:\n    pass\n"
    )
    temuan = periksa_ambang(_pohon(tmp_path, modul=rusak))
    assert temuan
    assert any("bawaan" in str(t) for t in temuan)


def test_parameter_ambang_bernama_wajib_berbawaan_ditemukan(tmp_path: Path) -> None:
    """Parameter khusus-kata-kunci diperiksa juga. Melewatkannya akan membuat
    satu tanda bintang cukup untuk meloloskan nilai bawaan."""
    rusak = (
        MODUL_BIASA
        + "\ndef nilai(hasil: object, *, ambang: AmbangKecukupan = None) -> None:\n    pass\n"
    )
    assert periksa_ambang(_pohon(tmp_path, modul=rusak))


def test_parameter_ambang_tanpa_bawaan_tidak_ditemukan(tmp_path: Path) -> None:
    bersih = MODUL_BIASA + "\ndef nilai(ambang: AmbangKecukupan) -> None:\n    pass\n"
    assert periksa_ambang(_pohon(tmp_path, modul=bersih)) == []


# ------------------------------------------------------------------- aturan 3


def test_tetapan_tanpa_uraian_ditemukan(tmp_path: Path) -> None:
    """**Aturan 3.** Tetapan tanpa uraian sama sekali."""
    rusak = TETAPAN_BERSIH + "\nAMBANG_DIAM = 0.42\n"
    temuan = periksa_ambang(_pohon(tmp_path, tetapan=rusak))
    assert any("AMBANG_DIAM" in str(t) for t in temuan)


def test_tetapan_beruraian_tanpa_sumber_ditemukan(tmp_path: Path) -> None:
    """Lebih halus, dan lebih mungkin: uraian **ada** tetapi tidak menyebut
    dokumen mana pun.

    "Nilai yang bekerja baik pada uji internal" adalah uraian yang lengkap,
    sopan, dan persis menandai angka yang disetel seseorang.
    """
    rusak = (
        TETAPAN_BERSIH
        + '\nAMBANG_SUNYI = 0.42\n"""Nilai yang bekerja baik pada uji internal."""\n'
    )
    temuan = periksa_ambang(_pohon(tmp_path, tetapan=rusak))
    assert any("AMBANG_SUNYI" in str(t) for t in temuan)


def test_tetapan_bersumber_makalah_diterima(tmp_path: Path) -> None:
    """Menyalin nilai dari sumber yang dokumen pengendalinya kutip adalah
    mengutip, bukan menyetel — KB-034 pertanyaan 2."""
    bersih = (
        TETAPAN_BERSIH + '\nBM25_K1 = 1.2\n"""Penjenuhan — Robertson & Zaragoza."""\n'
    )
    assert periksa_ambang(_pohon(tmp_path, tetapan=bersih)) == []


def test_rumah_tetapan_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Menghapus tempat angka dimiliki bukan cara sah meloloskan pemeriksa.

    Bentuk yang sama dengan pemeriksa C-02 yang menemukan `kredensial_baku.py`
    hilang.
    """
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    temuan = periksa_ambang(akar)
    assert len(temuan) == len(rumah_tetapan(akar))


def test_tetapan_pribadi_tidak_dituntut_beruraian(tmp_path: Path) -> None:
    """Nama berawalan garis bawah adalah rincian pelaksanaan, bukan angka yang
    dokumen miliki. Menuntutnya beruraian akan membuat pemeriksanya menandai
    hal-hal yang bukan urusannya, dan pemeriksa semacam itu dimatikan orang."""
    bersih = TETAPAN_BERSIH + "\n_PENYEBUT = 2.0\n"
    assert periksa_ambang(_pohon(tmp_path, tetapan=bersih)) == []


# ---------------------------------------------------------------- pendaftaran


def test_c16_terdaftar_dengan_pemeriksa_bukan_fitur_pengunci() -> None:
    """C-16 berpindah dari `fitur_pengunci="007 …"` menjadi `pemeriksa=`."""
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-16")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None


def test_rumah_tetapan_dimiliki_perkakas_bukan_uji() -> None:
    """Daftarnya lahir sebagai daftar putih uji pada fitur 003. Sejak fitur 007
    ia **aturan**, dan aturan tidak tinggal di `tests/` — uji yang mengimpornya
    dari sana akan berbeda dari pemeriksa yang menyalinnya."""
    from tests.nlp.test_ambang_kesepakatan import RUMAH_TETAPAN

    assert rumah_tetapan(AKAR) == RUMAH_TETAPAN
