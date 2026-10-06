"""Penyimpan analitik — T-3 fitur 035, R-02, R-06; K-1.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL; yang kedua
tersambung sebagai `peran_analitik` sendiri. Peristiwa ditanam lewat
`peran_telemetri`, peran yang memang menulisnya.
"""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, timedelta

import pytest
from src.penyimpanan.analitik import (
    PERAN_ANALITIK,
    AnalitikMemori,
    AnalitikPostgres,
    CatatanEkspor,
    PenyimpanAnalitik,
)
from src.penyimpanan.telemetri import (
    PERAN_TELEMETRI,
    BarisPeristiwa,
    PenyimpanTelemetri,
    TelemetriMemori,
    TelemetriPostgres,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

# Jauh di masa depan, agar peristiwa uji lain pada basis data bersama tidak
# masuk rentang yang dibaca uji ini.
T0 = datetime(2031, 3, 4, 1, 0, tzinfo=UTC)


def _psd() -> str:
    return "psd_" + "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(16))


def _baris(pemilik: str, waktu: datetime, jenis: str = "session_start") -> BarisPeristiwa:
    return BarisPeristiwa(
        pseudonim=pemilik,
        jenis=jenis,
        waktu=waktu,
        properti={},
        versi_aplikasi="uji-035",
        versi_model="tanpa_model",
    )


@pytest.fixture(params=["memori", "postgres"])
def pasangan(request: pytest.FixtureRequest) -> tuple[PenyimpanTelemetri, PenyimpanAnalitik]:
    if request.param == "memori":
        telemetri = TelemetriMemori()
        return telemetri, AnalitikMemori(telemetri)
    return (
        TelemetriPostgres(SambunganPeran(PERAN_TELEMETRI)),  # type: ignore[arg-type]
        AnalitikPostgres(SambunganPeran(PERAN_ANALITIK)),  # type: ignore[arg-type]
    )


def test_peristiwa_dalam_rentang_setengah_terbuka_terlama_lebih_dulu(
    pasangan: tuple[PenyimpanTelemetri, PenyimpanAnalitik],
) -> None:
    telemetri, analitik = pasangan

    async def uji() -> None:
        a = _psd()
        for menit in (30, 0, 60, -1):
            await telemetri.tambah(_baris(a, T0 + timedelta(minutes=menit)))
        hasil = await analitik.peristiwa(mulai=T0, sebelum=T0 + timedelta(minutes=60))
        milik = [b for b in hasil if b.pseudonim == a]
        assert [b.waktu for b in milik] == [T0, T0 + timedelta(minutes=30)]
        # Rentang uji sendiri: basis data bersama memuat baris rusak buatan uji
        # fitur 034, dan pembacaan menolaknya keras alih-alih melewatinya.
        semua = [
            b for b in await analitik.peristiwa(mulai=T0 - timedelta(days=1)) if b.pseudonim == a
        ]
        assert len(semua) == 4

    jalankan(uji())


def test_ekspor_tercatat_bernomor_naik(
    pasangan: tuple[PenyimpanTelemetri, PenyimpanAnalitik],
) -> None:
    _, analitik = pasangan

    async def uji() -> None:
        catatan = CatatanEkspor(
            peneliti=_psd(),
            diekspor_pada=T0,
            dari=date(2031, 3, 1),
            sampai=date(2031, 3, 4),
            termasuk_pengembangan=False,
            jumlah_baris=7,
        )
        satu = await analitik.catat_ekspor(catatan)
        dua = await analitik.catat_ekspor(catatan)
        assert dua > satu > 0

    jalankan(uji())


@pytest.mark.parametrize(
    "ganti",
    [
        {"peneliti": "ks-017"},
        {"dari": date(2031, 3, 5)},
        {"jumlah_baris": -1},
        {"diekspor_pada": T0.replace(tzinfo=None)},
    ],
)
def test_catatan_ekspor_salah_ditolak_sama(
    pasangan: tuple[PenyimpanTelemetri, PenyimpanAnalitik], ganti: dict[str, object]
) -> None:
    _, analitik = pasangan
    dasar: dict[str, object] = {
        "peneliti": _psd(),
        "diekspor_pada": T0,
        "dari": date(2031, 3, 1),
        "sampai": date(2031, 3, 4),
        "termasuk_pengembangan": False,
        "jumlah_baris": 7,
    }
    with pytest.raises(ValueError):
        jalankan(analitik.catat_ekspor(CatatanEkspor(**{**dasar, **ganti})))  # type: ignore[arg-type]


def test_permukaan_tanpa_tulis_peristiwa_maupun_ubah_ekspor() -> None:
    """R-07, C-17: analitik membaca peristiwa dan menambah jejak, tidak lebih."""
    for kelas in (AnalitikMemori, AnalitikPostgres):
        nama = {n for n in dir(kelas) if not n.startswith("_")}
        assert nama == {"peristiwa", "catat_ekspor"}, (kelas.__name__, nama)


def test_baris_berproperti_rusak_ditolak_keras_bukan_dilewati() -> None:
    """Integritas S-18: baris rusak menghentikan pembacaan, tidak hilang diam-diam."""

    async def uji() -> None:
        kapan = T0 + timedelta(days=40)
        await SambunganPeran(PERAN_TELEMETRI).execute(
            "INSERT INTO telemetri.peristiwa (pseudonim, jenis, waktu, properti, "
            "versi_aplikasi, versi_model) VALUES ($1, 'session_start', $2, '[]'::jsonb, "
            "'uji', 'tanpa_model')",
            _psd(),
            kapan,
        )
        analitik = AnalitikPostgres(SambunganPeran(PERAN_ANALITIK))  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="bukan objek"):
            await analitik.peristiwa(mulai=kapan, sebelum=kapan + timedelta(seconds=1))

    jalankan(uji())
