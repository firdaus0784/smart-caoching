"""Perkakas penarikan data — T-5 fitur 033, R-03, R-04, R-09; K-7.

Keluaran diuji terhadap PostgreSQL dengan kedua peran perkakas. Pseudonim
tidak pernah tercetak: orang yang menjalankan perkakas butuh nomor dan jumlah,
bukan siapa.
"""

from __future__ import annotations

import io
import re
from datetime import timedelta
from pathlib import Path

from tests.konftes_asinkron import jalankan
from tests.penyimpanan.test_penarikan_simpan import T0, _isi, _minta, _penarikan, _psd

from perkakas.penarikan import BATAS_HARI, utama

AKAR = Path(__file__).resolve().parents[2]


def _jalan(*argv: str, kini=T0) -> tuple[int, str]:  # type: ignore[no-untyped-def]
    keluar = io.StringIO()
    kode = utama(list(argv), penarikan=_penarikan(), keluar=keluar, sekarang=lambda: kini)
    return kode, keluar.getvalue()


def test_daftar_menandai_yang_melewati_empat_belas_hari_tanpa_pseudonim() -> None:
    a, b = _psd(), _psd()
    jalankan(_isi(a))
    jalankan(_isi(b))
    lama = jalankan(_minta(a, T0 - timedelta(days=BATAS_HARI + 1)))
    baru = jalankan(_minta(b, T0 - timedelta(days=2)))
    kode, teks = _jalan("daftar")
    assert kode == 0
    baris = {int(m.group(1)): m.group(0) for m in re.finditer(r"#(\d+)[^\n]*", teks)}
    assert "melewati 14 hari" in baris[lama]
    assert "15 hari" in baris[lama]
    assert "melewati" not in baris[baru]
    assert "2 hari" in baris[baru]
    assert a not in teks and b not in teks
    assert "psd_" not in teks
    assert BATAS_HARI == 14


def test_jalankan_memenuhi_seluruh_yang_tertunda_dan_mencetak_jumlah_saja() -> None:
    a = _psd()
    jalankan(_isi(a))
    nomor = jalankan(_minta(a))
    kode, teks = _jalan("jalankan")
    assert kode == 0
    assert f"#{nomor} dipenuhi" in teks
    assert "telemetri.peristiwa: 1" in teks
    assert "pemetaan pseudonim: 1" in teks
    assert "psd_" not in teks
    assert nomor not in [p.nomor for p in jalankan(_penarikan().tertunda())]
    kode, teks = _jalan("daftar")
    assert f"#{nomor} " not in teks


def test_tanpa_permintaan_tertunda_mengatakannya() -> None:
    jalankan(_penarikan().tertunda())
    kode, _ = _jalan("jalankan")
    assert kode == 0
    kode, teks = _jalan("daftar")
    assert kode == 0
    assert "Tidak ada permintaan tertunda." in teks


def test_layanan_aplikasi_tidak_memakai_penyimpan_penarikan() -> None:
    """R-04, M-7: hanya perkakas penarikan yang mengimpor penyimpan ini.

    Peran penghapus yang terjangkau layanan aplikasi meruntuhkan sifat
    tambah-saja empat fitur pada satu kredensial (P-1).
    """
    pemakai = sorted(
        str(p.relative_to(AKAR))
        for akar in ("src", "perkakas", "web/src")
        for p in (AKAR / akar).rglob("*")
        if p.suffix in {".py", ".ts", ".tsx"}
        and p.is_file()
        and "penyimpanan.penarikan" in p.read_text(encoding="utf-8")
        and p.name != "penarikan.py"
    )
    assert pemakai == []
    assert "penyimpanan.penarikan" in (AKAR / "perkakas" / "penarikan.py").read_text("utf-8")
    assert "PERAN_PENARIKAN" not in (AKAR / "perkakas" / "jalankan_lokal.py").read_text("utf-8")
