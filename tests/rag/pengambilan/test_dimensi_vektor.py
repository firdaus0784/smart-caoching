"""Pencocokan dimensi kolom vektor — T-4 fitur 019, R-08.

Ketidakcocokan dimensi **tidak menghasilkan galat yang jelas** bila dibiarkan
sampai kueri: `pgvector` menolak perbandingan antardimensi dengan pesan yang
menyebut angka, bukan menyebut penyemat mana yang salah pasang — dan yang
membacanya sudah berada di lingkungan sungguhan.

Karena itu pemeriksaannya menanyakan **katalog peladen**, bukan tetapan pada
kode. Dua angka yang dibaca dari satu tempat hanya membuktikan angka itu sama
dengan dirinya sendiri.

Menuntut peladen: dimensi kolom hanya ada pada peladen.
"""

from __future__ import annotations

import pytest
from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import PenyematTiruan
from src.rag.pengambilan.vektor import (
    GalatDimensiVektor,
    dimensi_kolom,
    pastikan_dimensi_cocok,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import DIMENSI_UJI, HOST, PORT, psql, siapkan

siapkan()


class SambunganNyata:
    """Menyambung sebagai pengelola, menutup tiap panggilan."""

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user="pengelola", database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("execute", kueri, *argumen)


# ── dimensi dibaca dari peladen ──────────────────────────────────────


@pytest.mark.parametrize("tujuan", list(IndeksTujuan))
def test_dimensi_dibaca_dari_katalog_peladen(tujuan: IndeksTujuan) -> None:
    assert jalankan(dimensi_kolom(SambunganNyata(), tujuan)) == DIMENSI_UJI


@pytest.mark.parametrize("tujuan", list(IndeksTujuan))
def test_penyemat_sepadan_diterima(tujuan: IndeksTujuan) -> None:
    jalankan(pastikan_dimensi_cocok(SambunganNyata(), PenyematTiruan(dimensi=DIMENSI_UJI), tujuan))


# ── ketidakcocokan ditolak saat penyusunan ───────────────────────────


@pytest.mark.parametrize("tujuan", list(IndeksTujuan))
def test_penyemat_berdimensi_lain_ditolak(tujuan: IndeksTujuan) -> None:
    with pytest.raises(GalatDimensiVektor) as galat:
        jalankan(
            pastikan_dimensi_cocok(
                SambunganNyata(), PenyematTiruan(dimensi=DIMENSI_UJI + 1), tujuan
            )
        )
    pesan = str(galat.value)
    assert str(DIMENSI_UJI + 1) in pesan, "dimensi penyemat tidak disebut"
    assert str(DIMENSI_UJI) in pesan, "dimensi kolom tidak disebut"
    assert "penyemat-tiruan" in pesan, "nama penyemat tidak disebut"


def test_kolom_yang_tidak_ada_menyebut_berkas_migrasinya() -> None:
    """Galat pemasangan yang tidak menyebut cara memperbaikinya memaksa yang
    membacanya mencari — di lingkungan sungguhan, saat sesuatu sedang rusak."""
    psql("smart_coaching", "-c", "ALTER TABLE indeks_utama.segmen_teks DROP COLUMN vektor")
    try:
        with pytest.raises(GalatDimensiVektor, match="05-kolom-vektor"):
            jalankan(dimensi_kolom(SambunganNyata(), IndeksTujuan.UTAMA))
    finally:
        psql(
            "smart_coaching",
            "-c",
            f"ALTER TABLE indeks_utama.segmen_teks ADD COLUMN vektor vector({DIMENSI_UJI})",
        )


# ── bidang tabel selaras dengan tipenya ──────────────────────────────


@pytest.mark.parametrize(
    ("tujuan", "skema_wajib"),
    [
        (IndeksTujuan.UTAMA, "indeks_utama"),
        (IndeksTujuan.METADATA, "indeks_metadata"),
    ],
)
def test_kueri_menanyakan_skema_yang_benar(tujuan: IndeksTujuan, skema_wajib: str) -> None:
    """Lubang yang ditemukan uji mutasi T4-4.

    Kedua skema memiliki tabel yang sama persis, sehingga membaca dimensi dari
    skema yang **keliru** menghasilkan jawaban yang sama dan setiap uji atas
    nilainya tetap lulus. Yang dibedakan di sini karena itu bukan hasilnya
    melainkan **argumen yang dikirim ke peladen**.

    Peta yang salah meruntuhkan C-02 tanpa satu galat pun: segmen metadata
    akan dibaca dan ditulis pada indeks yang boleh masuk konteks LLM.
    """
    tertangkap: list[object] = []

    class SambunganPenangkap:
        async def fetchrow(self, kueri: str, *argumen: object) -> object:
            tertangkap.extend(argumen)
            return {"dimensi": DIMENSI_UJI}

        async def execute(self, kueri: str, *argumen: object) -> object:
            raise AssertionError("tidak dipakai")

    jalankan(dimensi_kolom(SambunganPenangkap(), tujuan))
    assert tertangkap[0] == skema_wajib, f"{tujuan} dipetakan ke {tertangkap[0]!r}"


@pytest.mark.parametrize("skema", ["indeks_utama", "indeks_metadata"])
def test_kolom_tabel_selaras_dengan_segmen_terindeks(skema: str) -> None:
    """`SegmenTerindeks` dan DDL adalah dua daftar yang menggambarkan hal yang
    sama. Yang hanyut tidak terlihat dari salah satunya.

    `indeks_tujuan` sengaja **tidak** menjadi kolom: ia terbaca dari skema
    tempat barisnya berada, dan itu yang membuatnya dapat dijaga peladen.

    Diperiksa pada **kedua** skema. Uji mutasi T4-6 menemukan versi
    sebelumnya hanya memeriksa `indeks_utama`, sehingga penyimpangan pada
    tabel metadata lolos tanpa suara.
    """
    from src.penyimpanan.indeks import SegmenTerindeks

    hasil = psql(
        "smart_coaching",
        "-c",
        "select column_name from information_schema.columns "
        f"where table_schema='{skema}' and table_name='segmen_teks'",
    )
    kolom = {b.strip() for b in hasil.stdout.splitlines() if b.strip()}
    bidang = set(SegmenTerindeks.model_fields)

    assert bidang - kolom == {"indeks_tujuan"}, f"bidang tanpa kolom: {sorted(bidang - kolom)}"
    assert kolom - bidang == {"vektor", "diindeks_pada"}, (
        f"kolom tanpa bidang: {sorted(kolom - bidang)}"
    )


def test_katalog_yang_mengembalikan_bukan_bilangan_ditolak() -> None:
    """Penjagaan atas bentuk katalog, bukan atas nilainya.

    `atttypmod` selalu bilangan pada PostgreSQL 16, sehingga cabang ini tidak
    dapat dipicu peladen sungguhan — dan justru karena itu ia diuji dengan
    sambungan buatan. Penjagaan yang tidak pernah dijalankan adalah penjagaan
    yang belum diketahui bekerja atau tidak.
    """

    class SambunganAneh:
        async def fetchrow(self, kueri: str, *argumen: object) -> object:
            return {"dimensi": "seribu dua puluh empat"}

        async def execute(self, kueri: str, *argumen: object) -> object:
            raise AssertionError("tidak dipakai")

    with pytest.raises(GalatDimensiVektor, match="bukan bilangan"):
        jalankan(dimensi_kolom(SambunganAneh(), IndeksTujuan.UTAMA))
