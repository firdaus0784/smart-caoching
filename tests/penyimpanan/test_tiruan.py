"""Kontrak `PenyimpanDasar` — R-01, R-02, R-03, R-04, C-03, ADR-06, ADR-12.

Tugas terpenting Fase A. Penyimpan yang memeriksa keberadaan dokumen lebih
dulu membocorkan keberadaan dokumen karantina lewat perbedaan galat, dan itu
meruntuhkan C-03 **tanpa satu pun dokumen terbaca**.

Kebocorannya halus: pemanggil yang menerima "tidak ditemukan" untuk satu id dan
"tidak berwenang" untuk id lain sudah mengetahui id mana yang ada di karantina.
Cukup satu perbedaan untuk menyusun daftar.

## Berkas ini berparameter — T-2 fitur 024

R-01 menuntut `PenyimpanPostgres` lulus rangkaian uji yang **sama** dengan
`PenyimpanTiruan`, tanpa satu pun uji diubah. Karena itu seluruh uji di bawah
menerima pelaksananya dari `PABRIK`, bukan menyusunnya sendiri.

Hari ini `PABRIK` berisi **satu** pelaksana. Itu disengaja: tugas T-2 mengubah
bentuk uji dan membuktikan hasilnya tidak berubah, sebelum pelaksana kedua
ditambahkan pada T-3. Menambah keduanya sekaligus membuat kegagalan tidak
dapat ditelusuri ke perubahan yang mana.

## Temuan T-2 yang belum diperbaiki, dan sengaja begitu

`GalatDokumenTidakAda` tinggal di `src/penyimpanan/tiruan.py` — di dalam
**pelaksana** — padahal ia bagian kontrak: R-03 menuntut galat "tidak ada"
pada area yang boleh dibaca, dan tuntutan itu berlaku bagi setiap pelaksana.
`PenyimpanPostgres` yang mengimpornya dari `tiruan.py` akan menjadikan
pelaksana sungguhan bergantung pada pelaksana tiruan.

Perbaikannya memindahkan kelas itu ke `galat.py`, dan itu **penyesuaian
kontrak** yang Keputusan Gerbang 1 nomor 3 wajibkan melewati Gerbang 2
tersendiri. Karena itu tidak dikerjakan di sini. Sebagai gantinya, tiap entri
`PABRIK` memasok sendiri tipe galatnya — bentuk yang menampung perbaikan itu
kelak tanpa mengubah satu pun uji di bawah.
"""

from collections.abc import Callable

import pytest
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, VERIFIKASI
from src.penyimpanan.tiruan import GalatDokumenTidakAda, PenyimpanTiruan
from tests.konftes_asinkron import jalankan

Penanam = Callable[[PenyimpanDasar, Area, str, object], None]


def _susun_tiruan() -> tuple[PenyimpanDasar, Penanam, type[Exception]]:
    def tanam(penyimpan: PenyimpanDasar, area: Area, id_dokumen: str, isi: object) -> None:
        assert isinstance(penyimpan, PenyimpanTiruan)
        penyimpan.tanam(area, id_dokumen, isi)

    return PenyimpanTiruan(), tanam, GalatDokumenTidakAda


PABRIK = {"tiruan": _susun_tiruan}
"""Satu pelaksana hari ini. `PenyimpanPostgres` menyusul pada T-3."""


@pytest.fixture(params=sorted(PABRIK), ids=sorted(PABRIK))
def terisi(request: pytest.FixtureRequest) -> tuple[PenyimpanDasar, type[Exception]]:
    """Penyimpan berisi dua dokumen — satu karantina, satu korpus."""
    penyimpan, tanam, galat_tidak_ada = PABRIK[request.param]()
    tanam(penyimpan, Area.KARANTINA, "dok_karantina", {"isi": "notulen rapat"})
    tanam(penyimpan, Area.KORPUS, "dok_korpus", {"isi": "Permendikdasmen 1/2026"})
    return penyimpan, galat_tidak_ada


