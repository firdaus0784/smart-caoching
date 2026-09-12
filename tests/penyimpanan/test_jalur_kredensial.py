"""Jalur kredensial `PenyimpanPostgres` — T-4 fitur 024, R-02, R-03, R-04.

Tiga tuntutan, dan **urutannya** yang menentukan.

## R-02 · kredensial sebelum data

Kredensial diperiksa sebelum basis data disentuh — sebelum menyambung, sebelum
menyusun kueri. Diuji dengan sambungan yang **melempar bila dipakai**: bila
pemeriksaan bergeser ke belakang kueri, uji gagal dengan galat sambungan alih-
alih lulus diam-diam. Sambungan yang hanya diam tidak membuktikan apa pun.

## R-03 · tanggapan seragam

Pemanggil yang menerima "tidak ditemukan" untuk satu id dan "tidak berwenang"
untuk id lain sudah mengetahui id mana yang ada di karantina. Cukup satu
perbedaan untuk menyusun daftar. Karena itu yang dibandingkan **pesannya
langsung**, bukan dua uji terpisah yang kebetulan sama.

## R-04 · penolakan oleh peladen, bukan oleh kode

Uji paling berharga pada berkas ini, dan satu-satunya yang **tidak dapat
ditiru**: sambungan dibangun dari `peran_penjawaban`, lalu dipakai dengan
kredensial `VERIFIKASI` yang **menurut kode boleh** membaca karantina.

Kode mengizinkan. Peladen menolak. Itu arti "kredensial berbeda, bukan penanda
status" pada C-03 — dan satu-satunya bentuk penjagaan yang bertahan terhadap
kekeliruan kode di kemudian hari.
"""

from __future__ import annotations

import json

import pytest
from src.penyimpanan.area import Area
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenTidakAda
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, VERIFIKASI
from src.penyimpanan.postgres import PenyimpanPostgres
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, psql, siapkan

siapkan()


class SambunganYangMelarang:
    """Melempar bila dipakai. Penjaga atas R-02."""

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        raise AssertionError("basis data disentuh sebelum kredensial diperiksa")

    async def execute(self, kueri: str, *argumen: object) -> object:
        raise AssertionError("basis data disentuh sebelum kredensial diperiksa")


class SambunganNyata:
    """Menyambung sebagai peran tertentu, menutup tiap panggilan.

    Sambungan tidak disimpan: `asyncio.run` membuat gelung peristiwa baru tiap
    pemanggilan, dan sambungan `asyncpg` terikat pada gelung tempat ia dibuka.
    """

    def __init__(self, peran: str) -> None:
        self._peran = peran

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user=self._peran, database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("execute", kueri, *argumen)


@pytest.fixture(scope="module", autouse=True)
def basis_data_siap() -> None:
    psql("smart_coaching", "-c", "CREATE SCHEMA IF NOT EXISTS karantina")
    psql("smart_coaching", "-c", "CREATE SCHEMA IF NOT EXISTS korpus")
    psql(
        "smart_coaching", "-v", "ON_ERROR_STOP=1", "-f", "perkakas/basis_data/04-tabel-dokumen.sql"
    )
    psql("smart_coaching", "-c", "TRUNCATE karantina.dokumen_sumber, korpus.dokumen_sumber")
    isi = json.dumps({"isi": "notulen rapat"})
    psql(
        "smart_coaching",
        "-c",
        f"INSERT INTO karantina.dokumen_sumber (id, isi) VALUES ('dok_karantina', '{isi}'::jsonb)",
    )


# ── R-02 · kredensial diperiksa sebelum basis data disentuh ───────────


@pytest.mark.parametrize("kredensial", [PENJAWABAN, PEMANGGIL_LLM])
def test_baca_ditolak_tanpa_menyentuh_basis_data(kredensial: object) -> None:
    penyimpan = PenyimpanPostgres(SambunganYangMelarang())
    with pytest.raises(GalatAksesDitolak):
        jalankan(penyimpan.baca_dokumen(kredensial, Area.KARANTINA, "dok_karantina"))  # type: ignore[arg-type]


