"""Uji pemantauan antrean dan pengereman — C-1 fitur 010, R-11, R-12, FR-I08.

Dokumen: D-06 Bagian 8.3.

**Diuji dari kedua arah.** "Melampaui → direm" lulus juga pada implementasi
yang mengerem pada hari pertama, dan pengereman yang terlalu cepat menurunkan
frekuensi K-C setiap kali antrean naik sehari — lalu feed kekurangan isi dan
titik kritis T5 pada D-02 menyala. Karena itu uji yang menegakkan aturannya
adalah **uji dua hari yang tidak mengerem**, bukan uji tiga hari yang mengerem.
"""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.ingest.kanal import Kanal
from src.ingest.kurasi.antrean import GalatAntrean, HasilPantauan, pantau
from src.ingest.kurasi.tetapan import (
    HARI_BERTURUT_SEBELUM_PENGEREMAN,
    PAGU_KURASI_HARIAN,
    PENGALI_AMBANG_ANTREAN,
)

AKAR = Path(__file__).resolve().parents[3]

AMBANG = PAGU_KURASI_HARIAN * PENGALI_AMBANG_ANTREAN
MELAMPAUI = AMBANG + 1
AMAN = AMBANG - 1


# ------------------------------------------------------ R-11 · tiga hari, bukan satu


def test_dua_hari_melampaui_tidak_mengerem() -> None:
    """**Uji terpenting berkas ini**, dan ia menuntut sesuatu **tidak** terjadi.

    Implementasi yang mengerem pada hari pertama lulus setiap uji yang hanya
    menanyakan "apakah antrean yang melampaui ambang direm". Yang
    membedakannya hanya uji ini.
    """
    hasil = pantau([MELAMPAUI, MELAMPAUI])
    assert not hasil.mengerem
    assert hasil.hari_berturut_melampaui == 2


def test_tiga_hari_melampaui_mengerem() -> None:
    hasil = pantau([MELAMPAUI] * HARI_BERTURUT_SEBELUM_PENGEREMAN)
    assert hasil.mengerem


def test_satu_hari_melampaui_tidak_mengerem() -> None:
    assert not pantau([MELAMPAUI]).mengerem


def test_hitungan_berturut_terputus_oleh_hari_yang_aman() -> None:
    """ "Berturut-turut", bukan "tiga kali".

    Antrean yang melampaui pada Senin, turun Selasa, lalu melampaui Rabu dan
    Kamis belum menumpuk — ia berayun. Mengeremnya akan menurunkan frekuensi
    K-C atas dasar tiga hari yang tidak bersambung.
    """
    hasil = pantau([MELAMPAUI, MELAMPAUI, AMAN, MELAMPAUI, MELAMPAUI])
    assert hasil.hari_berturut_melampaui == 2
    assert not hasil.mengerem


def test_hitungan_dibaca_dari_hari_terakhir_bukan_terpanjang() -> None:
    """Rentetan terpanjang yang sudah berakhir bukan keadaan hari ini.

    Antrean yang pernah menumpuk empat hari lalu pulih tidak sedang menumpuk,
    dan mengeremnya sekarang memakai keadaan yang sudah lewat.
    """
    hasil = pantau([MELAMPAUI] * 4 + [AMAN])
    assert hasil.hari_berturut_melampaui == 0
    assert not hasil.mengerem


def test_antrean_tepat_pada_ambang_tidak_melampaui() -> None:
    """D-06 menulis *"Antrean > 2x pagu kurasi harian"* — lebih besar, bukan
    sama dengan. Uji satu arah membiarkan penjagaannya digeser satu butir."""
    hasil = pantau([AMBANG] * HARI_BERTURUT_SEBELUM_PENGEREMAN)
    assert hasil.hari_berturut_melampaui == 0
    assert not hasil.mengerem


def test_riwayat_kosong_ditolak() -> None:
    """Pemantauan tanpa data yang melaporkan "tidak perlu mengerem" adalah
    laporan bersih yang tidak memeriksa apa pun — bentuk yang sama dengan
    pelajaran TA-01."""
    with pytest.raises(GalatAntrean):
        pantau([])


def test_panjang_antrean_negatif_ditolak() -> None:
    with pytest.raises(GalatAntrean):
        pantau([3, -1])


# ------------------------------------------------- R-11 · K-C diperlambat lebih dulu


def test_kanal_jurnal_diperlambat_lebih_dulu() -> None:
    """D-06 Bagian 8.3: *"frekuensi K-C diturunkan lebih dulu"*, dan alasannya
    tertulis — *"kanal jurnal menghasilkan volume terbesar dengan tingkat
    kelolosan terendah, sehingga pengurangannya paling sedikit merugikan."*
    """
    hasil = pantau([MELAMPAUI] * HARI_BERTURUT_SEBELUM_PENGEREMAN)
    assert hasil.kanal_diperlambat[0] is Kanal.K_C


