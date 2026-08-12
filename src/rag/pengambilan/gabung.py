"""Penggabungan peringkat — R-04, R-05, R-06, ADR-03, D-07 Bagian 4.4.

*Reciprocal Rank Fusion* (Cormack dkk. 2009). D-07 Bagian 4.4 memilihnya
dengan alasan kelayakan yang dinyatakan terbuka: *"Pemilihan Reciprocal Rank
Fusion, bukan pembobotan manual, adalah keputusan kelayakan: penyetelan bobot
menuntut data pengujian yang belum tersedia pada awal Fase 3."*

Ia bekerja atas **peringkat**, bukan atas skor. Itu bukan penyederhanaan
melainkan syarat: skor BM25 dan skor kemiripan vektor tidak sebanding, dan
menjumlahkannya langsung membuat sisi yang kebetulan berskala lebih besar
selalu menang.

## Mengapa modul ini menolak satu sumber

**Bahaya utama fitur 007, dan ia tidak menghasilkan satu galat pun.**

Penggabungan atas satu daftar mengembalikan daftar itu — urutan yang sama,
tanpa galat, dengan nama fungsi yang tetap berbunyi `gabung_peringkat`, dan
seluruh uji tetap hijau. ADR-03 menolak dua hal secara tegas: *"Vektor saja —
gagal pada nomor regulasi... Leksikal saja — gagal pada parafrase pengguna."*

Sisi vektor belum dapat dibangun; ia fitur 019. Hari ketika seseorang
menjalankan sistem ini tanpa memasangnya, sistem **berhenti** — bukan diam-diam
menjadi mesin pencari kata kunci yang ADR-03 sudah menolaknya.

Dua penjagaan bekerja bersama, dan masing-masing sendirian bocor:

- **Menolak kurang dari dua sumber** — dapat dipuaskan pelaksana kosong yang
  mengembalikan daftar kosong tanpa mencari apa pun. Karena itu tiruan sumber
  vektor tinggal di `tests/`, bukan di `src/` (KB-034 pertanyaan 3).
- **Setiap hasil membawa penyumbangnya** — hanya melaporkan, tidak menahan.
  Tetapi tanpanya tidak ada cara membedakan segmen yang disetujui kedua sumber
  dari segmen yang ditemukan satu sumber pada peringkat tinggi, dan perbedaan
  itulah yang akan dibaca saat BT-29 mengalibrasi.

## Daftar kosong tetap terhitung sebagai sumber

Sumber yang tidak menemukan apa pun **mencari**. Menolaknya akan membuat
setiap kueri yang hanya cocok pada satu sisi gagal seluruhnya — dan kueri
semacam itu justru yang ADR-03 tuju: nomor regulasi ditemukan leksikal dan
tidak ditemukan vektor.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from src.rag.pengambilan.kandidat import HasilSumber
from src.rag.pengambilan.tetapan import JUMLAH_SUMBER_MINIMUM, TETAPAN_RRF_K


class Penyumbang(BaseModel):
    """Satu sumber yang menemukan sebuah segmen, beserta peringkatnya di sana."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    nama_sumber: str = Field(min_length=1)
    peringkat: int = Field(ge=1)
    """Peringkat dihitung dari 1. Peringkat 0 akan menyumbang `1/k` — nilai
    yang lebih besar daripada peringkat pertama yang sah."""


class HasilGabungan(BaseModel):
    """Satu segmen sesudah penggabungan, beserta seluruh penyumbangnya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_segmen: str = Field(min_length=1)
    skor: float = Field(gt=0.0)
    penyumbang: tuple[Penyumbang, ...] = Field(min_length=1)
    """Sumber yang menemukan segmen ini, terurut menurut nama — R-06.

    Tidak pernah kosong: hasil gabungan tanpa penyumbang adalah segmen yang
    tidak ditemukan sumber mana pun, dan ia tidak boleh ada pada keluaran sama
    sekali. Terurut agar dapat dibandingkan langsung pada uji dan pada catatan
    percobaan D-10.
    """


def gabung_peringkat(hasil_sumber: Sequence[HasilSumber]) -> tuple[HasilGabungan, ...]:
    """Gabungkan daftar berperingkat dengan *Reciprocal Rank Fusion*.

    `skor(d) = Σ 1 / (k + peringkat_s(d))` atas seluruh sumber `s` yang
    menemukan `d`. Seri diputus `id_segmen` menaik — pada penggabungan, seri
    jauh lebih sering daripada pada BM25, sebab skornya hanya bergantung pada
    peringkat dan peringkat berupa bilangan bulat kecil.
    """
    if len(hasil_sumber) < JUMLAH_SUMBER_MINIMUM:
        raise ValueError(
            f"penggabungan menuntut sekurangnya {JUMLAH_SUMBER_MINIMUM} sumber, "
            f"diberi {len(hasil_sumber)} — ADR-03 menolak pengambilan leksikal saja "
            "maupun vektor saja, dan penggabungan atas satu daftar mengembalikan "
            "daftar itu tanpa satu galat pun"
        )

    nama = [h.nama_sumber for h in hasil_sumber]
    if len(nama) != len(set(nama)):
        raise ValueError(
            "dua daftar dengan nama sumber yang sama memenuhi hitungan dua tanpa "
            "memenuhi maksudnya; daftar penyumbangnya juga akan menyebut satu "
            f"sumber dua kali: {sorted(nama)}"
        )

    skor: dict[str, float] = {}
    penyumbang: dict[str, list[Penyumbang]] = {}
    for satu in hasil_sumber:
        for urutan, kandidat in enumerate(satu.peringkat, start=1):
            skor[kandidat.id_segmen] = skor.get(kandidat.id_segmen, 0.0) + 1 / (
                TETAPAN_RRF_K + urutan
            )
            penyumbang.setdefault(kandidat.id_segmen, []).append(
                Penyumbang(nama_sumber=satu.nama_sumber, peringkat=urutan)
            )

    gabungan = [
        HasilGabungan(
            id_segmen=id_segmen,
            skor=nilai,
            penyumbang=tuple(sorted(penyumbang[id_segmen], key=lambda p: p.nama_sumber)),
        )
        for id_segmen, nilai in skor.items()
    ]
    return tuple(sorted(gabungan, key=lambda h: (-h.skor, h.id_segmen)))
