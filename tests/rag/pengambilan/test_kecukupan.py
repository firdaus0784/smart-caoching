"""Uji penilaian kecukupan bukti — C-2 fitur 007, R-11, R-12, C-16.

**Tempat C-16 dipatuhi atau dilanggar diam-diam.**

Cara paling sunyi melanggar C-16 bukan mengubah angka melainkan **menuliskan
angka awal yang tak pernah ditinjau**. Ia berjalan pada hari pertama, memberi
hasil yang masuk akal, dan tidak seorang pun kembali kepadanya — sampai angka
itu masuk naskah sebagai ambang yang "dikalibrasi".

D-07 Bagian 4.6 tidak memberi nilai bagi ambang tinggi maupun menengah; ia
menyerahkannya ke BT-29, kalibrasi terhadap *gold set* BT-35 yang baru ada
bulan 4-5.

Karena itu bentuk yang diuji di sini bukan "ambang bawaan bernilai wajar"
melainkan **ambang tidak dapat disusun tanpa catatan kalibrasi**. Bukan gagal
saat dijalankan: kegagalan saat jalan akan ditangkap seseorang dengan nilai
bawaan pada pemanggilnya.
"""

import inspect
from datetime import date

import pytest
from pydantic import ValidationError
from src.rag.pengambilan.gabung import HasilGabungan, Penyumbang
from src.rag.pengambilan.hibrida import AsalSumber, HasilPengambilan
from src.rag.pengambilan.kecukupan import (
    AmbangKecukupan,
    CatatanKalibrasi,
    PenilaianKecukupan,
    StatusDasar,
)

KALIBRASI = CatatanKalibrasi(
    tanggal=date(2026, 9, 1),
    gold_set="BT-35 v1",
    jumlah_pertanyaan=200,
    pemutus="rapat tim, BT-29",
    prosedur="D-07 BT-29",
)
"""Catatan kalibrasi **contoh**, dipakai uji saja.

Ia tidak menjadikan angka di bawah ambang yang sah — kalibrasi sungguhan
berlangsung bulan 4-5 dan hasilnya keputusan tim, bukan keputusan berkas uji.
"""


def _ambang(tinggi: float = 0.03, menengah: float = 0.02) -> AmbangKecukupan:
    return AmbangKecukupan(tinggi=tinggi, menengah=menengah, kalibrasi=KALIBRASI)


def _hasil(*skor: tuple[str, float]) -> HasilPengambilan:
    return HasilPengambilan(
        segmen=tuple(
            HasilGabungan(
                id_segmen=id_segmen,
                skor=nilai,
                penyumbang=(Penyumbang(nama_sumber="bm25", peringkat=1),),
            )
            for id_segmen, nilai in skor
        ),
        asal=(
            AsalSumber(nama_sumber="bm25", versi_indeks="v1", jumlah_kandidat=len(skor)),
            AsalSumber(nama_sumber="vektor", versi_indeks="v1", jumlah_kandidat=0),
        ),
    )


# --------------------------------------------------------------- R-11, R-12


def test_ambang_tidak_dapat_disusun_tanpa_catatan_kalibrasi() -> None:
    """**Uji terpenting fitur 007 bagi C-16.**

    Tidak gagal saat dijalankan — **tidak dapat dibentuk**. Kegagalan saat jalan
    akan ditangkap seseorang dengan nilai bawaan pada pemanggilnya, dan nilai
    bawaan itu yang kemudian tak pernah ditinjau.
    """
    with pytest.raises(ValidationError):
        AmbangKecukupan(tinggi=0.03, menengah=0.02)  # type: ignore[call-arg]


def test_ambang_tidak_punya_nilai_bawaan() -> None:
    """Sifat, bukan kasus."""
    for bidang in ("tinggi", "menengah", "kalibrasi"):
        assert AmbangKecukupan.model_fields[bidang].is_required()


def test_penilaian_tidak_dapat_disusun_tanpa_ambang() -> None:
    """`PenilaianKecukupan` menuntut ambang tepat sesudah `self`, mengikuti
    `PenyimpanDasar` fitur 002: menempatkannya di akhir daftar parameter
    membuatnya terbaca sebagai renungan belakangan."""
    with pytest.raises(TypeError):
        PenilaianKecukupan()  # type: ignore[call-arg]


def test_ambang_tidak_punya_nilai_bawaan_pada_tanda_tangan_penilaian() -> None:
    """Parameter berbawaan `None` akan berubah menjadi "tanpa ambang berarti
    tanpa batas" pada pemanggilan pertama yang lupa mengisinya — kalimat
    `kredensial.py`, dan ia berlaku sama di sini."""
    tanda = inspect.signature(PenilaianKecukupan.__init__)
    assert tanda.parameters["ambang"].default is inspect.Parameter.empty


