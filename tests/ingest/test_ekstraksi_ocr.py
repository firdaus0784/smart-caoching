"""Uji pengekstrak OCR — D-1 fitur 015, R-04, R-06.

Seluruh uji perilaku di sini berjalan **tanpa Tesseract terpasang**. Mesinnya
disuntikkan sebagai parameter, sehingga ujinya tidak menuntut perkakas luar —
uji yang menuntut perkakas luar adalah uji yang kelak dilewati orang, dan uji
yang dilewati tidak menjaga apa pun.

Keadaan "mesin OCR tidak terpasang" pada `spec.md` justru keadaan bawaan
lingkungan uji ini, sehingga ia diuji tanpa persiapan apa pun.
"""

from pathlib import Path

import pytest
from src.ingest.ekstraksi.dasar import TeksKanonik
from src.ingest.ekstraksi.galat import GalatEkstraksi
from src.ingest.ekstraksi.ocr import HasilMesin, PengekstrakOcr

BAHAN = Path(__file__).resolve().parents[1] / "bahan"

TEKS_PINDAIAN = "Notulen Rapat Pleno\nSDN Sukamaju\nKepala sekolah memimpin rapat."


def _mesin_baik(_: Path) -> HasilMesin:
    return HasilMesin(teks=TEKS_PINDAIAN, versi_mesin="5.3.4", sidik_model="sha256:abc")


def test_pindaian_menghasilkan_teks_kanonik() -> None:
    hasil = PengekstrakOcr(mesin=_mesin_baik).ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")
    assert isinstance(hasil, TeksKanonik)
    assert "Sukamaju" in hasil.isi


def test_mesin_tidak_terpasang_gagal_tegas_bukan_teks_kosong() -> None:
    """**Uji terpenting berkas ini** — R-06.

    Mesin OCR yang hilang adalah keadaan yang paling mungkin terjadi pada
    penyebaran. Kegagalan diam di sana menghasilkan korpus berisi dokumen
    pindaian tanpa teks yang tak seorang pun sadari.
    """

    def _tidak_terpasang(_: Path) -> HasilMesin:
        raise FileNotFoundError("tesseract")

    with pytest.raises(GalatEkstraksi):
        PengekstrakOcr(mesin=_tidak_terpasang).ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")


def test_mesin_yang_gagal_menahan_bukan_meloloskan() -> None:
    """R-06 — kegagalan mesin apa pun bentuknya berakhir sebagai penolakan."""

    def _gagal(_: Path) -> HasilMesin:
        raise RuntimeError("mesin berhenti di tengah jalan")

    with pytest.raises(GalatEkstraksi):
        PengekstrakOcr(mesin=_gagal).ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")


def test_hasil_kosong_ditolak() -> None:
    """Pindaian yang tidak menghasilkan satu kata pun adalah pindaian yang
    gagal dibaca, bukan dokumen kosong yang sah."""

    def _hampa(_: Path) -> HasilMesin:
        return HasilMesin(teks="   \n ", versi_mesin="5.3.4", sidik_model="sha256:abc")

    with pytest.raises(GalatEkstraksi):
        PengekstrakOcr(mesin=_hampa).ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")


def test_berkas_tidak_ada_ditolak_sebelum_mesin_dipanggil() -> None:
    """Memanggil mesin atas berkas yang tidak ada membuang waktu dan
    menghasilkan pesan galat dari pustaka, bukan dari kita."""
    dipanggil = False

    def _catat(_: Path) -> HasilMesin:
        nonlocal dipanggil
        dipanggil = True
        return _mesin_baik(_)

    with pytest.raises(GalatEkstraksi):
        PengekstrakOcr(mesin=_catat).ekstrak(BAHAN / "tidak-ada.pdf")
    assert not dipanggil


def test_menangani_pdf_dan_gambar() -> None:
    """FR-B01 menyebut "gambar hasil pindai" di samping PDF."""
    pengekstrak = PengekstrakOcr(mesin=_mesin_baik)
    for nama in ("a.pdf", "a.png", "a.jpg", "a.jpeg", "a.tif", "a.tiff", "a.PNG"):
        assert pengekstrak.menangani(Path(nama)), nama
    for nama in ("a.docx", "a.xlsx", "a.txt"):
        assert not pengekstrak.menangani(Path(nama)), nama


def test_asal_dan_pengekstrak_terisi() -> None:
    hasil = PengekstrakOcr(mesin=_mesin_baik).ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")
    assert hasil.asal == "pindaian-tanpa-teks.pdf"
    assert hasil.pengekstrak


def test_versi_mesin_dan_sidik_model_dibawa_keluar() -> None:
    """C-09 — tanpa keduanya, hasil OCR tidak dapat diulang siapa pun.

    Dibawa pada hasilnya, bukan dicatat diam-diam di dalam: pemanggil yang
    hendak menjejakkannya ke `logbook/` memerlukannya, dan modul ini bukan
    penulis logbook.
    """
    hasil = PengekstrakOcr(mesin=_mesin_baik).ekstrak(BAHAN / "pindaian-tanpa-teks.pdf")
    assert hasil.versi_mesin == "5.3.4"
    assert hasil.sidik_model == "sha256:abc"