def test_kanal_selain_jurnal_tidak_ikut_diperlambat() -> None:
    """**Pernyataan yang lebih kuat, dan ia yang D-06 dukung.**

    D-06 menyebut K-C dan berhenti di situ. Memperlambat K-A akan mengurangi
    justru kanal regulasi — kanal yang butirnya paling menentukan dan paling
    jarang, dan urutan itu tidak tertulis di dokumen mana pun.
    """
    hasil = pantau([MELAMPAUI] * HARI_BERTURUT_SEBELUM_PENGEREMAN)
    assert set(hasil.kanal_diperlambat) == {Kanal.K_C}


def test_tanpa_pengereman_tidak_ada_kanal_diperlambat() -> None:
    assert pantau([MELAMPAUI, MELAMPAUI]).kanal_diperlambat == ()


# ---------------------------------- paruh kedua pengereman belum dapat dijalankan


def test_paruh_kedua_pengereman_dinyatakan_tertahan() -> None:
    """D-06 memberi pengereman **dua** paruh: frekuensi K-C diturunkan **dan**
    ambang relevansi L4 dinaikkan.

    Paruh kedua menuntut ambang yang belum ada — D-06 Bagian 6 menyerahkannya
    ke BT-24, dan menaikkan ambang yang belum dikalibrasi adalah menyetel
    ambang yang C-16 larang. Yang dilaporkan karena itu bukan "pengereman
    berjalan" melainkan pengereman yang separuhnya tertahan, beserta apa yang
    ditunggunya.

    Laporan yang menyebut pengereman lengkap sementara separuhnya tidak
    berjalan akan membuat penanggung jawab teknis mengira antrean sudah
    ditangani.
    """
    hasil = pantau([MELAMPAUI] * HARI_BERTURUT_SEBELUM_PENGEREMAN)
    assert "BT-24" in hasil.paruh_kedua_tertahan
    assert "L4" in hasil.paruh_kedua_tertahan


def test_tidak_ada_ambang_l4_yang_disetel_modul_ini() -> None:
    """C-16. Modul yang menaikkan ambang menyimpan nilai ambang, dan nilai
    ambang yang belum dikalibrasi tidak boleh ada di mana pun."""
    isi = (AKAR / "src" / "ingest" / "kurasi" / "antrean.py").read_text(encoding="utf-8")
    for terlarang in ("AMBANG_RELEVANSI", "ambang_relevansi", "AMBANG_L4"):
        assert terlarang not in isi


# --------------------------------------------- R-12 · angka dibaca dari D-06 8.3


def test_ambang_dihitung_dari_pagu_bukan_ditulis_ulang() -> None:
    """D-06 menyatakannya sebagai kelipatan pagu harian, bukan sebagai angka
    30. Menuliskannya sebagai 30 akan membuatnya diam-diam salah pada hari
    kapasitas kurator berubah."""
    hasil = pantau([MELAMPAUI])
    assert hasil.ambang == PAGU_KURASI_HARIAN * PENGALI_AMBANG_ANTREAN


def test_angka_pengereman_dibaca_dari_d06() -> None:
    """Sumbernya, bukan salinannya — sama dengan uji tetapan pada A-2."""
    teks = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")
    baris = next(g for g in teks.splitlines() if g.startswith("| Tindakan bila melampaui"))
    cocok = re.search(r"(\d+) hari berturut-turut", baris)
    assert cocok is not None
    assert int(cocok.group(1)) == HARI_BERTURUT_SEBELUM_PENGEREMAN
    assert "K-C" in baris


def test_hasil_pantauan_membawa_pagu_yang_dipakainya() -> None:
    """Laporan yang menyebut "melampaui ambang" tanpa menyebut ambangnya tidak
    dapat ditinjau ulang ketika pagunya berubah."""
    hasil = pantau([MELAMPAUI])
    assert hasil.pagu_harian == PAGU_KURASI_HARIAN
    assert hasil.panjang_antrean == MELAMPAUI


def test_hasil_pantauan_beku() -> None:
    with pytest.raises(ValidationError):
        pantau([MELAMPAUI]).mengerem = True  # type: ignore[misc]


def test_mengerem_sifat_terhitung_bukan_bidang() -> None:
    """Bidang dapat diisi `False` oleh pemanggil yang lelah, dan pengereman yang
    dimatikan sekali tidak akan pernah menyala lagi."""
    assert "mengerem" not in HasilPantauan.model_fields
