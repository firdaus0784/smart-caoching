"""Pemeriksa penyimpangan keluaran — VS-09, R-07, FR-F16, D-13 KD-13.

Kendali atas AN-03: *"Penyimpangan perilaku keluaran — model mengubah persona,
memuat instruksi, atau menyisipkan tautan keluar."*

Tiga hal diperiksa, dan ketiganya **bentuk**:

1. Kontrak D-07 Bagian 5.1 dipenuhi — maksimal tiga butir ringkasan,
   masing-masing ≤ 20 kata (NFR-19, C-13).
2. Tautan yang muncul berasal dari metadata segmen yang benar-benar diambil.
3. Keluaran tidak memuat kalimat yang ditujukan kepada **sistem**, bukan
   kepada kepala sekolah.

## Tautan diperiksa terhadap metadata, bukan terhadap daftar ranah

Ranah tepercaya adalah daftar yang bertambah, dan yang bertambah akan
ditambahi — sekali oleh orang yang butuh satu tautan lagi, dan sesudah itu
daftarnya tidak menjaga apa pun. Lebih tajam lagi: penyerang yang dapat menaruh
satu halaman pada ranah tepercaya kemudian dapat mengarahkan pembaca ke mana
saja.

Yang dibandingkan karena itu **tautan segmen itu sendiri**, bukan ranahnya.

## Bentuk, bukan kosakata

Daftar hitam kata ditolak: ia meloloskan setiap ungkapan yang belum pernah
terlihat, dan yang belum pernah terlihat justru yang dipakai penyerang. Sama
alasannya dengan daftar putih lisensi pada fitur 006, dari arah sebaliknya.

Yang dicari adalah **kalimat perintah yang ditujukan kepada sistem** — pola
yang menggabungkan kata kerja perintah dengan sasaran berupa aturan, instruksi,
atau persona. "Kepala sekolah dapat mengabaikan usulan yang tidak berdasar"
memuat kata yang sama dan sepenuhnya wajar; pemeriksa yang menolaknya akan
menolak jawaban manajerial yang sah, lalu dimatikan orang.

## Batas yang diakui terbuka

Sama dengan pemeriksa C-02 dan C-03: ini pembacaan bentuk. D-13 PT-01 sudah
menyatakannya — *"Penyisipan akan berhasil sesekali; rancangan mengasumsikan
itu."* Yang membatasi kerugian bukan pemeriksa ini melainkan **ketiadaan
kemampuan bertindak** (C-17, KD-09, PT-02). Menganggap pemeriksa ini sebagai
pengaman utama adalah pengulangan TA-01 pada tempat yang berbeda.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from src.rag.validator.keluaran import KeluaranModel, SegmenRujukan
from src.rag.validator.pemeriksaan import HasilPemeriksaan, KodePemeriksaan, Status

JUMLAH_BUTIR_RINGKASAN_MAKSIMUM = 3
"""D-07 Bagian 5.1: `ringkasan_tindakan` maksimal 3 butir."""

JUMLAH_KATA_MAKSIMUM = 20
"""NFR-19 dan C-13: kalimat ≤ 20 kata. Batasnya "≤", bukan "<"."""

_SASARAN_SISTEM = r"(instruksi|aturan|perintah|batasan|pesan)"
_POLA_INSTRUKSI: tuple[re.Pattern[str], ...] = (
    re.compile(rf"\b(abaikan|lupakan|hiraukan)\b[^.]*\b{_SASARAN_SISTEM}\b", re.IGNORECASE),
    re.compile(r"\b(mulai sekarang|sejak sekarang)\b[^.]*\banda adalah\b", re.IGNORECASE),
    re.compile(r"\b(system|sistem)\s*:", re.IGNORECASE),
    re.compile(r"\bubah\s+persona\b", re.IGNORECASE),
    re.compile(r"\b(abaikan|lupakan)\b[^.]*\b(di atas|sebelumnya)\b", re.IGNORECASE),
)
"""Pola kalimat yang ditujukan kepada sistem, bukan kepada kepala sekolah.

Masing-masing menuntut **dua** bagian — kata kerja perintah **dan** sasaran
yang hanya masuk akal bila lawan bicaranya sistem. Pola berkata tunggal akan
menolak "kepala sekolah dapat mengabaikan usulan yang tidak berdasar", dan
penolakan yang salah itu yang membuat pemeriksa dimatikan orang.
"""


def _tautan_sah(segmen: Sequence[SegmenRujukan]) -> frozenset[str]:
    return frozenset(s.tautan for s in segmen if s.tautan is not None)


def _gagal(alasan: str) -> HasilPemeriksaan:
    """Kegagalan VS-09 tidak pernah menunjuk klaim tertentu.

    D-07 Bagian 6.2: jawaban dibuang tanpa perbaikan, dicatat sebagai
    `injection_suspected` dan ditelusuri. Perbaikan sebagian atas keluaran yang
    disusupi menghasilkan jawaban yang tampak bersih dari keluaran yang tidak
    dipercaya.
    """
    return HasilPemeriksaan(kode=KodePemeriksaan.VS_09, status=Status.GAGAL, alasan=alasan)


def periksa_penyimpangan(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> HasilPemeriksaan:
    """**VS-09** — keluaran memenuhi kontrak dan tidak menyimpang (R-07)."""
    if len(keluaran.ringkasan_tindakan) > JUMLAH_BUTIR_RINGKASAN_MAKSIMUM:
        return _gagal(
            f"ringkasan tindakan memuat {len(keluaran.ringkasan_tindakan)} butir, "
            f"melampaui {JUMLAH_BUTIR_RINGKASAN_MAKSIMUM} (D-07 Bagian 5.1)"
        )

    for butir in keluaran.ringkasan_tindakan:
        if len(butir.split()) > JUMLAH_KATA_MAKSIMUM:
            return _gagal(f"butir ringkasan melampaui {JUMLAH_KATA_MAKSIMUM} kata (NFR-19, C-13)")

    sah = _tautan_sah(segmen)
    asing = tuple(t for t in keluaran.tautan_disebut if t not in sah)
    if asing:
        return _gagal(
            "keluaran memuat tautan yang tidak berasal dari metadata segmen terambil — "
            f"indikasi AN-03 (FR-F16); tautan: {sorted(asing)}"
        )

    teks = "\n".join(
        (keluaran.penjelasan, keluaran.catatan_keberlakuan, *keluaran.ringkasan_tindakan)
    )
    for pola in _POLA_INSTRUKSI:
        if pola.search(teks):
            return _gagal(
                "keluaran memuat kalimat yang ditujukan kepada sistem, bukan kepada "
                "kepala sekolah — indikasi penyisipan instruksi (AN-03, KD-13)"
            )

    return HasilPemeriksaan(
        kode=KodePemeriksaan.VS_09,
        status=Status.LULUS,
        alasan="kontrak D-07 Bagian 5.1 terpenuhi; tautan berasal dari metadata segmen; "
        "tidak ada bentuk instruksi",
    )
