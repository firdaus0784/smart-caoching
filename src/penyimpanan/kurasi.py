"""Penyimpan antrean kurasi dan butir tayang — T-3 fitur 013, R-02, R-04, K-1, K-4, K-5.

Bentuk tabelnya D-14 Bagian 4.7 dan 5.1 dan `perkakas/basis_data/09-kurasi.sql`.

## Baris sederhana, bukan model fitur 010

`src/penyimpanan/` tidak mengimpor `src/ingest/` — ia lapisan di bawahnya
(AGENTS.md). Butir disimpan sebagai JSON apa adanya; `src/api/kurasi.py` yang
membentuk `ButirPengetahuan`, `Putusan`, dan `ButirTayang` darinya, dan model
itulah yang menegakkan C-06 dan lapis kedua C-07. Yang diperiksa di sini hanya
bentuk yang tabelnya juga tolak — pemutus berpola pseudonim, empat jenis
putusan, waktu UTC — agar kedua pelaksana menolak sama.

## Dua permukaan, dua peran

`PengisiAntrean` milik perkakas tim (`peran_pengisi_antrean`): menambah
kandidat, memperbarui salinan status regulasi, menarik otomatis.
`PenyimpanKurasi` milik rute kurator (`peran_kurasi`): membaca antrean,
memutus, menarik. Keduanya sengaja tidak disatukan: layar kurator yang dapat
menambah kandidat melewati penyaringan L1 s.d. L3 (FR-I07), dan peladen menolaknya
juga (T-2).

## Satu pernyataan, bukan transaksi

`SambunganAktif` tidak menyediakan transaksi. Putusan yang menyetujui dan
butir tayangnya karena itu ditulis dalam **satu pernyataan** berbentuk
`WITH … INSERT … INSERT`, sehingga tidak ada keadaan antara tempat butir tayang
tanpa putusan, atau putusan setuju tanpa butir tayang. Bentuk yang sama dengan
`riwayat.py`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Any, Final, Protocol

from src.penyimpanan.sambungan import SambunganAktif

PERAN_KURASI: Final = "peran_kurasi"
PERAN_PENGISI_ANTREAN: Final = "peran_pengisi_antrean"
"""Peran basis data — `09-kurasi.sql`. Tanpa tipe kredensial tersendiri, alasan
yang sama dengan `PERAN_RIWAYAT` (KB-142)."""

_POLA_PSEUDONIM: Final = re.compile(r"psd_[a-z]{16}")
_KATEGORI: Final = frozenset(f"K{i}" for i in range(1, 9))
_STATUS: Final = frozenset({"berlaku", "diubah", "dicabut"})
_MENYETUJUI: Final = frozenset({"setujui", "sunting_lalu_setujui"})
_PERAN_PEMUTUS: Final = frozenset({"kurator", "kurator_pengganti"})
_PEMICU: Final = frozenset(
    {"regulasi_sumber_berubah", "kekeliruan_isi_dilaporkan", "data_sumber_diperbarui"}
)
_TINDAKAN: Final = frozenset({"ditarik", "ditandai_perlu_tinjauan"})
"""Salinan nilai `JenisPutusan`, `PeranKurasi`, `Pemicu`, dan `TindakanPenarikan`
fitur 010 — lapisan ini tidak mengimpornya. Kesamaannya dijaga uji, bukan
kepercayaan (`tests/penyimpanan/test_kurasi_selaras.py`)."""


@dataclass(frozen=True)
class BarisKandidat:
    id_butir: str
    butir: dict[str, Any]
    """`ButirPengetahuan` sebagai JSON."""
    sumber: dict[str, Any]
    """Salinan metadata sumber: judul, penerbit, tahun, tautan (K-3)."""
    id_dokumen_sumber: str
    kategori: str
    status_keberlakuan: str | None
    """Salinan yang diperbarui perkakas (K-4); `None` bagi sumber bukan regulasi."""
    masuk_pada: datetime
    kembali_pada: date | None = None


@dataclass(frozen=True)
class PutusanTayang:
    """Putusan yang menayangkan sebuah butir, sebagaimana tersimpan.

    Tiga kolom yang membuktikan **persetujuan**-nya, tanpa pemutus maupun
    alasan. Dengan ini rute penarikan dan feed membentuk `ButirTayang` fitur 010
    lewat `terapkan()` atas putusan sungguhan, alih-alih putusan karangan.
    Peran penayang membaca ketiga kolom ini saja; pemutus dan alasan ditolak
    peladen (T-6, KB-185).
    """

    jenis: str
    peran: str
    waktu: datetime


@dataclass(frozen=True)
class BarisTayang:
    id_butir: str
    butir: dict[str, Any]
    sumber: dict[str, Any]
    id_dokumen_sumber: str
    kategori: str
    status_keberlakuan: str | None
    tayang_pada: datetime
    ditarik_pada: datetime | None = None
    perlu_tinjauan_pada: datetime | None = None
    putusan: PutusanTayang | None = None
    """Putusan yang menayangkannya; `None` hanya bila penyimpan rusak."""


@dataclass(frozen=True)
class CatatanPutusan:
    """Satu baris jejak FR-I05 — peran **dan** pseudonim kurator (K-5)."""

    id_butir: str
    jenis: str
    peran: str
    pseudonim_kurator: str
    alasan: str
    waktu: datetime


class PengisiAntrean(Protocol):
    async def tambah_kandidat(self, kandidat: BarisKandidat) -> bool:
        """`False` bila id butir itu sudah pernah masuk antrean."""
        ...

    async def perbarui_status(self, id_dokumen: str, status: str) -> tuple[str, ...]:
        """Perbarui salinan status setiap kandidat dan butir tayang bersumber
        dokumen itu; kembalikan id butir tayang yang **belum ditarik**."""
        ...

    async def tarik_otomatis(self, id_butir: str, alasan: str, *, sekarang: datetime) -> bool:
        """Penarikan tanpa pemutus — hanya pemicu regulasi (D-06 Bagian 7.5)."""
        ...

    async def dokumen_dikenal(self) -> frozenset[str]:
        """Dokumen sumber kandidat dan butir tayang — masukan lapis L2 `saring()`."""
        ...

    async def jumlah_masuk(self, *, sejak: datetime, sampai: datetime) -> int:
        """Kandidat yang masuk antrean dalam `[sejak, sampai)` — bagi pagu
        kurasi harian TK-72 B (KB-190)."""
        ...


class PenyimpanKurasi(Protocol):
    async def menunggu(self, *, hari_ini: date) -> tuple[BarisKandidat, ...]:
        """Kandidat tanpa putusan akhir, yang tundaannya sudah lewat."""
        ...

    async def satu_menunggu(self, id_butir: str, *, hari_ini: date) -> BarisKandidat | None: ...

    async def tayang_aktif(self) -> tuple[BarisTayang, ...]: ...

    async def setujui(self, catatan: CatatanPutusan, *, butir: dict[str, Any]) -> bool:
        """Putusan menyetujui dan butir tayangnya, satu pernyataan. `butir` adalah
        naskah yang tayang — hasil suntingan bila ada. `False` bila tidak menunggu."""
        ...

    async def tolak(self, catatan: CatatanPutusan) -> bool: ...

    async def tunda(self, catatan: CatatanPutusan, kembali_pada: date) -> bool: ...

    async def tarik(
        self,
        id_butir: str,
        *,
        pemicu: str,
        tindakan: str,
        peran: str,
        pseudonim_kurator: str,
        alasan: str,
        sekarang: datetime,
    ) -> bool:
        """`False` bila butir tidak sedang tayang."""
        ...


def _utc(waktu: datetime) -> None:
    offset = waktu.utcoffset()
    if offset is None or offset.total_seconds():
        raise ValueError("waktu wajib berzona UTC (KM-01)")


def _pseudonim(nilai: str) -> None:
    if _POLA_PSEUDONIM.fullmatch(nilai) is None:
        raise ValueError("pemutus wajib pseudonim akun, bukan nama akun (C-05, K-5)")


def _isi(nilai: str, nama: str) -> None:
    if not nilai.strip():
        raise ValueError(f"{nama} wajib terisi")


def _catatan(catatan: CatatanPutusan, *jenis: str) -> None:
    if catatan.jenis not in jenis:
        raise ValueError(f"jenis putusan {catatan.jenis!r} tidak sesuai jalurnya")
    if catatan.peran not in _PERAN_PEMUTUS:
        raise ValueError("peran pemutus di luar D-06 Bagian 7.1")
    _pseudonim(catatan.pseudonim_kurator)
    _isi(catatan.alasan, "alasan")
    _utc(catatan.waktu)


def _status(status: str | None) -> None:
    if status is not None and status not in _STATUS:
        raise ValueError("status keberlakuan di luar tiga nilai KL-07")


def _kandidat(kandidat: BarisKandidat) -> None:
    _isi(kandidat.id_butir, "id butir")
    _isi(kandidat.id_dokumen_sumber, "dokumen sumber")
    if kandidat.kategori not in _KATEGORI:
        raise ValueError("kategori di luar K1 s.d. K8")
    _status(kandidat.status_keberlakuan)
    _utc(kandidat.masuk_pada)


def _penarikan(pemicu: str, tindakan: str, alasan: str, sekarang: datetime) -> None:
    if pemicu not in _PEMICU or tindakan not in _TINDAKAN:
        raise ValueError("pemicu atau tindakan penarikan di luar D-06 Bagian 7.5")
    _isi(alasan, "alasan")
    _utc(sekarang)


def json_dari(nilai: object) -> dict[str, Any]:
    """Kolom `jsonb` sebagaimana dikembalikan penggerak — untai atau kamus."""
    hasil = json.loads(nilai) if isinstance(nilai, str) else nilai
    if not isinstance(hasil, dict):
        raise TypeError("kolom JSON bukan objek")
    return hasil


# ── memori ───────────────────────────────────────────────────────────


@dataclass
class _Isi:
    kandidat: dict[str, BarisKandidat] = field(default_factory=dict)
    putusan: list[CatatanPutusan] = field(default_factory=list)
    tayang: dict[str, BarisTayang] = field(default_factory=dict)
    penarikan: list[tuple[str, str, str]] = field(default_factory=list)


class KurasiMemori:
    """Pelaksana di memori bagi kedua permukaan — bagi uji dan `make jalan`
    tanpa basis data. Hilang ketika proses berhenti."""

    def __init__(self) -> None:
        self._isi = _Isi()

    # PengisiAntrean

    async def tambah_kandidat(self, kandidat: BarisKandidat) -> bool:
        _kandidat(kandidat)
        if kandidat.id_butir in self._isi.kandidat:
            return False
        self._isi.kandidat[kandidat.id_butir] = kandidat
        return True

    async def perbarui_status(self, id_dokumen: str, status: str) -> tuple[str, ...]:
        if status not in _STATUS:
            raise ValueError("status keberlakuan di luar tiga nilai KL-07")
        for kunci, k in list(self._isi.kandidat.items()):
            if k.id_dokumen_sumber == id_dokumen:
                self._isi.kandidat[kunci] = replace(k, status_keberlakuan=status)
        aktif = []
        for kunci, t in list(self._isi.tayang.items()):
            if t.id_dokumen_sumber == id_dokumen:
                self._isi.tayang[kunci] = replace(t, status_keberlakuan=status)
                if t.ditarik_pada is None:
                    aktif.append(kunci)
        return tuple(sorted(aktif))

    async def tarik_otomatis(self, id_butir: str, alasan: str, *, sekarang: datetime) -> bool:
        _penarikan("regulasi_sumber_berubah", "ditarik", alasan, sekarang)
        return self._tarik(id_butir, "regulasi_sumber_berubah", "ditarik", alasan, sekarang)

    async def dokumen_dikenal(self) -> frozenset[str]:
        return frozenset(k.id_dokumen_sumber for k in self._isi.kandidat.values())

    async def jumlah_masuk(self, *, sejak: datetime, sampai: datetime) -> int:
        _utc(sejak)
        _utc(sampai)
        return sum(1 for k in self._isi.kandidat.values() if sejak <= k.masuk_pada < sampai)

    # PenyimpanKurasi

    def _akhir(self, id_butir: str) -> bool:
        return any(p.id_butir == id_butir and p.jenis != "tunda" for p in self._isi.putusan)

    def _menunggu(self, k: BarisKandidat, hari_ini: date) -> bool:
        if self._akhir(k.id_butir):
            return False
        return k.kembali_pada is None or k.kembali_pada <= hari_ini

    async def menunggu(self, *, hari_ini: date) -> tuple[BarisKandidat, ...]:
        semua = [k for k in self._isi.kandidat.values() if self._menunggu(k, hari_ini)]
        return tuple(sorted(semua, key=lambda k: (k.masuk_pada, k.id_butir)))

    async def satu_menunggu(self, id_butir: str, *, hari_ini: date) -> BarisKandidat | None:
        k = self._isi.kandidat.get(id_butir)
        return k if k is not None and self._menunggu(k, hari_ini) else None

    async def tayang_aktif(self) -> tuple[BarisTayang, ...]:
        aktif = [t for t in self._isi.tayang.values() if t.ditarik_pada is None]
        return tuple(sorted(aktif, key=lambda t: (t.tayang_pada, t.id_butir)))

    def _dapat_diputus(self, id_butir: str) -> BarisKandidat | None:
        k = self._isi.kandidat.get(id_butir)
        return None if k is None or self._akhir(id_butir) else k

    async def setujui(self, catatan: CatatanPutusan, *, butir: dict[str, Any]) -> bool:
        _catatan(catatan, *_MENYETUJUI)
        k = self._dapat_diputus(catatan.id_butir)
        if k is None:
            return False
        self._isi.putusan.append(catatan)
        self._isi.tayang[k.id_butir] = BarisTayang(
            id_butir=k.id_butir,
            butir=dict(butir),
            sumber=k.sumber,
            id_dokumen_sumber=k.id_dokumen_sumber,
            kategori=k.kategori,
            status_keberlakuan=k.status_keberlakuan,
            tayang_pada=catatan.waktu,
            putusan=PutusanTayang(jenis=catatan.jenis, peran=catatan.peran, waktu=catatan.waktu),
        )
        return True

    async def tolak(self, catatan: CatatanPutusan) -> bool:
        _catatan(catatan, "tolak")
        if self._dapat_diputus(catatan.id_butir) is None:
            return False
        self._isi.putusan.append(catatan)
        return True

    async def tunda(self, catatan: CatatanPutusan, kembali_pada: date) -> bool:
        _catatan(catatan, "tunda")
        k = self._dapat_diputus(catatan.id_butir)
        if k is None:
            return False
        self._isi.putusan.append(catatan)
        self._isi.kandidat[k.id_butir] = replace(k, kembali_pada=kembali_pada)
        return True

    async def tarik(
        self,
        id_butir: str,
        *,
        pemicu: str,
        tindakan: str,
        peran: str,
        pseudonim_kurator: str,
        alasan: str,
        sekarang: datetime,
    ) -> bool:
        _penarikan(pemicu, tindakan, alasan, sekarang)
        if peran not in _PERAN_PEMUTUS:
            raise ValueError("peran pemutus di luar D-06 Bagian 7.1")
        _pseudonim(pseudonim_kurator)
        return self._tarik(id_butir, pemicu, tindakan, alasan, sekarang)

    def _tarik(
        self, id_butir: str, pemicu: str, tindakan: str, alasan: str, waktu: datetime
    ) -> bool:
        t = self._isi.tayang.get(id_butir)
        if t is None or t.ditarik_pada is not None:
            return False
        self._isi.penarikan.append((id_butir, pemicu, tindakan))
        if tindakan == "ditarik":
            self._isi.tayang[id_butir] = replace(t, ditarik_pada=waktu)
        else:
            self._isi.tayang[id_butir] = replace(t, perlu_tinjauan_pada=waktu)
        return True

    def baris_tayang(self) -> dict[str, BarisTayang]:
        """Bagi `PenemuanMemori` — salinan, bukan rujukan ke isi."""
        return dict(self._isi.tayang)

    def jejak(self) -> tuple[CatatanPutusan, ...]:
        """Seluruh putusan tercatat — bagi uji jejak FR-I05."""
        return tuple(self._isi.putusan)


# ── PostgreSQL ───────────────────────────────────────────────────────

_KOLOM_KANDIDAT: Final = (
    "k.id_butir, k.butir, k.sumber, k.id_dokumen_sumber, k.kategori, "
    "k.status_keberlakuan, k.masuk_pada, k.kembali_pada"
)
KOLOM_TAYANG: Final = (
    "b.id_butir, b.butir, b.sumber, b.id_dokumen_sumber, b.kategori, b.status_keberlakuan, "
    "b.tayang_pada, b.ditarik_pada, b.perlu_tinjauan_pada, p.jenis, p.peran, p.waktu "
    "FROM kurasi.butir_tayang b JOIN kurasi.putusan p ON p.nomor = b.nomor_putusan"
)
"""Kolom butir tayang beserta putusan yang menayangkannya — `SELECT` + ini."""

_MENUNGGU: Final = f"""
SELECT {_KOLOM_KANDIDAT} FROM kurasi.kandidat k
 WHERE NOT EXISTS (SELECT 1 FROM kurasi.putusan p
                    WHERE p.id_butir = k.id_butir AND p.jenis <> 'tunda')
   AND (k.kembali_pada IS NULL OR k.kembali_pada <= $1)
