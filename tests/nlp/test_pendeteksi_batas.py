"""Uji batas pendeteksi — E-2 dan E-3 fitur 015, R-10, R-11, R-12.

Dua sifat yang tidak dapat diperiksa dari hasilnya, dan karena itu diperiksa
dari bentuk modulnya:

- **melapor, tidak memutuskan** (R-10) — pendeteksi yang juga memutuskan akan
  menggoda siapa pun melonggarkan ambangnya ketika antrean menumpuk
- **nilai yang dideteksi tidak pernah keluar** (R-11) — cacat yang paling
  mudah dibuat pada modul semacam ini, dan akibatnya kebalikan persis dari
  maksudnya

Ditambah satu yang hanya dapat dijaga tulisan: uraiannya menyatakan apa yang
**tidak** dideteksinya (R-12).
"""

import dataclasses
import logging

import pytest
import src.nlp.anonimisasi.pola as modul
from src.nlp.anonimisasi.pola import Temuan, periksa_data_pribadi

BERMUATAN = "NIK 3211019999999999 dan telepon 081299999999 pada lampiran halaman tiga."


def test_temuan_tidak_memiliki_bidang_untuk_nilainya() -> None:
    """**Uji terpenting berkas ini** — R-11.

    Bukan "nilainya tidak diisi" melainkan "tidak ada tempat untuk mengisinya".
    Bidang yang ada akan terisi seseorang, dan yang terisi akan tercetak.
    """
    assert {f.name for f in dataclasses.fields(Temuan)} == {"jenis", "mulai", "akhir"}


def test_temuan_tidak_memiliki_bidang_putusan() -> None:
    """R-10 — sengaja tanpa `lolos`, `ditolak`, maupun `skor`.

    Bentuk yang sama dengan `Temuan` pada pemeriksa pola adversarial fitur
    002, dan alasannya sama.
    """
    nama = {f.name for f in dataclasses.fields(Temuan)}
    assert not nama & {"lolos", "ditolak", "skor", "aman", "layak"}


def test_wujud_temuan_tidak_memuat_nilai_dokumen() -> None:
    """`repr` masuk ke log dengan sendirinya lewat pesan galat dan penelusuran.

    Diperiksa terhadap nilai sungguhan, bukan terhadap daftar bidang: bidang
    yang benar tetapi `__repr__` yang ditulis sendiri akan lolos uji di atas.
    """
    for t in periksa_data_pribadi(BERMUATAN):
        assert "3211019999999999" not in repr(t)
        assert "081299999999" not in repr(t)


def test_pendeteksi_tidak_menulis_ke_log(caplog: pytest.LogCaptureFixture) -> None:
    """Modul yang mencatat sendiri akan mencatat pada tingkat yang tidak
    diketahui pemanggilnya, dan nilai dokumen ikut ke sana."""
    with caplog.at_level(logging.DEBUG):
        periksa_data_pribadi(BERMUATAN)
    assert caplog.records == []


def test_modul_tidak_mengimpor_logging() -> None:
    """Dinyatakan pada bentuk modulnya, bukan hanya pada satu pemanggilan.

    Pemanggilan yang tidak mencatat hari ini dapat mencatat besok; impor yang
    tidak ada tidak dapat dipakai sama sekali.
    """
    import inspect

    sumber = inspect.getsource(modul)
    assert "import logging" not in sumber
    assert "print(" not in sumber
