"""Penyimpan pembaca sumber — T-4 fitur 032, R-04, R-06, R-07; K-1, K-3; FR-F11.

Bentuk tabelnya D-14 Bagian 5.1 dan `perkakas/basis_data/14-sumber-dan-koleksi.sql`.

## Yang dapat dibaca pembaca

Keberadaan dokumen di **korpus** (kolom `id` saja, bukan teksnya), catatan
metadata dan status terbaru, dan segmen `indeks_utama` satu bagian. Permukaan
ini **tidak memiliki** cara membaca teks dokumen utuh, karantina, maupun
`indeks_metadata` — bukan dilarang, melainkan tidak ada; dan peladen
menolaknya pula (T-2). Ia juga tidak menulis apa pun (R-05).

## Mentah, bukan putusan

Baris dikembalikan apa adanya: penyaringan segmen dan alasan tanpa teks milik
`src/api/sumber.py`. Aturan yang ditulis di dua tempat akan berselisih, dan
yang berselisih di sini adalah teks yang tampil atau tidak.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final, Protocol

from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.sambungan import SambunganAktif

PERAN_PEMBACA_SUMBER: Final = "peran_pembaca_sumber"
"""Peran basis data pembaca sumber — `14-sumber-dan-koleksi.sql`."""


@dataclass(frozen=True)
class BarisSumber:
    """Dokumen korpus beserta catatan metadata dan status terbarunya."""

    id_dokumen: str
    metadata: MetadataDokumen
    status: str | None
    """`None` berarti belum pernah dicatat — **bukan** `berlaku` (TK-81 A)."""
    rujukan_pengganti: str | None


@dataclass(frozen=True)
class SegmenBagian:
    """Satu segmen `indeks_utama` pada bagian yang diminta."""

    teks: str
    lisensi: str
    anonimisasi_terverifikasi: bool


class PembacaSumber(Protocol):
    async def dokumen(self, id_dokumen: str) -> BarisSumber | None:
        """`None` bagi yang tidak di korpus atau tanpa catatan metadata — satu
        bentuk (R-04)."""
        ...

    async def segmen(self, id_dokumen: str, bagian: str) -> tuple[SegmenBagian, ...]:
        """Segmen yang `penanda_bagian`-nya sama persis, berurutan `id_segmen`."""
        ...


@dataclass
class SumberMemori:
    """Pelaksana di memori — bagi uji dan `make jalan` tanpa basis data. Korpus
    `make jalan` kosong, sehingga pelaksana ini selalu menjawab tidak ada."""

    _korpus: set[str] = field(default_factory=set)
    _metadata: list[tuple[str, MetadataDokumen]] = field(default_factory=list)
    _status: list[tuple[str, str, str | None]] = field(default_factory=list)
    _segmen: dict[str, tuple[str, str, SegmenBagian]] = field(default_factory=dict)

    def tanam_dokumen(self, id_dokumen: str) -> None:
        self._korpus.add(id_dokumen)

    def tanam_metadata(self, id_dokumen: str, metadata: MetadataDokumen) -> None:
        self._metadata.append((id_dokumen, metadata))

    def tanam_status(self, id_dokumen: str, status: str, rujukan_pengganti: str | None) -> None:
        self._status.append((id_dokumen, status, rujukan_pengganti))

    def tanam_segmen(
        self, id_segmen: str, id_dokumen: str, bagian: str, segmen: SegmenBagian
    ) -> None:
        self._segmen[id_segmen] = (id_dokumen, bagian, segmen)

    async def dokumen(self, id_dokumen: str) -> BarisSumber | None:
        metadata = [m for i, m in self._metadata if i == id_dokumen]
        if id_dokumen not in self._korpus or not metadata:
            return None
        status = [(s, p) for i, s, p in self._status if i == id_dokumen]
        terakhir, pengganti = status[-1] if status else (None, None)
        return BarisSumber(
            id_dokumen=id_dokumen,
            metadata=metadata[-1],
            status=terakhir,
            rujukan_pengganti=pengganti,
        )

    async def segmen(self, id_dokumen: str, bagian: str) -> tuple[SegmenBagian, ...]:
        return tuple(
            s
            for _, (dok, bag, s) in sorted(self._segmen.items())
            if dok == id_dokumen and bag == bagian
        )


_DOKUMEN: Final = """
SELECT d.id, m.judul, m.jenis, m.penerbit, m.tahun, m.tingkat_kerahasiaan,
       s.status, s.rujukan_pengganti
  FROM korpus.dokumen_sumber d
  JOIN LATERAL (
    SELECT judul, jenis, penerbit, tahun, tingkat_kerahasiaan FROM korpus.metadata_dokumen
     WHERE id_dokumen = d.id ORDER BY nomor DESC LIMIT 1) m ON true
  LEFT JOIN LATERAL (
    SELECT status, rujukan_pengganti FROM korpus.status_dokumen
     WHERE id_dokumen = d.id ORDER BY nomor DESC LIMIT 1) s ON true
 WHERE d.id = $1
"""
"""Hanya kolom `id` dokumen korpus — peran ini tidak memegang hak atas `isi`."""


class PembacaSumberPostgres:
    """Sambungannya wajib tersambung sebagai `PERAN_PEMBACA_SUMBER`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def dokumen(self, id_dokumen: str) -> BarisSumber | None:
        b: Any = await self._sambungan.fetchrow(_DOKUMEN, id_dokumen)
        if b is None:
            return None
        return BarisSumber(
            id_dokumen=str(b["id"]),
            metadata=MetadataDokumen(
                judul=str(b["judul"]),
                jenis=str(b["jenis"]),
                penerbit=str(b["penerbit"]),
                tahun=int(b["tahun"]),
                tingkat_kerahasiaan=str(b["tingkat_kerahasiaan"]),
            ),
            status=b["status"],
            rujukan_pengganti=b["rujukan_pengganti"],
        )

    async def segmen(self, id_dokumen: str, bagian: str) -> tuple[SegmenBagian, ...]:
        baris: Any = await self._sambungan.fetch(
            "SELECT teks, lisensi, anonimisasi_terverifikasi FROM indeks_utama.segmen_teks "
            "WHERE id_dokumen = $1 AND penanda_bagian = $2 ORDER BY id_segmen",
            id_dokumen,
            bagian,
        )
        return tuple(
            SegmenBagian(
                teks=str(b["teks"]),
                lisensi=str(b["lisensi"]),
                anonimisasi_terverifikasi=bool(b["anonimisasi_terverifikasi"]),
            )
            for b in baris
        )
