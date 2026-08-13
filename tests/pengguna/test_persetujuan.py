"""Uji persetujuan penelitian — B-1 fitur 022, R-05, R-06, R-08, FR-A05.

**Berkas ini adalah prasyarat C-04.** Pasal itu berbunyi *"telemetri tidak
merekam bagi pengguna tanpa persetujuan aktif; pencabutan menghentikan
perekaman seketika"*, dan `boleh_merekam` di sini adalah satu-satunya sifat
yang fitur 012 kelak tanyakan.

## Empat keadaan, dan dua pembedaan yang mudah hilang

Kosakatanya milik D-14 Bagian 5.1, yang sudah menetapkannya bagi persetujuan
pemilik dokumen: `belum_diminta`, `diberikan`, `ditolak`, `dicabut`.

**`belum_diminta` bukan `ditolak`.** Keduanya menghentikan perekaman, tetapi
yang pertama pekerjaan yang belum dilakukan dan yang kedua keputusan
partisipan. Menyamakannya membuat laporan partisipasi tidak dapat membedakan
orang yang menolak dari orang yang belum ditanya.

**`ditolak` bukan `dicabut`.** WMA Declaration of Helsinki menyebut hak menolak
dan hak mencabut kapan saja sebagai dua hal (D-11 Bagian 3.6). Sistem yang
hanya mengenal satu memaksa pencabutan dicatat sebagai penolakan — lalu data
yang sudah terekam sebelum pencabutan kehilangan penjelasannya.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from src.pengguna.persetujuan import (
    CatatanPersetujuan,
    JenisPersetujuan,
    KeadaanPersetujuan,
)

AKAR = Path(__file__).resolve().parents[2]

DIBERIKAN_PADA = datetime(2026, 8, 1, 2, 0, tzinfo=UTC)


def _catatan(**ganti: object) -> CatatanPersetujuan:
    argumen: dict[str, object] = {
        "id_pengguna": "PGN-001",
        "jenis": JenisPersetujuan.PENELITIAN,
        "versi_naskah": "ET-02 v1.0",
        "disetujui": True,
        "tanggal": DIBERIKAN_PADA,
    }
    argumen.update(ganti)
    return CatatanPersetujuan(**argumen)  # type: ignore[arg-type]


# ------------------------------------------------------------ R-05 · empat keadaan


def test_empat_keadaan_tidak_kurang_tidak_lebih() -> None:
    assert {k.value for k in KeadaanPersetujuan} == {
        "belum_diminta",
        "diberikan",
        "ditolak",
        "dicabut",
    }


def test_kosakata_sama_dengan_d14() -> None:
    """D-14 Bagian 5.1 sudah menetapkan keempat nilai ini bagi persetujuan
    pemilik dokumen. Kosakata kedua bagi hal yang sama akan membuat dua bagian
    sistem menyebut keadaan yang sama dengan dua nama."""
    teks = (AKAR / "docs" / "D14.md").read_text(encoding="utf-8")
    for nilai in ("belum_diminta", "diberikan", "ditolak", "dicabut"):
        assert f"`{nilai}`" in teks, nilai


def test_tanpa_catatan_berarti_belum_diminta() -> None:
    """Ketiadaan catatan adalah keadaan, bukan kekosongan yang perlu ditebak.

    Fungsi ini ada justru agar pemanggil tidak menuliskan `if catatan is None`
    sendiri — dan tidak menyimpulkan `ditolak` darinya.
    """
    assert KeadaanPersetujuan.dari(None) is KeadaanPersetujuan.BELUM_DIMINTA


def test_belum_diminta_berbeda_dari_ditolak() -> None:
    """**Uji terpenting pertama.** Keduanya menghentikan perekaman, dan justru
    karena itu godaan menyatukannya besar.

    Laporan partisipasi yang tidak dapat membedakan orang yang menolak dari
    orang yang belum ditanya tidak dapat menjawab apakah pengambilan data sudah
    lengkap.
    """
    belum = KeadaanPersetujuan.dari(None)
    ditolak = KeadaanPersetujuan.dari(_catatan(disetujui=False))
    assert belum is not ditolak
    assert not belum.boleh_merekam
    assert not ditolak.boleh_merekam


def test_ditolak_berbeda_dari_dicabut() -> None:
    """**Uji terpenting kedua** — Helsinki menyebut hak menolak dan hak mencabut
    sebagai dua hal (D-11 Bagian 3.6).

    Pencabutan yang dicatat sebagai penolakan membuat data yang sudah terekam
    sebelum pencabutan kehilangan penjelasannya.
    """
    ditolak = KeadaanPersetujuan.dari(_catatan(disetujui=False))
    dicabut = KeadaanPersetujuan.dari(
        _catatan(dicabut_pada=datetime(2026, 9, 1, tzinfo=UTC))
    )
    assert ditolak is not dicabut
    assert ditolak is KeadaanPersetujuan.DITOLAK
    assert dicabut is KeadaanPersetujuan.DICABUT


def test_diberikan_tanpa_pencabutan() -> None:
    assert KeadaanPersetujuan.dari(_catatan()) is KeadaanPersetujuan.DIBERIKAN


# --------------------------------------------------- R-06 · C-04, perekaman


def test_hanya_diberikan_yang_mengizinkan_perekaman() -> None:
    """**C-04.** Disapu atas seluruh keadaan, bukan atas daftar yang disalin —
    keadaan kelima yang ditambahkan kelak menyalakan uji ini."""
    for keadaan in KeadaanPersetujuan:
        harapan = keadaan is KeadaanPersetujuan.DIBERIKAN
        assert keadaan.boleh_merekam is harapan, keadaan


def test_pencabutan_menghentikan_perekaman() -> None:
    """`persetujuan.dicabut_pada` (D-14 Bagian 5.1): *"bila terisi, perekaman
    telemetri berhenti seketika"* — FR-J05."""
    dicabut = _catatan(dicabut_pada=datetime(2026, 9, 1, tzinfo=UTC))
    assert not KeadaanPersetujuan.dari(dicabut).boleh_merekam
    assert not dicabut.boleh_merekam


