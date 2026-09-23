"""Kontrak `SumberKandidat` — T-2 fitur 019, R-01.

R-01 menuntut `SumberVektor` lulus rangkaian uji yang **sama** dengan sumber
yang sudah ada, tanpa satu pun uji diubah. Karena itu uji di bawah menerima
pelaksananya dari `PABRIK`, bukan menyusunnya sendiri.

## Hari ini `PABRIK` berisi satu pelaksana, dan itu disengaja

Tugas T-2 mengubah **bentuk** uji dan membuktikan hasilnya tidak berubah,
sebelum pelaksana kedua ditambahkan pada T-5. Menambah keduanya sekaligus
membuat kegagalan tidak dapat ditelusuri ke perubahan yang mana — pelajaran
T-2 fitur 024.

## Yang pindah ke sini, dan yang tidak

Lima uji pindah dari `test_kandidat.py`: keduanya menguji **kontrak sumber**,
dan sebelumnya dijalankan atas `SumberTiruan` — sebuah ganda uji, bukan
pelaksana yang disebarkan. Uji yang menguji `Kandidat`, `HasilSumber`, dan
`urutkan_kandidat` tetap di sana: ia menguji **tipe**, bukan pelaksana.

`test_bm25.py` tetap memuat uji yang khas BM25 — skor yang dihitung tangan,
perlakuan stem, kata henti. Itu bukan kontrak: sumber vektor tidak memiliki
skor BM25 untuk dihitung.

## Temuan yang dicatat, bukan diperbaiki di sini

`SumberTiruan` — dipakai `test_gabung.py` dan `test_hibrida.py` — **tidak lagi
dijalankan terhadap kontrak ini** sesudah lima uji itu pindah. Bila ganda uji
itu menyimpang dari kontrak, berkas yang bersandar padanya akan lulus sambil
membuktikan lebih sedikit daripada yang terbaca.

Menambahkannya ke `PABRIK` adalah perubahan satu baris, dan **sengaja tidak
dikerjakan sekarang**: `tasks.md` T-2 menetapkan satu pelaksana, dan menambah
entri kedua atas penilaian sendiri adalah mengubah cakupan yang sudah lewat
Gerbang 3. Diangkat pada T-5, ketika `PABRIK` memang bertambah.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import PenyematTiruan
from src.penyimpanan.indeks import SegmenTerindeks, StatusLisensi
from src.rag.pengambilan.bm25 import SumberBM25, bangun_indeks
from src.rag.pengambilan.kandidat import SumberKandidat
from src.rag.pengambilan.vektor import SKEMA, TABEL, SumberVektor
from tests.konftes_asinkron import jalankan
from tests.peladen import DIMENSI_UJI, HOST, PORT, psql, siapkan
from tests.rag.pengambilan.sumber_tiruan import SumberTiruan

siapkan()


class SambunganUji:
    """Menyambung sebagai pengelola, menutup tiap panggilan."""

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user="pengelola", database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def fetch(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetch", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("execute", kueri, *argumen)


VERSI_UJI = "indeks-2026-08-12"


def _segmen(
    id_segmen: str, teks: str, *, tujuan: IndeksTujuan = IndeksTujuan.UTAMA
) -> SegmenTerindeks:
    return SegmenTerindeks(
        id_segmen=id_segmen,
        id_dokumen="DOC-" + id_segmen,
        teks=teks,
        lisensi=StatusLisensi.TERBUKA,
        indeks_tujuan=tujuan,
        anonimisasi_terverifikasi=True,
        penanda_bagian="Pasal 1",
    )


KORPUS = (
    _segmen("SEG-A", "Kepala sekolah menyusun RKAS"),
    _segmen("SEG-B", "Kepala sekolah"),
    _segmen("SEG-C", "Guru mengajar kelas satu"),
)
"""Bahan yang sama bagi setiap pelaksana.

