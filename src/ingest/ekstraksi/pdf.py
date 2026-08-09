"""Pengekstrak PDF — R-01, R-02, dua keadaan PDF pada spec.

PDF satu-satunya format pada fitur ini yang punya **dua cara gagal yang harus
dibedakan tegas**:

| Keadaan | Perlakuan |
|---|---|
| Berkas tidak dapat dibaca — rusak, kosong, terkunci | dokumen ditolak |
| Berkas terbaca tetapi tanpa lapisan teks | **dialihkan ke OCR** |

Menyamakan keduanya berarti seluruh dokumen pindaian ditolak, dan itu
membatalkan FR-B02 sebelum ia dibangun. Membalikkannya lebih buruk: berkas
rusak yang dialihkan ke OCR menghasilkan teks acak yang masuk korpus sebagai
dokumen sah, dan tidak ada gerbang berikutnya yang dapat membedakannya dari
hasil pindaian yang buruk.

Pembedaannya dibawa **tipe galat**, bukan isi pesan. `GalatTanpaLapisanTeks`
mewarisi `GalatEkstraksi` supaya pemanggil yang belum peduli OCR tetap
menangkapnya sebagai kegagalan biasa — tanpa pewarisan itu, tipe baru akan
lolos dari setiap `except` yang sudah ada dan naik sampai menghentikan
ingesti.

**Berkas terkunci tidak dicoba dibuka.** Tidak dengan kata sandi kosong,
tidak dengan daftar tebakan. Dokumen yang pemiliknya kunci adalah dokumen
yang pemiliknya belum izinkan dibaca, dan ET-04 sudah menetapkan sikap
terhadap itu — persetujuan pemilik, bukan kemampuan teknis, yang menentukan.

**Batas pertama, ditemukan saat menguji.** Berkas PDF dengan kerangka sah
tetapi aliran isi rusak — misalnya menyatakan diri terkompresi Flate padahal
bukan — **tidak** membuat pypdf melempar galat; ia mengembalikan teks kosong.
Akibatnya berkas semacam itu tidak dapat dibedakan dari pindaian pada lapisan
ini, dan ia dialihkan ke OCR. Perilaku itu dipilih dan diuji, bukan kebetulan.
Yang menahan kerugiannya adalah jalur OCR yang juga tidak akan menghasilkan
teks dari berkas itu, sehingga dokumennya tetap tertahan — hanya lewat pintu
yang berbeda dari yang diduga.

Batas kedua: mutu ekstraksi `pypdf` atas dokumen ber-tabel
belum diukur. Bila pengukuran D-08 menyatakannya kurang, `pdfplumber` diajukan
sebagai ketergantungan baru lewat C-12 — diputuskan dari angka, bukan dari
dugaan (KB-017 pertanyaan 4).
"""

from __future__ import annotations

from pathlib import Path

from src.ingest.ekstraksi.dasar import Pengekstrak, TeksKanonik
from src.ingest.ekstraksi.galat import PESAN, GalatEkstraksi

NAMA = "pdf"


class GalatTanpaLapisanTeks(GalatEkstraksi):
    """Berkas PDF sah tetapi tidak memuat teks yang dapat diambil.

    Bukan kegagalan melainkan **pengalihan**: dokumen semacam ini adalah
    pindaian, dan jalurnya OCR (FR-B02). Tipe tersendiri supaya pemanggil
    tidak perlu membaca isi pesan untuk mengetahuinya.
    """


class PengekstrakPdf(Pengekstrak):
    """Satu berkas PDF menjadi satu `TeksKanonik`, atau salah satu dari dua galat."""

    def menangani(self, jalur: Path) -> bool:
        return jalur.suffix.lower() == ".pdf"

    def ekstrak(self, jalur: Path) -> TeksKanonik:
        from pypdf import PdfReader
        from pypdf.errors import PyPdfError

        try:
            pembaca = PdfReader(jalur)
        except (PyPdfError, OSError, ValueError) as galat:
            raise GalatEkstraksi(
                f"berkas PDF tidak dapat dibuka: {type(galat).__name__}"
            ) from galat

        if pembaca.is_encrypted:
            raise GalatEkstraksi(
                "berkas PDF terkunci kata sandi dan tidak dicoba dibuka (ET-04)",
                pesan_pengguna=PESAN["terkunci"],
            )

        try:
            halaman = [h.extract_text() or "" for h in pembaca.pages]
        except (PyPdfError, OSError, ValueError) as galat:
            raise GalatEkstraksi(f"isi PDF tidak dapat diurai: {type(galat).__name__}") from galat

        isi = "\n".join(halaman)
        if not isi.strip():
            raise GalatTanpaLapisanTeks(
                "PDF terbaca tanpa lapisan teks — dialihkan ke OCR (FR-B02)",
                pesan_pengguna=PESAN["perlu_pindaian"],
            )

        return TeksKanonik(isi=isi, asal=jalur.name, pengekstrak=NAMA)
