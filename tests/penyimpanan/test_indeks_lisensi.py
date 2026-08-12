"""Uji pemisahan indeks menurut lisensi — A-1 s.d. A-3 fitur 006, R-01 s.d. R-05.

D-07 Bagian 3.1 menyatakannya dalam satu kalimat: *"Ini keputusan struktural,
bukan penyaringan."* Alasannya pada kalimat berikutnya — **pemisahan pada
tingkat indeks membuat kekeliruan kueri tidak dapat meloloskan teks berlisensi
tertutup.**

Penyaringan saat kueri terasa cukup: satu klausa, mudah dibaca, mudah diuji.
Yang membuatnya tidak cukup adalah bahwa klausa itu ada pada **setiap** kueri,
dan satu kueri yang lupa memuatnya tidak menghasilkan galat apa pun — ia
menghasilkan jawaban yang lebih lengkap, dan jawaban yang lebih lengkap tidak
pernah terasa seperti kekeliruan sampai audit lisensi.

**A-3 menjaga hal yang berbeda dari nama fitur ini.** Penegakan lisensi mudah
menyita seluruh perhatian, dan sementara itu dokumen yang anonimisasinya masih
menunggu verifikasi masuk indeks utama tanpa satu pun pemeriksaan menyala.
Yang bocor di sana bukan lisensi melainkan data pribadi.
"""

import pytest
from pydantic import ValidationError
from src.ingest.dokumen import Dokumen, StatusAnonimisasi
from src.penyimpanan.indeks import (
    IndeksTujuan,
    SegmenTerindeks,
    StatusLisensi,
    indeks_bagi,
    lisensi_dari_metadata,
)


def _segmen(**ganti: object) -> SegmenTerindeks:
    argumen: dict[str, object] = {
        "id_segmen": "SEG-001",
        "id_dokumen": "DOC-001",
        "teks": "Kepala sekolah menyusun RKAS bersama komite sekolah.",
        "lisensi": StatusLisensi.TERBUKA,
        "indeks_tujuan": IndeksTujuan.UTAMA,
        "anonimisasi_terverifikasi": True,
        "penanda_bagian": "Pasal 12 ayat (2)",
    }
    argumen.update(ganti)
    return SegmenTerindeks(**argumen)  # type: ignore[arg-type]


# ---------------------------------------------------------- A-1, R-01, R-02


def test_dua_nilai_indeks_persis_d14() -> None:
    """D-14 Bagian 5 menamai `segmen_teks.indeks_tujuan` dengan nilai `utama`
    dan `metadata`. Fitur ini mewujudkannya, tidak menciptakannya — AG-04
    melarang agen mengubah daftar nilai enum."""
    assert {i.value for i in IndeksTujuan} == {"utama", "metadata"}


def test_segmen_tanpa_indeks_tujuan_tidak_dapat_dibentuk() -> None:
    """**R-02.** Segmen yang dibentuk tanpa indeks tujuan lalu diisi kemudian
    adalah segmen yang sempat ada tanpa penjagaan."""
    with pytest.raises(ValidationError):
        SegmenTerindeks(  # type: ignore[call-arg]
            id_segmen="SEG-001",
            id_dokumen="DOC-001",
            teks="isi",
            lisensi=StatusLisensi.TERBUKA,
            anonimisasi_terverifikasi=True,
            penanda_bagian="Pasal 1",
        )


def test_indeks_tujuan_tidak_punya_nilai_bawaan() -> None:
    """Sifat, bukan kasus. Nilai bawaan apa pun akan menjadi jawaban bagi
    segmen yang tujuannya sebenarnya belum ditentukan siapa pun."""
    assert SegmenTerindeks.model_fields["indeks_tujuan"].is_required()
    assert SegmenTerindeks.model_fields["lisensi"].is_required()


def test_segmen_beku() -> None:
    """Indeks tujuan yang dapat diubah setelah segmen dibentuk adalah indeks
    yang dapat dipindahkan ketika hasil pencarian terasa kurang."""
    segmen = _segmen()
    with pytest.raises(ValidationError):
        segmen.indeks_tujuan = IndeksTujuan.METADATA  # type: ignore[misc]


# ---------------------------------------------------------- A-2, R-03


