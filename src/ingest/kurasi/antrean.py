"""Pemantauan antrean kurasi dan pengereman ingesti — R-11, R-12, FR-I08, PP-06.

D-06 Bagian 8.3 menetapkan ambangnya sebagai **kelipatan** pagu kurasi harian,
dan tindakannya setelah **tiga hari berturut-turut** melampaui.

## Tiga hari, bukan satu

Pengereman pada hari pertama menurunkan frekuensi K-C setiap kali antrean naik
sehari. Sesudah beberapa ayunan semacam itu, kanal jurnal berjalan pada
frekuensi terendah sementara antrean sebenarnya tidak pernah menumpuk — lalu
feed kekurangan isi dan titik kritis T5 pada D-02 menyala.

"Berturut-turut" juga bukan "tiga kali": rentetan dihitung dari hari terakhir
mundur, dan satu hari yang aman memutusnya. Antrean yang berayun belum
menumpuk.

## Pengereman punya dua paruh, dan paruh keduanya tertahan

D-06 Bagian 8.3 menuliskan tindakannya utuh:

> Ingesti diperlambat: frekuensi K-C diturunkan lebih dulu, **ambang relevansi
> L4 dinaikkan**.

Paruh pertama dapat dijalankan. Paruh kedua tidak: ambang relevansi L4 belum
ada, D-06 Bagian 6 menyerahkannya ke BT-24, dan menaikkan ambang yang belum
dikalibrasi adalah menyetel ambang yang C-16 larang.

Yang dilaporkan karena itu **bukan** "pengereman berjalan" melainkan pengereman
yang separuhnya tertahan, beserta apa yang ditunggunya. Laporan yang menyebut
pengereman lengkap sementara separuhnya tidak berjalan akan membuat penanggung
jawab teknis mengira antrean sudah ditangani — dan ia baru mengetahui
sebaliknya ketika kurator berhenti menyanggupi ritmenya.

## Hanya K-C yang diperlambat

D-06 menyebut K-C dan berhenti di situ, beserta alasannya: *"kanal jurnal
menghasilkan volume terbesar dengan tingkat kelolosan terendah, sehingga
pengurangannya paling sedikit merugikan."*

Urutan bagi kanal selebihnya tidak tertulis pada dokumen mana pun, dan
menyusunnya di sini akan menetapkan kebijakan yang bukan milik kode. K-A
khususnya tidak boleh ikut: kanal regulasi menghasilkan butir yang paling
menentukan dan paling jarang.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from src.ingest.kanal import Kanal
from src.ingest.kurasi.tetapan import (
    HARI_BERTURUT_SEBELUM_PENGEREMAN,
    PAGU_KURASI_HARIAN,
    PENGALI_AMBANG_ANTREAN,
)

_PARUH_KEDUA_TERTAHAN = (
    "kenaikan ambang relevansi L4 tertahan — ambangnya belum dikalibrasi, "
    "D-06 Bagian 6 menyerahkannya ke BT-24 (C-16)"
)
"""Apa yang tidak berjalan pada pengereman, beserta apa yang ditunggunya.

Alasan yang tidak menyebut apa yang ditunggu adalah alasan yang tidak dapat
ditagih — bentuk yang sama dengan `_MENUNGGU_L4` pada `saring.py` dan
`_MENUNGGU_FITUR_020` pada fitur 008.
"""

_KANAL_DIPERLAMBAT = (Kanal.K_C,)
"""Kanal yang diperlambat saat pengereman — D-06 Bagian 8.3, K-C saja."""


class GalatAntrean(Exception):
    """Riwayat antrean tidak dapat dibaca.

    Berupa galat, bukan laporan "tidak perlu mengerem": laporan bersih yang
    tidak memeriksa apa pun adalah laporan yang keliru, dan ia terbaca persis
    seperti laporan yang benar.
    """


class HasilPantauan(BaseModel):
    """Keadaan antrean pada hari terakhir riwayat — R-11."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    panjang_antrean: int = Field(ge=0)
    """Panjang pada hari terakhir."""
    pagu_harian: int = Field(gt=0)
    """Dibawa serta agar laporan dapat ditinjau ulang ketika pagunya berubah."""
    hari_berturut_melampaui: int = Field(ge=0)
    """Dihitung dari hari terakhir mundur; satu hari aman memutusnya.

    Sengaja **tanpa** sifat pendamping `melampaui_hari_ini`: nilainya sama
    dengan `hari_berturut_melampaui >= 1`, dan dua cara menanyakan hal yang
    sama adalah dua tempat yang dapat berselisih pada hari salah satunya
    diperbaiki.
    """

    @property
    def ambang(self) -> int:
        """Kelipatan pagu harian — D-06 Bagian 8.3, bukan angka tersendiri."""
        return self.pagu_harian * PENGALI_AMBANG_ANTREAN

    @property
    def mengerem(self) -> bool:
        """Sifat terhitung, bukan bidang.

        Bidang dapat diisi `False` oleh pemanggil yang lelah, dan pengereman
        yang dimatikan sekali tidak akan pernah menyala lagi.
        """
        return self.hari_berturut_melampaui >= HARI_BERTURUT_SEBELUM_PENGEREMAN

    @property
    def kanal_diperlambat(self) -> tuple[Kanal, ...]:
        """K-C saja, dan hanya ketika mengerem — lihat uraian modul."""
        return _KANAL_DIPERLAMBAT if self.mengerem else ()

    @property
    def paruh_kedua_tertahan(self) -> str:
        """Bagian pengereman yang belum dapat dijalankan — lihat uraian modul."""
        return _PARUH_KEDUA_TERTAHAN


def pantau(
    panjang_harian: Sequence[int], *, pagu_harian: int = PAGU_KURASI_HARIAN
) -> HasilPantauan:
    """Baca riwayat panjang antrean harian — R-11.

    `panjang_harian` berurutan dari hari terlama ke hari terakhir. Riwayat
    diserahkan pemanggil: membacanya menuntut akses penyimpanan, dan itu milik
    `src/penyimpanan/` menurut `AGENTS.md`.
    """
    if not panjang_harian:
        raise GalatAntrean(
            "riwayat antrean kosong — pemantauan tanpa data tidak dapat menyatakan "
            "antrean aman"
        )
    if any(panjang < 0 for panjang in panjang_harian):
        raise GalatAntrean("panjang antrean tidak dapat bernilai negatif")

    ambang = pagu_harian * PENGALI_AMBANG_ANTREAN
    berturut = 0
    for panjang in reversed(panjang_harian):
        if panjang <= ambang:
            break
        berturut += 1

    return HasilPantauan(
        panjang_antrean=panjang_harian[-1],
        pagu_harian=pagu_harian,
        hari_berturut_melampaui=berturut,
    )
