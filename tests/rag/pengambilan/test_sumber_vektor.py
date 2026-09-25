"""Sifat yang khas `SumberVektor` — T-5 fitur 019.

Kontraknya diuji `test_kontrak_sumber.py` bersama pelaksana lain. Berkas ini
memuat yang **tidak** berlaku bagi pelaksana lain: penyusunan yang menuntut
dimensi cocok, dan penjagaan bentuk yang datang dari peladen.
"""

from __future__ import annotations

import pytest
from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import PenyematTiruan
from src.penyimpanan.skema_indeks import GalatDimensiVektor
from src.rag.pengambilan.vektor import SumberVektor
from tests.konftes_asinkron import jalankan
from tests.peladen import DIMENSI_UJI, psql, siapkan
from tests.rag.pengambilan.sumber_tiruan import SumberTiruan
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
            # Satu sambungan melayani dua kueri berbeda — pencocokan dimensi
            # dan penghitungan segmen tanpa vektor. Keduanya dijawab.
            return {"dimensi": DIMENSI_UJI, "jumlah": 0}

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


def _isi_korpus(penyemat: PenyematTiruan) -> None:
    """Tulis KORPUS ke indeks utama, disemat dengan `penyemat`."""
    psql("smart_coaching", "-c", "DELETE FROM indeks_utama.segmen_teks")
    for segmen in KORPUS:
        vektor = jalankan(penyemat.sematkan([segmen.teks]))[0]
        nilai = "[" + ",".join(repr(float(n)) for n in vektor) + "]"
        psql(
            "smart_coaching",
            "-c",
            "INSERT INTO indeks_utama.segmen_teks "
            "(id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, "
            "penanda_bagian, vektor_sematan) VALUES "
            f"('{segmen.id_segmen}', '{segmen.id_dokumen}', '{segmen.teks}', "
            f"'{segmen.lisensi.value}', true, '{segmen.penanda_bagian}', '{nilai}'::vector)",
        )


def _sumber_terisi() -> SumberVektor:
    """Sumber vektor berisi tiga segmen, disemat dengan penyemat tiruan."""
    penyemat = PenyematTiruan(dimensi=DIMENSI_UJI)
    _isi_korpus(penyemat)
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


# ── T-6 · jumlah segmen tanpa vektor dibawa keluar ──────────────────


def test_indeks_penuh_melaporkan_nol() -> None:
    """Nol menyatakan indeks penuh. Ia bukan hal yang sama dengan `None`."""
    hasil = jalankan(_sumber_terisi().cari(KORPUS[0].teks, batas=5))
    assert hasil.segmen_tanpa_vektor == 0


def test_segmen_belum_tersemat_terhitung_dan_terbawa_keluar() -> None:
    """**Inti T-6.**

    Indeks yang separuh terisi sambil terbaca penuh adalah bentuk kekeliruan
    yang sama dengan uji yang dilewati tanpa dilaporkan: hasilnya tampak sah,
    dan yang membacanya tidak punya cara mengetahui sebaliknya.
    """
    sumber = _sumber_terisi()
    for nomor in (1, 2):
        psql(
            "smart_coaching",
            "-c",
            "INSERT INTO indeks_utama.segmen_teks "
            "(id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian) "
            f"VALUES ('SEG-KOSONG-{nomor}', 'DOC-X', 'belum disematkan', 'terbuka', "
            "true, 'Pasal 1')",
        )
    hasil = jalankan(sumber.cari(KORPUS[0].teks, batas=10))
    assert hasil.segmen_tanpa_vektor == 2
    assert all(not k.id_segmen.startswith("SEG-KOSONG") for k in hasil.peringkat)


def test_jumlah_tetap_terbawa_ketika_pencarian_tidak_menemukan_apa_pun() -> None:
    """Keadaan yang paling perlu terbaca, dan yang paling mudah hilang.

    Kueri gabungan yang menyisipkan hitungan ke baris hasil kehilangan
    angkanya tepat ketika tidak ada baris hasil — yaitu ketika seluruh isi
    indeks belum tersemat.
    """
    sumber = _sumber_terisi()
    psql("smart_coaching", "-c", "UPDATE indeks_utama.segmen_teks SET vektor_sematan = NULL")
    hasil = jalankan(sumber.cari(KORPUS[0].teks, batas=10))
    assert hasil.peringkat == ()
    assert hasil.segmen_tanpa_vektor == len(KORPUS)


def test_sumber_lain_membiarkan_jumlah_tidak_diketahui() -> None:
    """`None` berarti tidak diketahui, bukan nol.

    BM25 tidak memiliki gagasan "segmen belum tersemat"; memaksanya menjawab
    akan menghasilkan angka yang dikarang agar bidang terisi, dan angka
    semacam itu lebih buruk daripada bidang kosong.
    """
    from tests.rag.pengambilan.test_kontrak_sumber import PABRIK

    for nama in ("bm25", "tiruan"):
        hasil = jalankan(PABRIK[nama](IndeksTujuan.UTAMA).cari("kepala sekolah", batas=5))
        assert hasil.segmen_tanpa_vektor is None, nama


