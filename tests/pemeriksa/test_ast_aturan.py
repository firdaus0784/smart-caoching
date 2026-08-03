"""Uji inti pemeriksa AST — prasyarat R-04, R-13, ADR-13.

Tiga aturan bersandar pada inti ini: larangan impor pustaka penyedia di luar
`src/llm/` (C-08), larangan membuka `logbook/` dengan mode tulis (R-13), dan
pembatasan konstruksi `Instruksi` (ADR-13).

Uji di bawah memuat pelanggaran buatan yang **wajib tertangkap**. Pemeriksa
yang hanya diuji pada berkas bersih akan lulus tanpa pernah menyala, dan
pemeriksa yang tidak pernah menyala lebih buruk daripada tidak ada pemeriksa —
ia menambahkan tampilan keyakinan pada keadaan yang tidak diperiksa.
"""

from pathlib import Path

from perkakas.pemeriksa.ast_aturan import (
    berkas_python,
    impor_pada,
    panggilan_nama,
    pembukaan_berkas,
)


def _tulis(akar: Path, nama: str, isi: str) -> Path:
    berkas = akar / nama
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(isi, encoding="utf-8")
    return berkas


def test_menelusuri_berkas_python_saja(tmp_path: Path) -> None:
    _tulis(tmp_path, "a.py", "x = 1\n")
    _tulis(tmp_path, "dalam/b.py", "y = 2\n")
    _tulis(tmp_path, "c.txt", "bukan python\n")

    ditemukan = {b.name for b in berkas_python(tmp_path)}
    assert ditemukan == {"a.py", "b.py"}


def test_melewati_direktori_singgahan(tmp_path: Path) -> None:
    _tulis(tmp_path, "a.py", "x = 1\n")
    _tulis(tmp_path, ".venv/paket/b.py", "y = 2\n")
    _tulis(tmp_path, "__pycache__/c.py", "z = 3\n")

    ditemukan = {b.name for b in berkas_python(tmp_path)}
    assert ditemukan == {"a.py"}, f"singgahan ikut tertelusur: {ditemukan}"


def test_impor_biasa_dan_from_tertangkap(tmp_path: Path) -> None:
    berkas = _tulis(
        tmp_path,
        "m.py",
        "import satu\nfrom dua.tiga import empat\nimport lima.enam\n",
    )
    modul = {i.modul for i in impor_pada(berkas)}
    assert modul == {"satu", "dua", "lima"}


def test_impor_di_dalam_fungsi_tetap_tertangkap(tmp_path: Path) -> None:
    """Pelanggaran buatan: impor disembunyikan di dalam fungsi.

    Pemeriksa yang hanya melihat pernyataan tingkat atas akan melewatkannya,
    dan itu jalan keluar termudah bagi siapa pun yang ingin menghindari C-08.
    """
    berkas = _tulis(
        tmp_path,
        "m.py",
        "def f():\n    import tersembunyi\n    return tersembunyi\n",
    )
    modul = {i.modul for i in impor_pada(berkas)}
    assert "tersembunyi" in modul, f"impor bersarang lolos: {modul}"


def test_nomor_baris_dilaporkan(tmp_path: Path) -> None:
    berkas = _tulis(tmp_path, "m.py", "x = 1\n\nimport tiga\n")
    impor = impor_pada(berkas)
    assert [i.baris for i in impor] == [3]


def test_panggilan_nama_tertangkap(tmp_path: Path) -> None:
    berkas = _tulis(
        tmp_path,
        "m.py",
        "a = Instruksi(teks='x')\nb = lain()\nc = modul.Instruksi(teks='y')\n",
    )
    assert panggilan_nama(berkas, "Instruksi") == [1, 3], (
        "konstruksi lewat atribut modul harus ikut tertangkap"
    )


def test_pembukaan_berkas_mode_tulis_tertangkap(tmp_path: Path) -> None:
    berkas = _tulis(
        tmp_path,
        "m.py",
        "open('logbook/L1.jsonl', 'a')\nopen('logbook/L1.jsonl', 'w')\nopen('lain.txt', 'w')\n",
    )
    hasil = pembukaan_berkas(berkas)
    modus = {(jalur, mode) for _, jalur, mode in hasil}
    assert ("logbook/L1.jsonl", "w") in modus
    assert ("logbook/L1.jsonl", "a") in modus


def test_berkas_rusak_dilaporkan_bukan_dilewati(tmp_path: Path) -> None:
    """Berkas yang gagal diurai tidak boleh dianggap bersih."""
    berkas = _tulis(tmp_path, "rusak.py", "def f(\n")
    try:
        impor_pada(berkas)
    except SyntaxError:
        return
    raise AssertionError("berkas rusak dilewati diam-diam, seharusnya menyalak")
