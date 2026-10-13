"""Perkakas evaluasi pengambilan — T-7 fitur 040, R-01 s.d. R-08, K-7.

Korpus PostgreSQL dibaca sebagai peran pemuat fitur 039 sungguhan:
`peran_pemanggil_llm` bagi indeks utama, `peran_penjawaban` bagi indeks
metadata. Isi korpus ditanam pengelola dan dibuat-buat; *gold set* rekaan.
Logbook selalu akar sementara — logbook repositori tidak pernah disentuh.
"""

from __future__ import annotations

import io
import json
import logging
import re
import secrets
from datetime import UTC, datetime
from pathlib import Path

import pytest
from src.kamus.segmen import IndeksTujuan
from src.logbook.penulis import Buku, tambah_baris
from src.rag.evaluasi.gold_set import JenisPertanyaan, urai
from src.rag.evaluasi.jejak import VersiGoldSet, baca
from tests.api.test_penjawab_korpus import _kata_unik, _pengelola, _sql, _tanam
from tests.penyimpanan.test_akun import SambunganPeran
from tests.rag.evaluasi.rekaan import baris, berkas, komposisi_penuh

import perkakas.evaluasi as evaluasi
from perkakas.evaluasi import utama

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA
RAHASIA = "Bu Ratnasari kepala SDN 4 Jatinunggal bertanya"


class Jalankan:
    def __init__(self, akar: Path, peran_paksa: str | None = None) -> None:
        self.akar = akar
        self.logbook = akar / "logbook-sementara"
        self.repo = akar / "repo-tiruan"
        self.repo.mkdir(exist_ok=True)
        self.peran: list[str] = []
        self._paksa = peran_paksa

    def __call__(self, *argumen: str) -> tuple[int, str, str]:
        keluar, galat = io.StringIO(), io.StringIO()

        def sambung(peran: str) -> SambunganPeran:
            self.peran.append(peran)
            return SambunganPeran(self._paksa or peran)

        kode = utama(
            list(argumen),
            sambung=sambung,  # type: ignore[arg-type]
            keluar=keluar,
            galat=galat,
            akar_logbook=self.logbook,
            akar_repo=self.repo,
            versi_kode=lambda: "abc123def456",
        )
        return kode, keluar.getvalue(), galat.getvalue()

    def tulis(self, nama: str, teks: str) -> str:
        jalur = self.akar / nama
        jalur.write_text(teks, encoding="utf-8")
        return str(jalur)


def _korpus() -> tuple[str, str, str]:
    """Dua dokumen utama dan satu metadata, berkata unik."""
    kata = _kata_unik()
    awal = "d40e-" + secrets.token_hex(3)
    _tanam(f"{awal}-a", UTAMA, f"Kepala sekolah menyusun {kata} rencana kerja.")
    _tanam(f"{awal}-b", UTAMA, f"Komite sekolah menetapkan {kata} iuran.")
    _tanam(f"{awal}-m", METADATA, f"Kajian {kata} rencana.", lisensi="CC-BY-NC 4.0")
    return kata, awal, f"{awal}-m"


def _kecil(kata: str, awal: str) -> str:
    return berkas(
        baris("q1", kunci=[(f"{awal}-a", "Pasal 1")], pertanyaan=f"{RAHASIA} {kata} rencana kerja"),
        baris(
            "q2",
            "F",
            kunci=[(f"{awal}-a", "Pasal 1"), (f"{awal}-b", "Pasal 1")],
            pertanyaan=f"REKAAN {kata} iuran komite",
        ),
        baris("q3", kunci=[(f"{awal}-m", "Pasal 1")], pertanyaan=f"REKAAN {kata} kajian"),
        baris("d1", "D", pertanyaan="REKAAN resep rendang"),
    )


def _bekukan_langsung(logbook: Path, teks: str) -> VersiGoldSet:
    """Baris L2 bagi *gold set* kecil — menguji `ukur`, bukan komposisi."""
    gold = urai(teks)
    v = VersiGoldSet(
        versi="GS-REKAAN-KECIL",
        sidik=gold.sidik,
        dibekukan_pada=datetime(2026, 10, 13, tzinfo=UTC),
        jumlah=len(gold.pertanyaan),
        komposisi_jenis={j.value: n for j, n in gold.komposisi().items()},
        komposisi_kategori=gold.komposisi_kategori(),
        jumlah_bernomor_regulasi=gold.jumlah_bernomor_regulasi(),
        pelaku="Uji",
    )
    tambah_baris(logbook, Buku.L2, v.model_dump(mode="json"))
    return v


