"""Uji prioritas manajerial — A-2 fitur 022, R-03, R-04, FR-A03.

FR-A03: pengguna menetapkan **3 sampai 5** prioritas manajerial *"yang menjadi
dasar penyaringan konten"*. Kalimat terakhir itu yang membuat berkas ini
penting melebihi ukurannya: prioritas adalah masukan bagi FR-G01, dan pipeline
kurasi fitur 010 sudah menyaring terhadapnya.

## Diuji dari kedua arah

"Menerima 3 sampai 5" lulus juga pada implementasi yang menerima berapa pun di
atas 2. Prioritas yang boleh berjumlah sembilan membuat penyaringan feed tidak
menyaring apa pun — seluruh delapan kategori terpilih, dan "prioritas" berhenti
berarti. Karena itu **batas atas diuji sama tegasnya dengan batas bawah**.

Rentang 3–5 **dibaca dari `docs/D01.md`**, bukan disalin ke berkas ini.
"""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.nlp.anotasi.skema import KategoriMasalah
from src.pengguna.prioritas import (
    JUMLAH_PRIORITAS_MAKSIMUM,
    JUMLAH_PRIORITAS_MINIMUM,
    PrioritasManajerial,
)

AKAR = Path(__file__).resolve().parents[2]

DELAPAN = tuple(KategoriMasalah)


def _prioritas(
    kategori: tuple[KategoriMasalah, ...] = DELAPAN[:3], **ganti: object
) -> PrioritasManajerial:
    argumen: dict[str, object] = {"id_pengguna": "PGN-001", "kategori": kategori}
    argumen.update(ganti)
    return PrioritasManajerial(**argumen)  # type: ignore[arg-type]


def _rentang_d01() -> tuple[int, int]:
    """Rentang FR-A03 pada D-01 — sumbernya, bukan salinannya."""
    teks = (AKAR / "docs" / "D01.md").read_text(encoding="utf-8")
    baris = next(g for g in teks.splitlines() if g.startswith("| FR-A03"))
    cocok = re.search(r"(\d+)\s*[–-]\s*(\d+)", baris)
    assert cocok is not None, baris
    return int(cocok.group(1)), int(cocok.group(2))


# ------------------------------------------------------------ R-03 · kedua arah


def test_rentang_dibaca_dari_d01() -> None:
    """Pemeriksaan yang tidak menemukan sumbernya tidak memeriksa apa pun."""
    assert _rentang_d01() == (JUMLAH_PRIORITAS_MINIMUM, JUMLAH_PRIORITAS_MAKSIMUM)
    assert (JUMLAH_PRIORITAS_MINIMUM, JUMLAH_PRIORITAS_MAKSIMUM) == (3, 5)


def test_dua_prioritas_ditolak() -> None:
    """Batas bawah. Dua prioritas membuat feed menyempit sampai kekurangan isi,
    dan titik kritis T5 pada D-02 mengukur akibatnya."""
    with pytest.raises(ValidationError):
        _prioritas(DELAPAN[:2])


def test_enam_prioritas_ditolak() -> None:
    """**Batas atas, dan ia yang paling mudah terlewat.**

    "Menerima 3 sampai 5" lulus juga pada implementasi yang menerima berapa pun
    di atas 2. Prioritas yang boleh berjumlah sembilan membuat penyaringan
    FR-G01 tidak menyaring apa pun.
    """
    with pytest.raises(ValidationError):
        _prioritas(DELAPAN[:6])


def test_delapan_prioritas_ditolak() -> None:
    """Memilih seluruh kategori adalah cara paling langsung membuat "prioritas"
    berhenti berarti — dan bentuk yang paling mungkin dicoba pengguna."""
    with pytest.raises(ValidationError):
        _prioritas(DELAPAN)


def test_nol_prioritas_ditolak() -> None:
    with pytest.raises(ValidationError):
        _prioritas(())


@pytest.mark.parametrize("jumlah", [3, 4, 5])
def test_tiga_sampai_lima_diterima(jumlah: int) -> None:
    """Ketiga nilai di dalam rentang diuji, bukan hanya satu. Batas yang hanya
    diuji pada tengahnya membiarkan salah satu ujungnya bergeser."""
    assert len(_prioritas(DELAPAN[:jumlah]).kategori) == jumlah


# ------------------------------------------------------------ R-04 · tanpa kembar


