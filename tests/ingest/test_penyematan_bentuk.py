"""Bentuk hasil penyematan dan versi indeks — T-3 fitur 026, K-2, KM-01.

Tanpa peladen. Yang diuji di sini bentuk dan nilai, bukan jalur.

**Versi indeks dinilai atas nilainya, bukan atas polanya.** Uji yang hanya
mencocokkan pola membuktikan pola — ia lulus juga pada penyusun yang selalu
mengembalikan tanggal yang sama. Karena itu jamnya disuntikkan, dan nilainya
dibandingkan harfiah.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from src.ingest.penyematan import HasilPenyematan, susun_versi_indeks
from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import VersiPenyemat

SAAT = datetime(2026, 9, 23, 7, 30, 0, tzinfo=UTC)
VERSI_TIRUAN = VersiPenyemat(nama_model="penyemat-tiruan", versi_model="hash-sha256-1")


# ── versi indeks — K-2 ──────────────────────────────────────────────


@pytest.mark.parametrize(
    ("tujuan", "harap"),
    [
        (IndeksTujuan.UTAMA, "utama-20260923T073000Z"),
        (IndeksTujuan.METADATA, "metadata-20260923T073000Z"),
    ],
)
def test_versi_indeks_bernilai_harfiah(tujuan: IndeksTujuan, harap: str) -> None:
    """Nilainya, bukan polanya. Jam disuntikkan sehingga hasilnya pasti."""
    assert susun_versi_indeks(tujuan, sekarang=lambda: SAAT) == harap


def test_dua_indeks_pada_saat_sama_tidak_bertabrakan() -> None:
    """Versi indeks dipakai membedakan percobaan pada D-10 L1. Dua indeks yang
    dibangun bersamaan lalu berversi sama membuat keduanya tidak terbedakan."""
    utama = susun_versi_indeks(IndeksTujuan.UTAMA, sekarang=lambda: SAAT)
    metadata = susun_versi_indeks(IndeksTujuan.METADATA, sekarang=lambda: SAAT)
    assert utama != metadata


def test_dua_pembangunan_pada_detik_berbeda_berversi_berbeda() -> None:
    """Sifat yang membuat cacah naik ditolak pada K-2: nilainya tidak pernah
    terpakai ulang."""
    kemudian = SAAT + timedelta(seconds=1)
    assert susun_versi_indeks(IndeksTujuan.UTAMA, sekarang=lambda: SAAT) != susun_versi_indeks(
        IndeksTujuan.UTAMA, sekarang=lambda: kemudian
    )


def test_waktu_berzona_lain_diubah_ke_utc() -> None:
    """**KM-01.** Waktu disimpan UTC, bukan ditolak karena zonanya lain.

    Jam 14.30 di WIB adalah 07.30 UTC, dan versinya wajib berbunyi 07.30 —
    bukan 14.30 dengan huruf `Z` di belakangnya, yang menyatakan hal yang
    tidak benar dengan bentuk yang tampak benar.
    """
    wib = datetime(2026, 9, 23, 14, 30, 0, tzinfo=timezone(timedelta(hours=7)))
    assert susun_versi_indeks(IndeksTujuan.UTAMA, sekarang=lambda: wib) == (
        "utama-20260923T073000Z"
    )


def test_waktu_tanpa_zona_ditolak() -> None:
    """Waktu tanpa zona tidak dapat diubah ke UTC tanpa menebak zonanya, dan
    tebakan itu tidak pernah terlihat pada hasilnya."""
    polos = datetime(2026, 9, 23, 7, 30, 0)
    with pytest.raises(ValueError, match="zona"):
        susun_versi_indeks(IndeksTujuan.UTAMA, sekarang=lambda: polos)


# ── HasilPenyematan ─────────────────────────────────────────────────


def _hasil(**ganti: object) -> HasilPenyematan:
    bidang: dict[str, object] = {
        "indeks_tujuan": IndeksTujuan.UTAMA,
        "versi_indeks": "utama-20260923T073000Z",
        "versi_penyemat": VERSI_TIRUAN,
        "tersemat": 3,
        "dilewati_teks_kosong": 1,
        "tersisa_tanpa_vektor": 0,
    }
    bidang.update(ganti)
    return HasilPenyematan(**bidang)  # type: ignore[arg-type]


def test_hasil_beku_dan_menolak_bidang_asing() -> None:
    hasil = _hasil()
    with pytest.raises(ValidationError):
        hasil.tersemat = 9  # type: ignore[misc]
    with pytest.raises(ValidationError):
        _hasil(bidang_asing="apa saja")


@pytest.mark.parametrize("bidang", ["tersemat", "dilewati_teks_kosong", "tersisa_tanpa_vektor"])
def test_ketiga_hitungan_tidak_boleh_negatif(bidang: str) -> None:
    with pytest.raises(ValidationError) as galat:
        _hasil(**{bidang: -1})
    assert [g["loc"] for g in galat.value.errors()] == [(bidang,)], (
        f"galat bukan tentang {bidang!r}: {[(g['type'], g['loc']) for g in galat.value.errors()]}"
    )


@pytest.mark.parametrize(
    "bidang",
    [
        "indeks_tujuan",
        "versi_indeks",
        "versi_penyemat",
        "tersemat",
        "dilewati_teks_kosong",
        "tersisa_tanpa_vektor",
    ],
)
def test_seluruh_bidang_wajib(bidang: str) -> None:
    """Sebabnya diperiksa, bukan hanya kejadiannya — pelajaran T-2 (KB-113):
    `pytest.raises` telanjang diam ketika bidangnya diberi nilai baku dan
    penjaga lain yang menyalak."""
    lengkap = _hasil().model_dump()
    del lengkap[bidang]
    with pytest.raises(ValidationError) as galat:
        HasilPenyematan(**lengkap)
    hilang = [g for g in galat.value.errors() if g["type"] == "missing"]
    assert [g["loc"] for g in hilang] == [(bidang,)], (
        f"galat bukan karena {bidang!r} hilang: "
        f"{[(g['type'], g['loc']) for g in galat.value.errors()]}"
    )


def test_ketiga_hitungan_terpisah_bukan_satu() -> None:
    """`tersemat` sendirian tidak dapat dibedakan dari indeks yang sebagian
    segmennya dilewati karena bertext kosong — dan pembedaan itu yang memberi
    tahu apakah korpusnya bermasalah atau jalurnya."""
    hasil = _hasil(tersemat=3, dilewati_teks_kosong=2, tersisa_tanpa_vektor=2)
    assert (hasil.tersemat, hasil.dilewati_teks_kosong, hasil.tersisa_tanpa_vektor) == (3, 2, 2)
