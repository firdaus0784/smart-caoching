"""Uji pemeriksa pemisahan penyimpanan — C-03, R-01, R-01a, ADR-06.

Pemeriksa ini yang memindahkan C-03 dari "belum dapat diperiksa" menjadi
pasal yang dijaga mesin. Karena itu ujinya wajib menyalakan pemeriksa pada
pelanggaran buatan, bukan sekadar memastikan ia berjalan bersih pada pohon
yang memang bersih — pemeriksa yang tidak memeriksa apa pun juga bersih.
"""

from pathlib import Path

from perkakas.pemeriksa.pemisahan_penyimpanan import periksa_pemisahan_penyimpanan

AKAR = Path(__file__).resolve().parents[2]

KREDENSIAL_BERSIH = """
from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial

PENJAWABAN = Kredensial(nama="penjawaban", baca=frozenset({Area.KORPUS}), tulis=frozenset(), indeks=frozenset())
PEMANGGIL_LLM = Kredensial(nama="llm", baca=frozenset({Area.KORPUS}), tulis=frozenset(), indeks=frozenset())
VERIFIKASI = Kredensial(
    nama="verifikasi",
    baca=frozenset({Area.KARANTINA, Area.KORPUS}),
    tulis=frozenset({Area.KORPUS}),
)
"""


def _pohon(tmp_path: Path, isi_kredensial: str, berkas_lain: dict[str, str] | None = None) -> Path:
    """Pohon sumber tiruan sekecil mungkin, berisi hanya yang diperiksa."""
    (tmp_path / "src" / "penyimpanan").mkdir(parents=True)
    (tmp_path / "src" / "penyimpanan" / "kredensial_baku.py").write_text(
        isi_kredensial, encoding="utf-8"
    )
    for nama, isi in (berkas_lain or {}).items():
        jalur = tmp_path / nama
        jalur.parent.mkdir(parents=True, exist_ok=True)
        jalur.write_text(isi, encoding="utf-8")
    return tmp_path


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_pemisahan_penyimpanan(_pohon(tmp_path, KREDENSIAL_BERSIH)) == []


