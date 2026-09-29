"""Uji giliran percakapan — C-1 fitur 021, R-13, R-14, FR-F09; fitur 028 T-6.

## Yang diuji bukan bahwa riwayat dapat mencatat

Yang diuji: giliran **tidak menyimpan** salinan tanggapan, dan **tidak
dapat** memuat pertanyaan bermuatan data pribadi.

Yang pertama adalah keputusan yang paling mudah dibalik dan paling mahal bila
dibalik: tanggapan yang tersimpan menua, status keberlakuan sitasinya berubah
ketika regulasi sumbernya dicabut, dan riwayat yang menayangkan salinan lama
melanggar C-07 lewat pintu yang tidak dijaga siapa pun.

## Sejak fitur 028

Kelas `Percakapan` — penyimpan di memori tanpa pemilik — digantikan
`src/penyimpanan/riwayat.py`. Validasinya tinggal di sini sebagai
`giliran_sah()`, sebab `src/penyimpanan/` tidak boleh mengimpor `src/nlp/`.
Lima uji yang khusus menguji kelas lama dihapus bersama kelasnya; padanannya
di `tests/penyimpanan/test_riwayat.py` — urutan giliran, permukaan tanpa ubah
maupun hapus, penolakan tanpa menulis — dijalankan atas pelaksana memori
**dan** PostgreSQL (KB-145).
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from src.api.percakapan import GalatPercakapan, Giliran, giliran_sah

SAAT = datetime(2026, 8, 13, 3, 0, tzinfo=UTC)


def _giliran() -> Giliran:
    return giliran_sah(
        pertanyaan="Bagaimana menyusun jadwal supervisi akademik?",
        id_pesan="PSN-1",
        waktu=SAAT,
    )


# --------------------------------------------- R-13 · rujukan, bukan salinan


def test_giliran_tidak_memiliki_bidang_bagi_tanggapan() -> None:
    """**Uji terpenting berkas ini, dan ia diuji sebagai ketiadaan bidang.**

    Bidang yang ada akan terisi. Tanggapan yang tersimpan menua — status
    keberlakuan sitasinya berubah ketika regulasi sumbernya dicabut, dan fitur
    010 memang menariknya. Riwayat yang menayangkan salinan lama menayangkan
    klaim atas regulasi yang tidak berlaku, dan validator tidak pernah
    dipanggil ulang sebab tidak ada yang dianggap sedang menjawab.
    """
    assert set(Giliran.model_fields) == {"pertanyaan", "id_pesan", "waktu"}


def test_giliran_menyimpan_rujukan_pesan() -> None:
    giliran = _giliran()
    assert giliran.id_pesan == "PSN-1"
    assert giliran.pertanyaan.startswith("Bagaimana")
    assert giliran.waktu == SAAT


def test_bidang_tambahan_ditolak() -> None:
    """`extra="forbid"`. Bidang `tanggapan` yang ditambahkan seseorang kelak
    akan lolos diam-diam tanpa ini, dan tidak satu uji perilaku pun gagal."""
    with pytest.raises(ValidationError):
        Giliran(
            pertanyaan="Bagaimana menyusun jadwal supervisi?",
            id_pesan="PSN-1",
            waktu=SAAT,
            tanggapan="tersalin",  # type: ignore[call-arg]
        )


def test_giliran_beku() -> None:
    giliran = _giliran()
    with pytest.raises(ValidationError):
        giliran.id_pesan = "PSN-9"  # type: ignore[misc]


# ------------------------------------------------------------- KM-03 · penjagaan


@pytest.mark.parametrize(
    "pertanyaan",
    [
        "Bagaimana melapor untuk NIK 3273010101800001?",
        "Nomor saya 081234567890, tolong dihubungi.",
    ],
)
def test_pertanyaan_bermuatan_data_pribadi_ditolak(pertanyaan: str) -> None:
    """**Tolak, jangan saring.** Menyaring diam-diam menghasilkan baris yang
    tampak bersih sementara penulisnya tidak pernah tahu ia hampir membocorkan
    sesuatu, dan ia akan menulisnya lagi."""
    with pytest.raises(GalatPercakapan):
        giliran_sah(pertanyaan=pertanyaan, id_pesan="PSN-1", waktu=SAAT)


def test_galat_tidak_mengulang_muatan_yang_ditolaknya() -> None:
    """Galat yang mengutip pertanyaannya memindahkan kebocoran dari riwayat ke
    log — kebalikan persis dari maksudnya. Ditemukan pada fitur 012 sebagai
    kebocoran lewat `ValidationError` pydantic, bukan lewat pesan buatan
    sendiri (KB-049)."""
    with pytest.raises(GalatPercakapan) as galat:
        giliran_sah(pertanyaan="Nomor saya 081234567890.", id_pesan="PSN-1", waktu=SAAT)
    assert "081234567890" not in str(galat.value)
    assert "telepon" in str(galat.value)
    assert galat.value.__cause__ is None, "rantai sebab pydantic diputus"


# ------------------------------------------------------------------- bentuk lain


def test_waktu_wajib_berzona_utc() -> None:
    """Waktu tanpa zona tidak dapat dibandingkan dengan waktu berzona, dan
    perbandingan itu yang menyusun urutan giliran."""
    with pytest.raises(GalatPercakapan) as galat:
        giliran_sah(
            pertanyaan="Bagaimana menyusun jadwal supervisi?",
            id_pesan="PSN-1",
            waktu=datetime(2026, 8, 13, 3, 0),
        )
    assert "UTC" in str(galat.value)


def test_pertanyaan_kosong_ditolak_dengan_pesan_yang_menyebut_sebabnya() -> None:
    """Penolakan bentuk **wajib** menyebut apa yang kurang — berbeda dari
    penolakan KM-03, yang tidak boleh membawa keterangan apa pun. Pesan yang
    tidak menyebutnya membuat pemanggil menebak."""
    with pytest.raises(GalatPercakapan) as galat:
        giliran_sah(pertanyaan="", id_pesan="PSN-1", waktu=SAAT)
    assert "tidak lengkap" in str(galat.value)


def test_giliran_tanpa_id_pengguna() -> None:
    """Sama dengan `Peristiwa` fitur 012: yang tidak ada tidak dapat terisi.
    Pemilik percakapan tinggal pada `riwayat.percakapan` sebagai pseudonim,
    bukan pada giliran (C-05)."""
    assert "id_pengguna" not in Giliran.model_fields
