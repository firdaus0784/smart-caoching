"""Pemuat korpus jalur penjawab — T-5 fitur 039, R-01, R-04, R-06; K-4.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL. Yang kedua
tersambung **sebagai peran sungguhan** (TK-64): `peran_pemanggil_llm` atas
indeks utama, `peran_penjawaban` atas indeks metadata. Isi ditanam pengelola
pada PostgreSQL, sebab kedua peran itu sengaja tidak dapat menulis.

Indeks pada peladen uji dipakai bersama uji lain, sehingga pernyataan tentang
isi selalu dibatasi pada dokumen milik uji ini. Teks contoh dibuat-buat.
"""

from __future__ import annotations

import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.korpus_penjawab import (
    BarisKorpus,
    PemuatKorpus,
    PemuatKorpusMemori,
    PemuatKorpusPostgres,
)
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, PENYEMATAN
from src.penyimpanan.skema_indeks import SKEMA_INDEKS
from tests.konftes_asinkron import jalankan
from tests.peladen import psql, siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA
PERAN_PEMUAT = {UTAMA: "peran_pemanggil_llm", METADATA: "peran_penjawaban"}
KREDENSIAL_PEMUAT = {UTAMA: PEMANGGIL_LLM, METADATA: PENJAWABAN}


def _metadata(**ubah: object) -> MetadataDokumen:
    bidang: dict[str, object] = {
        "judul": "Peraturan Contoh",
        "jenis": "regulasi_resmi",
        "penerbit": "Kementerian Contoh",
        "tahun": 2026,
        "tingkat_kerahasiaan": "publik",
        "lisensi": "CC BY 4.0",
        "tautan": "https://jdih.contoh.go.id/p/1",
    }
    bidang.update(ubah)
    return MetadataDokumen(**bidang)  # type: ignore[arg-type]


@dataclass
class Pelaksana:
    pemuat: Callable[[IndeksTujuan], PemuatKorpus]
    dokumen: Callable[[str], None]
    metadata: Callable[[str, MetadataDokumen], None]
    status: Callable[[str, str, str | None], None]
    segmen: Callable[[IndeksTujuan, str, str, str, str], None]
    """(indeks, id_segmen, id_dokumen, teks, penanda)"""


def _sql(nilai: object) -> str:
    if nilai is None:
        return "null"
    if isinstance(nilai, int):
        return str(nilai)
    return "'" + str(nilai).replace("'", "''") + "'"


