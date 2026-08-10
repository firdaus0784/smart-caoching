"""Uji ekspor JSONL — B-1 fitur 016, R-09, R-12, D-03 Bagian 15.

D-03 Bagian 15 menetapkan bentuknya lengkap dengan contoh. Yang diuji di sini
bukan kemiripan dengan contoh itu melainkan **kesamaan nama bidang satu per
satu** — bidang yang namanya bergeser menghasilkan berkas yang terbaca wajar
dan tidak dapat dipakai perkakas mana pun tanpa disunting.

Dua hal yang lebih mudah luput daripada daftar bidangnya:

1. **Bendera yang tidak terkumpul ditulis `null`, bukan `[]`.** `[]` berarti
   diperiksa dan bersih. Pembedaan itu dibawa sepanjang jalan dari `impor_ls`
   sampai ke berkas ekspor, sebab berkas ekspor inilah yang dilampirkan naskah
   dan dibaca orang di luar tim.

2. **Dokumen beranotasi ganda tidak diekspor sebelum diadjudikasi.** D-03
   menetapkan satu baris mewakili satu dokumen, sedangkan dokumen beranotasi
   ganda punya dua putusan yang mungkin berbeda. Memilih salah satunya berarti
   membuang pekerjaan seorang anotator tanpa jejak, dan memilih yang pertama
   berarti memilihnya berdasarkan urutan penyimpanan Label Studio.
"""

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from src.nlp.anotasi.ekspor import GalatEkspor, SumberDokumen, ekspor_jsonl
from src.nlp.anotasi.impor_ls import impor
from src.nlp.anotasi.skema import VersiSkema

BAHAN = Path(__file__).resolve().parents[1] / "bahan" / "ekspor-label-studio-1.23.json"
VERSI = VersiSkema(mayor=1, minor=0)
KODE = {1: "A01", 2: "A02"}

BIDANG_D03 = (
    "doc_id",
    "sumber",
    "teks",
    "entitas",
    "kategori_utama",
    "kategori_sekunder",
    "anotator",
    "anotasi_ganda",
    "bendera",
    "versi_skema",
    "tanggal_anotasi",
)


def _muat() -> list[dict[str, Any]]:
    isi: list[dict[str, Any]] = json.loads(BAHAN.read_text(encoding="utf-8"))
    return isi


SUMBER = {
    "3": SumberDokumen(jenis="notulen_rapat", tahun=2025, instansi_penerbit="sekolah"),
    "4": SumberDokumen(jenis="regulasi", tahun=2025, instansi_penerbit="kementerian"),
}
TANGGAL = date(2026, 9, 14)


def _hasil(bendera_terkumpul: bool = True) -> Any:  # noqa: ANN401
    return impor(
        _muat(), versi_skema=VERSI, kode_anotator=KODE, bendera_terkumpul=bendera_terkumpul
    )


def _ekspor(tmp: Path, bendera_terkumpul: bool = True) -> tuple[list[dict[str, Any]], Any]:
    """`tmp` dipertahankan pada tanda tangan supaya ujinya tetap menulis
    berkas sungguhan — penulisannya pekerjaan pemanggil, dan uji yang tidak
    pernah menulis tidak menguji bentuk berkasnya."""
    hasil = ekspor_jsonl(_hasil(bendera_terkumpul), sumber=SUMBER, tanggal_anotasi=TANGGAL)
    berkas = tmp / "korpus.jsonl"
    berkas.write_text("".join(b + "\n" for b in hasil.baris), encoding="utf-8")
    baris = [json.loads(b) for b in berkas.read_text(encoding="utf-8").splitlines()]
    return baris, hasil


def test_hanya_dokumen_beranotasi_tunggal_yang_diekspor(tmp_path: Path) -> None:
    """Bahan memuat satu dokumen beranotasi ganda dan satu tunggal."""
    baris, laporan = _ekspor(tmp_path)
    assert len(baris) == 1
    assert laporan.tertunda_adjudikasi == ("3",)


def test_dokumen_beranotasi_ganda_dilaporkan_bukan_dibuang_diam_diam(tmp_path: Path) -> None:
    """**Uji terpenting berkas ini.**

    D-03 menetapkan satu baris mewakili satu dokumen. Dokumen beranotasi ganda
    punya dua putusan yang mungkin berbeda, dan memilih salah satunya berarti
    memilih berdasarkan urutan penyimpanan Label Studio — bukan berdasarkan
    adjudikasi.

    Yang wajib: ia tidak masuk berkas **dan** namanya dilaporkan. Dibuang tanpa
    laporan berarti korpus diam-diam kehilangan justru dokumen yang paling
    banyak dikerjakan orang.
    """
    _, laporan = _ekspor(tmp_path)
    assert "3" in laporan.tertunda_adjudikasi


@pytest.mark.parametrize("bidang", BIDANG_D03)
def test_setiap_bidang_d03_ada_dengan_nama_persis(tmp_path: Path, bidang: str) -> None:
    baris, _ = _ekspor(tmp_path)
    assert bidang in baris[0]