def test_lisensi_tertutup_ke_indeks_utama_ditolak() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-03.**

    Penempatan yang keliru ditolak **saat segmen dibentuk**, bukan disaring
    saat dibaca. Segmen tertutup yang sempat ada di indeks utama adalah segmen
    yang dapat terbaca sebelum penyaring mana pun berjalan.
    """
    with pytest.raises(ValidationError) as galat:
        _segmen(lisensi=StatusLisensi.TERTUTUP, indeks_tujuan=IndeksTujuan.UTAMA)
    assert "tertutup" in str(galat.value)


def test_lisensi_tertutup_ke_indeks_metadata_diterima() -> None:
    segmen = _segmen(lisensi=StatusLisensi.TERTUTUP, indeks_tujuan=IndeksTujuan.METADATA)
    assert segmen.indeks_tujuan is IndeksTujuan.METADATA


def test_lisensi_terbuka_ke_indeks_metadata_diterima() -> None:
    """Arah sebaliknya **tidak** dilarang: menaruh segmen terbuka pada indeks
    metadata mengurangi jangkauan jawaban, tidak membocorkan apa pun.

    Melarangnya akan menghalangi keputusan kurasi yang sah — misalnya artikel
    terbuka yang hanya abstraknya relevan.
    """
    segmen = _segmen(lisensi=StatusLisensi.TERBUKA, indeks_tujuan=IndeksTujuan.METADATA)
    assert segmen.indeks_tujuan is IndeksTujuan.METADATA


def test_indeks_bagi_menetapkan_dari_lisensinya() -> None:
    assert indeks_bagi(StatusLisensi.TERBUKA) is IndeksTujuan.UTAMA
    assert indeks_bagi(StatusLisensi.TERTUTUP) is IndeksTujuan.METADATA


def test_lisensi_yang_tidak_terbaca_mesin_diperlakukan_tertutup() -> None:
    """**Aturan pelaksanaan KL-01 pada D-06.**

    "Artikel tanpa keterangan lisensi yang terbaca mesin diperlakukan sebagai
    tertutup. Ini pilihan konservatif yang disengaja: kekeliruan ke arah ini
    hanya mengurangi jumlah butir, sedangkan kekeliruan ke arah sebaliknya
    menggugurkan publikasi."
    """
    assert lisensi_dari_metadata(None) is StatusLisensi.TERTUTUP
    assert lisensi_dari_metadata("") is StatusLisensi.TERTUTUP
    assert lisensi_dari_metadata("hak cipta dilindungi") is StatusLisensi.TERTUTUP


def test_lisensi_terbuka_yang_terbaca_mesin_dikenali() -> None:
    for nilai in ("CC-BY", "cc-by-4.0", "CC0", "CC-BY-SA-4.0"):
        assert lisensi_dari_metadata(nilai) is StatusLisensi.TERBUKA


def test_lisensi_tidak_disimpulkan_dari_jenis_sumber() -> None:
    """D-06: "Bidang lisensi diambil dari metadata sumber, **bukan
    disimpulkan**."

    Menyimpulkannya dari jenis sumber akan membuat artikel jurnal berlisensi
    tertutup yang diberi jenis `artikel_lisensi_terbuka` oleh kekeliruan
    kurasi ikut masuk indeks utama.

    Diperiksa pada tingkat AST, bukan dengan mencari untainya. Bentuk pertama
    uji ini menyapu seluruh berkas dan menandai uraian modulnya sendiri — yang
    justru menjelaskan mengapa `JenisSumber` tidak dipakai. Uji yang menandai
    penjelasan tentang aturan sebagai pelanggaran aturan itu akan membuat
    penjelasannya dihapus, dan penjelasan itu yang paling berharga.
    """
    import ast
    import inspect

    import src.penyimpanan.indeks as modul

    pohon = ast.parse(inspect.getsource(modul))
    nama = {simpul.id for simpul in ast.walk(pohon) if isinstance(simpul, ast.Name)} | {
        simpul.attr for simpul in ast.walk(pohon) if isinstance(simpul, ast.Attribute)
    }
    assert "JenisSumber" not in nama


# ---------------------------------------------------------- A-3, R-05


def test_segmen_yang_anonimisasinya_belum_terverifikasi_ditolak() -> None:
    """**Uji terpenting Fase A.**

    Yang bocor di sini bukan lisensi melainkan data pribadi — dan penegakan
    lisensi mudah menyita seluruh perhatian sehingga celah ini lewat tanpa
    satu pun pemeriksaan menyala.
    """
    with pytest.raises(ValidationError) as galat:
        _segmen(anonimisasi_terverifikasi=False)
    assert "anonimisasi" in str(galat.value)


def test_penolakan_berlaku_pada_kedua_indeks() -> None:
    """Indeks metadata bukan tempat pembuangan.

    Segmen yang anonimisasinya belum diverifikasi ditolak dari **keduanya**;
    menaruhnya di metadata akan membuat data pribadi tersimpan dengan alasan
    bahwa ia tidak akan masuk konteks LLM — padahal ia tetap tersimpan.
    """
    with pytest.raises(ValidationError):
        _segmen(
            anonimisasi_terverifikasi=False,
            lisensi=StatusLisensi.TERTUTUP,
            indeks_tujuan=IndeksTujuan.METADATA,
        )


@pytest.mark.parametrize("status", [StatusAnonimisasi.MENUNGGU, StatusAnonimisasi.DITOLAK])
def test_kedua_status_selain_terverifikasi_menghasilkan_penolakan(
    status: StatusAnonimisasi,
) -> None:
    """Diuji lewat aturan yang sudah ada pada fitur 002, bukan lewat aturan
    kedua yang ditulis ulang di sini.

    Dua aturan yang ditulis terpisah akan berbeda ketika D-14 menambah nilai
    keempat, dan yang berbeda adalah yang tidak diperbarui.
    """
    izin = Dokumen.anonimisasi_mengizinkan_indeks(status)
    assert izin is False
    with pytest.raises(ValidationError):
        _segmen(anonimisasi_terverifikasi=izin)


def test_status_terverifikasi_diterima() -> None:
    izin = Dokumen.anonimisasi_mengizinkan_indeks(StatusAnonimisasi.TERVERIFIKASI)
    assert _segmen(anonimisasi_terverifikasi=izin).anonimisasi_terverifikasi


# ------------------------------------------------ A-1 fitur 007, R-10, FR-F11


def test_segmen_tanpa_penanda_bagian_tidak_dapat_dibentuk() -> None:
    """**Uji A-1 fitur 007.** `docs/D14.md` Bagian 5: `segmen_teks.penanda_bagian`
    berisi "Pasal, ayat, atau subjudul. **Wajib**; tanpanya FR-F11 gagal."

    Fitur 006 membangun `SegmenTerindeks` tanpanya. Itu kelalaian, bukan
    keputusan — dan yang membuatnya perlu ditutup sekarang adalah fitur 007
    menjadi pemakai pertama segmen. Segmen yang dapat diambil tetapi tidak
    dapat disitasi gagal pada titik kritis T2 (D-02), dan kegagalan itu baru
    terlihat pada fitur 009 ketika indeksnya mungkin sudah terisi.
    """
    with pytest.raises(ValidationError):
        SegmenTerindeks(  # type: ignore[call-arg]
            id_segmen="SEG-001",
            id_dokumen="DOC-001",
            teks="isi",
            lisensi=StatusLisensi.TERBUKA,
            indeks_tujuan=IndeksTujuan.UTAMA,
            anonimisasi_terverifikasi=True,
        )


@pytest.mark.parametrize("kosong", ["", " ", "\t", "\n  "])
def test_penanda_bagian_kosong_atau_hanya_spasi_ditolak(kosong: str) -> None:
    """Bidang wajib yang menerima untai kosong adalah bidang opsional yang
    ditulis dengan cara lebih panjang.

    Spasi diperiksa terpisah dari kosong sebab `min_length` meloloskan `" "`,
    dan penanda berisi satu spasi tidak menunjuk pasal mana pun.
    """
    with pytest.raises(ValidationError) as galat:
        _segmen(penanda_bagian=kosong)
    assert "penanda" in str(galat.value).lower()


def test_penanda_bagian_tidak_punya_nilai_bawaan() -> None:
    """Sifat, bukan kasus. Nilai bawaan `""` akan membuat setiap segmen yang
    lupa mengisinya lolos, dan yang lolos tidak dapat disitasi."""
    assert SegmenTerindeks.model_fields["penanda_bagian"].is_required()


def test_penanda_bagian_dipangkas_ujungnya() -> None:
    """Penanda yang tersimpan dengan spasi di ujung akan ditampilkan begitu
    pada sitasi. Dipangkas saat masuk, bukan saat ditampilkan — satu tempat,
    bukan setiap tempat."""
    assert _segmen(penanda_bagian="  Pasal 3  ").penanda_bagian == "Pasal 3"
