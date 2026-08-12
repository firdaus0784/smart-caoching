"""Uji gerbang putusan kurasi — B-1 fitur 010, R-02, R-07, R-08.

Dokumen: D-06 Bagian 7.3 (empat putusan) dan Bagian 7.4 (TL-01 s.d. TL-11).

**Berkas ini menguji C-06 itu sendiri.** Pasal itu berbunyi *"Butir pengetahuan
tidak tayang tanpa persetujuan kurator"*, dan yang mewujudkannya bukan sebuah
pemeriksaan melainkan sebuah **bentuk**: `ButirTayang` hanya dibentuk
`putusan.py`, sehingga fitur 011 yang menayangkan feed kelak tidak **memiliki
cara** menayangkan kandidat. Bentuk yang sama dengan `JawabanTervalidasi`
(008) dan `Instruksi` (ADR-13).

Keempat putusan dan kesebelas kode penolakan **dibaca dari `docs/D06.md`**,
bukan disalin ke berkas ini. Kode TL yang tertulis pada D-06 tidak berurutan —
TL-11 duduk di antara TL-04 dan TL-05 — dan daftar yang disalin akan
memperbaikinya diam-diam, lalu berbeda dari dokumennya tanpa seorang pun tahu.
"""

import re
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.ingest.kurasi.putusan import (
    Akibat,
    AlasanTolak,
    ButirTayang,
    GalatPutusan,
    JenisPutusan,
    PeranKurasi,
    Putusan,
    terapkan,
)
from src.kamus.segmen import StatusKeberlakuan
from src.nlp.anotasi.skema import KategoriMasalah

AKAR = Path(__file__).resolve().parents[3]


def _butir(**ganti: object) -> ButirPengetahuan:
    argumen: dict[str, object] = {
        "id_butir": "BTR-001",
        "jenis_sumber": JenisSumberButir.REGULASI,
        "judul": "Kewajiban sekolah menyusun rencana kegiatan dan anggaran",
        "alasan_relevansi": (
            "Sekolah Anda menetapkan tata kelola sebagai prioritas, "
            "dan penyusunan anggaran jatuh bulan depan."
        ),
        "inti_temuan": "Rencana kegiatan disusun bersama komite sekolah setiap tahun.",
        "implikasi_tindakan": ("Susun jadwal rapat komite sekolah.",),
        "perkiraan_waktu_baca": 3,
        "kategori": KategoriMasalah.K3,
        "id_dokumen_sumber": "DOC-001",
        "lisensi": "CC-BY-4.0",
        "status_keberlakuan": StatusKeberlakuan.BERLAKU,
        "tanggal_akses": date(2026, 8, 12),
    }
    argumen.update(ganti)
    return ButirPengetahuan(**argumen)  # type: ignore[arg-type]


def _putusan(**ganti: object) -> Putusan:
    argumen: dict[str, object] = {
        "jenis": JenisPutusan.SETUJUI,
        "id_butir": "BTR-001",
        "peran_pemutus": PeranKurasi.KURATOR,
        "waktu": datetime(2026, 8, 12, 3, 0, tzinfo=UTC),
    }
    argumen.update(ganti)
    return Putusan(**argumen)  # type: ignore[arg-type]


# ------------------------------------------------- R-07 · empat putusan setara


def _putusan_d06() -> set[str]:
    """Kolom putusan tabel D-06 Bagian 7.3 — sumbernya, bukan salinannya."""
    teks = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")
    awal = teks.index("### 7.3 Keputusan Kurasi")
    akhir = teks.index("### 7.4 Daftar Alasan Penolakan Baku")
    return {
        nama.strip().lower().replace(" ", "_")
        for nama in re.findall(r"^\|\s*\*\*(.+?)\*\*\s*\|", teks[awal:akhir], re.M)
    }


def test_keempat_putusan_d06_ada_pada_enum() -> None:
    """**Uji terpenting bagian ini**, dan ia membaca D-06 sungguhan."""
    assert _putusan_d06() == {p.value for p in JenisPutusan}


def test_tabel_7_3_memang_terbaca() -> None:
    """Pemeriksaan yang tidak menemukan sumbernya tidak memeriksa apa pun."""
    assert len(_putusan_d06()) == 4


@pytest.mark.parametrize("jenis", list(JenisPutusan))
def test_setiap_putusan_memiliki_akibat(jenis: JenisPutusan) -> None:
    """**Keempatnya setara** — tidak ada putusan yang menjadi cabang lain-lain.

    Cabang `else` akan membuat putusan kelima yang ditambahkan kelak
    diperlakukan sebagai putusan yang kebetulan berada paling akhir, dan
    D-06 Bagian 7.3 memberi keempatnya akibat yang berbeda.
    """
    assert isinstance(Akibat.bagi(jenis), Akibat)


