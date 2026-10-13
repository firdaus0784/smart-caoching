"""Judul regulasi bernomor dan bertahun — T-3 fitur 041, P-3 A, TK-88, D-06 K-A.

Judul ikut dicari bersama setiap pasal (D-07 Bagian 3.3), sehingga nomor dan
tahun pada judul yang membuat pasal dapat ditemukan dengan menyebut
regulasinya. Contohnya milik D-06; uji membacanya dari sana.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from src.ingest.dokumen import Dokumen, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.gerbang import GalatGerbang, GalatJudulRegulasi, Gerbang
from src.ingest.judul_regulasi import judul_regulasi_sah
from src.ingest.peringkat import JenisSumber
from src.penyimpanan.kredensial_baku import VERIFIKASI
from src.penyimpanan.tiruan import PenyimpanTiruan
from tests.konftes_asinkron import jalankan

AKAR = Path(__file__).resolve().parents[2]
D06 = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")


def _contoh() -> list[tuple[str, str]]:
    bagian = D06.split("**Contoh judul regulasi**", 1)[1].split("\n\n", 2)[1]
    hasil = []
    for b in bagian.splitlines():
        sel = [x.strip() for x in b.strip("|").split("|")]
        if len(sel) == 2 and sel[1] in ("Diterima", "Ditolak"):
            hasil.append((sel[0], sel[1]))
    return hasil


def test_d06_memuat_contoh_kedua_arah() -> None:
    keputusan = [k for _, k in _contoh()]
    assert keputusan.count("Diterima") >= 3
    assert keputusan.count("Ditolak") >= 3


@pytest.mark.parametrize(("judul", "keputusan"), _contoh())
def test_contoh_d06(judul: str, keputusan: str) -> None:
    """P-3 A (M-6): pola milik D-06, tidak dikarang saat implementasi."""
    assert judul_regulasi_sah(judul) is (keputusan == "Diterima")


def _dokumen(**ubah: object) -> Dokumen:
    bidang: dict[str, object] = {
        "id": "dok_041",
        "judul": "Peraturan Menteri Contoh Nomor 6 Tahun 2021",
        "jenis": JenisSumber.REGULASI_RESMI,
        "penerbit": "Kementerian Contoh",
        "tahun": 2021,
        "tingkat_kerahasiaan": TingkatKerahasiaan.PUBLIK,
        "status_persetujuan_pemilik": StatusPersetujuan.BELUM_DIMINTA,
    }
    bidang.update(ubah)
    return Dokumen(**bidang)  # type: ignore[arg-type]


def test_terima_menolak_regulasi_tanpa_pola_sebelum_menulis() -> None:
    """P-3 A (M-5): ditolak di gerbang, satu-satunya pintu penerimaan; tidak
    satu catatan pun tersimpan; judul tidak dikutip."""
    gerbang = Gerbang(PenyimpanTiruan())
    with pytest.raises(GalatJudulRegulasi) as galat:
        jalankan(gerbang.terima(_dokumen(judul="Juknis Zqbtrx 2026"), "Pasal 1 isi."))
    assert "Zqbtrx" not in str(galat.value)
    assert "Nomor" in str(galat.value) and "Tahun" in str(galat.value)
    assert jalankan(gerbang.daftar(VERIFIKASI)) == []


def test_terima_regulasi_berpola() -> None:
    gerbang = Gerbang(PenyimpanTiruan())
    jalankan(gerbang.terima(_dokumen(), "Pasal 1 isi."))
    assert [r.dokumen.id for r in jalankan(gerbang.daftar(VERIFIKASI))] == ["dok_041"]


@pytest.mark.parametrize("jenis", [j for j in JenisSumber if j is not JenisSumber.REGULASI_RESMI])
def test_jenis_lain_tidak_diperiksa(jenis: JenisSumber) -> None:
    """P-3 A (M-7): hanya `regulasi_resmi`."""
    ubah: dict[str, object] = {"jenis": jenis, "judul": "Juknis BOSP 2026"}
    if jenis is JenisSumber.DOKUMEN_SEKOLAH:
        ubah |= {
            "tingkat_kerahasiaan": TingkatKerahasiaan.INTERNAL_SEKOLAH,
            "status_persetujuan_pemilik": StatusPersetujuan.DIBERIKAN,
        }
    gerbang = Gerbang(PenyimpanTiruan())
    jalankan(gerbang.terima(_dokumen(**ubah), "Isi dokumen."))
    assert len(jalankan(gerbang.daftar(VERIFIKASI))) == 1


def test_galat_judul_adalah_galat_gerbang() -> None:
    """Pemanggil yang menangani galat gerbang tetap menanganinya."""
    assert issubclass(GalatJudulRegulasi, GalatGerbang)
