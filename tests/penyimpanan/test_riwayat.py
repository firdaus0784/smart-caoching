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


def _tanggapan(id_pesan: str, **lain: object) -> dict[str, object]:
    """Bentuk D-14 Bagian 4.1 yang cukup bagi penyimpan — ia tidak membaca isinya."""
    return {
        "id_pesan": id_pesan,
        "status_dasar": "kuat",
        "penjelasan": "…",
        "versi": {"model": "model-uji", "indeks": "i", "kode": "k"},
        **lain,
    }


def _pesan_unik() -> str:
    """Basis data bersama: `id_pesan` kunci utama, sehingga tiap uji membangkitkannya."""
    return f"msg_uji_{uuid.uuid4().hex[:12]}"


def _catat(
    r: PenyimpanRiwayat,
    pemilik: str,
    id_percakapan: uuid.UUID,
    pertanyaan: str = "Bagaimana menyusun jadwal supervisi?",
    waktu: datetime = T0,
    id_pesan: str | None = None,
) -> str:
    id_pesan = id_pesan or _pesan_unik()
    jalankan(
        r.catat(
            pemilik=pemilik,
            id_percakapan=id_percakapan,
            pertanyaan=pertanyaan,
            id_pesan=id_pesan,
            waktu=waktu,
            tanggapan=_tanggapan(id_pesan),
        )
    )
    return id_pesan


# ── perilaku bersama ────────────────────────────────────────────────────


def test_giliran_tercatat_dapat_dibaca_berurutan(riwayat: PenyimpanRiwayat) -> None:
    a, p = _pemilik(), uuid.uuid4()
    satu = _catat(riwayat, a, p, "Pertanyaan pertama", T0)
    dua = _catat(riwayat, a, p, "Pertanyaan kedua", T0 + timedelta(minutes=1))

    giliran = jalankan(riwayat.baca(pemilik=a, id_percakapan=p))

    assert giliran == (
        BarisGiliran(pertanyaan="Pertanyaan pertama", id_pesan=satu, waktu=T0),
        BarisGiliran(pertanyaan="Pertanyaan kedua", id_pesan=dua, waktu=T0 + timedelta(minutes=1)),
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
        "tanggapan": _tanggapan("p"),
        bidang: nilai,
    }
    with pytest.raises(ValueError, match=bidang):
        jalankan(riwayat.catat(**argumen))  # type: ignore[arg-type]
    assert jalankan(riwayat.daftar(pemilik=a)) == ()


def test_waktu_tanpa_zona_ditolak(riwayat: PenyimpanRiwayat) -> None:
    with pytest.raises(ValueError, match="UTC"):
        _catat(riwayat, _pemilik(), uuid.uuid4(), waktu=datetime(2026, 9, 29, 7, 30))


def test_dapat_ditulis_bagi_baru_dan_milik_sendiri_bukan_milik_orang_lain(
    riwayat: PenyimpanRiwayat,
) -> None:
    """T-6: pemeriksaan sebelum jawaban disusun. Pengenal baru membuka
    percakapan (P-2), sehingga `True`; milik orang lain `False`."""
    a, b, p = _pemilik(), _pemilik(), uuid.uuid4()
    assert jalankan(riwayat.dapat_ditulis(pemilik=a, id_percakapan=p)) is True
    _catat(riwayat, a, p)
    assert jalankan(riwayat.dapat_ditulis(pemilik=a, id_percakapan=p)) is True
    assert jalankan(riwayat.dapat_ditulis(pemilik=b, id_percakapan=p)) is False
    # Membaca tidak meninggalkan jejak: percakapan tetap milik A seorang.
    assert jalankan(riwayat.daftar(pemilik=b)) == ()


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
    # `dapat_ditulis` ditambahkan T-6 (KB-145): pemilik diperiksa **sebelum**
    # jalur penjawab dipanggil. Ia membaca, tidak mengubah.
    harapan = {"catat", "daftar", "baca", "dapat_ditulis"}
    if kelas is RiwayatMemori:
        # Fitur 036: pembaca tanggapan bagi penilaian di memori — padanan hak
        # SELECT `peran_penilaian`. `RiwayatPostgres` tidak menyediakannya,
        # dan `peran_riwayat` tidak dapat membaca tabelnya (C-07).
        harapan |= {"baris_pesan"}
    assert publik == harapan


