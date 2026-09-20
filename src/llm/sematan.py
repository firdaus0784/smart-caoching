"""Antarmuka penyemat dan tiruannya — R-02, R-06, R-08; C-08, C-09, ADR-12.

Sisi semantik ADR-03 menuntut vektor, dan vektor menuntut model. Modul ini
menyediakan **antarmukanya**, bukan modelnya.

## Mengapa berkas ini di `src/llm/`, dan bukan di `src/rag/`

Bukan pilihan rancangan. `periksa_impor_penyedia` menyenaraikan `torch`,
`transformers`, dan `sentence_transformers` sebagai pustaka model yang **hanya
boleh diimpor di dalam `src/llm/`** — C-08, tanpa pengecualian. Adaptor
sungguhan yang kelak memakainya tidak punya rumah lain, dan antarmukanya
tinggal bersamanya agar keduanya tidak terpisah oleh batas lapisan.

`src/rag/` boleh mengimpornya: `llm` lapisan terbuka menurut `AGENTS.md`,
sejajar `kamus`, `penyimpanan`, dan `logbook`.

## Tiruan yang menyatakan dirinya tiruan

`PenyematTiruan` **bukan** penyemat sungguhan yang disederhanakan. Ia
memetakan teks ke vektor tetap lewat fungsi hash, dan `versi` yang
dikeluarkannya berbunyi demikian.

Pembedaan itu yang paling perlu dijaga pada seluruh berkas ini. Penyemat
buatan sendiri yang "mirip semantik" menghasilkan angka kemiripan yang tidak
berarti apa-apa sambil terbaca seperti berfungsi — dan angka semacam itu akan
masuk catatan percobaan, lalu masuk naskah.

Adaptor sungguhan (`intfloat/multilingual-e5-large-instruct`) **tidak ada di
sini**: bobotnya tidak terjangkau dari lingkungan agen, dan pemasangannya
pekerjaan mesin penelitian. Ia fitur 025.

## Asinkron sejak awal

`sematkan` asinkron meski tiruannya tidak menunggu apa pun. Kontrak yang
bentuknya bergantung pada pelaksana mana yang kebetulan ada hari ini adalah
kontrak yang berubah tiap pelaksana baru — dan adaptor sungguhan memanggil
model, baik lewat jaringan maupun lewat GPU. Alasan yang sama dipakai pada
`SumberKandidat.cari` (T-1).
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

DIMENSI_TIRUAN: Final = 16
"""Dimensi bawaan tiruan.

Sengaja **jauh lebih kecil** daripada 1024 milik model sungguhan. Tiruan yang
berdimensi sama dengan model sungguhan mengundang kolom vektor disusun menurut
tiruannya, dan ketidakcocokannya baru terlihat pada hari model sungguhan
dipasang.
"""


class VersiPenyemat(BaseModel):
    """Nama dan versi model penyemat — C-09.

    Dibawa setiap keluaran yang membentuk indeks. Indeks yang tidak menyatakan
    penyemat mana yang membangunnya tidak dapat dibandingkan dengan indeks
    berikutnya, dan perbandingan antarpercobaan menjadi perbandingan yang tidak
    diketahui apa yang berubah.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    nama_model: str = Field(min_length=1)
    versi_model: str = Field(min_length=1)


class Penyemat(ABC):
    """Kontrak penyematan teks menjadi vektor — ADR-12.

    Sengaja kecil: satu sifat versi, satu sifat dimensi, satu metode. Yang
    tidak disebut di sini tidak dapat dipakai pemanggil, dan itu yang membuat
    penggantian pelaksananya tetap murah (RP-04).
    """

    @property
    @abstractmethod
    def versi(self) -> VersiPenyemat:
        """Nama dan versi model — C-09."""

    @property
    @abstractmethod
    def dimensi(self) -> int:
        """Panjang setiap vektor. Dicocokkan dengan kolom saat penyusunan."""

    @abstractmethod
    async def sematkan(self, teks: Sequence[str]) -> Sequence[Sequence[float]]:
        """Satu vektor per teks, **pada urutan yang sama**.

        Urutan yang tidak dijaga menghasilkan vektor yang tertaut ke segmen
        yang keliru — dan kekeliruan itu tidak menghasilkan satu galat pun,
        hanya pencarian yang menemukan hal yang salah.
        """


class PenyematTiruan(Penyemat):
    """Penyemat tiruan deterministik — ADR-12.

    **Menyatakan dirinya tiruan pada `versi`.** Lihat uraian modul.
    """

    def __init__(self, *, dimensi: int = DIMENSI_TIRUAN) -> None:
        if dimensi <= 0:
            raise ValueError(
                f"dimensi wajib lebih besar dari nol; diberi {dimensi}. "
                "Ditolak saat penyusunan, bukan saat kueri pertama"
            )
        self._dimensi = dimensi

    @property
    def versi(self) -> VersiPenyemat:
        return VersiPenyemat(nama_model="penyemat-tiruan", versi_model="hash-sha256-1")

    @property
    def dimensi(self) -> int:
        return self._dimensi

    async def sematkan(self, teks: Sequence[str]) -> Sequence[Sequence[float]]:
        for satu in teks:
            if not satu.strip():
                raise ValueError(
                    "teks kosong tidak dapat disematkan — vektornya tetap dekat "
                    "dengan segala sesuatu, dan kedekatan itu dihitung sebagai bukti"
                )
        return tuple(self._vektor(satu) for satu in teks)

    def _vektor(self, satu: str) -> tuple[float, ...]:
        """Peta tetap dari teks ke vektor satuan.

        Dinormalkan agar jarak kosinus berada pada rentang yang lazim; ia
        **tidak** membuat angkanya bermakna secara semantik.
        """
        sidik = hashlib.sha256(satu.strip().encode("utf-8")).digest()
        mentah = [(sidik[i % len(sidik)] * (i + 1)) % 251 / 251.0 for i in range(self._dimensi)]
        panjang = math.sqrt(sum(n * n for n in mentah)) or 1.0
        return tuple(n / panjang for n in mentah)