# ── penyemat dipilih pemanggil, dan versinya terbawa keluar ──────────


def test_sumber_memakai_penyemat_yang_diserahkan_pemanggil() -> None:
    """**R-02.** Pelaksana sungguhan dipilih pemanggil, bukan disusun sumber.

    Ditemukan lewat mutasi M-8 T-8, yang **diam** pada putaran pertama:
    seluruh uji menyerahkan `PenyematTiruan()`, sehingga sumber yang diam-diam
    menyusun `PenyematTiruan()` sendiri menghasilkan keluaran yang persis sama.
    Mutasinya tidak lemah — tidak ada uji yang membedakan penyemat pemanggil
    dari penyemat baku, karena tidak pernah ada penyemat kedua.

    Uji ini memberi penyemat yang **tidak dapat ditiru bawaan**: ia memetakan
    teks apa pun ke vektor segmen ketiga. Hasilnya menjadi pasti, bukan
    kebetulan — kueri berbunyi teks segmen pertama, dan yang wajib teratas
    tetap segmen ketiga.
    """
    sasaran = KORPUS[2]

    class PenyematTetap(PenyematTiruan):
        """Memetakan teks apa pun ke vektor `sasaran`."""

        async def sematkan(self, teks):  # type: ignore[no-untyped-def]
            satu = (await super().sematkan([sasaran.teks]))[0]
            return [satu for _ in teks]

    penyemat = PenyematTiruan(dimensi=DIMENSI_UJI)
    _isi_korpus(penyemat)
    sumber = jalankan(
        SumberVektor.susun(
            sambungan=SambunganUji(),
            penyemat=PenyematTetap(dimensi=DIMENSI_UJI),
            indeks_tujuan=IndeksTujuan.UTAMA,
            versi_indeks=VERSI_UJI,
        )
    )

    hasil = jalankan(sumber.cari(KORPUS[0].teks, batas=5))
    assert hasil.peringkat[0].id_segmen == sasaran.id_segmen


def test_versi_penyemat_terbawa_pada_hasil() -> None:
    """**R-06, C-09.** Versi model tercatat pada keluaran percobaan.

    Sebelum bidang ini ada, `Penyemat.versi` hanya muncul pada satu pesan
    galat — mutasi M-7 tidak dapat dipasang sama sekali, sebab tidak ada
    keluaran yang membawanya.
    """
    hasil = jalankan(_sumber_terisi().cari(KORPUS[0].teks, batas=5))
    assert hasil.versi_penyemat == PenyematTiruan(dimensi=DIMENSI_UJI).versi


def test_sumber_tanpa_penyemat_membiarkan_versinya_kosong() -> None:
    """`None` berarti sumber ini tidak memakai model penyemat — bukan bahwa
    versinya tidak diketahui. BM25 tidak boleh mengarang versi agar bidangnya
    terisi."""
    hasil = jalankan(SumberTiruan("bm25", {"SEG-A": 1.0}).cari("kueri", batas=5))
    assert hasil.versi_penyemat is None


# ── TK-64: pencarian berjalan dengan peran produksi ─────────────────


class SambunganPemanggilLlm(SambunganUji):
    """Menyambung sebagai `peran_pemanggil_llm` — peran jalur yang menjawab."""

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg
        from tests.peladen import HOST, PORT

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user="peran_pemanggil_llm", database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()


def test_pencarian_berjalan_dengan_peran_pemanggil_llm() -> None:
    """**TK-64 — uji yang semestinya ada sejak fitur 019.**

    Seluruh uji sumber vektor tersambung sebagai pengelola, peran yang boleh
    segalanya. Pada peran produksi, pencarian gagal dengan
    `type "vector" does not exist`, sebab ekstensi terpasang di skema `public`
    yang haknya dicabut dari semua orang. Fitur 019 lolos Gerbang 4 dengan
    cacat itu, dan ia ditemukan bukan oleh uji fitur 019 melainkan saat
    membuat peran penyematan pada TK-63.

    Uji yang tersambung sebagai peran paling berkuasa membuktikan kueri benar,
    bukan membuktikan sistem dapat menjalankannya.
    """
    _isi_korpus(PenyematTiruan(dimensi=DIMENSI_UJI))
    sumber = jalankan(
        SumberVektor.susun(
            sambungan=SambunganPemanggilLlm(),
            penyemat=PenyematTiruan(dimensi=DIMENSI_UJI),
            indeks_tujuan=IndeksTujuan.UTAMA,
            versi_indeks=VERSI_UJI,
        )
    )
    hasil = jalankan(sumber.cari(KORPUS[0].teks, batas=5))
    assert hasil.peringkat[0].id_segmen == KORPUS[0].id_segmen
