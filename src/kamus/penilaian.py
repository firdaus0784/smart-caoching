"""Enum penilaian jawaban dan tindak lanjut aduan — FR-F07, FR-I04; `docs/D14.md` Bagian 5.1.

Ditulis pada T-4 fitur 036. Nilainya milik D-14, bukan milik lapisan yang
kebetulan pertama memakainya: `src/api/` menerimanya lewat rute,
`src/penyimpanan/` menyimpannya, dan analitik menghitungnya. Mengubah daftar
nilai adalah perubahan versi kamus (KM-04), bukan perubahan kode (AG-04).
"""

from __future__ import annotations

from enum import Enum


class NilaiPenilaian(Enum):
    """Tiga nilai FR-F07, setara — tidak ada urutan baik ke buruk."""

    MEMBANTU = "membantu"
    TIDAK_MEMBANTU = "tidak_membantu"
    KELIRU = "keliru"


class TindakLanjutAduan(Enum):
    """Empat tindak lanjut kurator atas aduan (P-3 B fitur 036).

    Tidak satu pun menambah pengetahuan secara langsung: sumber baru diajukan
    lewat kanal D-06 dan melewati gerbang kurasi seperti sumber lain (C-06).
    """

    SUMBER_DIAJUKAN = "sumber_diajukan"
    BUTIR_DITARIK = "butir_ditarik"
    JAWABAN_SESUAI_DASAR = "jawaban_sesuai_dasar"
    DI_LUAR_CAKUPAN = "di_luar_cakupan"