"""

_DAPAT_DIPUTUS: Final = """
  FROM kurasi.kandidat k
 WHERE k.id_butir = $1
   AND NOT EXISTS (SELECT 1 FROM kurasi.putusan x
                    WHERE x.id_butir = k.id_butir AND x.jenis <> 'tunda')
"""

_SISIP_PUTUSAN: Final = (
    "INSERT INTO kurasi.putusan (id_butir, jenis, peran, pseudonim_kurator, alasan, waktu) "
    "SELECT k.id_butir, $2, $3, $4, $5, $6" + _DAPAT_DIPUTUS
)

_SETUJUI: Final = f"""
WITH p AS ({_SISIP_PUTUSAN} RETURNING nomor, id_butir)
INSERT INTO kurasi.butir_tayang
  (id_butir, butir, sumber, id_dokumen_sumber, kategori, status_keberlakuan,
   nomor_putusan, tayang_pada)
SELECT p.id_butir, $7::jsonb, k.sumber, k.id_dokumen_sumber, k.kategori,
       k.status_keberlakuan, p.nomor, $6
  FROM p JOIN kurasi.kandidat k USING (id_butir)
RETURNING id_butir
"""

_TUNDA: Final = f"""
WITH p AS ({_SISIP_PUTUSAN} RETURNING id_butir)
UPDATE kurasi.kandidat k SET kembali_pada = $7 FROM p
 WHERE k.id_butir = p.id_butir
