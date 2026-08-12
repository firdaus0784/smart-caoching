"""Uji pemeriksa pemisahan indeks — B-2 fitur 006, R-06, R-07, C-02.

**Tugas ini yang menyusutkan tagihan kepatuhan.** `make compliance` berbunyi
8 lulus / 0 gagal / 12 belum pada fitur 015, 003, 016, dan 004 berturut-turut,
sedangkan D-12 menyatakan daftar itu "tagihan, bukan pengecualian — wajib
menyusut pada setiap fitur berikutnya".

Yang paling mudah keliru di sini bukan pemeriksanya melainkan **cara
menilainya berhasil**. Pemeriksa yang terdaftar tetapi tidak memeriksa apa pun
melapor LULUS dengan cara yang persis sama dengan pemeriksa yang benar — dan
tagihannya menyusut tanpa satu pun aturan ditegakkan. Karena itu berkas ini
menguji pemeriksanya terhadap pohon yang **sengaja dirusak**, bukan hanya
terhadap pohon yang bersih.
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.pemisahan_indeks import periksa_pemisahan_indeks

AKAR = Path(__file__).resolve().parents[2]

BERSIH = """
from src.penyimpanan.indeks import IndeksTujuan
from src.penyimpanan.kredensial import Kredensial

PENJAWABAN = Kredensial(
    nama="penjawaban",
    indeks=frozenset({IndeksTujuan.UTAMA, IndeksTujuan.METADATA}),
)
PEMANGGIL_LLM = Kredensial(
    nama="pemanggil_llm",
    indeks=frozenset({IndeksTujuan.UTAMA}),
)
"""


def _pohon(tmp_path: Path, isi: str, llm: str | None = None) -> Path:
    akar = tmp_path / "pohon"
    (akar / "src" / "penyimpanan").mkdir(parents=True)
    (akar / "src" / "penyimpanan" / "kredensial_baku.py").write_text(isi, encoding="utf-8")
    (akar / "src" / "llm").mkdir(parents=True)
    (akar / "src" / "llm" / "pembungkus.py").write_text(
        llm if llm is not None else '"""Pembungkus."""\n', encoding="utf-8"
    )
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_pemisahan_indeks(_pohon(tmp_path, BERSIH)) == []


def test_pemanggil_llm_yang_menjangkau_metadata_ditemukan(tmp_path: Path) -> None:
    """**Aturan 1, dan inti C-02.**"""
    rusak = BERSIH.replace(
        'nama="pemanggil_llm",\n    indeks=frozenset({IndeksTujuan.UTAMA}),',
        'nama="pemanggil_llm",\n    indeks=frozenset({IndeksTujuan.UTAMA, IndeksTujuan.METADATA}),',
    )
    temuan = periksa_pemisahan_indeks(_pohon(tmp_path, rusak))
    assert temuan
    assert "metadata" in temuan[0].pesan


def test_himpunan_indeks_yang_dihitung_dari_syarat_ditemukan(tmp_path: Path) -> None:
    """**Aturan 3.** Himpunan yang dihitung dari sebuah syarat adalah
    penyaringan yang menyamar sebagai pemisahan — persis yang C-02 kalimat
    kedua tolak.

    Bentuk yang dipakai sengaja **tidak menyebut METADATA sama sekali**,
    sehingga yang diuji benar-benar aturan bentuknya. Uji yang menyebut
    METADATA akan menyala karena aturan 1 dan meninggalkan aturan ini tanpa
    uji — pelajaran yang sama dengan pemeriksa C-03 fitur 002.
    """
    rusak = BERSIH.replace(
        "indeks=frozenset({IndeksTujuan.UTAMA}),",
        "indeks=frozenset({IndeksTujuan.UTAMA}) if not LUAS else frozenset(IndeksTujuan),",
    )
    temuan = periksa_pemisahan_indeks(_pohon(tmp_path, rusak))
    assert temuan
    assert "syarat" in temuan[0].pesan


def test_jalur_llm_yang_menyebut_metadata_ditemukan(tmp_path: Path) -> None:
    """**Aturan 2**, sengaja lebih luas daripada pelanggarannya.

    Penyebutan yang belum membaca apa pun tetap salah, sebab langkah
    berikutnya tinggal satu baris.
    """
    llm = '"""Pembungkus."""\nfrom x import IndeksTujuan\n\nP = IndeksTujuan.METADATA\n'
    temuan = periksa_pemisahan_indeks(_pohon(tmp_path, BERSIH, llm=llm))
    assert temuan
    assert "metadata" in temuan[0].pesan


def test_kredensial_baku_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Menghapus tempat pemisahan diwujudkan bukan cara sah meloloskan
    pemeriksa ini."""
    akar = tmp_path / "kosong"
    akar.mkdir()
    temuan = periksa_pemisahan_indeks(akar)
    assert temuan
    assert "tidak ditemukan" in temuan[0].pesan


def test_pemanggil_llm_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Kredensial yang dihapus tidak boleh terbaca sebagai pemisahan yang
    lulus — pemeriksa yang tidak menemukan bahannya lalu melapor bersih adalah
    laporan palsu (TA-01)."""
    rusak = BERSIH.replace("PEMANGGIL_LLM", "PEMANGGIL_MODEL")
    temuan = periksa_pemisahan_indeks(_pohon(tmp_path, rusak))
    assert temuan


def test_pohon_sesungguhnya_bersih() -> None:
    """Dijalankan pada pohon proyek, bukan hanya pada pohon tiruan.

    Pohon tiruan membuktikan pemeriksanya bekerja; ini membuktikan proyeknya
    memenuhi aturan hari ini.
    """
    assert periksa_pemisahan_indeks(AKAR) == []


def test_c02_berpindah_menjadi_terperiksa_mesin() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-06.**

    C-02 tidak lagi menunggu fitur; ia punya pemeriksa. Uji ini menangkap
    kemunduran — pasal yang dikembalikan menjadi `fitur_pengunci` karena
    pemeriksanya merepotkan.
    """
    c02 = next(p for p in DAFTAR_PASAL if p.kode == "C-02")
    assert c02.pemeriksa is not None
    assert not c02.fitur_pengunci


# Hitungan tagihan kepatuhan dahulu ditegakkan di sini. Ia pindah ke
# `tests/perkakas/test_tagihan_kepatuhan.py` pada fitur 007, ketika C-16
# menyusutkannya lagi dan angkanya ternyata tertulis pada dua berkas fitur yang
# berbeda. Buku besar yang tinggal di berkas satu fitur akan diperbarui oleh
# fitur berikutnya di berkasnya sendiri, dan sesudah beberapa fitur tidak ada
# yang tahu berkas mana yang berlaku.

