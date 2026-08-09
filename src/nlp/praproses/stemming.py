"""Stemming dan stop-word Bahasa Indonesia — R-07, R-08, C-10, FR-B03.

Satu aturan menaungi seluruh modul, dan ia kelanjutan langsung dari
`tokenisasi`:

**stemming mengubah `stem`, tidak pernah `permukaan`, `mulai`, maupun
`akhir`.**

Di sinilah C-10 paling mudah runtuh. "menugaskan" menjadi "tugas" — lima
karakter lebih pendek — dan versi yang menuliskan hasil stem kembali ke
permukaan akan membuat setiap rentang sesudahnya menunjuk kata yang salah
tanpa satu galat pun. Token baru karena itu dibentuk dengan rentang lama,
bukan dihitung ulang.

**Stop-word dibuang sebagai token, bukan dipotong dari teks.** Teks kanonik
tidak berubah sama sekali; yang berkurang adalah daftar tokennya. Karena itu
rentang token yang tersisa tetap sah, dan itu perbedaan yang menentukan
antara modul ini dan praproses yang lazim ditulis untuk pencarian.

**Daftar stop-word bawaan disaring.** Daftar Sastrawi disusun untuk teks umum
Bahasa Indonesia, dan sebagian isinya adalah kata yang justru menjadi inti
kategori D-03. Pengambilan yang kehilangan kata "kepala" tidak dapat menemukan
dokumen tentang kepala sekolah, dan kehilangan itu tidak akan terlihat sebagai
galat — hanya sebagai hasil pencarian yang sepi.

Kegunaan keluaran modul ini dibatasi tegas: **untuk pencarian, bukan untuk
menyiapkan bahan anotasi.** Bahan anotasi diambil dari teks kanonik dengan
rentang karakter (D-03 Bagian 15).
"""

from __future__ import annotations

from functools import lru_cache

from src.nlp.praproses.token import Token

KATA_DILINDUNGI = frozenset(
    {
        "kepala",
        "sekolah",
        "guru",
        "siswa",
        "murid",
        "anggaran",
        "supervisi",
        "mutu",
        "program",
        "kurikulum",
        "rapat",
        "laporan",
        "dana",
    }
)
"""Kata yang tidak boleh menjadi stop-word meski daftar bawaan memuatnya.

Disusun dari kategori D-03 dan skema label FR-C04. Bukan hasil kalibrasi;
penyetelannya mengikuti BT-29 (C-16).
"""


@lru_cache(maxsize=1)
def _pemenggal() -> object:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

    return StemmerFactory().create_stemmer()


@lru_cache(maxsize=1)
def _stop_word_bawaan() -> frozenset[str]:
    from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

    return frozenset(StopWordRemoverFactory().get_stop_words())


def _susun_stop_word() -> frozenset[str]:
    return _stop_word_bawaan() - KATA_DILINDUNGI


STOP_WORD: frozenset[str] = _susun_stop_word()
"""Daftar yang berlaku: bawaan Sastrawi dikurangi kata yang dilindungi."""


def stemkan(token: list[Token]) -> list[Token]:
    """Isi `stem` tiap token dengan bentuk dasarnya.

    Rentang dan permukaan **disalin apa adanya**, tidak dihitung ulang. Yang
    dihitung ulang akan berbeda begitu stemnya berbeda panjang, dan itu persis
    kegagalan yang C-10 larang.

    Stem kosong tidak pernah dituliskan: pemenggal yang mengembalikan untai
    kosong pada kata tertentu akan membuat `Token` gagal dibentuk dan seluruh
    dokumen ikut gagal. Pada keadaan itu permukaan ternormalkan yang dipakai.
    """
    pemenggal = _pemenggal()
    hasil: list[Token] = []
    for t in token:
        dasar = pemenggal.stem(t.stem) or t.stem  # type: ignore[attr-defined]
        hasil.append(Token(permukaan=t.permukaan, stem=dasar, mulai=t.mulai, akhir=t.akhir))
    return hasil


def tanpa_stop_word(token: list[Token]) -> list[Token]:
    """Buang token yang stemnya termasuk stop-word.

    Yang dibuang tokennya, bukan karakternya. Token stop-word yang dikosongkan
    alih-alih dibuang tetap menempati rentangnya, sehingga ia muncul sebagai
    kata kosong pada setiap pemakaian berikutnya.
    """
    return [t for t in token if t.stem not in STOP_WORD and t.permukaan.lower() not in STOP_WORD]
