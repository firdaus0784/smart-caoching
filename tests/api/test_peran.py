"""Uji kendali peran — A-1 fitur 021, R-01 s.d. R-04, `docs/D14.md` Bagian 3.

## Tabel perannya dibaca dari dokumen, bukan disalin ke uji

Tabel peran yang disalin akan benar pada hari ia disalin. Lalu D-14 bertambah
satu rute, dan **tidak satu pun uji gagal** — rute baru itu berjalan tanpa
peran karena tidak ada baris yang menolaknya. Kegagalan yang tidak berbunyi.

Bentuk yang sama dengan uji bidang D-06 (fitur 010), taksonomi D-01 Bagian 9
(fitur 012), dan bentuk tanggapan D-14 Bagian 4.1 (fitur 009).

## Dua arah, dan keduanya perlu

1. Setiap rute D-14 punya peran pada kode — menangkap rute yang **bertambah**.
2. Setiap rute pada kode ada di D-14 — menangkap rute yang **dikarang**, yang
   AG-02 larang.

Satu arah saja meninggalkan lubang yang bentuknya persis kebalikan dari yang
dijaga.
"""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.api.peran import PETA_RUTE, Peran, Rute, boleh

AKAR = Path(__file__).resolve().parents[2]
D14 = AKAR / "docs" / "D14.md"

_BARIS_RUTE = re.compile(
    r"^\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|",
    re.MULTILINE,
)


def _rute_dari_dokumen() -> dict[tuple[str, str], str]:
    """Baca peta rute D-14 Bagian 3 apa adanya.

    Bagian 3 saja: Bagian 4 memuat blok JSON contoh yang memuat kata yang sama
    tanpa menjadi rute.
    """
    isi = D14.read_text(encoding="utf-8")
    awal = isi.index("## 3. Peta Rute")
    akhir = isi.index("## 4. Bentuk Tanggapan")
    return {
        (metode, jalur): peran.strip()
        for metode, jalur, peran in _BARIS_RUTE.findall(isi[awal:akhir])
    }


# ------------------------------------------------------------ R-01 · enam peran


def test_keenam_peran_d14_ada_sebagai_tipe() -> None:
    """D-14 Bagian 3 menyebut enam peran. `verifikator` ditambahkan pada
    Gerbang 2 fitur 002 (KB-011) dan ikut dihitung — ia satu-satunya peran yang
    kredensialnya menjangkau area karantina."""
    assert {p.value for p in Peran} == {
        "pengguna",
        "kurator",
        "anotator",
        "peneliti",
        "verifikator",
        "admin",
    }


def test_peran_bertipe_bukan_untai() -> None:
    """Kendali yang membandingkan untai meloloskan salah eja sebagai peran yang
    tidak dikenal — dan peran yang tidak dikenal ditolak diam-diam, sehingga
    salah ejanya tidak pernah ketahuan sampai seseorang mengeluh."""
    with pytest.raises(ValueError):
        Peran("penggguna")


# -------------------------------------------- R-02, R-04 · arah 1, dari dokumen


def test_setiap_rute_d14_punya_peran_pada_kode() -> None:
    """**Uji terpenting berkas ini, arah pertama.**

    Rute yang bertambah pada D-14 tanpa baris peran adalah rute yang, pada hari
    ia dibangun, terbuka bagi siapa saja karena tidak ada yang menolaknya.
    """
    dokumen = _rute_dari_dokumen()
    assert dokumen, "peta rute D-14 Bagian 3 tidak terbaca — polanya yang keliru"
    kode = {(r.metode, r.jalur) for r in PETA_RUTE}
    kurang = set(dokumen) - kode
    assert not kurang, f"rute D-14 tanpa peran pada kode: {sorted(kurang)}"


def test_setiap_rute_pada_kode_ada_di_d14() -> None:
    """**Arah kedua.** AG-02 melarang menambah rute yang tidak ada pada D-14
    Bagian 3, dan larangan tanpa pemeriksa adalah kalimat."""
    dokumen = _rute_dari_dokumen()
    lebih = {(r.metode, r.jalur) for r in PETA_RUTE} - set(dokumen)
    assert not lebih, f"rute pada kode yang tidak ada di D-14: {sorted(lebih)}"


def test_peran_penjaga_sama_dengan_yang_tertulis_di_d14() -> None:
    """Kolom peran ikut dibaca. Rute yang ada pada kedua sisi dengan peran yang
    berbeda adalah kekeliruan yang tidak tertangkap kedua uji di atas."""
    dokumen = _rute_dari_dokumen()
    for rute in PETA_RUTE:
        # Rute yang tidak ada pada dokumen milik uji di atas. Uji yang gagal
        # karena pelanggaran uji lain menyembunyikan pelanggarannya sendiri.
        tertulis = dokumen.get((rute.metode, rute.jalur))
        if tertulis is None:
            continue
        assert rute.penjaga_tertulis == tertulis, (
            f"{rute.metode} {rute.jalur}: D-14 menulis {tertulis!r}, "
            f"kode menulis {rute.penjaga_tertulis!r}"
        )


