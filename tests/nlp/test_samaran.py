"""Uji penyamaran enam pengenal berpola — T-3 fitur 037, FR-B04, P-5 A, KM-03.

Teks asli tidak tersimpan di mana pun; yang tersimpan teks bertoken D-03 dan
jumlah samaran per jenis, tanpa nilainya. Nama dan alamat tidak tersamarkan
sampai model NER ada (BT-70).

Seluruh nomor pada berkas ini dibuat-buat: berpola benar, berangka berulang,
bukan pengenal siapa pun.
"""

import re
from pathlib import Path

import pytest
from src.nlp.anonimisasi.pola import JENIS, Temuan
from src.nlp.anonimisasi.samaran import TOKEN, samarkan

AKAR = Path(__file__).resolve().parents[2]

CONTOH = {
    "nik": ("NIK 3211019999999999 tercatat.", "NIK [NIK] tercatat."),
    "nip": ("NIP 199901019999019999 pada kop.", "NIP [NIP] pada kop."),
    "nisn": ("NISN 0099999999 milik siswa.", "NISN [NISN] milik siswa."),
    "nuptk": ("NUPTK 1234999999999999 hadir.", "NUPTK [NUPTK] hadir."),
    "telepon": ("Hubungi 0812-9999-9999 segera.", "Hubungi [TELEPON] segera."),
    "rekening": ("Rekening 9999999999 bank.", "Rekening [REKENING] bank."),
}


@pytest.mark.parametrize("jenis", JENIS)
def test_tiap_jenis_diganti_tokennya(jenis: str) -> None:
    asli, harapan = CONTOH[jenis]
    hasil = samarkan(asli)
    assert hasil.teks == harapan
    assert hasil.jumlah[jenis] == 1


def test_token_mengikuti_daftar_d03() -> None:
    """Token dibaca dari D-03, bukan dipercaya: token yang tidak dikenal
    pedoman anotasi akan dianotasi sebagai isi."""
    d03 = (AKAR / "docs" / "D03.md").read_text(encoding="utf-8")
    (baris,) = [b for b in d03.splitlines() if b.startswith("`[NAMA]`")]
    assert set(TOKEN.values()) <= set(re.findall(r"`(\[[A-Z_]+\])`", baris))
    assert set(TOKEN) == set(JENIS)


def test_beberapa_temuan_berurutan_dan_teks_di_antaranya_utuh() -> None:
    """Penggantian dari akhir ke awal: rentang yang lebih awal tidak bergeser."""
    asli = "NIK 3211019999999999, telepon 0812-9999-9999, NIP 199901019999019999."
    hasil = samarkan(asli)
    assert hasil.teks == "NIK [NIK], telepon [TELEPON], NIP [NIP]."
    assert hasil.jumlah == {
        "nik": 1,
        "nip": 1,
        "nisn": 0,
        "nuptk": 0,
        "telepon": 1,
        "rekening": 0,
    }


def test_tanpa_temuan_teks_tetap_dan_jumlah_nol() -> None:
    asli = "Kepala sekolah menugaskan wakil kurikulum menyusun jadwal supervisi."
    hasil = samarkan(asli)
    assert hasil.teks == asli
    assert hasil.jumlah == dict.fromkeys(JENIS, 0)


def test_tidak_satu_digit_pengenal_tersisa() -> None:
    asli = " ".join(a for a, _ in CONTOH.values())
    hasil = samarkan(asli)
    assert not re.search(r"\d{6,}", hasil.teks), hasil.teks
    assert sum(hasil.jumlah.values()) == len(JENIS)


def test_jumlah_tidak_memuat_nilai() -> None:
    """KM-03: keenam kunci, bilangan cacah — bentuk yang sama dengan batasan
    `penerimaan.samaran` peladen."""
    hasil = samarkan(CONTOH["nik"][0])
    assert list(hasil.jumlah) == list(JENIS)
    assert all(isinstance(n, int) and n >= 0 for n in hasil.jumlah.values())


def test_rentang_bertindih_digabung_dengan_jenis_yang_lebih_dulu() -> None:
    """Pendeteksi fitur 015 tidak menghasilkan rentang bertindih; penyamar
    tetap tidak memercayainya. Rentang yang bertindih menjadi satu token, dan
    tidak sepotong pun nilai tertinggal di antara dua token."""
    teks = "nomor 1234567890123 akhir"

    def pendeteksi(_: str) -> list[Temuan]:
        return [Temuan("nik", 6, 15), Temuan("rekening", 10, 19)]

    hasil = samarkan(teks, pendeteksi=pendeteksi)
    assert hasil.teks == "nomor [NIK] akhir"
    assert hasil.jumlah["nik"] == 1
    assert hasil.jumlah["rekening"] == 0


def test_jenis_asing_dari_pendeteksi_ditolak() -> None:
    """Jenis di luar keenam tidak memiliki token; menyamarkannya dengan token
    karangan sama buruknya dengan membiarkannya."""

    def pendeteksi(_: str) -> list[Temuan]:
        return [Temuan("paspor", 0, 3)]

    with pytest.raises(ValueError):
        samarkan("abc def", pendeteksi=pendeteksi)
