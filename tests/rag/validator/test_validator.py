"""Uji penyusun validator — C-2 fitur 008, R-06, R-09, R-10, R-11, R-12.

**Tempat TA-01 diulang atau ditutup.**

Tiga dari sembilan pemeriksaan D-07 Bagian 6.1 tidak dapat dijalankan hari ini.
Validator yang mengembalikan `True` atas kesembilannya tidak dapat dibedakan
dari validator yang benar — dan ia tinggal di komponen yang D-04 ADR-04 sebut
terpenting dalam sistem.

Uji pertama di bawah menyatakan akibat yang tidak menyenangkan dan disengaja:
**sistem ini tidak dapat menayangkan jawaban apa pun hari ini.** D-07 Bagian 1
menetapkan arahnya — "jawaban yang salah lebih merugikan daripada jawaban yang
tidak ada".
"""

import pytest
from src.kamus.segmen import IndeksTujuan, Peringkat, StatusKeberlakuan
from src.rag.validator.keluaran import KeluaranModel, Klaim, SegmenRujukan
from src.rag.validator.pemeriksaan import HasilPemeriksaan, KodePemeriksaan, Status
from src.rag.validator.validator import (
    HasilValidasi,
    JawabanTervalidasi,
    keluaran_setelah_tindakan,
    validasi,
)


def _segmen(
    id_segmen: str = "SEG-A",
    *,
    peringkat: Peringkat = Peringkat.T1,
    indeks: IndeksTujuan = IndeksTujuan.UTAMA,
    keberlakuan: StatusKeberlakuan = StatusKeberlakuan.BERLAKU,
) -> SegmenRujukan:
    return SegmenRujukan(
        id_segmen=id_segmen,
        peringkat_kepercayaan=peringkat,
        indeks_asal=indeks,
        status_keberlakuan=keberlakuan,
    )


def _keluaran(*klaim: Klaim, ringkasan: tuple[str, ...] = ("Susun RKAS.",)) -> KeluaranModel:
    return KeluaranModel(ringkasan_tindakan=ringkasan, klaim=klaim)


def _klaim(id_klaim: str, *id_segmen: str) -> Klaim:
    return Klaim(id_klaim=id_klaim, teks=f"Klaim {id_klaim}.", id_segmen=id_segmen)


def _lulus_semua() -> HasilValidasi:
    return HasilValidasi(
        pemeriksaan=tuple(
            HasilPemeriksaan(kode=k, status=Status.LULUS, alasan="lulus") for k in KodePemeriksaan
        )
    )


# ------------------------------------------------------------------ R-10


def test_sistem_belum_dapat_menayangkan_jawaban_apa_pun() -> None:
    """**Uji terpenting fitur 008, dan akibatnya disengaja.**

    Keluaran yang sepenuhnya sehat pun tidak tervalidasi, sebab VS-03, VS-05,
    dan VS-07 belum dapat dijalankan. Itu bukan cacat melainkan pembacaan jujur
    atas apa yang sudah dan belum ada.

    Uji ini **wajib gagal** pada fitur 020, dan kegagalannya adalah tandanya
    selesai.
    """
    hasil, jawaban = validasi(_keluaran(_klaim("K1", "SEG-A")), segmen=(_segmen(),))
    assert not hasil.tervalidasi
    assert jawaban is None


def test_ketiga_yang_belum_dapat_diperiksa_disebut_beserta_yang_ditunggunya() -> None:
    """Alasan yang tidak menyebut apa yang ditunggu adalah alasan yang tidak
    dapat ditagih."""
    hasil, _ = validasi(_keluaran(_klaim("K1", "SEG-A")), segmen=(_segmen(),))
    belum = {
        h.kode: h.alasan for h in hasil.pemeriksaan if h.status is Status.BELUM_DAPAT_DIPERIKSA
    }
    assert set(belum) == {KodePemeriksaan.VS_03, KodePemeriksaan.VS_05, KodePemeriksaan.VS_07}
    assert "019" in belum[KodePemeriksaan.VS_03]
    assert "BT-29" in belum[KodePemeriksaan.VS_05]
    assert "017" in belum[KodePemeriksaan.VS_07]


def test_keenam_yang_dapat_dijalankan_benar_benar_dijalankan() -> None:
    """Sisi lain dari uji sebelumnya: "belum dapat diperiksa" tidak boleh
    menjadi jawaban bagi pemeriksaan yang sebenarnya dapat berjalan."""
    hasil, _ = validasi(_keluaran(_klaim("K1", "SEG-A")), segmen=(_segmen(),))
    lulus = {h.kode for h in hasil.pemeriksaan if h.status is Status.LULUS}
    assert lulus == {
        KodePemeriksaan.VS_01,
        KodePemeriksaan.VS_02,
        KodePemeriksaan.VS_04,
        KodePemeriksaan.VS_06,
        KodePemeriksaan.VS_08,
        KodePemeriksaan.VS_09,
    }