Kueri `kepala` menemukan SEG-A dan SEG-B; `RKAS` menemukan SEG-A saja. Kedua
sifat itu yang uji di bawah bersandar padanya, dan keduanya berlaku bagi
pencarian leksikal maupun semantik.
"""

KUERI_DUA_HASIL = "kepala sekolah"
KUERI_SATU_HASIL = "RKAS"


def _susun_bm25(indeks_tujuan: IndeksTujuan = IndeksTujuan.UTAMA) -> SumberKandidat:
    korpus = tuple(_segmen(s.id_segmen, s.teks, tujuan=indeks_tujuan) for s in KORPUS)
    return SumberBM25(bangun_indeks(korpus, versi=VERSI_UJI, indeks_tujuan=indeks_tujuan))


def _susun_vektor(indeks_tujuan: IndeksTujuan = IndeksTujuan.UTAMA) -> SumberKandidat:
    """Sumber vektor di atas peladen sungguhan, dengan korpus yang sama.

    Isi tabelnya ditanam ulang tiap pemanggilan: rangkaian uji lain memakai
    tabel yang sama, dan urutan uji bukan hal yang boleh diandalkan.
    """
    penyemat = PenyematTiruan(dimensi=DIMENSI_UJI)
    skema = SKEMA[indeks_tujuan]
    psql("smart_coaching", "-c", f"DELETE FROM {skema}.{TABEL}")
    for segmen in KORPUS:
        vektor = jalankan(penyemat.sematkan([segmen.teks]))[0]
        nilai = "[" + ",".join(repr(float(n)) for n in vektor) + "]"
        psql(
            "smart_coaching",
            "-c",
            f"INSERT INTO {skema}.{TABEL} "
            "(id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, "
            "penanda_bagian, vektor_sematan) VALUES "
            f"('{segmen.id_segmen}', '{segmen.id_dokumen}', '{segmen.teks}', "
            f"'{segmen.lisensi.value}', true, '{segmen.penanda_bagian}', '{nilai}'::vector)",
        )
    return jalankan(
        SumberVektor.susun(
            sambungan=SambunganUji(),
            penyemat=penyemat,
            indeks_tujuan=indeks_tujuan,
            versi_indeks=VERSI_UJI,
        )
    )


def _susun_tiruan(indeks_tujuan: IndeksTujuan = IndeksTujuan.UTAMA) -> SumberKandidat:
    """Ganda uji yang dipakai `test_gabung.py` dan `test_hibrida.py`.

    Ia **wajib** memenuhi kontrak yang sama: ganda yang menyimpang membuat
    berkas yang bersandar padanya lulus sambil membuktikan lebih sedikit
    daripada yang terbaca. Diangkat di sini sebagaimana KB-095 janjikan, dan
    penyimpangannya memang ditemukan — ia menerima kueri kosong.
    """
    return SumberTiruan(
        "tiruan",
        {"SEG-A": 3.0, "SEG-B": 2.0, "SEG-C": 1.0},
        indeks_tujuan=indeks_tujuan,
        versi_indeks=VERSI_UJI,
    )


PABRIK: dict[str, Callable[[IndeksTujuan], SumberKandidat]] = {
    "bm25": _susun_bm25,
    "tiruan": _susun_tiruan,
    "vektor": _susun_vektor,
}
"""Pelaksana yang wajib lulus kontrak yang sama — R-01.

