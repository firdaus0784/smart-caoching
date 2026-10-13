"""Kunci jawaban *gold set* — T-2 dan T-3 fitur 040, R-02, P-2 A, D-08 Bagian 5.3.

Kunci menunjuk **dokumen dan pasal**, bukan segmen. Tim substansi berpikir
dalam pasal, dan pengenal segmen berubah bila ukuran segmen D-07 Bagian 3.2
kelak berubah — sedangkan *gold set* yang beku tidak boleh ikut berubah.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Kunci(BaseModel):
    """Satu kunci: dokumen dan bagiannya."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    dokumen: str = Field(min_length=1)
    bagian: str = Field(min_length=1)
