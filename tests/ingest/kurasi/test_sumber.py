"""Metadata sumber butir — T-4 fitur 013, K-3, KL-04."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.ingest.kurasi.sumber import SumberButir

SAH = {"judul": "Laporan", "penerbit": "Kemendikdasmen", "tahun": 2025}


def test_tautan_boleh_kosong_atau_https() -> None:
    assert SumberButir(**SAH).tautan is None
    assert SumberButir(**SAH, tautan="https://contoh.go.id/a").tautan == "https://contoh.go.id/a"


@pytest.mark.parametrize(
    "ubah",
    [
        {"tautan": "http://contoh.go.id"},
        {"tautan": "https://contoh.go.id/a b"},
        {"tautan": "javascript:alert(1)"},
        {"judul": "  "},
        {"penerbit": ""},
        {"tahun": 1900},
        {"lain": "x"},
    ],
)
def test_bentuk_salah_ditolak(ubah: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SumberButir(**{**SAH, **ubah})
