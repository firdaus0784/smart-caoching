"""Metadata sumber sebuah butir — T-4 fitur 013, K-3, KL-04, D-05 S-06 blok 7.

D-05 S-06 blok 7 menuntut nama, penerbit, tahun, dan tautan sumber.
`ButirPengetahuan` hanya membawa `id_dokumen_sumber`, dan model `Dokumen`
tidak memiliki tautan. Salinan metadata ini menyertai kandidat sejak masuk
antrean, sehingga peran yang menayangkan tidak pernah membaca korpus — yang
kolom isinya memuat teks penuh, termasuk teks berlisensi tertutup (C-02).

## Tautan ke halaman sumber, bukan unduhan

Hanya `https`. Tautan boleh kosong; yang menentukan boleh tidaknya teks penuh
ditawarkan adalah `boleh_teks_penuh` fitur 011, bukan keberadaan tautan.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.ingest.dokumen import TAHUN_PALING_AWAL


class SumberButir(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    judul: str = Field(min_length=1)
    penerbit: str = Field(min_length=1)
    tahun: int = Field(ge=TAHUN_PALING_AWAL)
    tautan: str | None = None

    @field_validator("judul", "penerbit")
    @classmethod
    def _tidak_hanya_spasi(cls, nilai: str) -> str:
        if not nilai.strip():
            raise ValueError("bidang sumber wajib terisi")
        return nilai

    @field_validator("tautan")
    @classmethod
    def _https(cls, nilai: str | None) -> str | None:
        if nilai is None:
            return None
        if not nilai.startswith("https://") or any(c.isspace() for c in nilai):
            raise ValueError("tautan sumber wajib https tanpa spasi")
        return nilai
