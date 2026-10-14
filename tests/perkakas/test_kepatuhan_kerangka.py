"""Kerangka penjalan uji kepatuhan U5 — T-2 fitur 042, R-01, R-02, R-05, R-06.

Daftar UK milik D-08 Bagian 8 dan D-13 Bagian 8; uji membacanya dari sana.
Pemeriksa di sini ganda uji: kerangka diuji terpisah dari pemeriksaan
basis data, dalam proses, dan API (T-3 s.d. T-5).
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pytest
from src.logbook.penulis import Buku, tambah_baris
from src.rag.evaluasi.jejak import baca

from perkakas.kepatuhan.__main__ import konteks_dari_lingkungan, utama
from perkakas.kepatuhan.daftar import BELUM_BAHAN, KODE_UK
from perkakas.kepatuhan.hasil import HasilUK, Keadaan, KonfigurasiApi, Konteks, keseluruhan
from perkakas.pemeriksa.catatan_versi import periksa_catatan_versi

AKAR = Path(__file__).resolve().parents[2]
KUKI = "kuki-rahasia-" + "x" * 24


def _kode_tabel(dokumen: str, judul: str, akhir: str) -> list[str]:
    teks = (AKAR / "docs" / dokumen).read_text(encoding="utf-8")
    bagian = teks.split(judul, 1)[1].split(akhir, 1)[0]
    return re.findall(r"^\| (UK-\d\d) \|", bagian, flags=re.MULTILINE)


def test_lima_belas_uk_dibaca_dari_d08_dan_d13() -> None:
    """R-01 (M-4): tidak ada UK yang hilang dari daftar."""
    d08 = _kode_tabel(
        "D08.md", "## 8. Pengujian Kepatuhan dan Keamanan (U5)", "**Aturan pelaksanaan"
    )
    d13 = _kode_tabel("D13.md", "## 8. Uji Keamanan Tambahan", "\n---")
    assert tuple(d08 + d13) == KODE_UK
    assert len(KODE_UK) == 15


def test_empat_uk_belum_dapat_diperiksa_sesuai_d08() -> None:
    """P-6 A: UK-01, UK-03, UK-06, UK-11 menunggu bahannya."""
    assert set(BELUM_BAHAN) == {"UK-01", "UK-03", "UK-06", "UK-11"}
    aturan = (
        (AKAR / "docs" / "D08.md")
        .read_text(encoding="utf-8")
        .split("**Aturan pelaksanaan.** Ditambahkan 14 Oktober", 1)[1]
    )
    (baris,) = [b for b in aturan.splitlines() if b.startswith("- **Belum dapat diperiksa**")]
    for kode in BELUM_BAHAN:
        assert kode in baris
    assert all(BELUM_BAHAN.values())


def _hasil(keadaan: dict[str, Keadaan]) -> list[HasilUK]:
    return [HasilUK(k, keadaan.get(k, Keadaan.LULUS), ("rincian uji",)) for k in KODE_UK]


def test_keseluruhan_lolos_hanya_bila_kelima_belasnya_lulus() -> None:
    """R-02 (M-3): belum dapat diperiksa tidak pernah terbaca lulus."""
    assert keseluruhan(_hasil({})) is Keadaan.LULUS
    assert keseluruhan(_hasil({"UK-01": Keadaan.BELUM})) is Keadaan.BELUM
    assert keseluruhan(_hasil({"UK-01": Keadaan.BELUM, "UK-02": Keadaan.GAGAL})) is Keadaan.GAGAL


class Jalankan:
    def __init__(self, akar: Path, pemeriksa: dict, api: KonfigurasiApi | None = None) -> None:  # type: ignore[type-arg]
        self.logbook = akar / "logbook"
        self.pemeriksa = pemeriksa
        self.api = api

    def __call__(self, *argumen: str) -> tuple[int, str, str]:
        keluar, galat = io.StringIO(), io.StringIO()

        def konteks() -> Konteks:
            return Konteks(buka=None, api=self.api, akar_repo=AKAR)  # type: ignore[arg-type]

        kode = utama(
            list(argumen),
            konteks=konteks,
            pemeriksa=self.pemeriksa,
            keluar=keluar,
            galat=galat,
            akar_logbook=self.logbook,
            versi_kode=lambda: "abc123def456",
        )
        return kode, keluar.getvalue(), galat.getvalue()


def _lulus(kode: str):  # type: ignore[no-untyped-def]
    async def periksa(_: Konteks) -> HasilUK:
        return HasilUK(kode, Keadaan.LULUS, (f"{kode} uji",))

    return periksa


def _semua_lulus() -> dict:  # type: ignore[type-arg]
    return {k: _lulus(k) for k in KODE_UK if k not in BELUM_BAHAN}


def test_putaran_tanpa_gagal_tetapi_belum_lengkap_berkode_4(tmp_path: Path) -> None:
    j = Jalankan(tmp_path, _semua_lulus(), KonfigurasiApi("http://127.0.0.1:9", "uji-001", KUKI))
    kode, keluar, _ = j("jalankan", "--lingkungan", "pementasan", "--id-percobaan", "EXP-2026-801")
    assert kode == 4
    baris = [b for b in keluar.splitlines() if re.match(r"UK-\d\d ", b)]
    assert [b[:5] for b in baris] == list(KODE_UK)
    assert "UK-01 belum dapat diperiksa" in keluar
    assert "UK-02 lulus" in keluar
    assert "Tidak lolos" in keluar
    assert KUKI not in keluar


def test_satu_gagal_berkode_1_dan_l1_berstatus_gagal(tmp_path: Path) -> None:
    """R-06 (M-7): putaran yang gagal pun tercatat."""
    pemeriksa = _semua_lulus()

    async def gagal(_: Konteks) -> HasilUK:
        return HasilUK("UK-02", Keadaan.GAGAL, ("peran_x: pernyataan berhasil",))

    pemeriksa["UK-02"] = gagal
    j = Jalankan(tmp_path, pemeriksa, KonfigurasiApi("http://127.0.0.1:9", "uji-001", KUKI))
    kode, _, _ = j("jalankan", "--lingkungan", "produksi", "--id-percobaan", "EXP-2026-802")
    assert kode == 1
    (l1,) = baca(j.logbook, Buku.L1)
    assert l1["tugas"] == "kepatuhan"
    assert l1["lingkungan"] == "produksi"
    assert l1["status"] == "gagal"
    assert "UK-02" in str(l1["catatan"])
    assert l1["hasil"]["UK-02"] == {"keadaan": "gagal", "rincian": ["peran_x: pernyataan berhasil"]}  # type: ignore[index]
    assert l1["hasil"]["UK-11"]["keadaan"] == "belum dapat diperiksa"  # type: ignore[index]
    assert l1["versi_kode"] == "abc123def456"
    assert KUKI not in json.dumps(l1)
    akar = tmp_path / "repo"
    (akar / "logbook").mkdir(parents=True)
    (akar / "logbook" / Buku.L1.value).write_text(
        (j.logbook / Buku.L1.value).read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert periksa_catatan_versi(akar) == []


def test_pemeriksa_yang_melempar_dicatat_gagal_tanpa_pesannya(tmp_path: Path) -> None:
    pemeriksa = _semua_lulus()

    async def melempar(_: Konteks) -> HasilUK:
        raise RuntimeError("pesan yang mungkin memuat rahasia")

    pemeriksa["UK-09"] = melempar
    j = Jalankan(tmp_path, pemeriksa)
    kode, keluar, _ = j("jalankan", "--lingkungan", "uji", "--id-percobaan", "EXP-2026-803")
    assert kode == 1
    assert "UK-09 gagal" in keluar and "RuntimeError" in keluar
    assert "rahasia" not in keluar


def test_pemeriksa_belum_terpasang_belum_dapat_diperiksa(tmp_path: Path) -> None:
    j = Jalankan(tmp_path, {})
    kode, keluar, _ = j("jalankan", "--lingkungan", "uji", "--id-percobaan", "EXP-2026-804")
    assert kode == 4
    assert "UK-02 belum dapat diperiksa" in keluar


def test_konfigurasi_api_tidak_menampilkan_kuki() -> None:
    """R-05 (M-6)."""
    api = KonfigurasiApi("http://127.0.0.1:9", "uji-001", KUKI)
    assert KUKI not in repr(api) and KUKI not in str(api)


@pytest.mark.parametrize(
    "argumen",
    [
        (),
        ("jalankan", "--lingkungan", "uji"),
        ("jalankan", "--lingkungan", "Produksi Utama", "--id-percobaan", "EXP-2026-805"),
        ("jalankan", "--lingkungan", "uji", "--id-percobaan", "EXP-26-1"),
    ],
)
def test_masukan_tidak_sah_berkode_2_tanpa_l1(tmp_path: Path, argumen: tuple[str, ...]) -> None:
    j = Jalankan(tmp_path, _semua_lulus())
    assert j(*argumen)[0] == 2
    assert baca(j.logbook, Buku.L1) == ()


def test_id_percobaan_terpakai_berkode_2(tmp_path: Path) -> None:
    j = Jalankan(tmp_path, _semua_lulus())
    tambah_baris(j.logbook, Buku.L1, {"id_percobaan": "EXP-2026-806"})
    kode, _, galat = j("jalankan", "--lingkungan", "uji", "--id-percobaan", "EXP-2026-806")
    assert kode == 2 and "sudah tercatat" in galat
    assert len(baca(j.logbook, Buku.L1)) == 1


def test_konteks_api_hanya_bila_ketiganya_ada() -> None:
    lengkap = {
        "KEPATUHAN_API": "http://127.0.0.1:9",
        "KEPATUHAN_AKUN": "uji-001",
        "KEPATUHAN_KUKI": KUKI,
    }
    api = konteks_dari_lingkungan(lengkap, AKAR).api
    assert api is not None and api.akun == "uji-001" and api.kuki == KUKI
    for hilang in lengkap:
        sebagian = {k: v for k, v in lengkap.items() if k != hilang}
        assert konteks_dari_lingkungan(sebagian, AKAR).api is None