def test_penjawaban_membaca_korpus(terisi: tuple) -> None:
    assert jalankan(terisi[0].baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_korpus"))


def test_penjawaban_ditolak_membaca_karantina(terisi: tuple) -> None:
    """C-03, R-01a."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_karantina"))


def test_dokumen_karantina_yang_tidak_ada_juga_galat_akses(terisi: tuple) -> None:
    """**Uji terpenting berkas ini.**

    Kredensial diperiksa sebelum data disentuh, sehingga jawaban untuk id yang
    ada dan id yang tidak ada identik. Bila penyimpan memeriksa keberadaan
    lebih dulu, uji ini gagal — dan kegagalannya berarti daftar dokumen
    karantina dapat disusun dari luar.
    """
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_tidak_pernah_ada"))


def test_dua_galat_tidak_dapat_dibedakan_dari_luar(terisi: tuple) -> None:
    """Perbandingan langsung, bukan dua uji terpisah yang kebetulan sama."""
    penyimpan = terisi[0]
    hasil = []
    for id_dokumen in ("dok_karantina", "dok_tidak_pernah_ada"):
        try:
            jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, id_dokumen))
        except GalatAksesDitolak as galat:
            hasil.append(galat.tanggapan().galat.pesan_pengguna)
    assert len(hasil) == 2
    assert hasil[0] == hasil[1]


def test_verifikasi_membaca_karantina(terisi: tuple) -> None:
    assert jalankan(terisi[0].baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina"))


def test_dokumen_tidak_ada_pada_area_yang_boleh_dibaca(terisi: tuple) -> None:
    """Ketika kredensialnya memang menjangkau, barulah keberadaan diperiksa."""
    with pytest.raises(terisi[1]):
        jalankan(terisi[0].baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_tidak_pernah_ada"))


def test_pemanggil_llm_tidak_dapat_menulis(terisi: tuple) -> None:
    """R-01b."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].tulis_dokumen(PEMANGGIL_LLM, Area.KORPUS, "dok_baru", {"isi": "x"}))


def test_penjawaban_tidak_dapat_menulis(terisi: tuple) -> None:
    """C-17."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].tulis_dokumen(PENJAWABAN, Area.KORPUS, "dok_baru", {"isi": "x"}))


def test_verifikasi_menulis_ke_korpus(terisi: tuple) -> None:
    """Sisi positif R-04. Uji yang hanya memeriksa penolakan tidak
    membuktikan bahwa yang berhak dapat bekerja."""
    penyimpan = terisi[0]
    jalankan(penyimpan.tulis_dokumen(VERIFIKASI, Area.KORPUS, "dok_baru", {"isi": "x"}))
    assert jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_baru")) == {"isi": "x"}


def test_pindah_menuntut_baca_asal_dan_tulis_tujuan(terisi: tuple) -> None:
    """R-04."""
    penyimpan = terisi[0]
    jalankan(penyimpan.pindahkan(VERIFIKASI, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos"))
    assert jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_karantina"))


def test_pindah_ditolak_bagi_kredensial_penjawaban(terisi: tuple) -> None:
    with pytest.raises(GalatAksesDitolak):
        jalankan(
            terisi[0].pindahkan(PENJAWABAN, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos")
        )


def test_pindah_dokumen_yang_tidak_ada(terisi: tuple) -> None:
    with pytest.raises(terisi[1]):
        jalankan(
            terisi[0].pindahkan(
                VERIFIKASI, "dok_tidak_pernah_ada", Area.KARANTINA, Area.KORPUS, "lolos"
            )
        )


def test_dokumen_hilang_dari_area_asal_setelah_dipindah(terisi: tuple) -> None:
    """Menyalin, bukan memindahkan, meninggalkan salinan mentah di karantina —
    dan salinan itulah yang ADR-06 cegah."""
    penyimpan = terisi[0]
    jalankan(penyimpan.pindahkan(VERIFIKASI, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos"))
    with pytest.raises(terisi[1]):
        jalankan(penyimpan.baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina"))