RETURNING k.id_butir
"""

_TARIK: Final = """
WITH t AS (
  INSERT INTO kurasi.penarikan (id_butir, pemicu, tindakan, peran, pseudonim_kurator, alasan, waktu)
  SELECT b.id_butir, $2, $3::text, $4, $5, $6, $7 FROM kurasi.butir_tayang b
   WHERE b.id_butir = $1 AND b.ditarik_pada IS NULL
  RETURNING id_butir)
UPDATE kurasi.butir_tayang b SET
  ditarik_pada = CASE WHEN $3::text = 'ditarik' THEN $7 ELSE b.ditarik_pada END,
  alasan_tarik = CASE WHEN $3::text = 'ditarik' THEN $6 ELSE b.alasan_tarik END,
  perlu_tinjauan_pada = CASE WHEN $3::text = 'ditandai_perlu_tinjauan' THEN $7
                             ELSE b.perlu_tinjauan_pada END
  FROM t WHERE b.id_butir = t.id_butir
RETURNING b.id_butir
"""

_TARIK_OTOMATIS: Final = """
WITH t AS (
  UPDATE kurasi.butir_tayang b SET ditarik_pada = $3, alasan_tarik = $2
   WHERE b.id_butir = $1 AND b.ditarik_pada IS NULL
  RETURNING b.id_butir)
