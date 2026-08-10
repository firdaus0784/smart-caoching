"""Uji penguraian bentuk ekspor Label Studio — A-1 fitur 016, R-02.

**Diuji terhadap berkas sungguhan, dan bentuk rusaknya dibuat dengan merusak
salinannya.** Menyusun bentuk rusak dari nol berarti menguji terhadap dugaan
penulisnya — kekeliruan yang KB-021 tolak dengan dua contoh dari fitur 015.

Yang dijaga di sini satu sifat: **penguraian tidak pernah sebagian.** Label
Studio dapat naik versi tanpa kita, dan penguraian yang toleran menghasilkan
korpus yang sebagian bidangnya hilang tanpa satu galat pun. Bidang yang hilang
paling mungkin bidang yang jarang terisi — yaitu bendera, dan salah satu
bendera menyatakan data pribadi lolos anonimisasi.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from src.nlp.anotasi.impor_ls import GalatBentukEkspor, urai_ekspor

BAHAN = Path(__file__).resolve().parents[1] / "bahan" / "ekspor-label-studio-1.23.json"


def _muat() -> list[dict[str, Any]]:
    isi: list[dict[str, Any]] = json.loads(BAHAN.read_text(encoding="utf-8"))
    return isi


def test_bahan_sungguhan_terurai() -> None:
    """Bila ini gagal, seluruh uji lain pada berkas ini menguji hal yang salah."""
    tugas = urai_ekspor(_muat())
    assert len(tugas) == 2


def test_tugas_membawa_teks_anotasi_dan_prediksi() -> None:
    tugas = urai_ekspor(_muat())
    pertama = tugas[0]
    assert pertama.teks
    assert len(pertama.anotasi) == 2
    assert pertama.prediksi == ()


KUNCI_TUGAS = ("id", "data", "annotations", "predictions")


@pytest.mark.parametrize("kunci", KUNCI_TUGAS)
def test_kunci_tugas_yang_hilang_menggagalkan_penguraian(kunci: str) -> None:
    """**Uji yang dituntut `tasks.md`.**

    Galatnya menyebut kunci yang hilang. Galat yang hanya berkata "bentuk tidak
    dikenali" memaksa pembacanya membandingkan dua berkas besar dengan mata.
    """
    rusak = _muat()
    del rusak[0][kunci]
    with pytest.raises(GalatBentukEkspor) as galat:
        urai_ekspor(rusak)
    assert kunci in str(galat.value)


@pytest.mark.parametrize("kunci", ("id", "completed_by", "result", "was_cancelled"))
def test_kunci_anotasi_yang_hilang_menggagalkan_penguraian(kunci: str) -> None:
    rusak = _muat()
    del rusak[0]["annotations"][0][kunci]
    with pytest.raises(GalatBentukEkspor) as galat:
        urai_ekspor(rusak)
    assert kunci in str(galat.value)


def test_bidang_teks_yang_hilang_menggagalkan_penguraian() -> None:
    """`data` membawa kunci yang namanya ditetapkan konfigurasi proyek.

    Kunci `teks` adalah yang `plan.md` Bagian 3 tetapkan. Proyek yang memakai
    nama lain menghasilkan dokumen tanpa teks, dan dokumen tanpa teks membuat
    seluruh pemeriksaan rentang lolos karena tidak ada yang diperiksa.
    """
    rusak = _muat()
    rusak[0]["data"] = {"text": "salah nama kunci"}
    with pytest.raises(GalatBentukEkspor) as galat:
        urai_ekspor(rusak)
    assert "teks" in str(galat.value)


def test_tipe_yang_berubah_menggagalkan_penguraian() -> None:
    """Bentuk yang berubah tidak selalu berupa kunci yang hilang; ia dapat
    berupa daftar yang menjadi objek."""
    rusak = _muat()
    rusak[0]["annotations"] = {"0": rusak[0]["annotations"][0]}
    with pytest.raises(GalatBentukEkspor):
        urai_ekspor(rusak)


def test_berkas_yang_bukan_daftar_ditolak() -> None:
    with pytest.raises(GalatBentukEkspor):
        urai_ekspor({"tasks": []})  # type: ignore[arg-type]


def test_penguraian_tidak_pernah_sebagian() -> None:
    """**Sifat, bukan kasus.**

    Tugas kedua dirusak; tugas pertama sah. Penguraian yang mengembalikan satu
    tugas dan mengabaikan yang rusak menghasilkan korpus yang **kurang satu
    dokumen tanpa seorang pun tahu** — dan dokumen yang hilang adalah dokumen
    yang bentuknya tidak biasa, yaitu justru yang perlu dilihat orang.
    """
    rusak = _muat()
    del rusak[1]["annotations"]
    with pytest.raises(GalatBentukEkspor):
        urai_ekspor(rusak)


def test_galat_menyebut_letak_tugasnya() -> None:
    """Berkas ekspor sungguhan memuat ribuan tugas. Galat tanpa letak menuntut
    pembacanya mencari sendiri."""
    rusak = _muat()
    del rusak[1]["id"]
    with pytest.raises(GalatBentukEkspor) as galat:
        urai_ekspor(rusak)
    assert "1" in str(galat.value)


def test_tugas_yang_bukan_objek_ditolak() -> None:
    """Daftar tugas yang isinya bukan objek — bentuk yang muncul ketika
    seseorang mengekspor daftar id alih-alih daftar tugas."""
    with pytest.raises(GalatBentukEkspor) as galat:
        urai_ekspor([1, 2])  # type: ignore[list-item]
    assert "id" in str(galat.value)


def test_teks_kosong_ditolak() -> None:
    """**Sisi lain dari uji nama kunci yang salah, dan lebih halus.**

    Kuncinya benar, isinya kosong. Dokumen tanpa teks lolos seluruh
    pemeriksaan rentang karena tidak ada rentang yang dapat diperiksa — bentuk
    kegagalan diam yang sama dengan pengekstrak yang mengembalikan untai
    kosong pada fitur 015.
    """
    rusak = _muat()
    rusak[0]["data"] = {"teks": ""}
    with pytest.raises(GalatBentukEkspor) as galat:
        urai_ekspor(rusak)
    assert "teks" in str(galat.value)


def test_teks_bukan_untai_ditolak() -> None:
    rusak = _muat()
    rusak[0]["data"] = {"teks": ["Kepala sekolah"]}
    with pytest.raises(GalatBentukEkspor):
        urai_ekspor(rusak)
