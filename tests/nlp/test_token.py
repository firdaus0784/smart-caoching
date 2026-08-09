"""Uji `Token` — C-1 fitur 015, R-08, C-10.

`Token` membawa **empat** hal, bukan tiga: permukaan asli, stem, dan rentang
karakternya. Yang keempat itu yang membuat C-10 dapat ditegakkan.

Stemming mengubah panjang kata — "menugaskan" menjadi "tugas". Token yang
hanya menyimpan stem kehilangan tempatnya pada teks asli, dan setiap rentang
anotasi yang menunjuk kepadanya menjadi salah tanpa ada yang menyadarinya.
"""

import pytest
from pydantic import ValidationError
from src.nlp.praproses.token import Token


def _token() -> Token:
    return Token(permukaan="menugaskan", stem="tugas", mulai=16, akhir=26)


def test_token_beku() -> None:
    with pytest.raises(ValidationError):
        _token().stem = "lain"  # type: ignore[misc]


def test_token_tanpa_rentang_ditolak() -> None:
    """**Uji terpenting berkas ini.**

    Rentang yang boleh kosong adalah rentang yang akan dikosongkan seseorang
    ketika ia merasa tidak memerlukannya, dan C-10 runtuh pada saat itu tanpa
    satu galat pun.
    """
    with pytest.raises(ValidationError):
        Token(permukaan="menugaskan", stem="tugas")  # type: ignore[call-arg]


def test_rentang_terbalik_ditolak() -> None:
    with pytest.raises(ValidationError):
        Token(permukaan="a", stem="a", mulai=10, akhir=5)


def test_rentang_kosong_ditolak() -> None:
    """Token sepanjang nol karakter tidak menunjuk apa pun."""
    with pytest.raises(ValidationError):
        Token(permukaan="", stem="", mulai=5, akhir=5)


def test_rentang_negatif_ditolak() -> None:
    with pytest.raises(ValidationError):
        Token(permukaan="a", stem="a", mulai=-1, akhir=3)


def test_panjang_rentang_sama_dengan_panjang_permukaan() -> None:
    """Ini yang menjadikan rentangnya berarti.

    Rentang yang panjangnya berbeda dari permukaannya akan memotong kalimat
    di tempat yang salah pada setiap pemakaian berikutnya.
    """
    with pytest.raises(ValidationError):
        Token(permukaan="menugaskan", stem="tugas", mulai=0, akhir=3)


def test_permukaan_dan_stem_boleh_berbeda() -> None:
    """Justru itu gunanya: yang satu untuk menunjuk, yang lain untuk mencari."""
    t = _token()
    assert t.permukaan != t.stem
    assert t.akhir - t.mulai == len(t.permukaan)


def test_stem_tidak_menggantikan_permukaan() -> None:
    """Token tanpa `permukaan` akan memaksa pemakainya memotong teks asli
    dengan rentang lalu berharap hasilnya cocok — dan tidak ada yang
    memeriksanya."""
    assert "permukaan" in Token.model_fields
