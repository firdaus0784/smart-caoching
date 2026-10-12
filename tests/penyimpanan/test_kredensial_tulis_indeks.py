"""Hak tulis ke indeks — TK-62, C-02, C-17.

`Kredensial` semula hanya dapat menyatakan indeks mana yang boleh **dibaca**.
Tabel indeks tinggal pada skema `indeks_utama` dan `indeks_metadata`, bukan
pada `Area`, sehingga `boleh_tulis` tidak menjangkaunya sama sekali — dan
penjagaan jalur penyematan fitur 026 tidak dapat dinyatakan.

**Memakai `boleh_baca_indeks` sebagai penggantinya ditolak, dan berkas ini
yang membuat penolakan itu dapat diuji.** Menulis bukan membaca, dan C-17
bersandar tepat pada perbedaan tersebut: jalur penjawaban menjangkau kedua
indeks untuk dibaca, sehingga menyamakan keduanya memberinya hak tulis lewat
pintu belakang tanpa satu baris pun yang menyatakannya.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.area import Area
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.kredensial_baku import (
    PEMANGGIL_LLM,
    PENGINDEKSAN,
    PENJAWABAN,
    PENYEMATAN,
    VERIFIKASI,
)

SELURUH_BAKU = (PENJAWABAN, VERIFIKASI, PEMANGGIL_LLM, PENYEMATAN, PENGINDEKSAN)


# ── bidangnya wajib, bukan berbawaan ────────────────────────────────


def test_bidang_tulis_indeks_wajib() -> None:
    """Alasannya sudah tertulis pada uraian bidang `indeks` sejak fitur 006:
    bidang berbawaan akan diisi diam-diam oleh kredensial yang ditambahkan
    kelak, dan mewarisi bawaan yang longgar tanpa seorang pun memutuskannya."""
    assert Kredensial.model_fields["tulis_indeks"].is_required()


def test_kredensial_tanpa_tulis_indeks_tidak_dapat_dibentuk() -> None:
    with pytest.raises(ValidationError) as galat:
        Kredensial(  # type: ignore[call-arg]
            nama="uji", baca=frozenset(), tulis=frozenset(), indeks=frozenset()
        )
    hilang = [g for g in galat.value.errors() if g["type"] == "missing"]
    assert [g["loc"] for g in hilang] == [("tulis_indeks",)]


def test_himpunan_kosong_berarti_tidak_boleh_menulis_ke_mana_pun() -> None:
    """Arah gagalnya menutup, bukan membuka."""
    k = Kredensial(
        nama="uji",
        baca=frozenset(),
        tulis=frozenset(),
        indeks=frozenset({IndeksTujuan.UTAMA}),
        tulis_indeks=frozenset(),
    )
    assert not k.boleh_tulis_indeks(IndeksTujuan.UTAMA)
    assert not k.boleh_tulis_indeks(IndeksTujuan.METADATA)


# ── membaca bukan menulis — inti C-17 ───────────────────────────────


def test_membaca_indeks_tidak_memberi_hak_menulis() -> None:
    """**Sifat yang membuat TK-62 ada.**

    Kredensial yang menjangkau sebuah indeks untuk dibaca tidak dengan
    sendirinya boleh menulis ke sana. Bila keduanya pernah disamakan, jalur
    penjawaban memperoleh hak tulis tanpa satu baris pun yang menyatakannya.
    """
    k = Kredensial(
        nama="pembaca",
        baca=frozenset({Area.KORPUS}),
        tulis=frozenset(),
        indeks=frozenset({IndeksTujuan.UTAMA, IndeksTujuan.METADATA}),
        tulis_indeks=frozenset(),
    )
    assert k.boleh_baca_indeks(IndeksTujuan.UTAMA)
    assert not k.boleh_tulis_indeks(IndeksTujuan.UTAMA)


@pytest.mark.parametrize(
    "kredensial", [PENJAWABAN, VERIFIKASI, PEMANGGIL_LLM], ids=lambda k: k.nama
)
def test_tiga_kredensial_lama_menyatakan_tidak_boleh_menulis_indeks(
    kredensial: Kredensial,
) -> None:
    """**C-17 menguat, bukan melemah.**

    Ketiganya kini **menyatakan** ketiadaan hak tulis indeks, alih-alih tidak
    memilikinya karena tidak ada cara menyebutnya. Ketiadaan yang dinyatakan
    dapat diuji; ketiadaan yang kebetulan tidak.
    """
    assert kredensial.tulis_indeks == frozenset()
    for indeks in IndeksTujuan:
        assert not kredensial.boleh_tulis_indeks(indeks)


# ── kredensial keempat ──────────────────────────────────────────────


def test_penyematan_boleh_menulis_kedua_indeks() -> None:
    """Penyematan mengisi kedua indeks — R-06 fitur 026 menuntut keduanya
    disemat terpisah, bukan salah satunya saja."""
    for indeks in IndeksTujuan:
        assert PENYEMATAN.boleh_tulis_indeks(indeks)


def test_penyematan_tidak_menjangkau_karantina() -> None:
    """**C-03.** Jalur penyematan membaca korpus, tidak pernah karantina."""
    assert not PENYEMATAN.boleh_baca(Area.KARANTINA)
    assert not PENYEMATAN.boleh_tulis(Area.KARANTINA)


def test_penyematan_tidak_menulis_ke_area_mana_pun() -> None:
    """Ia menulis **vektor pada indeks**, bukan dokumen pada area. Hak tulis
    area yang ikut diberikan adalah hak yang tidak diminta siapa pun."""
    assert PENYEMATAN.tulis == frozenset()


def test_kredensial_baku_yang_boleh_menulis_indeks_persis() -> None:
    """Sifat seluruh daftar, bukan satu kredensial.

    Kredensial kelima yang ditambahkan kelak wajib memutuskan sendiri apakah
    ia boleh menulis indeks, dan uji ini yang memaksanya diputuskan alih-alih
    diwarisi. Kredensial kelima itu `PENGINDEKSAN` (fitur 038), dan
    keputusannya P-2 A — bukan warisan.
    """
    boleh = [k.nama for k in SELURUH_BAKU if k.tulis_indeks]
    assert boleh == [PENYEMATAN.nama, PENGINDEKSAN.nama], f"yang boleh menulis indeks: {boleh}"


# ── kredensial kelima — fitur 038 ───────────────────────────────────


def test_pengindeksan_membaca_korpus_dan_menulis_kedua_indeks() -> None:
    """P-2 A: membaca teks dan metadata korpus, mengganti segmen kedua indeks —
    penggantian menghapus dari keduanya, sehingga keduanya wajib."""
    assert PENGINDEKSAN.baca == frozenset({Area.KORPUS})
    assert PENGINDEKSAN.tulis_indeks == frozenset(IndeksTujuan)


def test_pengindeksan_tanpa_karantina_tanpa_tulis_area_tanpa_baca_indeks() -> None:
    """C-03: tidak menjangkau karantina. Tidak menulis dokumen pada area mana
    pun, dan tidak membaca segmen — perannya hanya memegang pengenal segmen
    untuk menghapusnya, bukan teksnya (TK-86, `16-segmen-dan-lisensi.sql`)."""
    assert not PENGINDEKSAN.boleh_baca(Area.KARANTINA)
    assert PENGINDEKSAN.tulis == frozenset()
    assert PENGINDEKSAN.indeks == frozenset()
