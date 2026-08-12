"""Pemeriksaan cakupan domain — R-02, R-03, FR-F13, D-07 Bagian 4.1.

Tahap 1 pada alur D-07 Bagian 4. Pertanyaan di luar manajemen sekolah dasar
ditolak **sebelum mencapai pengambilan**, dan *"tidak dikirim ke LLM sama
sekali"*.

D-07 menyebut dua alasannya, dan keduanya perlu: menghemat biaya, **dan**
mencegah sistem memberi nasihat pada bidang yang tidak memiliki dasar rujukan
sama sekali di korpusnya. Yang kedua bukan soal biaya.

## Daftar hitam, dan arahnya berlawanan dengan fitur 006

`indeks.py` fitur 006 memilih **daftar putih** bagi lisensi, dengan alasan yang
tertulis di sana: daftar hitam meloloskan setiap sebutan yang belum pernah
terlihat. Modul ini memilih sebaliknya, dan itu bukan ketidakkonsistenan
melainkan arah kerugian yang berlawanan:

| | Kekeliruan ke arah longgar | Kekeliruan ke arah ketat |
|---|---|---|
| Lisensi (006) | **Menggugurkan publikasi** | Mengurangi jumlah butir |
| Cakupan domain | Satu panggilan yang berakhir tidak-ditemukan | **Menolak kepala sekolah yang bertanya wajar** |

D-02 titik kritis T1: jawaban pertama menentukan retensi. Kepala sekolah yang
pertanyaan sahnya ditolak tidak bertanya kedua kalinya.

## Batas yang diakui terbuka

Daftar hitam **meloloskan yang belum pernah terlihat**. Penutupnya bukan
pemeriksaan ini melainkan **penilaian kecukupan bukti**: pertanyaan di luar
domain tidak memiliki segmen pendukung pada korpus, sehingga berakhir pada
`tidak_ditemukan` (FR-F04). FR-F13 memangkas biaya dan mempercepat; ia bukan
lapisan tunggal, dan menganggapnya begitu adalah pengulangan TA-01.

## Pola menuntut niat pribadi, bukan kata

Yang dicari bukan kata "kesehatan" melainkan **pertanyaan yang menempatkan
penanyanya sebagai pasien, terdakwa, atau nasabah**. "Bagaimana mengelola
program kesehatan sekolah" dan "obat apa untuk sakit kepala saya" berbagi satu
ranah dan tidak berbagi satu pun maksud.

Penyaring berkata tunggal menolak keduanya, lalu dimatikan orang — dan yang
mati bersamanya adalah FR-F13 seluruhnya.
"""

from __future__ import annotations

import re

RANAH_TERLARANG: tuple[str, ...] = ("medis", "hukum_pidana", "keuangan_pribadi")
"""Ranah yang FR-F13 sebut.

Tertulis agar penambahan ranah menjadi keputusan yang terbaca, bukan satu baris
yang menyelinap. FR-F13 berbunyi "dan sebagainya"; perluasannya tetap keputusan
manusia.
"""

PESAN_DI_LUAR_DOMAIN = (
    "Sistem ini menjawab pertanyaan seputar manajemen sekolah dasar. "
    "Silakan ajukan pertanyaan mengenai pengelolaan sekolah Anda."
)
"""Penolakan menyebut **cakupan**, bukan kesalahan.

D-07 Bagian 4.1: "Penolakan disampaikan dengan menyebutkan cakupan sistem,
bukan sebagai pesan galat." Pengguna yang menerima pesan galat menyimpulkan
sistemnya rusak; pengguna yang menerima keterangan cakupan tahu apa yang dapat
ditanyakannya.

Dua kalimat, masing-masing ≤ 20 kata (NFR-19, C-13).
"""

_PENANDA_PRIBADI = r"(saya|aku|pribadi|milik saya)"

_POLA: dict[str, tuple[re.Pattern[str], ...]] = {
    "medis": (
        re.compile(rf"\b(obat|dosis|gejala|diagnosis|resep)\b[^.?]*\b{_PENANDA_PRIBADI}\b", re.I),
        re.compile(rf"\b{_PENANDA_PRIBADI}\b[^.?]*\b(sakit|demam|nyeri|obat|dosis)\b", re.I),
    ),
    "hukum_pidana": (
        re.compile(r"\b(menuntut|dituntut|dipenjara|ancaman hukuman|hukuman pidana)\b", re.I),
        re.compile(r"\b(pengadilan|pidana)\b[^.?]*\b(saya|tetangga|pribadi)\b", re.I),
    ),
    "keuangan_pribadi": (
        re.compile(rf"\b(investasi|saham|kartu kredit|pinjaman|bunga)\b[^.?]*\b{_PENANDA_PRIBADI}\b", re.I),
        re.compile(rf"\b{_PENANDA_PRIBADI}\b[^.?]*\b(investasi|saham|kartu kredit|pinjaman)\b", re.I),
    ),
}
"""Pola per ranah, masing-masing menuntut **dua** bagian.

Kata ranah **dan** penanda bahwa penanyanya subjek pribadinya — pasien,
terdakwa, nasabah. Pola berkata tunggal menolak "bagaimana mengelola program
kesehatan sekolah", dan penolakan yang salah itu yang membuat penjagaan
dimatikan orang.
"""


def ranah_di_luar_domain(pertanyaan: str) -> str | None:
    """Ranah terlarang yang cocok, atau `None`.

    Mengembalikan namanya, bukan hanya benar-salah: telemetri RT dan penelusuran
    memerlukan **ranah mana**, dan penolakan tanpa sebabnya tidak dapat ditinjau
    apakah ia benar.
    """
    if not pertanyaan.strip():
        return None
    for ranah in RANAH_TERLARANG:
        if any(pola.search(pertanyaan) for pola in _POLA[ranah]):
            return ranah
    return None


def di_luar_domain(pertanyaan: str) -> bool:
    """Apakah pertanyaan berada di luar manajemen sekolah dasar (FR-F13).

    Kueri kosong **bukan** di luar domain: ia pemanggilan yang keliru, dan
    menyamakannya membuat pengguna yang menekan kirim tanpa mengetik menerima
    keterangan cakupan yang tidak relevan.
    """
    return ranah_di_luar_domain(pertanyaan) is not None