def test_kesembilan_kode_selalu_hadir_pada_hasil() -> None:
    """Menjatuhkan satu pemeriksaan dari daftar jalannya adalah cara termudah
    melanggar C-19 tanpa menyentuh satu baris logika pun."""
    hasil, _ = validasi(_keluaran(_klaim("K1", "SEG-A")), segmen=(_segmen(),))
    assert {h.kode for h in hasil.pemeriksaan} == set(KodePemeriksaan)


def test_tervalidasi_adalah_sifat_terhitung_bukan_bidang() -> None:
    """**R-10.** Bidang dapat diisi `True` oleh pemanggil yang lelah, dan
    pemanggil yang lelah adalah keadaan yang wajar pada bulan kelima."""
    assert "tervalidasi" not in HasilValidasi.model_fields
    assert isinstance(type(HasilValidasi.tervalidasi), type(property))


def test_satu_pemeriksaan_belum_dapat_diperiksa_menghalangi_seluruhnya() -> None:
    """Delapan lulus dan satu belum dapat diperiksa **bukan** delapan per
    sembilan tervalidasi. Ia tidak tervalidasi."""
    hampir = [
        HasilPemeriksaan(kode=k, status=Status.LULUS, alasan="lulus")
        for k in KodePemeriksaan
        if k is not KodePemeriksaan.VS_03
    ]
    hampir.append(
        HasilPemeriksaan(
            kode=KodePemeriksaan.VS_03,
            status=Status.BELUM_DAPAT_DIPERIKSA,
            alasan="menunggu fitur 019",
        )
    )
    assert not HasilValidasi(pemeriksaan=tuple(hampir)).tervalidasi


def test_hasil_yang_kehilangan_satu_pemeriksaan_tidak_tervalidasi() -> None:
    """**Kelengkapan diperiksa, bukan hanya statusnya.**

    Delapan pemeriksaan lulus bukan hasil yang tervalidasi — ia hasil yang satu
    pemeriksaannya hilang. Tanpa uji ini, `all()` atas daftar yang lebih pendek
    mengembalikan `True`, dan daftar kosong pun tervalidasi.
    """
    delapan = tuple(
        HasilPemeriksaan(kode=k, status=Status.LULUS, alasan="lulus")
        for k in KodePemeriksaan
        if k is not KodePemeriksaan.VS_08
    )
    assert not HasilValidasi(pemeriksaan=delapan).tervalidasi
    assert not HasilValidasi(pemeriksaan=()).tervalidasi


def test_jalur_tervalidasi_terbuka_ketika_fitur_020_mendarat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**Uji yang membuktikan sistem ini akan bekerja, bukan hanya menolak.**

    Jalur yang membentuk `JawabanTervalidasi` tidak dapat dicapai hari ini —
    ketiga pemeriksaan fitur 020 selalu menghalanginya. Tanpa uji ini, jalur
    itu tidak pernah dijalankan satu kali pun sampai bulan kelima, dan
    kekeliruan di dalamnya baru ketahuan ketika seluruh perhatian tertuju pada
    model sematan yang baru dipasang.

    Yang disimulasikan adalah **mendaratnya fitur 020**: sambungan
    `pemeriksaan_menunggu_model` mengembalikan ketiga hasil yang lulus, persis
    bentuk yang fitur 020 akan hasilkan.

    Ia sisi lain `test_sistem_belum_dapat_menayangkan_jawaban_apa_pun`: yang
    menahan jawaban hari ini adalah ketiga pemeriksaan itu, bukan kekeliruan
    pada keenam yang lain.
    """
    import src.rag.validator.validator as modul

    def mendarat(
        keluaran: KeluaranModel, *, segmen: object
    ) -> dict[KodePemeriksaan, HasilPemeriksaan]:
        return {
            k: HasilPemeriksaan(kode=k, status=Status.LULUS, alasan="fitur 020 mendarat")
            for k in (KodePemeriksaan.VS_03, KodePemeriksaan.VS_05, KodePemeriksaan.VS_07)
        }

    monkeypatch.setattr(modul, "pemeriksaan_menunggu_model", mendarat)

    hasil, jawaban = modul.validasi(_keluaran(_klaim("K1", "SEG-A")), segmen=(_segmen(),))
    assert hasil.tervalidasi
    assert jawaban is not None
    assert jawaban.hasil is hasil
    assert jawaban.keluaran.klaim[0].id_klaim == "K1"


def test_pemeriksaan_yang_hilang_menghentikan_validasi_dengan_keras(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**Penjagaan terakhir sebelum diam.**

    Bila sebuah kode kehilangan hasilnya — sambungan yang keliru, kunci yang
    terhapus — `HasilValidasi` masih dapat dibentuk, dan `tervalidasi` akan
    mengembalikan `False`. Itu **aman tetapi diam**: sistem berhenti menjawab
    tanpa ada yang tahu sebabnya, dan sebabnya akan dicari pada tempat yang
    salah selama berhari-hari.

    `RuntimeError` di sini menyebut kode yang hilang. Ia bukan penjagaan
    kepatuhan — `tervalidasi` sudah menutup itu — melainkan penjagaan terhadap
    kegagalan yang tidak terbaca.
    """
    import src.rag.validator.validator as modul

    def sebagian(keluaran: KeluaranModel, *, segmen: object) -> dict[object, object]:
        return {}

    monkeypatch.setattr(modul, "pemeriksaan_menunggu_model", sebagian)

    with pytest.raises(RuntimeError) as galat:
        modul.validasi(_keluaran(_klaim("K1", "SEG-A")), segmen=(_segmen(),))
    pesan = str(galat.value)
    assert "VS-03" in pesan
    assert "VS-05" in pesan
    assert "VS-07" in pesan