def test_putusan_di_luar_enum_menyalakan_galat_bukan_bawaan() -> None:
    """Pemetaan berkunci, bukan berurutan. Bentuk yang sama dengan `_PETA_STATUS`
    fitur 009: yang hilang menyalakan `KeyError`, tidak mendarat pada bawaan."""
    with pytest.raises(KeyError):
        Akibat.bagi("setujui")  # type: ignore[arg-type]


def test_kedua_putusan_menyetujui_berakhir_pada_kolam() -> None:
    """D-06 Bagian 7.3: sunting-lalu-setujui "disunting pada S-16, lalu masuk
    kolam". Akibatnya sama; **jalannya** yang berbeda, dan jejak B-2 yang
    membedakannya."""
    assert Akibat.bagi(JenisPutusan.SETUJUI) is Akibat.MASUK_KOLAM
    assert Akibat.bagi(JenisPutusan.SUNTING_LALU_SETUJUI) is Akibat.MASUK_KOLAM


def test_tunda_kembali_ke_antrean_bukan_dibuang() -> None:
    assert Akibat.bagi(JenisPutusan.TUNDA) is Akibat.KEMBALI_KE_ANTREAN


def test_tolak_menjadi_umpan_balik_penyaring() -> None:
    """FR-I02: penolakan menjadi data perbaikan, bukan sekadar pembuangan."""
    assert Akibat.bagi(JenisPutusan.TOLAK) is Akibat.UMPAN_BALIK_PENYARING


# ------------------------------------------------- R-08 · alasan penolakan baku


def _kode_tl_d06() -> set[str]:
    """Kode TL pada tabel D-06 Bagian 7.4 — sumbernya, bukan salinannya."""
    teks = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")
    awal = teks.index("### 7.4 Daftar Alasan Penolakan Baku")
    akhir = teks.index("### 7.5 Penarikan Butir yang Sudah Tayang")
    return set(re.findall(r"^\|\s*(TL-\d{2})\s*\|", teks[awal:akhir], re.M))


def test_seluruh_kode_tl_d06_ada_pada_enum() -> None:
    """Kesebelasnya, dan urutannya pada D-06 memang tidak menaik.

    Daftar yang disalin akan "memperbaiki" urutan TL-11 diam-diam lalu berbeda
    dari dokumennya. Yang dibandingkan di sini himpunan, bukan urutan — sebab
    yang mengikat adalah kelengkapannya.
    """
    assert _kode_tl_d06() == {a.value for a in AlasanTolak}


def test_tabel_7_4_memang_terbaca() -> None:
    assert len(_kode_tl_d06()) == 11


def test_penolakan_wajib_membawa_kode_baku() -> None:
    """**R-08.** Penolakan tanpa kode tidak dapat menjadi umpan balik penyaring
    — ia hanya pembuangan yang tercatat."""
    with pytest.raises(ValidationError):
        _putusan(jenis=JenisPutusan.TOLAK)


def test_penolakan_menolak_untai_bebas() -> None:
    """Untai bebas mengumpul menjadi sebelas ejaan bagi satu alasan, dan
    perhitungan FR-I05 kemudian menghitung sebelas hal berbeda."""
    with pytest.raises(ValidationError):
        _putusan(jenis=JenisPutusan.TOLAK, alasan_tolak="tidak relevan")


def test_penolakan_dengan_kode_baku_diterima() -> None:
    putusan = _putusan(jenis=JenisPutusan.TOLAK, alasan_tolak=AlasanTolak.TL_01)
    assert putusan.alasan_tolak is AlasanTolak.TL_01


def test_kode_penolakan_hanya_pada_putusan_tolak() -> None:
    """Persetujuan yang membawa alasan penolakan adalah putusan yang tidak dapat
    dibaca: dua bidangnya menyatakan hal yang berlawanan."""
    with pytest.raises(ValidationError):
        _putusan(jenis=JenisPutusan.SETUJUI, alasan_tolak=AlasanTolak.TL_01)


# --------------------------------------------------------- R-07 · tunda berwaktu


