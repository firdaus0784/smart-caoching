"""Catatan keadaan gerbang ingesti — T-4 fitur 037, P-1 A, P-2 A, TK-84 A, TK-85 A.

Gerbang fitur 002 menyimpan keadaannya di memori: metadata dokumen karantina,
temuan pola, tinjauan, putusan, dan jejak. Perkakas yang dijalankan per
perintah kehilangan semuanya sebelum verifikator sempat menilai. Modul ini
menyimpannya sebagai **catatan tambah-saja** dan **menurunkan** keadaannya —
tidak ada kolom status yang disunting (P-1 A).

**Aturan tidak tinggal di sini.** Kelayakan persetujuan, gerbang pola
adversarial, dan persetujuan pemilik tetap milik `src/ingest/gerbang.py`.
Modul ini hanya mencatat dan membaca, sehingga pelaksana memori dan PostgreSQL
tidak dapat berselisih tentang aturan: keduanya lulus uji kontrak yang sama.

**Untai dan bilangan, bukan enum ingesti.** Penyimpanan berada di bawah
ingesti dan tidak mengimpornya — alasan yang sama dengan `MetadataDokumen`.

**Penurunan keadaan bagi penerimaan terbaru `P`:**

- area: tabel tempat teksnya berada;
- status anonimisasi: putusan setujui atau tolak terbaru yang merujuk `P`,
  tanpanya `menunggu`;
- persetujuan dicabut: ada putusan pencabutan yang merujuk `P`;
- temuan dan tinjauan: yang merujuk `P` saja — unggahan ulang membatalkan
  tinjauan lama tanpa menghapusnya (R-03);
- alasan terakhir: jejak terbaru dokumen itu, merujuk penerimaan mana pun.

Kredensial diperiksa kode **sebelum** apa pun disentuh; pada PostgreSQL peran
sambungannya menolak sekali lagi (C-03, dua lapis).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, cast

from src.kamus.gerbang import PutusanGerbang
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import BarisJejak, MetadataDokumen, PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenDiKorpus, GalatDokumenTidakAda
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.postgres import BAGIAN_SEGMEN_KELUAR
from src.penyimpanan.sambungan import SambunganAktif

PERAN_INGESTI: Final = "peran_ingesti"
"""Peran `terima`: menaruh teks karantina tanpa dapat membacanya (P-2 A)."""

PERAN_VERIFIKASI: Final = "peran_verifikasi"
"""Peran tinjauan dan putusan: membaca karantina, hanya dapat mengeluarkan."""

PERAN_PENARIKAN_DOKUMEN: Final = "peran_penarikan_dokumen"
"""Peran pencabutan: mengeluarkan dari korpus beserta segmennya (TK-84 A)."""


@dataclass(frozen=True)
class CatatanPenerimaan:
    """Satu unggahan — D-14 Bagian 5.1 `penerimaan`.

    `samaran` berisi jumlah per jenis pendeteksi FR-B04, **tidak pernah**
    nilainya (P-5 A, KM-03). `id_penerima` kode anggota tim (P-6 A).
    """

    id_dokumen: str
    judul: str
    jenis: str
    penerbit: str
    tahun: int
    tingkat_kerahasiaan: str
    status_persetujuan_pemilik: str
    samaran: dict[str, int]
    id_penerima: str


@dataclass(frozen=True)
class TemuanPola:
    """Temuan pemeriksa pola adversarial atas teks tersamar — indeks karakter."""

    pola: str
    mulai: int
    akhir: int
    kutipan: str


@dataclass(frozen=True)
class KeadaanKarantina:
    """Keadaan gerbang yang diturunkan bagi penerimaan terbaru."""

    penerimaan: CatatanPenerimaan
    area: Area
    temuan: tuple[TemuanPola, ...]
    ditinjau: bool
    catatan_tinjauan: str
    status_anonimisasi: str
    persetujuan_dicabut: bool
    alasan_terakhir: str


def _tolak_bila(syarat: bool, kredensial: Kredensial, area: Area, operasi: str) -> None:
    if syarat:
        raise GalatAksesDitolak(kredensial=kredensial, area=area, operasi=operasi)


def _pastikan_baca_karantina(kredensial: Kredensial) -> None:
    _tolak_bila(not kredensial.boleh_baca(Area.KARANTINA), kredensial, Area.KARANTINA, "baca")


def _pastikan_tulis_karantina(kredensial: Kredensial) -> None:
    _tolak_bila(not kredensial.boleh_tulis(Area.KARANTINA), kredensial, Area.KARANTINA, "tulis")


def _pastikan_boleh_cabut(kredensial: Kredensial) -> None:
    """Pencabutan membaca korpus dan menulis karantina — kredensial penarikan.
    Verifikator sengaja tidak menulis karantina, sehingga tidak dapat mencabut."""
    _tolak_bila(not kredensial.boleh_baca(Area.KORPUS), kredensial, Area.KORPUS, "baca")
    _pastikan_tulis_karantina(kredensial)


class CatatanGerbang(ABC):
    """Kontrak catatan gerbang. Setiap penulisan majemuk satu pernyataan."""

    @abstractmethod
    async def terima(
        self,
        kredensial: Kredensial,
        penerimaan: CatatanPenerimaan,
        teks: str,
        temuan: Sequence[TemuanPola],
    ) -> None:
        """Teks, penerimaan, dan temuan sekaligus.

        `GalatDokumenDiKorpus` bila dokumennya sedang di korpus (TK-85 A):
        tidak satu catatan pun tersimpan.
        """

    @abstractmethod
    async def keadaan(self, id_dokumen: str) -> KeadaanKarantina | None:
        """Keadaan yang diturunkan; `None` bagi dokumen yang tidak pernah
        diterima.

        **Tanpa kredensial, dan itu disengaja**: dipakai gerbang untuk
        mengetahui area sebelum pemeriksaan kredensialnya sendiri
        (`_pastikan_terbaca`), sama dengan kamus area fitur 002. Gerbang tidak
        pernah meneruskan hasilnya kepada pemanggil yang tidak lolos
        pemeriksaan itu. Pada PostgreSQL peran sambungannya yang menjaga.
        """

    @abstractmethod
    async def daftar(self) -> tuple[KeadaanKarantina, ...]:
        """Keadaan setiap dokumen yang kini di karantina, berurutan id — bagi
        perintah `daftar` perkakas (fitur 037, T-6). Tanpa kredensial, sama
        dengan `keadaan`; gerbang memeriksanya sebelum memanggil."""

    @abstractmethod
    async def tinjau(
        self, kredensial: Kredensial, id_dokumen: str, id_peninjau: str, catatan: str
    ) -> None:
        """Tinjauan atas temuan penerimaan terbaru."""

    @abstractmethod
    async def tolak(
        self, kredensial: Kredensial, id_dokumen: str, id_pelaku: str, alasan: str
    ) -> None:
        """Putusan menahan — jejak berarah karantina ke karantina."""

    @abstractmethod
    async def setujui(
        self,
        kredensial: Kredensial,
        id_dokumen: str,
        id_pelaku: str,
        alasan: str,
        metadata: MetadataDokumen,
    ) -> None:
        """Pindah ke korpus beserta metadata dan jejaknya, sekaligus."""

    @abstractmethod
    async def cabut(
        self, kredensial: Kredensial, id_dokumen: str, id_pelaku: str, alasan: str
    ) -> Area:
        """Pencabutan persetujuan pemilik — keluar dari korpus bila di sana,
        beserta segmennya. Mengembalikan area asalnya. `GalatDokumenTidakAda`
        bagi dokumen yang tidak pernah diterima."""


# ── Memori ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _Jejak:
    id_dokumen: str
    nomor_penerimaan: int
    putusan: PutusanGerbang
    alasan: str


class CatatanGerbangMemori(CatatanGerbang):
    """Pelaksana memori. Teks dokumen tinggal pada penyimpan dokumennya."""

    def __init__(self, penyimpan: PenyimpanDasar) -> None:
        self.penyimpan = penyimpan
        self._penerimaan: list[tuple[CatatanPenerimaan, tuple[TemuanPola, ...]]] = []
        self._tinjauan: list[tuple[int, str]] = []
        self._jejak: list[_Jejak] = []
        self._area: dict[str, Area] = {}

    def _nomor_terbaru(self, id_dokumen: str) -> int | None:
        nomor = [i + 1 for i, (p, _) in enumerate(self._penerimaan) if p.id_dokumen == id_dokumen]
        return nomor[-1] if nomor else None

    async def terima(
        self,
        kredensial: Kredensial,
        penerimaan: CatatanPenerimaan,
        teks: str,
        temuan: Sequence[TemuanPola],
    ) -> None:
        _pastikan_tulis_karantina(kredensial)
        if self._area.get(penerimaan.id_dokumen) is Area.KORPUS:
            raise GalatDokumenDiKorpus(penerimaan.id_dokumen)
        await self.penyimpan.tulis_dokumen(kredensial, Area.KARANTINA, penerimaan.id_dokumen, teks)
        self._penerimaan.append((penerimaan, tuple(temuan)))
        self._area[penerimaan.id_dokumen] = Area.KARANTINA

    async def keadaan(self, id_dokumen: str) -> KeadaanKarantina | None:
        nomor = self._nomor_terbaru(id_dokumen)
        if nomor is None:
            return None
        penerimaan, temuan = self._penerimaan[nomor - 1]
        tinjauan = [c for n, c in self._tinjauan if n == nomor]
        putusan = [
            j.putusan
            for j in self._jejak
            if j.nomor_penerimaan == nomor
            and j.putusan in (PutusanGerbang.SETUJUI, PutusanGerbang.TOLAK)
        ]
        semua_jejak = [j for j in self._jejak if j.id_dokumen == id_dokumen]
        return KeadaanKarantina(
            penerimaan=penerimaan,
            area=self._area[id_dokumen],
            temuan=temuan,
            ditinjau=bool(tinjauan),
            catatan_tinjauan=tinjauan[-1] if tinjauan else "",
            status_anonimisasi=_STATUS_MENURUT_PUTUSAN[putusan[-1]] if putusan else "menunggu",
            persetujuan_dicabut=any(
                j.nomor_penerimaan == nomor and j.putusan is PutusanGerbang.CABUT_PERSETUJUAN
                for j in self._jejak
            ),
            alasan_terakhir=semua_jejak[-1].alasan if semua_jejak else "",
        )

    async def daftar(self) -> tuple[KeadaanKarantina, ...]:
        hasil = []
        for id_dokumen in sorted(i for i, a in self._area.items() if a is Area.KARANTINA):
            keadaan = await self.keadaan(id_dokumen)
            if keadaan is not None:
                hasil.append(keadaan)
        return tuple(hasil)

    def _nomor_wajib(self, id_dokumen: str) -> int:
        nomor = self._nomor_terbaru(id_dokumen)
        if nomor is None:
            raise GalatDokumenTidakAda(id_dokumen)
        return nomor

    async def tinjau(
        self, kredensial: Kredensial, id_dokumen: str, id_peninjau: str, catatan: str
    ) -> None:
        _pastikan_baca_karantina(kredensial)
        self._tinjauan.append((self._nomor_wajib(id_dokumen), catatan))

    async def tolak(
        self, kredensial: Kredensial, id_dokumen: str, id_pelaku: str, alasan: str
    ) -> None:
        _pastikan_baca_karantina(kredensial)
        nomor = self._nomor_wajib(id_dokumen)
        self._jejak.append(_Jejak(id_dokumen, nomor, PutusanGerbang.TOLAK, alasan))

    async def setujui(
        self,
        kredensial: Kredensial,
        id_dokumen: str,
        id_pelaku: str,
        alasan: str,
        metadata: MetadataDokumen,
    ) -> None:
        jejak = BarisJejak(id_pelaku=id_pelaku, alasan=alasan, putusan=PutusanGerbang.SETUJUI)
        await self.penyimpan.pindahkan(
            kredensial,
            id_dokumen,
            Area.KARANTINA,
            Area.KORPUS,
            alasan,
            metadata=metadata,
            jejak=jejak,
        )
        nomor = self._nomor_wajib(id_dokumen)
        self._jejak.append(_Jejak(id_dokumen, nomor, PutusanGerbang.SETUJUI, alasan))
        self._area[id_dokumen] = Area.KORPUS

    async def cabut(
        self, kredensial: Kredensial, id_dokumen: str, id_pelaku: str, alasan: str
    ) -> Area:
        _pastikan_boleh_cabut(kredensial)
        nomor = self._nomor_wajib(id_dokumen)
        dari = self._area[id_dokumen]
        if dari is Area.KORPUS:
            jejak = BarisJejak(
                id_pelaku=id_pelaku, alasan=alasan, putusan=PutusanGerbang.CABUT_PERSETUJUAN
            )
            await self.penyimpan.pindahkan(
                kredensial, id_dokumen, Area.KORPUS, Area.KARANTINA, alasan, jejak=jejak
            )
        self._jejak.append(_Jejak(id_dokumen, nomor, PutusanGerbang.CABUT_PERSETUJUAN, alasan))
        self._area[id_dokumen] = Area.KARANTINA
        return dari


_STATUS_MENURUT_PUTUSAN: Final[dict[PutusanGerbang | str, str]] = {
    PutusanGerbang.SETUJUI: "terverifikasi",
    PutusanGerbang.TOLAK: "ditolak",
    PutusanGerbang.SETUJUI.value: "terverifikasi",
    PutusanGerbang.TOLAK.value: "ditolak",
}
"""Status anonimisasi menurut putusan verifikator — D-14 Bagian 5.1."""


# ── PostgreSQL ────────────────────────────────────────────────────────

_TERIMA: Final = """
WITH ganti AS (
  UPDATE karantina.dokumen_sumber SET isi = $2, disimpan_pada = now()
  WHERE id = $1 RETURNING id
), baru AS (
  INSERT INTO karantina.dokumen_sumber (id, isi)
  SELECT $1, $2
  WHERE NOT EXISTS (SELECT 1 FROM ganti)
    AND NOT EXISTS (SELECT 1 FROM korpus.dokumen_sumber WHERE id = $1)
  RETURNING id
), tulis AS (
  SELECT id FROM ganti UNION ALL SELECT id FROM baru
), terima AS (
  INSERT INTO karantina.penerimaan (id_dokumen, judul, jenis, penerbit, tahun,
    tingkat_kerahasiaan, status_persetujuan_pemilik, samaran, id_penerima)
  SELECT id, $3, $4, $5, $6, $7, $8, $9, $10 FROM tulis
  RETURNING nomor
), temuan AS (
  INSERT INTO karantina.temuan_pola (nomor_penerimaan, pola, mulai, akhir, kutipan)
  SELECT terima.nomor, t.pola, t.mulai, t.akhir, t.kutipan
  FROM terima, unnest($11::text[], $12::int[], $13::int[], $14::text[])
    AS t(pola, mulai, akhir, kutipan)
)
SELECT nomor FROM terima
"""
"""Ganti lalu sisip, bukan `ON CONFLICT`: `excluded.isi` menuntut hak baca
`isi`, dan ingesti sengaja tidak memegangnya (KB-258). Sisip baru tidak terjadi
bila dokumennya di korpus (TK-85 A), di dalam pernyataan yang sama."""

_KEADAAN: Final = """
WITH p AS (
  SELECT * FROM karantina.penerimaan WHERE id_dokumen = $1 ORDER BY nomor DESC LIMIT 1
)
SELECT p.id_dokumen, p.judul, p.jenis, p.penerbit, p.tahun, p.tingkat_kerahasiaan,
  p.status_persetujuan_pemilik, p.samaran::text AS samaran, p.id_penerima,
  EXISTS (SELECT 1 FROM korpus.dokumen_sumber WHERE id = $1) AS di_korpus,
  (SELECT coalesce(json_agg(json_build_object('pola', t.pola, 'mulai', t.mulai,
     'akhir', t.akhir, 'kutipan', t.kutipan) ORDER BY t.nomor), '[]'::json)::text
   FROM karantina.temuan_pola t WHERE t.nomor_penerimaan = p.nomor) AS temuan,
  EXISTS (SELECT 1 FROM karantina.tinjauan_temuan WHERE nomor_penerimaan = p.nomor)
    AS ditinjau,
  (SELECT catatan FROM karantina.tinjauan_temuan WHERE nomor_penerimaan = p.nomor
   ORDER BY nomor DESC LIMIT 1) AS catatan_tinjauan,
  (SELECT putusan FROM karantina.jejak_area WHERE nomor_penerimaan = p.nomor
   AND putusan IN ('setujui', 'tolak') ORDER BY id DESC LIMIT 1) AS putusan_verifikasi,
  EXISTS (SELECT 1 FROM karantina.jejak_area WHERE nomor_penerimaan = p.nomor
   AND putusan = 'cabut_persetujuan') AS dicabut,
  (SELECT alasan FROM karantina.jejak_area WHERE id_dokumen = $1
   ORDER BY id DESC LIMIT 1) AS alasan_terakhir
