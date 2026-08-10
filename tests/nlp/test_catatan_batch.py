"""Uji catatan batch anotasi — C-4 fitur 003, R-15, C-09, D-03 Bagian 11.3.

D-03 Bagian 11.3 menyebut delapan hal yang wajib ada pada catatan tiap batch,
dan kalimat penutupnya menentukan taruhannya: catatan ini "masuk ke D-10 dan
menjadi bahan bagian metode naskah artikel". Bidang yang hilang di sini adalah
bidang yang tidak dapat dipulihkan berbulan kemudian — batchnya sudah lewat,
anotatornya sudah lupa, dan angkanya tidak dapat dihitung ulang tanpa data
yang mungkin sudah berubah.

Dua hal yang diuji, dan yang kedua yang lebih mudah luput:

1. **Kedelapan bidang ada.** Diuji sebagai daftar, bukan satu per satu pada
   uji terpisah, supaya bidang yang ditambahkan D-03 kelak menjatuhkan satu
   uji yang jelas alih-alih tidak menjatuhkan apa pun.

2. **Bidang yang belum terhitung tercatat sebagai belum terhitung.** Kappa
   yang tidak dapat dihitung wajib tertulis sebagai `terhitung: false` beserta
   alasannya — bukan sebagai `null` telanjang, dan sama sekali bukan sebagai
   0,0. `null` tidak dapat dibedakan dari cacat pada penulisnya, dan 0,0
   terbaca sebagai kesepakatan yang buruk. Keduanya masuk naskah sebagai hal
   yang berbeda dari kenyataannya.

`f1_per_label` dibangun bersama tugas ini meski tidak disebut B-4: D-03 Bagian
11.3 menuntut "F1 tepat dan longgar keseluruhan **dan per label**", sehingga
tanpanya catatan batch tidak dapat lengkap. Mencatatnya sebagai "belum
terhitung" akan memakai jalan keluar yang disediakan bagi batch yang kurang
bahan untuk menutupi fungsi yang belum ditulis.
"""

import json
from pathlib import Path

import pytest
from src.nlp.anotasi.batch import BatchAnotasi, DokumenAnotasi, StatusPraAnotasi, catat_batch
from src.nlp.anotasi.kesepakatan import (
    HasilKesepakatan,
    f1_per_label,
    f1_rentang,
    kappa_kategori,
    kappa_per_kategori,
)
from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas
from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema

VERSI = VersiSkema(mayor=1, minor=0)
TEKS = "Kepala sekolah menyusun RKAS tahun anggaran 2026 bersama komite sekolah."

DOKUMEN_L = LabelEntitas.DOKUMEN
JABATAN = LabelEntitas.JABATAN_PERAN

BIDANG_D03 = (
    "jumlah_dokumen",
    "jumlah_dokumen_anotasi_ganda",
    "kappa_keseluruhan",
    "kappa_per_kategori",
    "f1_tepat",
    "f1_longgar",
    "jumlah_kasus_adjudikasi",
    "kasus_baru_katalog",
)


def _r(mulai: int, akhir: int, label: LabelEntitas, anotator: str) -> RentangEntitas:
    return RentangEntitas(
        teks_kanonik=TEKS,
        mulai=mulai,
        akhir=akhir,
        label=label,
        versi_skema=VERSI,
        id_anotator=anotator,
    )


def _p(id_dokumen: str, kategori: KategoriMasalah, anotator: str) -> PutusanKategori:
    return PutusanKategori(
        id_dokumen=id_dokumen,
        kategori_utama=kategori,
        versi_skema=VERSI,
        id_anotator=anotator,
    )


def _batch() -> BatchAnotasi:
    return BatchAnotasi(
        id_batch="BATCH-2026-001",
        dokumen=(
            DokumenAnotasi(
                id_dokumen="dok0", status_pra_anotasi=StatusPraAnotasi.DENGAN_PRA_ANOTASI
            ),
            DokumenAnotasi(id_dokumen="dok1", status_pra_anotasi=StatusPraAnotasi.PEMBANDING),
        ),
    )


def _catat(
    akar: Path,
    *,
    kappa: HasilKesepakatan | None = None,
    rentang_a: list[RentangEntitas] | None = None,
    rentang_b: list[RentangEntitas] | None = None,
) -> dict[str, object]:
    a = rentang_a if rentang_a is not None else [_r(24, 28, DOKUMEN_L, "ant_a")]
    b = rentang_b if rentang_b is not None else [_r(24, 28, DOKUMEN_L, "ant_b")]
    putusan_a = [_p("dok0", KategoriMasalah.K5, "ant_a"), _p("dok1", KategoriMasalah.K1, "ant_a")]
    putusan_b = [_p("dok0", KategoriMasalah.K5, "ant_b"), _p("dok1", KategoriMasalah.K1, "ant_b")]

    catat_batch(
        akar,
        batch=_batch(),
        versi_skema=VERSI,
        jumlah_dokumen_anotasi_ganda=2,
        kappa_keseluruhan=kappa if kappa is not None else kappa_kategori(putusan_a, putusan_b),
        kappa_per_kategori=kappa_per_kategori(putusan_a, putusan_b),
        f1=f1_rentang(a, b),
        f1_per_label=f1_per_label(a, b),
        jumlah_kasus_adjudikasi=3,
        kasus_baru_katalog=("KS-27",),
    )
    hasil: dict[str, object] = json.loads(_baris(akar)[-1])
    return hasil


