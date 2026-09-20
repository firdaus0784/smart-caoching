"""Antarmuka penyemat dan tiruannya — T-3 fitur 019, R-02, R-06, R-08.

## Mengapa penyemat tinggal di `src/llm/`

Bukan pilihan rancangan. `periksa_impor_penyedia` menyenaraikan `torch`,
`transformers`, dan `sentence_transformers` sebagai pustaka model yang **hanya
boleh diimpor di dalam `src/llm/`** — C-08, tanpa pengecualian. Adaptor
sungguhan yang kelak memakainya karena itu tidak punya rumah lain, dan
antarmukanya tinggal bersamanya.

## Tiruan yang menyatakan dirinya tiruan

`PenyematTiruan` **bukan** penyemat sungguhan yang disederhanakan. Ia
memetakan teks ke vektor tetap lewat fungsi hash, dan `versi` yang
dikeluarkannya berbunyi demikian.

Pembedaan itu yang paling perlu dijaga. Penyemat buatan sendiri yang "mirip
semantik" menghasilkan angka kemiripan yang tidak berarti apa-apa sambil
terbaca seperti berfungsi — dan angka semacam itu akan masuk catatan
percobaan, lalu masuk naskah.

## Yang sengaja tidak diuji di sini

Mutu penyematannya. Vektor dari fungsi hash tidak memiliki mutu semantik untuk
diukur, dan uji yang berpura-pura mengukurnya akan lulus tanpa membuktikan
apa pun. Mutu sesungguhnya diukur pada kalibrasi gold set — fitur 025.
"""

from __future__ import annotations

import pytest
from src.llm.sematan import DIMENSI_TIRUAN, Penyemat, PenyematTiruan
from tests.konftes_asinkron import jalankan


def _penyemat(dimensi: int = DIMENSI_TIRUAN) -> PenyematTiruan:
    return PenyematTiruan(dimensi=dimensi)


# ── bentuk keluaran ──────────────────────────────────────────────────


def test_satu_vektor_per_teks() -> None:
    hasil = jalankan(_penyemat().sematkan(["kepala sekolah", "RKAS", "supervisi"]))
    assert len(hasil) == 3


def test_setiap_vektor_berdimensi_sama_dengan_yang_dinyatakan() -> None:
    """R-08. Dimensi yang dinyatakan berbeda dari dimensi yang dihasilkan
    membuat ketidakcocokan kolom baru terlihat pada kueri pertama."""
    penyemat = _penyemat()
    for vektor in jalankan(penyemat.sematkan(["a", "bb", "ccc"])):
        assert len(vektor) == penyemat.dimensi


def test_daftar_kosong_menghasilkan_daftar_kosong() -> None:
    assert list(jalankan(_penyemat().sematkan([]))) == []


def test_teks_kosong_ditolak() -> None:
    """Teks kosong yang disematkan menghasilkan vektor yang tetap dekat dengan
    segala sesuatu, dan kedekatan itu dihitung sebagai bukti."""
    with pytest.raises(ValueError):
        jalankan(_penyemat().sematkan(["   "]))


# ── determinisme ─────────────────────────────────────────────────────


def test_teks_sama_menghasilkan_vektor_sama() -> None:
    """Tanpa ini, indeks yang dibangun ulang tidak dapat dibandingkan dengan
    indeks sebelumnya, dan percobaan pada catatan D-10 L1 tidak dapat
    diulang siapa pun."""
    pertama = jalankan(_penyemat().sematkan(["kepala sekolah"]))
    kedua = jalankan(_penyemat().sematkan(["kepala sekolah"]))
    assert list(pertama[0]) == list(kedua[0])


def test_teks_berbeda_menghasilkan_vektor_berbeda() -> None:
    """Penjaga atas uji di atasnya: penyemat yang mengembalikan vektor tetap
    untuk segala masukan juga lulus uji determinisme."""
    hasil = jalankan(_penyemat().sematkan(["kepala sekolah", "anggaran BOS"]))
    assert list(hasil[0]) != list(hasil[1])


def test_urutan_masukan_dipertahankan() -> None:
    teks = ["satu", "dua", "tiga"]
    lurus = jalankan(_penyemat().sematkan(teks))
    terbalik = jalankan(_penyemat().sematkan(list(reversed(teks))))
    assert list(lurus[0]) == list(terbalik[2])


# ── C-09 · versi menyatakan dirinya ──────────────────────────────────


def test_versi_menyatakan_dirinya_tiruan() -> None:
    """**Uji terpenting berkas ini.**

    Angka kemiripan dari fungsi hash tidak berarti apa-apa. Yang mencegahnya
    masuk catatan percobaan sebagai hasil sungguhan adalah penanda versinya —
    dan penanda itu wajib terbaca, bukan tersirat.
    """
    assert "tiruan" in _penyemat().versi.nama_model.lower()


def test_versi_membawa_nama_dan_versi_model() -> None:
    """C-09: setiap keluaran percobaan mencatat versi model."""
    versi = _penyemat().versi
    assert versi.nama_model.strip()
    assert versi.versi_model.strip()


# ── R-08 · dimensi dicocokkan saat penyusunan ────────────────────────


@pytest.mark.parametrize("dimensi", [0, -1])
def test_dimensi_tidak_masuk_akal_ditolak_saat_penyusunan(dimensi: int) -> None:
    """Bukan saat kueri pertama, ketika pemanggilnya sudah di lingkungan
    sungguhan."""
    with pytest.raises(ValueError):
        _penyemat(dimensi)


def test_dimensi_yang_diminta_dipatuhi() -> None:
    penyemat = _penyemat(8)
    assert penyemat.dimensi == 8
    assert len(jalankan(penyemat.sematkan(["a"]))[0]) == 8


# ── kontrak abstrak ──────────────────────────────────────────────────


def test_penyemat_abstrak_tidak_dapat_disusun() -> None:
    with pytest.raises(TypeError):
        Penyemat()  # type: ignore[abstract]


def test_tiruan_memenuhi_kontrak() -> None:
    assert isinstance(_penyemat(), Penyemat)