def test_pencarian_berkas_model_tidak_menebak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`jalur_model` mengembalikan `None` bila berkasnya tidak ada.

    Pemeriksa yang menebak isi berkas yang tidak dapat dibacanya bukan
    pemeriksa, dan sidik yang dikarang lebih buruk daripada sidik yang kosong.
    """
    from src.ingest.ekstraksi.model_ocr import jalur_model, sidik_model

    monkeypatch.setenv("TESSDATA_PREFIX", str(tmp_path))
    assert jalur_model("tidak-ada.traineddata") is None
    assert sidik_model("tidak-ada.traineddata") is None


def test_sidik_berkas_model_dihitung_dari_isinya(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sidik dibaca dari lingkungan, bukan disalin dari catatan persetujuan.

    Yang disalin adalah nilai yang dipercaya; yang perlu dicatat adalah nilai
    yang terjadi. Keduanya berbeda persis ketika ada yang keliru.
    """
    import hashlib

    from src.ingest.ekstraksi.model_ocr import sidik_model

    (tmp_path / "ind.traineddata").write_bytes(b"model-uji")
    monkeypatch.setenv("TESSDATA_PREFIX", str(tmp_path))
    assert sidik_model("ind.traineddata") == "sha256:" + hashlib.sha256(b"model-uji").hexdigest()


def test_tessdata_prefix_didahulukan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mesinnya sendiri membaca `TESSDATA_PREFIX`.

    Pemeriksa yang melihat tempat lain daripada yang dipakai mesin akan
    melaporkan sidik berkas yang tidak pernah dipakai siapa pun.
    """
    from src.ingest.ekstraksi.model_ocr import jalur_model

    dalam = tmp_path / "tessdata"
    dalam.mkdir()
    (dalam / "ind.traineddata").write_bytes(b"x")
    monkeypatch.setenv("TESSDATA_PREFIX", str(tmp_path))
    assert jalur_model("ind.traineddata") == dalam / "ind.traineddata"


def test_pemanggilan_mesin_sungguhan_disuntik(monkeypatch: pytest.MonkeyPatch) -> None:
    """Jalur mesin sungguhan tetap diuji meski Tesseract tidak terpasang.

    Yang diperiksa bukan mutu OCR-nya melainkan bahwa ketiga keterangan —
    teks, versi mesin, sidik model — benar-benar dirakit dari satu pemanggilan
    dan tidak ada yang tertinggal kosong (C-09).
    """
    import sys
    import types

    palsu = types.ModuleType("pytesseract")
    palsu.image_to_string = lambda _jalur, lang: f"teks {lang}"  # type: ignore[attr-defined]
    palsu.get_tesseract_version = lambda: "5.3.4"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pytesseract", palsu)

    from src.ingest.ekstraksi.ocr import _jalankan_tesseract

    hasil = _jalankan_tesseract(BAHAN / "pindaian-tanpa-teks.pdf")
    assert hasil.teks == "teks ind"
    assert hasil.versi_mesin == "5.3.4"
    assert hasil.sidik_model


def test_sidik_model_tidak_ditemukan_dinyatakan_bukan_dikosongkan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Sidik yang tidak ditemukan dicatat sebagai "tidak-ditemukan", bukan
    sebagai untai kosong.

    Untai kosong pada catatan versi terbaca seperti bidang yang lupa diisi;
    yang dituju adalah pembaca yang tahu bahwa berkasnya memang tidak ada.
    """
    from src.ingest.ekstraksi.ocr import _sidik_model_terpasang

    monkeypatch.setenv("TESSDATA_PREFIX", str(tmp_path))
    monkeypatch.setattr("src.ingest.ekstraksi.model_ocr.TEMPAT_BAKU", ())
    assert _sidik_model_terpasang() == "tidak-ditemukan"


def test_berkas_model_tak_terbaca_diperlakukan_sebagai_tidak_ada(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Izin baca yang ditolak bukan alasan menebak isinya."""
    from src.ingest.ekstraksi import model_ocr

    def _menolak(self: Path) -> bool:
        raise OSError("izin ditolak")

    monkeypatch.setenv("TESSDATA_PREFIX", str(tmp_path))
    monkeypatch.setattr(Path, "is_file", _menolak)
    assert model_ocr.jalur_model("ind.traineddata") is None


def test_berkas_model_gagal_dibaca_menghasilkan_sidik_kosong(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Berkas ada tetapi tidak dapat dibaca — berbeda dari berkas yang tidak
    ada, dan keduanya sama-sama tidak boleh menghasilkan sidik yang dikarang."""
    from src.ingest.ekstraksi import model_ocr

    berkas = tmp_path / "ind.traineddata"
    berkas.write_bytes(b"x")
    monkeypatch.setenv("TESSDATA_PREFIX", str(tmp_path))

    def _menolak(self: Path) -> bytes:
        raise OSError("izin ditolak")

    monkeypatch.setattr(Path, "read_bytes", _menolak)
    assert model_ocr.sidik_model("ind.traineddata") is None
