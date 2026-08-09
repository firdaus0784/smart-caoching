"""Larangan impor `pytesseract` di luar satu modul — R-05, C-09, KB-017.

Bentuknya sama dengan `impor_penyedia.py` yang menegakkan C-08 bagi
`src/llm/`, dan alasannya sejenis: **satu tempat yang tahu versi mesin dan
sidik berkas model.**

Keluaran OCR tanpa keterangan versinya tidak dapat diulang, dan korpus yang
tidak dapat diulang membatalkan klaim reproduktibilitas pada naskah (NFR-15,
C-09). Bila `pytesseract` boleh diimpor di mana saja, pencatatan versi
bergantung pada ingatan penulis kode — dan ingatan bukan kendali.

**Berkas sah yang hilang menjadi temuan.** Itu kegagalan diam yang paling
mungkin: satu berkas berpindah nama, tidak ada lagi yang mengimpor apa pun,
dan pemeriksa melapor bersih karena memang tidak menemukan pelanggaran.
Bentuk yang sama dengan pemeriksa C-03 yang menuntut berkas kredensial baku
ada.

Dibangun **sesudah** modul yang diperiksanya, kebalikan dari urutan biasa.
Pemeriksa impor tunggal yang dipasang sebelum ada yang mengimpor akan lulus
karena tidak memeriksa apa pun — pelajaran T-7 fitur 014, dan `tasks.md`
fitur ini menetapkan urutannya lebih dulu justru karena itu.
"""

from __future__ import annotations

from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python, impor_pada

PUSTAKA = "pytesseract"

MODUL_SAH = "src/ingest/ekstraksi/ocr.py"
"""Satu-satunya berkas yang boleh mengimpornya.

Ditulis sebagai jalur, bukan sebagai nama direktori: kelonggaran setingkat
direktori akan membuat berkas kedua di dalamnya lolos tanpa keputusan siapa
pun.
"""


def periksa_impor_ocr(akar: Path) -> list[Temuan]:
    """`pytesseract` hanya boleh diimpor pada `MODUL_SAH`."""
    cabang = akar / "src"
    if not cabang.is_dir():
        return []

    temuan: list[Temuan] = []
    sah = akar / MODUL_SAH
    if not sah.is_file():
        temuan.append(
            Temuan(
                sah,
                0,
                f"modul yang berhak mengimpor {PUSTAKA!r} tidak ditemukan — "
                "pemeriksa yang kehilangan bahannya melapor bersih tanpa "
                "memeriksa apa pun (R-05, C-09)",
            )
        )

    for berkas in berkas_python(cabang):
        if berkas == sah:
            continue
        for impor in impor_pada(berkas):
            if impor.modul == PUSTAKA:
                temuan.append(
                    Temuan(
                        berkas,
                        impor.baris,
                        f"{PUSTAKA!r} diimpor di luar {MODUL_SAH} — keluaran OCR "
                        "dari sini tidak akan tercatat versinya, dan korpus yang "
                        "tidak dapat diulang membatalkan NFR-15",
                    )
                )
    return temuan
