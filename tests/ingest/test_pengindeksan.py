"""Pengindeksan dokumen korpus — T-5 fitur 038, R-02 s.d. R-07; K-3; P-2 A, P-4 A.

Atas memori **dan** PostgreSQL sebagai `peran_pengindeks`, lewat pelaksana
yang sama dengan uji kontrak penulisnya. Teks contoh berpola peraturan
dibuat-buat.
"""

from __future__ import annotations

import pytest
from src.ingest.pengindeksan import HasilPengindeksan, RingkasanSegmen, indekskan
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.galat import GalatDokumenTidakAda
from src.penyimpanan.kredensial_baku import PENGINDEKSAN
from tests.konftes_asinkron import jalankan
from tests.penyimpanan.test_pengindeks_simpan import (
    Pelaksana,
    id_dokumen_baru,
    pelaksana_memori,
    pelaksana_postgres,
)

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA
TEKS = "PERATURAN CONTOH\nMenimbang: perlu.\nPasal 1\nKepala sekolah menyusun.\nPasal 2\nRencana."


@pytest.fixture(params=["memori", "postgres"])
def pelaksana(request: pytest.FixtureRequest) -> Pelaksana:
    return pelaksana_memori() if request.param == "memori" else pelaksana_postgres()


def _indekskan(p: Pelaksana, id_dokumen: str, *, tulis: bool = True) -> HasilPengindeksan:
    return jalankan(indekskan(p.penulis, PENGINDEKSAN, id_dokumen, tulis=tulis))


def test_lisensi_terbuka_ke_indeks_utama(pelaksana: Pelaksana) -> None:
    """R-03; pengenal deterministik berurutan (R-06, D-14 Bagian 5.1)."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, TEKS, "Public Domain")
    hasil = _indekskan(pelaksana, id_dokumen)
    assert hasil == HasilPengindeksan(
        id_dokumen=id_dokumen,
        indeks_tujuan=UTAMA,
        segmen=(
            RingkasanSegmen("Pembukaan", 4),
            RingkasanSegmen("Pasal 1", 5),
            RingkasanSegmen("Pasal 2", 3),
        ),
        ditulis=True,
    )
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == [
        (f"{id_dokumen}:0001", "Pembukaan", "terbuka"),
        (f"{id_dokumen}:0002", "Pasal 1", "terbuka"),
        (f"{id_dokumen}:0003", "Pasal 2", "terbuka"),
    ]
    assert pelaksana.tersimpan(METADATA, id_dokumen) == []


@pytest.mark.parametrize("lisensi", [None, "Hak cipta dilindungi", "lisensi khusus penerbit"])
def test_lisensi_kosong_atau_tak_dikenal_ke_indeks_metadata(
    pelaksana: Pelaksana, lisensi: str | None
) -> None:
    """R-03, KL-01, C-02, M-4: tertutup kecuali terbaca terbuka — tidak
    disimpulkan dari jenis dokumen, yang di sini regulasi resmi."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, TEKS, lisensi)
    assert _indekskan(pelaksana, id_dokumen).indeks_tujuan is METADATA
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == []
    assert [s[2] for s in pelaksana.tersimpan(METADATA, id_dokumen)] == ["tertutup"] * 3


def test_pengindeksan_ulang_mengganti_dengan_pengenal_sama(pelaksana: Pelaksana) -> None:
    """R-06, M-9: teks yang sama menghasilkan segmen dan pengenal yang sama;
    pengindeksan ulang tidak menambah."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, TEKS, "cc-by-4.0")
    pertama = _indekskan(pelaksana, id_dokumen)
    sebelum = pelaksana.tersimpan(UTAMA, id_dokumen)
    assert _indekskan(pelaksana, id_dokumen) == pertama
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == sebelum
    assert len(sebelum) == 3


def test_pratinjau_tidak_menulis(pelaksana: Pelaksana) -> None:
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, TEKS, "cc0")
    hasil = _indekskan(pelaksana, id_dokumen, tulis=False)
    assert not hasil.ditulis
    assert [s.penanda for s in hasil.segmen] == ["Pembukaan", "Pasal 1", "Pasal 2"]
    for indeks in IndeksTujuan:
        assert pelaksana.tersimpan(indeks, id_dokumen) == []


def test_ringkasan_tanpa_teks(pelaksana: Pelaksana) -> None:
    """R-07: yang dikembalikan penanda dan jumlah kata, bukan isi."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, TEKS, "cc0")
    hasil = _indekskan(pelaksana, id_dokumen, tulis=False)
    assert "Kepala sekolah menyusun" not in repr(hasil)


def test_di_luar_korpus_ditolak_tanpa_menulis(pelaksana: Pelaksana) -> None:
    """R-04, C-03."""
    di_karantina = id_dokumen_baru()
    pelaksana.tanam_karantina(di_karantina)
    with pytest.raises(GalatDokumenTidakAda):
        _indekskan(pelaksana, di_karantina)
    for indeks in IndeksTujuan:
        assert pelaksana.tersimpan(indeks, di_karantina) == []


def test_dokumen_hampa_mengosongkan_segmennya(pelaksana: Pelaksana) -> None:
    """Indeks mencerminkan dokumennya: teks hampa berarti tanpa segmen, bukan
    segmen lama yang tertinggal."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, "   ", "cc0")
    hasil = _indekskan(pelaksana, id_dokumen)
    assert hasil.segmen == () and hasil.ditulis
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == []
