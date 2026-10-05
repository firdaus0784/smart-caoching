"""Perkakas kurasi tim — T-4 fitur 013, R-04, K-3, K-4, FR-I07.

Dijalankan terhadap PostgreSQL sungguhan sebagai `peran_pengisi_antrean`:
perkakas ini ada untuk memakai hak T-2, dan tiruannya tidak membuktikan apa
pun tentang hak itu.

## Penyaring yang disuntikkan

`saring()` fitur 010 menahan **setiap** kandidat di L4 sampai ambang relevansi
dikalibrasi (BT-24, C-16), sehingga hari ini tidak satu kandidat pun boleh
masuk antrean (TK-72). Uji jalur "masuk" karena itu menyuntikkan penyaring
yang meloloskan — perilaku perkakas yang diuji, bukan keputusan penyaringnya.
Uji yang memakai penyaring sungguhan membuktikan penahanan itu.
"""

from __future__ import annotations

import io
import json
import secrets
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from src.ingest.kurasi.butir import ButirPengetahuan
from src.ingest.kurasi.saring import HasilSaring, Keadaan, Lapis, Tindakan
from src.penyimpanan.kurasi import (
    PERAN_KURASI,
    PERAN_PENGISI_ANTREAN,
    CatatanPutusan,
    KurasiPostgres,
    PengisiAntreanPostgres,
)
from src.penyimpanan.penemuan import PERAN_PENAYANGAN, PenemuanPostgres
from tests.konftes_asinkron import jalankan
from tests.peladen import siapkan
from tests.penyimpanan.test_akun import SambunganPeran

from perkakas import kurasi as perkakas_kurasi

siapkan()

T0 = datetime(2026, 10, 5, 1, 0, tzinfo=UTC)
HARI = date(2026, 10, 5)
KURATOR = "psd_kkkkkkkkkkkkkkkk"
JUDUL_RAHASIA = "Judul yang tidak boleh terkutip"


def _acak(n: int = 10) -> str:
    return "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))


def _entri(
    *, jenis: str = "riset", lisensi: str = "CC-BY", status: str | None = None, dokumen: str = ""
) -> dict[str, Any]:
    return {
        "butir": {
            "id_butir": "b-" + _acak(),
            "jenis_sumber": jenis,
            "judul": JUDUL_RAHASIA,
            "alasan_relevansi": "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
            "inti_temuan": "Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
            "implikasi_tindakan": ["Susun jadwal supervisi satu semester."],
            "perkiraan_waktu_baca": 4,
            "kategori": "K1",
            "id_dokumen_sumber": dokumen or "dok-" + _acak(),
            "lisensi": lisensi,
            "status_keberlakuan": status,
            "tanggal_akses": "2026-10-01",
        },
        "sumber": {"judul": "Laporan", "penerbit": "Penerbit", "tahun": 2025, "tautan": None},
    }


def _loloskan(butir: ButirPengetahuan, **_: object) -> HasilSaring:
    return HasilSaring(
        lapis_terakhir=Lapis.L4_RELEVANSI,
        keadaan=Keadaan.LOLOS,
        tindakan=Tindakan.MASUK_ANTREAN,
        alasan="diloloskan uji",
    )


def _jalan(*argumen: str, penyaring: Any = None) -> tuple[int, str, str]:
    keluar, galat = io.StringIO(), io.StringIO()
    tambahan = {} if penyaring is None else {"penyaring": penyaring}
    kode = perkakas_kurasi.utama(
        list(argumen),
        pengisi=PengisiAntreanPostgres(SambunganPeran(PERAN_PENGISI_ANTREAN)),  # type: ignore[arg-type]
        keluar=keluar,
        galat=galat,
        sekarang=lambda: T0,
        **tambahan,
    )
    return kode, keluar.getvalue(), galat.getvalue()


def _berkas(tmp_path: Path, isi: object) -> str:
    jalur = tmp_path / "kandidat.json"
    jalur.write_text(json.dumps(isi), encoding="utf-8")
    return str(jalur)


def _menunggu() -> set[str]:
    kurasi = KurasiPostgres(SambunganPeran(PERAN_KURASI))  # type: ignore[arg-type]
    return {k.id_butir for k in jalankan(kurasi.menunggu(hari_ini=HARI))}