def test_peran_riwayat_ada_pada_berkas_sql() -> None:
    """Tetapan peran di kode dan peran di SQL tidak boleh bercerita berbeda."""
    for berkas in ("01-peran-dan-basis-data.sql", "06-riwayat.sql"):
        assert PERAN_RIWAYAT in (AKAR / "perkakas" / "basis_data" / berkas).read_text()


def test_penyimpan_tidak_mengimpor_api_maupun_nlp() -> None:
    """Aturan arah: validasi `Giliran` tinggal di `src/api/`."""
    isi = (AKAR / "src" / "penyimpanan" / "riwayat.py").read_text(encoding="utf-8")
    assert "src.api" not in isi
    assert "src.nlp" not in isi


# ── tanggapan sebagai catatan audit — fitur 036, P-1 A ─────────────────


def _pesan_tersimpan(r: PenyimpanRiwayat, id_pesan: str) -> dict[str, object] | None:
    """Dibaca sebagai pengelola pada PostgreSQL: `peran_riwayat` sendiri tidak
    dapat membacanya, dan itu disengaja (C-07)."""
    if isinstance(r, RiwayatMemori):
        baris = r.baris_pesan().get(id_pesan)
        return None if baris is None else dict(baris.tanggapan)
    import json

    b = jalankan(
        SambunganPeran("pengelola").fetchrow(
            "SELECT tanggapan FROM riwayat.pesan WHERE id_pesan = $1", id_pesan
        )
    )
    if b is None:
        return None
    isi = b["tanggapan"]  # type: ignore[index]
    return json.loads(isi) if isinstance(isi, str) else dict(isi)


def test_tanggapan_tercatat_bersama_gilirannya(riwayat: PenyimpanRiwayat) -> None:
    a, p = _pemilik(), uuid.uuid4()
    id_pesan = _catat(riwayat, a, p)
    assert _pesan_tersimpan(riwayat, id_pesan) == _tanggapan(id_pesan)
    # Rute riwayat tetap tidak mengembalikannya.
    (giliran,) = jalankan(riwayat.baca(pemilik=a, id_percakapan=p))
    assert giliran.id_pesan == id_pesan


@pytest.mark.parametrize(
    ("tanggapan", "pesan"),
    [
        (_tanggapan("msg_lain"), "tanggapan milik pesan lain"),
        (_tanggapan("{id}", tingkat_keyakinan=0.9), "tingkat keyakinan"),
        (_tanggapan("{id}", versi={"indeks": "i"}), "versi model"),
    ],
)
def test_tanggapan_salah_bentuk_ditolak_tanpa_menulis(
    riwayat: PenyimpanRiwayat, tanggapan: dict[str, object], pesan: str
) -> None:
    a, p, id_pesan = _pemilik(), uuid.uuid4(), _pesan_unik()
    isi = {k: (id_pesan if v == "{id}" else v) for k, v in tanggapan.items()}
    with pytest.raises(ValueError, match=pesan):
        jalankan(
            riwayat.catat(
                pemilik=a,
                id_percakapan=p,
                pertanyaan="x",
                id_pesan=id_pesan,
                waktu=T0,
                tanggapan=isi,
            )
        )
    assert jalankan(riwayat.daftar(pemilik=a)) == ()
    assert _pesan_tersimpan(riwayat, id_pesan) is None


def test_pesan_ganda_tidak_meninggalkan_giliran_maupun_percakapan(
    riwayat: PenyimpanRiwayat,
) -> None:
    """M-3: giliran dan tanggapan satu pernyataan — gagal yang satu, tidak
    tertulis keduanya. Tanggapan yang tidak tercatat tidak dikirim."""
    a, p1, p2 = _pemilik(), uuid.uuid4(), uuid.uuid4()
    id_pesan = _catat(riwayat, a, p1)
    with pytest.raises(Exception):  # noqa: B017 — penggerak memakai galatnya sendiri
        _catat(riwayat, a, p2, id_pesan=id_pesan)
    assert jalankan(riwayat.daftar(pemilik=a)) == (p1,)
    assert len(jalankan(riwayat.baca(pemilik=a, id_percakapan=p1))) == 1


def test_pemilik_lain_tidak_mencatat_tanggapan(riwayat: PenyimpanRiwayat) -> None:
    a, b, p = _pemilik(), _pemilik(), uuid.uuid4()
    _catat(riwayat, a, p)
    id_pesan = _pesan_unik()
    with pytest.raises(PercakapanTidakAda):
        _catat(riwayat, b, p, id_pesan=id_pesan)
    assert _pesan_tersimpan(riwayat, id_pesan) is None
