"""Uji pemeriksa bentuk `HasilTanya` — B-2 fitur 021, R-06, R-10.

Menyala pada pohon yang dirusak, diam pada pohon yang sehat. Keduanya diuji;
pelajaran pemeriksa C-10 (KB-050) menunjukkan sebuah pemeriksa dapat gagal ke
kedua arah dalam satu sore.
"""

from pathlib import Path

from perkakas.pemeriksa.hasil_jalur import periksa_hasil_jalur

AKAR = Path(__file__).resolve().parents[2]

JALUR_SEHAT = '''"""Jalur tiruan."""


class Jalur:
    def __init__(self, *, sumber: list[str], pembungkus: object) -> None:
        self._sumber = sumber
        self._pembungkus = pembungkus

    def jawab(self) -> object:
        return HasilTanya(tanggapan=None)
'''


def _pohon(tmp_path: Path, *, jalur: str = JALUR_SEHAT, lain: str = "") -> Path:
    modul = tmp_path / "src" / "api"
    modul.mkdir(parents=True, exist_ok=True)
    (modul / "tanya.py").write_text(jalur, encoding="utf-8")
    if lain:
        (modul / "lain.py").write_text(lain, encoding="utf-8")
    return tmp_path


# ------------------------------------------------------------- pohon sungguhan


def test_pohon_sungguhan_bersih() -> None:
    """Pemeriksa yang berteriak pada pohon yang sehat akan dimatikan, dan yang
    dimatikan tidak menjaga apa pun."""
    assert periksa_hasil_jalur(AKAR) == []


# ------------------------------------------- aturan 1 · pembentukan terbatas


def test_pembentukan_di_modul_lain_ditolak(tmp_path: Path) -> None:
    """**Uji terpenting aturan 1.**

    Hasil jalur yang dapat disusun sendiri adalah hasil yang melewati tahap
    mana pun tanpa satu galat pun.
    """
    akar = _pohon(tmp_path, lain="def curang():\n    return HasilTanya(tanggapan=None)\n")
    temuan = periksa_hasil_jalur(akar)
    assert len(temuan) == 1
    assert "melewati tahap" in temuan[0].pesan


def test_pembentukan_pada_modul_jalur_sendiri_dilewati(tmp_path: Path) -> None:
    """`tanya.py` adalah satu-satunya tempat yang benar. Pemeriksa yang
    menolaknya di sana menolak satu-satunya jalan yang sah."""
    assert periksa_hasil_jalur(_pohon(tmp_path)) == []


def test_menyebut_nama_tanpa_membentuknya_bukan_pelanggaran(tmp_path: Path) -> None:
    """Anotasi tipe dan impor menyebut namanya tanpa membentuk apa pun.
    Menolaknya berarti melarang modul lain menyatakan bahwa ia menerima hasil
    jalur — dan aturan yang melarang menyatakan tipe akan dimatikan orang."""
    akar = _pohon(
        tmp_path,
        lain="def pakai(h: HasilTanya) -> HasilTanya:\n    return h\n",
    )
    assert periksa_hasil_jalur(akar) == []


# ------------------------------------- aturan 2 · validator tidak disuntikkan


def test_validator_yang_dapat_disuntikkan_ditolak(tmp_path: Path) -> None:
    """**Aturan 2 menutup lubang aturan 1.**

    Pembentukan yang terbatas pada satu modul tetap menghasilkan apa saja bila
    modul itu menjalankan validator pilihan pemanggil — hasilnya sah menurut
    aturan 1 dan tidak divalidasi menurut apa pun.
    """
    jalur = JALUR_SEHAT.replace(
        "def __init__(self, *, sumber: list[str], pembungkus: object) -> None:",
        "def __init__(self, *, sumber: list[str], validator: object) -> None:",
    )
    temuan = periksa_hasil_jalur(_pohon(tmp_path, jalur=jalur))
    assert len(temuan) == 1
    assert "C-19" in temuan[0].pesan


def test_parameter_posisional_juga_terjaring(tmp_path: Path) -> None:
    """Aturan yang hanya melihat parameter berkata kunci dilewati dengan
    memindahkan satu koma."""
    jalur = JALUR_SEHAT.replace(
        "def __init__(self, *, sumber: list[str], pembungkus: object) -> None:",
        "def __init__(self, pemeriksa: object) -> None:",
    )
    assert periksa_hasil_jalur(_pohon(tmp_path, jalur=jalur))


def test_modul_jalur_hilang_berbunyi_bukan_diam(tmp_path: Path) -> None:
    """**Aturan yang tidak menemukan yang dijaganya wajib berbunyi.**

    Pemeriksa yang diam ketika berkasnya hilang melaporkan bersih pada pohon
    yang justru kehilangan seluruh penjagaannya — bentuk TA-01 pada lapisan
    pemeriksa.
    """
    (tmp_path / "src").mkdir(parents=True, exist_ok=True)
    temuan = periksa_hasil_jalur(tmp_path)
    assert len(temuan) == 1
    assert "tidak ditemukan" in temuan[0].pesan


def test_berkas_bergalat_sintaksis_tidak_menghentikan_sapuan(tmp_path: Path) -> None:
    akar = _pohon(tmp_path, lain="def (:\n")
    assert periksa_hasil_jalur(akar) == []
