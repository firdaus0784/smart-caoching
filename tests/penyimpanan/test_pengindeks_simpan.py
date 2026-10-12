"""Penulis indeks — T-5 fitur 038, R-03, R-04, R-05; K-3; P-2 A, P-4 A.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL. Yang kedua
tersambung **sebagai `peran_pengindeks`** (TK-64): uji yang tersambung sebagai
pengelola tidak membuktikan apa pun tentang peran. Dokumen korpus ditanam
lewat jalan masing-masing pelaksana — pemindahan dari karantina pada memori,
pengelola pada PostgreSQL — sebab peran pengindeks sengaja tidak dapat
menaruhnya.

Teks contoh dibuat-buat; tidak ada data pribadi.
"""

from __future__ import annotations

import contextlib
import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenTidakAda
from src.penyimpanan.indeks import SegmenTerindeks, StatusLisensi
from src.penyimpanan.kredensial_baku import (
    PENGINDEKSAN,
    PENJAWABAN,
    PENYEMATAN,
    VERIFIKASI,
)
from src.penyimpanan.pengindeks import (
    PERAN_PENGINDEKS,
    BahanDokumen,
    PenulisIndeks,
    PenulisIndeksMemori,
    PenulisIndeksPostgres,
)
from src.penyimpanan.skema_indeks import SKEMA_INDEKS
from src.penyimpanan.tiruan import PenyimpanTiruan
from tests.konftes_asinkron import jalankan
from tests.peladen import psql, siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA


@dataclass
class Pelaksana:
    penulis: PenulisIndeks
    tanam_korpus: Callable[[str, object, str | None], None]
    tanam_karantina: Callable[[str], None]
    tersimpan: Callable[[IndeksTujuan, str], list[tuple[str, str, str]]]
    """(id_segmen, penanda_bagian, lisensi) berurutan id_segmen."""
    postgres: bool


def _metadata(lisensi: str | None) -> MetadataDokumen:
    return MetadataDokumen(
        judul="Peraturan Contoh",
        jenis="regulasi_resmi",
        penerbit="Kementerian Contoh",
        tahun=2026,
        tingkat_kerahasiaan="publik",
        lisensi=lisensi,
    )


def pelaksana_memori() -> Pelaksana:
    penyimpan = PenyimpanTiruan()
    penulis = PenulisIndeksMemori(penyimpan)

    def tanam_korpus(id_dokumen: str, isi: object, lisensi: str | None) -> None:
        penyimpan.tanam(Area.KARANTINA, id_dokumen, isi)
        jalankan(
            penyimpan.pindahkan(
                VERIFIKASI,
                id_dokumen,
                Area.KARANTINA,
                Area.KORPUS,
                "uji",
                metadata=_metadata(lisensi),
            )
        )

    def tersimpan(indeks: IndeksTujuan, id_dokumen: str) -> list[tuple[str, str, str]]:
        return [
            (s.id_segmen, s.penanda_bagian, s.lisensi.value)
            for s in penulis.segmen_tersimpan(indeks, id_dokumen)
        ]

    return Pelaksana(
        penulis,
        tanam_korpus,
        lambda i: penyimpan.tanam(Area.KARANTINA, i, "Notulen"),
        tersimpan,
        postgres=False,
    )


def _sql_teks(nilai: str | None) -> str:
    return "null" if nilai is None else "'" + nilai.replace("'", "''") + "'"


def _pengelola(kueri: str) -> str:
    hasil = psql("smart_coaching", "-c", kueri)
    assert hasil.returncode == 0 and not hasil.stderr, hasil.stderr
    return hasil.stdout


def pelaksana_postgres() -> Pelaksana:
    def tanam_korpus(id_dokumen: str, isi: object, lisensi: str | None) -> None:
        _pengelola(
            f"insert into korpus.dokumen_sumber (id, isi) values ('{id_dokumen}', "
            f"{_sql_teks(json.dumps(isi))}::jsonb); "
            "insert into korpus.metadata_dokumen (id_dokumen, judul, jenis, penerbit, tahun, "
            f"tingkat_kerahasiaan, lisensi) values ('{id_dokumen}', 'Peraturan Contoh', "
            f"'regulasi_resmi', 'Kementerian Contoh', 2026, 'publik', {_sql_teks(lisensi)})",
        )

    def tanam_karantina(id_dokumen: str) -> None:
        _pengelola(
            f"insert into karantina.dokumen_sumber (id, isi) values ('{id_dokumen}', "
            "'\"Notulen\"'::jsonb)",
        )

    def tersimpan(indeks: IndeksTujuan, id_dokumen: str) -> list[tuple[str, str, str]]:
        keluaran = _pengelola(
            f"select id_segmen || '|' || penanda_bagian || '|' || lisensi "
            f"from {SKEMA_INDEKS[indeks]}.segmen_teks where id_dokumen = '{id_dokumen}' "
            "order by id_segmen",
        )
        return [tuple(b.split("|")) for b in keluaran.split("\n") if b]  # type: ignore[misc]

    return Pelaksana(
        PenulisIndeksPostgres(SambunganPeran(PERAN_PENGINDEKS)),  # type: ignore[arg-type]
        tanam_korpus,
        tanam_karantina,
        tersimpan,
        postgres=True,
    )