INSERT INTO kurasi.penarikan (id_butir, pemicu, tindakan, alasan, waktu)
SELECT id_butir, 'regulasi_sumber_berubah', 'ditarik', $2, $3 FROM t
"""
"""Tanpa `RETURNING` dari `penarikan`: peran pengisi hanya memegang `INSERT` atas
tabel itu, dan hak baca tidak ditambahkan demi satu nilai kembali. Jumlah baris
dibaca dari status perintah."""


def _jumlah(status: object) -> int:
    """`INSERT 0 1` → 1. Status perintah sebagaimana dikembalikan penggerak."""
    return int(str(status).rsplit(" ", 1)[-1])


_PERBARUI_STATUS: Final = """
WITH k AS (
  UPDATE kurasi.kandidat SET status_keberlakuan = $2 WHERE id_dokumen_sumber = $1
  RETURNING id_butir)
UPDATE kurasi.butir_tayang SET status_keberlakuan = $2 WHERE id_dokumen_sumber = $1
RETURNING id_butir, ditarik_pada
"""


def _baris_kandidat(b: Any) -> BarisKandidat:
    return BarisKandidat(
        id_butir=str(b["id_butir"]),
        butir=json_dari(b["butir"]),
        sumber=json_dari(b["sumber"]),
        id_dokumen_sumber=str(b["id_dokumen_sumber"]),
        kategori=str(b["kategori"]),
        status_keberlakuan=b["status_keberlakuan"],
        masuk_pada=b["masuk_pada"],
        kembali_pada=b["kembali_pada"],
    )


def baris_tayang(b: Any) -> BarisTayang:
    """Baris hasil `KOLOM_TAYANG`."""
    return BarisTayang(
        id_butir=str(b["id_butir"]),
        butir=json_dari(b["butir"]),
        sumber=json_dari(b["sumber"]),
        id_dokumen_sumber=str(b["id_dokumen_sumber"]),
        kategori=str(b["kategori"]),
        status_keberlakuan=b["status_keberlakuan"],
        tayang_pada=b["tayang_pada"],
        ditarik_pada=b["ditarik_pada"],
        perlu_tinjauan_pada=b["perlu_tinjauan_pada"],
        putusan=PutusanTayang(jenis=str(b["jenis"]), peran=str(b["peran"]), waktu=b["waktu"]),
    )


class PengisiAntreanPostgres:
    """Sambungannya wajib tersambung sebagai `PERAN_PENGISI_ANTREAN`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def tambah_kandidat(self, kandidat: BarisKandidat) -> bool:
        _kandidat(kandidat)
        b = await self._sambungan.fetchrow(
            "INSERT INTO kurasi.kandidat (id_butir, butir, sumber, id_dokumen_sumber, kategori, "
            "status_keberlakuan, masuk_pada, kembali_pada) "
            "VALUES ($1, $2::jsonb, $3::jsonb, $4, $5, $6, $7, $8) "
            "ON CONFLICT (id_butir) DO NOTHING RETURNING id_butir",
            kandidat.id_butir,
            json.dumps(kandidat.butir),
            json.dumps(kandidat.sumber),
            kandidat.id_dokumen_sumber,
            kandidat.kategori,
            kandidat.status_keberlakuan,
            kandidat.masuk_pada,
            kandidat.kembali_pada,
        )
        return b is not None

    async def perbarui_status(self, id_dokumen: str, status: str) -> tuple[str, ...]:
        if status not in _STATUS:
            raise ValueError("status keberlakuan di luar tiga nilai KL-07")
        baris = await self._sambungan.fetch(_PERBARUI_STATUS, id_dokumen, status)
        return tuple(sorted(str(b["id_butir"]) for b in baris if b["ditarik_pada"] is None))

    async def tarik_otomatis(self, id_butir: str, alasan: str, *, sekarang: datetime) -> bool:
        _penarikan("regulasi_sumber_berubah", "ditarik", alasan, sekarang)
        return (
            _jumlah(await self._sambungan.execute(_TARIK_OTOMATIS, id_butir, alasan, sekarang)) > 0
        )

    async def dokumen_dikenal(self) -> frozenset[str]:
        baris = await self._sambungan.fetch(
            "SELECT id_dokumen_sumber FROM kurasi.kandidat "
            "UNION SELECT id_dokumen_sumber FROM kurasi.butir_tayang"
        )
        return frozenset(str(b["id_dokumen_sumber"]) for b in baris)

    async def jumlah_masuk(self, *, sejak: datetime, sampai: datetime) -> int:
        _utc(sejak)
        _utc(sampai)
        b = await self._sambungan.fetchrow(
            "SELECT count(*) AS n FROM kurasi.kandidat WHERE masuk_pada >= $1 AND masuk_pada < $2",
            sejak,
            sampai,
        )
        return 0 if b is None else int(b["n"])  # type: ignore[call-overload]


