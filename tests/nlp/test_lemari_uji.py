"""Uji lemari himpunan uji — A-5 fitur 004, R-06, PU-01, D-08 Bagian 4.2.

PU-01 berbunyi: **data uji tidak pernah menyentuh proses pelatihan atau
penyetelan.** D-08 menambahkan bahwa himpunan uji "dibuka satu kali" saat
evaluasi akhir.

**Pelanggarannya tidak pernah disengaja.** Ia terjadi ketika seseorang sekadar
melihat hasil uji untuk memutuskan konfigurasi berikutnya — satu kali, untuk
memastikan arahnya benar. Sesudah itu angka yang masuk naskah bukan lagi hasil
pada data tersembunyi, dan **tidak ada satu pun jejak yang menunjukkannya.**

Yang dibangun di sini adalah jejak itu. Bukan larangan: KB-028 memutuskan
pembukaan tetap diizinkan, sebab penjagaan yang menghalangi pekerjaan sah —
mengulang evaluasi karena galat perkakas — akan dilucuti, dan cara
melucutinya adalah membuat pembagian baru, yang justru menghapus jejaknya.

Yang dituntut: setiap pembukaan **tercatat beserta alasannya**, dan
hitungannya ikut pada catatan percobaan yang menjadi bahan naskah.
"""

import ast
from pathlib import Path

import pytest
from src.nlp.pelatihan.lemari_uji import GalatLemariUji, LemariUji
from src.nlp.pelatihan.pembagian import buat_pembagian

AKAR = Path(__file__).resolve().parents[2]


def _lemari() -> LemariUji:
    bagi = buat_pembagian(
        [f"dok{i:04d}" for i in range(100)], seed=7, versi_korpus="1.0", id_pembagian="B1"
    )
    return LemariUji(bagi)


def test_lemari_baru_belum_pernah_dibuka() -> None:
    lemari = _lemari()
    assert lemari.jumlah_pembukaan == 0
    assert lemari.riwayat == ()


def test_membuka_mengembalikan_himpunan_uji() -> None:
    lemari = _lemari()
    uji = lemari.buka("evaluasi akhir model NER v1")
    assert len(uji) == 15


def test_pembukaan_tercatat_beserta_alasannya() -> None:
    """**Inti R-06.** Alasan yang tidak tercatat membuat riwayat pembukaan
    menjadi deret angka tanpa arti — dan deret angka tanpa arti tidak
    membedakan evaluasi akhir dari mengintip."""
    lemari = _lemari()
    lemari.buka("evaluasi akhir model NER v1")
    assert lemari.jumlah_pembukaan == 1
    assert lemari.riwayat[0].alasan == "evaluasi akhir model NER v1"


def test_pembukaan_kedua_menaikkan_hitungan() -> None:
    """**Uji yang dituntut `tasks.md`.**

    Pembukaan kedua tidak ditolak — KB-028 pilihan C — tetapi ia terhitung,
    dan hitungannya ikut pada catatan percobaan yang masuk naskah.
    """
    lemari = _lemari()
    lemari.buka("evaluasi akhir model NER v1")
    lemari.buka("evaluasi diulang: perkakas metrik salah versi")
    assert lemari.jumlah_pembukaan == 2
    assert len(lemari.riwayat) == 2


def test_alasan_kosong_ditolak() -> None:
    """Pembukaan tanpa alasan adalah pembukaan yang tidak dapat dinilai siapa
    pun kemudian. Yang menilai bukan modul ini melainkan pembaca laporannya,
    dan ia hanya punya alasan yang tertulis."""
    lemari = _lemari()
    with pytest.raises(GalatLemariUji):
        lemari.buka("")


def test_alasan_terlalu_pendek_ditolak() -> None:
    """ "ok" dan "cek" memenuhi syarat tidak kosong dan tidak menerangkan apa
    pun. Ambangnya rendah dengan sengaja — ia menghalangi kelalaian, bukan
    menghalangi orang yang memang hendak menyamarkan."""
    lemari = _lemari()
    with pytest.raises(GalatLemariUji):
        lemari.buka("cek")


