"""Uji status pra-anotasi — C-2 fitur 003, R-12, FR-C10, D-03 BT-13.

**Pengendalian yang dibangun sebelum yang dikendalikannya ada.** Pra-anotasi
otomatis menunggu model NER fitur 004; *automation bias* yang dikendalikannya
muncul pada hari pertama pra-anotasi dipakai. Menambahkan penandanya belakangan
berarti batch-batch pertama tidak membawanya — dan batch pertama justru yang
paling menentukan kebiasaan anotator.

Yang diuji di sini satu sifat, dan sifat itu yang menentukan seluruh gunanya:
**dokumen tidak dapat dibentuk tanpa menyatakan status pra-anotasinya.** Bukan
nilai bawaan yang aman, bukan pemeriksaan belakangan. Nilai bawaan apa pun
akan menjadi jawaban bagi dokumen yang statusnya sebenarnya tidak diketahui,
dan dokumen berstatus keliru lebih buruk daripada dokumen tanpa status —
ia terbaca sebagai keterangan.

**Tiga nilai, bukan dua.** Dokumen tanpa pra-anotasi dan dokumen pembanding
sama-sama dianotasi dari halaman kosong, dan tetap dibedakan: yang pertama
berasal dari batch yang memang belum memakai pra-anotasi sama sekali, yang
kedua **sengaja disisihkan** di dalam batch yang memakainya. Menyatukan
keduanya membuat porsi pembanding pada batch berpra-anotasi tidak dapat
dihitung siapa pun — dan itu persis angka yang R-13 tuntut.
"""

import pytest
from pydantic import ValidationError
from src.nlp.anotasi.batch import DokumenAnotasi, StatusPraAnotasi


def test_tiga_status_ada() -> None:
    assert {s.name for s in StatusPraAnotasi} == {
        "TANPA_PRA_ANOTASI",
        "DENGAN_PRA_ANOTASI",
        "PEMBANDING",
    }


def test_pembanding_bukan_nilai_yang_sama_dengan_tanpa_pra_anotasi() -> None:
    """**Uji yang menjaga pembedaan paling mudah dihapus.**

    Keduanya berarti "dianotasi dari halaman kosong", sehingga menyatukannya
    tampak seperti menghapus nilai yang mubazir. Yang hilang bersamanya adalah
    kemampuan menghitung porsi pembanding pada batch berpra-anotasi.
    """
    assert StatusPraAnotasi.PEMBANDING is not StatusPraAnotasi.TANPA_PRA_ANOTASI


def test_dokumen_tanpa_status_tidak_dapat_dibentuk() -> None:
    """Uji yang dituntut C-1 pada `tasks.md`, dan inti R-12."""
    with pytest.raises(ValidationError):
        DokumenAnotasi(id_dokumen="dok1")  # type: ignore[call-arg]


def test_status_tidak_punya_nilai_bawaan() -> None:
    """Sifat, bukan kasus.

    Uji sebelumnya lulus juga pada versi yang punya nilai bawaan tetapi
    kebetulan menolak pemanggilan itu karena alasan lain. Yang diperiksa di
    sini adalah bidangnya sendiri: ia wajib, dan tidak menyediakan jawaban
    bagi yang lupa.
    """
    assert DokumenAnotasi.model_fields["status_pra_anotasi"].is_required()


def test_dokumen_dengan_status_terbentuk() -> None:
    dokumen = DokumenAnotasi(
        id_dokumen="dok1", status_pra_anotasi=StatusPraAnotasi.DENGAN_PRA_ANOTASI
    )
    assert dokumen.status_pra_anotasi is StatusPraAnotasi.DENGAN_PRA_ANOTASI


def test_dokumen_beku() -> None:
    """Status yang dapat diubah sesudah dokumen dianotasi adalah status yang
    dapat disesuaikan agar batchnya memenuhi porsi pembanding."""
    dokumen = DokumenAnotasi(id_dokumen="dok1", status_pra_anotasi=StatusPraAnotasi.PEMBANDING)
    with pytest.raises(ValidationError):
        dokumen.status_pra_anotasi = StatusPraAnotasi.DENGAN_PRA_ANOTASI  # type: ignore[misc]


def test_id_dokumen_kosong_ditolak() -> None:
    """Dokumen tanpa pengenal tidak dapat ditelusuri siapa pun, dan status
    pra-anotasi yang tidak dapat ditelusuri ke dokumennya tidak menjaga apa
    pun."""
    with pytest.raises(ValidationError):
        DokumenAnotasi(id_dokumen="", status_pra_anotasi=StatusPraAnotasi.PEMBANDING)


def test_untai_di_luar_daftar_ditolak() -> None:
    """Enum sebagai tipe, bukan untai bebas — `AGENTS.md` bagian Gaya.

    Untai bebas di sini berarti "pembanding", "Pembanding", dan "kontrol"
    hidup berdampingan, lalu porsi pembanding dihitung atas salah satunya saja.
    """
    for keliru in ("Pembanding", "kontrol", "PEMBANDING", "tanpa pra anotasi"):
        with pytest.raises(ValidationError):
            DokumenAnotasi(id_dokumen="dok1", status_pra_anotasi=keliru)  # type: ignore[arg-type]


def test_untai_yang_tepat_menjadi_anggota_enum_bukan_untai() -> None:
    """**Uji ini menggantikan uji yang saya tulis lebih dulu, dan sebabnya
    perlu tertulis.**

    Bentuk pertamanya menuntut untai `"pembanding"` ditolak. Ia gagal, dan
    yang keliru ujinya: pydantic memetakan untai yang **persis sama dengan
    nilai enumnya** menjadi anggota enum itu. Sifat yang sesungguhnya dijaga
    bukan "untai ditolak" melainkan "yang tersimpan selalu anggota enum" —
    dan sifat itu justru dipenuhi pemetaan tersebut.

    Menolaknya akan menuntut mode ketat pada satu bidang, dan itu penjagaan
    terhadap sesuatu yang sudah dijaga: ragam ejaan lain tetap ditolak, dan
    penulisan bertipe salah tertangkap mypy sebelum berjalan.
    """
    dokumen = DokumenAnotasi(id_dokumen="dok1", status_pra_anotasi="pembanding")  # type: ignore[arg-type]
    assert dokumen.status_pra_anotasi is StatusPraAnotasi.PEMBANDING
    assert not isinstance(dokumen.status_pra_anotasi, str)


def test_uraian_menyatakan_mengapa_penandanya_ada_sebelum_pra_anotasinya() -> None:
    """Modul yang membangun pengendali sebelum yang dikendalikannya ada akan
    tampak seperti kerangka kosong bagi pembaca berikutnya — dan C-14 melarang
    kerangka kosong. Alasannya wajib tertulis agar pembedaannya terbaca."""
    import src.nlp.anotasi.batch as modul_batch

    uraian = modul_batch.__doc__ or ""
    assert "fitur 004" in uraian
    assert "automation bias" in uraian.lower()
