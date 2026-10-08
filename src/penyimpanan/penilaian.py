"""Penyimpan penilaian jawaban dan aduan kurator — T-4 fitur 036.

FR-F07: *"Pengguna dapat menandai jawaban sebagai membantu / tidak membantu /
keliru, dengan kolom alasan opsional."* FR-I04: kurator melihat jawaban yang
ditandai keliru. Bentuknya D-14 Bagian 4.9 dan 5.1; tabelnya
`perkakas/basis_data/13-penilaian.sql`.

## Dua penyimpan, dua peran

`PenilaianPostgres` tersambung sebagai `peran_penilaian`: memeriksa pemilik
pesan, mencatat penilaian, dan — **hanya bila peserta mencentang** (P-2 B) —
menyalin pertanyaan dan tanggapan ke aduan. `AduanPostgres` tersambung sebagai
`peran_kurasi`, yang tidak memegang hak apa pun atas skema `riwayat`: kurator
membaca salinan, bukan riwayat (R-06).

## Salinan tanpa penaut

Aduan tidak membawa pemilik, percakapan, maupun `id_pesan`. Pengenal pesan
ikut pada peristiwa `answer_rated` (KB-228), sehingga salinan yang memuatnya
dapat ditautkan ke pseudonim oleh pemegang ekspor analitik.

## Satu pernyataan per penulisan

`SambunganAktif` tidak menyediakan transaksi. Pemeriksaan pemilik, penilaian,
aduan, dan pengguguran aduan terdahulu atas pesan yang sama (R-05) karena itu
satu pernyataan CTE. Pesan milik orang lain tidak menulis apa pun dan menolak
dengan `PesanTidakAda` yang **sama persis** dengan pesan yang tidak dikenal.

## Tambah-saja

Tidak ada yang mengubah maupun menghapus. Penilaian yang diganti tetap
tercatat; aduan yang gugur ditandai pada tabel tersendiri. Penarikan data
(NFR-09) berjalan dengan peran tersendiri.

`src/penyimpanan/` tidak mengimpor `src/api/` maupun `src/nlp/`: pemeriksaan
data pribadi pada alasan dan catatan dijalankan rute (KM-03). Yang diperiksa
di sini hanya bentuk yang tabelnya juga tolak, agar kedua pelaksana sepakat.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, Protocol

from src.kamus.penilaian import NilaiPenilaian, TindakLanjutAduan
from src.penyimpanan.kurasi import json_dari
from src.penyimpanan.riwayat import PercakapanTidakAda, RiwayatMemori
from src.penyimpanan.sambungan import SambunganAktif

PERAN_PENILAIAN: Final = "peran_penilaian"
"""Peran basis data penilai — `01-peran-dan-basis-data.sql`, `13-penilaian.sql`."""

_POLA_PSEUDONIM: Final = re.compile(r"^psd_[a-z]{16}$")
_PERAN_KURATOR: Final = frozenset({"kurator", "kurator_pengganti"})


class PesanTidakAda(Exception):
    """Pesan tidak dikenal **atau** milik orang lain — sengaja tak dibedakan."""

    def __init__(self) -> None:
        super().__init__("pesan tidak ada")


@dataclass(frozen=True)
class HasilPenilaian:
    nomor: int
    versi_model: str
    """Versi model pada tanggapan yang dinilai — bagi `answer_rated` (FR-J02)."""


@dataclass(frozen=True)
class BarisAduan:
    """Aduan sebagaimana dibaca kurator. Sengaja tanpa penaut ke peserta."""

    nomor: int
    diadukan_pada: datetime
    pertanyaan: str
    alasan: str | None
    tanggapan: Mapping[str, Any]


class PenyimpanPenilaian(Protocol):
    async def catat(
        self,
        *,
        pemilik: str,
        id_pesan: str,
        nilai: NilaiPenilaian,
        alasan: str | None,
        kirim_ke_kurator: bool,
        waktu: datetime,
    ) -> HasilPenilaian:
        """Catat satu penilaian; salin ke aduan bila dikirim; gugurkan aduan
        terdahulu atas pesan yang sama. `PesanTidakAda` bila bukan milik `pemilik`."""
        ...


class PenyimpanAduan(Protocol):
    async def terbuka(self) -> tuple[BarisAduan, ...]:
        """Aduan yang tidak gugur dan belum bertindak lanjut, terlama lebih dulu."""
        ...

    async def tindak_lanjut(
        self,
        nomor: int,
        *,
        tindak_lanjut: TindakLanjutAduan,
        catatan: str,
        peran: str,
        pseudonim_kurator: str,
        waktu: datetime,
    ) -> bool:
        """`False` bila aduan tidak dikenal, gugur, atau sudah bertindak lanjut."""
        ...


def _utc(waktu: datetime) -> None:
    if waktu.tzinfo is None or waktu.utcoffset() is None or waktu.utcoffset().total_seconds():  # type: ignore[union-attr]
        raise ValueError("waktu wajib berzona UTC (KM-01)")


def _periksa_penilaian(
    pemilik: str, nilai: NilaiPenilaian, alasan: str | None, kirim: bool, waktu: datetime
) -> None:
    if not pemilik.strip():
        raise ValueError("pemilik tidak boleh kosong")
    if kirim and nilai is not NilaiPenilaian.KELIRU:
        raise ValueError("hanya penilaian keliru yang dapat dikirim kepada kurator (P-2 B)")
    if alasan is not None and not alasan.strip():
        raise ValueError("alasan kosong disimpan sebagai ketiadaan, bukan untai kosong")
    _utc(waktu)


def _periksa_tindak_lanjut(catatan: str, peran: str, pseudonim: str, waktu: datetime) -> None:
    if not catatan.strip():
        raise ValueError("catatan tindak lanjut wajib")
    if peran not in _PERAN_KURATOR:
        raise ValueError("peran tindak lanjut bukan kurator")
    if not _POLA_PSEUDONIM.match(pseudonim):
        raise ValueError("pseudonim kurator tidak berpola — tidak pernah nama akun (C-05)")
    _utc(waktu)


def _tanpa_id_pesan(tanggapan: Mapping[str, Any]) -> dict[str, Any]:
    salinan = json.loads(json.dumps(dict(tanggapan)))
    salinan.pop("id_pesan", None)
    return dict(salinan)


def _versi_model(tanggapan: Mapping[str, Any]) -> str:
    """Selalu ada: riwayat menolak mencatat tanggapan tanpanya, dan batasan
    `pesan_bermodel` menolaknya pada peladen (D-14 Bagian 4.1, KT-06)."""
    return str(tanggapan["versi"]["model"])


# ── memori ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Penilaian:
    nomor: int
    id_pesan: str
    nilai: NilaiPenilaian
    alasan: str | None
    kirim_ke_kurator: bool
    waktu: datetime


@dataclass(frozen=True)
class _Aduan:
    baris: BarisAduan
    id_pesan: str
    """Penaut internal pelaksana memori — padanan `nomor_penilaian`. Tidak
    pernah keluar lewat `BarisAduan`."""


class PenilaianMemori:
    """Pelaksana di memori — bagi uji dan `make jalan` tanpa basis data.

    Membaca tanggapan lewat `RiwayatMemori.baris_pesan` dan memeriksa pemilik
    lewat `baca` — padanan hak `SELECT` berkolom `peran_penilaian`.
    """

    def __init__(self, riwayat: RiwayatMemori) -> None:
        self._riwayat = riwayat
        self._penilaian: list[_Penilaian] = []
        self._aduan: list[_Aduan] = []
        self._digantikan: dict[int, datetime] = {}

    async def catat(
        self,
        *,
        pemilik: str,
        id_pesan: str,
        nilai: NilaiPenilaian,
        alasan: str | None,
        kirim_ke_kurator: bool,
        waktu: datetime,
    ) -> HasilPenilaian:
        _periksa_penilaian(pemilik, nilai, alasan, kirim_ke_kurator, waktu)
        pesan = self._riwayat.baris_pesan().get(id_pesan)
        if pesan is None:
            raise PesanTidakAda
        try:
            giliran = await self._riwayat.baca(pemilik=pemilik, id_percakapan=pesan.id_percakapan)
        except PercakapanTidakAda:
            raise PesanTidakAda from None
        pertanyaan = next(g.pertanyaan for g in giliran if g.id_pesan == id_pesan)
        for aduan in self._aduan:
            if aduan.id_pesan == id_pesan:
                self._digantikan.setdefault(aduan.baris.nomor, waktu)
        nomor = len(self._penilaian) + 1
        self._penilaian.append(_Penilaian(nomor, id_pesan, nilai, alasan, kirim_ke_kurator, waktu))
        if kirim_ke_kurator:
            baris = BarisAduan(
                nomor=len(self._aduan) + 1,
                diadukan_pada=waktu,
                pertanyaan=pertanyaan,
                alasan=alasan,
                tanggapan=_tanpa_id_pesan(pesan.tanggapan),
            )
            self._aduan.append(_Aduan(baris=baris, id_pesan=id_pesan))
        return HasilPenilaian(nomor=nomor, versi_model=_versi_model(pesan.tanggapan))

    def baris_aduan(self) -> tuple[BarisAduan, ...]:
        """Seluruh aduan — **hanya** bagi `AduanMemori`, padanan hak `SELECT` kurator."""
        return tuple(a.baris for a in self._aduan)

    def digantikan(self) -> frozenset[int]:
        """Nomor aduan yang gugur — bagi `AduanMemori`."""
        return frozenset(self._digantikan)


class AduanMemori:
    """Antrean aduan di memori; aduan dibaca dari `PenilaianMemori` yang sama."""

    def __init__(self, penilaian: PenilaianMemori) -> None:
        self._penilaian = penilaian
        self._tindak_lanjut: dict[int, tuple[TindakLanjutAduan, str, str, str, datetime]] = {}

    async def terbuka(self) -> tuple[BarisAduan, ...]:
        gugur = self._penilaian.digantikan()
        sisa = [
            a
            for a in self._penilaian.baris_aduan()
            if a.nomor not in gugur and a.nomor not in self._tindak_lanjut
        ]
        return tuple(sorted(sisa, key=lambda a: (a.diadukan_pada, a.nomor)))

    async def tindak_lanjut(
        self,
        nomor: int,
        *,
        tindak_lanjut: TindakLanjutAduan,
        catatan: str,
        peran: str,
        pseudonim_kurator: str,
        waktu: datetime,
    ) -> bool:
        _periksa_tindak_lanjut(catatan, peran, pseudonim_kurator, waktu)
        if nomor not in {a.nomor for a in await self.terbuka()}:
            return False
        self._tindak_lanjut[nomor] = (tindak_lanjut, catatan, peran, pseudonim_kurator, waktu)
        return True


# ── PostgreSQL ───────────────────────────────────────────────────────

_CATAT: Final = """
WITH milik AS (
    SELECT p.id_pesan, p.tanggapan, g.pertanyaan
      FROM riwayat.pesan p
      JOIN riwayat.percakapan c ON c.id_percakapan = p.id_percakapan
      JOIN riwayat.giliran g ON g.id_pesan = p.id_pesan
     WHERE p.id_pesan = $1 AND c.pemilik = $2
     LIMIT 1
), baru AS (
    INSERT INTO riwayat.penilaian (id_pesan, nilai, alasan, kirim_ke_kurator, waktu)
    SELECT id_pesan, $3, $4, $5, $6 FROM milik
    RETURNING nomor
), aduan AS (
    INSERT INTO kurasi.aduan (nomor_penilaian, pertanyaan, tanggapan, alasan, diadukan_pada)
    SELECT b.nomor, m.pertanyaan, m.tanggapan - 'id_pesan', $4, $6
      FROM baru b CROSS JOIN milik m
     WHERE $5
), gugur AS (
    INSERT INTO kurasi.aduan_digantikan (nomor_aduan, waktu)
    SELECT a.nomor, $6
      FROM kurasi.aduan a
      JOIN riwayat.penilaian n ON n.nomor = a.nomor_penilaian
     WHERE n.id_pesan = $1 AND EXISTS (SELECT 1 FROM baru)
    -- Tanpa sasaran konflik: sasaran menuntut hak baca atas kolomnya, dan
    -- penilai tidak perlu tahu aduan mana yang sudah gugur.
    ON CONFLICT DO NOTHING
)
SELECT b.nomor, m.tanggapan FROM baru b CROSS JOIN milik m
"""
"""Pemeriksaan pemilik, penilaian, salinan aduan, dan pengguguran dalam **satu
pernyataan**. Potret pernyataan tidak melihat sisipan `aduan`, sehingga
`gugur` hanya menjangkau aduan **terdahulu** atas pesan ini — tepat yang
dimaksud R-05. Tanpa `milik`, tidak satu sisipan pun menulis."""


class PenilaianPostgres:
    """Pelaksana di atas PostgreSQL; sambungannya wajib sebagai `PERAN_PENILAIAN`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def catat(
        self,
        *,
        pemilik: str,
        id_pesan: str,
        nilai: NilaiPenilaian,
        alasan: str | None,
        kirim_ke_kurator: bool,
        waktu: datetime,
    ) -> HasilPenilaian:
        _periksa_penilaian(pemilik, nilai, alasan, kirim_ke_kurator, waktu)
        baris = await self._sambungan.fetchrow(
            _CATAT, id_pesan, pemilik, nilai.value, alasan, kirim_ke_kurator, waktu
        )
        if baris is None:
            raise PesanTidakAda
        return HasilPenilaian(
            nomor=int(baris["nomor"]),  # type: ignore[call-overload]
            versi_model=_versi_model(json_dari(baris["tanggapan"])),
        )


