"""Pengekstrak DOCX — R-01, R-02, keadaan "perubahan terlacak" pada spec.

**Teks final yang diambil, bukan riwayat suntingannya.** Dokumen manajerial
sekolah beredar dengan perubahan terlacak menyala, dan yang dimaksud
penulisnya adalah keadaan sesudah suntingan diterima. Teks yang sudah dihapus
tidak pernah menjadi bagian dokumen; membawanya masuk berarti korpus memuat
kalimat yang tidak pernah disetujui siapa pun — dan pada dokumen manajerial,
kalimat yang dicabut biasanya dicabut karena keliru.

**Mengapa XML dibaca sendiri alih-alih memakai `paragraph.text`.** Bukan
karena kurang percaya pada pustakanya, melainkan karena `paragraph.text`
**bukan** teks final: ia mengumpulkan run yang berada langsung di bawah
paragraf, sedangkan run hasil sisipan dibungkus `w:ins` satu tingkat lebih
dalam. Akibatnya kata sisipan hilang tanpa tanda apa pun. Diperiksa langsung
pada bahan uji `notulen-terlacak.docx`:

    paragraph.text -> 'Jadwal supervisi disusun untuk  guru kelas, bukan delapan.'

Kata "enam" hilang, dan kalimatnya tetap terbaca wajar. Itu bentuk kegagalan
yang tidak akan disadari siapa pun dari hasilnya saja, dan karena itu ia
ditangani di sini alih-alih dipercayakan pada bawaan.

Aturannya: ambil setiap `w:t` yang **tidak berada di dalam `w:del`**. `w:t` di
dalam `w:ins` ikut terambil dengan sendirinya karena penelusuran menjangkau
seluruh kedalaman.

Yang ditolak adalah **letaknya**, bukan nama tagnya. Versi pertama modul ini
melewati `w:delText` saja, dan itu keliru: sebagian penghasil DOCX menulis
teks terhapus sebagai `w:t` biasa di dalam `w:del`. Pengekstrak semacam itu
memasukkan kalimat yang sudah dicabut, dan ujinya tetap hijau selama bahan
ujinya hanya memakai bentuk yang satu. Tertangkap pada tugas ini juga, bukan
kelak.
"""

from __future__ import annotations

from pathlib import Path

from src.ingest.ekstraksi.dasar import Pengekstrak, TeksKanonik
from src.ingest.ekstraksi.galat import GalatEkstraksi

NAMA = "docx"
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_TEKS = f"{_W}t"
_DIHAPUS = f"{_W}del"
_PARAGRAF = f"{_W}p"


class PengekstrakDocx(Pengekstrak):
    """Satu berkas DOCX menjadi satu `TeksKanonik`, atau `GalatEkstraksi`."""

    def menangani(self, jalur: Path) -> bool:
        return jalur.suffix.lower() == ".docx"

    def ekstrak(self, jalur: Path) -> TeksKanonik:
        from docx import Document
        from docx.opc.exceptions import PackageNotFoundError

        try:
            dokumen = Document(str(jalur))
        except (PackageNotFoundError, OSError, ValueError, KeyError) as galat:
            raise GalatEkstraksi(
                f"berkas DOCX tidak dapat dibuka: {type(galat).__name__}"
            ) from galat

        paragraf = [self._teks_paragraf(p) for p in dokumen.element.body.iter(_PARAGRAF)]
        isi = "\n".join(paragraf)
        if not isi.strip():
            raise GalatEkstraksi("berkas DOCX terbuka tetapi tidak memuat teks")

        return TeksKanonik(isi=isi, asal=jalur.name, pengekstrak=NAMA)

    @classmethod
    def _teks_paragraf(cls, paragraf: object) -> str:
        """Seluruh `w:t` yang tidak berada di dalam `w:del`.

        Penelusuran menjangkau seluruh kedalaman, sehingga `w:t` di dalam
        `w:ins` ikut terambil tanpa perlakuan khusus — dan itu memang yang
        diinginkan, karena sisipan adalah bagian teks final.

        `w:delText` terlewati dengan sendirinya karena tagnya bukan `w:t`;
        yang perlu ditolak tegas adalah `w:t` yang letaknya di dalam `w:del`.
        """
        return "".join(
            unsur.text or ""
            for unsur in paragraf.iter()  # type: ignore[attr-defined]
            if unsur.tag == _TEKS and not cls._di_dalam_penghapusan(unsur)
        )

    @staticmethod
    def _di_dalam_penghapusan(unsur: object) -> bool:
        """Apakah unsur berada di bawah `w:del` pada kedalaman berapa pun."""
        induk = unsur.getparent()  # type: ignore[attr-defined]
        while induk is not None:
            if induk.tag == _DIHAPUS:
                return True
            induk = induk.getparent()
        return False
