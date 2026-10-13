"""Uji jejak logbook *gold set* — T-6 fitur 040, R-03, R-06, R-07, K-6, AP-05.

Setiap uji menulis ke `tmp_path`. Logbook repositori tambah-saja dan tidak
dapat dikoreksi; pembekuan rekaan yang sampai ke sana tinggal selamanya.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.logbook.penulis import Buku, tambah_baris
from src.rag.evaluasi.gold_set import GoldSet, urai
from src.rag.evaluasi.jejak import (
    GalatPembekuan,
    VersiGoldSet,
    baca,
    bekukan,
    catat_putaran,
    hasil_l1,
    id_percobaan_terpakai,
    konfigurasi_l1,
    pembekuan,
    pembukaan_berikutnya,
)
from src.rag.evaluasi.pengukur import ukur
from tests.rag.evaluasi.rekaan import baris, berkas, komposisi_penuh
from tests.rag.evaluasi.test_pengukur import LAYAK, METADATA, SEGMEN, SumberPerKueri

from perkakas.pemeriksa.catatan_versi import periksa_catatan_versi

WAKTU = datetime(2026, 10, 13, 5, 0, tzinfo=UTC)
RAHASIA = "Pak Darmawan dari SDN 2 Cikoneng bertanya"


def _penuh() -> GoldSet:
    isi = komposisi_penuh()
    isi[0] = {**isi[0], "pertanyaan": RAHASIA}
    return urai(berkas(*isi))


def _versi(**ubah: object) -> VersiGoldSet:
    dasar: dict[str, object] = {
        "versi": "GS-REKAAN-1",
        "sidik": "sha256:" + "a" * 64,
        "dibekukan_pada": WAKTU,
        "jumlah": 3,
        "komposisi_jenis": {"A": 2, "D": 1},
        "komposisi_kategori": {"K1": 2, "tanpa-kategori": 1},
        "jumlah_bernomor_regulasi": 1,
        "pelaku": "Penanggung jawab substansi",
    }
    return VersiGoldSet.model_validate({**dasar, **ubah})


def test_versi_gold_set_sah() -> None:
    assert _versi().artefak == "gold-set"


@pytest.mark.parametrize(
    "ubah",
    [
        {"dibekukan_pada": datetime(2026, 10, 13, 5, 0)},
        {"komposisi_jenis": {"A": 2}},
        {"komposisi_kategori": {"K1": 4}},
        {"komposisi_jenis": {"A": 4, "D": -1}},
        {"jumlah_bernomor_regulasi": 4},
        {"sidik": "md5:abc"},
        {"pelaku": "  "},
        {"versi": ""},
        {"catatan": "bidang asing"},
    ],
)
def test_versi_gold_set_menolak(ubah: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _versi(**ubah)


def test_baca_berkas_tidak_ada_kosong_dan_baris_rusak_ditolak(tmp_path: Path) -> None:
    assert baca(tmp_path, Buku.L2) == ()
    tambah_baris(tmp_path, Buku.L2, {"artefak": "indeks", "versi_indeks": "x"})
    assert baca(tmp_path, Buku.L2)[0]["artefak"] == "indeks"
    with (tmp_path / Buku.L2.value).open("a", encoding="utf-8") as f:
        f.write("\n[1, 2]\n")
    with pytest.raises(ValueError, match="baris 3"):
        baca(tmp_path, Buku.L2)


def test_bekukan_mencatat_satu_baris_l2_tanpa_teks(tmp_path: Path) -> None:
    """R-03: sidik dan komposisi; R-07: tanpa teks pertanyaan."""
    gold = _penuh()
    v = bekukan(tmp_path, gold, versi="GS-REKAAN-1", pelaku="Uji", sekarang=WAKTU)
    (baris_l2,) = baca(tmp_path, Buku.L2)
    assert baris_l2["artefak"] == "gold-set"
    assert baris_l2["sidik"] == gold.sidik
    assert baris_l2["komposisi_jenis"] == {"A": 100, "B": 30, "C": 30, "D": 15, "E": 15, "F": 10}
    assert baris_l2["jumlah"] == 200
    assert "dicatat_pada" in baris_l2
    assert pembekuan(tmp_path, gold.sidik) == v
    assert pembekuan(tmp_path, "sha256:" + "b" * 64) is None
    assert "Darmawan" not in (tmp_path / Buku.L2.value).read_text(encoding="utf-8")


def test_bekukan_menolak_komposisi_menyimpang_tanpa_menulis(tmp_path: Path) -> None:
    """P-3 A (M-1): D-08 Bagian 5.1 persis, di fungsi pembekuan itu sendiri."""
    kurang = GoldSet(pertanyaan=_penuh().pertanyaan[1:])
    with pytest.raises(GalatPembekuan, match="A 99/100"):
        bekukan(tmp_path, kurang, versi="GS-1", pelaku="Uji", sekarang=WAKTU)
    assert baca(tmp_path, Buku.L2) == ()


def test_bekukan_menolak_sidik_beku_dan_versi_terpakai(tmp_path: Path) -> None:
    gold = _penuh()
    bekukan(tmp_path, gold, versi="GS-1", pelaku="Uji", sekarang=WAKTU)
    with pytest.raises(GalatPembekuan, match="GS-1"):
        bekukan(tmp_path, gold, versi="GS-2", pelaku="Uji", sekarang=WAKTU)
    isi = komposisi_penuh()
    isi[0] = {**isi[0], "pertanyaan": "REKAAN lain"}
    lain = urai(berkas(*isi))
    with pytest.raises(GalatPembekuan, match="sudah dipakai"):
        bekukan(tmp_path, lain, versi="GS-1", pelaku="Uji", sekarang=WAKTU)
    assert len(baca(tmp_path, Buku.L2)) == 1


def test_baris_gold_set_rusak_tidak_diabaikan(tmp_path: Path) -> None:
    tambah_baris(tmp_path, Buku.L2, {"artefak": "gold-set", "sidik": "sha256:x"})
    with pytest.raises(ValidationError):
        pembekuan(tmp_path, "sha256:x")


def _putaran():  # type: ignore[no-untyped-def]
    gold = urai(
        berkas(
            baris("q1", kunci=[("DOK-1", "Pasal 1")], pertanyaan=RAHASIA),
            baris("q2", kunci=[("DOK-3", "Pasal 1")], pertanyaan="REKAAN dua"),
            baris("d1", "D", pertanyaan="REKAAN enam"),
        )
    )
    sumber = SumberPerKueri({RAHASIA: ["u1", "m1"], "REKAAN dua": ["u2"]})
    return asyncio.run(ukur(gold, sumber, segmen=SEGMEN, layak=LAYAK, id_metadata=METADATA))


def test_hasil_l1_pengenal_dan_pecahan_tanpa_teks() -> None:
    hasil = hasil_l1(_putaran())
    teks = json.dumps(hasil, ensure_ascii=False)
    assert "Darmawan" not in teks
    assert "REKAAN dua" not in teks
    assert hasil["putusan"] == "GAGAL_KEPATUHAN"
    assert hasil["utama"]["recall_8"] == {
        "pembilang": "1",
        "penyebut": 2,
        "persen": "50,0%",
        "terhitung": True,
    }
    assert hasil["kebocoran"] == {"jumlah": 1, "segmen": ["m1"]}
    assert hasil["pertanyaan_gagal"] == [
        {
            "id": "q2",
            "jenis": "A",
            "peringkat_pertama": None,
            "kunci_luput": [
                {"urutan": 1, "dokumen": "DOK-3", "bagian": "Pasal 1", "sebab": "DI_LUAR_KORPUS"}
            ],
        }
    ]
    assert hasil["pertanyaan_bocor"] == [{"id": "q1", "segmen": ["m1"]}]
    assert set(hasil["per_jenis"]) == {"A", "B", "E", "F"}


def test_konfigurasi_l1_menyatakan_sumber_dan_k() -> None:
    """P-4 A: konfigurasi tercatat bersama hasilnya."""
    assert konfigurasi_l1(_putaran()) == {
        "sumber": "bm25",
        "indeks": "utama",
        "kedalaman": 20,
        "versi_penyemat": None,
        "k_recall": 8,
        "k_presisi": 5,
    }


def _catat(akar: Path, id_percobaan: str, **ubah: object) -> None:
    argumen: dict[str, object] = {
        "id_percobaan": id_percobaan,
        "beku": _versi(),
        "versi_kode": "abc1234",
        "versi_indeks": "utama:x;metadata:y",
        "versi_model": "belum-berlaku",
        "konfigurasi": {"sumber": "bm25"},
        "hasil": {"putusan": "DIUKUR"},
        "status": "berhasil",
        "catatan": "",
        "durasi_detik": 3,
    }
    catat_putaran(akar, **{**argumen, **ubah})  # type: ignore[arg-type]


def test_catat_putaran_lulus_pemeriksa_catatan_versi(tmp_path: Path) -> None:
    """C-09, R-06: kelima bidang versi; pemeriksa V-0x yang sama dengan
    `make check`."""
    _catat(tmp_path, "EXP-2026-001")
    (l1,) = baca(tmp_path, Buku.L1)
    assert l1["tugas"] == "pengambilan"
    assert l1["sidik_gold_set"] == _versi().sidik
    assert l1["versi_gold_set"] == "GS-REKAAN-1"
    assert l1["pembukaan_gold_set"] == 1
    assert l1["versi_indeks"] == "utama:x;metadata:y"
    for bidang in ("versi_skema_anotasi", "pembagian_data", "model_dasar", "perangkat_keras"):
        assert l1[bidang] == "belum-berlaku"
    akar = tmp_path / "repo"
    (akar / "logbook").mkdir(parents=True)
    (akar / "logbook" / Buku.L1.value).write_text(
        (tmp_path / Buku.L1.value).read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert periksa_catatan_versi(akar) == []


def test_pembukaan_dihitung_per_sidik(tmp_path: Path) -> None:
    """AP-05: berapa kali *gold set* ini dibuka, terbaca dari L1."""
    assert pembukaan_berikutnya(tmp_path, _versi().sidik) == 1
    _catat(tmp_path, "EXP-2026-001")
    _catat(tmp_path, "EXP-2026-002", status="gagal", catatan="ditolak peladen (OperationalError)")
    _catat(tmp_path, "EXP-2026-003", beku=_versi(sidik="sha256:" + "c" * 64))
    assert [r["pembukaan_gold_set"] for r in baca(tmp_path, Buku.L1)] == [1, 2, 1]
    assert pembukaan_berikutnya(tmp_path, _versi().sidik) == 3
    assert id_percobaan_terpakai(tmp_path, "EXP-2026-002")
    assert not id_percobaan_terpakai(tmp_path, "EXP-2026-004")


@pytest.mark.parametrize(
    ("id_percobaan", "ubah", "pesan"),
    [
        ("EXP-26-1", {}, "EXP-2026-nnn"),
        ("EXP-2026-001", {"status": "gagal", "catatan": " "}, "dugaan penyebab"),
        ("EXP-2026-001", {"status": "dibatalkan"}, "status"),
    ],
)
def test_catat_putaran_menolak(
    tmp_path: Path, id_percobaan: str, ubah: dict[str, object], pesan: str
) -> None:
    with pytest.raises(ValueError, match=pesan):
        _catat(tmp_path, id_percobaan, **ubah)
    assert baca(tmp_path, Buku.L1) == ()


def test_id_percobaan_kembar_ditolak(tmp_path: Path) -> None:
    _catat(tmp_path, "EXP-2026-001")
    with pytest.raises(ValueError, match="sudah tercatat"):
        _catat(tmp_path, "EXP-2026-001")
    assert len(baca(tmp_path, Buku.L1)) == 1
