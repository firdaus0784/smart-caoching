"""Sapuan: galat tidak boleh mengulang muatan yang ditolaknya — KM-03, R-11.

Proyek ini menolak data pribadi pada beberapa tempat, dan setiap penolakan
menghasilkan galat. **Galat yang mengutip muatannya memindahkan kebocoran dari
basis data ke log** — kebalikan persis dari maksud penjagaannya. Prinsip itu
sudah tertulis sejak `GalatJejak` fitur 002.

## Mengapa sapuan ini ada

Penjagaan yang benar tidak cukup. `ValidationError` pydantic secara bawaan
menyalin **nilai masukan** ke dalam pesannya, sehingga nomor yang baru saja
ditolak tetap muncul — lewat jalur yang bukan pesan yang kita tulis. Pesan
buatan sendiri dapat sempurna dan kebocorannya tetap terjadi.

Ditemukan 13 Agustus 2026 pada `Peristiwa` (fitur 012), lalu **cacat yang sama
ditemukan pada `ProfilSekolah`** yang ditulis beberapa jam sebelumnya pada hari
yang sama. Dua kejadian dalam satu hari cukup untuk menjadikannya aturan,
bukan perbaikan.

Sapuan ini menyatakan aturannya: **setiap model pydantic yang menolak data
pribadi wajib menyetel `hide_input_in_errors`.**
"""

import re
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]

PENANDA_PENOLAKAN = "periksa_data_pribadi"
PENANDA_KENDALI = "hide_input_in_errors"


def _modul_yang_menolak_data_pribadi() -> list[Path]:
    """Modul `src/` yang menolak data pribadi lewat validator pydantic."""
    return [
        jalur
        for jalur in sorted((AKAR / "src").rglob("*.py"))
        if PENANDA_PENOLAKAN in (isi := jalur.read_text(encoding="utf-8"))
        and "field_validator" in isi
    ]


def test_sapuan_menemukan_sesuatu() -> None:
    """Sapuan yang tidak menemukan apa pun memeriksa himpunan kosong dan lulus.

    Pelajaran TA-01 pada perkakas sapuan: nol yang terbaca seperti kelulusan.
    """
    assert _modul_yang_menolak_data_pribadi()


def test_setiap_penolak_data_pribadi_menyembunyikan_masukan() -> None:
    """**Aturannya.** Penjagaan yang benar dengan galat yang membocorkan adalah
    penjagaan yang membatalkan dirinya sendiri."""
    lalai = [
        jalur.relative_to(AKAR)
        for jalur in _modul_yang_menolak_data_pribadi()
        if PENANDA_KENDALI not in jalur.read_text(encoding="utf-8")
    ]
    assert lalai == [], (
        f"model menolak data pribadi tanpa {PENANDA_KENDALI}: {lalai} — "
        "pydantic menyalin nilai masukan ke dalam pesan galat, sehingga muatan "
        "yang ditolak tetap muncul (KM-03)"
    )


def test_kendali_menyertai_modelnya_bukan_berkasnya() -> None:
    """`hide_input_in_errors` disetel pada `model_config`, bukan disebut pada
    komentar di mana pun.

    Sapuan atas kata saja akan lulus pada berkas yang hanya menyebutkannya
    dalam uraian — dan uraian tidak menegakkan apa pun.
    """
    for jalur in _modul_yang_menolak_data_pribadi():
        isi = jalur.read_text(encoding="utf-8")
        assert re.search(rf"^\s+{PENANDA_KENDALI}=True,", isi, re.M), jalur


def test_galat_sungguhan_tidak_memuat_nomornya() -> None:
    """Uji perilaku di samping sapuan bentuk: keduanya diperlukan.

    Sapuan menutup modul yang lupa menyetelnya; uji ini menutup kemungkinan
    setelan itu tidak bekerja sebagaimana disangka.
    """
    from datetime import UTC, datetime

    import pytest
    from pydantic import ValidationError
    from src.pengguna.profil import JalurAkreditasi, ProfilSekolah
    from src.telemetri.peristiwa import JenisPeristiwa, Peristiwa

    with pytest.raises(ValidationError) as galat_profil:
        ProfilSekolah(
            id_pengguna="PGN-001",
            jabatan="Kepala Sekolah",
            masa_kerja=7,
            jumlah_rombel=12,
            jumlah_ptk=18,
            jalur_akreditasi=JalurAkreditasi.VISITASI,
            wilayah="Sumedang 081234567890",
        )
    assert "081234567890" not in str(galat_profil.value)

    with pytest.raises(ValidationError) as galat_peristiwa:
        Peristiwa(
            pseudonim="PSD-a1",
            jenis=JenisPeristiwa.QUESTION_ASKED,
            waktu=datetime(2026, 8, 13, tzinfo=UTC),
            properti={"catatan": "hubungi 081234567890"},
            versi_aplikasi="0.12.0",
            versi_model="tiruan-0",
        )
    assert "081234567890" not in str(galat_peristiwa.value)
