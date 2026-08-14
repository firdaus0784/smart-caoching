"""Uji penggabungan peringkat — B-3 fitur 007, R-04, R-05, R-06.

**Tugas terpenting fitur ini**, dan alasannya bukan kerumitan rumusnya.

*Reciprocal Rank Fusion* atas **satu** daftar mengembalikan daftar itu —
urutan yang sama, tanpa galat, dengan nama fungsi yang tetap berbunyi
`gabung_peringkat`, dan seluruh uji tetap hijau. ADR-03 menolak "leksikal
saja" secara tegas: *"gagal pada parafrase pengguna."* Sistem yang berjalan
dengan satu sumber karena itu **wajib berhenti**, bukan diam-diam menjadi
mesin pencari kata kunci.

Bentuk kegagalannya sama persis dengan TA-01: laporan bersih yang tidak
memeriksa apa pun.

Dua kebutuhan menutupnya **bersama**. R-05 menolak penggabungan berkurang dari
dua sumber; R-06 menuntut setiap hasil membawa daftar penyumbangnya.
Masing-masing sendirian bocor — penolakan sendirian dapat dipuaskan pelaksana
kosong, penyumbang sendirian hanya melaporkan tanpa menahan.
"""

import pytest
from src.rag.pengambilan.gabung import gabung_peringkat
from src.rag.pengambilan.kandidat import HasilSumber, Kandidat
from src.rag.pengambilan.tetapan import TETAPAN_RRF_K
from tests.rag.pengambilan.sumber_tiruan import SumberTiruan


def _daftar(nama: str, *id_segmen: str) -> HasilSumber:
    """Daftar berperingkat dengan skor menurun yang sudah rapi.

    Skornya tidak dipakai RRF sama sekali — RRF bekerja atas peringkat. Itu
    justru sifat yang diuji di bawah.
    """
    return HasilSumber(
        nama_sumber=nama,
        versi_indeks="v1",
        peringkat=tuple(
            Kandidat(id_segmen=s, skor=float(len(id_segmen) - i)) for i, s in enumerate(id_segmen)
        ),
    )


# ------------------------------------------------------------ R-05, penolakan


def test_satu_sumber_ditolak() -> None:
    """**Uji terpenting berkas ini.**

    Bukan karena hasilnya salah — hasilnya justru "benar": daftar yang sama,
    terurut sama. Itulah masalahnya. ADR-03 menolak pengambilan leksikal saja,
    dan sistem yang menjalankannya tidak akan terlihat berbeda dari sistem
    yang benar.
    """
    with pytest.raises(ValueError) as galat:
        gabung_peringkat([_daftar("bm25", "SEG-A", "SEG-B")])
    pesan = str(galat.value)
    assert "dua" in pesan.lower() or "2" in pesan
    assert "ADR-03" in pesan


def test_tanpa_sumber_sama_sekali_ditolak() -> None:
    with pytest.raises(ValueError):
        gabung_peringkat([])


def test_dua_sumber_bernama_sama_ditolak() -> None:
    """Dua daftar dengan nama sumber yang sama memenuhi hitungan dua tanpa
    memenuhi maksudnya.

    Ia juga merusak R-06: daftar penyumbang menyebut `bm25` dua kali, dan
    pembacanya menyimpulkan dua jenis pengambilan menyetujui segmen itu.
    """
    with pytest.raises(ValueError, match="nama sumber"):
        gabung_peringkat([_daftar("bm25", "SEG-A"), _daftar("bm25", "SEG-B")])


def test_sumber_yang_tidak_menemukan_apa_pun_tetap_terhitung() -> None:
    """Daftar kosong adalah hasil pencarian yang sah — sumber itu **mencari**.

    Menolaknya akan membuat setiap kueri yang hanya cocok pada satu sisi gagal
    seluruhnya, dan kueri semacam itu justru yang ADR-03 tuju: nomor regulasi
    ditemukan leksikal dan tidak ditemukan vektor.
    """
    hasil = gabung_peringkat([_daftar("bm25", "SEG-A"), _daftar("vektor")])
    assert [h.id_segmen for h in hasil] == ["SEG-A"]
    assert [p.nama_sumber for p in hasil[0].penyumbang] == ["bm25"]