def test_tidak_ada_rute_berpasangan_ganda() -> None:
    """Dua baris bagi satu rute membuat yang kedua tidak pernah terbaca — dan
    yang tidak pernah terbaca adalah yang paling mungkin lebih longgar."""
    pasangan = [(r.metode, r.jalur) for r in PETA_RUTE]
    assert len(pasangan) == len(set(pasangan))


# ------------------------------------------------------------ R-02 · penegakan


def test_peran_berwenang_diterima() -> None:
    assert boleh(Peran.PENGGUNA, "POST", "/api/v1/tanya")
    assert boleh(Peran.KURATOR, "GET", "/api/v1/kurasi/antrean")


def test_peran_tidak_berwenang_ditolak() -> None:
    """Kurator bukan pengguna yang bertanya, dan pengguna bukan kurator."""
    assert not boleh(Peran.KURATOR, "POST", "/api/v1/tanya")
    assert not boleh(Peran.PENGGUNA, "GET", "/api/v1/kurasi/antrean")
    assert not boleh(Peran.PENGGUNA, "GET", "/api/v1/analitik/ringkas")


def test_rute_publik_tidak_menuntut_peran() -> None:
    """`/api/v1/auth/masuk` berpenjaga `publik` — pengguna belum punya peran
    ketika ia memanggilnya, dan menuntut peran di sana mengunci pintu dari
    dalam."""
    assert all(boleh(p, "POST", "/api/v1/auth/masuk") for p in Peran)


def test_rute_semua_peran_terbuka_bagi_seluruhnya() -> None:
    """`/api/v1/auth/keluar` berpenjaga `semua`. Peran yang tidak dapat keluar
    adalah sesi yang hanya dapat berakhir dengan kedaluwarsa."""
    assert all(boleh(p, "POST", "/api/v1/auth/keluar") for p in Peran)


def test_rute_yang_tidak_dikenal_ditolak() -> None:
    """**Ditolak, bukan diloloskan.**

    Rute tak dikenal yang diloloskan berarti salah ketik pada penangan menjadi
    pintu terbuka. Ditolak berarti ia menjadi galat yang terlihat pada uji
    pertama.
    """
    assert not boleh(Peran.ADMIN, "POST", "/api/v1/tanyaa")
    assert not boleh(Peran.ADMIN, "GET", "/api/v1/tanya")


def test_metode_ikut_menentukan() -> None:
    """`GET /api/v1/saya/profil` dan `PUT /api/v1/saya/profil` adalah dua baris
    pada D-14. Kendali yang hanya melihat jalurnya menyamakan membaca dengan
    mengubah."""
    assert boleh(Peran.PENGGUNA, "PUT", "/api/v1/saya/profil")
    assert not boleh(Peran.PENGGUNA, "PATCH", "/api/v1/saya/profil")


# ------------------------------------------------------------- R-01 · bentuk


def test_rute_beku() -> None:
    """Tabel peran yang dapat diubah saat jalan adalah tabel yang dapat
    dilonggarkan oleh kode mana pun yang kebetulan mengimpornya."""
    rute = PETA_RUTE[0]
    with pytest.raises(ValidationError):
        rute.jalur = "/api/v1/lain"  # type: ignore[misc]


def test_peta_rute_tidak_dapat_ditambahi_pemanggil() -> None:
    assert isinstance(PETA_RUTE, tuple)
    with pytest.raises(AttributeError):
        PETA_RUTE.append(PETA_RUTE[0])  # type: ignore[attr-defined]


def test_rute_membawa_kebutuhan_yang_menuntutnya() -> None:
    """Setiap baris D-14 Bagian 3 menyebut kode kebutuhannya. Membawanya serta
    membuat rute yang kehilangan dasarnya terlihat — dan `AGENTS.md` menuntut
    setiap berkas berubah dapat ditelusuri ke kode kebutuhan."""
    assert all(r.kebutuhan for r in PETA_RUTE if r.penjaga_tertulis != "semua")


def test_kelas_rute_tanpa_bidang_berbawaan_pada_penjaga() -> None:
    """Penjaga berbawaan membuat rute yang lupa diberi peran terbentuk sebagai
    rute yang sudah berpenjaga — dan tidak satu uji perilaku pun gagal, sebab
    penjaganya memang ada, hanya saja tidak seorang pun memilihnya.

    Bentuk yang sama dengan aturan 2 pemeriksa C-06.
    """
    assert Rute.model_fields["penjaga_tertulis"].is_required()
