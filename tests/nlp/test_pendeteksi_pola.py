"""Uji pendeteksi data pribadi berpola — E-1 fitur 015, R-09, C-10.

Enam pengenal berpola tetap: NIK, NIP, NISN, NUPTK, nomor telepon, nomor
rekening. Nama perorangan dan alamat **tidak** termasuk — keduanya menunggu
model NER fitur 004 (BT-70).

Seluruh nomor pada berkas ini dibuat-buat: berpola benar, berangka berulang,
bukan pengenal siapa pun.
"""

import pytest
from src.nlp.anonimisasi.pola import JENIS, periksa_data_pribadi

BERSIH = "Kepala sekolah menugaskan wakil kurikulum menyusun jadwal supervisi."


def _jenis(teks: str) -> list[str]:
    return [t.jenis for t in periksa_data_pribadi(teks)]


def test_teks_biasa_tidak_menghasilkan_temuan() -> None:
    """Penjagaan yang menyala pada teks biasa akan dimatikan orang."""
    assert periksa_data_pribadi(BERSIH) == []


def test_nik_tertangkap() -> None:
    assert "nik" in _jenis("NIK 3211019999999999 tercatat pada berkas.")


def test_nip_tertangkap() -> None:
    assert "nip" in _jenis("NIP 199901019999019999 pada kop surat.")


def test_nisn_tertangkap() -> None:
    assert "nisn" in _jenis("NISN 0099999999 milik peserta didik.")


def test_nuptk_tertangkap() -> None:
    assert "nuptk" in _jenis("NUPTK 1234999999999999 pada daftar hadir.")


def test_nomor_telepon_tertangkap() -> None:
    for teks in ("081299999999", "+6281299999999", "0812-9999-9999"):
        assert "telepon" in _jenis(f"hubungi {teks} bila perlu"), teks


def test_nomor_rekening_tertangkap() -> None:
    assert "rekening" in _jenis("Rekening 1234567890 atas nama bendahara.")


@pytest.mark.parametrize("teks", ["tahun 2026", "pukul 07.30", "Rp12.000.000", "kelas 6A"])
def test_angka_biasa_tidak_tertangkap(teks: str) -> None:
    """Salah tangkap membebani verifikator, dan verifikator yang dibebani
    temuan palsu berhenti membaca temuan."""
    assert periksa_data_pribadi(teks) == []


def test_rentang_menunjuk_nilai_yang_dideteksi() -> None:
    """**Sifat terpenting berkas ini** — C-10.

    Rentang yang meleset akan menyamarkan karakter yang salah pada tahap
    penyamaran, dan yang tersamarkan keliru berarti dua kerugian sekaligus:
    data pribadi tetap terbaca, dan kata biasa menjadi rusak.
    """
    teks = "NIK 3211019999999999 dan telepon 081299999999 pada lampiran."
    for t in periksa_data_pribadi(teks):
        assert len(teks[t.mulai : t.akhir]) == t.akhir - t.mulai
        assert teks[t.mulai : t.akhir].strip()


def test_seluruh_kemunculan_dilaporkan_bukan_yang_pertama() -> None:
    """Melaporkan satu temuan menyembunyikan luasnya, dan verifikator
    memutuskan dari luasnya."""
    teks = "NIK 3211019999999999 dan NIK 3211018888888888."
    assert len(periksa_data_pribadi(teks)) == 2


def test_temuan_terurut_menurut_letak() -> None:
    teks = "telepon 081299999999 lalu NIK 3211019999999999"
    temuan = periksa_data_pribadi(teks)
    assert [t.mulai for t in temuan] == sorted(t.mulai for t in temuan)


def test_jenis_yang_dilaporkan_ada_pada_daftar() -> None:
    """Jenis bebas-untai akan berbeda ejaan pada tiap pemakainya."""
    teks = "NIK 3211019999999999, telepon 081299999999, NISN 0099999999"
    assert all(t.jenis in JENIS for t in periksa_data_pribadi(teks))


def test_enam_jenis_persis_sesuai_keputusan_gerbang() -> None:
    """Jumlahnya bukan kebetulan: KB-017 menetapkan enam pengenal berpola
    tetap, dan nama serta alamat sengaja di luar."""
    assert set(JENIS) == {"nik", "nip", "nisn", "nuptk", "telepon", "rekening"}


def test_temuan_beku() -> None:
    import dataclasses

    temuan = periksa_data_pribadi("NIK 3211019999999999")[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        temuan.jenis = "lain"  # type: ignore[misc]


def test_nama_orang_memang_tidak_tertangkap() -> None:
    """Dinyatakan sebagai uji, bukan hanya sebagai catatan.

    Bila kelak seseorang menambahkan kamus nama tanpa melewati gerbang, uji
    ini yang berubah warna — dan perubahannya menuntut penjelasan.
    """
    assert periksa_data_pribadi("Dra. Siti Aminah memimpin rapat pleno.") == []


def test_label_menang_atas_panjang() -> None:
    """Deret sepuluh digit berlabel NISN dilaporkan sebagai NISN, bukan
    rekening — meski panjangnya menebak rekening."""
    assert _jenis("NISN 0099999999 milik peserta didik") == ["nisn"]
    assert _jenis("Rekening 0099999999 atas nama bendahara") == ["rekening"]


def test_deret_tanpa_label_dan_tanpa_panjang_dikenal_tidak_dilaporkan() -> None:
    """Lebih baik tidak melaporkan daripada melaporkan jenis yang dikarang.

    Temuan yang tidak dapat dipertanggungjawabkan membuat verifikator berhenti
    mempercayai seluruh laporan — dan itu kerugian yang lebih besar daripada
    satu deret yang terlewat.
    """
    assert periksa_data_pribadi("kode arsip 123456789012 pada rak") == []


def test_satu_nomor_menghasilkan_satu_temuan() -> None:
    """NIP berdigit 18 tidak boleh dilaporkan dua kali dengan dua jenis.

    Verifikator yang melihat dua temuan pada satu angka akan mengira ada dua
    nomor, dan ia akan mencari yang kedua.
    """
    assert len(periksa_data_pribadi("NIP 199901019999019999 tercatat")) == 1
