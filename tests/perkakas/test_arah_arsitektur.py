"""Uji pemeriksa arah arsitektur — fitur 009, V-03, `AGENTS.md`.

**Pemeriksa ini lahir dari tiga kekeliruan berturut-turut**, dan menemukan yang
ketiga sendiri pada menit pertama ia dijalankan.

- Fitur 007: tepi `rag → nlp` dipakai tanpa pernah dituliskan.
- Fitur 008: tepi `ingest → llm` ada **sejak fitur 002** dengan cara yang sama.
- Fitur 009: `src/logbook/` diimpor **lima lapisan** tanpa pernah tercatat pada
  daftar arsitektur sama sekali — dan ia modul yang menegakkan C-09.

Ketiganya sah setelah ditinjau. Itu yang membuatnya mengkhawatirkan: yang lolos
bukan pelanggaran melainkan **keputusan arsitektur yang tidak pernah diambil
siapa pun**, dan tidak satu gerbang pun menyala.
"""

from pathlib import Path

from perkakas.pemeriksa.arah_arsitektur import baca_arah, periksa_arah_arsitektur

AKAR = Path(__file__).resolve().parents[2]

AGEN = """# AGENTS.md

Aturan arah: `api` boleh memanggil `nlp`, `rag`. Tidak sebaliknya.
`rag` boleh memanggil `nlp`, satu jurusan.
`src/kamus/` boleh diimpor siapa pun dan tidak mengimpor apa pun.
Semua akses penyimpanan lewat `src/penyimpanan/`. Tanpa pengecualian.
"""


def _pohon(tmp_path: Path, berkas: dict[str, str], agen: str = AGEN) -> Path:
    akar = tmp_path / "pohon"
    akar.mkdir()
    (akar / "AGENTS.md").write_text(agen, encoding="utf-8")
    for jalur, isi in berkas.items():
        p = akar / jalur
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(isi, encoding="utf-8")
    return akar


def test_repositori_ini_bersih() -> None:
    """Ia **tidak** bersih ketika pemeriksa ini pertama dijalankan: sembilan
    temuan pada lima lapisan, seluruhnya menunjuk `src/logbook/`."""
    assert periksa_arah_arsitektur(AKAR) == []


def test_arah_dibaca_dari_agents_md() -> None:
    tepi, terbuka = baca_arah(AGEN)
    assert tepi == {"api": frozenset({"nlp", "rag"}), "rag": frozenset({"nlp"})}
    assert terbuka == frozenset({"kamus", "penyimpanan"})


def test_tepi_yang_tertulis_diterima(tmp_path: Path) -> None:
    akar = _pohon(
        tmp_path,
        {"src/rag/cari.py": '"""Cari."""\nfrom src.nlp.praproses import tokenkan\n'},
    )
    assert periksa_arah_arsitektur(akar) == []


def test_tepi_yang_tidak_tertulis_ditemukan(tmp_path: Path) -> None:
    """**Bentuk ketiga temuan sungguhan**: impor yang bekerja, tidak melanggar
    apa pun, dan tidak dijelaskan dokumen mana pun."""
    akar = _pohon(
        tmp_path,
        {"src/nlp/praproses.py": '"""Praproses."""\nfrom src.rag.cari import cari\n'},
    )
    temuan = periksa_arah_arsitektur(akar)
    assert temuan
    assert "nlp → rag" in str(temuan[0])


def test_arah_sebaliknya_tetap_ditemukan(tmp_path: Path) -> None:
    """`rag → nlp` tertulis; `nlp → rag` tidak. Pemeriksa yang membaca tepi
    sebagai dua arah akan meloloskannya, dan `AGENTS.md` menyatakan arah
    sebaliknya terlarang dengan alasan tersendiri."""
    akar = _pohon(
        tmp_path,
        {"src/nlp/a.py": '"""A."""\nfrom src.rag.b import b\n'},
    )
    assert periksa_arah_arsitektur(akar)


def test_lapisan_terbuka_boleh_diimpor_siapa_pun(tmp_path: Path) -> None:
    akar = _pohon(
        tmp_path,
        {
            "src/ingest/a.py": '"""A."""\nfrom src.kamus.segmen import IndeksTujuan\n',
            "src/nlp/b.py": '"""B."""\nfrom src.penyimpanan.dasar import Penyimpan\n',
        },
    )
    assert periksa_arah_arsitektur(akar) == []


def test_impor_di_dalam_satu_lapisan_tidak_diperiksa(tmp_path: Path) -> None:
    """`AGENTS.md` mengatur antar lapisan puncak, bukan susunan di dalamnya.

    Pemeriksa yang ikut mengatur susunan dalam akan menandai `rag/validator`
    yang mengimpor `rag/pengambilan` — pekerjaan sah yang tidak diatur dokumen
    mana pun, dan penjagaan yang menandai pekerjaan sah akan dimatikan orang.
    """
    akar = _pohon(
        tmp_path,
        {"src/rag/validator/v.py": '"""V."""\nfrom src.rag.pengambilan.bm25 import cari\n'},
    )
    assert periksa_arah_arsitektur(akar) == []


def test_agents_md_yang_hilang_ditemukan(tmp_path: Path) -> None:
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    assert periksa_arah_arsitektur(akar)


def test_agents_md_tanpa_satu_pun_tepi_ditemukan(tmp_path: Path) -> None:
    """**Pemeriksa yang tidak menemukan aturan tidak memeriksa apa pun.**

    Tanpa uji ini, menghapus bagian Arsitektur dari `AGENTS.md` akan membuat
    pemeriksanya melaporkan bersih atas pohon apa pun — TA-01 pada perkakas
    yang dibangun justru untuk menutup TA-01.
    """
    akar = _pohon(tmp_path, {"src/nlp/a.py": '"""A."""\n'}, agen="# AGENTS.md\n\nKosong.\n")
    temuan = periksa_arah_arsitektur(akar)
    assert temuan
    assert "tidak memeriksa apa pun" in str(temuan[0])


def test_berkas_di_luar_src_tidak_diperiksa(tmp_path: Path) -> None:
    akar = _pohon(tmp_path, {"src/nlp/a.py": '"""A."""\n'})
    (akar / "perkakas").mkdir()
    (akar / "perkakas" / "alat.py").write_text(
        '"""Alat."""\nfrom src.rag.b import b\n', encoding="utf-8"
    )
    assert periksa_arah_arsitektur(akar) == []