def _tanpa_teks(*isi: str) -> None:
    for t in isi:
        assert "Ratnasari" not in t
        assert "Jatinunggal" not in t
        assert "Kepala sekolah menyusun" not in t


def test_akar_repo_bawaan_adalah_repositori_dan_logbook_di_dalamnya() -> None:
    akar = Path(__file__).resolve().parents[2]
    assert akar == evaluasi.AKAR_REPO
    assert akar / "logbook" == evaluasi.AKAR_LOGBOOK


def test_periksa_sebagai_peran_pemuat_tanpa_teks(tmp_path: Path) -> None:
    """R-02, R-07, R-08: dua peran pemuat; komposisi dibandingkan dengan D-08."""
    kata, awal, _ = _korpus()
    j = Jalankan(tmp_path)
    kode, keluar, galat = j("periksa", "--berkas", j.tulis("gs.jsonl", _kecil(kata, awal)))
    assert kode == 0, galat
    assert j.peran == ["peran_pemanggil_llm", "peran_penjawaban"]
    assert urai(_kecil(kata, awal)).sidik in keluar
    assert "A 2/100" in keluar and "F 1/10" in keluar
    assert "Dapat dibekukan: tidak" in keluar
    _tanpa_teks(keluar, galat)
    assert baca(j.logbook, Buku.L2) == ()


def test_periksa_kunci_di_luar_korpus_dengan_pengenal(tmp_path: Path) -> None:
    kata, awal, _ = _korpus()
    teks = _kecil(kata, awal) + berkas(
        baris("q9", kunci=[(f"{awal}-tidak-ada", "Pasal 1")], pertanyaan=RAHASIA),
        baris("q8", kunci=[(f"{awal}-a", "Pasal 7")], pertanyaan=RAHASIA),
    )
    j = Jalankan(tmp_path)
    kode, keluar, galat = j("periksa", "--berkas", j.tulis("gs.jsonl", teks))
    assert kode == 2
    semua = keluar + galat
    assert "q9 kunci 1: dokumen di luar korpus" in semua
    assert "q8 kunci 1: bagian tanpa segmen" in semua
    _tanpa_teks(semua)


def test_bentuk_tidak_sah_ditolak_sebelum_menyambung(tmp_path: Path) -> None:
    j = Jalankan(tmp_path)
    jalur = j.tulis("gs.jsonl", berkas({**baris("q1", pertanyaan=RAHASIA), "jenis": "G"}))
    kode, keluar, galat = j("periksa", "--berkas", jalur)
    assert kode == 2 and "baris 1" in galat
    assert j.peran == []
    _tanpa_teks(keluar, galat)


def test_berkas_bukan_utf8_dan_tidak_ada_ditolak(tmp_path: Path) -> None:
    j = Jalankan(tmp_path)
    jalur = tmp_path / "gs.jsonl"
    jalur.write_bytes(b"\xff\xfe\x00rusak")
    assert j("periksa", "--berkas", str(jalur))[0] == 2
    assert j("periksa", "--berkas", str(tmp_path / "tidak-ada.jsonl"))[0] == 2
    assert j.peran == []


def test_berkas_di_dalam_repositori_ditolak(tmp_path: Path) -> None:
    """R-01 (M-12): ditolak sebelum dibaca dan sebelum menyambung."""
    j = Jalankan(tmp_path)
    (j.repo / "data").mkdir()
    jalur = j.repo / "data" / "gs.jsonl"
    jalur.write_text(berkas(baris("q1")), encoding="utf-8")
    for perintah in (
        ("periksa",),
        ("bekukan", "--versi", "GS-1", "--pelaku", "Uji"),
        ("ukur", "--id-percobaan", "EXP-2026-001"),
    ):
        kode, _, galat = j(perintah[0], "--berkas", str(jalur), *perintah[1:])
        assert kode == 2
        assert "repositori" in galat
    tautan = tmp_path / "tautan.jsonl"
    tautan.symlink_to(jalur)
    assert j("periksa", "--berkas", str(tautan))[0] == 2
    assert j.peran == []