def test_tulis_ditolak_tanpa_menyentuh_basis_data() -> None:
    penyimpan = PenyimpanPostgres(SambunganYangMelarang())
    with pytest.raises(GalatAksesDitolak):
        jalankan(penyimpan.tulis_dokumen(PENJAWABAN, Area.KORPUS, "dok", {"a": 1}))


def test_pindah_memeriksa_kedua_kredensial_sebelum_data() -> None:
    """Memeriksa tujuan sesudah asal terbaca meninggalkan dokumen terbaca oleh
    pemanggil yang tidak berhak menuliskannya ke mana pun."""
    penyimpan = PenyimpanPostgres(SambunganYangMelarang())
    with pytest.raises(GalatAksesDitolak):
        jalankan(penyimpan.pindahkan(PENJAWABAN, "dok", Area.KARANTINA, Area.KORPUS, "uji"))


# ── R-03 · tanggapan seragam ─────────────────────────────────────────


def test_dua_galat_tidak_dapat_dibedakan_dari_luar() -> None:
    penyimpan = PenyimpanPostgres(SambunganYangMelarang())
    pesan = []
    for id_dokumen in ("dok_karantina", "dok_tidak_pernah_ada"):
        try:
            jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, id_dokumen))
        except GalatAksesDitolak as galat:
            pesan.append(galat.tanggapan().galat.pesan_pengguna)
    assert len(pesan) == 2
    assert pesan[0] == pesan[1]


def test_dokumen_tidak_ada_pada_area_yang_boleh_dibaca() -> None:
    """Hanya di sini `GalatDokumenTidakAda` muncul — pada area yang memang
    boleh dibaca. Menuntut peladen: jawabannya datang dari kueri sungguhan."""
    penyimpan = PenyimpanPostgres(SambunganNyata("peran_verifikasi"))
    with pytest.raises(GalatDokumenTidakAda):
        jalankan(penyimpan.baca_dokumen(VERIFIKASI, Area.KORPUS, "tidak_pernah_ada"))


# ── R-04 · ditolak peladen meski kode mengizinkan ────────────────────


def test_peladen_menolak_meski_kode_mengizinkan() -> None:
    """**Uji terpenting berkas ini.**

    `VERIFIKASI` menurut `kredensial_baku.py` boleh membaca karantina, sehingga
    pemeriksaan kode meloloskannya. Sambungannya dibangun dari
    `peran_penjawaban`, yang tidak pernah diberi `USAGE` atas skema karantina.

    Yang menolak peladen. Bila suatu hari kekeliruan kode melonggarkan
    pemeriksaan kredensial, lapisan ini tetap berdiri.
    """
    penyimpan = PenyimpanPostgres(SambunganNyata("peran_penjawaban"))
    assert VERIFIKASI.boleh_baca(Area.KARANTINA), "prasyarat uji: kode mengizinkan"

    with pytest.raises(Exception) as galat:
        jalankan(penyimpan.baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina"))

    assert "permission denied" in str(galat.value).lower(), str(galat.value)
    assert not isinstance(galat.value, GalatAksesDitolak), (
        "penolakan datang dari kode, bukan dari peladen — uji ini kehilangan gunanya"
    )


def test_peran_penjawaban_memang_dapat_membaca_korpus() -> None:
    """Penjaga atas uji di atasnya: peran yang ditolak segalanya juga lulus."""
    isi = json.dumps({"isi": "Permendikdasmen 1/2026"})
    psql(
        "smart_coaching",
        "-c",
        f"INSERT INTO korpus.dokumen_sumber (id, isi) VALUES ('dok_korpus', '{isi}'::jsonb) "
        f"ON CONFLICT (id) DO NOTHING",
    )
    penyimpan = PenyimpanPostgres(SambunganNyata("peran_penjawaban"))
    assert jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_korpus"))
