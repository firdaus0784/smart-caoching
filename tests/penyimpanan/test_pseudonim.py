"""Uji peta pseudonim — C-1 fitur 022, R-09, C-05, KA-03.

C-05 menuntut dua hal, dan hanya satu terbaca kode: **tidak terjangkau layanan
aplikasi**. Yang mewujudkannya bukan pemeriksaan melainkan **tipe**:
`KredensialPseudonim` bertipe tersendiri, sehingga kredensial layanan aplikasi
tidak dapat dipakaikan ke sana oleh kekeliruan pengetikan mana pun.

Yang diuji di sini karena itu sebagian besar berupa **penolakan**.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.penyimpanan.area import Area
from src.penyimpanan.kredensial_baku import PENJAWABAN, VERIFIKASI
from src.penyimpanan.pseudonim import (
    GalatPseudonim,
    KredensialPseudonim,
    PetaPseudonim,
)

AKAR = Path(__file__).resolve().parents[2]

PENELITI = KredensialPseudonim(nama="peneliti")


def _peta() -> PetaPseudonim:
    peta = PetaPseudonim()
    peta.daftarkan("PGN-001", "PSD-a1", kredensial=PENELITI)
    return peta


# ------------------------------------------------- C-05 · tipe, bukan nilai lain


def test_kredensial_layanan_aplikasi_ditolak() -> None:
    """**Uji terpenting berkas ini.**

    `PENJAWABAN` dan `VERIFIKASI` adalah kredensial layanan aplikasi. Keduanya
    bertipe `Kredensial`, dan peta pseudonim menuntut `KredensialPseudonim` —
    tipe yang berbeda, bukan nilai lain pada tipe yang sama.
    """
    for kredensial in (PENJAWABAN, VERIFIKASI):
        with pytest.raises(GalatPseudonim):
            _peta().pseudonim_bagi("PGN-001", kredensial=kredensial)  # type: ignore[arg-type]


def test_kredensial_pseudonim_bukan_ragam_kredensial_biasa() -> None:
    """Kesamaan bentuk akan mengundang seseorang menulis fungsi yang menerima
    keduanya, dan fungsi semacam itu adalah tempat C-05 runtuh tanpa terlihat.

    Diuji atas pewarisan **dan** atas kesamaan bidang: dua tipe yang berbeda
    nama tetapi sama bidangnya akan saling menggantikan pada pemanggil yang
    memakai pemetaan bebas.
    """
    from src.penyimpanan.kredensial import Kredensial

    assert not issubclass(KredensialPseudonim, Kredensial)
    assert not issubclass(Kredensial, KredensialPseudonim)
    assert set(KredensialPseudonim.model_fields) != set(Kredensial.model_fields)


def test_tanpa_kredensial_tidak_dapat_dipanggil() -> None:
    """Tidak ada nilai bawaan bagi kredensialnya — parameter berbawaan akan
    berubah menjadi "tanpa kredensial berarti boleh" pada pemanggilan pertama
    yang lupa mengisinya."""
    with pytest.raises(TypeError):
        _peta().pseudonim_bagi("PGN-001")  # type: ignore[call-arg]


def test_kredensial_tanpa_nama_ditolak() -> None:
    """Pemeriksaan kedua sesudah tipe: kredensial yang disusun asal ada tidak
    dapat ditelusuri kepada siapa pun."""
    with pytest.raises(ValidationError):
        KredensialPseudonim(nama="")
    with pytest.raises(GalatPseudonim):
        _peta().pseudonim_bagi(
            "PGN-001", kredensial=KredensialPseudonim.model_construct(nama="  ")
        )


def test_kredensial_beku() -> None:
    with pytest.raises(ValidationError):
        PENELITI.nama = "lain"  # type: ignore[misc]


# --------------------------------------------------- arah balik yang dilindungi


def test_arah_balik_menuntut_kredensial_yang_sama() -> None:
    """**Inilah yang C-05 lindungi.** Telemetri menyimpan pseudonim; yang
    mengubahnya kembali menjadi identitas adalah fungsi ini."""
    peta = _peta()
    assert peta.id_pengguna_bagi("PSD-a1", kredensial=PENELITI) == "PGN-001"
    with pytest.raises(GalatPseudonim):
        peta.id_pengguna_bagi("PSD-a1", kredensial=PENJAWABAN)  # type: ignore[arg-type]


def test_pseudonim_tidak_dikenal_menghasilkan_none() -> None:
    """`None`, bukan galat: bertanya tentang pseudonim yang belum terdaftar
    bukan pelanggaran, dan galat di sini akan mengundang pemanggil
    membungkusnya dengan `try` yang juga menelan galat kewenangan."""
    peta = _peta()
    assert peta.id_pengguna_bagi("PSD-zz", kredensial=PENELITI) is None
    assert peta.pseudonim_bagi("PGN-999", kredensial=PENELITI) is None


# ------------------------------------------------------------ pemetaan tetap


def test_pemetaan_tidak_dapat_ditimpa() -> None:
    """Pseudonim yang berpindah pemilik membuat data perilaku lama tertaut ke
    orang yang keliru — dan itu tidak dapat diperbaiki sesudah pemetaan lamanya
    hilang."""
    peta = _peta()
    with pytest.raises(GalatPseudonim):
        peta.daftarkan("PGN-001", "PSD-b2", kredensial=PENELITI)
    assert peta.pseudonim_bagi("PGN-001", kredensial=PENELITI) == "PSD-a1"


def test_pseudonim_tidak_dapat_dipakai_dua_pengguna() -> None:
    """Dua pengguna berpseudonim sama membuat arah balik tidak berjawab
    tunggal, dan data perilaku keduanya bercampur."""
    peta = _peta()
    with pytest.raises(GalatPseudonim):
        peta.daftarkan("PGN-002", "PSD-a1", kredensial=PENELITI)


def test_pendaftaran_menuntut_kedua_nilai() -> None:
    peta = PetaPseudonim()
    with pytest.raises(GalatPseudonim):
        peta.daftarkan("", "PSD-a1", kredensial=PENELITI)
    with pytest.raises(GalatPseudonim):
        peta.daftarkan("PGN-001", "", kredensial=PENELITI)


def test_pendaftaran_menuntut_kredensial_yang_sama() -> None:
    peta = PetaPseudonim()
    with pytest.raises(GalatPseudonim):
        peta.daftarkan("PGN-001", "PSD-a1", kredensial=VERIFIKASI)  # type: ignore[arg-type]


# ------------------------------------------------- AG-04 · Area tetap dua nilai


def test_peta_pseudonim_bukan_nilai_ketiga_pada_area() -> None:
    """AG-04 melarang mengubah daftar nilai enum, dan `Area` mewujudkan
    `dokumen_sumber.area_simpan` milik D-14 Bagian 5.1.

    Alasannya bukan sekadar formal: area adalah tempat **dokumen** berada, dan
    menaruh peta identitas pada sumbu yang sama membuat kredensial yang berhak
    membaca korpus tampak sebanding dengan yang berhak membaca identitas.
    """
    assert {a.value for a in Area} == {"karantina", "korpus"}