def test_boleh_merekam_sifat_terhitung_bukan_bidang() -> None:
    """Bidang dapat diisi `True` oleh pemanggil yang lelah, dan yang dilewati
    bersamanya adalah C-04."""
    assert "boleh_merekam" not in CatatanPersetujuan.model_fields
    with pytest.raises(ValidationError):
        _catatan(boleh_merekam=True)


# ---------------------------------------- gabungan mustahil ditolak saat dibentuk


def test_penolakan_yang_membawa_waktu_pencabutan_ditolak() -> None:
    """**Baris terakhir tabel `plan.md` Bagian 2.2.**

    Penolakan yang membawa waktu pencabutan tidak berarti apa pun — tidak ada
    yang dicabut. Yang tidak berarti apa pun akan ditafsirkan berbeda oleh dua
    pembaca, dan salah satu tafsiran itu mengizinkan perekaman.
    """
    with pytest.raises(ValidationError):
        _catatan(disetujui=False, dicabut_pada=datetime(2026, 9, 1, tzinfo=UTC))


def test_pencabutan_tidak_boleh_mendahului_persetujuan() -> None:
    """Perekaman berhenti sebelum ia diizinkan adalah keadaan yang tidak dapat
    terjadi."""
    with pytest.raises(ValidationError):
        _catatan(dicabut_pada=datetime(2026, 7, 1, tzinfo=UTC))


def test_pencabutan_pada_saat_yang_sama_ditolak() -> None:
    """Sama persis juga mustahil: persetujuan yang dicabut pada detik yang sama
    tidak pernah berlaku, dan mencatatnya sebagai pernah berlaku keliru."""
    with pytest.raises(ValidationError):
        _catatan(dicabut_pada=DIBERIKAN_PADA)


# --------------------------------------------------------- R-08 · versi naskah


def test_versi_naskah_wajib() -> None:
    """**R-08.** Persetujuan tanpa naskah yang dapat ditunjuk bukan persetujuan.

    Helsinki menempatkan **keterangan** sebagai salah satu dari tiga unsur
    persetujuan (D-11 Bagian 3.6); tanpa versi naskah, tidak ada cara mengetahui
    keterangan apa yang partisipan baca.
    """
    with pytest.raises(ValidationError):
        _catatan(versi_naskah="")
    with pytest.raises(ValidationError):
        _catatan(versi_naskah="   ")


