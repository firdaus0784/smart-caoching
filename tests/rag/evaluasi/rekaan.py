"""Pembentuk baris *gold set* **rekaan** bagi uji fitur 040.

Isinya bukan *gold set*. D-08 Bagian 5.2 menyerahkan penyusunannya kepada tim
substansi, dan spec fitur 025 menyatakan alasannya: agen yang menyusunnya
menguji dirinya sendiri. Setiap pertanyaan di sini berawalan `REKAAN` agar
tidak pernah terbaca sebagai pertanyaan kepala sekolah.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from src.rag.evaluasi.gold_set import KOMPOSISI_D08, JenisPertanyaan

_KUNCI_MINIMUM = {"A": 1, "B": 1, "C": 0, "D": 0, "E": 1, "F": 2}


def baris(
    id_: str,
    jenis: str = "A",
    *,
    pertanyaan: str | None = None,
    kategori: str | None = "K1",
    kunci: Sequence[tuple[str, str]] | None = None,
    bernomor_regulasi: bool = False,
) -> dict[str, object]:
    """Satu baris sah menurut D-08 Bagian 5.3, kecuali diubah pemanggil."""
    if kunci is None:
        kunci = [("DOK-REKAAN", f"Pasal {i + 1}") for i in range(_KUNCI_MINIMUM[jenis])]
    return {
        "id": id_,
        "pertanyaan": pertanyaan or f"REKAAN pertanyaan {id_}?",
        "jenis": jenis,
        "kategori": None if jenis == "D" else kategori,
        "kunci": [{"dokumen": d, "bagian": b} for d, b in kunci],
        "bernomor_regulasi": bernomor_regulasi,
    }


def berkas(*isi: Mapping[str, object]) -> str:
    """Baris-baris menjadi teks JSON Lines."""
    return "".join(json.dumps(b, ensure_ascii=False) + "\n" for b in isi)


def komposisi_penuh(
    kunci: Mapping[JenisPertanyaan, Sequence[tuple[str, str]]] | None = None,
) -> list[dict[str, object]]:
    """Baris rekaan berkomposisi D-08 Bagian 5.1 persis."""
    hasil: list[dict[str, object]] = []
    for jenis, jumlah in KOMPOSISI_D08.items():
        for i in range(jumlah):
            hasil.append(
                baris(
                    f"REKAAN-{jenis.value}-{i:03d}",
                    jenis.value,
                    kunci=None if kunci is None else kunci.get(jenis),
                )
            )
    return hasil
