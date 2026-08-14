"""Uji pemeriksa regulasi dicabut — C-2 fitur 010, C-07, VS-06, KL-07.

**Ketiga lapis diuji terpisah**, dan itu pokok berkas ini. Pemeriksa yang
memeriksa satu lapis terbaca lengkap sementara ia menjaga sepertiga, dan
penghapusan dua lapis hilir tidak terlihat sampai ada jawaban yang tayang atas
regulasi yang sudah dicabut.

Uji di bawah karena itu merusak **satu lapis pada satu waktu** dan menuntut
temuan yang menyebut lapis itu. Satu uji yang merusak ketiganya sekaligus akan
lulus juga pada pemeriksa yang hanya melihat satu.
"""

from pathlib import Path

import pytest

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL
from perkakas.pemeriksa.regulasi_dicabut import (
    LAPIS_C07,
    Lapis,
    periksa_regulasi_dicabut,
)

AKAR = Path(__file__).resolve().parents[2]


def _isi(lapis: Lapis) -> str:
    anggota = sorted(lapis.anggota)[0]
    return (
        f'"""Lapis tiruan."""\n\n'
        f"from src.kamus.segmen import StatusKeberlakuan\n\n\n"
        f"def periksa(status: StatusKeberlakuan) -> bool:\n"
        f"    return status is StatusKeberlakuan.{anggota}\n"
    )


def _pohon(tmp_path: Path, *, rusak: Lapis | None = None, hapus: bool = False) -> Path:
    """Pohon dengan ketiga lapis utuh, kecuali satu yang sengaja dirusak."""
    akar = tmp_path / "pohon"
    for lapis in LAPIS_C07:
        jalur = akar / lapis.berkas
        jalur.parent.mkdir(parents=True, exist_ok=True)
        if lapis is rusak:
            if hapus:
                continue
            jalur.write_text('"""Lapis yang berhenti membaca status."""\n', encoding="utf-8")
            continue
        jalur.write_text(_isi(lapis), encoding="utf-8")
    return akar


def test_pohon_bersih_tidak_menghasilkan_temuan(tmp_path: Path) -> None:
    assert periksa_regulasi_dicabut(_pohon(tmp_path)) == []


def test_repositori_ini_bersih() -> None:
    """Pernyataan yang paling lemah pada berkas ini; uji di bawahnya yang
    membuatnya berarti."""
    assert periksa_regulasi_dicabut(AKAR) == []


def test_ketiga_lapis_terdaftar() -> None:
    """Tiga, bukan satu. Lapis yang jatuh dari daftar berhenti diperiksa tanpa
    satu uji pun gagal."""
    assert len(LAPIS_C07) == 3
    assert {satu.berkas.parts[1] for satu in LAPIS_C07} == {"rag", "ingest"}


@pytest.mark.parametrize("lapis", LAPIS_C07, ids=lambda satu: satu.nama)
def test_lapis_yang_berhenti_membaca_status_ditemukan(tmp_path: Path, lapis: Lapis) -> None:
    """**Uji terpenting berkas ini**, dan ia dijalankan tiga kali.

    Masing-masing lapis dirusak sendirian sementara dua lainnya utuh. Pemeriksa
    yang hanya melihat satu lapis lulus pada dua dari tiga jalannya.
    """
    temuan = periksa_regulasi_dicabut(_pohon(tmp_path, rusak=lapis))
    assert len(temuan) == 1
    assert lapis.nama in str(temuan[0])


@pytest.mark.parametrize("lapis", LAPIS_C07, ids=lambda satu: satu.nama)
def test_lapis_yang_dihapus_ditemukan(tmp_path: Path, lapis: Lapis) -> None:
    """Menghapus berkasnya bukan cara sah meloloskan pemeriksa ini."""
    temuan = periksa_regulasi_dicabut(_pohon(tmp_path, rusak=lapis, hapus=True))
    assert len(temuan) == 1
    assert "tidak ditemukan" in str(temuan[0])


@pytest.mark.parametrize("lapis", LAPIS_C07, ids=lambda satu: satu.nama)
def test_temuan_menyebut_akibat_bila_lapisnya_hilang(tmp_path: Path, lapis: Lapis) -> None:
    """Temuan yang hanya menyebut "lapis hilang" tidak memberi tahu pembacanya
    seberapa jauh regulasi yang dicabut dapat berjalan sebelum tertahan — dan
    itu yang menentukan seberapa mendesak perbaikannya."""
    (temuan,) = periksa_regulasi_dicabut(_pohon(tmp_path, rusak=lapis))
    assert lapis.akibat_bila_hilang in str(temuan)


def test_ketiga_lapis_rusak_menghasilkan_tiga_temuan(tmp_path: Path) -> None:
    """Terpisah, bukan satu temuan gabungan. Temuan gabungan menyembunyikan
    lapis mana yang hilang."""
    akar = tmp_path / "kosong"
    (akar / "src").mkdir(parents=True)
    assert len(periksa_regulasi_dicabut(akar)) == 3


def test_lapis_ingesti_membaca_berlaku_bukan_dicabut() -> None:
    """Ketiga lapis tidak mengeja aturannya sama, dan pemeriksanya tidak
    memaksakan keseragaman.

    L3 menolak **selain** `berlaku`, sehingga ia menangkap `diubah` juga. Dua
    lapis hilir menolak persis `dicabut`. Menuntut ejaan yang sama akan memaksa
    L3 ditulis dengan cara yang lebih lemah.
    """
    ingesti = next(satu for satu in LAPIS_C07 if "ingesti" in satu.nama)
    assert ingesti.anggota == frozenset({"BERLAKU"})
    hilir = [satu for satu in LAPIS_C07 if "ingesti" not in satu.nama]
    assert all(satu.anggota == frozenset({"DICABUT"}) for satu in hilir)


# ---------------------------------------------------------------- pendaftaran


def test_c07_terdaftar_dengan_pemeriksa_bukan_fitur_pengunci() -> None:
    pasal = next(p for p in DAFTAR_PASAL if p.kode == "C-07")
    assert pasal.pemeriksa is not None
    assert pasal.fitur_pengunci is None