def test_versi_naskah_tidak_dapat_dilewatkan() -> None:
    """**Uji yang menutup mutasi yang selamat.**

    Menolak untai kosong dan menuntut bidangnya diisi adalah dua hal. Bidang
    berbawaan `""` lolos pemeriksaan isi karena validator pydantic tidak
    berjalan atas nilai bawaan — sehingga persetujuan tanpa naskah terbentuk
    diam-diam, dan tidak satu uji pun menyala.

    Ditemukan uji mutasi 13 Agustus 2026, bukan oleh mata.
    """
    assert CatatanPersetujuan.model_fields["versi_naskah"].is_required()
    with pytest.raises(ValidationError):
        CatatanPersetujuan(  # type: ignore[call-arg]
            id_pengguna="PGN-001",
            jenis=JenisPersetujuan.PENELITIAN,
            disetujui=True,
            tanggal=DIBERIKAN_PADA,
        )


def test_seluruh_bidang_selain_pencabutan_wajib() -> None:
    """Alasan yang sama pada bidang lain: bidang berbawaan pada catatan
    persetujuan akan terisi diam-diam, dan yang terisi diam-diam tidak pernah
    ditinjau siapa pun.

    `dicabut_pada` **memang** boleh kosong — itu keadaan yang sah, bukan bidang
    yang lupa diisi.
    """
    for bidang in ("id_pengguna", "jenis", "versi_naskah", "disetujui", "tanggal"):
        assert CatatanPersetujuan.model_fields[bidang].is_required(), bidang
    assert not CatatanPersetujuan.model_fields["dicabut_pada"].is_required()


def test_versi_naskah_tercatat_apa_adanya() -> None:
    assert _catatan(versi_naskah="ET-02 v2.1").versi_naskah == "ET-02 v2.1"


# ------------------------------------------------------------------- R-12 · waktu


def test_waktu_wajib_berzona() -> None:
    """KM-01. Waktu tanpa zona dari dua mesin tidak dapat diurutkan, dan urutan
    persetujuan-lalu-pencabutan adalah yang C-04 tanyakan."""
    with pytest.raises(ValidationError):
        _catatan(tanggal=datetime(2026, 8, 1, 2, 0))
    with pytest.raises(ValidationError):
        _catatan(dicabut_pada=datetime(2026, 9, 1))


def test_catatan_beku() -> None:
    """Catatan persetujuan yang dapat disunting tidak membuktikan apa pun
    tentang apa yang partisipan setujui."""
    with pytest.raises(ValidationError):
        _catatan().disetujui = False  # type: ignore[misc]


def test_bidang_mengikuti_d04() -> None:
    """D-04 Bagian 7.1: `persetujuan` — id_pengguna, jenis, versi_naskah,
    disetujui, tanggal, dicabut_pada."""
    teks = (AKAR / "docs" / "D04.md").read_text(encoding="utf-8")
    baris = next(g for g in teks.splitlines() if g.startswith("| `persetujuan`"))
    diharapkan = {n.strip() for n in baris.split("|")[2].split(",")}
    assert diharapkan == set(CatatanPersetujuan.model_fields)


# ═══════════════════════════════ B-2 · R-07 ═══════════════════════════════
#
# FR-A05 menjamin "opsi menolak tanpa kehilangan akses fitur inti", dan WMA
# Declaration of Helsinki merumuskannya sebagai hak menolak atau mencabut
# "tanpa akibat merugikan" (D-11 Bagian 3.6).
#
# Itu **larangan**, dan larangan tidak dapat dibuktikan dengan menjalankan apa
# pun — tidak ada masukan yang membuktikan sesuatu tidak terjadi. Yang dapat
# diuji adalah bentuknya: cara paling kokoh menjamin sebuah larangan adalah
# tidak menyediakan alatnya.
#
# Bentuk yang sama dengan C-17 pada fitur 001 dan `JejakKurasi` yang tidak
# menyediakan cara menyunting.