def test_pendaratan_020_tidak_menutupi_kegagalan_keenam_yang_lain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sambungan yang mendarat tidak boleh membuat keenam pemeriksaan yang
    sudah ada berhenti menahan.

    Tanpa uji ini, `validasi` yang keliru menyusun daftarnya — misalnya
    mengganti seluruh daftar alih-alih menambahinya — akan lolos uji
    sebelumnya.
    """
    import src.rag.validator.validator as modul

    def mendarat(
        keluaran: KeluaranModel, *, segmen: object
    ) -> dict[KodePemeriksaan, HasilPemeriksaan]:
        return {
            k: HasilPemeriksaan(kode=k, status=Status.LULUS, alasan="fitur 020 mendarat")
            for k in (KodePemeriksaan.VS_03, KodePemeriksaan.VS_05, KodePemeriksaan.VS_07)
        }

    monkeypatch.setattr(modul, "pemeriksaan_menunggu_model", mendarat)

    hasil, jawaban = modul.validasi(_keluaran(_klaim("K1", "SEG-KARANGAN")), segmen=(_segmen(),))
    assert not hasil.tervalidasi
    assert jawaban is None
    assert KodePemeriksaan.VS_02 in {h.kode for h in hasil.menghalangi}


def test_seluruh_lulus_menghasilkan_jawaban_tervalidasi() -> None:
    """Bentuknya dapat dicapai — diuji lewat `HasilValidasi` yang disusun
    tangan, sebab jalur sesungguhnya baru terbuka pada fitur 020.

    Tanpa uji ini, `tervalidasi` yang selalu `False` akan lolos seluruh uji
    lain di berkas ini.
    """
    assert _lulus_semua().tervalidasi


# ------------------------------------------------------------------ R-08


def test_pemeriksaan_yang_menghalangi_dilaporkan_beserta_kodenya() -> None:
    """D-07 Bagian 6.2: setiap kegagalan memicu `answer_rejected_validator`
    beserta kode pemeriksaan yang gagal, dan itu yang membuat RT-02 terukur."""
    hasil, _ = validasi(_keluaran(_klaim("K1", "SEG-KARANGAN")), segmen=(_segmen(),))
    kode = {h.kode for h in hasil.menghalangi}
    assert KodePemeriksaan.VS_02 in kode


# ------------------------------------------------------ R-03, R-04, R-06


def test_insiden_kepatuhan_membuang_seluruh_jawaban() -> None:
    """VS-04 gagal → dibuang tanpa perbaikan, meski klaim lain sehat."""
    keluaran = _keluaran(_klaim("K1", "SEG-M"), _klaim("K2", "SEG-A"))
    hasil, _ = validasi(
        keluaran, segmen=(_segmen("SEG-M", indeks=IndeksTujuan.METADATA), _segmen("SEG-A"))
    )
    assert hasil.insiden_kepatuhan == (KodePemeriksaan.VS_04,)
    assert keluaran_setelah_tindakan(keluaran, hasil) is None


def test_segmen_dicabut_juga_insiden() -> None:
    keluaran = _keluaran(_klaim("K1", "SEG-C"))
    hasil, _ = validasi(keluaran, segmen=(_segmen("SEG-C", keberlakuan=StatusKeberlakuan.DICABUT),))
    assert KodePemeriksaan.VS_06 in hasil.insiden_kepatuhan


def test_klaim_bermasalah_dibuang_dan_jawaban_lanjut() -> None:
    """D-07 Bagian 6.2 baris pertama: gagal sebagian → klaim bermasalah
    dibuang, jawaban lanjut."""
    keluaran = _keluaran(_klaim("K1", "SEG-A"), _klaim("K2", "SEG-C"))
    hasil, _ = validasi(
        keluaran,
        segmen=(_segmen("SEG-A"), _segmen("SEG-C", peringkat=Peringkat.T3)),
    )
    sesudah = keluaran_setelah_tindakan(keluaran, hasil)
    assert sesudah is not None
    assert [k.id_klaim for k in sesudah.klaim] == ["K1"]


def test_seluruh_klaim_bermasalah_membatalkan_jawaban() -> None:
    keluaran = _keluaran(_klaim("K1", "SEG-C"))
    hasil, _ = validasi(keluaran, segmen=(_segmen("SEG-C", peringkat=Peringkat.T3),))
    assert keluaran_setelah_tindakan(keluaran, hasil) is None


def test_ringkasan_kosong_membatalkan_jawaban() -> None:
    """**R-06.** D-07 Bagian 6.2: "Bila ringkasan tindakan menjadi kosong,
    seluruh jawaban dibatalkan."

    Diperiksa terpisah dari "seluruh klaim bermasalah": jawaban dapat
    kehilangan ringkasannya sementara sebagian klaimnya bertahan, dan jawaban
    tanpa ringkasan tindakan bukan jawaban manajerial.
    """
    keluaran = _keluaran(_klaim("K1", "SEG-A"), ringkasan=())
    hasil, _ = validasi(keluaran, segmen=(_segmen(),))
    assert keluaran_setelah_tindakan(keluaran, hasil) is None


def test_jawaban_tanpa_klaim_sama_sekali_tetap_sah() -> None:
    """Bentuk `tidak_ditemukan` (D-14 Bagian 4.1): ringkasan dan klaim kosong.

    Ia bukan jawaban yang dibatalkan melainkan balasan tidak-ditemukan, dan
    D-05 menampilkannya sebagai jawaban sah, bukan pesan galat.
    """
    keluaran = KeluaranModel()
    hasil, _ = validasi(keluaran, segmen=())
    assert keluaran_setelah_tindakan(keluaran, hasil) is not None


# ------------------------------------------------------------ R-09, R-11, R-12


def test_jawaban_tervalidasi_hanya_dibentuk_modul_validator() -> None:
    """**R-09.** Mengikuti ADR-13. Diperiksa pada tingkat AST atas seluruh
    `src/`; pemeriksa C-19 menegakkannya pada tugas C-3, uji ini menyatakannya
    agar kegagalannya terbaca di sini."""
    import ast
    from pathlib import Path

    akar = Path(__file__).resolve().parents[3]
    diizinkan = (akar / "src" / "rag" / "validator" / "validator.py").resolve()
    pelanggaran: list[str] = []
    for berkas in sorted((akar / "src").rglob("*.py")):
        if berkas.resolve() == diizinkan:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == "JawabanTervalidasi"
            ):
                pelanggaran.append(f"{berkas.relative_to(akar)}:{simpul.lineno}")
    assert not pelanggaran, "; ".join(pelanggaran)


def test_validator_tidak_menulis_dan_tidak_memanggil_model() -> None:
    """**R-11.** C-17 melarang akses tulis dari jalur penjawaban; C-08
    menuntut seluruh pemanggilan model lewat `src/llm/`."""
    import ast
    import inspect

    import src.rag.validator.validator as modul

    pohon = ast.parse(inspect.getsource(modul))
    dipanggil = {
        s.func.attr
        for s in ast.walk(pohon)
        if isinstance(s, ast.Call) and isinstance(s.func, ast.Attribute)
    }
    assert not (dipanggil & {"write_text", "write_bytes", "mkdir", "unlink", "open"})
    assert "src.llm" not in inspect.getsource(modul)


def test_validator_tidak_memuat_satu_pun_ambang() -> None:
    """**R-12.** VS-03 dan VS-05 menuntut ambang; keduanya belum dikalibrasi,
    dan menuliskan nilai awal di sini adalah menyetel ambang (C-16)."""
    import ast
    import inspect

    import src.rag.validator.validator as modul

    pohon = ast.parse(inspect.getsource(modul))
    pecahan = [
        s.value
        for s in ast.walk(pohon)
        if isinstance(s, ast.Constant) and isinstance(s.value, float)
    ]
    assert not pecahan, f"validator memuat pecahan yang dapat menjadi ambang: {pecahan}"


def test_jawaban_tervalidasi_membawa_hasilnya() -> None:
    """Jawaban yang tervalidasi tanpa membawa hasil pemeriksaannya adalah
    jawaban yang tidak dapat ditelusuri saat audit."""
    jawaban = JawabanTervalidasi(keluaran=KeluaranModel(), hasil=_lulus_semua())
    assert jawaban.hasil.tervalidasi
