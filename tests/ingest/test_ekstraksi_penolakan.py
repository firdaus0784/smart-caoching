"""Uji sifat penolakan berkas bermasalah — B-6 fitur 015, R-02.

**Tugas terpenting Fase B.** Pengekstrak yang mengembalikan untai kosong pada
berkas rusak menghasilkan dokumen yang lolos seluruh gerbang fitur 002 tanpa
satu pun berbunyi: tidak ada pola instruksi adversarial pada teks kosong, dan
tidak ada data pribadi pada teks kosong. Verifikator menerima antrean dokumen
yang tampak bersih karena memang tidak berisi apa-apa.

Dinyatakan sebagai **sifat atas seluruh pengekstrak dan seluruh bahan
bermasalah**, bukan sebagai kasus per pengekstrak. Uji per kasus akan lolos
pada pengekstrak keenam yang ditambahkan kelak tanpa seorang pun menyadari
bahwa ia tidak diperiksa.
"""

from pathlib import Path

import pytest
from src.ingest.ekstraksi.dasar import Pengekstrak, TeksKanonik
from src.ingest.ekstraksi.docx import PengekstrakDocx
from src.ingest.ekstraksi.galat import GalatEkstraksi
from src.ingest.ekstraksi.pdf import PengekstrakPdf
from src.ingest.ekstraksi.xlsx import PengekstrakXlsx

BAHAN = Path(__file__).resolve().parents[1] / "bahan"

PENGEKSTRAK: tuple[Pengekstrak, ...] = (
    PengekstrakDocx(),
    PengekstrakXlsx(),
    PengekstrakPdf(),
)
"""Seluruh pengekstrak yang ada. Yang ditambahkan kelak wajib masuk ke sini."""

BERMASALAH = (
    "rusak.pdf",
    "kosong.pdf",
    "terkunci.pdf",
    "isi-rusak.pdf",
    "kosong.docx",
    "kosong.xlsx",
    "tidak-ada-sama-sekali.pdf",
)


@pytest.mark.parametrize("pengekstrak", PENGEKSTRAK, ids=lambda p: type(p).__name__)
@pytest.mark.parametrize("nama", BERMASALAH)
def test_tidak_ada_berkas_bermasalah_yang_menghasilkan_teks(
    pengekstrak: Pengekstrak, nama: str
) -> None:
    """Setiap pasangan pengekstrak dan berkas bermasalah wajib melempar galat.

    Termasuk pasangan yang "tidak masuk akal" — `PengekstrakDocx` atas berkas
    PDF. Justru pasangan itu yang menguji bahwa pengekstrak tidak mencoba
    menebak isi berkas yang bukan urusannya.
    """
    with pytest.raises(GalatEkstraksi):
        pengekstrak.ekstrak(BAHAN / nama)


@pytest.mark.parametrize("pengekstrak", PENGEKSTRAK, ids=lambda p: type(p).__name__)
def test_hasil_yang_berhasil_tidak_pernah_hampa(pengekstrak: Pengekstrak) -> None:
    """Sisi lain sifat yang sama: yang **berhasil** wajib benar-benar berisi.

    Diperiksa atas seluruh bahan yang sah, sehingga pengekstrak yang berhasil
    tetapi menghasilkan spasi belaka tertangkap di sini walau ia tidak melempar
    apa pun.
    """
    berhasil = 0
    for jalur in sorted(BAHAN.iterdir()):
        if jalur.suffix == ".py" or not pengekstrak.menangani(jalur):
            continue
        try:
            hasil = pengekstrak.ekstrak(jalur)
        except GalatEkstraksi:
            continue
        assert isinstance(hasil, TeksKanonik)
        assert hasil.isi.strip()
        berhasil += 1
    assert berhasil, f"{type(pengekstrak).__name__} tidak berhasil atas satu bahan pun"


def test_setiap_pengekstrak_yang_ada_terdaftar_pada_uji_ini() -> None:
    """Sifat di atas hanya sekuat daftarnya.

    Pengekstrak keenam yang ditambahkan kelak dan lupa dimasukkan ke
    `PENGEKSTRAK` akan membuat seluruh uji di berkas ini lulus tanpa
    memeriksanya. Karena itu daftarnya sendiri diperiksa terhadap isi paket.
    """
    import importlib
    import pkgutil

    import src.ingest.ekstraksi as paket

    ditemukan: set[str] = set()
    for modul in pkgutil.iter_modules(paket.__path__):
        isi = importlib.import_module(f"{paket.__name__}.{modul.name}")
        for nama in dir(isi):
            nilai = getattr(isi, nama)
            if (
                isinstance(nilai, type)
                and issubclass(nilai, Pengekstrak)
                and nilai is not Pengekstrak
            ):
                ditemukan.add(nilai.__name__)

    terdaftar = {type(p).__name__ for p in PENGEKSTRAK}
    assert ditemukan == terdaftar, f"belum terdaftar: {sorted(ditemukan - terdaftar)}"