_TERBUKA: Final = """
SELECT a.nomor, a.diadukan_pada, a.pertanyaan, a.alasan, a.tanggapan
  FROM kurasi.aduan a
 WHERE NOT EXISTS (SELECT 1 FROM kurasi.aduan_digantikan d WHERE d.nomor_aduan = a.nomor)
   AND NOT EXISTS (SELECT 1 FROM kurasi.tindak_lanjut_aduan t WHERE t.nomor_aduan = a.nomor)
 ORDER BY a.diadukan_pada, a.nomor
"""

_TINDAK_LANJUT: Final = """
INSERT INTO kurasi.tindak_lanjut_aduan
       (nomor_aduan, tindak_lanjut, catatan, peran, pseudonim_kurator, waktu)
SELECT a.nomor, $2, $3, $4, $5, $6
  FROM kurasi.aduan a
 WHERE a.nomor = $1
   AND NOT EXISTS (SELECT 1 FROM kurasi.aduan_digantikan d WHERE d.nomor_aduan = a.nomor)
ON CONFLICT (nomor_aduan) DO NOTHING
RETURNING nomor_aduan
"""
"""Aduan gugur tidak dapat ditindaklanjuti; yang kedua ditolak kunci utama."""


class AduanPostgres:
    """Pelaksana di atas PostgreSQL; sambungannya wajib sebagai `PERAN_KURASI`."""

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def terbuka(self) -> tuple[BarisAduan, ...]:
        baris = await self._sambungan.fetch(_TERBUKA)
        return tuple(
            BarisAduan(
                nomor=int(b["nomor"]),  # type: ignore[call-overload]
                diadukan_pada=b["diadukan_pada"],  # type: ignore[arg-type]
                pertanyaan=str(b["pertanyaan"]),
                alasan=None if b["alasan"] is None else str(b["alasan"]),
                tanggapan=json_dari(b["tanggapan"]),
            )
            for b in baris
        )

    async def tindak_lanjut(
        self,
        nomor: int,
        *,
        tindak_lanjut: TindakLanjutAduan,
        catatan: str,
        peran: str,
        pseudonim_kurator: str,
        waktu: datetime,
    ) -> bool:
        _periksa_tindak_lanjut(catatan, peran, pseudonim_kurator, waktu)
        baris = await self._sambungan.fetchrow(
            _TINDAK_LANJUT, nomor, tindak_lanjut.value, catatan, peran, pseudonim_kurator, waktu
        )
        return baris is not None