def test_pembukaan_membawa_waktu_utc() -> None:
    """Waktu yang membedakan pembukaan sebelum pelatihan dari sesudahnya, dan
    urutan itu yang menentukan apakah PU-01 dilanggar. Disimpan UTC sesuai
    `AGENTS.md` bagian Gaya."""
    lemari = _lemari()
    lemari.buka("evaluasi akhir model NER v1")
    assert lemari.riwayat[0].waktu.tzinfo is not None


def test_riwayat_tidak_dapat_diubah_dari_luar() -> None:
    """Riwayat yang dapat disunting adalah riwayat yang akan disunting ketika
    hitungannya memalukan."""
    lemari = _lemari()
    lemari.buka("evaluasi akhir model NER v1")
    riwayat = lemari.riwayat
    assert isinstance(riwayat, tuple)
    with pytest.raises(AttributeError):
        riwayat[0].alasan = "lain"  # type: ignore[misc]


def test_latih_dan_validasi_tidak_lewat_lemari() -> None:
    """Lemari hanya menjaga himpunan uji.

    Menjaga ketiganya akan membuat pencatatan menjadi kebisingan — himpunan
    latih dibaca pada setiap epoch — dan pencatatan yang bising adalah
    pencatatan yang tidak ada yang membaca.
    """
    lemari = _lemari()
    assert lemari.latih
    assert lemari.validasi
    assert lemari.jumlah_pembukaan == 0


MODUL_BOLEH_MEMBACA_UJI = (
    "src/nlp/pelatihan/pembagian.py",
    "src/nlp/pelatihan/lemari_uji.py",
)


def test_himpunan_uji_tidak_dibaca_di_luar_lemari() -> None:
    """**Uji terpenting berkas ini, dan satu-satunya yang menegakkan R-06
    sebagai sifat.**

    `LemariUji` mencatat pembukaan hanya bila ia yang dipakai. Kode yang
    membaca `pembagian.uji` langsung melewatinya tanpa satu galat pun —
    dan itu persis bentuk "sekadar melihat" yang PU-01 larang.

    Disapu pada tingkat AST atas seluruh `src/`. Bentuk yang sama dengan
    pemeriksa impor tunggal `pytesseract` fitur 015: aturan yang tidak dapat
    ditegakkan bahasa ditegakkan pemeriksa.

    **Batas yang diakui:** sapuan ini menangkap `sesuatu.uji`, bukan akses
    lewat `getattr` maupun lewat pembongkaran model pydantic. Ia menghalangi
    kelalaian, bukan orang yang memang hendak melewatinya — dan yang kedua
    memang bukan yang dijaga di sini.
    """
    boleh = {(AKAR / j).resolve() for j in MODUL_BOLEH_MEMBACA_UJI}
    pelanggaran: list[str] = []
    for berkas in sorted((AKAR / "src").rglob("*.py")):
        if berkas.resolve() in boleh:
            continue
        for simpul in ast.walk(ast.parse(berkas.read_text(encoding="utf-8"))):
            if isinstance(simpul, ast.Attribute) and simpul.attr == "uji":
                pelanggaran.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno}")
    assert not pelanggaran, (
        "himpunan uji dibaca di luar LemariUji: "
        + "; ".join(pelanggaran)
        + " — pembacaan langsung melewati pencatatan R-06"
    )


def test_sapuan_menangkap_pembacaan_langsung(tmp_path: Path) -> None:
    """**Uji atas uji sebelumnya.**

    Sapuan yang tidak pernah dibuktikan menangkap sasarannya adalah sapuan
    yang mungkin sudah berhenti menjaga sejak lama — dan tidak ada yang tahu,
    sebab ia selalu melapor bersih.
    """
    palsu = tmp_path / "pelanggar.py"
    palsu.write_text("def f(bagi):\n    return bagi.uji\n", encoding="utf-8")
    ditemukan = [
        s
        for s in ast.walk(ast.parse(palsu.read_text(encoding="utf-8")))
        if isinstance(s, ast.Attribute) and s.attr == "uji"
    ]
    assert ditemukan


def test_uraian_menyebut_pu_01_dan_alasannya() -> None:
    """Aturan tanpa alasan akan dilanggar oleh orang yang mengira ia usang.

    Di sini alasannya khusus: pelanggarannya tidak terasa seperti pelanggaran
    ketika dilakukan.
    """
    import src.nlp.pelatihan.lemari_uji as modul

    uraian = modul.__doc__ or ""
    assert "PU-01" in uraian
    assert "D-08" in uraian