def test_bekukan_komposisi_d08_satu_baris_l2(tmp_path: Path) -> None:
    """R-03: sidik dan komposisi ke L2; pembekuan kedua ditolak."""
    kata, awal, _ = _korpus()
    dua = [(f"{awal}-a", "Pasal 1"), (f"{awal}-b", "Pasal 1")]
    isi = komposisi_penuh(kunci={j: dua for j in JenisPertanyaan if j.value in "ABEF"})
    isi[0] = {**isi[0], "pertanyaan": f"{RAHASIA} {kata}"}
    j = Jalankan(tmp_path)
    jalur = j.tulis("gs.jsonl", berkas(*isi))
    kode, keluar, galat = j("bekukan", "--berkas", jalur, "--versi", "GS-1", "--pelaku", "Uji")
    assert kode == 0, galat
    (l2,) = baca(j.logbook, Buku.L2)
    assert l2["artefak"] == "gold-set" and l2["versi"] == "GS-1"
    assert l2["sidik"] in keluar
    kode, _, galat = j("bekukan", "--berkas", jalur, "--versi", "GS-2", "--pelaku", "Uji")
    assert kode == 2 and "sudah beku" in galat
    assert len(baca(j.logbook, Buku.L2)) == 1
    _tanpa_teks(keluar, galat, (j.logbook / Buku.L2.value).read_text(encoding="utf-8"))


def test_bekukan_komposisi_menyimpang_ditolak(tmp_path: Path) -> None:
    """P-3 A (M-1)."""
    kata, awal, _ = _korpus()
    j = Jalankan(tmp_path)
    jalur = j.tulis("gs.jsonl", _kecil(kata, awal))
    kode, _, galat = j("bekukan", "--berkas", jalur, "--versi", "GS-1", "--pelaku", "Uji")
    assert kode == 2
    assert "D-08 Bagian 5.1" in galat
    assert baca(j.logbook, Buku.L2) == ()


def test_ukur_belum_beku_ditolak_tanpa_l1_dan_tanpa_menyambung(tmp_path: Path) -> None:
    """R-03 (M-2): berkas yang belum beku belum menjadi bahan percobaan."""
    j = Jalankan(tmp_path)
    jalur = j.tulis("gs.jsonl", berkas(baris("q1")))
    kode, _, galat = j("ukur", "--berkas", jalur, "--id-percobaan", "EXP-2026-001")
    assert kode == 2 and "belum beku" in galat
    assert j.peran == []
    assert baca(j.logbook, Buku.L1) == ()