# ------------------------------------------------ R-04, skor dihitung tangan


def test_skor_rrf_terhadap_contoh_yang_dihitung_tangan() -> None:
    """**Contoh yang membalik urutan kedua sumber** — dituntut `tasks.md`.

    ```
    bm25   : SEG-A(1)  SEG-B(2)  SEG-C(3)
    vektor : SEG-C(1)  SEG-B(2)  SEG-X(3)

    k = 60,  skor = Σ 1 / (k + peringkat)

    SEG-A =        1/61                = 0,0163934
    SEG-B =        1/62 + 1/62         = 0,0322581
    SEG-C =        1/63 + 1/61         = 0,0322664
    SEG-X =        1/63                = 0,0158730
    ```

    **SEG-A jatuh dari peringkat pertama menjadi ketiga.** Ia teratas pada
    BM25 dan tidak ditemukan sama sekali oleh sumber kedua; SEG-B yang kedua
    pada **keduanya** melampauinya hampir dua kali lipat.

    Itu perilaku yang ADR-03 tuju, dan penggabungan yang tidak pernah membalik
    apa pun tidak dapat dibedakan dari penggabungan yang salah.
    """
    hasil = gabung_peringkat(
        [
            _daftar("bm25", "SEG-A", "SEG-B", "SEG-C"),
            _daftar("vektor", "SEG-C", "SEG-B", "SEG-X"),
        ]
    )

    assert [h.id_segmen for h in hasil] == ["SEG-C", "SEG-B", "SEG-A", "SEG-X"]

    skor = {h.id_segmen: h.skor for h in hasil}
    assert skor["SEG-A"] == pytest.approx(1 / 61)
    assert skor["SEG-B"] == pytest.approx(1 / 62 + 1 / 62)
    assert skor["SEG-C"] == pytest.approx(1 / 63 + 1 / 61)
    assert skor["SEG-X"] == pytest.approx(1 / 63)

    assert skor["SEG-B"] == pytest.approx(0.0322581, abs=1e-7)
    assert skor["SEG-A"] == pytest.approx(0.0163934, abs=1e-7)


def test_penyebut_memuat_k_bukan_peringkat_saja() -> None:
    """Mutasi M-2: `1/peringkat` alih-alih `1/(k + peringkat)`.

    Tanpa `k`, peringkat pertama menyumbang 1,0 dan peringkat kedua 0,5 — jarak
    yang begitu lebar sehingga segmen teratas satu sumber tidak pernah dapat
    disusul segmen yang disetujui kedua sumber. Penggabungannya berjalan dan
    tidak pernah menggabungkan apa pun.
    """
    hasil = gabung_peringkat([_daftar("bm25", "SEG-A"), _daftar("vektor", "SEG-B")])
    assert hasil[0].skor == pytest.approx(1 / (TETAPAN_RRF_K + 1))
    assert hasil[0].skor < 0.02


def test_skor_sumber_tidak_ikut_masuk_perhitungan() -> None:
    """RRF bekerja atas **peringkat**, bukan atas skor — itu alasan D-07
    Bagian 4.4 memilihnya: "Tidak memerlukan penyetelan bobot manual."

    Skor BM25 dan skor kemiripan vektor tidak sebanding; menjumlahkannya
    langsung akan membuat sisi yang kebetulan berskala lebih besar selalu
    menang.
    """
    kecil = HasilSumber(
        nama_sumber="bm25",
        versi_indeks="v1",
        peringkat=(Kandidat(id_segmen="SEG-A", skor=0.001),),
    )
    besar = HasilSumber(
        nama_sumber="vektor",
        versi_indeks="v1",
        peringkat=(Kandidat(id_segmen="SEG-B", skor=999.0),),
    )
    hasil = gabung_peringkat([kecil, besar])
    assert hasil[0].skor == pytest.approx(hasil[1].skor)


