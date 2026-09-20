"""Keutuhan penulisan dan pembedaan galat — T-8 fitur 024.

Dua keadaan pada `spec.md` "Keadaan yang wajib ditangani" yang **tidak dapat
ditiru**, dan karena itu hanya terbukti atas peladen sungguhan:

| Keadaan | Yang wajib terjadi |
|---|---|
| Sambungan putus di tengah penulisan | Penulisan tidak setengah jadi |
| Peladen tidak dapat dihubungi | Galat yang menyebut keadaannya, bukan galat kredensial |

Yang kedua penting justru karena mudah tertukar. Pemanggil yang menerima
"tidak berwenang" ketika peladennya sebenarnya mati akan mencari kekeliruan
pada kredensial, dan tidak menemukannya — berjam-jam.
"""

from __future__ import annotations

import json

import pytest
from src.penyimpanan.area import Area
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenTidakAda
from src.penyimpanan.kredensial_baku import VERIFIKASI
from src.penyimpanan.postgres import PenyimpanPostgres
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, psql, siapkan

siapkan()


class SambunganNyata:
    def __init__(self, peran: str = "pengelola", porta: int | None = None) -> None:
        self._peran = peran
        self._porta = porta if porta is not None else int(PORT)

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg

        sambungan = await asyncpg.connect(
            host=HOST, port=self._porta, user=self._peran, database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("execute", kueri, *argumen)


def _tanam(area: str, id_dokumen: str) -> None:
    isi = json.dumps({"isi": "notulen rapat"})
    psql(
        "smart_coaching",
        "-c",
        f"INSERT INTO {area}.dokumen_sumber (id, isi) VALUES ('{id_dokumen}', '{isi}'::jsonb) "
        f"ON CONFLICT (id) DO UPDATE SET isi = EXCLUDED.isi",
    )


def _jumlah(area: str, id_dokumen: str) -> int:
    hasil = psql(
        "smart_coaching",
        "-c",
        f"select count(*) from {area}.dokumen_sumber where id = '{id_dokumen}'",
    )
    return int(hasil.stdout.strip() or 0)


# ── keutuhan pemindahan ──────────────────────────────────────────────


def test_dokumen_tidak_pernah_berada_pada_dua_area() -> None:
    """Pemindahan satu pernyataan — `DELETE ... RETURNING` menyuapi `INSERT`.

    Menyalin lalu menghapus meninggalkan jendela ketika dokumen ada di
    keduanya, dan salinan mentah yang tertinggal di karantina adalah persis
    yang ADR-06 cegah.
    """
    psql("smart_coaching", "-c", "TRUNCATE karantina.dokumen_sumber, korpus.dokumen_sumber")
    _tanam("karantina", "dok_pindah")

    penyimpan = PenyimpanPostgres(SambunganNyata())
    jalankan(penyimpan.pindahkan(VERIFIKASI, "dok_pindah", Area.KARANTINA, Area.KORPUS, "uji"))

    assert _jumlah("karantina", "dok_pindah") == 0, "salinan tertinggal di karantina"
    assert _jumlah("korpus", "dok_pindah") == 1


def test_pemindahan_yang_gagal_tidak_menghapus_asalnya() -> None:
    """Tujuan sudah terisi id yang sama, sehingga `INSERT` melanggar kunci.

    Bila pemindahan bukan satu pernyataan, `DELETE` sudah terlanjur berjalan
    ketika `INSERT` gagal — dan dokumennya hilang dari keduanya.
    """
    psql("smart_coaching", "-c", "TRUNCATE karantina.dokumen_sumber, korpus.dokumen_sumber")
    _tanam("karantina", "dok_bentrok")
    _tanam("korpus", "dok_bentrok")

    penyimpan = PenyimpanPostgres(SambunganNyata())
    with pytest.raises(Exception) as galat:
        jalankan(penyimpan.pindahkan(VERIFIKASI, "dok_bentrok", Area.KARANTINA, Area.KORPUS, "uji"))

    assert not isinstance(galat.value, GalatAksesDitolak)
    assert _jumlah("karantina", "dok_bentrok") == 1, "dokumen hilang dari asalnya"
    assert _jumlah("korpus", "dok_bentrok") == 1


def test_pemindahan_dokumen_yang_tidak_ada_tidak_membuat_apa_pun() -> None:
    psql("smart_coaching", "-c", "TRUNCATE karantina.dokumen_sumber, korpus.dokumen_sumber")
    penyimpan = PenyimpanPostgres(SambunganNyata())

    with pytest.raises(GalatDokumenTidakAda):
        jalankan(penyimpan.pindahkan(VERIFIKASI, "hantu", Area.KARANTINA, Area.KORPUS, "uji"))

    assert _jumlah("korpus", "hantu") == 0


# ── peladen tidak dapat dihubungi ────────────────────────────────────


def test_peladen_mati_bukan_galat_kredensial() -> None:
    """Pemanggil yang menerima "tidak berwenang" ketika peladennya mati akan
    mencari kekeliruan pada kredensial, dan tidak menemukannya."""
    penyimpan = PenyimpanPostgres(SambunganNyata(porta=59999))

    with pytest.raises(Exception) as galat:
        jalankan(penyimpan.baca_dokumen(VERIFIKASI, Area.KORPUS, "apa pun"))

    assert not isinstance(galat.value, GalatAksesDitolak), (
        "galat sambungan menyamar sebagai galat kredensial"
    )
    assert not isinstance(galat.value, GalatDokumenTidakAda), (
        "galat sambungan menyamar sebagai dokumen tidak ada"
    )


def test_kredensial_tetap_menang_atas_peladen_mati() -> None:
    """Urutan R-02 berlaku juga ketika peladennya mati.

    Kredensial diperiksa sebelum menyambung, sehingga pemanggil yang tidak
    berhak menerima galat kredensial — bukan galat sambungan yang membocorkan
    bahwa peladennya ada dan sedang mati.
    """
    from src.penyimpanan.kredensial_baku import PENJAWABAN

    penyimpan = PenyimpanPostgres(SambunganNyata(porta=59999))
    with pytest.raises(GalatAksesDitolak):
        jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, "apa pun"))
