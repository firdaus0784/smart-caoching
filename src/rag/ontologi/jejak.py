"""Pencatatan ekspor ontologi — R-10, C-09, D-10 Bagian 4.

Ontologi diekspor untuk **HKI dan publikasi**. C-09 menuntut setiap keluaran
mencatat versinya, dan di sini yang wajib tercatat bukan hanya versinya
melainkan **kedua angka** — sah dan mentah.

Sebabnya: naskah akan menyebut satu angka. Bila kelak seseorang membandingkan
angka pada naskah dengan jumlah simpul pada berkas ekspornya, selisih yang
tidak dapat diterangkan menjadi pertanyaan yang tidak ada yang dapat menjawab.
Catatan ini jawabannya.

Ditulis ke **L2**, sama dengan pencatatan keluaran OCR fitur 015, catatan
batch anotasi fitur 003, dan penempatan indeks fitur 006: ia menerangkan
bagaimana sepotong artefak terbentuk.
"""

from __future__ import annotations

from pathlib import Path

from src.logbook.penulis import Buku, tambah_baris
from src.rag.ontologi.hitung import HasilHitung


def catat_ekspor(akar_logbook: Path, hitungan: HasilHitung, *, versi: str, sidik: str) -> None:
    """Satu baris L2 bagi satu ekspor ontologi — R-10, C-09.

    `sidik` adalah sidik untai hasil ekspornya. Tanpanya, dua ekspor berversi
    sama yang isinya berbeda tidak dapat dibedakan — dan versi yang sama
    dengan isi berbeda adalah keadaan yang muncul justru ketika seseorang
    memperbaiki satu definisi tanpa menaikkan versinya.
    """
    tambah_baris(
        akar_logbook,
        Buku.L2,
        {
            "artefak": "ekspor-ontologi",
            "peristiwa": "ontologi diekspor sebagai JSON-LD",
            "versi": versi,
            "sidik": sidik,
            "konsep_sah": hitungan.konsep_sah,
            "konsep_mentah": hitungan.konsep_mentah,
            "relasi_sah": hitungan.relasi_sah,
            "relasi_mentah": hitungan.relasi_mentah,
        },
    )