def test_tunda_wajib_membawa_waktu_kembali() -> None:
    """D-06 Bagian 7.3: *"kembali ke antrean pada waktu yang ditetapkan"*.

    Tunda tanpa waktu kembali adalah penolakan yang tidak mengaku sebagai
    penolakan — butirnya tidak pernah dinilai lagi, dan alasannya tidak pernah
    tercatat sebagai umpan balik.
    """
    with pytest.raises(ValidationError):
        _putusan(jenis=JenisPutusan.TUNDA)


def test_waktu_kembali_hanya_pada_putusan_tunda() -> None:
    with pytest.raises(ValidationError):
        _putusan(jenis=JenisPutusan.SETUJUI, kembali_pada=date(2026, 9, 1))


def test_waktu_kembali_wajib_sesudah_putusan() -> None:
    """Tunda ke tanggal yang sudah lewat mengembalikan butir ke antrean seketika,
    dan antrean yang menerima butir yang baru saja ditunda akan menumpuk."""
    with pytest.raises(ValidationError):
        _putusan(jenis=JenisPutusan.TUNDA, kembali_pada=date(2026, 8, 11))


def test_tunda_ke_hari_berikutnya_diterima() -> None:
    assert _putusan(jenis=JenisPutusan.TUNDA, kembali_pada=date(2026, 8, 13))


# ------------------------------------------- R-02 · C-06, butir tayang berpagar


def test_setujui_menghasilkan_butir_tayang() -> None:
    akibat, tayang = terapkan(_butir(), _putusan())
    assert akibat is Akibat.MASUK_KOLAM
    assert tayang is not None
    assert tayang.butir.id_butir == "BTR-001"


@pytest.mark.parametrize(
    "jenis", [JenisPutusan.TOLAK, JenisPutusan.TUNDA]
)
def test_putusan_bukan_persetujuan_tidak_menghasilkan_butir_tayang(
    jenis: JenisPutusan,
) -> None:
    """**C-06.** Butir tidak tayang tanpa persetujuan kurator, dan bentuk dua
    nilai ini yang mewujudkannya: pemanggil yang hanya membaca nilai kedua tidak
    memiliki apa pun untuk ditayangkan."""
    tambahan: dict[str, object] = {
        JenisPutusan.TOLAK: {"alasan_tolak": AlasanTolak.TL_01},
        JenisPutusan.TUNDA: {"kembali_pada": date(2026, 9, 1)},
    }[jenis]
    _, tayang = terapkan(_butir(), _putusan(jenis=jenis, **tambahan))
    assert tayang is None


def test_putusan_untuk_butir_lain_ditolak() -> None:
    """Putusan yang menunjuk butir lain akan menayangkan butir yang tidak
    seorang pun nilai — bentuk paling halus dari pelanggaran C-06."""
    with pytest.raises(GalatPutusan):
        terapkan(_butir(id_butir="BTR-002"), _putusan(id_butir="BTR-001"))


def test_suntingan_wajib_pada_putusan_sunting_lalu_setujui() -> None:
    with pytest.raises(ValidationError):
        _putusan(jenis=JenisPutusan.SUNTING_LALU_SETUJUI)


def test_suntingan_yang_ditayangkan_adalah_hasil_suntingan() -> None:
    """Menayangkan naskah sebelum suntingan akan menayangkan justru parafrase
    yang kurator anggap belum memadai."""
    disunting = _butir(inti_temuan="Rencana kegiatan disusun bersama komite sekolah.")
    akibat, tayang = terapkan(
        _butir(),
        _putusan(
            jenis=JenisPutusan.SUNTING_LALU_SETUJUI, butir_suntingan=disunting
        ),
    )
    assert akibat is Akibat.MASUK_KOLAM
    assert tayang is not None
    assert tayang.butir.inti_temuan == disunting.inti_temuan


def test_suntingan_tidak_boleh_berganti_dokumen_sumber() -> None:
    """PP-02. Suntingan yang mengganti sumber bukan suntingan melainkan butir
    lain, dan penarikan FR-I06 kemudian menelusuri dokumen yang keliru."""
    with pytest.raises(GalatPutusan):
        terapkan(
            _butir(),
            _putusan(
                jenis=JenisPutusan.SUNTING_LALU_SETUJUI,
                butir_suntingan=_butir(id_dokumen_sumber="DOC-999"),
            ),
        )


def test_suntingan_tidak_boleh_berganti_identitas_butir() -> None:
    with pytest.raises(GalatPutusan):
        terapkan(
            _butir(),
            _putusan(
                jenis=JenisPutusan.SUNTING_LALU_SETUJUI,
                butir_suntingan=_butir(id_butir="BTR-002"),
            ),
        )


# ------------------------------------- C-07 lapis kedua · persetujuan tidak cukup