class KurasiPostgres:
    """Sambungannya wajib tersambung sebagai `PERAN_KURASI`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def menunggu(self, *, hari_ini: date) -> tuple[BarisKandidat, ...]:
        baris = await self._sambungan.fetch(
            _MENUNGGU + " ORDER BY k.masuk_pada, k.id_butir", hari_ini
        )
        return tuple(_baris_kandidat(b) for b in baris)

    async def satu_menunggu(self, id_butir: str, *, hari_ini: date) -> BarisKandidat | None:
        b = await self._sambungan.fetchrow(_MENUNGGU + " AND k.id_butir = $2", hari_ini, id_butir)
        return None if b is None else _baris_kandidat(b)

    async def tayang_aktif(self) -> tuple[BarisTayang, ...]:
        baris = await self._sambungan.fetch(
            f"SELECT {KOLOM_TAYANG} WHERE b.ditarik_pada IS NULL ORDER BY b.tayang_pada, b.id_butir"
        )
        return tuple(baris_tayang(b) for b in baris)

    async def _putuskan(self, kueri: str, catatan: CatatanPutusan, *lebih: object) -> bool:
        b = await self._sambungan.fetchrow(
            kueri,
            catatan.id_butir,
            catatan.jenis,
            catatan.peran,
            catatan.pseudonim_kurator,
            catatan.alasan,
            catatan.waktu,
            *lebih,
        )
        return b is not None

    async def setujui(self, catatan: CatatanPutusan, *, butir: dict[str, Any]) -> bool:
        _catatan(catatan, *_MENYETUJUI)
        return await self._putuskan(_SETUJUI, catatan, json.dumps(butir))

    async def tolak(self, catatan: CatatanPutusan) -> bool:
        _catatan(catatan, "tolak")
        return await self._putuskan(_SISIP_PUTUSAN + " RETURNING nomor", catatan)

    async def tunda(self, catatan: CatatanPutusan, kembali_pada: date) -> bool:
        _catatan(catatan, "tunda")
        return await self._putuskan(_TUNDA, catatan, kembali_pada)

    async def tarik(
        self,
        id_butir: str,
        *,
        pemicu: str,
        tindakan: str,
        peran: str,
        pseudonim_kurator: str,
        alasan: str,
        sekarang: datetime,
    ) -> bool:
        _penarikan(pemicu, tindakan, alasan, sekarang)
        if peran not in _PERAN_PEMUTUS:
            raise ValueError("peran pemutus di luar D-06 Bagian 7.1")
        _pseudonim(pseudonim_kurator)
        b = await self._sambungan.fetchrow(
            _TARIK, id_butir, pemicu, tindakan, peran, pseudonim_kurator, alasan, sekarang
        )
        return b is not None
