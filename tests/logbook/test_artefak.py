"""Catatan versi artefak L2 — T-2 fitur 026, R-02, C-09, D-10 Bagian 4.

D-10 Bagian 4 menetapkan apa yang dicatat bagi tiap artefak. Dua baris
berlaku bagi fitur 026:

| Model sematan | Nama dan versi |
| Indeks | Nomor versi, tanggal pembangunan, jumlah segmen, komposisi sumber |

Berkas ini menguji bahwa kelimanya **tidak dapat luput karena lupa** —
kekurangannya tertangkap saat memanggil, bukan saat membaca berkas berbulan
kemudian. Alasan yang sama dengan `tambah_percobaan`, yang menerima `Versi`
bertipe alih-alih pemetaan bebas.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.logbook.artefak import KomposisiSumber, VersiIndeks
from src.logbook.penulis import Buku, tambah_versi_artefak

SAAT = datetime(2026, 9, 23, 7, 30, 0, tzinfo=UTC)


def _indeks(**ganti: object) -> VersiIndeks:
    bidang: dict[str, object] = {
        "versi_indeks": "indeks_utama-20260923T073000Z",
        "dibangun_pada": SAAT,
        "jumlah_segmen": 3,
        "komposisi_sumber": (KomposisiSumber(label="terbuka", jumlah=3),),
        "nama_model_sematan": "penyemat-tiruan",
        "versi_model_sematan": "hash-sha256-1",
    }
    bidang.update(ganti)
    return VersiIndeks(**bidang)  # type: ignore[arg-type]


# ── kelima keterangan D-10 tidak dapat luput ────────────────────────


@pytest.mark.parametrize(
    "bidang",
    [
        "versi_indeks",
        "dibangun_pada",
        "jumlah_segmen",
        "komposisi_sumber",
        "nama_model_sematan",
        "versi_model_sematan",
    ],
)
def test_bidang_d10_wajib(bidang: str) -> None:
    """Tiap bidang yang D-10 Bagian 4 tuntut wajib, tanpa nilai baku.

    Nilai baku pada salah satunya membuat catatan yang tampak lengkap
    sementara satu keterangan dikarang — dan yang membacanya berbulan kemudian
    tidak punya cara mengetahuinya.
    """
    lengkap = _indeks().model_dump()
    del lengkap[bidang]
    with pytest.raises(ValidationError) as galat:
        VersiIndeks(**lengkap)

    # Sebabnya diperiksa, bukan hanya kejadiannya. Uji mutasi T-2 menemukan
    # `pytest.raises(ValidationError)` telanjang **diam** ketika bidangnya
    # diberi nilai baku: bidang itu terisi diam-diam, lalu penjaga lain yang
    # menyalak — dan ujinya lulus karena alasan yang bukan alasannya.
    # Bentuk yang sama dengan KB-098.
    hilang = [g for g in galat.value.errors() if g["type"] == "missing"]
    assert [g["loc"] for g in hilang] == [(bidang,)], (
        f"galat bukan karena {bidang!r} hilang, melainkan: "
        f"{[(g['type'], g['loc']) for g in galat.value.errors()]}"
    )


def test_untai_kosong_ditolak() -> None:
    with pytest.raises(ValidationError):
        _indeks(versi_indeks="")


def test_waktu_tanpa_zona_ditolak() -> None:
    """KM-01: seluruh waktu disimpan UTC. Waktu tanpa zona **tampak** benar
    dan menjadi salah saat dibaca di zona lain."""
    with pytest.raises(ValidationError):
        _indeks(dibangun_pada=datetime(2026, 9, 23, 7, 30, 0))


def test_catatan_beku_dan_menolak_bidang_asing() -> None:
    catatan = _indeks()
    with pytest.raises(ValidationError):
        catatan.jumlah_segmen = 9  # type: ignore[misc]
    with pytest.raises(ValidationError):
        _indeks(bidang_asing="apa saja")


# ── komposisi yang tidak menjumlah adalah komposisi yang salah ──────


def test_komposisi_wajib_menjumlah_ke_jumlah_segmen() -> None:
    """**Bentuk, bukan pemeriksaan saat membaca.**

    Komposisi yang jumlahnya tidak sama dengan `jumlah_segmen` tidak
    menghasilkan galat pada siapa pun — ia menghasilkan catatan percobaan yang
    dua angkanya bertentangan, dan yang membacanya tidak tahu mana yang benar.
    """
    with pytest.raises(ValidationError, match="komposisi"):
        _indeks(jumlah_segmen=5, komposisi_sumber=(KomposisiSumber(label="terbuka", jumlah=3),))


def test_indeks_kosong_boleh_tanpa_komposisi() -> None:
    """Nol segmen dengan komposisi kosong adalah keadaan sah — indeks yang
    memang belum berisi apa pun."""
    catatan = _indeks(jumlah_segmen=0, komposisi_sumber=())
    assert catatan.jumlah_segmen == 0


def test_komposisi_kosong_dengan_segmen_ditolak() -> None:
    with pytest.raises(ValidationError, match="komposisi"):
        _indeks(jumlah_segmen=3, komposisi_sumber=())


def test_label_komposisi_kembar_ditolak() -> None:
    """Dua baris berlabel sama menjumlah benar sambil menyatakan dua hal
    tentang satu sumber."""
    with pytest.raises(ValidationError, match="kembar|label"):
        _indeks(
            jumlah_segmen=4,
            komposisi_sumber=(
                KomposisiSumber(label="terbuka", jumlah=2),
                KomposisiSumber(label="terbuka", jumlah=2),
            ),
        )


# ── tertulis ke L2, dan hanya menambah ──────────────────────────────


def test_tertulis_ke_l2_bukan_l1(tmp_path: Path) -> None:
    tambah_versi_artefak(tmp_path, keterangan=_indeks())
    assert (tmp_path / Buku.L2.value).is_file()
    assert not (tmp_path / Buku.L1.value).exists()


def test_baris_memuat_keenam_keterangan_dan_penanda_artefak(tmp_path: Path) -> None:
    tambah_versi_artefak(tmp_path, keterangan=_indeks())
    baris = json.loads((tmp_path / Buku.L2.value).read_text(encoding="utf-8").strip())
    assert baris["artefak"] == "indeks"
    assert baris["versi_indeks"] == "indeks_utama-20260923T073000Z"
    assert baris["jumlah_segmen"] == 3
    assert baris["nama_model_sematan"] == "penyemat-tiruan"
    assert baris["versi_model_sematan"] == "hash-sha256-1"
    assert baris["komposisi_sumber"] == [{"label": "terbuka", "jumlah": 3}]
    assert "dicatat_pada" in baris, "stempel waktu pencatatan tidak ada"


def test_hanya_menambah_tidak_mengubah_baris_lama(tmp_path: Path) -> None:
    """Sifat tambah-saja C-09, diuji atas fungsi baru ini — bukan dipercaya
    karena `tambah_baris` di bawahnya sudah diuji."""
    tambah_versi_artefak(tmp_path, keterangan=_indeks(versi_indeks="pertama"))
    sebelum = (tmp_path / Buku.L2.value).read_text(encoding="utf-8")
    tambah_versi_artefak(tmp_path, keterangan=_indeks(versi_indeks="kedua"))
    sesudah = (tmp_path / Buku.L2.value).read_text(encoding="utf-8")
    assert sesudah.startswith(sebelum), "baris lama berubah"
    assert len(sesudah.splitlines()) == 2
