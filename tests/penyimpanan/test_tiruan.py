"""Uji penyimpan tiruan — R-01a, R-02, R-04, C-03, ADR-06, ADR-12.

Tugas terpenting Fase A. Penyimpan yang memeriksa keberadaan dokumen lebih
dulu membocorkan keberadaan dokumen karantina lewat perbedaan galat, dan itu
meruntuhkan C-03 **tanpa satu pun dokumen terbaca**.

Kebocorannya halus: pemanggil yang menerima "tidak ditemukan" untuk satu id dan
"tidak berwenang" untuk id lain sudah mengetahui id mana yang ada di karantina.
Cukup satu perbedaan untuk menyusun daftar.
"""

import pytest
from src.penyimpanan.area import Area
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, VERIFIKASI
from src.penyimpanan.tiruan import GalatDokumenTidakAda, PenyimpanTiruan


def _terisi() -> PenyimpanTiruan:
    penyimpan = PenyimpanTiruan()
    penyimpan.tanam(Area.KARANTINA, "dok_karantina", {"isi": "notulen rapat"})
    penyimpan.tanam(Area.KORPUS, "dok_korpus", {"isi": "Permendikdasmen 1/2026"})
    return penyimpan


def test_penjawaban_membaca_korpus() -> None:
    assert _terisi().baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_korpus")


def test_penjawaban_ditolak_membaca_karantina() -> None:
    """C-03, R-01a."""
    with pytest.raises(GalatAksesDitolak):
        _terisi().baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_karantina")


def test_dokumen_karantina_yang_tidak_ada_juga_galat_akses() -> None:
    """**Uji terpenting berkas ini.**

    Kredensial diperiksa sebelum data disentuh, sehingga jawaban untuk id yang
    ada dan id yang tidak ada identik. Bila penyimpan memeriksa keberadaan
    lebih dulu, uji ini gagal — dan kegagalannya berarti daftar dokumen
    karantina dapat disusun dari luar.
    """
    with pytest.raises(GalatAksesDitolak):
        _terisi().baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_tidak_pernah_ada")


def test_dua_galat_tidak_dapat_dibedakan_dari_luar() -> None:
    """Perbandingan langsung, bukan dua uji terpisah yang kebetulan sama."""
    penyimpan = _terisi()
    hasil = []
    for id_dokumen in ("dok_karantina", "dok_tidak_pernah_ada"):
        try:
            penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, id_dokumen)
        except GalatAksesDitolak as galat:
            hasil.append(galat.tanggapan().galat.pesan_pengguna)
    assert len(hasil) == 2
    assert hasil[0] == hasil[1]


def test_verifikasi_membaca_karantina() -> None:
    assert _terisi().baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina")


def test_dokumen_tidak_ada_pada_area_yang_boleh_dibaca() -> None:
    """Ketika kredensialnya memang menjangkau, barulah keberadaan diperiksa."""
    with pytest.raises(GalatDokumenTidakAda):
        _terisi().baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_tidak_pernah_ada")


def test_pemanggil_llm_tidak_dapat_menulis() -> None:
    """R-01b."""
    with pytest.raises(GalatAksesDitolak):
        _terisi().tulis_dokumen(PEMANGGIL_LLM, Area.KORPUS, "dok_baru", {"isi": "x"})


def test_penjawaban_tidak_dapat_menulis() -> None:
    """C-17."""
    with pytest.raises(GalatAksesDitolak):
        _terisi().tulis_dokumen(PENJAWABAN, Area.KORPUS, "dok_baru", {"isi": "x"})


def test_verifikasi_menulis_ke_korpus() -> None:
    """Sisi positif R-04. Uji yang hanya memeriksa penolakan tidak
    membuktikan bahwa yang berhak dapat bekerja."""
    penyimpan = _terisi()
    penyimpan.tulis_dokumen(VERIFIKASI, Area.KORPUS, "dok_baru", {"isi": "x"})
    assert penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_baru") == {"isi": "x"}


def test_pindah_menuntut_baca_asal_dan_tulis_tujuan() -> None:
    """R-04."""
    penyimpan = _terisi()
    penyimpan.pindahkan(VERIFIKASI, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos")
    assert penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_karantina")


def test_pindah_ditolak_bagi_kredensial_penjawaban() -> None:
    with pytest.raises(GalatAksesDitolak):
        _terisi().pindahkan(PENJAWABAN, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos")


def test_pindah_dokumen_yang_tidak_ada() -> None:
    with pytest.raises(GalatDokumenTidakAda):
        _terisi().pindahkan(
            VERIFIKASI, "dok_tidak_pernah_ada", Area.KARANTINA, Area.KORPUS, "lolos"
        )


def test_dokumen_hilang_dari_area_asal_setelah_dipindah() -> None:
    """Menyalin, bukan memindahkan, meninggalkan salinan mentah di karantina —
    dan salinan itulah yang ADR-06 cegah."""
    penyimpan = _terisi()
    penyimpan.pindahkan(VERIFIKASI, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos")
    with pytest.raises(GalatDokumenTidakAda):
        penyimpan.baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina")
