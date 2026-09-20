"""Sifat yang khas `SumberVektor` — T-5 fitur 019.

Kontraknya diuji `test_kontrak_sumber.py` bersama pelaksana lain. Berkas ini
memuat yang **tidak** berlaku bagi pelaksana lain: penyusunan yang menuntut
dimensi cocok, dan penjagaan bentuk yang datang dari peladen.
"""

from __future__ import annotations

import pytest
from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import PenyematTiruan
from src.rag.pengambilan.vektor import GalatDimensiVektor, SumberVektor
from tests.konftes_asinkron import jalankan
from tests.peladen import DIMENSI_UJI, psql, siapkan
from tests.rag.pengambilan.test_kontrak_sumber import KORPUS, VERSI_UJI, SambunganUji

siapkan()


def test_penyusunan_menolak_penyemat_berdimensi_lain() -> None:
    """Pemanggil yang salah pasang **tidak memperoleh objek sama sekali** —
    bukan memperoleh objek yang gagal pada kueri pertama."""
    with pytest.raises(GalatDimensiVektor):
        jalankan(
            SumberVektor.susun(
                sambungan=SambunganUji(),
                penyemat=PenyematTiruan(dimensi=DIMENSI_UJI + 1),
                indeks_tujuan=IndeksTujuan.UTAMA,
                versi_indeks=VERSI_UJI,
            )
        )


def test_skor_bukan_bilangan_dari_peladen_ditolak() -> None:
    """Penjagaan bentuk, bukan nilai.

    `pgvector` mengembalikan `double precision` bagi ungkapan jaraknya,
    sehingga cabang ini tidak dapat dipicu peladen sungguhan — dan justru
    karena itu ia diuji dengan sambungan buatan. Penjagaan yang tidak pernah
    dijalankan adalah penjagaan yang belum diketahui bekerja atau tidak.
    """

    class SambunganAneh:
        async def fetchrow(self, kueri: str, *argumen: object) -> object:
            return {"dimensi": DIMENSI_UJI}

        async def fetch(self, kueri: str, *argumen: object) -> object:
            return [{"id_segmen": "SEG-A", "skor": "dekat sekali"}]

        async def execute(self, kueri: str, *argumen: object) -> object:
            raise AssertionError("tidak dipakai")

    sumber = jalankan(
        SumberVektor.susun(
            sambungan=SambunganAneh(),
            penyemat=PenyematTiruan(dimensi=DIMENSI_UJI),
            indeks_tujuan=IndeksTujuan.UTAMA,
            versi_indeks=VERSI_UJI,
        )
    )
    with pytest.raises(GalatDimensiVektor, match="bukan bilangan"):
        jalankan(sumber.cari("kepala sekolah", batas=5))


# ── urutan menurut jarak — sifat yang membuat sumber ini ada ─────────


def _sumber_terisi() -> SumberVektor:
    """Sumber vektor berisi tiga segmen, disemat dengan penyemat tiruan."""
    penyemat = PenyematTiruan(dimensi=DIMENSI_UJI)
    psql("smart_coaching", "-c", "DELETE FROM indeks_utama.segmen_teks")
    for segmen in KORPUS:
        vektor = jalankan(penyemat.sematkan([segmen.teks]))[0]
        nilai = "[" + ",".join(repr(float(n)) for n in vektor) + "]"
        psql(
            "smart_coaching",
            "-c",
            "INSERT INTO indeks_utama.segmen_teks "
            "(id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, "
            "penanda_bagian, vektor) VALUES "
            f"('{segmen.id_segmen}', '{segmen.id_dokumen}', '{segmen.teks}', "
            f"'{segmen.lisensi.value}', true, '{segmen.penanda_bagian}', '{nilai}'::vector)",
        )
    return jalankan(
        SumberVektor.susun(
            sambungan=SambunganUji(),
            penyemat=penyemat,
            indeks_tujuan=IndeksTujuan.UTAMA,
            versi_indeks=VERSI_UJI,
        )
    )


@pytest.mark.parametrize("segmen", KORPUS, ids=lambda s: s.id_segmen)
def test_segmen_terdekat_berperingkat_teratas(segmen: object) -> None:
    """**Uji terpenting berkas ini.**

    Kueri yang sama persis dengan teks sebuah segmen berjarak nol darinya,
    sehingga segmen itu **wajib** teratas. Diuji bagi ketiga segmen, bukan
    satu: sumber yang selalu mengembalikan segmen yang sama juga lulus bila
    hanya satu yang diperiksa.

    Tanpa uji ini, `ORDER BY` yang keliru maupun arah skor yang terbalik lolos
    tanpa suara — keduanya ditemukan diam pada uji mutasi T5-3 dan T5-5.
    """
    hasil = jalankan(_sumber_terisi().cari(segmen.teks, batas=5))  # type: ignore[attr-defined]
    assert hasil.peringkat[0].id_segmen == segmen.id_segmen  # type: ignore[attr-defined]


