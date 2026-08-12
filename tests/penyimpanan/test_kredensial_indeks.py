"""Uji pemisahan indeks pada kredensial — B-1 fitur 006, R-04, C-02.

**Di sinilah C-02 diwujudkan, dan tempatnya bukan yang paling terduga.**

Bentuk pertama `spec.md` fitur ini menuliskan R-04 sebagai "jalur penjawaban
tidak boleh memiliki kredensial membaca `indeks_metadata`". Itu **lebih ketat
daripada C-02 dan melanggar D-14**: `docs/D14.md` Bagian 6 menetapkan
`bacaan_lanjutan` sebagai "tempat satu-satunya bagi sumber `indeks_metadata`",
sehingga jalur yang menyusun tanggapan justru wajib dapat membacanya.

Yang C-02 larang bukan membacanya melainkan **memasukkannya ke konteks yang
dikirim ke LLM**. Garis itu jatuh pada `PEMANGGIL_LLM`, bukan pada
`PENJAWABAN` — dan pembedaannya menentukan apakah blok bacaan lanjutan dapat
dibangun sama sekali.
"""

import pytest
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.kredensial_baku import (
    PEMANGGIL_LLM,
    PENJAWABAN,
    SELURUH_KREDENSIAL,
    VERIFIKASI,
)


def test_pemanggil_llm_tidak_menjangkau_indeks_metadata() -> None:
    """**Uji terpenting fitur ini, dan inti C-02.**

    Bukan tidak boleh — tidak bisa. Satu kueri yang lupa menyaring tetap tidak
    menjangkaunya, sebab yang dijaga bukan kuerinya melainkan kredensialnya.
    """
    assert not PEMANGGIL_LLM.boleh_baca_indeks(IndeksTujuan.METADATA)


def test_pemanggil_llm_menjangkau_indeks_utama() -> None:
    """Tanpa ini, pemisahan yang lulus adalah pemisahan yang melumpuhkan
    seluruh penjawaban — dan yang lumpuh akan dilonggarkan seseorang."""
    assert PEMANGGIL_LLM.boleh_baca_indeks(IndeksTujuan.UTAMA)


def test_penjawaban_menjangkau_kedua_indeks() -> None:
    """**Bukan kelonggaran, melainkan tuntutan D-14 Bagian 6.**

    `bacaan_lanjutan` adalah tempat satu-satunya bagi sumber `indeks_metadata`,
    dan jalur yang menyusun tanggapan wajib dapat membacanya. Menutupnya di
    sini akan membuat blok itu tidak dapat dibangun sama sekali — lalu
    seseorang membukanya kembali pada `PEMANGGIL_LLM` sekalian, sebab dari
    sana pemisahannya tampak sewenang-wenang.
    """
    assert PENJAWABAN.boleh_baca_indeks(IndeksTujuan.UTAMA)
    assert PENJAWABAN.boleh_baca_indeks(IndeksTujuan.METADATA)


def test_verifikasi_menjangkau_kedua_indeks() -> None:
    """Kurator menilai butir dari kedua indeks (fitur 010)."""
    assert VERIFIKASI.boleh_baca_indeks(IndeksTujuan.METADATA)


def test_bidang_indeks_wajib_pada_setiap_kredensial() -> None:
    """Sifat, bukan kasus.

    Bidang berbawaan akan diisi diam-diam oleh kredensial keempat yang
    ditambahkan kelak, dan yang paling mungkin terjadi adalah ia mewarisi
    bawaan yang longgar tanpa seorang pun memutuskannya.
    """
    assert Kredensial.model_fields["indeks"].is_required()


def test_kredensial_baru_tanpa_indeks_tidak_dapat_dibentuk() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Kredensial(  # type: ignore[call-arg]
            nama="uji", baca=frozenset(), tulis=frozenset()
        )


def test_himpunan_indeks_kosong_berarti_tidak_menjangkau_apa_pun() -> None:
    """Arah gagalnya menutup, bukan membuka.

    Kredensial yang lupa diisi tidak menjangkau indeks mana pun — bentuk yang
    sama dengan himpunan `baca` kosong pada fitur 002, dan alasan yang sama:
    kekeliruan sebaliknya adalah cara paling sunyi meruntuhkan pemisahan.
    """
    k = Kredensial(nama="uji", baca=frozenset(), tulis=frozenset(), indeks=frozenset())
    assert not k.boleh_baca_indeks(IndeksTujuan.UTAMA)
    assert not k.boleh_baca_indeks(IndeksTujuan.METADATA)


def test_tepat_satu_kredensial_baku_yang_tertutup_dari_metadata() -> None:
    """**Sifat seluruh daftar, bukan satu kredensial.**

    Kredensial keempat yang ditambahkan kelak wajib memutuskan sendiri apakah
    ia menjangkau metadata, dan uji ini menangkapnya bila jumlahnya bergeser
    tanpa keputusan.
    """
    tertutup = [k for k in SELURUH_KREDENSIAL if not k.boleh_baca_indeks(IndeksTujuan.METADATA)]
    assert [k.nama for k in tertutup] == ["pemanggil_llm"]


def test_indeks_beku() -> None:
    with pytest.raises(Exception):  # noqa: B017 — pydantic tidak menjanjikan satu tipe
        PEMANGGIL_LLM.indeks = frozenset(IndeksTujuan)  # type: ignore[misc]