def test_catatan_kalibrasi_wajib_menyebut_tanggal_gold_set_dan_pemutus() -> None:
    """**R-12.** Ambang tanpa asal-usul tidak dapat dibedakan dari ambang yang
    disetel seseorang, dan itu persis yang C-16 larang."""
    for bidang in ("tanggal", "gold_set", "jumlah_pertanyaan", "pemutus", "prosedur"):
        assert CatatanKalibrasi.model_fields[bidang].is_required()


def test_catatan_kalibrasi_menolak_prosedur_di_luar_bt29() -> None:
    """C-16: "Ambang tidak disetel **di luar prosedur kalibrasi** D-07 BT-29."

    Bidang prosedur yang menerima untai bebas akan diisi "penyetelan manual"
    dan tetap lolos — catatan yang mencatat pelanggaran tetap catatan yang
    lolos.
    """
    with pytest.raises(ValidationError, match="BT-29"):
        CatatanKalibrasi(
            tanggal=date(2026, 9, 1),
            gold_set="BT-35 v1",
            jumlah_pertanyaan=200,
            pemutus="saya",
            prosedur="penyetelan manual saat pilot",
        )


def test_catatan_kalibrasi_menolak_gold_set_kosong() -> None:
    with pytest.raises(ValidationError):
        CatatanKalibrasi(
            tanggal=date(2026, 9, 1),
            gold_set="  ",
            jumlah_pertanyaan=200,
            pemutus="rapat tim",
            prosedur="D-07 BT-29",
        )


def test_ambang_tinggi_wajib_di_atas_menengah() -> None:
    """Terbalik, seluruh jawaban menjadi "rujukan kuat" — termasuk yang
    seharusnya ditolak. Kekeliruannya tidak menghasilkan galat, hanya sistem
    yang jauh lebih percaya diri."""
    with pytest.raises(ValidationError, match="menengah"):
        AmbangKecukupan(tinggi=0.01, menengah=0.05, kalibrasi=KALIBRASI)


def test_ambang_tidak_dibatasi_atas_pada_satu() -> None:
    """**Batas atas 1,0 akan menjadi asumsi diam.**

    Skor RRF tidak berada pada rentang 0-1: dengan dua sumber dan k = 60,
    nilai tertingginya 2/61 ≈ 0,0328. Membatasi ambang pada 0-1 tidak salah
    hari ini, tetapi ia menyandera BT-29 pada skala yang belum diputuskan —
    kalibrasi boleh saja menormalkan skornya lebih dulu.
    """
    assert AmbangKecukupan(tinggi=5.0, menengah=1.5, kalibrasi=KALIBRASI).tinggi == 5.0


def test_ambang_nol_atau_negatif_ditolak() -> None:
    with pytest.raises(ValidationError):
        AmbangKecukupan(tinggi=0.03, menengah=0.0, kalibrasi=KALIBRASI)


# ---------------------------------------------------------- StatusDasar, AG-04


def test_empat_nilai_persis_d14() -> None:
    """`docs/D14.md` Bagian 4.1 menetapkan `status_dasar` dengan empat nilai:
    `kuat | terbatas | tidak_ditemukan | di_luar_domain`.

    AG-04 melarang agen mengubah daftar nilai enum. Fitur ini mewujudkannya
    utuh meski hanya memakai tiga — enum berisi tiga nilai akan menuntut
    penambahan nilai keempat pada fitur 009, dan penambahan nilai enum adalah
    persis yang AG-04 larang.
    """
    assert {s.value for s in StatusDasar} == {
        "kuat",
        "terbatas",
        "tidak_ditemukan",
        "di_luar_domain",
    }


def test_penilaian_tidak_pernah_menghasilkan_di_luar_domain() -> None:
    """`di_luar_domain` adalah keputusan **tahap 1** D-07 Bagian 4.1, bukan
    tahap 7. Pertanyaan di luar domain ditolak sebelum mencapai pengambilan dan
    tidak dikirim ke LLM sama sekali (FR-F13); ia fitur 009.

    Penilaian yang dapat menghasilkannya di sini akan membuat dua tempat
    memutuskan hal yang sama, dan yang kedua akan memutuskan berbeda.
    """
    penilaian = PenilaianKecukupan(_ambang())
    for hasil in (_hasil(), _hasil(("SEG-A", 0.001)), _hasil(("SEG-A", 9.0), ("SEG-B", 8.0))):
        status = penilaian.nilai(hasil, segmen_resmi=frozenset({"SEG-A"}))
        assert status is not StatusDasar.DI_LUAR_DOMAIN


# ------------------------------------------------- tiga keadaan D-07 Bagian 4.6


