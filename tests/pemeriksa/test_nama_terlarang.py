"""Uji pemeriksa nama terlarang — C-15.

C-15: "Tidak membuat tabel poin, lencana, papan peringkat, atau pertemanan.
Membuatnya kosong pun tidak."

Bahaya terbesar pemeriksa ini bukan melewatkan pelanggaran, melainkan
menyalak pada nama yang justru diwajibkan dokumen lain. `peringkat_kepercayaan`
(D-13 Bagian 6) dan `skor_relevansi` (D-01 Bagian 9) sah dan wajib ada.
Pemeriksa yang menolak keduanya akan dimatikan dalam sepekan, dan setelah itu
ia tidak menjaga apa pun.

Karena itu uji negatif-atas-negatif di bawah sama pentingnya dengan uji
pelanggarannya.
"""

from pathlib import Path

from perkakas.pemeriksa.nama_terlarang import periksa_nama_terlarang


def _tulis(akar: Path, nama: str, isi: str = "x = 1\n") -> None:
    berkas = akar / "src" / nama
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(isi, encoding="utf-8")


def test_nama_berkas_terlarang_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "lencana.py")
    temuan = periksa_nama_terlarang(tmp_path)
    assert len(temuan) == 1, f"nama berkas lolos: {temuan}"


def test_nama_kelas_terlarang_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "a.py", "class PapanPeringkat:\n    pass\n")
    assert len(periksa_nama_terlarang(tmp_path)) == 1


def test_nama_fungsi_terlarang_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "a.py", "def hitung_poin():\n    return 0\n")
    assert len(periksa_nama_terlarang(tmp_path)) == 1


def test_nama_peubah_terlarang_tertangkap(tmp_path: Path) -> None:
    _tulis(tmp_path, "a.py", "daftar_pertemanan = []\n")
    assert len(periksa_nama_terlarang(tmp_path)) == 1


def test_tabel_kosong_pun_tertangkap(tmp_path: Path) -> None:
    """C-15: "Membuatnya kosong pun tidak." """
    _tulis(tmp_path, "a.py", "class TabelLencana:\n    pass\n")
    assert len(periksa_nama_terlarang(tmp_path)) == 1


def test_peringkat_kepercayaan_tidak_dianggap_pelanggaran(tmp_path: Path) -> None:
    """D-13 Bagian 6 MEWAJIBKAN bidang ini. Menolaknya membatalkan C-19."""
    _tulis(tmp_path, "a.py", "peringkat_kepercayaan = 'T1'\n")
    assert periksa_nama_terlarang(tmp_path) == []


def test_skor_relevansi_tidak_dianggap_pelanggaran(tmp_path: Path) -> None:
    """D-01 Bagian 9 mensyaratkan skor relevansi pada discovery_served."""
    _tulis(tmp_path, "a.py", "skor_relevansi = 0.8\n")
    assert periksa_nama_terlarang(tmp_path) == []


def test_komentar_dan_untai_tidak_dianggap_pelanggaran(tmp_path: Path) -> None:
    """Menjelaskan mengapa lencana dilarang bukan membuat lencana."""
    _tulis(
        tmp_path,
        "a.py",
        '# lencana dan papan peringkat dilarang C-15\npesan = "tanpa lencana"\n',
    )
    assert periksa_nama_terlarang(tmp_path) == []


def test_perkakas_tidak_diperiksa(tmp_path: Path) -> None:
    """Pemeriksa ini sendiri memuat kata terlarang sebagai daftar."""
    berkas = tmp_path / "perkakas" / "daftar.py"
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text("lencana = 'x'\n", encoding="utf-8")
    assert periksa_nama_terlarang(tmp_path) == []


def test_src_nyata_bersih() -> None:
    akar = Path(__file__).resolve().parents[2]
    assert periksa_nama_terlarang(akar) == []
