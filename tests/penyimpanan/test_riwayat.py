"""Penyimpan riwayat percakapan — T-3 fitur 028, R-02, R-08, R-12, R-13.

**Satu himpunan uji, dua pelaksana.** Setiap uji perilaku dijalankan atas
`RiwayatMemori` dan `RiwayatPostgres`. Uji yang hanya ada bagi pelaksana
memori menguji tiruan, bukan sistemnya — dan tiruan yang lulus sendirian
adalah tiruan yang kelak berbeda dari yang sungguhan tanpa ada yang tahu.

`RiwayatPostgres` tersambung sebagai `peran_riwayat` sendiri, bukan sebagai
pengelola: uji yang tersambung sebagai pengelola menyembunyikan kegagalan hak
peran produksi (TK-64).

Pemilik tiap uji dibangkitkan acak, sehingga baris uji sebelumnya pada basis
data bersama tidak memengaruhi hasil.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from src.penyimpanan.riwayat import (
    PERAN_RIWAYAT,
    BarisGiliran,
    PenyimpanRiwayat,
    PercakapanTidakAda,
    RiwayatMemori,
    RiwayatPostgres,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, siapkan

AKAR = Path(__file__).resolve().parents[2]
T0 = datetime(2026, 9, 29, 7, 30, tzinfo=UTC)

siapkan()


class SambunganPeran:
    """Satu sambungan baru per kueri, sebagai peran tertentu.

    Sambungan baru tiap kali juga membuat uji R-13 jujur: tidak ada keadaan
    yang tertinggal pada sambungan yang sama.
    """

    def __init__(self, peran: str = PERAN_RIWAYAT) -> None:
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

    async def fetch(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetch", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("execute", kueri, *argumen)


PELAKSANA: dict[str, Callable[[], PenyimpanRiwayat]] = {
    "memori": RiwayatMemori,
    "postgres": lambda: RiwayatPostgres(SambunganPeran()),  # type: ignore[arg-type]
}


@pytest.fixture(params=sorted(PELAKSANA))
def riwayat(request: pytest.FixtureRequest) -> PenyimpanRiwayat:
    return PELAKSANA[request.param]()


def _pemilik() -> str:
    return f"ps_uji_{uuid.uuid4().hex[:12]}"


def _catat(
    r: PenyimpanRiwayat,
    pemilik: str,
    id_percakapan: uuid.UUID,
    pertanyaan: str = "Bagaimana menyusun jadwal supervisi?",
    waktu: datetime = T0,
    id_pesan: str = "pesan-1",
) -> None:
    jalankan(
        r.catat(
            pemilik=pemilik,
            id_percakapan=id_percakapan,
            pertanyaan=pertanyaan,
            id_pesan=id_pesan,
            waktu=waktu,
        )
    )


# ── perilaku bersama ────────────────────────────────────────────────────


def test_giliran_tercatat_dapat_dibaca_berurutan(riwayat: PenyimpanRiwayat) -> None:
    a, p = _pemilik(), uuid.uuid4()
    _catat(riwayat, a, p, "Pertanyaan pertama", T0, "pesan-1")
    _catat(riwayat, a, p, "Pertanyaan kedua", T0 + timedelta(minutes=1), "pesan-2")

    giliran = jalankan(riwayat.baca(pemilik=a, id_percakapan=p))

    assert giliran == (
        BarisGiliran(pertanyaan="Pertanyaan pertama", id_pesan="pesan-1", waktu=T0),
        BarisGiliran(
            pertanyaan="Pertanyaan kedua", id_pesan="pesan-2", waktu=T0 + timedelta(minutes=1)
        ),
    )


def test_daftar_hanya_milik_pemilik_dan_terbaru_lebih_dulu(riwayat: PenyimpanRiwayat) -> None:
    a, b = _pemilik(), _pemilik()
    lama, baru, milik_b = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    _catat(riwayat, a, lama, waktu=T0)
    _catat(riwayat, a, baru, waktu=T0 + timedelta(hours=1))
    _catat(riwayat, b, milik_b, waktu=T0 + timedelta(hours=2))

    assert jalankan(riwayat.daftar(pemilik=a)) == (baru, lama)
    assert jalankan(riwayat.daftar(pemilik=b)) == (milik_b,)
    assert jalankan(riwayat.daftar(pemilik=_pemilik())) == ()


def test_pemilik_lain_tidak_dapat_menulis_dan_tidak_ada_yang_tertulis(
    riwayat: PenyimpanRiwayat,
) -> None:
    a, b, p = _pemilik(), _pemilik(), uuid.uuid4()
    _catat(riwayat, a, p, "Milik A")

    with pytest.raises(PercakapanTidakAda):
        _catat(riwayat, b, p, "Sisipan B")

    assert [g.pertanyaan for g in jalankan(riwayat.baca(pemilik=a, id_percakapan=p))] == ["Milik A"]
    assert jalankan(riwayat.daftar(pemilik=b)) == ()


def test_pemilik_lain_dan_tidak_dikenal_tidak_dapat_dibedakan(riwayat: PenyimpanRiwayat) -> None:
    """R-02, R-03: kedua penolakan berjenis dan berpesan sama persis."""
    a, b, p = _pemilik(), _pemilik(), uuid.uuid4()
    _catat(riwayat, a, p)

    with pytest.raises(PercakapanTidakAda) as milik_orang_lain:
        jalankan(riwayat.baca(pemilik=b, id_percakapan=p))
    with pytest.raises(PercakapanTidakAda) as tidak_dikenal:
        jalankan(riwayat.baca(pemilik=b, id_percakapan=uuid.uuid4()))

    assert type(milik_orang_lain.value) is type(tidak_dikenal.value)
    assert str(milik_orang_lain.value) == str(tidak_dikenal.value)


def test_waktu_percakapan_dari_giliran_pertama(riwayat: PenyimpanRiwayat) -> None:
    """Giliran berikutnya tidak menggeser urutan percakapan pada daftar."""
    a = _pemilik()
    pertama, kedua = uuid.uuid4(), uuid.uuid4()
    _catat(riwayat, a, pertama, waktu=T0)
    _catat(riwayat, a, kedua, waktu=T0 + timedelta(hours=1))
    _catat(riwayat, a, pertama, waktu=T0 + timedelta(hours=2))

    assert jalankan(riwayat.daftar(pemilik=a)) == (kedua, pertama)


@pytest.mark.parametrize(
    ("bidang", "nilai"),
    [("pertanyaan", ""), ("pertanyaan", "   "), ("id_pesan", ""), ("pemilik", "")],
)
def test_isian_kosong_ditolak_tanpa_menulis(
    riwayat: PenyimpanRiwayat, bidang: str, nilai: str
) -> None:
    a, p = _pemilik(), uuid.uuid4()
    argumen = {
        "pemilik": a,
        "id_percakapan": p,
        "pertanyaan": "x",
        "id_pesan": "p",
        "waktu": T0,
        bidang: nilai,
    }
    with pytest.raises(ValueError, match=bidang):
        jalankan(riwayat.catat(**argumen))  # type: ignore[arg-type]
    assert jalankan(riwayat.daftar(pemilik=a)) == ()


def test_waktu_tanpa_zona_ditolak(riwayat: PenyimpanRiwayat) -> None:
    with pytest.raises(ValueError, match="UTC"):
        _catat(riwayat, _pemilik(), uuid.uuid4(), waktu=datetime(2026, 9, 29, 7, 30))


# ── khusus PostgreSQL ───────────────────────────────────────────────────


def test_r13_riwayat_bertahan_antarpenyimpan() -> None:
    """R-13: penyimpan kedua — sambungan lain, objek lain — membaca yang
    ditulis penyimpan pertama. Itu yang terjadi ketika peladen aplikasi
    dimulai ulang."""
    a, p = _pemilik(), uuid.uuid4()
    _catat(RiwayatPostgres(SambunganPeran()), a, p, "Ditulis sebelum dimulai ulang")  # type: ignore[arg-type]

    sesudah = RiwayatPostgres(SambunganPeran())  # type: ignore[arg-type]

    assert jalankan(sesudah.daftar(pemilik=a)) == (p,)
    assert [g.pertanyaan for g in jalankan(sesudah.baca(pemilik=a, id_percakapan=p))] == [
        "Ditulis sebelum dimulai ulang"
    ]


def test_memori_tidak_bertahan_dan_itu_dinyatakan() -> None:
    """Pasangan uji di atas: pelaksana memori memang tidak memenuhi R-13, dan
    uraian kelasnya wajib menyatakannya."""
    a, p = _pemilik(), uuid.uuid4()
    _catat(RiwayatMemori(), a, p)
    assert jalankan(RiwayatMemori().daftar(pemilik=a)) == ()
    assert "R-13" in (RiwayatMemori.__doc__ or "")


# ── permukaan ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("kelas", [RiwayatMemori, RiwayatPostgres])
def test_permukaan_tanpa_ubah_maupun_hapus(kelas: type) -> None:
    """R-08. Yang tidak disediakan tidak dapat dipanggil karena lupa."""
    publik = {n for n in dir(kelas) if not n.startswith("_")}
    assert publik == {"catat", "daftar", "baca"}


def test_peran_riwayat_ada_pada_berkas_sql() -> None:
    """Tetapan peran di kode dan peran di SQL tidak boleh bercerita berbeda."""
    for berkas in ("01-peran-dan-basis-data.sql", "06-riwayat.sql"):
        assert PERAN_RIWAYAT in (AKAR / "perkakas" / "basis_data" / berkas).read_text()


def test_penyimpan_tidak_mengimpor_api_maupun_nlp() -> None:
    """Aturan arah: validasi `Giliran` tinggal di `src/api/`."""
    isi = (AKAR / "src" / "penyimpanan" / "riwayat.py").read_text(encoding="utf-8")
    assert "src.api" not in isi
    assert "src.nlp" not in isi
