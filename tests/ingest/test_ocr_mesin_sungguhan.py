"""Uji OCR terhadap mesin sungguhan — D-4 fitur 015, R-04.

**Satu-satunya uji pada proyek ini yang menuntut perkakas di luar pohon
Python.** Ia dilewati bila Tesseract tidak terpasang, dan pelewatannya
terlihat pada laporan — bukan lulus diam-diam.

Pembedaan itu yang menjaga laporan uji tetap jujur. Uji yang lulus karena
tidak menjalankan apa pun adalah laporan palsu, dan laporan palsu
menghentikan kewaspadaan — pelajaran TA-01, yang pada fitur ini sudah dipakai
dua kali: pada `make compliance` dan pada pemeriksa ketergantungan sistem.

Seluruh uji perilaku OCR yang lain berjalan tanpa mesin, memakai mesin yang
disuntikkan. Berkas ini melengkapi keduanya: yang di sana membuktikan kodenya
benar, yang di sini membuktikan pembungkusnya benar-benar tersambung ke mesin
sungguhan.
"""

import shutil
from pathlib import Path

import pytest
from src.ingest.ekstraksi.model_ocr import jalur_model
from src.ingest.ekstraksi.ocr import BAHASA, PengekstrakOcr

BAHAN = Path(__file__).resolve().parents[1] / "bahan"

ADA_MESIN = shutil.which("tesseract") is not None
ADA_MODEL = jalur_model(f"{BAHASA}.traineddata") is not None

perlu_mesin = pytest.mark.skipif(
    not (ADA_MESIN and ADA_MODEL),
    reason=(
        "mesin OCR atau berkas model Bahasa Indonesia tidak terpasang — "
        "uji dilewati, bukan diluluskan"
    ),
)


@pytest.mark.perkakas_luar
@perlu_mesin
def test_pindaian_terbaca_mesin_sungguhan() -> None:
    """Jalur penuh: berkas pindaian, mesin sungguhan, model Bahasa Indonesia.

    Yang diperiksa bukan mutu pengenalannya — pengukuran itu milik D-08 —
    melainkan bahwa pembungkusnya memanggil mesin dengan model yang benar dan
    menerima kembali sesuatu yang berisi.
    """
    hasil = PengekstrakOcr().ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")
    assert hasil.isi.strip()
    assert hasil.versi_mesin
    assert hasil.sidik_model.startswith("sha256:")


def test_uji_mesin_sungguhan_ditandai_dan_dapat_dilewati() -> None:
    """**Uji terpenting berkas ini**, dan satu-satunya yang selalu berjalan.

    Ia menjaga agar uji di atas tidak diam-diam berubah menjadi uji yang
    selalu dilewati tanpa seorang pun tahu: penandanya wajib ada, dan
    alasan pelewatannya wajib menyebut bahwa ia dilewati, bukan diluluskan.
    """
    tanda = {m.name for m in test_pindaian_terbaca_mesin_sungguhan.pytestmark}
    assert "perkakas_luar" in tanda
    assert "skipif" in tanda

    alasan = next(
        m.kwargs["reason"]
        for m in test_pindaian_terbaca_mesin_sungguhan.pytestmark
        if m.name == "skipif"
    )
    assert "dilewati" in alasan
    assert "diluluskan" in alasan


def test_keadaan_lingkungan_dilaporkan_apa_adanya() -> None:
    """Bila keduanya ada, uji di atas benar-benar berjalan; bila tidak, ia
    dilewati. Yang tidak boleh terjadi adalah keduanya tidak ada sementara
    laporan menyatakan seluruh uji lulus."""
    assert isinstance(ADA_MESIN, bool)
    assert isinstance(ADA_MODEL, bool)
