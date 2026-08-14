"""Penyusun tanggapan — R-10, R-11, R-12; D-07 Bagian 4 dan 5.

Mengubah `JawabanTervalidasi` (fitur 008) menjadi `Tanggapan` (D-14 Bagian
4.1). Ia tahap 10 pada alur D-07 Bagian 4 — penyajian — dan tidak melakukan
satu pun tahap sebelumnya.

## Hanya menerima `JawabanTervalidasi`, dan itu lapisan kedua

`susun()` tidak menerima `KeluaranModel`. Tipe `JawabanTervalidasi` hanya dapat
dibentuk `src/rag/validator/validator.py` (fitur 008, R-09), sehingga jalur dari
keluaran model ke tanggapan **melewati validator karena tidak ada jalan lain** —
bukan karena pemanggilnya ingat.

Tiga lapisan menjaga jalur itu, dan masing-masing menutup yang di bawahnya:

| Lapisan | Menutup |
|---|---|
| `JawabanTervalidasi` hanya dibentuk validator | jalur pintas dari keluaran model |
| `susun()` hanya menerima tipe itu | jalur pintas dari `KeluaranModel` |
| Pemeriksa C-19 aturan 1 | pembentukan tipe itu di luar validator |

Menghapus salah satunya meninggalkan dua. Itu sebabnya ketiganya ada meski
masing-masing terlihat cukup sendiri.

## Pemetaan `StatusDasar` satu tempat

`kecukupan.StatusDasar` (hasil tahap 7) dan `tanggapan.StatusDasar` (bidang
tanggapan) bernilai sama dan berbeda urusan. Pemetaan di antaranya tinggal di
sini — satu tempat, sehingga nilai kelima yang D-14 tambahkan kelak tidak
diam-diam jatuh ke salah satunya.

## Tidak menulis, tidak memanggil model

C-17 melarang akses tulis dari jalur penjawaban; C-08 menuntut seluruh
pemanggilan model lewat `src/llm/`. Modul ini melakukan keduanya dengan cara
yang sama: ia tidak menyentuh keduanya sama sekali.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.rag.jawaban.tanggapan import (
    PENAFIAN_BAKU,
    BacaanLanjutan,
    KlaimTampil,
    Sitasi,
    StatusDasar,
    Tanggapan,
    Versi,
)
from src.rag.pengambilan.kecukupan import StatusDasar as StatusKecukupan
from src.rag.validator.validator import JawabanTervalidasi

_PETA_STATUS: dict[StatusKecukupan, StatusDasar] = {
    StatusKecukupan.KUAT: StatusDasar.KUAT,
    StatusKecukupan.TERBATAS: StatusDasar.TERBATAS,
    StatusKecukupan.TIDAK_DITEMUKAN: StatusDasar.TIDAK_DITEMUKAN,
    StatusKecukupan.DI_LUAR_DOMAIN: StatusDasar.DI_LUAR_DOMAIN,
}
"""Satu tempat bagi pemetaan kedua enum — lihat uraian modul.

Berkunci enum, bukan berupa perbandingan berantai: nilai kelima yang D-14
tambahkan kelak menjadi `KeyError` yang berisik, bukan cabang `else` yang
diam.
"""


def status_tanggapan(status: StatusKecukupan) -> StatusDasar:
    """Petakan hasil tahap 7 menjadi bidang tanggapan.

    `KeyError` bila nilainya belum dipetakan — dan itu disengaja. Cabang `else`
    yang mengembalikan `TIDAK_DITEMUKAN` akan membuat nilai baru berakhir
    sebagai penolakan tanpa seorang pun memutuskannya.
    """
    return _PETA_STATUS[status]


def susun(
    jawaban: JawabanTervalidasi,
    *,
    id_pesan: str,
    versi: Versi,
    status: StatusKecukupan,
    sitasi: Sequence[Sitasi],
    bacaan_lanjutan: Sequence[BacaanLanjutan] = (),
    catatan_keberlakuan: str = "",
) -> Tanggapan:
    """Susun tanggapan dari jawaban yang **sudah tervalidasi** (R-10).

    `sitasi` dan `bacaan_lanjutan` diserahkan pemanggil, bukan disimpulkan dari
    segmennya. Keduanya menuntut metadata dokumen — judul, penerbit, tahun —
    yang tinggal pada `src/ingest/`, dan `AGENTS.md` tidak memberi `rag` tepi ke
    sana. Menyimpulkannya di sini akan menciptakan tepi tanpa keputusan gerbang,
    dan pemeriksa arah fitur 009 menolaknya.

    Bentuk yang sama dengan `segmen_resmi` pada `PenilaianKecukupan` fitur 007.
    """
    keluaran = jawaban.keluaran
    return Tanggapan(
        id_pesan=id_pesan,
        status_dasar=status_tanggapan(status),
        ringkasan_tindakan=keluaran.ringkasan_tindakan,
        penjelasan=keluaran.penjelasan,
        klaim=tuple(KlaimTampil(teks=k.teks, id_segmen=k.id_segmen) for k in keluaran.klaim),
        sitasi=tuple(sitasi),
        bacaan_lanjutan=tuple(bacaan_lanjutan),
        catatan_keberlakuan=catatan_keberlakuan,
        penafian=PENAFIAN_BAKU,
        versi=versi,
    )
