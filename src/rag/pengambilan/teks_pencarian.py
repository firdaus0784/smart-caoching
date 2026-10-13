"""Teks pencarian leksikal — T-2 fitur 041, R-01, R-04, TK-88, D-07 Bagian 3.3.

Pemotongan D-07 Bagian 3.2 menaruh judul, nomor, dan tahun regulasi hanya
pada segmen pembukaan. Tanpa judul, pertanyaan yang menyebut "Nomor 6 Tahun
2021" mencocokkan nomornya pada pembukaan, dan pasal berisi serupa dari
regulasi lain tidak dapat dibedakan dari pasal yang ditanyakan.

**Hanya yang dicari, bukan yang dibaca.** Teks pencarian membangun indeks
leksikal saja. Teks segmen yang disimpan, dikirim ke model, ditampilkan
pembaca sumber, dan diperiksa validator tetap teks segmen (P-1 A).

**Tanpa bobot** (C-16). Judul ditulis sekali, tidak diulang: mengulangnya
adalah bobot yang disamarkan.
"""

from __future__ import annotations

from typing import Final

ATURAN_PENCARIAN: Final = "pencarian:judul-1"
"""Penanda aturan pada versi indeks — D-07 Bagian 3.3. Naik bila aturan
berubah, agar putaran U3 sebelum dan sesudahnya tidak terbaca sebagai indeks
yang sama (R-04)."""


def teks_pencarian(judul: str, teks: str) -> str:
    """Judul dokumen, baris baru, teks segmen."""
    return f"{judul}\n{teks}"
