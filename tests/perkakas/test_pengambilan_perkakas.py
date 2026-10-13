"""Perkakas pencarian — T-7 fitur 039, R-08; K-7; P-1 A.

Satu sumber leksikal atas korpus PostgreSQL, tersambung sebagai peran per
indeks: `peran_pemanggil_llm` bagi indeks utama, `peran_penjawaban` bagi indeks
metadata. Tanpa penyemat, tanpa model, tanpa jawaban; keluarannya tanpa teks
segmen. Isi ditanam pengelola; teks dan metadata contoh dibuat-buat.
"""

from __future__ import annotations

import io
import logging
import secrets

import pytest
from src.kamus.segmen import IndeksTujuan
from src.rag.pengambilan.teks_pencarian import ATURAN_PENCARIAN
from tests.api.test_penjawab_korpus import _kata_unik, _tanam
from tests.penyimpanan.test_akun import SambunganPeran

from perkakas.pengambilan import utama

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA


class Jalankan:
    def __init__(self) -> None:
        self.peran: list[str] = []

    def __call__(self, *argumen: str) -> tuple[int, str, str]:
        keluar, galat = io.StringIO(), io.StringIO()

        def sambung(peran: str) -> SambunganPeran:
            self.peran.append(peran)
            return SambunganPeran(peran)

        kode = utama(list(argumen), sambung=sambung, keluar=keluar, galat=galat)  # type: ignore[arg-type]
        return kode, keluar.getvalue(), galat.getvalue()


def test_cari_indeks_utama_tanpa_teks_dengan_perannya(caplog: pytest.LogCaptureFixture) -> None:
    """K-7, R-08, M-10: peringkat berisi skor, dokumen, penanda, dan judul;
    segmen tak layak tidak muncul; dokumen yang lisensinya kini tertutup
    disebut untuk diindeks ulang; tidak satu teks segmen pun ke keluaran
    maupun log."""
    caplog.set_level(logging.DEBUG)
    kata = _kata_unik()
    awal = "d39p-" + secrets.token_hex(3)
    teks = f"Kepala sekolah menyusun {kata} rencana kerja tahunan."
    layak = _tanam(f"{awal}-a", UTAMA, teks, judul="Peraturan Contoh A")
    dicabut = _tanam(f"{awal}-c", UTAMA, teks, status="dicabut")
    tertutup = _tanam(f"{awal}-n", UTAMA, teks, lisensi="CC-BY-NC 4.0")

    j = Jalankan()
    kode, keluar, galat = j("cari", "--kueri", kata)
    assert kode == 0, galat
    assert j.peran == ["peran_pemanggil_llm"]
    assert "Indeks utama" in keluar and "versi utama:" in keluar
    assert f";{ATURAN_PENCARIAN}." in keluar, "R-04 fitur 041: versi memuat penanda aturan"
    baris = [b for b in keluar.splitlines() if awal in b and b[:1].isdigit()]
    assert len(baris) == 1 and layak.split(":")[0] in baris[0]
    assert "Pasal 1" in baris[0] and "Peraturan Contoh A" in baris[0] and "skor" in baris[0]
    assert dicabut.split(":")[0] not in "\n".join(baris)
    assert tertutup.split(":")[0] not in "\n".join(baris)
    assert "dicabut" in keluar and "lisensi_tertutup" in keluar
    ulang = next(b for b in keluar.splitlines() if b.startswith("Perlu diindeks ulang"))
    assert f"{awal}-n" in ulang
    for isi in (keluar, galat, *(c.getMessage() for c in caplog.records)):
        assert "Kepala sekolah menyusun" not in isi


def test_cari_indeks_metadata_sebagai_peran_penjawaban() -> None:
    kata = _kata_unik()
    awal = "d39p-" + secrets.token_hex(3)
    _tanam(f"{awal}-m", METADATA, f"Kajian {kata} rencana kerja.", lisensi=None)
    j = Jalankan()
    kode, keluar, galat = j("cari", "--kueri", kata, "--indeks", "metadata")
    assert kode == 0, galat
    assert j.peran == ["peran_penjawaban"]
    assert "Indeks metadata" in keluar and f"{awal}-m" in keluar


@pytest.mark.parametrize("kueri", ["", "   "])
def test_kueri_kosong_ditolak_sebelum_menyambung(kueri: str) -> None:
    j = Jalankan()
    kode, _, galat = j("cari", "--kueri", kueri)
    assert kode == 2 and galat.strip()
    assert j.peran == []


def test_penolakan_peladen_tanpa_kutipan() -> None:
    """Peladen yang menolak menghasilkan kode 1 dan pesan tanpa kueri."""
    keluar, galat = io.StringIO(), io.StringIO()

    def sambung(peran: str) -> SambunganPeran:
        return SambunganPeran("peran_penyematan")  # tanpa hak korpus

    kode = utama(
        ["cari", "--kueri", "rahasia-kueri-uji"],
        sambung=sambung,  # type: ignore[arg-type]
        keluar=keluar,
        galat=galat,
    )
    assert kode == 1
    assert "rahasia-kueri-uji" not in galat.getvalue()


@pytest.mark.parametrize(
    "argumen",
    [("cari",), ("cari", "--kueri", "rencana", "--indeks", "karantina"), ("hapus",)],
)
def test_argumen_tidak_sah_ditolak_sebelum_menyambung(argumen: tuple[str, ...]) -> None:
    """Indeks di luar keduanya — termasuk karantina — tidak dapat diminta."""
    j = Jalankan()
    kode, _, _ = j(*argumen)
    assert kode == 2
    assert j.peran == []