def _baris(akar: Path) -> list[str]:
    return (akar / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()


def test_kedelapan_bidang_d03_ada(tmp_path: Path) -> None:
    """**Uji yang dituntut `tasks.md`.**"""
    catatan = _catat(tmp_path)
    hilang = [b for b in BIDANG_D03 if b not in catatan]
    assert not hilang, f"bidang D-03 Bagian 11.3 yang hilang: {hilang}"


def test_satu_baris_per_batch(tmp_path: Path) -> None:
    """Ringkasan berkelompok menghapus waktu, dan waktu yang membedakan batch
    sebelum pedoman disegarkan dari batch sesudahnya."""
    _catat(tmp_path)
    assert len(_baris(tmp_path)) == 1
    _catat(tmp_path)
    assert len(_baris(tmp_path)) == 2


def test_kappa_yang_belum_terhitung_tercatat_sebagai_belum_terhitung(tmp_path: Path) -> None:
    """**Uji kedua yang dituntut `tasks.md`, dan yang lebih mudah luput.**

    `null` telanjang tidak dapat dibedakan dari cacat pada penulisnya; 0,0
    terbaca sebagai kesepakatan yang buruk. Keduanya masuk naskah sebagai hal
    yang berbeda dari kenyataannya.
    """
    belum = HasilKesepakatan.belum_terhitung("tidak ada dokumen yang keduanya anotasi")
    catatan = _catat(tmp_path, kappa=belum)
    kappa = catatan["kappa_keseluruhan"]
    assert isinstance(kappa, dict)
    assert kappa["terhitung"] is False
    assert kappa["nilai"] is None
    assert kappa["alasan"]


def test_nilai_yang_terhitung_tercatat_beserta_penanda_terhitung(tmp_path: Path) -> None:
    """Penanda `terhitung` ada pada kedua keadaan, bukan hanya pada yang belum.

    Penanda yang muncul hanya ketika ada masalah menuntut pembacanya
    menyimpulkan dari ketiadaan, dan ketiadaan pada berkas JSONL juga berarti
    versi penulis yang lebih tua.
    """
    catatan = _catat(tmp_path)
    kappa = catatan["kappa_keseluruhan"]
    assert isinstance(kappa, dict)
    assert kappa["terhitung"] is True
    assert kappa["nilai"] == pytest.approx(1.0)


def test_catatan_membawa_porsi_pembanding(tmp_path: Path) -> None:
    """C-3 menghitung porsinya dan tidak menilainya; nilainya di sini yang
    membuat porsi terlalu kecil terbaca seseorang."""
    catatan = _catat(tmp_path)
    assert catatan["porsi_pembanding"] == pytest.approx(0.5)


def test_catatan_membawa_versi_skema(tmp_path: Path) -> None:
    """C-09 dan FR-C08. Angka kesepakatan tanpa versi skema tidak dapat
    dibandingkan dengan angka batch lain."""
    catatan = _catat(tmp_path)
    assert catatan["versi_skema"] == "1.0"


def test_isi_dokumen_tidak_pernah_masuk_catatan(tmp_path: Path) -> None:
    """Dokumen batch anotasi memuat teks sekolah sungguhan. Catatan batch
    membawa angka dan pengenal, tidak membawa isi."""
    catatan = _catat(tmp_path)
    assert TEKS not in json.dumps(catatan, ensure_ascii=False)


def test_f1_per_label_hanya_melaporkan_label_yang_muncul() -> None:
    """Mengikuti `kappa_per_kategori`: melaporkan kedelapan label menghasilkan
    tujuh baris kosong, dan pembacanya berhenti membaca."""
    a = [_r(24, 28, DOKUMEN_L, "ant_a"), _r(0, 14, JABATAN, "ant_a")]
    b = [_r(24, 28, DOKUMEN_L, "ant_b"), _r(0, 14, JABATAN, "ant_b")]
    assert set(f1_per_label(a, b)) == {DOKUMEN_L, JABATAN}


def test_f1_per_label_kosong_ketika_tidak_ada_bahan() -> None:
    """Peta kosong, bukan peta berisi delapan hasil yang belum terhitung.

    Yang kedua terbaca sebagai "sudah diperiksa dan hasilnya nihil", padahal
    tidak ada yang diperiksa sama sekali.
    """
    assert f1_per_label([], []) == {}


def test_f1_per_label_memisahkan_label_yang_buruk_dari_yang_baik() -> None:
    """**Alasan fungsi ini ada.**

    F1 keseluruhan yang sedang dapat berasal dari dua label yang baik dan satu
    yang kacau. Hanya pemisahannya yang memberi tahu label mana yang
    definisinya perlu dipertajam — sama dengan `kappa_per_kategori` bagi
    kategori.
    """
    a = [_r(24, 28, DOKUMEN_L, "ant_a"), _r(0, 14, JABATAN, "ant_a")]
    b = [_r(24, 28, DOKUMEN_L, "ant_b"), _r(0, 6, JABATAN, "ant_b")]
    hasil = f1_per_label(a, b)
    assert hasil[DOKUMEN_L].tepat.nilai == pytest.approx(1.0)
    assert hasil[JABATAN].tepat.nilai == pytest.approx(0.0)


def test_f1_per_label_menolak_putusan_kategori() -> None:
    """Sifat yang sama dengan `f1_rentang` — lihat B-5."""
    putusan = [_p("dok0", KategoriMasalah.K5, "ant_a")]
    with pytest.raises(AttributeError):
        f1_per_label(putusan, putusan)  # type: ignore[arg-type]