Ketiganya menjalankan **rangkaian uji yang sama, tanpa satu pun uji diubah**.
Itu bunyi R-01 apa adanya.
"""


@pytest.fixture(params=sorted(PABRIK), ids=sorted(PABRIK))
def sumber(request: pytest.FixtureRequest) -> SumberKandidat:
    return PABRIK[request.param](IndeksTujuan.UTAMA)


# ── kontrak ──────────────────────────────────────────────────────────


def test_peringkat_sama_pada_masukan_sama(sumber: SumberKandidat) -> None:
    """**R-02.** Dijalankan dua kali pada sumber yang sama.

    Sumber yang hasilnya bergeser antarpemanggilan membuat percobaan pada
    catatan D-10 L1 tidak dapat diulang siapa pun, termasuk tim sendiri tiga
    bulan kemudian.
    """
    pertama = jalankan(sumber.cari(KUERI_DUA_HASIL, batas=10))
    kedua = jalankan(sumber.cari(KUERI_DUA_HASIL, batas=10))
    assert pertama.peringkat == kedua.peringkat


def test_hasil_membawa_versi_indeks(sumber: SumberKandidat) -> None:
    """D-07 Bagian 3.3: setiap pembangunan ulang menghasilkan nomor versi.

    Tanpanya, dua percobaan atas indeks berbeda tidak dapat dibedakan, dan
    perbandingan antarpercobaan menjadi perbandingan yang tidak diketahui apa
    yang berubah.
    """
    assert jalankan(sumber.cari(KUERI_DUA_HASIL, batas=5)).versi_indeks == VERSI_UJI


def test_hasil_menyatakan_peringkat_setiap_kandidat(sumber: SumberKandidat) -> None:
    """Peringkat dihitung dari posisinya, bukan disimpan terpisah.

    Dua sumber kebenaran bagi hal yang sama akan berbeda ketika salah satunya
    disunting, dan yang berbeda adalah yang tidak diperbarui.
    """
    hasil = jalankan(sumber.cari(KUERI_DUA_HASIL, batas=5))
    assert hasil.peringkat, "kueri ini wajib menemukan sesuatu pada korpus uji"
    teratas = hasil.peringkat[0].id_segmen
    assert hasil.peringkat_dari(teratas) == 1
    assert hasil.peringkat_dari("SEG-TIDAK-ADA") is None


def test_batas_memangkas_bukan_mengisi(sumber: SumberKandidat) -> None:
    """Kandidat yang lebih sedikit daripada batas diteruskan seluruhnya.

    Mengisi sampai penuh dengan segmen berskor nol memberi penyusun jawaban
    bahan yang tidak relevan, dan penilaian kecukupan bukti kemudian menghitung
    bahan itu sebagai bukti.
    """
    longgar = jalankan(sumber.cari(KUERI_DUA_HASIL, batas=10))
    sempit = jalankan(sumber.cari(KUERI_DUA_HASIL, batas=1))
    assert len(longgar.peringkat) <= 10
    assert len(sempit.peringkat) == 1
    assert len(longgar.peringkat) >= len(sempit.peringkat)


def test_nama_sumber_terbawa_ke_hasilnya(sumber: SumberKandidat) -> None:
    """`ambil_hibrida` menyusun daftar penyumbang dari `nama_sumber` pada
    hasil. Sumber yang menamai hasilnya berbeda dari dirinya sendiri membuat
    daftar itu menyebut sumber yang tidak pernah dijalankan."""
    hasil = jalankan(sumber.cari(KUERI_DUA_HASIL, batas=5))
    assert hasil.nama_sumber == sumber.nama


def test_sumber_menyatakan_versi_indeksnya(sumber: SumberKandidat) -> None:
    """Dibaca sebelum sumber dijalankan — mis. ketika penyusun hibrida
    melaporkan indeks mana yang ikut menyumbang. Sumber yang hanya
    menyatakannya di dalam hasil memaksa pemanggil menjalankannya dulu untuk
    tahu indeks apa yang akan dijalankan."""
    assert sumber.versi_indeks == VERSI_UJI


def test_kueri_kosong_ditolak(sumber: SumberKandidat) -> None:
    """Kueri kosong yang diteruskan menghasilkan kandidat sembarang, dan
    kandidat sembarang dihitung sebagai bukti pada tahap berikutnya."""
    with pytest.raises(ValueError):
        jalankan(sumber.cari("   ", batas=10))


@pytest.mark.parametrize("tujuan", list(IndeksTujuan))
@pytest.mark.parametrize("nama", sorted(PABRIK))
def test_sumber_menyatakan_indeks_tujuannya(nama: str, tujuan: IndeksTujuan) -> None:
    """Dipakai penyusun hibrida: kredensial diperiksa terhadap indeks tujuan
    sumber **sebelum** sumber dijalankan. Sumber yang salah menyatakannya
    membuat pemeriksaan itu memeriksa hal yang keliru."""
    assert PABRIK[nama](tujuan).indeks_tujuan is tujuan