def test_entitas_berbentuk_d03(tmp_path: Path) -> None:
    baris, _ = _ekspor(tmp_path)
    entitas = baris[0]["entitas"]
    assert entitas
    for e in entitas:
        assert set(e) == {"mulai", "akhir", "label", "teks"}
        assert baris[0]["teks"][e["mulai"] : e["akhir"]] == e["teks"]


def test_sumber_berbentuk_d03(tmp_path: Path) -> None:
    baris, _ = _ekspor(tmp_path)
    assert set(baris[0]["sumber"]) == {"jenis", "tahun", "instansi_penerbit"}


def test_bendera_tak_terkumpul_ditulis_null(tmp_path: Path) -> None:
    """**`null`, bukan `[]` — dan pembedaan itu yang paling mudah hilang di
    sini.**

    Berkas ekspor inilah yang dilampirkan naskah dan dibaca orang di luar tim.
    `[]` di sana menyatakan korpus sudah diperiksa dan bersih dari `bocor_pii`.
    """
    baris, _ = _ekspor(tmp_path, bendera_terkumpul=False)
    assert baris[0]["bendera"] is None


def test_bendera_terkumpul_tanpa_temuan_ditulis_daftar_kosong(tmp_path: Path) -> None:
    baris, _ = _ekspor(tmp_path)
    assert baris[0]["bendera"] == []


def test_versi_skema_tertulis(tmp_path: Path) -> None:
    baris, _ = _ekspor(tmp_path)
    assert baris[0]["versi_skema"] == "1.0"


def test_anotator_memakai_kode_anonim(tmp_path: Path) -> None:
    """R-07 dijaga sampai ke berkasnya, bukan hanya sampai ke tipenya."""
    baris, _ = _ekspor(tmp_path)
    assert baris[0]["anotator"] in set(KODE.values())


def test_sumber_yang_tidak_ada_menggagalkan_ekspor(tmp_path: Path) -> None:
    """Sumber dokumen tidak dibawa Label Studio. Menebaknya — atau menuliskan
    objek kosong — menghasilkan korpus yang menyatakan asal yang tidak
    diketahui siapa pun."""
    with pytest.raises(GalatEkspor) as galat:
        ekspor_jsonl(_hasil(), sumber={}, tanggal_anotasi=TANGGAL)
    assert "sumber" in str(galat.value)


def test_kategori_sekunder_null_bila_tidak_ada(tmp_path: Path) -> None:
    """D-03 mencantumkan bidangnya; ketiadaannya ditulis `null`, bukan
    dihilangkan. Bidang yang hilang tidak dapat dibedakan dari versi penulis
    yang lebih tua."""
    baris, _ = _ekspor(tmp_path)
    assert baris[0]["kategori_sekunder"] is None


def test_satu_baris_per_dokumen(tmp_path: Path) -> None:
    berkas = tmp_path / "korpus.jsonl"
    hasil = ekspor_jsonl(_hasil(), sumber=SUMBER, tanggal_anotasi=TANGGAL)
    berkas.write_text("".join(b + "\n" for b in hasil.baris), encoding="utf-8")
    isi = berkas.read_text(encoding="utf-8")
    assert isi.endswith("\n")
    assert len(isi.strip().splitlines()) == 1


def test_modul_tidak_menyediakan_penulisan_berkas() -> None:
    """**Uji yang lahir dari pemeriksa C-17 yang menjatuhkan kode saya.**

    `src/nlp` berada pada jalur penjawaban, dan C-17 melarang akses tulis dari
    sana. Bentuk pertama modul ini menulis berkas sendiri; yang diperbaiki
    rancangannya, bukan pemeriksanya.

    `tulis` ada sebagai metode yang menolak supaya penambahannya kelak menjadi
    keputusan, bukan kelalaian.
    """
    hasil = ekspor_jsonl(_hasil(), sumber=SUMBER, tanggal_anotasi=TANGGAL)
    with pytest.raises(NotImplementedError) as galat:
        hasil.tulis(Path("/tmp/x.jsonl"))
    assert "C-17" in str(galat.value)


def test_dokumen_tanpa_putusan_kategori_tetap_membawa_anotator(tmp_path: Path) -> None:
    """Keadaan yang sah, dan tidak disebut `spec.md`.

    D-03 memisahkan anotasi entitas dari klasifikasi, sehingga dokumen yang
    hanya dianotasi entitasnya adalah keadaan yang wajar. Bidang `anotator`
    tetap wajib ada — tanpanya baris itu tidak dapat ditelusuri ke siapa pun,
    dan analisis pergeseran pemahaman D-03 Bagian 15 kehilangan satu titik.
    """
    isi = _muat()
    for tugas in isi:
        for anotasi in tugas["annotations"]:
            anotasi["result"] = [h for h in anotasi["result"] if h["type"] != "choices"]
    hasil = impor(isi, versi_skema=VERSI, kode_anotator=KODE, bendera_terkumpul=True)
    keluaran = ekspor_jsonl(hasil, sumber=SUMBER, tanggal_anotasi=TANGGAL)
    baris = [json.loads(b) for b in keluaran.baris]
    assert baris[0]["anotator"] in set(KODE.values())
    assert baris[0]["kategori_utama"] is None
