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
from src.nlp.anotasi.batch import StatusPraAnotasi
from src.nlp.anotasi.impor_ls import Bendera, GalatImpor, impor
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


# ---------------------------------------------------------------- A-4, R-05


def test_tugas_tanpa_prediksi_berstatus_tanpa_pra_anotasi() -> None:
    """Bahan uji dibuat tanpa pra-anotasi, sehingga `predictions` kosong."""
    for dokumen in _impor().dokumen:
        assert dokumen.status_pra_anotasi is StatusPraAnotasi.TANPA_PRA_ANOTASI


def test_tugas_berprediksi_berstatus_dengan_pra_anotasi() -> None:
    """**R-05.** Diturunkan dari `predictions`, tidak ditulis tangan.

    Bidang yang ditulis tangan dapat berbeda dari keadaan sebenarnya;
    yang diturunkan tidak dapat.
    """
    isi = _muat()
    isi[0]["predictions"] = [{"model_version": "ner-0.1", "result": []}]
    hasil = _impor(isi)
    assert hasil.dokumen[0].status_pra_anotasi is StatusPraAnotasi.DENGAN_PRA_ANOTASI
    assert hasil.dokumen[1].status_pra_anotasi is StatusPraAnotasi.TANPA_PRA_ANOTASI


def test_pembanding_tidak_pernah_diturunkan_dari_berkas() -> None:
    """**Uji yang menjaga batas modul ini.**

    `PEMBANDING` berarti dokumen **sengaja** disisihkan di dalam batch
    berpra-anotasi, dan kesengajaan itu keputusan pengelola batch — bukan
    sesuatu yang dapat dibaca dari berkas ekspor. Menebaknya berarti
    menyatakan pengendalian yang mungkin tidak pernah direncanakan siapa pun.
    """
    isi = _muat()
    isi[0]["predictions"] = [{"model_version": "ner-0.1", "result": []}]
    hasil = _impor(isi)
    assert all(d.status_pra_anotasi is not StatusPraAnotasi.PEMBANDING for d in hasil.dokumen)


# ---------------------------------------------------------------- A-5, R-06


def _dengan_bendera(*nilai: str) -> list[dict[str, Any]]:
    isi = _muat()
    isi[0]["annotations"][0]["result"].append(
        {
            "from_name": "bendera",
            "to_name": "teks",
            "type": "choices",
            "value": {"choices": list(nilai)},
        }
    )
    return isi


def test_bendera_terbaca_dari_kendali_bernama_bendera() -> None:
    hasil = _impor(_dengan_bendera("perlu_adjudikasi"))
    assert hasil.dokumen[0].bendera == frozenset({Bendera.PERLU_ADJUDIKASI})


def test_bendera_boleh_lebih_dari_satu() -> None:
    """Kendalinya `choice="multiple"` — satu dokumen dapat sekaligus perlu
    adjudikasi dan memuat kerusakan OCR."""
    hasil = _impor(_dengan_bendera("perlu_adjudikasi", "ocr_rusak"))
    assert hasil.dokumen[0].bendera == frozenset({Bendera.PERLU_ADJUDIKASI, Bendera.OCR_RUSAK})


def test_bendera_tidak_tercampur_dengan_kategori() -> None:
    """Keduanya berjenis `choices`; yang membedakan hanya `from_name`.

    Tanpa pembedaan itu, bendera masuk sebagai kategori dan menggagalkan impor
    dengan galat yang menyesatkan — atau lebih buruk, `perlu_adjudikasi`
    tercatat sebagai putusan kategori.
    """
    hasil = _impor(_dengan_bendera("bocor_pii"))
    assert len(hasil.dokumen[0].putusan) == 2
    assert hasil.dokumen[0].bendera == frozenset({Bendera.BOCOR_PII})


def test_bendera_di_luar_daftar_d03_menggagalkan_impor() -> None:
    with pytest.raises(GalatImpor) as galat:
        _impor(_dengan_bendera("ragu_ragu"))
    assert "ragu_ragu" in str(galat.value)


def test_proyek_tanpa_kendali_bendera_tidak_menghasilkan_korpus_yang_terbaca_bersih() -> None:
    """**Uji terpenting fitur ini, dan alasan R-06 ada.**

    `bendera` bernilai `None`, bukan himpunan kosong. Himpunan kosong berarti
    anotator memeriksa dan tidak menemukan apa pun; `None` berarti tidak ada
    yang pernah diperiksa.

    Menyamakan keduanya menghasilkan korpus yang menyatakan dirinya bersih
    atas dasar instrumen yang tidak terpasang — dan salah satu bendera adalah
    `bocor_pii`, yang menyatakan data pribadi lolos anonimisasi dan diperiksa
    harian pada KM-05. Bentuk laporan palsu yang sama dengan TA-01, pada
    taruhan yang paling mahal.
    """
    hasil = impor(_muat(), versi_skema=VERSI, kode_anotator=KODE, bendera_terkumpul=False)
    assert hasil.bendera_terkumpul is False
    for dokumen in hasil.dokumen:
        assert dokumen.bendera is None
        assert dokumen.bendera != frozenset()


def test_proyek_berkendali_bendera_tanpa_temuan_menghasilkan_himpunan_kosong() -> None:
    """Sisi lain, dan tanpanya uji sebelumnya tidak membuktikan pembedaannya."""
    hasil = _impor()
    for dokumen in hasil.dokumen:
        assert dokumen.bendera == frozenset()
        assert dokumen.bendera is not None


# ---------------------------------------------------------------- A-6, R-07, R-08


def test_id_pengguna_label_studio_tidak_muncul_pada_korpus() -> None:
    """**R-07.** D-03 Bagian 15 menuntut kode anonim.

    Disapu atas seluruh korpus, bukan diperiksa pada satu bidang: id yang
    lolos lewat jalur yang tidak terpikir tetap id yang bertahan pada berkas
    yang dilampirkan naskah.
    """
    hasil = _impor()
    kode_sah = set(KODE.values())
    for dokumen in hasil.dokumen:
        for anotasi in (*dokumen.rentang, *dokumen.putusan):
            assert anotasi.id_anotator in kode_sah
            assert anotasi.id_anotator not in {str(i) for i in KODE}


def test_dua_anotator_menandai_anotasi_ganda() -> None:
    """**R-08.** Tugas pertama pada bahan dianotasi dua akun berbeda."""
    hasil = _impor()
    assert hasil.dokumen[0].anotasi_ganda is True


def test_satu_anotator_tidak_menandai_anotasi_ganda() -> None:
    """Tugas kedua pada bahan dianotasi satu akun saja.

    Menandainya ganda akan membuat porsi anotasi ganda FR-C02 dilaporkan
    lebih besar daripada yang sebenarnya dikerjakan.
    """
    hasil = _impor()
    assert hasil.dokumen[1].anotasi_ganda is False


def test_dua_anotasi_dari_akun_yang_sama_bukan_anotasi_ganda() -> None:
    """**Keadaan yang paling mudah keliru.**

    Anotator yang mengerjakan ulang dokumennya meninggalkan dua objek anotasi
    dengan `completed_by` yang sama. Menghitung jumlah anotasi alih-alih
    jumlah anotator menandainya ganda — dan angka kesepakatan atas dokumen itu
    akan sempurna, sebab ia dibandingkan dengan dirinya sendiri.
    """
    isi = _muat()
    isi[0]["annotations"][1]["completed_by"] = 1
    hasil = _impor(isi)
    assert hasil.dokumen[0].anotasi_ganda is False
