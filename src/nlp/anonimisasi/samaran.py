"""Penyamaran enam pengenal berpola — T-3 fitur 037, FR-B04, P-5 A, KM-03.

Pendeteksi fitur 015 **melapor**; modul ini yang menyamarkan, memakai rentang
laporannya. Keduanya sengaja terpisah: pendeteksi yang juga menyamarkan akan
menggoda siapa pun melonggarkan polanya ketika hasil samaran terasa terlalu
banyak.

**Teks asli tidak dibawa keluar.** `HasilSamaran` memuat teks bertoken dan
jumlah per jenis, tidak pernah nilai yang disamarkan — bentuk yang sama dengan
`Temuan` pendeteksi (R-11 fitur 015). Gerbang ingesti menyimpan hasil ini,
bukan teks yang diterimanya (P-5 A).

**Token milik D-03**, bukan dikarang di sini: `[NIK]`, `[NIP]`, `[NISN]`,
`[NUPTK]`, `[TELEPON]`, `[REKENING]`. Pedoman anotasi mengenali token itu
sebagai hasil penyamaran, bukan isi, sehingga tidak dianotasi.

**Penggantian dari akhir ke awal.** Indeks karakter rentang yang lebih awal
tidak bergeser oleh penggantian di belakangnya (C-10).

**Yang tidak tersamarkan, dinyatakan:** nama perorangan, alamat, nama sekolah
sebagai penunjuk orang, dan nomor yang ditulis terurai. Keduanya yang pertama
menunggu model NER (BT-70). Verifikasi manusia (FR-B05) tetap yang menahannya.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from src.nlp.anonimisasi.pola import JENIS, Temuan, periksa_data_pribadi

TOKEN: Final[dict[str, str]] = {
    "nik": "[NIK]",
    "nip": "[NIP]",
    "nisn": "[NISN]",
    "nuptk": "[NUPTK]",
    "telepon": "[TELEPON]",
    "rekening": "[REKENING]",
}
"""Token penyamaran per jenis — `docs/D03.md`, daftar token penyamaran."""


@dataclass(frozen=True)
class HasilSamaran:
    """Teks bertoken dan jumlah samaran per jenis — keenam jenis, termasuk
    yang nol, berurutan seperti `JENIS`. Tanpa nilai yang disamarkan."""

    teks: str
    jumlah: dict[str, int]


def samarkan(
    teks: str, pendeteksi: Callable[[str], list[Temuan]] = periksa_data_pribadi
) -> HasilSamaran:
    """Ganti setiap rentang temuan dengan token jenisnya.

    Rentang yang bertindih digabung menjadi satu token berjenis temuan yang
    lebih dulu: dua token bertumpuk akan meninggalkan potongan nilai di
    antaranya. Pendeteksi fitur 015 tidak menghasilkan rentang bertindih; yang
    dijaga di sini pendeteksi lain yang kelak menggantikannya.

    Jenis di luar keenam ditolak, bukan dilewati: rentang yang dilewati adalah
    nilai yang tersimpan apa adanya.
    """
    jumlah = dict.fromkeys(JENIS, 0)
    rentang: list[tuple[int, int, str]] = []
    for temuan in sorted(pendeteksi(teks), key=lambda t: (t.mulai, t.akhir)):
        if temuan.jenis not in TOKEN:
            raise ValueError(f"jenis tanpa token penyamaran: {temuan.jenis}")
        if rentang and temuan.mulai < rentang[-1][1]:
            mulai, akhir, jenis = rentang[-1]
            rentang[-1] = (mulai, max(akhir, temuan.akhir), jenis)
            continue
        rentang.append((temuan.mulai, temuan.akhir, temuan.jenis))

    hasil = teks
    for mulai, akhir, jenis in reversed(rentang):
        hasil = hasil[:mulai] + TOKEN[jenis] + hasil[akhir:]
        jumlah[jenis] += 1
    return HasilSamaran(teks=hasil, jumlah=jumlah)