@pytest.mark.parametrize(
    "status", [StatusKeberlakuan.DICABUT, StatusKeberlakuan.DIUBAH]
)
def test_persetujuan_tidak_dapat_menayangkan_regulasi_tak_berlaku(
    status: StatusKeberlakuan,
) -> None:
    """**Lapis kedua C-07**, dan alasannya bukan kecurigaan terhadap kurator.

    L3 pada `saring.py` menjaga jalur ingesti. Butir dapat masuk antrean
    sebelum regulasinya dicabut, lalu dicabut sementara ia menunggu dinilai —
    dan pada saat itu L3 sudah lewat. Kurator yang menyetujuinya tidak keliru
    membaca; yang berubah terjadi sesudah ia membaca.

    D-06 Bagian 7.4 menyediakan TL-04 bagi keadaan ini.
    """
    with pytest.raises(GalatPutusan) as galat:
        terapkan(_butir(status_keberlakuan=status), _putusan())
    assert "TL-04" in str(galat.value)


def test_butir_tayang_tidak_dapat_dibentuk_atas_regulasi_tak_berlaku() -> None:
    """Penjagaannya melekat pada **bentuknya**, bukan hanya pada `terapkan`.

    Penjagaan yang hanya berada pada fungsi akan lolos begitu seseorang
    membentuk `ButirTayang` langsung — dan bentuk itulah yang M-1 tiru.
    """
    with pytest.raises(ValidationError):
        ButirTayang(
            butir=_butir(status_keberlakuan=StatusKeberlakuan.DICABUT),
            putusan=_putusan(),
        )


def test_butir_tayang_menolak_putusan_bukan_persetujuan() -> None:
    """`ButirTayang` yang membawa putusan tolak adalah butir yang tayang tanpa
    persetujuan — C-06 dilanggar oleh bentuk yang sah menurut tipenya."""
    with pytest.raises(ValidationError):
        ButirTayang(
            butir=_butir(),
            putusan=_putusan(
                jenis=JenisPutusan.TOLAK, alasan_tolak=AlasanTolak.TL_01
            ),
        )


def test_butir_tayang_menolak_putusan_atas_butir_lain() -> None:
    """Penjagaan yang sama dengan `terapkan()`, diuji pada **bentuknya**.

    `terapkan()` menutupnya lebih dulu, sehingga penjagaan pada bentuk tidak
    pernah tersentuh lewat jalur itu. Yang menyentuhnya justru pembentukan
    langsung — dan pembentukan langsung persis yang M-1 tiru.
    """
    with pytest.raises(ValidationError):
        ButirTayang(butir=_butir(id_butir="BTR-002"), putusan=_putusan())


def test_butir_riset_tidak_terkena_pemeriksaan_keberlakuan() -> None:
    akibat, tayang = terapkan(
        _butir(jenis_sumber=JenisSumberButir.RISET, status_keberlakuan=None),
        _putusan(),
    )
    assert akibat is Akibat.MASUK_KOLAM
    assert tayang is not None


# ------------------------------------------------------ R-13 · tanpa data pribadi


def test_pemutus_disebut_perannya_bukan_namanya() -> None:
    """C-05 dan KM-03. Jejak kurasi menyebut peran, bukan orang.

    Dua kurator yang berganti peran tidak perlu dibedakan namanya untuk
    menelusuri sebuah putusan; yang perlu ditelusuri adalah kewenangannya.
    """
    assert set(Putusan.model_fields) & {"nama_kurator", "surel", "id_pengguna"} == set()
    assert Putusan.model_fields["peran_pemutus"].annotation is PeranKurasi


def test_peran_kurasi_mengikuti_d06_bagian_7_1() -> None:
    assert {p.value for p in PeranKurasi} == {"kurator", "kurator_pengganti"}


def test_waktu_putusan_wajib_berzona() -> None:
    """Waktu disimpan UTC (gaya proyek). Waktu tanpa zona dari dua mesin tidak
    dapat diurutkan, dan urutan putusan adalah yang FR-I05 tanyakan."""
    with pytest.raises(ValidationError):
        _putusan(waktu=datetime(2026, 8, 12, 3, 0))


def test_putusan_beku() -> None:
    with pytest.raises(ValidationError):
        _putusan().jenis = JenisPutusan.TOLAK  # type: ignore[misc]


def test_butir_tayang_beku() -> None:
    _, tayang = terapkan(_butir(), _putusan())
    assert tayang is not None
    with pytest.raises(ValidationError):
        tayang.butir = _butir()  # type: ignore[misc]