def test_karantina_pada_himpunan_baca_penjawaban_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini** — ia bentuk pelanggaran C-03 yang paling
    mungkin terjadi dan paling sulit terlihat pada tinjauan kode."""
    rusak = KREDENSIAL_BERSIH.replace(
        'nama="penjawaban", baca=frozenset({Area.KORPUS})',
        'nama="penjawaban", baca=frozenset({Area.KORPUS, Area.KARANTINA})',
    )
    assert periksa_pemisahan_penyimpanan(_pohon(tmp_path, rusak))


def test_karantina_pada_himpunan_baca_pemanggil_llm_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """C-02 bergantung pada ini juga: yang tidak dapat dibaca tidak dapat
    masuk konteks yang dikirim ke model."""
    rusak = KREDENSIAL_BERSIH.replace(
        'nama="llm", baca=frozenset({Area.KORPUS})',
        'nama="llm", baca=frozenset({Area.KORPUS, Area.KARANTINA})',
    )
    assert periksa_pemisahan_penyimpanan(_pohon(tmp_path, rusak))


def test_verifikasi_boleh_membaca_karantina(tmp_path: Path) -> None:
    """Penjagaan yang menutup jalur verifikasi akan dimatikan orang.

    C-03 menyebut layanan RAG dan pelatihan, bukan seluruh layanan. Verifikator
    justru wajib membaca karantina; itu pekerjaannya.
    """
    assert periksa_pemisahan_penyimpanan(_pohon(tmp_path, KREDENSIAL_BERSIH)) == []


def test_kredensial_buatan_sendiri_pada_jalur_penjawaban_menyalakan_pemeriksa(
    tmp_path: Path,
) -> None:
    """Pintu belakang yang tidak menyentuh `kredensial_baku.py` sama sekali.

    Memeriksa hanya ketiga tetapan baku meninggalkan jalan yang lurus: buat
    kredensial sendiri di dalam `src/rag/` dan bacalah karantina dengannya.
    """
    akar = _pohon(
        tmp_path,
        KREDENSIAL_BERSIH,
        {
            "src/rag/pengambil.py": (
                "from src.penyimpanan.area import Area\n"
                "from src.penyimpanan.kredensial import Kredensial\n\n"
                "MILIKKU = Kredensial(\n"
                '    nama="milikku",\n'
                "    baca=frozenset({Area.KARANTINA}),\n"
                "    tulis=frozenset(),\n"
                ")\n"
            )
        },
    )
    assert periksa_pemisahan_penyimpanan(akar)


def test_penyebutan_karantina_pada_jalur_penjawaban_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """Jalur penjawaban tidak punya urusan menyebut karantina sama sekali.

    Aturan ini sengaja lebih luas daripada pelanggarannya: `src/rag/` yang
    menyebut `Area.KARANTINA` sudah salah bahkan ketika penyebutannya belum
    membaca apa pun, karena langkah berikutnya tinggal satu baris.
    """
    akar = _pohon(
        tmp_path,
        KREDENSIAL_BERSIH,
        {
            "src/rag/penyusun.py": (
                "from src.penyimpanan.area import Area\n\n"
                "def area_asal() -> Area:\n"
                "    return Area.KARANTINA\n"
            )
        },
    )
    assert periksa_pemisahan_penyimpanan(akar)


def test_ingest_boleh_menyebut_karantina(tmp_path: Path) -> None:
    """`src/ingest/` menulis karantina — itu memang tugasnya (ADR-06)."""
    akar = _pohon(
        tmp_path,
        KREDENSIAL_BERSIH,
        {
            "src/ingest/gerbang.py": (
                "from src.penyimpanan.area import Area\n\n"
                "def masuk() -> Area:\n"
                "    return Area.KARANTINA\n"
            )
        },
    )
    assert periksa_pemisahan_penyimpanan(akar) == []


def test_pemisahan_penanda_status_bukan_kredensial_ditolak(tmp_path: Path) -> None:
    """C-03 berbunyi "kredensial berbeda, bukan penanda status".

    Kredensial yang himpunan bacanya dihitung dari sebuah syarat adalah penanda
    status yang menyamar: ia satu kredensial yang berubah wujud, bukan dua.

    Bentuk yang dipakai di sini sengaja **tidak menyebut karantina sama
    sekali**, sehingga yang diuji benar-benar aturan bentuknya. Uji yang
    menyebut karantina akan menyala karena aturan lain dan meninggalkan aturan
    ini tanpa uji.
    """
    rusak = KREDENSIAL_BERSIH.replace(
        "baca=frozenset({Area.KORPUS}), tulis=frozenset(), indeks=frozenset())\nPEMANGGIL_LLM",
        "baca=frozenset({Area.KORPUS}) if not MODE_LUAS else frozenset(SELURUH_AREA), "
        "tulis=frozenset(), indeks=frozenset())\nPEMANGGIL_LLM",
    )
    assert periksa_pemisahan_penyimpanan(_pohon(tmp_path, rusak))


def test_pohon_sesungguhnya_bersih() -> None:
    """Dijalankan pada pohon proyek, bukan hanya pada pohon tiruan.

    Pemeriksa yang hanya diuji pada pohon buatan dapat lulus seluruhnya lalu
    gagal berjalan pada tata letak sebenarnya.
    """
    assert periksa_pemisahan_penyimpanan(AKAR) == []


def test_pemeriksa_menemukan_berkas_kredensial_yang_diperiksanya() -> None:
    """Pemeriksa yang tidak menemukan berkasnya melapor bersih.

    Ini kegagalan diam yang paling mungkin: satu berkas berpindah nama, dan
    C-03 kembali tidak dijaga tanpa satu uji pun berubah warna.
    """
    assert (AKAR / "src" / "penyimpanan" / "kredensial_baku.py").is_file()


def test_berkas_kredensial_hilang_menyalakan_pemeriksa(tmp_path: Path) -> None:
    """Dinyatakan sebagai perilaku, bukan hanya sebagai keberadaan berkas.

    Uji di atas menjaga tata letak hari ini; uji ini menjaga apa yang terjadi
    besok ketika tata letaknya berubah.
    """
    (tmp_path / "src" / "rag").mkdir(parents=True)
    assert periksa_pemisahan_penyimpanan(tmp_path)
