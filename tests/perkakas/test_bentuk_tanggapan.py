"""Uji pemeriksa bentuk tanggapan — C-2 fitur 009, R-01, R-13, C-20.

Repositori ini sudah bersih terhadap kedua aturan pada hari pemeriksanya
ditulis, sehingga menjalankannya di sini tidak membuktikan satu pun aturan
bekerja. Keduanya diuji terhadap pohon yang **sengaja dirusak**.

**Aturan 2 diuji dengan rute yang benar-benar dideklarasikan**, bukan hanya
atas pohon tanpa `src/api/`. Tanpa itu, pemeriksanya lulus hari ini dan tetap
lulus pada hari fitur 021 menambah rute yang salah.
"""

from pathlib import Path

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.bentuk_tanggapan import (
    bidang_d14,
    periksa_bentuk_tanggapan,
    rute_d14,
)

AKAR = Path(__file__).resolve().parents[2]

D14 = """# D-14

## 3. Peta Rute

### 3.2 Tanya Jawab

| Metode | Rute | Peran | Kebutuhan |
|---|---|---|---|
| POST | `/api/v1/tanya` | pengguna | FR-F01 |
| GET | `/api/v1/percakapan` | pengguna | FR-F09 |

## 4. Bentuk Tanggapan

### 4.1 Tanggapan Jawaban

```json
{
  "id_pesan": "msg_1",
  "status_dasar": "kuat",
  "penafian": "..."
}
```
"""

TANGGAPAN = '''"""Tanggapan."""

from pydantic import BaseModel


class Tanggapan(BaseModel):
    id_pesan: str
    status_dasar: str
    penafian: str
'''


def _pohon(
    tmp_path: Path,
    *,
    d14: str = D14,
    tanggapan: str = TANGGAPAN,
    rute: str | None = None,
) -> Path:
    akar = tmp_path / "pohon"
    (akar / "docs").mkdir(parents=True)
    (akar / "docs" / "D14.md").write_text(d14, encoding="utf-8")
    (akar / "src" / "rag" / "jawaban").mkdir(parents=True)
    (akar / "src" / "rag" / "jawaban" / "tanggapan.py").write_text(tanggapan, encoding="utf-8")
    if rute is not None:
        (akar / "src" / "api").mkdir(parents=True)
        (akar / "src" / "api" / "rute.py").write_text(rute, encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_bentuk_tanggapan(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    assert periksa_bentuk_tanggapan(AKAR) == []


def test_kontrak_dibaca_dari_d14_sungguhan() -> None:
    """Sepuluh bidang dan dua puluh tujuh rute — dari dokumennya, bukan dari
    salinan pada pemeriksa."""
    teks = (AKAR / "docs" / "D14.md").read_text(encoding="utf-8")
    assert len(bidang_d14(teks)) == 10
    assert "/api/v1/tanya" in rute_d14(teks)


# ------------------------------------------------------------------- aturan 1


def test_bidang_tambahan_ditemukan(tmp_path: Path) -> None:
    """**Aturan 1, dan bentuk yang AG-03 persis larang.**

    `skor_keyakinan` tampak tidak berbahaya dan memindahkan penilaian dari
    sistem ke klien — dan klien tidak terikat konstitusi.
    """
    rusak = TANGGAPAN + "    skor_keyakinan: float\n"
    temuan = periksa_bentuk_tanggapan(_pohon(tmp_path, tanggapan=rusak))
    assert any("skor_keyakinan" in str(t) for t in temuan)


def test_bidang_yang_hilang_ditemukan(tmp_path: Path) -> None:
    """Pengurangan juga temuan: ia menghapus tempat sebuah pasal diwujudkan.

    Menghapus `status_dasar` menghapus tempat kecukupan bukti tampil sama
    sekali.
    """
    rusak = TANGGAPAN.replace("    status_dasar: str\n", "")
    temuan = periksa_bentuk_tanggapan(_pohon(tmp_path, tanggapan=rusak))
    assert any("status_dasar" in str(t) for t in temuan)


def test_modul_tanggapan_yang_hilang_ditemukan(tmp_path: Path) -> None:
    akar = _pohon(tmp_path)
    (akar / "src" / "rag" / "jawaban" / "tanggapan.py").unlink()
    assert periksa_bentuk_tanggapan(akar)


def test_kelas_tanggapan_yang_hilang_ditemukan(tmp_path: Path) -> None:
    assert periksa_bentuk_tanggapan(_pohon(tmp_path, tanggapan='"""Kosong."""\n'))


def test_d14_tanpa_blok_json_ditemukan(tmp_path: Path) -> None:
    """**Pemeriksa yang tidak menemukan kontraknya tidak memeriksa apa pun.**

    Tanpa uji ini, menghapus blok JSON dari D-14 membuat pemeriksanya melaporkan
    bersih atas bentuk tanggapan apa pun — TA-01 pada perkakas yang dibangun
    justru untuk menutupnya.
    """
    tanpa = D14.split("### 4.1")[0]
    temuan = periksa_bentuk_tanggapan(_pohon(tmp_path, d14=tanpa))
    assert any("tidak memeriksa apa pun" in str(t) for t in temuan)


# ------------------------------------------------------------------- aturan 2


def test_rute_yang_ada_pada_d14_diterima(tmp_path: Path) -> None:
    """**Aturan 2 diuji dengan rute yang benar-benar dideklarasikan.**

    Tanpa ini, pemeriksanya lulus hari ini dan tetap lulus pada hari fitur 021
    menambah rute yang salah.
    """
    rute = '''"""Rute."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/api/v1/tanya")
def tanya() -> None:
    pass
'''
    assert periksa_bentuk_tanggapan(_pohon(tmp_path, rute=rute)) == []


def test_rute_di_luar_d14_ditemukan(tmp_path: Path) -> None:
    """AG-02: agen tidak boleh menambah rute yang tidak ada pada Bagian 3.

    Rute yang tidak tercatat adalah rute yang **perannya tidak pernah
    ditetapkan** — dan AG-05 menuntut setiap rute baru menyatakan perannya.
    """
    rute = '''"""Rute."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/v1/debug/segmen")
def debug() -> None:
    pass
'''
    temuan = periksa_bentuk_tanggapan(_pohon(tmp_path, rute=rute))
    assert any("/api/v1/debug/segmen" in str(t) for t in temuan)


def test_tanpa_direktori_api_nol_temuan(tmp_path: Path) -> None:
    """**Pernyataan yang benar, bukan pemeriksaan yang hampa.**

    Aturan ini melarang keberadaan, bukan menuntut keberadaan: "nol rute,
    karena itu nol rute terlarang" benar tanpa syarat. Bedanya dengan
    kekeliruan C-01 pada fitur 008 dinyatakan pada uraian pemeriksanya.
    """
    assert periksa_bentuk_tanggapan(_pohon(tmp_path)) == []


def test_d14_tanpa_tabel_rute_ditemukan(tmp_path: Path) -> None:
    tanpa = D14.split("## 3. Peta Rute")[0] + D14.split("## 4. Bentuk Tanggapan")[1]
    assert periksa_bentuk_tanggapan(_pohon(tmp_path, d14="# D-14\n\n## 4\n\n" + tanpa))


# ---------------------------------------------------------------- pendaftaran


def test_c20_terdaftar_dengan_pemeriksa() -> None:
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-20")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None
