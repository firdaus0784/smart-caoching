"""Penyimpan pembaca sumber — T-4 fitur 032, R-04, R-06, R-07; K-1, K-3.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL. Yang kedua
tersambung sebagai `peran_pembaca_sumber` (TK-64), sehingga uji ini juga
membuktikan hak T-2 cukup bagi pekerjaannya.

Penyimpan mengembalikan baris apa adanya — catatan terbaru, segmen bagian itu
berurutan `id_segmen`. Aturan tampil milik `src/api/sumber.py`.
"""

from __future__ import annotations

import secrets
from collections.abc import Callable

import pytest
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.sumber import (
    PERAN_PEMBACA_SUMBER,
    BarisSumber,
    PembacaSumber,
    PembacaSumberPostgres,
    SegmenBagian,
    SumberMemori,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import psql, siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

_META = MetadataDokumen(
    judul="Permendikdasmen Nomor 1 Tahun 2026",
    jenis="regulasi_resmi",
    penerbit="Kemendikdasmen",
    tahun=2026,
    tingkat_kerahasiaan="publik",
)


def _acak() -> str:
    return "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(10))


class _Tanam:
    """Menanam isi pada pelaksana yang diuji — sebagai pengelola bagi PostgreSQL."""

    def __init__(self, memori: SumberMemori | None) -> None:
        self.memori = memori

    def _sql(self, kueri: str) -> None:
        hasil = psql("smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
        assert hasil.returncode == 0, hasil.stderr

    def dokumen(self, id_dokumen: str, area: str = "korpus") -> None:
        if self.memori is not None:
            if area == "korpus":
                self.memori.tanam_dokumen(id_dokumen)
            return
        self._sql(
            f"insert into {area}.dokumen_sumber (id, isi) values ('{id_dokumen}', '\"teks\"')"
        )

    def metadata(self, id_dokumen: str, meta: MetadataDokumen = _META) -> None:
        if self.memori is not None:
            self.memori.tanam_metadata(id_dokumen, meta)
            return
        self._sql(
            "insert into korpus.metadata_dokumen "
            "(id_dokumen, judul, jenis, penerbit, tahun, tingkat_kerahasiaan) values "
            f"('{id_dokumen}', '{meta.judul}', '{meta.jenis}', '{meta.penerbit}', {meta.tahun}, "
            f"'{meta.tingkat_kerahasiaan}')"
        )

    def status(self, id_dokumen: str, status: str, pengganti: str | None = None) -> None:
        if self.memori is not None:
            self.memori.tanam_status(id_dokumen, status, pengganti)
            return
        nilai = "null" if pengganti is None else f"'{pengganti}'"
        self._sql(
            "insert into korpus.status_dokumen (id_dokumen, status, rujukan_pengganti) "
            f"values ('{id_dokumen}', '{status}', {nilai})"
        )

    def segmen(
        self,
        id_segmen: str,
        id_dokumen: str,
        bagian: str,
        teks: str,
        *,
        lisensi: str = "terbuka",
        terverifikasi: bool = True,
    ) -> None:
        if self.memori is not None:
            self.memori.tanam_segmen(
                id_segmen,
                id_dokumen,
                bagian,
                SegmenBagian(teks=teks, lisensi=lisensi, anonimisasi_terverifikasi=terverifikasi),
            )
            return
        self._sql(
            "insert into indeks_utama.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
            "anonimisasi_terverifikasi, penanda_bagian) values "
            f"('{id_segmen}', '{id_dokumen}', '{teks}', '{lisensi}', {terverifikasi}, '{bagian}')"
        )


Susunan = Callable[[], tuple[PembacaSumber, _Tanam]]


@pytest.fixture(params=["memori", "postgres"])
def susunan(request: pytest.FixtureRequest) -> tuple[PembacaSumber, _Tanam]:
    if request.param == "memori":
        memori = SumberMemori()
        return memori, _Tanam(memori)
    pembaca = PembacaSumberPostgres(SambunganPeran(PERAN_PEMBACA_SUMBER))  # type: ignore[arg-type]
    return pembaca, _Tanam(None)


def test_dokumen_korpus_dengan_catatan_terbaru(susunan: tuple[PembacaSumber, _Tanam]) -> None:
    pembaca, tanam = susunan
    dok = "dok-" + _acak()
    tanam.dokumen(dok)
    tanam.metadata(
        dok, MetadataDokumen("Judul lama", "regulasi_resmi", "Kementerian", 2025, "publik")
    )
    tanam.metadata(dok)
    tanam.status(dok, "berlaku")
    tanam.status(dok, "diubah", "Permendikdasmen_2_2027")
    assert jalankan(pembaca.dokumen(dok)) == BarisSumber(
        id_dokumen=dok,
        metadata=_META,
        status="diubah",
        rujukan_pengganti="Permendikdasmen_2_2027",
    )


def test_dokumen_tanpa_status_bernilai_kosong(susunan: tuple[PembacaSumber, _Tanam]) -> None:
    pembaca, tanam = susunan
    dok = "dok-" + _acak()
    tanam.dokumen(dok)
    tanam.metadata(dok)
    baris = jalankan(pembaca.dokumen(dok))
    assert baris is not None and (baris.status, baris.rujukan_pengganti) == (None, None)


def test_satu_bentuk_bagi_yang_tidak_terjangkau(susunan: tuple[PembacaSumber, _Tanam]) -> None:
    """R-04: tidak dikenal, karantina, ditarik dari korpus (catatan tertinggal),
    dan korpus tanpa catatan metadata — keempatnya `None`."""
    pembaca, tanam = susunan
    karantina, ditarik, tanpa_meta = ("dok-" + _acak() for _ in range(3))
    tanam.dokumen(karantina, area="karantina")
    tanam.metadata(karantina)
    tanam.metadata(ditarik)
    tanam.dokumen(tanpa_meta)
    for dok in ("dok-tidak-pernah-ada", karantina, ditarik, tanpa_meta):
        assert jalankan(pembaca.dokumen(dok)) is None, dok


def test_segmen_bagian_itu_saja_berurutan(susunan: tuple[PembacaSumber, _Tanam]) -> None:
    pembaca, tanam = susunan
    dok = "dok-" + _acak()
    tanam.segmen(f"{dok}-b", dok, "Pasal 7", "Kalimat kedua.", terverifikasi=False)
    tanam.segmen(f"{dok}-a", dok, "Pasal 7", "Kalimat pertama.")
    tanam.segmen(f"{dok}-c", dok, "Pasal 8", "Pasal lain.")
    tanam.segmen(f"{dok}-d", dok, "Pasal 7 ayat (2)", "Bagian lain yang mirip.")
    assert jalankan(pembaca.segmen(dok, "Pasal 7")) == (
        SegmenBagian(teks="Kalimat pertama.", lisensi="terbuka", anonimisasi_terverifikasi=True),
        SegmenBagian(teks="Kalimat kedua.", lisensi="terbuka", anonimisasi_terverifikasi=False),
    )
    assert jalankan(pembaca.segmen(dok, "Pasal 9")) == ()
