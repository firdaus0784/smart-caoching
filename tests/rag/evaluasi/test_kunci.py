"""Uji kunci dokumen dan pasal — T-3 fitur 040, R-02, P-2 A, D-08 Bagian 5.3.

Penanda diambil dari pemotong fitur 038 sungguhan, bukan ditulis tangan:
satuan yang benar atas penanda karangan uji tidak membuktikan apa pun tentang
penanda yang benar-benar tersimpan di indeks.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from src.ingest.segmentasi import potong
from src.rag.evaluasi.gold_set import GalatBerkas, urai
from src.rag.evaluasi.kunci import (
    Kunci,
    SebabKunci,
    SegmenDikenal,
    cocok,
    periksa_korpus,
    satuan,
)
from tests.rag.evaluasi.rekaan import baris, berkas

_AYAT = " ".join(["kata"] * 200)


def _dokumen() -> str:
    """Pembukaan; Pasal 2 pendek; Pasal 7 panjang berayat; Pasal 21 panjang
    tanpa ayat; Pasal 2A; penjelasan."""
    return "\n".join(
        [
            "PERATURAN REKAAN",
            "Menimbang bahwa rekaan ini dibuat bagi uji.",
            "Pasal 2",
            "Isi pendek pasal dua.",
            "Pasal 7",
            *(f"({i}) {_AYAT}" for i in range(1, 6)),
            "Pasal 21",
            " ".join(["tanpa"] * 1200),
            "Pasal 2A",
            "Pasal sisipan.",
            "PENJELASAN",
            "Pasal 2",
            "Cukup jelas.",
        ]
    )


def _penanda() -> list[str]:
    return [p.penanda for p in potong(_dokumen())]


def test_penanda_fitur_038_memuat_ketiga_akhiran() -> None:
    """Prasyarat uji: dokumen contoh memang menghasilkan ayat, potongan, dan
    penjelasan; tanpanya uji di bawah lulus tanpa menguji apa pun."""
    penanda = _penanda()
    assert any(" ayat (" in p for p in penanda)
    assert any(", potongan " in p for p in penanda)
    assert "Penjelasan Pasal 2" in penanda
    assert "Pasal 2A" in penanda


def test_satuan_setiap_penanda_fitur_038() -> None:
    assert {satuan(p) for p in _penanda()} == {
        "Pembukaan",
        "Pasal 2",
        "Pasal 7",
        "Pasal 21",
        "Pasal 2A",
        "Penjelasan",
        "Penjelasan Pasal 2",
    }


@pytest.mark.parametrize(
    ("penanda", "harapan"),
    [
        ("Pasal 7", "Pasal 7"),
        ("Pasal 7 ayat (1)", "Pasal 7"),
        ("Pasal 7 ayat (1)\u2013(3)", "Pasal 7"),
        ("Pasal 7 ayat (2), potongan 1 dari 2", "Pasal 7"),
        ("Pasal 7, potongan 2 dari 3", "Pasal 7"),
        ("Pembukaan, bagian 2", "Pembukaan"),
        ("Bagian 3, potongan 1 dari 2", "Bagian 3"),
        ("Penjelasan Pasal 1", "Penjelasan Pasal 1"),
    ],
)
def test_satuan(penanda: str, harapan: str) -> None:
    assert satuan(penanda) == harapan


def test_kunci_cocok_sama_persis_bukan_awalan() -> None:
    """P-2 A (M-3): `Pasal 2` tidak cocok `Pasal 21` maupun `Pasal 2A`."""
    kunci = Kunci(dokumen="DOK-1", bagian="Pasal 2")
    cocok_ = {p for p in _penanda() if cocok(kunci, "DOK-1", p)}
    assert cocok_ == {"Pasal 2"}
    tujuh = Kunci(dokumen="DOK-1", bagian="Pasal 7")
    semua_tujuh = [p for p in _penanda() if p.startswith("Pasal 7")]
    assert len(semua_tujuh) > 1
    assert all(cocok(tujuh, "DOK-1", p) for p in semua_tujuh)
    assert not cocok(tujuh, "DOK-2", "Pasal 7")
    assert not cocok(Kunci(dokumen="DOK-1", bagian="Penjelasan"), "DOK-1", "Penjelasan Pasal 2")


@pytest.mark.parametrize(
    "bagian",
    [
        "Pasal 7 ayat (1)",
        "Pasal 7 ayat (1)\u2013(3)",
        "Pasal 7, potongan 1 dari 2",
        "Pembukaan, bagian 2",
        " Pasal 7",
        "Pasal 7 ",
    ],
)
def test_kunci_di_bawah_satuan_ditolak(bagian: str) -> None:
    """Kunci di bawah pasal tidak tahan perubahan ukuran segmen D-07."""
    with pytest.raises(ValidationError):
        Kunci(dokumen="DOK-1", bagian=bagian)
    with pytest.raises(GalatBerkas, match="baris 1"):
        urai(berkas(baris("q-1", kunci=[("DOK-1", bagian)])))


@pytest.mark.parametrize(
    "bagian", ["Pasal 7", "Pasal 7A", "Penjelasan Pasal 1", "Pembukaan", "Bagian 3", "Lampiran"]
)
def test_kunci_satuan_diterima(bagian: str) -> None:
    assert Kunci(dokumen="DOK-1", bagian=bagian).bagian == bagian


def test_dokumen_bertepi_spasi_ditolak() -> None:
    with pytest.raises(ValidationError):
        Kunci(dokumen=" DOK-1", bagian="Pasal 1")


def _segmen(id_dokumen: str) -> list[SegmenDikenal]:
    return [
        SegmenDikenal(id_segmen=f"{id_dokumen}:{i:04d}", id_dokumen=id_dokumen, penanda=p)
        for i, p in enumerate(_penanda())
    ]


def test_periksa_korpus_dua_masalah_dengan_pengenal_tanpa_teks() -> None:
    """R-02: dokumen di luar korpus; bagian tanpa segmen. R-07: tanpa teks."""
    rahasia = "Pak Darmawan bertanya soal dana BOS"
    gold = urai(
        berkas(
            baris("q-1", kunci=[("DOK-1", "Pasal 7")], pertanyaan=rahasia),
            baris("q-2", "F", kunci=[("DOK-1", "Pasal 2"), ("DOK-9", "Pasal 1")]),
            baris("q-3", "B", kunci=[("DOK-1", "Pasal 22")], pertanyaan=rahasia),
            baris("q-4", "C"),
        )
    )
    temuan = periksa_korpus(gold, _segmen("DOK-1"))
    assert [(t.id_pertanyaan, t.urutan, t.sebab) for t in temuan] == [
        ("q-2", 2, SebabKunci.DI_LUAR_KORPUS),
        ("q-3", 1, SebabKunci.TANPA_SEGMEN),
    ]
    pesan = "\n".join(map(str, temuan))
    assert "q-2" in pesan
    assert "DOK-9" in pesan
    assert "Pasal 22" in pesan
    assert "Darmawan" not in pesan


def test_periksa_korpus_bersih() -> None:
    gold = urai(
        berkas(baris("q-1", kunci=[("DOK-1", "Pasal 21"), ("DOK-1", "Penjelasan Pasal 2")]))
    )
    assert periksa_korpus(gold, _segmen("DOK-1")) == ()
