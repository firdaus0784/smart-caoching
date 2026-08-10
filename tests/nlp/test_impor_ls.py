"""Uji impor ekspor Label Studio menjadi tipe kita — A-2 fitur 016, R-01, R-03.

Seluruhnya berjalan atas `tests/bahan/ekspor-label-studio-1.23.json`, berkas
yang dihasilkan Label Studio 1.23.0 sungguhan dengan dua akun anotator
(KB-023). Uji terhadap bentuk yang disusun uji hanya membuktikan pengurainya
cocok dengan dugaan penulisnya.

Yang dijaga di sini: **hasil impor adalah tipe milik fitur 003, bukan bentuk
Label Studio yang diteruskan.** Bentuk yang diteruskan akan membuat seluruh
kode berikutnya mengenal `from_name`, `to_name`, dan `value` — dan ketika
perangkatnya naik versi, yang berubah bukan satu modul melainkan semuanya.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from src.nlp.anotasi.impor_ls import GalatImpor, impor
from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas
from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema

BAHAN = Path(__file__).resolve().parents[1] / "bahan" / "ekspor-label-studio-1.23.json"
VERSI = VersiSkema(mayor=1, minor=0)
KODE = {1: "A01", 2: "A02"}


def _muat() -> list[dict[str, Any]]:
    isi: list[dict[str, Any]] = json.loads(BAHAN.read_text(encoding="utf-8"))
    return isi


def _impor(isi: list[dict[str, Any]] | None = None) -> Any:
    return impor(
        isi if isi is not None else _muat(),
        versi_skema=VERSI,
        kode_anotator=KODE,
        bendera_terkumpul=True,
    )


def test_dua_dokumen_terbaca() -> None:
    assert len(_impor().dokumen) == 2


def test_rentang_menjadi_tipe_kita() -> None:
    """R-01. Bukan `dict`, bukan bentuk Label Studio yang diteruskan."""
    rentang = _impor().dokumen[0].rentang
    assert rentang
    assert all(isinstance(r, RentangEntitas) for r in rentang)


def test_putusan_menjadi_tipe_kita() -> None:
    putusan = _impor().dokumen[0].putusan
    assert putusan
    assert all(isinstance(p, PutusanKategori) for p in putusan)


def test_rentang_membawa_indeks_karakter_yang_cocok() -> None:
    """**R-03, dan inti C-10.**

    `RentangEntitas` sendiri sudah menolak rentang yang tidak cocok (R-06
    fitur 003). Uji ini memastikan indeks Label Studio dipakai apa adanya —
    bukan digeser, bukan diterjemahkan dari token.
    """
    dokumen = _impor().dokumen[0]
    for r in dokumen.rentang:
        assert dokumen.teks[r.mulai : r.akhir] == r.teks_rentang


def test_rentang_pertama_sesuai_bahan() -> None:
    """Nilai tertulis, bukan dihitung ulang dari berkasnya.

    Uji yang membaca nilai harapannya dari berkas yang sama dengan yang
    diujinya hanya membuktikan berkas itu sama dengan dirinya sendiri.
    """
    rentang = sorted(_impor().dokumen[0].rentang, key=lambda r: (r.mulai, r.label.value))
    pertama = rentang[0]
    assert (pertama.mulai, pertama.akhir) == (0, 14)
    assert pertama.teks_rentang == "Kepala sekolah"
    assert pertama.label is LabelEntitas.JABATAN_PERAN


def test_kategori_terbaca_sebagai_enum() -> None:
    putusan = _impor().dokumen[0].putusan
    assert {p.kategori_utama for p in putusan} == {KategoriMasalah.K5, KategoriMasalah.K8}


def test_label_di_luar_skema_menggagalkan_impor() -> None:
    """Label Studio tidak menjamin nilai labelnya ada pada skema kita —
    konfigurasinya dapat disunting siapa pun yang punya akses proyek."""
    rusak = _muat()
    rusak[0]["annotations"][0]["result"][0]["value"]["labels"] = ["SARANA"]
    with pytest.raises(GalatImpor) as galat:
        _impor(rusak)
    assert "SARANA" in str(galat.value)


def test_kategori_di_luar_skema_menggagalkan_impor() -> None:
    rusak = _muat()
    for hasil in rusak[0]["annotations"][0]["result"]:
        if hasil["type"] == "choices":
            hasil["value"]["choices"] = ["K9"]
    with pytest.raises(GalatImpor) as galat:
        _impor(rusak)
    assert "K9" in str(galat.value)


def test_rentang_yang_tidak_cocok_dengan_teks_ditolak() -> None:
    """**Uji yang dituntut `tasks.md`.**

    Rentang digeser dua karakter sementara `text`-nya dibiarkan. Rentang yang
    diperbaiki diam-diam menunjuk kata lain tanpa satu galat pun — pelajaran
    R-06 fitur 003, dan di sini datangnya dari luar sistem kita.
    """
    rusak = _muat()
    rusak[0]["annotations"][0]["result"][0]["value"]["start"] = 26
    with pytest.raises(GalatImpor):
        _impor(rusak)


def test_rentang_melampaui_panjang_teks_ditolak() -> None:
    rusak = _muat()
    rusak[0]["annotations"][0]["result"][0]["value"]["end"] = 9999
    with pytest.raises(GalatImpor):
        _impor(rusak)


def test_anotasi_batal_tidak_masuk_korpus() -> None:
    """`was_cancelled` menandai anotasi yang anotatornya sendiri batalkan.

    Memasukkannya berarti menghitung pekerjaan yang ditarik kembali sebagai
    ketidaksepakatan pada angka Kappa.
    """
    isi = _muat()
    isi[0]["annotations"][0]["was_cancelled"] = True
    hasil = _impor(isi)
    assert len(hasil.dokumen[0].putusan) == 1


def test_tugas_tanpa_anotasi_dilewati_dan_dilaporkan() -> None:
    """**Dilewati, dan jumlahnya dilaporkan — bukan diam.**

    Dokumen yang belum dianotasi bukan kesalahan; ia belum dikerjakan. Yang
    salah adalah korpus yang diam-diam lebih kecil daripada batchnya, sebab
    selisihnya baru terlihat ketika seseorang membandingkan dua angka yang
    tidak pernah dilaporkan bersama.
    """
    isi = _muat()
    isi[1]["annotations"] = []
    hasil = _impor(isi)
    assert len(hasil.dokumen) == 1
    assert len(hasil.dilewati) == 1


def test_hasil_di_luar_dua_jenis_yang_dikenali_ditolak() -> None:
    """Jenis hasil ketiga berarti konfigurasi proyek memuat kendali yang
    modul ini tidak tahu artinya. Mengabaikannya diam-diam berarti membuang
    pekerjaan anotator tanpa seorang pun tahu."""
    rusak = _muat()
    rusak[0]["annotations"][0]["result"].append(
        {"from_name": "catatan", "to_name": "teks", "type": "textarea", "value": {"text": ["x"]}}
    )
    with pytest.raises(GalatImpor) as galat:
        _impor(rusak)
    assert "textarea" in str(galat.value)


def test_id_pengguna_di_luar_tabel_menggagalkan_impor() -> None:
    """Uji ini milik A-6 dan datang lebih awal, sebab jalurnya sudah dilalui
    A-2: `RentangEntitas` menuntut `id_anotator`, sehingga tabel kodenya
    dipakai sejak impor pertama.

    Id mentah Label Studio adalah pengenal internal yang bertahan pada berkas
    yang dilampirkan naskah. Memakainya apa adanya ketika tabelnya tidak
    memuatnya berarti membocorkan pengenal karena kelalaian, bukan karena
    keputusan.
    """
    with pytest.raises(GalatImpor) as galat:
        impor(_muat(), versi_skema=VERSI, kode_anotator={1: "A01"}, bendera_terkumpul=True)
    assert "2" in str(galat.value)


def test_pilihan_ganda_pada_tempat_tunggal_ditolak() -> None:
    """Konfigurasi proyek dapat mengizinkan pilihan ganda di tempat yang skema
    kita anggap tunggal. Mengambil yang pertama berarti membuang putusan
    anotator tanpa jejak."""
    rusak = _muat()
    for hasil in rusak[0]["annotations"][0]["result"]:
        if hasil["type"] == "choices":
            hasil["value"]["choices"] = ["K5", "K8"]
    with pytest.raises(GalatImpor) as galat:
        _impor(rusak)
    assert "2 nilai" in str(galat.value)


# ---------------------------------------------------------------- A-3, R-04


def test_versi_skema_wajib_diberikan_pemanggil() -> None:
    """**R-04.** Label Studio tidak membawa versi skema dalam bentuk apa pun
    (KB-023), sehingga menebaknya berarti mengarang.

    Bersifat kata kunci dan tanpa nilai bawaan: nilai bawaan akan menjadi
    jawaban bagi korpus yang versinya sebenarnya tidak diketahui, dan FR-C08
    melarang korpus memuat dua versi skema tanpa penandaan.
    """
    with pytest.raises(TypeError):
        impor(_muat(), kode_anotator=KODE, bendera_terkumpul=True)  # type: ignore[call-arg]


def test_versi_skema_yang_diberikan_melekat_pada_setiap_anotasi() -> None:
    lain = VersiSkema(mayor=2, minor=1)
    hasil = impor(_muat(), versi_skema=lain, kode_anotator=KODE, bendera_terkumpul=True)
    assert hasil.versi_skema == lain
    for dokumen in hasil.dokumen:
        assert all(r.versi_skema == lain for r in dokumen.rentang)
        assert all(p.versi_skema == lain for p in dokumen.putusan)


def test_versi_pada_berkas_ekspor_tidak_dipakai() -> None:
    """**Uji terpenting A-3, dan ia menguji ketiadaan.**

    Bila kelak Label Studio menambahkan bidang bernama `version` atau
    `schema_version`, modul ini tidak boleh diam-diam memakainya — bidang itu
    akan berarti versi perangkatnya, bukan versi skema anotasi kita, dan
    keduanya tidak pernah sama.
    """
    isi = _muat()
    for tugas in isi:
        tugas["schema_version"] = "9.9"
        tugas["version"] = "9.9"
    hasil = impor(isi, versi_skema=VERSI, kode_anotator=KODE, bendera_terkumpul=True)
    assert hasil.versi_skema == VERSI