@pytest.fixture(params=["memori", "postgres"])
def pelaksana(request: pytest.FixtureRequest) -> Pelaksana:
    return pelaksana_memori() if request.param == "memori" else pelaksana_postgres()


def id_dokumen_baru() -> str:
    return "dok-038-" + secrets.token_hex(4)


def _segmen(
    id_dokumen: str,
    penanda: list[str],
    *,
    lisensi: StatusLisensi = StatusLisensi.TERBUKA,
    indeks: IndeksTujuan = UTAMA,
) -> list[SegmenTerindeks]:
    return [
        SegmenTerindeks(
            id_segmen=f"{id_dokumen}:{i:04d}",
            id_dokumen=id_dokumen,
            teks=f"Isi {p} yang dibuat-buat.",
            lisensi=lisensi,
            indeks_tujuan=indeks,
            anonimisasi_terverifikasi=True,
            penanda_bagian=p,
        )
        for i, p in enumerate(penanda, start=1)
    ]


# ── bahan ────────────────────────────────────────────────────────────


def test_bahan_teks_dan_lisensi_korpus(pelaksana: Pelaksana) -> None:
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, "Pasal 1\nIsi.", "public domain")
    bahan = jalankan(pelaksana.penulis.bahan(PENGINDEKSAN, id_dokumen))
    assert bahan == BahanDokumen(teks="Pasal 1\nIsi.", lisensi="public domain")


def test_bahan_tanpa_keterangan_lisensi_kosong(pelaksana: Pelaksana) -> None:
    """Kosong diteruskan apa adanya; yang membacanya sebagai tertutup
    `lisensi_dari_metadata`, bukan penulis (KL-01)."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, "Isi.", None)
    assert jalankan(pelaksana.penulis.bahan(PENGINDEKSAN, id_dokumen)).lisensi is None


def test_bahan_dokumen_karantina_tidak_ada(pelaksana: Pelaksana) -> None:
    """R-04, C-03: karantina tidak terjangkau — bentuknya sama dengan dokumen
    yang tidak ada di mana pun."""
    di_karantina, tak_ada = id_dokumen_baru(), id_dokumen_baru()
    pelaksana.tanam_karantina(di_karantina)
    for id_dokumen in (di_karantina, tak_ada):
        with pytest.raises(GalatDokumenTidakAda):
            jalankan(pelaksana.penulis.bahan(PENGINDEKSAN, id_dokumen))


def test_bahan_isi_bukan_teks_ditolak_tanpa_kutipan(pelaksana: Pelaksana) -> None:
    """Hanya teks yang dapat dipotong; pesannya tidak memuat isinya (R-07)."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, {"isi": "rahasia-contoh"}, None)
    with pytest.raises(ValueError, match="bukan teks") as galat:
        jalankan(pelaksana.penulis.bahan(PENGINDEKSAN, id_dokumen))
    assert "rahasia-contoh" not in str(galat.value)


def test_bahan_menuntut_baca_korpus(pelaksana: Pelaksana) -> None:
    """Penyematan menulis indeks tetapi tidak membaca korpus."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.penulis.bahan(PENYEMATAN, id_dokumen_baru()))


# ── ganti ────────────────────────────────────────────────────────────


def test_ganti_menyisipkan_ke_indeks_tujuan(pelaksana: Pelaksana) -> None:
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, "Isi.", "public domain")
    jalankan(
        pelaksana.penulis.ganti(
            PENGINDEKSAN, id_dokumen, _segmen(id_dokumen, ["Pasal 1", "Pasal 2"])
        )
    )
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == [
        (f"{id_dokumen}:0001", "Pasal 1", "terbuka"),
        (f"{id_dokumen}:0002", "Pasal 2", "terbuka"),
    ]
    assert pelaksana.tersimpan(METADATA, id_dokumen) == []


def test_ganti_mengganti_bukan_menambah_pada_kedua_indeks(pelaksana: Pelaksana) -> None:
    """Pengindeksan ulang menghapus segmen lama dari **kedua** indeks: dokumen
    yang lisensinya kini tertutup tidak meninggalkan segmen di indeks utama
    (C-02)."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, "Isi.", "public domain")
    penulis = pelaksana.penulis
    jalankan(penulis.ganti(PENGINDEKSAN, id_dokumen, _segmen(id_dokumen, ["A", "B", "C"])))
    jalankan(
        penulis.ganti(
            PENGINDEKSAN,
            id_dokumen,
            _segmen(id_dokumen, ["D"], lisensi=StatusLisensi.TERTUTUP, indeks=METADATA),
        )
    )
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == []
    assert pelaksana.tersimpan(METADATA, id_dokumen) == [(f"{id_dokumen}:0001", "D", "tertutup")]


