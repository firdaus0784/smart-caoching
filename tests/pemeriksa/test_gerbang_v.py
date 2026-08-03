"""Uji pemeriksa V-03, V-05, V-06 — R-14.

V-01 (uji dan cakupan), V-02 (kepatuhan), dan V-04 (ketergantungan) memakai
pemeriksa yang sudah diuji sendiri pada tugas sebelumnya. Tiga sisanya baru
dan diuji di sini.

Seluruhnya memakai berkas contoh, bukan repositori nyata: V-01 menjalankan
pytest sebagai subproses, dan memanggilnya dari dalam pytest akan berulang.
"""

from pathlib import Path

from perkakas.pemeriksa.gerbang_v import (
    periksa_keamanan_statis,
    periksa_ketertelusuran,
    periksa_rahasia,
)


def _tulis(akar: Path, nama: str, isi: str) -> None:
    berkas = akar / nama
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(isi, encoding="utf-8")


# --- V-03 ketertelusuran ---------------------------------------------------


def test_modul_tanpa_kode_kebutuhan_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""Modul tanpa rujukan."""\n')
    temuan = periksa_ketertelusuran(tmp_path)
    assert len(temuan) == 1, f"modul tanpa kode kebutuhan lolos: {temuan}"


def test_modul_dengan_kode_kebutuhan_lolos(tmp_path: Path) -> None:
    for rujukan in ("R-04", "FR-B05", "NFR-15", "C-08", "ADR-11"):
        akar = tmp_path / rujukan
        _tulis(akar, "src/a.py", f'"""Modul — {rujukan}."""\n')
        assert periksa_ketertelusuran(akar) == [], f"{rujukan} tidak dikenali"


def test_modul_tanpa_docstring_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", "x = 1\n")
    assert len(periksa_ketertelusuran(tmp_path)) == 1


def test_berkas_init_kosong_dikecualikan(tmp_path: Path) -> None:
    """__init__.py kosong adalah penanda paket, bukan modul."""
    _tulis(tmp_path, "src/__init__.py", "")
    assert periksa_ketertelusuran(tmp_path) == []


# --- V-05 pemindaian keamanan statis ---------------------------------------


def test_eval_dan_exec_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\neval("1")\nexec("2")\n')
    assert len(periksa_keamanan_statis(tmp_path)) == 2


def test_subprocess_shell_true_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\nrun(["ls"], shell=True)\n')
    assert len(periksa_keamanan_statis(tmp_path)) == 1


def test_pickle_loads_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\npickle.loads(b"")\n')
    assert len(periksa_keamanan_statis(tmp_path)) == 1


def test_kode_bersih_tidak_menyalak(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\nx = 1 + 1\n')
    assert periksa_keamanan_statis(tmp_path) == []


# --- V-06 rahasia dan data pribadi -----------------------------------------


def test_kunci_privat_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\nk = "-----BEGIN PRIVATE KEY-----"\n')
    assert len(periksa_rahasia(tmp_path)) == 1


def test_kunci_penyedia_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\nk = "sk-ant-api03-abcdefghijklmnop"\n')
    assert len(periksa_rahasia(tmp_path)) == 1


def test_nik_tertangkap(tmp_path: Path) -> None:
    """NIK enam belas digit — FR-B04 melarangnya masuk korpus, apalagi kode."""
    _tulis(tmp_path, "src/a.py", '"""R-01."""\nnik = "3273010101900001"\n')
    assert len(periksa_rahasia(tmp_path)) == 1


def test_sandi_harfiah_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\npassword = "rahasia123"\n')
    assert len(periksa_rahasia(tmp_path)) == 1


def test_angka_biasa_tidak_dianggap_rahasia(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\ntahun = 2026\nambang = 0.85\n')
    assert periksa_rahasia(tmp_path) == []


def test_re_compile_dan_json_loads_tidak_dianggap_pelanggaran(tmp_path: Path) -> None:
    """Kekeliruan yang ditangkap `make check` sendiri pada percobaan pertama.

    Mencocokkan nama atribut saja membuat `re.compile` dan `json.loads`
    menyalak. Pemeriksa yang berisik pada pola paling lazim akan dimatikan
    orang, dan setelah itu ia tidak menjaga apa pun.
    """
    _tulis(
        tmp_path,
        "src/a.py",
        '"""R-01."""\nimport re, json, tomllib\n'
        're.compile("x")\njson.loads("{}")\ntomllib.loads("")\n',
    )
    assert periksa_keamanan_statis(tmp_path) == []


def test_pickle_loads_tertangkap_tetapi_json_loads_tidak(tmp_path: Path) -> None:
    _tulis(
        tmp_path,
        "src/a.py",
        '"""R-01."""\nimport pickle, json\npickle.loads(b"")\njson.loads("{}")\n',
    )
    temuan = periksa_keamanan_statis(tmp_path)
    assert len(temuan) == 1
    assert "pickle.loads" in temuan[0].pesan


def test_os_system_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/a.py", '"""R-01."""\nimport os\nos.system("ls")\n')
    assert len(periksa_keamanan_statis(tmp_path)) == 1
