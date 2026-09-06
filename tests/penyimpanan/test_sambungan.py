"""Uji konfigurasi sambungan — T-1, R-05, Keputusan Gerbang 1 nomor 1.

## Yang dijaga di sini

Gerbang 1 fitur 024 memutuskan **satu peladen, dua basis data**: satu bagi
data perilaku dan korpus, satu bagi kunci pemetaan pseudonim. C-05 menuntut
keduanya tidak berada pada basis data yang sama.

Keputusan itu diwujudkan sebagai **dua tipe konfigurasi yang berbeda**, bukan
satu tipe dengan dua nilai — bentuk yang sama dengan `KredensialPseudonim`
pada fitur 002, dan alasannya sejajar:

- **Nilai lain pada tipe yang sama** dijaga pemeriksaan saat jalan, dan
  pemeriksaan yang lupa dipanggil tidak menghasilkan galat apa pun.
- **Tipe berbeda** tidak dapat dipakaikan oleh kekeliruan pengetikan mana pun.

## Mengapa sebagian uji memanggil `mypy`

Inti tugas ini bukan "salah pasang ditolak saat jalan" melainkan **salah pasang
tidak dapat ditulis**. Uji yang hanya memanggil fungsi dengan argumen keliru
membuktikan penolakan saat jalan; ia tidak membuktikan pemeriksa tipe
menangkapnya. Karena itu dua uji menjalankan `mypy` atas cuplikan yang sengaja
salah dan menuntutnya gagal — bentuk yang sama dengan uji linter pada
`tests/tata_kelola/`.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.penyimpanan.sambungan import (
    KonfigurasiPerilaku,
    KonfigurasiPseudonim,
    sambungan_perilaku,
    sambungan_pseudonim,
)

AKAR = Path(__file__).resolve().parents[2]

_PERILAKU = KonfigurasiPerilaku(
    peladen="127.0.0.1", porta=5432, basis_data="smart_coaching", pengguna="peran_penjawab"
)
_PSEUDONIM = KonfigurasiPseudonim(
    peladen="127.0.0.1",
    porta=5432,
    basis_data="smart_coaching_pseudonim",
    pengguna="peran_pseudonim",
)


# ── Dua tipe, dan keduanya tidak dapat saling menggantikan ────────────


def test_dua_tipe_berbeda_bukan_dua_nilai() -> None:
    """Kesamaan bentuk mengundang fungsi yang menerima keduanya, dan fungsi
    semacam itu adalah tempat C-05 runtuh tanpa terlihat."""
    assert KonfigurasiPerilaku is not KonfigurasiPseudonim
    assert not issubclass(KonfigurasiPerilaku, KonfigurasiPseudonim)
    assert not issubclass(KonfigurasiPseudonim, KonfigurasiPerilaku)


def test_penyusun_perilaku_menolak_konfigurasi_pseudonim() -> None:
    with pytest.raises(TypeError):
        sambungan_perilaku(_PSEUDONIM)  # type: ignore[arg-type]


def test_penyusun_pseudonim_menolak_konfigurasi_perilaku() -> None:
    with pytest.raises(TypeError):
        sambungan_pseudonim(_PERILAKU)  # type: ignore[arg-type]


def test_masing_masing_menerima_pasangannya() -> None:
    assert sambungan_perilaku(_PERILAKU)
    assert sambungan_pseudonim(_PSEUDONIM)


# ── Basis data wajib berbeda ──────────────────────────────────────────


def test_basis_data_kedua_konfigurasi_tidak_boleh_sama() -> None:
    """C-05: kunci pseudonim tidak berada pada basis data yang sama dengan
    data perilaku. Kesamaan nama basis data adalah pelanggarannya, dan ia
    tidak terbaca dari tipe mana pun."""
    from src.penyimpanan.sambungan import periksa_keterpisahan

    with pytest.raises(ValueError, match="basis data"):
        periksa_keterpisahan(
            _PERILAKU,
            KonfigurasiPseudonim(
                peladen="127.0.0.1",
                porta=5432,
                basis_data=_PERILAKU.basis_data,
                pengguna="peran_pseudonim",
            ),
        )


def test_pengguna_kedua_konfigurasi_tidak_boleh_sama() -> None:
    """Basis data terpisah dengan pengguna yang sama adalah keterpisahan yang
    dapat ditembus satu pernyataan hak akses."""
    from src.penyimpanan.sambungan import periksa_keterpisahan

    with pytest.raises(ValueError, match="pengguna"):
        periksa_keterpisahan(
            _PERILAKU,
            KonfigurasiPseudonim(
                peladen="127.0.0.1",
                porta=5432,
                basis_data="lain",
                pengguna=_PERILAKU.pengguna,
            ),
        )


def test_keterpisahan_yang_sah_diterima() -> None:
    from src.penyimpanan.sambungan import periksa_keterpisahan

    periksa_keterpisahan(_PERILAKU, _PSEUDONIM)


# ── Sifat konfigurasi ─────────────────────────────────────────────────


def test_konfigurasi_beku() -> None:
    """Konfigurasi yang dapat disunting saat jalan bukan pemisahan melainkan
    penanda — kalimat yang sama sudah berlaku bagi `KredensialPseudonim`."""
    with pytest.raises(ValidationError):
        _PERILAKU.basis_data = "lain"  # type: ignore[misc]


def test_bidang_tambahan_ditolak() -> None:
    with pytest.raises(ValidationError):
        KonfigurasiPerilaku(
            peladen="127.0.0.1",
            porta=5432,
            basis_data="x",
            pengguna="y",
            sandi="rahasia",  # type: ignore[call-arg]
        )


def test_sandi_tidak_menjadi_bidang_konfigurasi() -> None:
    """Sandi dibaca lingkungan saat menyambung, tidak disimpan pada objek yang
    dapat tercetak ke log. V-06 melarang rahasia pada repositori; menaruhnya
    pada model yang punya `__repr__` adalah cara paling mudah ia bocor."""
    assert "sandi" not in KonfigurasiPerilaku.model_fields
    assert "sandi" not in KonfigurasiPseudonim.model_fields


def test_konfigurasi_tidak_membaca_lingkungan_sendiri() -> None:
    """R-06: pemanggil yang memilih. Konfigurasi yang membaca lingkungan
    sendiri memilih untuk pemanggilnya."""
    isi = (AKAR / "src" / "penyimpanan" / "sambungan.py").read_text(encoding="utf-8")
    for terlarang in ("os.environ", "getenv", "load_dotenv"):
        assert terlarang not in isi, terlarang


# ── Pemeriksa tipe, bukan hanya penolakan saat jalan ──────────────────


def _mypy(cuplikan: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    """Cuplikan ditulis ke berkas, bukan diberikan lewat `-c`.

    `-c` bertabrakan dengan `files` pada konfigurasi proyek — mypy menolak
    keduanya sekaligus. Ditemukan uji penjaga `test_mypy_menerima_pasangan_
    yang_benar`, yang memang ada untuk itu: tanpanya, tabrakan konfigurasi
    akan membuat uji penolakan lulus tanpa membuktikan apa pun.
    """
    berkas = tmp_path / "cuplikan.py"
    berkas.write_text(textwrap.dedent(cuplikan), encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "mypy", "--no-error-summary", str(berkas)],
        cwd=AKAR,
        capture_output=True,
        text=True,
        check=False,
    )


def test_mypy_menolak_konfigurasi_pseudonim_pada_penyusun_perilaku(tmp_path: Path) -> None:
    """Inti T-1: salah pasang **tidak dapat ditulis**, bukan sekadar ditolak."""
    hasil = _mypy(
        """
        from src.penyimpanan.sambungan import KonfigurasiPseudonim, sambungan_perilaku
        k = KonfigurasiPseudonim(peladen="h", porta=1, basis_data="b", pengguna="p")
        sambungan_perilaku(k)
        """,
        tmp_path,
    )
    assert hasil.returncode != 0, hasil.stdout
    assert "arg-type" in hasil.stdout, hasil.stdout


def test_mypy_menerima_pasangan_yang_benar(tmp_path: Path) -> None:
    """Penjaga atas uji di atasnya: `mypy` yang gagal pada cuplikan apa pun
    akan membuat uji itu lulus tanpa membuktikan apa pun."""
    hasil = _mypy(
        """
        from src.penyimpanan.sambungan import KonfigurasiPerilaku, sambungan_perilaku
        k = KonfigurasiPerilaku(peladen="h", porta=1, basis_data="b", pengguna="p")
        sambungan_perilaku(k)
        """,
        tmp_path,
    )
    assert hasil.returncode == 0, hasil.stdout