def test_ukur_berhasil_l1_dan_laporan_tanpa_teks(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """R-04 s.d. R-08 (M-10): konfigurasi dinyatakan; tidak menyatakan U3
    lulus; L1 berbidang lengkap; pertanyaan gagal disebut pengenalnya."""
    caplog.set_level(logging.DEBUG)
    kata, awal, id_m = _korpus()
    j = Jalankan(tmp_path)
    teks = _kecil(kata, awal)
    beku = _bekukan_langsung(j.logbook, teks)
    kode, keluar, galat = j(
        "ukur", "--berkas", j.tulis("gs.jsonl", teks), "--id-percobaan", "EXP-2026-007"
    )
    assert kode == 0, galat
    assert j.peran == ["peran_pemanggil_llm", "peran_penjawaban"]
    assert "sumber bm25, indeks utama, kedalaman 20" in keluar
    assert "tidak diterapkan" in keluar and "lulus" not in keluar
    assert "Recall@8 (jenis A): 50,0% — 1 dari 2" in keluar
    assert "Kebocoran indeks: 0 segmen" in keluar
    assert re.search(r"q3 \(A\): kunci 1 .*bukan bahan indeks utama", keluar)
    assert "pembukaan ke-1" in keluar
    (l1,) = baca(j.logbook, Buku.L1)
    assert l1["id_percobaan"] == "EXP-2026-007"
    assert l1["status"] == "berhasil"
    assert l1["versi_kode"] == "abc123def456"
    assert l1["sidik_gold_set"] == beku.sidik
    assert str(l1["versi_indeks"]).startswith("utama:")
    assert l1["konfigurasi"]["sumber"] == "bm25"  # type: ignore[index]
    assert l1["hasil"]["utama"]["recall_8"]["penyebut"] == 2  # type: ignore[index]
    assert id_m not in json.dumps(l1["hasil"]["kebocoran"])  # type: ignore[index]
    _tanpa_teks(keluar, galat, json.dumps(l1, ensure_ascii=False))
    _tanpa_teks(*(c.getMessage() for c in caplog.records))
    kode, keluar, _ = j(
        "ukur", "--berkas", str(tmp_path / "gs.jsonl"), "--id-percobaan", "EXP-2026-008"
    )
    assert kode == 0 and "pembukaan ke-2" in keluar


def test_ukur_ditolak_peladen_tercatat_gagal(tmp_path: Path) -> None:
    """R-06 (M-11): putaran yang gagal tetap tercatat beserta dugaannya."""
    j = Jalankan(tmp_path, peran_paksa="peran_penyematan")
    teks = berkas(baris("q1", pertanyaan=RAHASIA))
    _bekukan_langsung(j.logbook, teks)
    kode, keluar, galat = j(
        "ukur", "--berkas", j.tulis("gs.jsonl", teks), "--id-percobaan", "EXP-2026-001"
    )
    assert kode == 1
    assert "EXP-2026-001" in galat
    (l1,) = baca(j.logbook, Buku.L1)
    assert l1["status"] == "gagal"
    assert "ditolak peladen" in str(l1["catatan"])
    assert l1["versi_indeks"] == "tidak-terbaca"
    _tanpa_teks(keluar, galat, json.dumps(l1, ensure_ascii=False))


def test_ukur_kebocoran_gagal_kepatuhan_kode_3(tmp_path: Path) -> None:
    """R-05, KL-01: segmen yang sama berada di kedua indeks."""
    kata, awal, _ = _korpus()
    id_segmen = f"{awal}-a:0001"
    _pengelola(
        "insert into indeks_metadata.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
        f"anonimisasi_terverifikasi, penanda_bagian) values ({_sql(id_segmen)}, "
        f"{_sql(awal + '-a')}, 'Salinan bocor.', 'tertutup', true, 'Pasal 1')"
    )
    j = Jalankan(tmp_path)
    teks = _kecil(kata, awal)
    _bekukan_langsung(j.logbook, teks)
    try:
        kode, keluar, galat = j(
            "ukur", "--berkas", j.tulis("gs.jsonl", teks), "--id-percobaan", "EXP-2026-001"
        )
    finally:
        _pengelola(f"delete from indeks_metadata.segmen_teks where id_segmen = {_sql(id_segmen)}")
    assert kode == 3, galat
    assert "gagal kepatuhan KL-01" in keluar
    assert id_segmen in keluar
    (l1,) = baca(j.logbook, Buku.L1)
    assert l1["status"] == "gagal"
    assert "kebocoran" in str(l1["catatan"])


@pytest.mark.parametrize("id_percobaan", ["EXP-1", "exp-2026-001", "EXP-2026-0001"])
def test_id_percobaan_tidak_sah_ditolak_sebelum_menyambung(
    tmp_path: Path, id_percobaan: str
) -> None:
    j = Jalankan(tmp_path)
    teks = berkas(baris("q1"))
    _bekukan_langsung(j.logbook, teks)
    kode, _, galat = j(
        "ukur", "--berkas", j.tulis("gs.jsonl", teks), "--id-percobaan", id_percobaan
    )
    assert kode == 2 and "EXP-2026-nnn" in galat
    assert j.peran == []


def test_id_percobaan_terpakai_ditolak_sebelum_menyambung(tmp_path: Path) -> None:
    j = Jalankan(tmp_path)
    teks = berkas(baris("q1"))
    _bekukan_langsung(j.logbook, teks)
    tambah_baris(j.logbook, Buku.L1, {"id_percobaan": "EXP-2026-001"})
    kode, _, galat = j(
        "ukur", "--berkas", j.tulis("gs.jsonl", teks), "--id-percobaan", "EXP-2026-001"
    )
    assert kode == 2 and "sudah tercatat" in galat
    assert j.peran == []


@pytest.mark.parametrize("argumen", [(), ("hapus",), ("periksa",), ("bekukan", "--berkas", "x")])
def test_argumen_tidak_sah(tmp_path: Path, argumen: tuple[str, ...]) -> None:
    j = Jalankan(tmp_path)
    assert j(*argumen)[0] == 2
    assert j.peran == []


def test_versi_kode_git_berbentuk_penanda_commit() -> None:
    assert re.fullmatch(r"[0-9a-f]{12}(\+ubahan)?", evaluasi.versi_kode_git())
