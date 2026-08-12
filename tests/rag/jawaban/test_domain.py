"""Uji pemeriksaan cakupan domain — A-1 fitur 009, R-02, R-03, FR-F13.

D-07 Bagian 4.1 menetapkan tahap 1: pertanyaan di luar manajemen sekolah dasar
ditolak **sebelum mencapai pengambilan**, dan *"tidak dikirim ke LLM sama
sekali"*.

**Uji yang paling mudah keliru ada di berkas ini, dan ia yang pertama.**
"Pertanyaan medis ditolak" dipenuhi juga oleh penyaring yang menolak setiap
pertanyaan yang menyebut "kesehatan" — dan *"bagaimana mengelola program
kesehatan sekolah"* adalah pertanyaan manajerial yang sepenuhnya sah.

D-02 titik kritis T1: jawaban pertama menentukan retensi. Kepala sekolah yang
pertanyaan sahnya ditolak tidak bertanya kedua kalinya.

## Arahnya berlawanan dengan fitur 006, dan itu disengaja

Fitur 006 memilih daftar putih bagi lisensi sebab kekeliruan ke arah longgar
**menggugurkan publikasi**. Di sini kekeliruan ke arah ketat **menolak kepala
sekolah yang bertanya wajar**, sedangkan kekeliruan ke arah longgar berbiaya
satu panggilan yang berakhir tidak-ditemukan. Arah konservatifnya berlawanan
karena kerugiannya berlawanan.
"""

import pytest
from src.rag.jawaban.domain import RANAH_TERLARANG, di_luar_domain


@pytest.mark.parametrize(
    "pertanyaan",
    [
        "Bagaimana mengelola program kesehatan sekolah?",
        "Apa kewajiban sekolah pada Usaha Kesehatan Sekolah?",
        "Bagaimana menyusun anggaran sekolah tahun depan?",
        "Bagaimana menangani laporan perundungan antarsiswa?",
        "Apa dasar hukum pengangkatan guru penggerak?",
        "Bagaimana melaporkan dana bantuan operasional sekolah?",
        "Bagaimana menyusun tata tertib yang mencegah kekerasan?",
    ],
)
def test_pertanyaan_manajerial_yang_bersinggungan_ranah_lain_tetap_diterima(
    pertanyaan: str,
) -> None:
    """**Uji terpenting berkas ini.**

    Ketujuhnya memuat kata yang berdekatan dengan ranah terlarang — kesehatan,
    keuangan, kekerasan, hukum — dan ketujuhnya pertanyaan manajerial kepala
    sekolah dasar yang sah.

    Penyaring berkata tunggal menolak seluruhnya, lalu dimatikan orang. Yang
    mati bersamanya adalah FR-F13 seluruhnya.
    """
    assert not di_luar_domain(pertanyaan)


@pytest.mark.parametrize(
    "pertanyaan",
    [
        "Saya sering sakit kepala, obat apa yang cocok?",
        "Apa dosis paracetamol untuk demam saya?",
        "Bagaimana cara menuntut tetangga saya di pengadilan pidana?",
        "Berapa ancaman hukuman untuk pencurian motor?",
        "Bagaimana cara mengatur investasi saham pribadi saya?",
        "Kartu kredit mana yang bunganya paling rendah untuk saya?",
    ],
)
def test_ranah_terlarang_ditolak(pertanyaan: str) -> None:
    """FR-F13 menyebut medis, hukum pidana, dan keuangan pribadi.

    Ketiganya ditolak **sebelum** pengambilan, dengan dua alasan yang D-07
    Bagian 4.1 sebut: menghemat biaya, dan mencegah sistem memberi nasihat pada
    bidang yang tidak memiliki dasar rujukan sama sekali di korpusnya.
    """
    assert di_luar_domain(pertanyaan)


def test_penolakan_menyebut_cakupan_sistem_bukan_galat() -> None:
    """**R-03.** D-07 Bagian 4.1: "Penolakan disampaikan dengan menyebutkan
    cakupan sistem, bukan sebagai pesan galat."

    Pengguna yang menerima pesan galat menyimpulkan sistemnya rusak; pengguna
    yang menerima keterangan cakupan tahu apa yang dapat ditanyakannya.
    """
    from src.rag.jawaban.domain import PESAN_DI_LUAR_DOMAIN

    assert "manajemen sekolah dasar" in PESAN_DI_LUAR_DOMAIN.lower()
    for kata in ("galat", "error", "gagal", "tidak valid"):
        assert kata not in PESAN_DI_LUAR_DOMAIN.lower()


def test_pesan_penolakan_memenuhi_batas_dua_puluh_kata() -> None:
    """NFR-19 dan C-13. Ia teks yang dibaca kepala sekolah, bukan catatan
    pengembang."""
    from src.rag.jawaban.domain import PESAN_DI_LUAR_DOMAIN

    for kalimat in PESAN_DI_LUAR_DOMAIN.split("."):
        assert len(kalimat.split()) <= 20


def test_ranah_terlarang_persis_yang_disebut_fr_f13() -> None:
    """FR-F13 menyebut "medis, hukum pidana, keuangan pribadi, dan sebagainya".

    Daftarnya tertulis agar penambahan ranah menjadi keputusan yang terbaca,
    bukan satu baris yang menyelinap.
    """
    assert set(RANAH_TERLARANG) == {"medis", "hukum_pidana", "keuangan_pribadi"}


def test_kueri_kosong_bukan_di_luar_domain() -> None:
    """Kueri kosong adalah pemanggilan yang keliru, bukan pertanyaan di luar
    domain. Menyamakannya membuat pengguna yang menekan kirim tanpa mengetik
    menerima keterangan cakupan yang tidak relevan."""
    assert not di_luar_domain("")
    assert not di_luar_domain("   ")


def test_pemeriksaan_tidak_memanggil_model() -> None:
    """**Inti FR-F13.** "Tidak dikirim ke LLM sama sekali" — dan itu separuh
    alasan tahap ini ada.

    Diperiksa pada tingkat sumber: pemanggilan yang tidak dilewati satu kali
    uji tetap ada pada kodenya.
    """
    import inspect

    import src.rag.jawaban.domain as modul

    assert "src.llm" not in inspect.getsource(modul)


def test_batas_daftar_hitam_tertulis_pada_uraian() -> None:
    """Daftar hitam meloloskan yang belum pernah terlihat, dan penutupnya
    bukan pemeriksaan ini melainkan kecukupan bukti.

    Batas yang tidak tertulis akan dilupakan, lalu pemeriksaan ini akan
    dianggap lapisan tunggal — dan lapisan tunggal yang bocor tidak punya
    lapisan kedua.
    """
    import src.rag.jawaban.domain as modul

    uraian = modul.__doc__ or ""
    assert "kecukupan" in uraian.lower()
    assert "belum pernah terlihat" in uraian.lower()