# ------------------------------------------------------------ R-06, penyumbang


def test_setiap_hasil_membawa_penyumbangnya() -> None:
    """**R-06.** Tanpa daftar penyumbang, tidak ada cara membedakan segmen yang
    ditemukan **kedua** sumber dari segmen yang ditemukan satu sumber pada
    peringkat tinggi — padahal perbedaan itulah yang membuat RRF berguna, dan
    ia pula yang akan dibaca saat BT-29 mengalibrasi.
    """
    hasil = gabung_peringkat([_daftar("bm25", "SEG-A", "SEG-B"), _daftar("vektor", "SEG-B")])
    menurut_id = {h.id_segmen: h for h in hasil}

    assert [(p.nama_sumber, p.peringkat) for p in menurut_id["SEG-B"].penyumbang] == [
        ("bm25", 2),
        ("vektor", 1),
    ]
    assert [(p.nama_sumber, p.peringkat) for p in menurut_id["SEG-A"].penyumbang] == [("bm25", 1)]


def test_penyumbang_terurut_nama_sumber() -> None:
    """Urutan tetap, sehingga daftar penyumbang dapat dibandingkan langsung
    pada uji dan pada catatan percobaan D-10."""
    hasil = gabung_peringkat([_daftar("vektor", "SEG-A"), _daftar("bm25", "SEG-A")])
    assert [p.nama_sumber for p in hasil[0].penyumbang] == ["bm25", "vektor"]


def test_penyumbang_tidak_pernah_kosong() -> None:
    """Hasil gabungan tanpa penyumbang adalah segmen yang tidak ditemukan
    sumber mana pun — ia tidak boleh ada pada keluaran sama sekali."""
    hasil = gabung_peringkat([_daftar("bm25", "SEG-A", "SEG-B"), _daftar("vektor", "SEG-C")])
    assert all(h.penyumbang for h in hasil)


def test_jumlah_penyumbang_tidak_melampaui_jumlah_sumber() -> None:
    hasil = gabung_peringkat([_daftar("bm25", "SEG-A"), _daftar("vektor", "SEG-A")])
    assert len(hasil[0].penyumbang) == 2


# ----------------------------------------------------------------- seri, R-03


def test_seri_diputus_id_segmen() -> None:
    """Dua segmen berperingkat sama pada sumber berbeda menghasilkan skor RRF
    yang **persis** sama. Pada penggabungan, seri jauh lebih sering daripada
    pada BM25 — skornya hanya bergantung pada peringkat, dan peringkat berupa
    bilangan bulat kecil."""
    hasil = gabung_peringkat([_daftar("bm25", "SEG-Q"), _daftar("vektor", "SEG-P")])
    assert [h.id_segmen for h in hasil] == ["SEG-P", "SEG-Q"]
    assert hasil[0].skor == pytest.approx(hasil[1].skor)


def test_urutan_masukan_tidak_mengubah_hasil() -> None:
    """Sifat: menukar urutan daftar sumber tidak mengubah keluaran."""
    a = _daftar("bm25", "SEG-A", "SEG-B")
    b = _daftar("vektor", "SEG-B", "SEG-C")
    assert gabung_peringkat([a, b]) == gabung_peringkat([b, a])


# ------------------------------------------------------ tiruan sebagai sumber


def test_bekerja_atas_hasil_sumber_sungguhan() -> None:
    """Digabung dari dua `SumberKandidat`, bukan dari daftar yang disusun
    tangan — memastikan bentuk `HasilSumber` yang dihasilkan sumber sungguhan
    memang yang diterima penggabungan."""
    leksikal = SumberTiruan("bm25", {"SEG-A": 3.0, "SEG-B": 1.0})
    semantik = SumberTiruan("vektor", {"SEG-B": 5.0})
    hasil = gabung_peringkat([leksikal.cari("q", batas=10), semantik.cari("q", batas=10)])
    assert [h.id_segmen for h in hasil] == ["SEG-B", "SEG-A"]