FROM p
"""

_DAFTAR: Final = """
SELECT d.id FROM karantina.dokumen_sumber d
WHERE EXISTS (SELECT 1 FROM karantina.penerimaan p WHERE p.id_dokumen = d.id)
ORDER BY d.id
"""
"""Dokumen karantina yang pernah diterima gerbang. Teks yang ditaruh di luar
gerbang — tanpa penerimaan — tidak memiliki keadaan, dan tidak tampil."""

_NOMOR_TERBARU: Final = "(SELECT max(nomor) FROM karantina.penerimaan WHERE id_dokumen = $1)"

_TINJAU: Final = f"""
INSERT INTO karantina.tinjauan_temuan (nomor_penerimaan, id_peninjau, catatan)
SELECT n, $2, $3 FROM (SELECT {_NOMOR_TERBARU} AS n) s WHERE n IS NOT NULL
RETURNING nomor_penerimaan
"""

_TOLAK: Final = f"""
INSERT INTO karantina.jejak_area (id_dokumen, nomor_penerimaan, putusan, id_pelaku,
  dari_area, ke_area, alasan)
SELECT $1, n, 'tolak', $2, 'karantina', 'karantina', $3
FROM (SELECT {_NOMOR_TERBARU} AS n) s WHERE n IS NOT NULL
RETURNING nomor_penerimaan
"""

_CABUT: Final = (
    f"WITH p AS (SELECT {_NOMOR_TERBARU} AS nomor), "
    "terangkat AS (DELETE FROM korpus.dokumen_sumber WHERE id = $1 "
    "  AND EXISTS (SELECT 1 FROM p WHERE nomor IS NOT NULL) RETURNING id, isi), "
    "pindah AS (INSERT INTO karantina.dokumen_sumber (id, isi) "
    "  SELECT id, isi FROM terangkat RETURNING id), "
    + ", ".join(BAGIAN_SEGMEN_KELUAR)
    + ", jejak AS (INSERT INTO karantina.jejak_area (id_dokumen, nomor_penerimaan, putusan, "
    "  id_pelaku, dari_area, ke_area, alasan) "
    "  SELECT $1, p.nomor, 'cabut_persetujuan', $2, "
    "  CASE WHEN EXISTS (SELECT 1 FROM pindah) THEN 'korpus' ELSE 'karantina' END, "
    "  'karantina', $3 FROM p WHERE p.nomor IS NOT NULL) "
    "SELECT p.nomor, EXISTS (SELECT 1 FROM pindah) AS dari_korpus FROM p"
)
"""Satu pernyataan bagi kedua keadaan — dokumen di korpus maupun di karantina —
sehingga tidak ada celah antara membaca area dan mencatat pencabutan. Dokumen
yang tidak pernah diterima tidak menyentuh apa pun. Segmen keluar lewat
bagian yang sama dengan `pindahkan()` (TK-84 A)."""


class CatatanGerbangPostgres(CatatanGerbang):
    """Pelaksana PostgreSQL. Sambungan dibuka sebagai peran perintahnya.

    Penyimpan dokumennya **disuntikkan**, tidak disusun di sini (R-06 fitur
    024): pemanggil memberinya `PenyimpanPostgres` di atas sambungan yang sama,
    dan persetujuan memakai `pindahkan()` miliknya — satu pernyataan
    pemindahan, bukan salinan kedua.
    """

    def __init__(self, sambungan: SambunganAktif, dokumen: PenyimpanDasar) -> None:
        self._sambungan = sambungan
        self._dokumen = dokumen

    async def terima(
        self,
        kredensial: Kredensial,
        penerimaan: CatatanPenerimaan,
        teks: str,
        temuan: Sequence[TemuanPola],
    ) -> None:
        _pastikan_tulis_karantina(kredensial)
        p = penerimaan
        baris = await self._sambungan.fetchrow(
            _TERIMA,
            p.id_dokumen,
            json.dumps(teks),
            p.judul,
            p.jenis,
            p.penerbit,
            p.tahun,
            p.tingkat_kerahasiaan,
            p.status_persetujuan_pemilik,
            json.dumps(p.samaran),
            p.id_penerima,
            [t.pola for t in temuan],
            [t.mulai for t in temuan],
            [t.akhir for t in temuan],
            [t.kutipan for t in temuan],
        )
        if baris is None:
            raise GalatDokumenDiKorpus(p.id_dokumen)

    async def keadaan(self, id_dokumen: str) -> KeadaanKarantina | None:
        b = await self._sambungan.fetchrow(_KEADAAN, id_dokumen)
        if b is None:
            return None
        putusan = b["putusan_verifikasi"]
        return KeadaanKarantina(
            penerimaan=CatatanPenerimaan(
                id_dokumen=str(b["id_dokumen"]),
                judul=str(b["judul"]),
                jenis=str(b["jenis"]),
                penerbit=str(b["penerbit"]),
                tahun=cast(int, b["tahun"]),
                tingkat_kerahasiaan=str(b["tingkat_kerahasiaan"]),
                status_persetujuan_pemilik=str(b["status_persetujuan_pemilik"]),
                samaran=cast(dict[str, int], json.loads(str(b["samaran"]))),
                id_penerima=str(b["id_penerima"]),
            ),
            area=Area.KORPUS if b["di_korpus"] else Area.KARANTINA,
            temuan=tuple(
                TemuanPola(**cast(Mapping[str, object], t))  # type: ignore[arg-type]
                for t in json.loads(str(b["temuan"]))
            ),
            ditinjau=bool(b["ditinjau"]),
            catatan_tinjauan=str(b["catatan_tinjauan"] or ""),
            status_anonimisasi=_STATUS_MENURUT_PUTUSAN[str(putusan)] if putusan else "menunggu",
            persetujuan_dicabut=bool(b["dicabut"]),
            alasan_terakhir=str(b["alasan_terakhir"] or ""),
        )

    async def daftar(self) -> tuple[KeadaanKarantina, ...]:
        hasil = []
        for baris in await self._sambungan.fetch(_DAFTAR):
            keadaan = await self.keadaan(str(baris["id"]))
            if keadaan is not None:
                hasil.append(keadaan)
        return tuple(hasil)

    async def tinjau(
        self, kredensial: Kredensial, id_dokumen: str, id_peninjau: str, catatan: str
    ) -> None:
        _pastikan_baca_karantina(kredensial)
        if await self._sambungan.fetchrow(_TINJAU, id_dokumen, id_peninjau, catatan) is None:
            raise GalatDokumenTidakAda(id_dokumen)

    async def tolak(
        self, kredensial: Kredensial, id_dokumen: str, id_pelaku: str, alasan: str
    ) -> None:
        _pastikan_baca_karantina(kredensial)
        if await self._sambungan.fetchrow(_TOLAK, id_dokumen, id_pelaku, alasan) is None:
            raise GalatDokumenTidakAda(id_dokumen)

    async def setujui(
        self,
        kredensial: Kredensial,
        id_dokumen: str,
        id_pelaku: str,
        alasan: str,
        metadata: MetadataDokumen,
    ) -> None:
        await self._dokumen.pindahkan(
            kredensial,
            id_dokumen,
            Area.KARANTINA,
            Area.KORPUS,
            alasan,
            metadata=metadata,
            jejak=BarisJejak(id_pelaku=id_pelaku, alasan=alasan, putusan=PutusanGerbang.SETUJUI),
        )

    async def cabut(
        self, kredensial: Kredensial, id_dokumen: str, id_pelaku: str, alasan: str
    ) -> Area:
        _pastikan_boleh_cabut(kredensial)
        baris = await self._sambungan.fetchrow(_CABUT, id_dokumen, id_pelaku, alasan)
        if baris is None or baris["nomor"] is None:
            raise GalatDokumenTidakAda(id_dokumen)
        return Area.KORPUS if baris["dari_korpus"] else Area.KARANTINA