_KOSAKATA_AKSES = (
    "akses",
    "izin",
    "hak_",
    "boleh_akses",
    "tingkat",
    "batasi",
    "kunci",
    "nonaktif",
    "fitur",
)
"""Kata yang menandakan pemetaan persetujuan ke tingkat akses.

Daftar hitam, bukan daftar putih — dan arahnya disengaja. Daftar putih akan
menuntut setiap nama baru didaftarkan, dan yang lupa didaftarkan justru lolos.
Di sini kekeliruan ke arah ketat hanya menuntut penamaan ulang, sedangkan
kekeliruan ke arah longgar meloloskan pelanggaran R-07.
"""


def test_modul_tidak_menyediakan_cara_menurunkan_akses() -> None:
    """**R-07 sebagai ketiadaan.**

    Permukaan modul tidak boleh memuat apa pun yang memetakan keadaan
    persetujuan ke tingkat akses. `boleh_merekam` adalah satu-satunya sifat
    yang boleh bergantung pada persetujuan, dan ia soal **perekaman**, bukan
    soal akses.
    """
    dari_modul = set()
    for tipe in (CatatanPersetujuan, KeadaanPersetujuan):
        dari_modul |= {n for n in dir(tipe) if not n.startswith("_")}
    dari_modul -= set(CatatanPersetujuan.model_fields)

    tercurigai = {
        n for n in dari_modul if any(k in n.lower() for k in _KOSAKATA_AKSES)
    }
    assert tercurigai == set(), (
        f"permukaan modul memuat nama yang menyiratkan pemetaan ke akses: "
        f"{sorted(tercurigai)} — FR-A05 menjamin menolak tidak mengurangi akses"
    )


def test_satu_satunya_sifat_yang_bergantung_pada_persetujuan_adalah_perekaman() -> None:
    """Pernyataan yang lebih tegas daripada uji di atas, dan ia disebut namanya.

    Bila kelak sebuah sifat baru bergantung pada persetujuan, uji ini menyala
    dan seseorang wajib menyatakan mengapa — alih-alih menambahkannya diam-diam
    di sebelah `boleh_merekam`.
    """
    def _sifat(tipe: type) -> set[str]:
        return {
            n
            for n in dir(tipe)
            if not n.startswith("_") and isinstance(getattr(tipe, n, None), property)
        }

    # Sifat bawaan pydantic disingkirkan dengan membandingkan terhadap
    # `BaseModel`, bukan dengan mendaftarkan namanya — daftar nama akan
    # tertinggal pada hari pydantik menambah sifat baru.
    milik_modul = _sifat(CatatanPersetujuan) - _sifat(BaseModel)
    assert milik_modul == {"keadaan", "boleh_merekam"}


def test_berkas_tidak_menyebut_penurunan_akses() -> None:
    """Sapuan atas naskah modulnya sendiri, bukan hanya atas permukaannya.

    Fungsi tingkat modul yang tidak terbaca `dir()` pada kedua tipe tetap dapat
    memetakan persetujuan ke akses — dan itu bentuk yang paling mungkin
    ditambahkan seseorang yang terburu-buru.
    """
    isi = (AKAR / "src" / "pengguna" / "persetujuan.py").read_text(encoding="utf-8")
    baris_kode = [
        b
        for b in isi.splitlines()
        if b.startswith("def ") or b.startswith("    def ")
    ]
    tercurigai = [
        b for b in baris_kode if any(k in b.lower() for k in _KOSAKATA_AKSES)
    ]
    assert tercurigai == [], tercurigai


def test_menolak_dan_mencabut_tetap_menghasilkan_catatan_yang_sah() -> None:
    """Sisi perilaku R-07: penolakan dan pencabutan adalah catatan yang sah
    sepenuhnya, bukan keadaan cacat yang perlu ditangani sebagai galat.

    Sistem yang memperlakukan penolakan sebagai kegagalan akan menemukan jalan
    untuk menghukumnya.
    """
    ditolak = _catatan(disetujui=False)
    dicabut = _catatan(dicabut_pada=datetime(2026, 9, 1, tzinfo=UTC))
    for catatan in (ditolak, dicabut):
        assert catatan.versi_naskah
        assert catatan.id_pengguna == "PGN-001"
        assert catatan.keadaan in set(KeadaanPersetujuan)
