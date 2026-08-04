"""Uji bentuk galat — R-09, C-13, `docs/D14.md` Bagian 4.2.

Bentuk galat adalah satu-satunya bagian D-14 yang sudah diwujudkan pada fitur
001. Ia dipakai ulang oleh keadaan KL-D pada layar (`docs/D05.md` Bagian 7)
ketika fitur 013 tiba, sehingga bentuknya ditetapkan sekarang agar tidak
diterjemahkan ulang.

Dua aturan yang mudah dilanggar tanpa disadari: pesan pengguna tidak boleh
memuat rincian teknis, dan tidak boleh melebihi dua puluh kata per kalimat
(NFR-19, C-13). Rincian teknis hanya ke log.
"""

import pytest
from pydantic import ValidationError
from src.llm.galat import (
    KODE_GALAT_D14,
    GalatLayananModel,
    KodeGalat,
    TanggapanGalat,
    kalimat_terlalu_panjang,
)


def test_seluruh_kode_galat_d14_ada() -> None:
    """`docs/D14.md` Bagian 4.2 — tujuh kode, tidak kurang."""
    assert {k.value for k in KodeGalat} == KODE_GALAT_D14


def test_pesan_pengguna_paling_banyak_dua_puluh_kata() -> None:
    """C-13, NFR-19."""
    galat = GalatLayananModel(sebab=RuntimeError("connection reset by peer"))
    for kalimat in galat.tanggapan().galat.pesan_pengguna.split("."):
        if kalimat.strip():
            assert len(kalimat.split()) <= 20, f"kalimat lebih dari 20 kata: {kalimat!r}"


def test_pesan_pengguna_tanpa_rincian_teknis() -> None:
    sebab = RuntimeError("HTTP 503 from api.penyedia.example: connection reset")
    pesan = GalatLayananModel(sebab=sebab).tanggapan().galat.pesan_pengguna
    for bocor in ("HTTP", "503", "api.penyedia.example", "connection reset", "RuntimeError"):
        assert bocor not in pesan, f"rincian teknis bocor ke pesan pengguna: {bocor!r}"


def test_sebab_asli_tetap_tersedia_untuk_log() -> None:
    """Menyembunyikan dari pengguna bukan berarti membuang."""
    sebab = RuntimeError("HTTP 503")
    galat = GalatLayananModel(sebab=sebab)
    assert galat.sebab is sebab
    assert "503" in galat.untuk_log()


def test_tanggapan_memakai_kode_layanan_model_gagal() -> None:
    tanggapan = GalatLayananModel(sebab=RuntimeError("x")).tanggapan()
    assert tanggapan.galat.kode is KodeGalat.LAYANAN_MODEL_GAGAL


def test_tanggapan_membawa_id_jejak() -> None:
    tanggapan = GalatLayananModel(sebab=RuntimeError("x")).tanggapan()
    assert tanggapan.galat.id_jejak.startswith("trc_")


def test_id_jejak_berbeda_tiap_kejadian() -> None:
    """Id jejak yang sama membuat dua insiden tidak dapat dibedakan di log."""
    a = GalatLayananModel(sebab=RuntimeError("x")).tanggapan().galat.id_jejak
    b = GalatLayananModel(sebab=RuntimeError("x")).tanggapan().galat.id_jejak
    assert a != b


def test_pesan_pengguna_panjang_ditolak_saat_dibentuk() -> None:
    """C-13 ditegakkan pada tipenya, bukan pada kehati-hatian penulis."""
    panjang = " ".join(["kata"] * 25)
    with pytest.raises(ValidationError):
        TanggapanGalat.susun(KodeGalat.GALAT_INTERNAL, panjang, "trc_1")


def test_pengukur_kalimat_menemukan_yang_melebihi_ambang() -> None:
    terlalu = " ".join(["kata"] * 21) + ". Pendek saja."
    assert len(kalimat_terlalu_panjang(terlalu)) == 1


def test_pengukur_kalimat_melewatkan_yang_pendek() -> None:
    assert kalimat_terlalu_panjang("Pendek saja. Ini juga pendek.") == []
