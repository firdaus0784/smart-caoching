"""Pemeringkat ulang tahap 5 dan jalur mundurnya — R-05, BT-30, C-09.

`docs/D07.md` Bagian 4 baris [5]: *"Penggabungan dan pemeringkatan ulang →
5-8 segmen teratas"*. BT-30 sudah memutuskan apa yang terjadi bila modelnya
tidak ada: *"bila tidak ada, tahap 5 memakai hasil penggabungan langsung"*.

Yang modul ini tambahkan bukan keputusan itu, melainkan **satu syarat atasnya**:
ketiadaan pemeringkat ulang wajib tercatat pada keluaran.

## Mengapa jalur mundur yang diam berbahaya

Jalur mundur yang diam menghasilkan **urutan yang sama** dengan pemeringkat
ulang yang berjalan dan kebetulan tidak mengubah apa pun. Dua keadaan itu
tidak dapat dibedakan dari keluarannya, dan keduanya menuntut tindakan yang
berbeda:

- Pemeringkat ulang berjalan tanpa mengubah urutan → penggabungan sudah baik;
  tidak ada yang perlu dikerjakan.
- Pemeringkat ulang tidak ada → tahap 5 belum pernah dijalankan sama sekali,
  dan seluruh angka percobaan yang tercatat pada D-10 L1 mengukur pipa yang
  kurang satu tahap.

Bentuk yang sama dengan `BELUM-DAPAT-DIPERIKSA` pada `make compliance` dan
dengan `segmen_tanpa_vektor=None` pada `HasilSumber`: keadaan "tidak
diketahui" diberi bentuknya sendiri, bukan disamarkan menjadi nol atau lulus.

## Bentuk, bukan pemeriksaan

`HasilPeringkatUlang.pemeringkatan` **tidak memiliki nilai baku**. Tidak ada
cara menyusun hasil tanpa menyatakan tahap 5 dijalankan oleh siapa; pemanggil
yang tidak punya pemeringkat wajib menuliskan `JalurMundurBT30` beserta
sebabnya. Pemeriksaan saat jalan dapat dilupakan seseorang — bidang wajib
tidak dapat.

Karena itu pula `peringkat_ulang()` menuntut `pemeringkat`, bukan menerima
`None` yang berarti "lewati saja". `None` yang berarti sesuatu adalah jalur
mundur yang diam dalam bentuk lain.

## Pemeringkat tidak boleh menambah atau menghilangkan segmen

Tahap 5 **mengurutkan ulang**. Segmen yang hilang di sini adalah bukti yang
lenyap tanpa satu pun catatan, dan segmen yang muncul di sini adalah segmen
yang tidak pernah ditemukan sumber mana pun — keduanya membatalkan sitasi yang
C-01 tuntut. Penjagaannya ada pada fungsi, bukan pada tiap pelaksana, supaya
pelaksana berikutnya mewarisinya tanpa menyalinnya.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from src.rag.pengambilan.gabung import HasilGabungan

SEBAB_BT30 = "model pemeringkat ulang lintas-enkoder untuk Bahasa Indonesia belum tersedia"
"""Sebab baku jalur mundur, dari BT-30 `docs/D07.md` Bagian 8.

Ia tetap wajib **dituliskan** pemanggil. Tetapan ini hanya membuat sebab yang
sama tidak ditulis ulang dengan kata berbeda di lima tempat, lalu berbeda di
salah satunya.
"""


class PemeringkatDipakai(BaseModel):
    """Tahap 5 dijalankan sebuah model — C-09 menuntut nama dan versinya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    nama_model: str = Field(min_length=1)
    versi_model: str = Field(min_length=1)


class JalurMundurBT30(BaseModel):
    """Tahap 5 **tidak** dijalankan; urutan penggabungan dipakai apa adanya.

    `sebab` wajib dan tidak boleh kosong. Jalur mundur tanpa sebab sama tidak
    dapat ditindaklanjutinya dengan jalur mundur yang diam — pembacanya tahu
    tahap 5 tidak berjalan, tetapi tidak tahu apakah itu keputusan BT-30 atau
    pemasangan yang gagal pagi itu.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    sebab: str = Field(min_length=1)


Pemeringkatan = PemeringkatDipakai | JalurMundurBT30
"""Siapa yang menjalankan tahap 5 — salah satu, tidak pernah tidak keduanya."""


class HasilPeringkatUlang(BaseModel):
    """Segmen sesudah tahap 5, beserta keterangan siapa yang menjalankannya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    segmen: tuple[HasilGabungan, ...]
    pemeringkatan: Pemeringkatan
    """Tanpa nilai baku, dengan sengaja — lihat docstring modul."""


class Pemeringkat(ABC):
    """Kontrak tahap 5.

    Asinkron karena pelaksana sungguhan memanggil model lewat `src/llm/`
    (C-08), dan pembungkus itu asinkron sejak fitur 019 T-3.
    """

    @property
    @abstractmethod
    def keterangan(self) -> Pemeringkatan:
        """Yang akan tercatat pada keluaran bila pelaksana ini dipakai."""

    @abstractmethod
    async def urutkan(
        self, kueri: str, segmen: Sequence[HasilGabungan]
    ) -> tuple[HasilGabungan, ...]:
        """Urutkan ulang `segmen`. Himpunan segmennya tidak boleh berubah."""


class PemeringkatTidakTersedia(Pemeringkat):
    """Jalur mundur BT-30 sebagai pelaksana, bukan sebagai `None`.

    Ia **pelaksana penuh**: dapat diberikan ke mana pun `Pemeringkat` diminta,
    dan keterangannya ikut pada keluaran. Itu yang membedakannya dari melewati
    tahap 5 — yang tidak meninggalkan jejak apa pun.
    """

    def __init__(self, *, sebab: str = SEBAB_BT30) -> None:
        self._keterangan = JalurMundurBT30(sebab=sebab)

    @property
    def keterangan(self) -> Pemeringkatan:
        return self._keterangan

    async def urutkan(
        self, kueri: str, segmen: Sequence[HasilGabungan]
    ) -> tuple[HasilGabungan, ...]:
        """Urutan penggabungan apa adanya — BT-30."""
        return tuple(segmen)


async def peringkat_ulang(
    kueri: str,
    segmen: Sequence[HasilGabungan],
    *,
    pemeringkat: Pemeringkat,
) -> HasilPeringkatUlang:
    """Jalankan tahap 5 dan catat siapa yang menjalankannya.

    `pemeringkat` wajib. Pemanggil yang tidak memilikinya menuliskan
    `PemeringkatTidakTersedia()`; ia tidak dapat sekadar menghilangkannya.
    """
    diurutkan = await pemeringkat.urutkan(kueri, segmen)

    sebelum = sorted(s.id_segmen for s in segmen)
    sesudah = sorted(s.id_segmen for s in diurutkan)
    if sebelum != sesudah:
        raise ValueError(
            "pemeringkat ulang mengubah himpunan segmen, bukan hanya urutannya; "
            f"masuk {sebelum}, keluar {sesudah} — tahap 5 mengurutkan, tidak "
            "menyaring maupun menambah"
        )

    return HasilPeringkatUlang(segmen=tuple(diurutkan), pemeringkatan=pemeringkat.keterangan)