def test_skor_menurun_seiring_peringkat() -> None:
    """Skor yang naik seiring peringkat berarti arahnya terbalik, dan
    penggabungan peringkat kemudian memakai urutan yang salah."""
    hasil = jalankan(_sumber_terisi().cari(KORPUS[0].teks, batas=5))
    skor = [k.skor for k in hasil.peringkat]
    assert skor == sorted(skor, reverse=True), skor
    assert skor[0] > skor[-1], "seluruh skor sama — jarak tidak memengaruhi apa pun"


# ── segmen tanpa vektor ──────────────────────────────────────────────


def test_segmen_tanpa_vektor_tidak_muncul() -> None:
    """Segmen yang sudah terindeks leksikal tetapi belum disematkan adalah
    keadaan sah; yang tidak sah adalah ia muncul sebagai kandidat dengan jarak
    yang tidak terdefinisi."""
    sumber = _sumber_terisi()
    psql(
        "smart_coaching",
        "-c",
        "INSERT INTO indeks_utama.segmen_teks "
        "(id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian) "
        "VALUES ('SEG-TANPA-VEKTOR', 'DOC-X', 'belum disematkan', 'terbuka', true, 'Pasal 1')",
    )
    hasil = jalankan(sumber.cari(KORPUS[0].teks, batas=10))
    assert "SEG-TANPA-VEKTOR" not in [k.id_segmen for k in hasil.peringkat]


# ── kueri kosong ditolak sebelum penyemat dipanggil ─────────────────


def test_kueri_kosong_ditolak_sebelum_penyemat_dipanggil() -> None:
    """Sumber tidak boleh bersandar pada penyemat untuk menolak kueri kosong.

    Penyemat yang lebih longgar — dan adaptor sungguhan mungkin demikian —
    akan membuat kueri kosong lolos sampai ke basis data. Penyemat yang
    melempar bila dipakai membuktikan penolakannya datang lebih dulu.
    """

    class PenyematYangMelarang(PenyematTiruan):
        async def sematkan(self, teks: object) -> object:  # type: ignore[override]
            raise AssertionError("penyemat dipanggil untuk kueri kosong")

    sumber = SumberVektor(
        sambungan=SambunganUji(),
        penyemat=PenyematYangMelarang(dimensi=DIMENSI_UJI),
        indeks_tujuan=IndeksTujuan.UTAMA,
        versi_indeks=VERSI_UJI,
    )
    with pytest.raises(ValueError, match="kueri kosong"):
        jalankan(sumber.cari("   ", batas=5))


def test_batas_memangkas_menurut_jarak_bukan_menurut_id() -> None:
    """Lubang yang ditemukan uji mutasi T5-3.

    `urutkan_kandidat` mengurutkan ulang menurut skor, sehingga urutan `ORDER
    BY` pada kueri tidak terlihat pada hasil — **selama tidak ada yang
    terpangkas**. Ketika `LIMIT` memangkas, urutan kueri yang menentukan baris
    mana yang selamat, dan urutan yang keliru membuang justru yang terdekat.

    Kueri sama persis dengan segmen terakhir; dengan `batas=1` hanya ia yang
    boleh selamat. `ORDER BY id_segmen` akan menyisakan SEG-A.
    """
    terjauh_menurut_id = KORPUS[-1]
    hasil = jalankan(_sumber_terisi().cari(terjauh_menurut_id.teks, batas=1))
    assert [k.id_segmen for k in hasil.peringkat] == [terjauh_menurut_id.id_segmen]


def test_nama_sumber_ini_vektor() -> None:
    """Lubang yang ditemukan uji mutasi T5-7.

    Uji kontrak hanya menuntut nama pada hasil sama dengan nama pada sumber —
    keduanya berubah bersama, sehingga penukaran nama lolos. Yang menjadikannya
    penting: `HasilPengambilan.asal` menyusun daftar penyumbang **menurut
    nama**, dan dua sumber bernama sama akan menumpuk menjadi satu baris.
    """
    assert _sumber_terisi().nama == "vektor"


def test_nama_pelaksana_tidak_ada_yang_kembar() -> None:
    """Dua sumber bernama sama membuat daftar penyumbang menyebut satu, dan
    yang hilang adalah yang dijalankan belakangan."""
    from tests.rag.pengambilan.test_kontrak_sumber import PABRIK

    nama = [PABRIK[k](IndeksTujuan.UTAMA).nama for k in sorted(PABRIK)]
    assert len(set(nama)) == len(nama), nama