def test_di_bawah_ambang_menengah_tidak_ditemukan() -> None:
    """D-07 Bagian 4.6 baris ketiga → balasan tidak-ditemukan (FR-F04).

    "Jawaban yang salah lebih merugikan daripada jawaban yang tidak ada"
    (D-07 Bagian 1).
    """
    penilaian = PenilaianKecukupan(_ambang())
    hasil = _hasil(("SEG-A", 0.01), ("SEG-B", 0.005))
    assert penilaian.nilai(hasil, segmen_resmi=frozenset({"SEG-A"})) is (
        StatusDasar.TIDAK_DITEMUKAN
    )


def test_hasil_kosong_tidak_ditemukan() -> None:
    penilaian = PenilaianKecukupan(_ambang())
    assert penilaian.nilai(_hasil(), segmen_resmi=frozenset()) is StatusDasar.TIDAK_DITEMUKAN


def test_ketiga_syarat_terpenuhi_menghasilkan_kuat() -> None:
    """D-07 Bagian 4.6 baris pertama: skor teratas melampaui ambang tinggi
    **dan** minimal 2 segmen relevan **dan** minimal 1 dari regulasi atau
    panduan resmi."""
    penilaian = PenilaianKecukupan(_ambang())
    hasil = _hasil(("SEG-A", 0.05), ("SEG-B", 0.025))
    assert penilaian.nilai(hasil, segmen_resmi=frozenset({"SEG-A"})) is StatusDasar.KUAT


def test_ambang_tinggi_terlampaui_tetapi_hanya_satu_segmen_relevan() -> None:
    """Syarat kedua gagal → terbatas, bukan kuat.

    Satu segmen yang cocok sangat baik tetap satu segmen. Klaim yang bersandar
    padanya tidak dapat diperiksa silang, dan D-07 PR-05 mengutamakan ketepatan
    daripada cakupan.
    """
    penilaian = PenilaianKecukupan(_ambang())
    hasil = _hasil(("SEG-A", 0.05), ("SEG-B", 0.001))
    assert penilaian.nilai(hasil, segmen_resmi=frozenset({"SEG-A"})) is StatusDasar.TERBATAS


def test_ambang_tinggi_terlampaui_tetapi_tanpa_sumber_resmi() -> None:
    """Syarat ketiga gagal → terbatas.

    Dua artikel yang saling menguatkan bukan dasar regulasi. Kepala sekolah
    yang bertindak atasnya mengambil keputusan administratif tanpa dasar
    aturan.
    """
    penilaian = PenilaianKecukupan(_ambang())
    hasil = _hasil(("SEG-A", 0.05), ("SEG-B", 0.025))
    assert penilaian.nilai(hasil, segmen_resmi=frozenset()) is StatusDasar.TERBATAS


def test_di_antara_kedua_ambang_terbatas() -> None:
    penilaian = PenilaianKecukupan(_ambang())
    hasil = _hasil(("SEG-A", 0.025), ("SEG-B", 0.021))
    assert penilaian.nilai(hasil, segmen_resmi=frozenset({"SEG-A"})) is StatusDasar.TERBATAS


def test_tepat_pada_ambang_menengah_belum_cukup() -> None:
    """ "Melampaui", bukan "mencapai". Perbandingan `>=` menggeser garis satu
    langkah ke arah menjawab, dan D-07 Bagian 1 menetapkan arah sebaliknya."""
    penilaian = PenilaianKecukupan(_ambang(tinggi=0.03, menengah=0.02))
    hasil = _hasil(("SEG-A", 0.02), ("SEG-B", 0.02))
    assert penilaian.nilai(hasil, segmen_resmi=frozenset({"SEG-A"})) is (
        StatusDasar.TIDAK_DITEMUKAN
    )


def test_segmen_relevan_diukur_dengan_ambang_menengah_bukan_angka_baru() -> None:
    """**Penafsiran yang wajib terbaca, bukan disembunyikan.**

    D-07 Bagian 4.6 menyebut "minimal 2 segmen relevan" tanpa menetapkan apa
    yang membuat sebuah segmen relevan. Fitur ini membacanya sebagai **skor
    melampaui ambang menengah** — memakai ambang yang sudah ada alih-alih
    memperkenalkan angka ketiga yang C-16 larang.

    Penafsirannya tetap wajib dikukuhkan pada BT-29; ia tercatat pada KB-035.
    """
    penilaian = PenilaianKecukupan(_ambang(tinggi=0.03, menengah=0.02))
    assert penilaian.jumlah_relevan(_hasil(("SEG-A", 0.05), ("SEG-B", 0.021))) == 2
    assert penilaian.jumlah_relevan(_hasil(("SEG-A", 0.05), ("SEG-B", 0.019))) == 1
