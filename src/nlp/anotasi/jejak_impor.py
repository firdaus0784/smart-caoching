"""Pencatatan impor anotasi ke logbook — R-14, C-09, D-10 Bagian 4.

C-09 menuntut setiap keluaran mencatat versinya. Pada impor anotasi yang wajib
tercatat bukan versi kode melainkan tiga hal yang **tidak satu pun dapat
dipulihkan dari korpusnya kemudian**:

| Yang dicatat | Mengapa tidak dapat dipulihkan |
|---|---|
| Versi Label Studio | Tidak dituliskan pada berkas ekspornya sendiri (KB-023) |
| Versi skema | Diberikan pemanggil; korpus dapat memuat dua versi |
| Keadaan bendera | Korpus tanpa bendera terbaca sama dengan korpus bersih |

Baris ketiga yang paling menentukan. Korpus yang diimpor dari proyek tanpa
kendali bendera membawa `bendera: null` pada berkas JSONL-nya — tetapi berkas
disalin, dipotong, dan digabung, dan pada salinan ketiga tidak ada lagi yang
mengingat mengapa nilainya `null`. Catatan ini satu-satunya tempat
pembedaannya bertahan.

Ditulis ke **L2**, bukan L1, dengan alasan yang sama seperti pencatatan
keluaran OCR fitur 015: ia menerangkan bagaimana sepotong korpus terbentuk,
bukan hipotesis apa yang diuji.

**Isi dokumen dan kode anotator tidak masuk catatan.** Yang pertama karena
dokumen anotasi memuat teks sekolah sungguhan; yang kedua karena catatan L2
menerangkan bagaimana korpus terbentuk, bukan siapa yang mengerjakannya — dan
yang kedua sudah ada pada korpusnya sendiri.
"""

from __future__ import annotations

from pathlib import Path

from src.logbook.penulis import Buku, tambah_baris
from src.nlp.anotasi.impor_ls import HasilImpor


def catat_impor(akar_logbook: Path, hasil: HasilImpor, *, versi_label_studio: str) -> None:
    """Satu baris L2 bagi satu impor — R-14, C-09.

    `versi_label_studio` bersifat kata kunci dan wajib. Ia tidak dapat dibaca
    dari berkas ekspornya, sehingga menyediakan nilai bawaan berarti mencatat
    versi yang tidak pernah diperiksa siapa pun — dan baris tanpa versi lebih
    buruk daripada tidak ada baris, sebab ia terbaca seperti catatan yang
    lengkap.
    """
    if not versi_label_studio:
        raise ValueError(
            "versi Label Studio wajib diisi — ia tidak tertulis pada berkas "
            "ekspornya, sehingga catatan tanpa versi menghilangkan satu-satunya "
            "keterangan tentang bentuk apa yang diurai (C-09)"
        )

    tambah_baris(
        akar_logbook,
        Buku.L2,
        {
            "artefak": "impor-anotasi",
            "peristiwa": "ekspor Label Studio diimpor menjadi korpus",
            "versi_label_studio": versi_label_studio,
            "versi_skema": str(hasil.versi_skema),
            "jumlah_dokumen": len(hasil.dokumen),
            "jumlah_dilewati": len(hasil.dilewati),
            "bendera_terkumpul": hasil.bendera_terkumpul,
        },
    )