def test_ganti_tidak_menyentuh_dokumen_lain(pelaksana: Pelaksana) -> None:
    satu, dua = id_dokumen_baru(), id_dokumen_baru()
    for id_dokumen in (satu, dua):
        pelaksana.tanam_korpus(id_dokumen, "Isi.", "public domain")
        jalankan(pelaksana.penulis.ganti(PENGINDEKSAN, id_dokumen, _segmen(id_dokumen, ["A"])))
    jalankan(pelaksana.penulis.ganti(PENGINDEKSAN, satu, []))
    assert pelaksana.tersimpan(UTAMA, satu) == []
    assert pelaksana.tersimpan(UTAMA, dua) == [(f"{dua}:0001", "A", "terbuka")]


def test_ganti_di_luar_korpus_ditolak_tanpa_menulis(pelaksana: Pelaksana) -> None:
    """R-04, M-6: dokumen karantina dan dokumen yang tidak ada tidak sampai ke
    indeks mana pun."""
    di_karantina, tak_ada = id_dokumen_baru(), id_dokumen_baru()
    pelaksana.tanam_karantina(di_karantina)
    for id_dokumen in (di_karantina, tak_ada):
        with pytest.raises(GalatDokumenTidakAda):
            jalankan(pelaksana.penulis.ganti(PENGINDEKSAN, id_dokumen, _segmen(id_dokumen, ["A"])))
        for indeks in IndeksTujuan:
            assert pelaksana.tersimpan(indeks, id_dokumen) == []


@pytest.mark.parametrize("kredensial", [PENJAWABAN, VERIFIKASI], ids=lambda k: k.nama)
def test_ganti_menuntut_tulis_indeks(pelaksana: Pelaksana, kredensial: object) -> None:
    """C-17 dan TK-86: penjawaban dan verifikasi tidak menulis indeks, dan
    ditolak sebelum apa pun disentuh."""
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, "Isi.", "public domain")
    with pytest.raises(PermissionError):
        jalankan(
            pelaksana.penulis.ganti(kredensial, id_dokumen, _segmen(id_dokumen, ["A"]))  # type: ignore[arg-type]
        )
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == []


def test_ganti_menuntut_baca_korpus(pelaksana: Pelaksana) -> None:
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.penulis.ganti(PENYEMATAN, id_dokumen_baru(), []))


@pytest.mark.parametrize("cacat", ["dokumen lain", "pengenal kembar"])
def test_ganti_menolak_segmen_cacat_sebelum_menyentuh(pelaksana: Pelaksana, cacat: str) -> None:
    id_dokumen = id_dokumen_baru()
    pelaksana.tanam_korpus(id_dokumen, "Isi.", "public domain")
    jalankan(pelaksana.penulis.ganti(PENGINDEKSAN, id_dokumen, _segmen(id_dokumen, ["A"])))
    segmen = _segmen(id_dokumen, ["B", "C"])
    if cacat == "dokumen lain":
        segmen = [*segmen, *_segmen(id_dokumen_baru(), ["X"])]
    else:
        segmen = [segmen[0], segmen[0]]
    with pytest.raises(ValueError):
        jalankan(pelaksana.penulis.ganti(PENGINDEKSAN, id_dokumen, segmen))
    assert pelaksana.tersimpan(UTAMA, id_dokumen) == [(f"{id_dokumen}:0001", "A", "terbuka")]


# ── keutuhan — hanya terbukti atas peladen ──────────────────────────


class SambunganPutus:
    """Sambungan peran pengindeks yang putus tepat sebelum panggilan ke-`n`."""

    def __init__(self, n: int) -> None:
        self._dasar = SambunganPeran(PERAN_PENGINDEKS)
        self._n = n
        self._ke = 0

    def _hitung(self) -> None:
        self._ke += 1
        if self._ke == self._n:
            raise ConnectionError("sambungan putus")

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        self._hitung()
        return await self._dasar.fetchrow(kueri, *argumen)

    async def fetch(self, kueri: str, *argumen: object) -> object:
        self._hitung()
        return await self._dasar.fetch(kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        self._hitung()
        return await self._dasar.execute(kueri, *argumen)


@pytest.mark.parametrize("putus_pada", [1, 2, 3])
def test_ganti_utuh_saat_sambungan_putus(putus_pada: int) -> None:
    """R-05, M-5: di titik mana pun sambungan putus, segmen dokumen itu lama
    seluruhnya atau baru seluruhnya — tidak pernah kosong atau separuh."""
    p = pelaksana_postgres()
    id_dokumen = id_dokumen_baru()
    p.tanam_korpus(id_dokumen, "Isi.", "public domain")
    jalankan(p.penulis.ganti(PENGINDEKSAN, id_dokumen, _segmen(id_dokumen, ["A", "B"])))
    lama = p.tersimpan(UTAMA, id_dokumen)
    penulis = PenulisIndeksPostgres(SambunganPutus(putus_pada))  # type: ignore[arg-type]
    with contextlib.suppress(ConnectionError):
        jalankan(penulis.ganti(PENGINDEKSAN, id_dokumen, _segmen(id_dokumen, ["C", "D", "E"])))
    sekarang = p.tersimpan(UTAMA, id_dokumen)
    baru = [(f"{id_dokumen}:{i:04d}", t, "terbuka") for i, t in enumerate("CDE", start=1)]
    assert sekarang in (lama, baru), sekarang