def test_kategori_kembar_ditolak() -> None:
    """Prioritas kembar membuat satu kategori berbobot dua kali pada penyaringan
    feed tanpa seorang pun memutuskannya, dan urutannya menjadi dua urutan."""
    with pytest.raises(ValidationError):
        _prioritas((KategoriMasalah.K1, KategoriMasalah.K3, KategoriMasalah.K1))


def test_kembar_ditolak_meski_jumlahnya_sah() -> None:
    """Penjagaan panjang dan penjagaan kekembaran berdiri sendiri: tiga pilihan
    yang dua di antaranya sama tetap tiga menurut panjangnya."""
    kembar = (KategoriMasalah.K2, KategoriMasalah.K2, KategoriMasalah.K2)
    assert len(kembar) == JUMLAH_PRIORITAS_MINIMUM
    with pytest.raises(ValidationError):
        _prioritas(kembar)


# ------------------------------------------------------ enum dipakai ulang


def test_kategori_dipakai_ulang_bukan_ditulis_ulang() -> None:
    """**Pemakaian ketiga** `KategoriMasalah` sesudah fitur 003 dan 010.

    D-04 Bagian 7.1 menulis `prioritas_manajerial.kategori (K1–K8)`, dan enum
    itu sudah mewujudkannya sejak fitur 003. Enum keempat akan mengulangi
    kekeliruan `IndeksTujuan` (KB-036) — yang sudah terulang sekali lagi pada
    pendeteksi data pribadi kemarin.
    """
    isi = (AKAR / "src" / "pengguna" / "prioritas.py").read_text(encoding="utf-8")
    assert "from src.nlp.anotasi.skema import KategoriMasalah" in isi
    assert "class KategoriMasalah" not in isi


def test_kategori_di_luar_k1_k8_ditolak() -> None:
    """KM-04: enum tidak pernah menyimpan nilai di luar daftar."""
    with pytest.raises(ValidationError):
        _prioritas(("K9", KategoriMasalah.K1, KategoriMasalah.K2))  # type: ignore[arg-type]


# ------------------------------------------------------------- urutan terhitung


def test_urutan_mengikuti_posisi_bukan_bidang_tersendiri() -> None:
    """D-04 Bagian 7.1 menyimpan `urutan` sebagai kolom; di sini ia **dihitung
    dari posisi**.

    Dua tempat yang menyatakan urutan yang sama dapat berselisih, dan yang
    berselisih membuat "prioritas pertama" tidak terjawab. Bentuk yang sama
    dengan `HasilSaring.boleh_masuk_antrean` (010).
    """
    prioritas = _prioritas((KategoriMasalah.K5, KategoriMasalah.K1, KategoriMasalah.K3))
    assert prioritas.baris() == (
        ("PGN-001", KategoriMasalah.K5, 1),
        ("PGN-001", KategoriMasalah.K1, 2),
        ("PGN-001", KategoriMasalah.K3, 3),
    )


def test_urutan_mulai_dari_satu() -> None:
    """Urutan yang mulai dari nol akan tampil sebagai "prioritas ke-0" pada
    layar S-xx, dan mikrokopi D-05 ditulis untuk pembaca, bukan untuk larik."""
    assert _prioritas().baris()[0][2] == 1


def test_urutan_pilihan_dipertahankan() -> None:
    """Urutan adalah pilihan pengguna, bukan urutan enum. Mengurutkannya ulang
    diam-diam akan mengubah prioritas pertama seseorang tanpa ia tahu."""
    dibalik = (KategoriMasalah.K8, KategoriMasalah.K2, KategoriMasalah.K5)
    assert _prioritas(dibalik).kategori == dibalik


def test_tidak_ada_bidang_urutan_pada_model() -> None:
    """Bidang `urutan` yang dapat diisi pemanggil dapat berselisih dengan
    posisinya."""
    assert "urutan" not in PrioritasManajerial.model_fields


# --------------------------------------------------------------------- bentuk


def test_prioritas_beku() -> None:
    with pytest.raises(ValidationError):
        _prioritas().id_pengguna = "PGN-002"  # type: ignore[misc]


def test_bidang_tambahan_ditolak() -> None:
    with pytest.raises(ValidationError):
        _prioritas(bobot=0.5)


def test_pemilik_wajib() -> None:
    with pytest.raises(ValidationError):
        _prioritas(id_pengguna="")
