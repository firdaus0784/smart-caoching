"""Uji pemeriksa ketiadaan kemampuan bertindak — C-17, FR-F17, D-13 KD-09.

C-17 menyebut tiga hal sekaligus: tanpa pemanggilan alat, tanpa akses tulis
dari jalur penjawaban, tanpa pengiriman pesan keluar. Ketiganya diperiksa.

`docs/D13.md` KD-09 menyebut ini kendali paling berdaya dalam dokumen itu:
penyisipan instruksi berbahaya karena memberi penyerang kemampuan bertindak
melalui sistem. Sistem yang hanya dapat berbicara membatasi kerugian maksimal
menjadi satu jawaban keliru kepada satu pengguna — buruk, tetapi dapat
dipulihkan.
"""

from pathlib import Path

from perkakas.pemeriksa.tanpa_kemampuan_bertindak import (
    periksa_tanpa_kemampuan_bertindak,
)


def _tulis(akar: Path, nama: str, isi: str) -> None:
    berkas = akar / nama
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(f'"""C-17."""\n{isi}', encoding="utf-8")


def test_pengiriman_keluar_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/kirim.py", "import smtplib\n")
    temuan = periksa_tanpa_kemampuan_bertindak(tmp_path)
    assert len(temuan) == 1, f"pengiriman keluar lolos: {temuan}"


def test_pemanggilan_perintah_luar_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/jalankan.py", "import subprocess\n")
    assert len(periksa_tanpa_kemampuan_bertindak(tmp_path)) == 1


def test_akses_tulis_dari_jalur_penjawaban_tertangkap(tmp_path: Path) -> None:
    """C-17 menyebut akses tulis DARI JALUR PENJAWABAN, bukan seluruh sistem."""
    _tulis(tmp_path, "src/rag/penyusun.py", 'open("keluaran.txt", "w")\n')
    assert len(periksa_tanpa_kemampuan_bertindak(tmp_path)) == 1


def test_penulis_logbook_tidak_dianggap_pelanggaran(tmp_path: Path) -> None:
    """src/logbook/ bukan jalur penjawaban; ia justru yang C-09 wajibkan."""
    _tulis(tmp_path, "src/logbook/penulis.py", 'berkas.open("a")\n')
    assert periksa_tanpa_kemampuan_bertindak(tmp_path) == []


def test_parameter_alat_pada_tanda_tangan_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/llm/pembungkus.py", "def panggil(self, tools=None):\n    pass\n")
    temuan = periksa_tanpa_kemampuan_bertindak(tmp_path)
    assert len(temuan) == 1, f"parameter alat lolos: {temuan}"


def test_bidang_alat_pada_model_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/llm/tipe.py", "class K:\n    daftar_alat: list[str] = []\n")
    assert len(periksa_tanpa_kemampuan_bertindak(tmp_path)) == 1


def test_membaca_berkas_tidak_dianggap_pelanggaran(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/rag/pembaca.py", 'open("korpus.txt")\n')
    assert periksa_tanpa_kemampuan_bertindak(tmp_path) == []


def test_repositori_nyata_bersih() -> None:
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_tanpa_kemampuan_bertindak(akar)
    assert temuan == [], "; ".join(str(t) for t in temuan)
