"""Setiap pemeriksa wajib punya uji — temuan sesudah KB-056.

## Apa yang terjadi

Sapuan atas seluruh **33** fungsi `periksa_*` menemukan dua tanpa satu uji pun:
`periksa_cakupan` dan `periksa_pemisahan_instruksi`. Yang kedua adalah pemeriksa
mesin bagi **C-18**, dan setiap `make compliance` sejak fitur 001 melaporkan
"C-18 LULUS" tanpa seorang pun pernah memastikan pemeriksanya mampu berkata
sebaliknya.

Keduanya lolos karena tidak ada yang menghitung. Pasal yang tertulis pada
`daftar_pasal.py` terbaca sebagai terjaga, dan yang dibaca orang adalah
laporannya — bukan ada atau tidaknya ujinya.

## Yang uji ini buktikan, dan yang **tidak**

Ia membuktikan setiap pemeriksa **disebut** sekurangnya satu berkas uji. Ia
**tidak** membuktikan uji itu menuntutnya menyala. Perbedaan itu nyata:
pemeriksa yang hanya diuji "diam pada pohon bersih" lulus di sini sambil tetap
tidak menjaga apa pun.

Batas itu dinyatakan alih-alih ditutupi. Pemeriksa yang mengaku lebih tebal
daripada kenyataannya adalah kekeliruan yang justru dua kali ditemukan pada
proyek ini (KB-049, KB-050). Yang menutup sisanya uji mutasi per fitur, dan
itu pekerjaan manusia yang membaca — bukan pekerjaan sapuan.

Yang ia tangkap adalah kasus yang **sungguh terjadi**: pemeriksa tanpa uji sama
sekali. Dua kali, dan keduanya bertahan sejak fitur 001.
"""

from __future__ import annotations

import re
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]

POLA_DEFINISI = re.compile(r"^def (periksa_[a-z0-9_]+)", re.MULTILINE)

TANPA_UJI_DIIZINKAN: frozenset[str] = frozenset()
"""Sengaja kosong, dan sebaiknya tetap kosong.

Daftar pengecualian yang bertambah adalah pola yang `pyproject.toml` sendiri
sudah tolak ketika `disallow_any_explicit` dicabut. Bila sebuah pemeriksa
sungguh tidak dapat diuji, alasannya ditulis di sini beserta namanya — dan
alasan yang tertulis dapat dibantah, sedangkan ketiadaan uji tidak.
"""


def _pemeriksa_terdefinisi() -> dict[str, Path]:
    ditemukan: dict[str, Path] = {}
    for berkas in (AKAR / "perkakas").rglob("*.py"):
        if "__pycache__" in berkas.parts:
            continue
        for nama in POLA_DEFINISI.findall(berkas.read_text(encoding="utf-8")):
            ditemukan[nama] = berkas
    return ditemukan


def _sumber_uji() -> str:
    return "\n".join(
        berkas.read_text(encoding="utf-8")
        for berkas in (AKAR / "tests").rglob("*.py")
        if "__pycache__" not in berkas.parts
    )


def test_pemeriksa_ditemukan_dan_jumlahnya_wajar() -> None:
    """Sapuan yang tidak menemukan apa pun melaporkan bersih atas himpunan
    kosong — bentuk TA-01 pada uji ini sendiri."""
    assert len(_pemeriksa_terdefinisi()) >= 30


def test_setiap_pemeriksa_disebut_sekurangnya_satu_uji() -> None:
    """**Uji terpenting berkas ini.**

    Pemeriksa tanpa uji adalah pasal yang laporannya selalu hijau dan tidak
    pernah dibuktikan mampu merah.
    """
    sumber = _sumber_uji()
    tanpa = sorted(
        nama
        for nama in _pemeriksa_terdefinisi()
        if nama not in TANPA_UJI_DIIZINKAN and nama not in sumber
    )
    assert not tanpa, f"pemeriksa tanpa satu uji pun: {tanpa}"


def test_setiap_pemeriksa_pasal_disebut_sekurangnya_satu_uji() -> None:
    """Yang terdaftar pada `daftar_pasal.py` diperiksa terpisah dan lebih keras.

    Pemeriksa yang menjaga pasal konstitusi bukan alat bantu: laporannya
    dibaca sebagai pernyataan kepatuhan, dan pernyataan kepatuhan yang tidak
    pernah diuji adalah pernyataan yang tidak dapat ditagih.
    """
    daftar = (AKAR / "perkakas" / "kepatuhan" / "daftar_pasal.py").read_text(encoding="utf-8")
    terdaftar = set(re.findall(r"pemeriksa=(periksa_[a-z0-9_]+)", daftar))
    assert terdaftar, "tidak satu pun pemeriksa terbaca dari daftar_pasal.py"
    sumber = _sumber_uji()
    tanpa = sorted(nama for nama in terdaftar if nama not in sumber)
    assert not tanpa, f"pemeriksa pasal tanpa satu uji pun: {tanpa}"


def test_daftar_pengecualian_tetap_kosong() -> None:
    """Bukan aturan gaya. Pengecualian pertama yang ditambahkan tanpa alasan
    tertulis membuat yang kedua terasa wajar, dan yang ketiga tidak lagi
    diperhatikan."""
    assert not TANPA_UJI_DIIZINKAN
