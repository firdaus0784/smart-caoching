"""Uji pemeriksa pemisahan instruksi — C-18, R-07, `docs/D13.md` KD-07.

## Uji yang seharusnya ada sejak fitur 001

`periksa_pemisahan_instruksi` adalah pemeriksa mesin bagi **C-18**, dan sampai
hari ini ia **tidak memiliki satu uji pun**. Setiap `make compliance` sejak
fitur 001 melaporkan "C-18 LULUS", dan tidak seorang pun pernah memastikan
pemeriksanya mampu berkata sebaliknya.

Ditemukan lewat sapuan atas seluruh 33 pemeriksa: 31 di antaranya memiliki uji
yang menuntutnya **menyala**, dua tidak. Yang satu ini menjaga pasal keamanan.

## Mengapa separuh perilakunya yang paling penting

Uraian modulnya menyatakannya sendiri: C-18 dapat dilanggar **tanpa mengubah
satu pun bentuk yang dapat dibaca AST** — cukup satu perangkaian untai di dalam
pembangun muatan. Separuh AST-nya (`periksa_konstruksi_instruksi`) sudah diuji
sejak fitur 001; **separuh perilakunya tidak pernah**.

Justru separuh itu yang menjadi alasan pemeriksa ini ada.

## Cara mengujinya

`_jalankan_penanda` mengimpor `susun_muatan` **di dalam fungsi**, sehingga
penggantian pada `src.llm.muatan` terbaca saat pemeriksa dipanggil. Yang
diganti hanya pembangun muatannya; pemeriksanya berjalan apa adanya.

Dua cara melanggar diuji terpisah, dan yang kedua yang paling mudah luput:

1. Muatan serangan **muncul utuh** pada posisi instruksi.
2. Posisi instruksi **berubah panjang** tanpa memuat penandanya utuh — bentuk
   yang terjadi ketika seseorang meringkas atau memotong segmen sebelum
   merangkainya. Penandanya tidak akan ditemukan pencarian untai, dan hanya
   perbandingan panjang yang melihatnya.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from src.llm import muatan as modul_muatan
from src.llm.muatan import MuatanPenyedia, susun_muatan

from perkakas.pemeriksa.pemisahan_instruksi import (
    MUATAN_SERANGAN,
    PENANDA,
    periksa_pemisahan_instruksi,
)

AKAR = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------- pohon sungguhan


def test_repositori_ini_bersih() -> None:
    """Pemeriksa yang berteriak pada pohon sehat akan dimatikan orang.

    Ini juga satu-satunya uji yang selama ini secara tidak langsung menjaga
    C-18 — lewat `make compliance`, bukan lewat rangkaian uji.
    """
    assert periksa_pemisahan_instruksi(AKAR) == []


# ------------------------------------------- pelanggaran 1 · muatan muncul utuh


def test_menyala_ketika_konten_dirangkai_ke_posisi_instruksi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**Uji terpenting berkas ini.**

    Perangkaian satu baris di dalam pembangun muatan membatalkan C-18 tanpa
    mengubah satu pun bentuk yang terbaca AST. Bila pemeriksa diam di sini, ia
    memberi rasa aman atas kendali yang sudah bocor — keadaan yang uraian
    modulnya sendiri sebut paling berbahaya (TA-01).
    """

    def merangkai(permintaan: object) -> MuatanPenyedia:
        asli = susun_muatan(permintaan)  # type: ignore[arg-type]
        rangkai = asli.posisi_instruksi + " " + " ".join(b.teks for b in asli.posisi_konten)
        return asli.model_copy(update={"posisi_instruksi": rangkai})

    monkeypatch.setattr(modul_muatan, "susun_muatan", merangkai)
    temuan = periksa_pemisahan_instruksi(AKAR)
    assert temuan, "pemeriksa C-18 diam pada perangkaian — ia tidak menjaga apa pun"
    assert any(PENANDA[:30] in t.pesan for t in temuan)


def test_setiap_muatan_serangan_dilaporkan_bukan_hanya_yang_pertama(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Laporan yang berhenti pada pelanggaran pertama membuat pembacanya
    mengira tinggal satu jalan masuk yang perlu ditutup."""

    def merangkai(permintaan: object) -> MuatanPenyedia:
        asli = susun_muatan(permintaan)  # type: ignore[arg-type]
        rangkai = asli.posisi_instruksi + " " + " ".join(b.teks for b in asli.posisi_konten)
        return asli.model_copy(update={"posisi_instruksi": rangkai})

    monkeypatch.setattr(modul_muatan, "susun_muatan", merangkai)
    assert len(periksa_pemisahan_instruksi(AKAR)) == len(MUATAN_SERANGAN)


# ------------------------------ pelanggaran 2 · panjang berubah tanpa penanda utuh


def test_menyala_ketika_posisi_instruksi_berubah_panjang_tanpa_penanda_utuh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**Cabang yang paling mudah luput.**

    Seseorang yang meringkas atau memotong segmen sebelum merangkainya tidak
    meninggalkan penandanya utuh, sehingga pencarian untai tidak menemukan apa
    pun. Yang melihatnya hanya perbandingan panjang terhadap muatan tanpa data.

    Tanpa uji ini, cabang `elif` pada pemeriksa tidak pernah dijalankan sekali
    pun — dan cabang yang tidak pernah dijalankan tidak diketahui benar.
    """

    def memotong(permintaan: object) -> MuatanPenyedia:
        asli = susun_muatan(permintaan)  # type: ignore[arg-type]
        if not asli.posisi_konten:
            return asli
        # Delapan aksara pertama saja: penandanya tidak akan muncul utuh.
        potongan = " ".join(b.teks[:8] for b in asli.posisi_konten)
        return asli.model_copy(update={"posisi_instruksi": asli.posisi_instruksi + " " + potongan})

    monkeypatch.setattr(modul_muatan, "susun_muatan", memotong)
    temuan = periksa_pemisahan_instruksi(AKAR)
    assert temuan
    assert any("berubah panjang" in t.pesan for t in temuan)
    assert all(PENANDA not in t.pesan for t in temuan)


# ------------------------------------------------------------------- gabungan


def test_kedua_sisi_dipanggil() -> None:
    """C-18 diperiksa dari dua sisi, dan pemeriksa ini gabungannya.

    Diuji pada **permukaan**, bukan dengan merusak salah satunya: sisi AST
    sudah punya ujinya sendiri, dan mengulangnya di sini membuat kegagalannya
    dilaporkan dua kali dengan sebab yang sama.
    """
    naskah = (AKAR / "perkakas" / "pemeriksa" / "pemisahan_instruksi.py").read_text(
        encoding="utf-8"
    )
    assert "periksa_konstruksi_instruksi(akar)" in naskah
    assert "_jalankan_penanda(akar)" in naskah


def test_penanda_tidak_muncul_pada_naskah_sumber_yang_diperiksa() -> None:
    """Penanda yang kebetulan tertulis pada `src/` akan membuat pemeriksa
    menemukan dirinya sendiri, dan temuannya terbaca sebagai pelanggaran."""
    for berkas in (AKAR / "src").rglob("*.py"):
        assert PENANDA not in berkas.read_text(encoding="utf-8"), berkas


def test_muatan_serangan_tidak_kosong() -> None:
    """Daftar serangan yang kosong membuat seluruh uji di atas lulus tanpa
    menjalankan satu pemeriksaan pun — bentuk TA-01 pada berkas uji ini
    sendiri."""
    assert len(MUATAN_SERANGAN) >= 5
    assert PENANDA in MUATAN_SERANGAN