# ── isi ──────────────────────────────────────────────────────────────


def test_penyaring_sungguhan_menahan_seluruhnya_di_l4(tmp_path: Path) -> None:
    """TK-72: tanpa ambang L4, antrean tidak terisi — dan perkakas mengatakannya."""
    entri = [_entri(), _entri()]
    kode, keluar, _ = _jalan("isi", "--berkas", _berkas(tmp_path, entri))
    assert kode == 0
    assert "Masuk antrean: 0" in keluar
    assert "Tertahan menunggu penyaring relevansi: 2" in keluar
    assert not {e["butir"]["id_butir"] for e in entri} & _menunggu()


def test_kandidat_lolos_masuk_antrean_beserta_sumbernya(tmp_path: Path) -> None:
    entri = _entri()
    kode, keluar, _ = _jalan("isi", "--berkas", _berkas(tmp_path, [entri]), penyaring=_loloskan)
    assert kode == 0, keluar
    assert "Masuk antrean: 1" in keluar
    kurasi = KurasiPostgres(SambunganPeran(PERAN_KURASI))  # type: ignore[arg-type]
    satu = jalankan(kurasi.satu_menunggu(entri["butir"]["id_butir"], hari_ini=HARI))
    assert satu is not None
    assert satu.sumber == entri["sumber"]
    assert satu.kategori == "K1"
    assert satu.butir["judul"] == JUDUL_RAHASIA


def test_lapis_l1_dan_l3_tetap_berlaku_dengan_penyaring_sungguhan(tmp_path: Path) -> None:
    """FR-I07: lisensi tertutup dibuang, regulasi dicabut menjadi rujukan historis."""
    tertutup = _entri(lisensi="Hak cipta dilindungi")
    dicabut = _entri(jenis="regulasi", status="dicabut")
    kode, keluar, _ = _jalan("isi", "--berkas", _berkas(tmp_path, [tertutup, dicabut]))
    assert kode == 0
    assert "Dibuang: 1" in keluar
    assert "Rujukan historis, tidak masuk antrean: 1" in keluar
    assert not {tertutup["butir"]["id_butir"], dicabut["butir"]["id_butir"]} & _menunggu()


def test_dokumen_yang_sudah_dikenal_dibuang_l2(tmp_path: Path) -> None:
    dokumen = "dok-" + _acak()
    pertama, kedua = _entri(dokumen=dokumen), _entri(dokumen=dokumen)
    kode, keluar, _ = _jalan(
        "isi", "--berkas", _berkas(tmp_path, [pertama, kedua]), penyaring=_loloskan_l2
    )
    assert kode == 0
    assert "Masuk antrean: 1" in keluar
    assert "Dibuang: 1" in keluar


def _loloskan_l2(butir: ButirPengetahuan, *, id_dokumen_dikenal: Any) -> HasilSaring:
    """Lapis L2 sungguhan, L4 diloloskan — bentuk keputusan yang menunggu TK-72."""
    if butir.id_dokumen_sumber in id_dokumen_dikenal:
        return HasilSaring(
            lapis_terakhir=Lapis.L2_KEBARUAN,
            keadaan=Keadaan.GUGUR,
            tindakan=Tindakan.DIBUANG,
            alasan="duplikat",
        )
    return _loloskan(butir)


@pytest.mark.parametrize(
    "isi",
    [
        "bukan json",
        {"butir": "bukan daftar"},
        [{"butir": {"id_butir": "b-x"}, "sumber": {}}],
        [{**_entri(), "lebih": 1}],
        [
            {
                **_entri(),
                "sumber": {"judul": "x", "penerbit": "y", "tahun": 2025, "tautan": "http://a"},
            }
        ],
    ],
)
def test_berkas_berbentuk_salah_ditolak_utuh(tmp_path: Path, isi: object) -> None:
    """Satu entri salah menolak seluruh berkas: tidak ada yang tertulis."""
    sah = _entri()
    jalur = tmp_path / "kandidat.json"
    teks = (
        isi if isinstance(isi, str) else json.dumps([sah, *isi] if isinstance(isi, list) else isi)
    )
    jalur.write_text(teks, encoding="utf-8")
    kode, keluar, galat = _jalan("isi", "--berkas", str(jalur), penyaring=_loloskan)
    assert kode == 2
    assert sah["butir"]["id_butir"] not in _menunggu()
    assert "Ditolak" in galat


