"""Pengekstrak OCR — R-04, R-05, R-06, FR-B02, C-08, C-09.

**Satu-satunya tempat `pytesseract` diimpor.** Alasannya sama dengan C-08 bagi
`src/llm/`: modul ini yang mengetahui versi mesin dan sidik berkas model, dan
impor di tempat lain akan menghasilkan keluaran OCR yang tidak tercatat
versinya. Hasil OCR tanpa versi tidak dapat diulang, dan korpus yang tidak
dapat diulang membatalkan klaim reproduktibilitas pada naskah (NFR-15).
Pemeriksa D-2 yang menegakkannya.

**Mesin disuntikkan sebagai parameter.** Itu yang membuat seluruh uji perilaku
berjalan tanpa Tesseract terpasang. Uji yang menuntut perkakas luar adalah uji
yang kelak dilewati orang, dan uji yang dilewati tidak menjaga apa pun.

**Kegagalan mesin menahan, tidak pernah meloloskan** (R-06). Mesin OCR yang
hilang adalah keadaan yang paling mungkin terjadi pada penyebaran — ia paket
sistem yang dipasang terpisah dari paket Python — dan kegagalan diam di sana
menghasilkan korpus berisi dokumen pindaian tanpa teks yang tak seorang pun
sadari. Setiap bentuk kegagalan berakhir sebagai `GalatEkstraksi`, termasuk
yang tidak terduga.

**Versi mesin dan sidik model dibawa keluar pada hasilnya**, bukan dicatat
diam-diam di dalam. Pemanggil yang menjejakkannya ke `logbook/` memerlukan
keduanya, dan modul ini bukan penulis logbook — memisahkannya menjaga
`src/logbook/` tetap satu-satunya penulis (C-09).

Batas yang dinyatakan terbuka: **mutu OCR atas dokumen manajerial sekolah
Indonesia belum diukur.** Tidak ada angka pada modul ini yang menyatakannya
memadai; pengukurannya milik prosedur uji D-08, dan ambang kepercayaannya
milik kalibrasi BT-29 (C-16).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.ingest.ekstraksi.dasar import Pengekstrak, TeksKanonik
from src.ingest.ekstraksi.galat import PESAN, GalatEkstraksi
from src.ingest.ekstraksi.model_ocr import sidik_model

NAMA = "ocr"

SUFIKS = frozenset({".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"})
"""FR-B01 menyebut "gambar hasil pindai" di samping PDF, sehingga keduanya
ditangani pengekstrak yang sama."""

BAHASA = "ind"
"""Berkas model Bahasa Indonesia. Bukan setelan yang boleh diubah pemanggil:
mesin yang dijalankan dengan model bahasa lain menghasilkan teks yang tetap
terbaca seperti teks, dan tidak ada yang menyadarinya dari hasilnya saja
(KB-018)."""


@dataclass(frozen=True)
class HasilMesin:
    """Keluaran mentah mesin OCR beserta keterangan versinya.

    Ketiganya datang bersama karena ketiganya lahir dari satu pemanggilan.
    Memisahkan versinya menjadi pemanggilan kedua membuka kemungkinan teks
    dari satu versi dicatat dengan versi yang lain.
    """

    teks: str
    versi_mesin: str
    sidik_model: str


class TeksPindaian(TeksKanonik):
    """`TeksKanonik` beserta keterangan yang C-09 wajibkan.

    Bukan bidang hiasan: tanpa keduanya, keluaran OCR tidak dapat diulang, dan
    yang tidak dapat diulang tidak dapat dipertanggungjawabkan pada naskah.
    """

    versi_mesin: str
    sidik_model: str


def _jalankan_tesseract(jalur: Path) -> HasilMesin:
    """Pemanggilan mesin sesungguhnya — satu-satunya tempat impornya."""
    import pytesseract

    teks = pytesseract.image_to_string(str(jalur), lang=BAHASA)
    versi = str(pytesseract.get_tesseract_version())
    return HasilMesin(teks=teks, versi_mesin=versi, sidik_model=_sidik_model_terpasang())


def _sidik_model_terpasang() -> str:
    """Sidik berkas model yang benar-benar dipakai.

    Dibaca dari lingkungan, bukan disalin dari `ketergantungan-disetujui.toml`
    — yang disalin adalah nilai yang dipercaya, dan yang perlu dicatat adalah
    nilai yang terjadi.
    """
    return sidik_model(f"{BAHASA}.traineddata") or "tidak-ditemukan"


class PengekstrakOcr(Pengekstrak):
    """Pindaian menjadi `TeksPindaian`, atau `GalatEkstraksi`."""

    def __init__(self, mesin: Callable[[Path], HasilMesin] = _jalankan_tesseract) -> None:
        self._mesin = mesin

    def menangani(self, jalur: Path) -> bool:
        return jalur.suffix.lower() in SUFIKS

    def ekstrak(self, jalur: Path) -> TeksPindaian:
        if not jalur.is_file():
            raise GalatEkstraksi(
                f"berkas tidak ditemukan: {jalur.name}",
                pesan_pengguna=PESAN["tidak_terbaca"],
            )

        try:
            hasil = self._mesin(jalur)
        except Exception as galat:
            raise GalatEkstraksi(
                f"mesin OCR gagal berjalan: {type(galat).__name__}",
                pesan_pengguna=PESAN["tidak_terbaca"],
            ) from galat

        if not hasil.teks.strip():
            raise GalatEkstraksi(
                "mesin OCR berjalan tetapi tidak menghasilkan satu kata pun",
                pesan_pengguna=PESAN["tanpa_isi"],
            )

        return TeksPindaian(
            isi=hasil.teks,
            asal=jalur.name,
            pengekstrak=NAMA,
            versi_mesin=hasil.versi_mesin,
            sidik_model=hasil.sidik_model,
        )
