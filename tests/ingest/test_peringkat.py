"""Uji pemetaan jenis sumber ke peringkat kepercayaan — R-07, FR-B09, KD-08.

Pemiliknya D-13 Bagian 6, bukan D-01. `docs/D00.md` Bagian 3 menetapkan
"tingkat kepercayaan asal segmen" dimiliki D-13, dan FR-B09 sendiri menutup
kalimatnya dengan "Dasar: D-13 Bagian 6". Ketika keduanya berbeda, D-13 yang
berlaku.

Perbedaannya nyata: D-13 menempatkan artikel berlisensi terbuka dari penerbit
terverifikasi pada T2, sedangkan daftar empat nama dalam kurung pada FR-B09
tidak menyediakan tempat baginya.
"""

import pytest
from src.ingest.peringkat import JenisSumber, peringkat_bagi
from src.llm.tipe import Peringkat


@pytest.mark.parametrize(
    ("jenis", "diharapkan"),
    [
        (JenisSumber.REGULASI_RESMI, Peringkat.T1),
        (JenisSumber.DATA_RESMI_AGREGAT, Peringkat.T2),
        (JenisSumber.ARTIKEL_LISENSI_TERBUKA, Peringkat.T2),
        (JenisSumber.DOKUMEN_SEKOLAH, Peringkat.T3),
        (JenisSumber.LAPORAN_LEMBAGA, Peringkat.T4),
    ],
)
def test_seluruh_baris_d13_terpetakan(jenis: JenisSumber, diharapkan: Peringkat) -> None:
    assert peringkat_bagi(jenis) is diharapkan


def test_setiap_jenis_punya_peringkat() -> None:
    """Jenis yang ditambahkan kelak tanpa peringkat tertangkap di sini, bukan
    pada dokumen pertama yang memakainya."""
    for jenis in JenisSumber:
        assert isinstance(peringkat_bagi(jenis), Peringkat)


def test_jenis_tak_dikenal_menghasilkan_galat() -> None:
    """Bukan T4 diam-diam. Memberi peringkat terendah pada yang tidak dikenal
    terdengar berhati-hati, tetapi ia menyembunyikan kekeliruan konfigurasi."""
    with pytest.raises(ValueError):
        JenisSumber("jenis_yang_tidak_ada")


def test_artikel_lisensi_terbuka_bukan_t4() -> None:
    """D-13 Bagian 6 menempatkannya pada T2.

    Bila dipetakan ke T4 — pembacaan yang wajar atas daftar empat nama FR-B09 —
    artikel jurnal tidak akan pernah dapat menopang klaim, dan seluruh kanal
    K-C pada D-06 kehilangan gunanya.
    """
    assert peringkat_bagi(JenisSumber.ARTIKEL_LISENSI_TERBUKA) is not Peringkat.T4


def test_hanya_dokumen_sekolah_dan_laporan_yang_tidak_boleh_jadi_dasar_tunggal() -> None:
    """C-19, FR-F15 — dinyatakan sebagai sifat seluruh pemetaan."""
    lemah = {j for j in JenisSumber if peringkat_bagi(j) in {Peringkat.T3, Peringkat.T4}}
    assert lemah == {JenisSumber.DOKUMEN_SEKOLAH, JenisSumber.LAPORAN_LEMBAGA}