def test_id_butir_ganda_dalam_satu_berkas_ditolak(tmp_path: Path) -> None:
    satu = _entri()
    kode, _, galat = _jalan("isi", "--berkas", _berkas(tmp_path, [satu, satu]), penyaring=_loloskan)
    assert kode == 2
    assert "Ditolak" in galat


def test_berkas_tidak_ada(tmp_path: Path) -> None:
    kode, _, galat = _jalan("isi", "--berkas", str(tmp_path / "tidak-ada.json"))
    assert kode == 2
    assert "Ditolak" in galat


def test_keluaran_tidak_mengutip_isi_butir(tmp_path: Path) -> None:
    kode, keluar, galat = _jalan(
        "isi", "--berkas", _berkas(tmp_path, [_entri()]), penyaring=_loloskan
    )
    assert kode == 0
    assert JUDUL_RAHASIA not in keluar + galat


# ── status ───────────────────────────────────────────────────────────


def _tayangkan(entri: dict[str, Any]) -> None:
    kurasi = KurasiPostgres(SambunganPeran(PERAN_KURASI))  # type: ignore[arg-type]
    catatan = CatatanPutusan(
        id_butir=entri["butir"]["id_butir"],
        jenis="setujui",
        peran="kurator",
        pseudonim_kurator=KURATOR,
        alasan="Layak tayang",
        waktu=T0,
    )
    assert jalankan(kurasi.setujui(catatan, butir=entri["butir"]))


def test_status_dicabut_memperbarui_antrean_dan_menarik_yang_tayang(tmp_path: Path) -> None:
    """K-4, C-07: butir tayang bersumber regulasi yang dicabut ditarik otomatis."""
    dokumen = "dok-" + _acak()
    menunggu = _entri(jenis="regulasi", status="berlaku", dokumen=dokumen)
    tayang = _entri(jenis="regulasi", status="berlaku", dokumen=dokumen)
    # Dua dokumen yang sama lolos karena penyaring uji tidak menjalankan L2.
    _jalan("isi", "--berkas", _berkas(tmp_path, [menunggu, tayang]), penyaring=_loloskan)
    _tayangkan(tayang)

    kode, keluar, _ = _jalan("status", "--dokumen", dokumen, "--status", "dicabut")
    assert kode == 0, keluar
    assert "Butir tayang ditarik: 1" in keluar

    kurasi = KurasiPostgres(SambunganPeran(PERAN_KURASI))  # type: ignore[arg-type]
    satu = jalankan(kurasi.satu_menunggu(menunggu["butir"]["id_butir"], hari_ini=HARI))
    assert satu is not None and satu.status_keberlakuan == "dicabut"
    penemuan = PenemuanPostgres(SambunganPeran(PERAN_PENAYANGAN))  # type: ignore[arg-type]
    baris = jalankan(penemuan.baca_tayang(tayang["butir"]["id_butir"]))
    assert baris is not None and baris.ditarik_pada == T0


def test_status_berlaku_tidak_menarik(tmp_path: Path) -> None:
    dokumen = "dok-" + _acak()
    tayang = _entri(jenis="regulasi", status="berlaku", dokumen=dokumen)
    _jalan("isi", "--berkas", _berkas(tmp_path, [tayang]), penyaring=_loloskan)
    _tayangkan(tayang)
    kode, keluar, _ = _jalan("status", "--dokumen", dokumen, "--status", "berlaku")
    assert kode == 0
    assert "Butir tayang ditarik: 0" in keluar


@pytest.mark.parametrize(
    "argumen",
    [
        ("status", "--dokumen", "dok-x", "--status", "kedaluwarsa"),
        ("status", "--dokumen", " ", "--status", "dicabut"),
        ("status", "--dokumen", "3201234567890001", "--status", "dicabut"),
    ],
)
def test_status_berbentuk_salah_ditolak(argumen: tuple[str, ...]) -> None:
    kode, _, galat = _jalan(*argumen)
    assert kode == 2
    assert "Ditolak" in galat
    assert "3201234567890001" not in galat
