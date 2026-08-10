"""Pencatatan penempatan segmen ke indeks — R-08, C-09, C-02.

Setiap penempatan tercatat **beserta lisensi yang mendasarinya**, dan itu yang
membuat catatan ini berguna: indeks tujuan saja tidak dapat diperiksa
kebenarannya berbulan kemudian, sebab yang menentukannya — lisensi sumber —
tidak ikut tersimpan di mana pun yang dapat ditelusuri audit.

Audit lisensi menanyakan satu hal: **atas dasar apa segmen ini ditempatkan di
indeks utama?** Tanpa catatan ini, jawabannya hanya dapat disusun dengan
membaca ulang metadata sumber yang mungkin sudah berubah.

Ditulis ke **L2**, bukan L1: ia menerangkan bagaimana sepotong korpus
terbentuk, bukan hipotesis apa yang diuji. Sama dengan pencatatan keluaran OCR
fitur 015 dan catatan batch anotasi fitur 003.

**Isi segmen tidak pernah masuk catatan**, hanya pengenal, lisensi, dan indeks
tujuannya. Segmen dapat memuat teks sekolah sungguhan.
"""

from __future__ import annotations

from pathlib import Path

from src.logbook.penulis import Buku, tambah_baris
from src.penyimpanan.indeks import SegmenTerindeks


def catat_penempatan(akar_logbook: Path, segmen: SegmenTerindeks, *, sumber_lisensi: str) -> None:
    """Satu baris L2 bagi satu penempatan — R-08, C-09.

    `sumber_lisensi` adalah keterangan lisensi **apa adanya dari metadata
    sumber**, bukan hasil pembacaannya. Menyimpan hasilnya saja membuat
    kekeliruan pembacaan tidak dapat ditelusuri: yang tercatat akan selalu
    tampak konsisten dengan indeks tujuannya, sebab keduanya berasal dari
    fungsi yang sama.
    """
    tambah_baris(
        akar_logbook,
        Buku.L2,
        {
            "artefak": "penempatan-indeks",
            "peristiwa": "segmen ditempatkan ke indeks",
            "id_segmen": segmen.id_segmen,
            "id_dokumen": segmen.id_dokumen,
            "indeks_tujuan": segmen.indeks_tujuan.value,
            "lisensi": segmen.lisensi.value,
            "sumber_lisensi": sumber_lisensi,
            "panjang_karakter": len(segmen.teks),
        },
    )