def _pengelola(kueri: str) -> None:
    hasil = psql("smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
    assert hasil.returncode == 0, hasil.stderr


def pelaksana_memori() -> Pelaksana:
    pemuat = PemuatKorpusMemori()
    return Pelaksana(
        pemuat=lambda _indeks: pemuat,
        dokumen=pemuat.tanam_dokumen,
        metadata=pemuat.tanam_metadata,
        status=pemuat.tanam_status,
        segmen=lambda indeks, i, d, teks, penanda: pemuat.tanam_segmen(
            indeks, id_segmen=i, id_dokumen=d, teks=teks, penanda_bagian=penanda
        ),
    )


def pelaksana_postgres() -> Pelaksana:
    def metadata(id_dokumen: str, m: MetadataDokumen) -> None:
        _pengelola(
            "insert into korpus.metadata_dokumen (id_dokumen, judul, jenis, penerbit, tahun, "
            "tingkat_kerahasiaan, lisensi, tautan) values ("
            + ", ".join(
                _sql(v)
                for v in (
                    id_dokumen,
                    m.judul,
                    m.jenis,
                    m.penerbit,
                    m.tahun,
                    m.tingkat_kerahasiaan,
                    m.lisensi,
                    m.tautan,
                )
            )
            + ")"
        )

    def segmen(indeks: IndeksTujuan, i: str, d: str, teks: str, penanda: str) -> None:
        lisensi = "terbuka" if indeks is UTAMA else "tertutup"
        _pengelola(
            f"insert into {SKEMA_INDEKS[indeks]}.segmen_teks (id_segmen, id_dokumen, teks, "
            f"lisensi, anonimisasi_terverifikasi, penanda_bagian) values ({_sql(i)}, {_sql(d)}, "
            f"{_sql(teks)}, '{lisensi}', true, {_sql(penanda)}) "
            "on conflict (id_segmen) do update set teks = excluded.teks"
        )

    return Pelaksana(
        pemuat=lambda indeks: PemuatKorpusPostgres(SambunganPeran(PERAN_PEMUAT[indeks])),  # type: ignore[arg-type]
        dokumen=lambda d: _pengelola(
            f"insert into korpus.dokumen_sumber (id, isi) values ({_sql(d)}, "
            f"{_sql(json.dumps('Isi.'))}::jsonb)"
        ),
        metadata=metadata,
        status=lambda d, s, p: _pengelola(
            "insert into korpus.status_dokumen (id_dokumen, status, rujukan_pengganti) "
            f"values ({_sql(d)}, {_sql(s)}, {_sql(p)})"
        ),
        segmen=segmen,
    )


@pytest.fixture(params=["memori", "postgres"])
def pelaksana(request: pytest.FixtureRequest) -> Pelaksana:
    return pelaksana_memori() if request.param == "memori" else pelaksana_postgres()


def _id() -> str:
    return "dok-039-" + secrets.token_hex(4)


def _milik(baris: tuple[BarisKorpus, ...], *dokumen: str) -> list[BarisKorpus]:
    return [b for b in baris if b.id_dokumen in dokumen]


def _muat(p: Pelaksana, indeks: IndeksTujuan) -> tuple[str, tuple[BarisKorpus, ...]]:
    muatan = jalankan(p.pemuat(indeks).muat(KREDENSIAL_PEMUAT[indeks], indeks))
    return muatan.sidik, muatan.baris


# ── isi ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("indeks", [UTAMA, METADATA], ids=lambda i: i.value)
def test_hanya_segmen_dokumen_korpus_beserta_catatan_terbarunya(
    pelaksana: Pelaksana, indeks: IndeksTujuan
) -> None:
    """R-04, M-2: segmen yang dokumennya tidak di korpus tidak termuat; catatan
    metadata dan status yang dipakai adalah yang terbaru."""
    d, yatim = _id(), _id()
    pelaksana.dokumen(d)
    pelaksana.metadata(d, _metadata(judul="Versi lama"))
    pelaksana.metadata(d, _metadata(judul="Versi baru", tautan=None))
    pelaksana.status(d, "berlaku", None)
    pelaksana.status(d, "diubah", "Peraturan Contoh Nomor 3")
    pelaksana.segmen(indeks, f"{d}:0002", d, "Rencana ditetapkan.", "Pasal 2")
    pelaksana.segmen(indeks, f"{d}:0001", d, "Kepala sekolah menyusun.", "Pasal 1")
    pelaksana.segmen(indeks, f"{yatim}:0001", yatim, "Teks yatim.", "Pasal 1")
    _, baris = _muat(pelaksana, indeks)
    milik = _milik(baris, d, yatim)
    assert [b.id_segmen for b in milik] == [f"{d}:0001", f"{d}:0002"]
    pertama = milik[0]
    assert (pertama.teks, pertama.penanda_bagian) == ("Kepala sekolah menyusun.", "Pasal 1")
    assert pertama.metadata is not None
    assert (pertama.metadata.judul, pertama.metadata.tautan) == ("Versi baru", None)
    assert (pertama.status, pertama.rujukan_pengganti) == ("diubah", "Peraturan Contoh Nomor 3")
    assert pertama.anonimisasi_terverifikasi


def test_tanpa_catatan_metadata_dan_status_tetap_termuat_kosong(pelaksana: Pelaksana) -> None:
    """Kosong diteruskan apa adanya; yang memutus kelayakannya muatan (T-6),
    bukan pemuat."""
    d = _id()
    pelaksana.dokumen(d)
    pelaksana.segmen(UTAMA, f"{d}:0001", d, "Isi.", "Bagian 1")
    (baris,) = _milik(_muat(pelaksana, UTAMA)[1], d)
    assert (baris.metadata, baris.status, baris.rujukan_pengganti) == (None, None, None)


# ── sidik ────────────────────────────────────────────────────────────


def test_sidik_deterministik_dan_sama_dengan_muatan(pelaksana: Pelaksana) -> None:
    d = _id()
    pelaksana.dokumen(d)
    pelaksana.metadata(d, _metadata())
    pelaksana.segmen(UTAMA, f"{d}:0001", d, "Isi.", "Pasal 1")
    sidik_muat, _ = _muat(pelaksana, UTAMA)
    assert _muat(pelaksana, UTAMA)[0] == sidik_muat
    assert jalankan(pelaksana.pemuat(UTAMA).sidik(PEMANGGIL_LLM, UTAMA)) == sidik_muat


@pytest.mark.parametrize("perubahan", ["teks", "metadata", "status"])
def test_sidik_berubah_bersama_isi_metadata_dan_status(
    pelaksana: Pelaksana, perubahan: str
) -> None:
    """R-06, M-9: regulasi yang baru dicabut, atau dokumen yang lisensinya baru
    dicatat ulang, tidak terus dilayani dari muatan lama."""
    d = _id()
    pelaksana.dokumen(d)
    pelaksana.metadata(d, _metadata())
    pelaksana.status(d, "berlaku", None)
    pelaksana.segmen(UTAMA, f"{d}:0001", d, "Isi lama.", "Pasal 1")
    sebelum = jalankan(pelaksana.pemuat(UTAMA).sidik(PEMANGGIL_LLM, UTAMA))
    if perubahan == "teks":
        pelaksana.segmen(UTAMA, f"{d}:0001", d, "Isi baru.", "Pasal 1")
    elif perubahan == "metadata":
        pelaksana.metadata(d, _metadata(lisensi="CC-BY-NC 4.0"))
    else:
        pelaksana.status(d, "dicabut", None)
    assert jalankan(pelaksana.pemuat(UTAMA).sidik(PEMANGGIL_LLM, UTAMA)) != sebelum


# ── kredensial ───────────────────────────────────────────────────────


def test_pemanggil_model_tidak_memuat_indeks_metadata(pelaksana: Pelaksana) -> None:
    """C-02, R-01, M-1: ditolak di kode sebelum peladen disentuh — bentuk yang
    sama dengan jalur penyematan bagi indeks yang tidak dijangkau."""
    pemuat = pelaksana.pemuat(METADATA)
    with pytest.raises(PermissionError):
        jalankan(pemuat.muat(PEMANGGIL_LLM, METADATA))
    with pytest.raises(PermissionError):
        jalankan(pemuat.sidik(PEMANGGIL_LLM, METADATA))


def test_kredensial_tanpa_korpus_ditolak(pelaksana: Pelaksana) -> None:
    """Penyematan menjangkau kedua indeks tetapi tidak membaca korpus."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.pemuat(UTAMA).muat(PENYEMATAN, UTAMA))


class _SambunganIndeksKosong:
    """Peladen yang indeksnya kosong: `string_agg` atas nol baris menghasilkan
    `NULL`, `coalesce` menjadikannya untai kosong, dan peladen meringkasnya."""

    async def fetch(self, kueri: str, *argumen: object) -> list[object]:
        return []

    async def fetchrow(self, kueri: str, *argumen: object) -> dict[str, object]:
        import hashlib

        return {"sidik": hashlib.md5(b"", usedforsecurity=False).hexdigest()}

    async def execute(self, kueri: str, *argumen: object) -> object:  # pragma: no cover
        raise AssertionError("pemuat tidak menulis apa pun (C-17)")


def test_indeks_kosong_sidik_muat_sama_dengan_sidik_peladen() -> None:
    """Tanpa kesamaan ini penjawab membangun ulang muatan pada setiap
    pertanyaan selama korpus kosong — keadaan sistem hari pertama."""
    pemuat = PemuatKorpusPostgres(_SambunganIndeksKosong())  # type: ignore[arg-type]
    muatan = jalankan(pemuat.muat(PEMANGGIL_LLM, UTAMA))
    assert muatan.baris == ()
    assert muatan.sidik == jalankan(pemuat.sidik(PEMANGGIL_LLM, UTAMA))
    memori = PemuatKorpusMemori()
    assert jalankan(memori.muat(PENJAWABAN, METADATA)).sidik == muatan.sidik
