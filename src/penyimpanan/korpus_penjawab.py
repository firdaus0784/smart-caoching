"""Pemuat korpus jalur penjawab — T-5 fitur 039, R-01, R-04, R-06; K-4.

Membaca segmen satu indeks beserta catatan metadata dan status **terbaru**
dokumennya, sebagai baris mentah. Kelayakan — keberlakuan, kerahasiaan,
lisensi yang dibaca ulang — milik `src/api/penjawab_korpus.py`: aturan yang
ditulis di dua tempat akan berselisih (bentuk yang sama dengan pembaca sumber
fitur 032).

## Kredensial, lalu peladen

Diperiksa sebelum peladen disentuh: baca korpus **dan** baca indeks yang
diminta. Pemanggil model atas indeks metadata ditolak di sini dengan
`PermissionError`, bentuk jalur penyematan bagi indeks yang tidak dijangkau;
pada PostgreSQL peran sambungannya ditolak sekali lagi (C-02, dua lapis).

## Hanya dokumen korpus

Segmen yang dokumennya tidak berada di `korpus.dokumen_sumber` tidak termuat
(R-04). Pencabutan sudah menghapus segmen bersama dokumennya (TK-84); syarat
ini lapis kedua, dan ia yang menjaga bila suatu hari tidak.

## Sidik

Ringkasan md5 atas baris kanonik setiap segmen berurutan pengenal: pengenal,
ringkasan teks, penanda, lisensi dan anonimisasi segmen, serta **nomor catatan
metadata dan status terbaru** dokumennya. Perubahan status mengubah sidik,
sehingga regulasi yang baru dicabut tidak terus dilayani dari muatan lama
(R-06). Pada PostgreSQL sidik dihitung peladen dalam pernyataan yang sama
dengan barisnya — satu potret.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Final

from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.sambungan import SambunganAktif
from src.penyimpanan.skema_indeks import SKEMA_INDEKS, TABEL_SEGMEN


@dataclass(frozen=True)
class BarisKorpus:
    """Satu segmen beserta catatan dokumennya, apa adanya.

    Untai, bukan enum ingesti: penyimpanan tidak mengimpor `ingest`.
    """

    id_segmen: str
    id_dokumen: str
    teks: str
    penanda_bagian: str
    lisensi_segmen: str
    """Nilai `StatusLisensi` yang tersimpan saat pengindeksan."""
    anonimisasi_terverifikasi: bool
    metadata: MetadataDokumen | None
    """Catatan metadata terbaru; kosong bila belum pernah dicatat."""
    status: str | None
    """Catatan status terbaru; kosong berarti belum diketahui, **bukan** berlaku."""
    rujukan_pengganti: str | None


@dataclass(frozen=True)
class MuatanKorpus:
    sidik: str
    baris: tuple[BarisKorpus, ...]


def _pastikan_terjangkau(kredensial: Kredensial, indeks: IndeksTujuan) -> None:
    if not kredensial.boleh_baca(Area.KORPUS):
        raise GalatAksesDitolak(kredensial=kredensial, area=Area.KORPUS, operasi="baca")
    if not kredensial.boleh_baca_indeks(indeks):
        raise PermissionError(
            f"kredensial {kredensial.nama!r} tidak menjangkau indeks {indeks.value} — "
            "pemisahan pada sambungan, bukan penyaringan sesudah memuat (C-02)"
        )


class PemuatKorpus(ABC):
    """Kontrak pemuat. Kredensial tepat sesudah `self`."""

    @abstractmethod
    async def muat(self, kredensial: Kredensial, indeks: IndeksTujuan) -> MuatanKorpus:
        """Seluruh segmen dokumen korpus pada satu indeks, berurutan pengenal,
        beserta sidik potret yang sama."""

    @abstractmethod
    async def sidik(self, kredensial: Kredensial, indeks: IndeksTujuan) -> str:
        """Sidik saja — sama dengan `muat(...).sidik` selama isinya sama."""


# ── Memori ────────────────────────────────────────────────────────────


def _kanon(
    id_segmen: str,
    teks: str,
    penanda: str,
    lisensi: str,
    anonimisasi: bool,
    nomor_metadata: int | None,
    nomor_status: int | None,
) -> str:
    return "|".join(
        (
            id_segmen,
            hashlib.md5(teks.encode("utf-8"), usedforsecurity=False).hexdigest(),
            penanda,
            lisensi,
            "true" if anonimisasi else "false",
            "" if nomor_metadata is None else str(nomor_metadata),
            "" if nomor_status is None else str(nomor_status),
        )
    )


def _ringkas(kanon: list[str]) -> str:
    return hashlib.md5("\n".join(kanon).encode("utf-8"), usedforsecurity=False).hexdigest()


@dataclass
class _SegmenMemori:
    id_dokumen: str
    teks: str
    penanda_bagian: str
    lisensi: str


@dataclass
class PemuatKorpusMemori(PemuatKorpus):
    """Pelaksana memori bagi uji; isinya ditanam."""

    _korpus: set[str] = field(default_factory=set)
    _segmen: dict[IndeksTujuan, dict[str, _SegmenMemori]] = field(
        default_factory=lambda: {indeks: {} for indeks in IndeksTujuan}
    )
    _metadata: list[tuple[str, MetadataDokumen]] = field(default_factory=list)
    _status: list[tuple[str, str, str | None]] = field(default_factory=list)

    def tanam_dokumen(self, id_dokumen: str) -> None:
        self._korpus.add(id_dokumen)

    def tanam_metadata(self, id_dokumen: str, metadata: MetadataDokumen) -> None:
        self._metadata.append((id_dokumen, metadata))

    def tanam_status(self, id_dokumen: str, status: str, rujukan_pengganti: str | None) -> None:
        self._status.append((id_dokumen, status, rujukan_pengganti))

    def tanam_segmen(
        self,
        indeks: IndeksTujuan,
        *,
        id_segmen: str,
        id_dokumen: str,
        teks: str,
        penanda_bagian: str,
        lisensi: str | None = None,
    ) -> None:
        bawaan = "terbuka" if indeks is IndeksTujuan.UTAMA else "tertutup"
        self._segmen[indeks][id_segmen] = _SegmenMemori(
            id_dokumen, teks, penanda_bagian, lisensi or bawaan
        )

    def _terbaru_metadata(self, id_dokumen: str) -> tuple[int | None, MetadataDokumen | None]:
        catatan = [(i + 1, m) for i, (d, m) in enumerate(self._metadata) if d == id_dokumen]
        return catatan[-1] if catatan else (None, None)

    def _terbaru_status(self, id_dokumen: str) -> tuple[int | None, str | None, str | None]:
        catatan = [(i + 1, s, p) for i, (d, s, p) in enumerate(self._status) if d == id_dokumen]
        return catatan[-1] if catatan else (None, None, None)

    def _potret(self, indeks: IndeksTujuan) -> MuatanKorpus:
        baris: list[BarisKorpus] = []
        kanon: list[str] = []
        isi = self._segmen[indeks]
        for id_segmen in sorted(isi):
            s = isi[id_segmen]
            if s.id_dokumen not in self._korpus:
                continue
            nomor_m, metadata = self._terbaru_metadata(s.id_dokumen)
            nomor_s, status, pengganti = self._terbaru_status(s.id_dokumen)
            baris.append(
                BarisKorpus(
                    id_segmen=id_segmen,
                    id_dokumen=s.id_dokumen,
                    teks=s.teks,
                    penanda_bagian=s.penanda_bagian,
                    lisensi_segmen=s.lisensi,
                    anonimisasi_terverifikasi=True,
                    metadata=metadata,
                    status=status,
                    rujukan_pengganti=pengganti,
                )
            )
            kanon.append(
                _kanon(id_segmen, s.teks, s.penanda_bagian, s.lisensi, True, nomor_m, nomor_s)
            )
        return MuatanKorpus(sidik=_ringkas(kanon), baris=tuple(baris))

    async def muat(self, kredensial: Kredensial, indeks: IndeksTujuan) -> MuatanKorpus:
        _pastikan_terjangkau(kredensial, indeks)
        return self._potret(indeks)

    async def sidik(self, kredensial: Kredensial, indeks: IndeksTujuan) -> str:
        _pastikan_terjangkau(kredensial, indeks)
        return self._potret(indeks).sidik


# ── PostgreSQL ────────────────────────────────────────────────────────

_KANON_SQL: Final = (
    "s.id_segmen || '|' || md5(s.teks) || '|' || s.penanda_bagian || '|' || s.lisensi "
    "|| '|' || s.anonimisasi_terverifikasi::text || '|' || coalesce(m.nomor::text, '') "
    "|| '|' || coalesce(st.nomor::text, '')"
)
"""Padanan `_kanon` — boolean PostgreSQL bertekst `true` dan `false`."""


def _sumber_sql(indeks: IndeksTujuan) -> str:
    return (
        f"FROM {SKEMA_INDEKS[indeks]}.{TABEL_SEGMEN} s "
        "JOIN korpus.dokumen_sumber d ON d.id = s.id_dokumen "
        "LEFT JOIN LATERAL (SELECT nomor, judul, jenis, penerbit, tahun, tingkat_kerahasiaan, "
        "  lisensi, tautan FROM korpus.metadata_dokumen WHERE id_dokumen = s.id_dokumen "
        "  ORDER BY nomor DESC LIMIT 1) m ON true "
        "LEFT JOIN LATERAL (SELECT nomor, status, rujukan_pengganti FROM korpus.status_dokumen "
        "  WHERE id_dokumen = s.id_dokumen ORDER BY nomor DESC LIMIT 1) st ON true"
    )


def _muat_sql(indeks: IndeksTujuan) -> str:
    return (
        "WITH b AS (SELECT s.id_segmen, s.id_dokumen, s.teks, s.penanda_bagian, "
        "  s.lisensi AS lisensi_segmen, s.anonimisasi_terverifikasi, m.nomor AS nomor_metadata, "
        "  m.judul, m.jenis, m.penerbit, m.tahun, m.tingkat_kerahasiaan, "
        "  m.lisensi AS lisensi_dokumen, m.tautan, st.status, st.rujukan_pengganti, "
        f"  {_KANON_SQL} AS kanon {_sumber_sql(indeks)}) "
        "SELECT b.*, (SELECT md5(coalesce(string_agg(kanon, E'\\n' ORDER BY id_segmen), '')) "
        "  FROM b) AS sidik FROM b ORDER BY b.id_segmen"
    )


def _sidik_sql(indeks: IndeksTujuan) -> str:
    return (
        f"SELECT md5(coalesce(string_agg({_KANON_SQL}, E'\\n' ORDER BY s.id_segmen), '')) "
        f"AS sidik {_sumber_sql(indeks)}"
    )


_SIDIK_KOSONG: Final = _ringkas([])


class PemuatKorpusPostgres(PemuatKorpus):
    """Sambungannya tersambung sebagai `peran_pemanggil_llm` bagi indeks utama
    dan `peran_penjawaban` bagi indeks metadata."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def muat(self, kredensial: Kredensial, indeks: IndeksTujuan) -> MuatanKorpus:
        _pastikan_terjangkau(kredensial, indeks)
        hasil: Any = await self._sambungan.fetch(_muat_sql(indeks))
        if not hasil:
            return MuatanKorpus(sidik=_SIDIK_KOSONG, baris=())
        return MuatanKorpus(sidik=str(hasil[0]["sidik"]), baris=tuple(_baris(b) for b in hasil))

    async def sidik(self, kredensial: Kredensial, indeks: IndeksTujuan) -> str:
        _pastikan_terjangkau(kredensial, indeks)
        hasil: Any = await self._sambungan.fetchrow(_sidik_sql(indeks))
        return str(hasil["sidik"])


def _teks_atau_kosong(nilai: object) -> str | None:
    return None if nilai is None else str(nilai)


def _baris(b: Any) -> BarisKorpus:
    metadata = (
        None
        if b["nomor_metadata"] is None
        else MetadataDokumen(
            judul=str(b["judul"]),
            jenis=str(b["jenis"]),
            penerbit=str(b["penerbit"]),
            tahun=int(b["tahun"]),
            tingkat_kerahasiaan=str(b["tingkat_kerahasiaan"]),
            lisensi=_teks_atau_kosong(b["lisensi_dokumen"]),
            tautan=_teks_atau_kosong(b["tautan"]),
        )
    )
    return BarisKorpus(
        id_segmen=str(b["id_segmen"]),
        id_dokumen=str(b["id_dokumen"]),
        teks=str(b["teks"]),
        penanda_bagian=str(b["penanda_bagian"]),
        lisensi_segmen=str(b["lisensi_segmen"]),
        anonimisasi_terverifikasi=bool(b["anonimisasi_terverifikasi"]),
        metadata=metadata,
        status=_teks_atau_kosong(b["status"]),
        rujukan_pengganti=_teks_atau_kosong(b["rujukan_pengganti"]),
    )
