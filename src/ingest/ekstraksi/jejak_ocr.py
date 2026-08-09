"""Pencatatan keluaran OCR ke logbook — R-05, C-09, D-10 Bagian 4.

C-09 menuntut setiap keluaran mencatat versinya. Pada OCR yang wajib tercatat
bukan versi kode melainkan **versi mesin dan sidik berkas model**: keduanya
berada di luar `uv.lock`, dan keduanya menentukan isi korpus. Mesin yang
diperbarui diam-diam menghasilkan teks yang berbeda dari berkas yang sama, dan
tidak ada yang menyadarinya dari hasilnya saja.

Ditulis ke **L2**, bukan L1. L1 mencatat percobaan penelitian; keluaran OCR
adalah versi artefak — ia menerangkan bagaimana sepotong korpus terbentuk,
bukan hipotesis apa yang diuji.

**Satu baris per keluaran.** Bukan satu baris per berkas, bukan ringkasan per
kelompok. Ringkasan menghapus waktu, dan waktu yang membedakan dokumen yang
diproses sebelum mesin diganti dari yang sesudahnya — pertanyaan yang baru
muncul ketika ada yang keliru, dan pada saat itu ringkasannya sudah tertulis.

**Isi dokumen tidak pernah masuk logbook**, hanya nama berkas dan panjangnya.
Dokumen pindaian sekolah memuat data pribadi yang belum diverifikasi siapa pun
— ia masih di karantina saat OCR berjalan. Panjang karakter cukup untuk
menyadari pindaian yang hasilnya tiba-tiba jauh lebih pendek daripada
biasanya, dan itu tanda mutu OCR yang turun.

Menolak keluaran yang bukan OCR bukan kerewelan: pencatat yang menerima apa
pun akan menuliskan baris tanpa versi mesin, dan baris tanpa versi lebih buruk
daripada tidak ada baris — ia terbaca seperti catatan yang lengkap.
"""

from __future__ import annotations

from pathlib import Path

from src.ingest.ekstraksi.ocr import TeksPindaian
from src.logbook.penulis import Buku, tambah_baris


def catat_keluaran_ocr(akar_logbook: Path, hasil: TeksPindaian) -> None:
    """Satu baris L2 bagi satu keluaran OCR.

    `hasil` wajib bertipe `TeksPindaian` — tipe yang membawa versi mesin dan
    sidik model. Tipe lain ditolak, sebab kekurangannya baru terlihat berbulan
    kemudian ketika baris itu dibaca untuk menyusun bagian metode naskah.
    """
    if not isinstance(hasil, TeksPindaian):
        raise TypeError(
            "hanya keluaran OCR yang dicatat di sini; keluaran lain tidak "
            "membawa versi mesin, dan baris tanpa versi terbaca seperti "
            "catatan yang lengkap"
        )

    tambah_baris(
        akar_logbook,
        Buku.L2,
        {
            "artefak": "keluaran-ocr",
            "peristiwa": "pindaian dibaca mesin OCR",
            "asal": hasil.asal,
            "pengekstrak": hasil.pengekstrak,
            "versi_mesin": hasil.versi_mesin,
            "sidik_model": hasil.sidik_model,
            "panjang_karakter": len(hasil),
        },
    )
