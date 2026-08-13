"""Uji pemeriksa rute terdaftar — A-2 fitur 021, R-02, R-03, AG-02.

## Yang diuji bukan bahwa pemeriksanya berjalan

Yang diuji: ia **menyala** pada pohon yang dirusak, dan **diam** pada pohon
yang sehat. Keduanya perlu. Pemeriksa yang diam pada pelanggaran yang persis
dinamainya lebih buruk daripada tidak ada — ia memberi rasa aman. Pemeriksa
yang berteriak pada pohon bersih akan dimatikan orang.

Pelajaran keduanya berasal dari pemeriksa C-10, yang mengalami keduanya dalam
satu sore (KB-050).
"""

from pathlib import Path

from perkakas.pemeriksa.rute_terdaftar import periksa_rute_terdaftar

AKAR = Path(__file__).resolve().parents[2]


def _pohon(tmp_path: Path, nama: str, isi: str) -> Path:
    modul = tmp_path / "src" / "api"
    modul.mkdir(parents=True, exist_ok=True)
    (modul / nama).write_text(isi, encoding="utf-8")
    return tmp_path


# ------------------------------------------------------------- pohon sungguhan


def test_pohon_sungguhan_bersih() -> None:
    """**Uji yang menjaga pemeriksa ini tetap dipakai.**

    Pemeriksa yang berteriak pada pohon yang sehat akan dimatikan, dan yang
    dimatikan tidak menjaga apa pun.
    """
    assert periksa_rute_terdaftar(AKAR) == []


# ---------------------------------------------------------------- aturan tunggal


def test_jalur_di_luar_berkas_peran_ditolak(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini.**

    Rute yang dituliskan di modul lain tidak pernah masuk `PETA_RUTE`, sehingga
    kendali peran tidak pernah dipanggil baginya — dan kedua arah uji
    `PETA_RUTE` tetap lulus karena tabelnya memang masih cocok dengan dokumen.
    """
    akar = _pohon(tmp_path, "adaptor.py", 'JALUR = "/api/v1/tanya"\n')
    temuan = periksa_rute_terdaftar(akar)
    assert len(temuan) == 1
    assert "kendali peran" in temuan[0].pesan


def test_berkas_peran_sendiri_dilewati(tmp_path: Path) -> None:
    """`peran.py` adalah tempat jalur memang tinggal. Pemeriksa yang menolaknya
    di sana menolak satu-satunya tempat yang benar."""
    akar = _pohon(tmp_path, "peran.py", 'JALUR = "/api/v1/tanya"\n')
    assert periksa_rute_terdaftar(akar) == []


def test_uraian_modul_boleh_menyebut_jalur(tmp_path: Path) -> None:
    """Melarang jalur pada docstring berarti melarang menjelaskan rute pada
    dokumentasinya sendiri — dan aturan yang melarang menjelaskan akan
    dimatikan orang."""
    akar = _pohon(tmp_path, "adaptor.py", '"""Penangan /api/v1/tanya."""\n')
    assert periksa_rute_terdaftar(akar) == []


def test_docstring_fungsi_juga_dilewati(tmp_path: Path) -> None:
    akar = _pohon(
        tmp_path,
        "adaptor.py",
        'def tangani() -> None:\n    """Melayani /api/v1/tanya."""\n',
    )
    assert periksa_rute_terdaftar(akar) == []


def test_untai_bukan_jalur_api_tidak_terjaring(tmp_path: Path) -> None:
    """Awalan versi ikut pada polanya justru agar untai lain yang kebetulan
    dimulai garis miring tidak menjadi temuan palsu."""
    akar = _pohon(
        tmp_path,
        "adaptor.py",
        'BERKAS = "/etc/hosts"\nAWALAN = "/api/"\nSATU = "/apiv1/tanya"\n',
    )
    assert periksa_rute_terdaftar(akar) == []


def test_beberapa_jalur_dilaporkan_seluruhnya(tmp_path: Path) -> None:
    """Laporan yang berhenti pada temuan pertama membuat pembacanya mengira
    tinggal satu yang perlu diperbaiki."""
    akar = _pohon(
        tmp_path,
        "adaptor.py",
        'A = "/api/v1/tanya"\nB = "/api/v1/beranda"\n',
    )
    assert len(periksa_rute_terdaftar(akar)) == 2


def test_berkas_bergalat_sintaksis_tidak_menggagalkan_pemeriksa(tmp_path: Path) -> None:
    """Berkas yang tidak dapat diurai adalah urusan linter, bukan pemeriksa ini.
    Melemparkan galat di sini membuat satu berkas rusak menghentikan seluruh
    pemeriksaan."""
    akar = _pohon(tmp_path, "rusak.py", "def (:\n")
    assert periksa_rute_terdaftar(akar) == []


def test_temuan_menyebut_berkas_dan_barisnya(tmp_path: Path) -> None:
    """Temuan tanpa tempat menuntut pembacanya mencari sendiri, dan yang
    menuntut pencarian akan ditunda."""
    akar = _pohon(tmp_path, "adaptor.py", '\n\nJALUR = "/api/v1/tanya"\n')
    (temuan,) = periksa_rute_terdaftar(akar)
    assert temuan.baris == 3
    assert temuan.berkas.name == "adaptor.py"
