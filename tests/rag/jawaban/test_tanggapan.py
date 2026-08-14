"""Uji bentuk tanggapan — B-1 dan B-2 fitur 009, R-01, R-04 s.d. R-09, C-20.

**Ini C-20 itu sendiri.** D-14 menyatakan alasannya dalam satu kalimat:
*"bentuk itu adalah tempat C-02, C-07, dan C-19 diwujudkan."*

Bidang tambahan yang tampak tidak berbahaya — `skor_keyakinan`,
`waktu_proses` — memindahkan penilaian dari sistem ke klien, dan klien tidak
terikat konstitusi.

## Bidang dibaca dari D-14, tidak disalin ke sini

Uji yang menyalin daftar bidangnya hanya membuktikan **dua salinan sama** —
termasuk ketika keduanya sudah menyimpang dari D-14. Bentuk yang sama dengan
`test_ambang_kesepakatan.py` fitur 003, yang membaca angkanya dari `docs/D03.md`
sungguhan alih-alih menyalinnya.
"""

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.kamus.segmen import StatusKeberlakuan
from src.rag.jawaban.tanggapan import (
    BacaanLanjutan,
    Sitasi,
    StatusDasar,
    Tanggapan,
    Versi,
)

AKAR = Path(__file__).resolve().parents[3]


def _bidang_d14() -> set[str]:
    """Kunci blok JSON `docs/D14.md` Bagian 4.1 — sumbernya, bukan salinannya."""
    teks = (AKAR / "docs" / "D14.md").read_text(encoding="utf-8")
    awal = teks.index("### 4.1 Tanggapan Jawaban")
    blok = re.search(r"```json\n(.*?)\n```", teks[awal:], re.S)
    assert blok is not None, "blok JSON Bagian 4.1 tidak ditemukan pada D-14"
    return set(json.loads(blok.group(1)).keys())


def _versi() -> Versi:
    return Versi(model="tiruan-1", indeks="leksikal-7", kode="abc1234")


def _sitasi(**ganti: object) -> Sitasi:
    argumen: dict[str, object] = {
        "id_dokumen": "DOC-1",
        "judul": "Permendikdasmen Nomor 1 Tahun 2026",
        "penerbit": "Kemendikdasmen",
        "tahun": 2026,
        "bagian": "Pasal 7 ayat (2)",
        "status_keberlakuan": StatusKeberlakuan.BERLAKU,
        "rujukan_pengganti": None,
        "tautan": None,
    }
    argumen.update(ganti)
    return Sitasi(**argumen)  # type: ignore[arg-type]


# ------------------------------------------------------------------ R-01, C-20


def test_bidang_tanggapan_persis_d14_bagian_4_1() -> None:
    """**Uji terpenting berkas ini**, dan ia membaca D-14 sungguhan.

    Kurang maupun lebih keduanya kekeliruan: AG-03 melarang penambahan, dan
    pengurangan menghapus tempat C-02, C-07, atau C-19 diwujudkan.
    """
    assert set(Tanggapan.model_fields) == _bidang_d14()


def test_bidang_tambahan_ditolak() -> None:
    """AG-03. `extra="forbid"` membuat bidang yang diselundupkan tertolak saat
    diurai, bukan diteruskan diam-diam ke klien."""
    with pytest.raises(ValidationError):
        Tanggapan(  # type: ignore[call-arg]
            id_pesan="msg_1",
            status_dasar=StatusDasar.TIDAK_DITEMUKAN,
            penafian="Keputusan akhir pada kepala sekolah.",
            versi=_versi(),
            skor_keyakinan=0.9,
        )


def test_tanggapan_beku() -> None:
    tanggapan = Tanggapan.tidak_ditemukan(id_pesan="msg_1", versi=_versi())
    with pytest.raises(ValidationError):
        tanggapan.status_dasar = StatusDasar.KUAT  # type: ignore[misc]


# ------------------------------------------------------------------------ R-04


@pytest.mark.parametrize("status", [StatusDasar.TIDAK_DITEMUKAN, StatusDasar.DI_LUAR_DOMAIN])
def test_penolakan_menuntut_ringkasan_dan_klaim_kosong(status: StatusDasar) -> None:
    """D-14 Bagian 4.1: kedua keadaan memakai **bentuk yang sama** dengan
    ringkasan dan klaim kosong.

    "Bentuk yang seragam inilah yang membuat layar D-05 dapat menampilkannya
    sebagai jawaban sah, bukan pesan galat."
    """
    with pytest.raises(ValidationError) as galat:
        Tanggapan(
            id_pesan="msg_1",
            status_dasar=status,
            ringkasan_tindakan=("Susun RKAS.",),
            penafian="Keputusan akhir pada kepala sekolah.",
            versi=_versi(),
        )
    assert "kosong" in str(galat.value).lower()


def test_penolakan_berbentuk_jawaban_bukan_galat() -> None:
    """`tolak_domain` menghasilkan `Tanggapan` yang sah, bukan menaikkan galat.

    D-02 titik kritis T3: sistem yang mengaku tidak tahu justru memperkuat
    kepercayaan.
    """
    tanggapan = Tanggapan.tolak_domain(id_pesan="msg_1", versi=_versi())
    assert tanggapan.status_dasar is StatusDasar.DI_LUAR_DOMAIN
    assert tanggapan.ringkasan_tindakan == ()
    assert tanggapan.klaim == ()
    assert "manajemen sekolah dasar" in tanggapan.penjelasan.lower()


def test_tidak_ditemukan_juga_berbentuk_jawaban() -> None:
    tanggapan = Tanggapan.tidak_ditemukan(id_pesan="msg_1", versi=_versi())
    assert tanggapan.status_dasar is StatusDasar.TIDAK_DITEMUKAN
    assert tanggapan.klaim == ()


# ------------------------------------------------------------------ R-05, R-06


def test_penafian_wajib_dan_tidak_boleh_kosong() -> None:
    """**FR-F10.** Penafian yang boleh kosong adalah penafian yang akan kosong
    pada tanggapan yang disusun tergesa."""
    assert Tanggapan.model_fields["penafian"].is_required()
    with pytest.raises(ValidationError):
        Tanggapan(
            id_pesan="msg_1",
            status_dasar=StatusDasar.TIDAK_DITEMUKAN,
            penafian="  ",
            versi=_versi(),
        )


def test_versi_wajib_memuat_ketiganya() -> None:
    """KT-06. Tanggapan tanpa versi adalah tanggapan yang tidak dapat
    ditelusuri ketika seseorang melaporkan arahan yang keliru (ET-11)."""
    for bidang in ("model", "indeks", "kode"):
        assert Versi.model_fields[bidang].is_required()


# ------------------------------------------------------------------ R-07, R-08


def test_sitasi_dicabut_tidak_dapat_dibentuk() -> None:
    """**R-08, C-07.** D-07 Bagian 4.5: menjawab berdasarkan aturan yang sudah
    dicabut adalah bentuk kekeliruan yang paling merugikan, **karena jawabannya
    terdengar berdasar**.

    Lapisan kedua sesudah VS-06: yang lolos validator lewat jalur lain tetap
    tidak dapat tayang.
    """
    with pytest.raises(ValidationError) as galat:
        _sitasi(status_keberlakuan=StatusKeberlakuan.DICABUT)
    assert "dicabut" in str(galat.value).lower()


def test_sitasi_diubah_menuntut_catatan_keberlakuan() -> None:
    """**R-07, FR-F14.** D-07 Bagian 4.5: segmen `diubah` dipakai, tetapi
    jawaban **wajib** menampilkan penanda dan rujukan pengubahnya."""
    with pytest.raises(ValidationError) as galat:
        Tanggapan(
            id_pesan="msg_1",
            status_dasar=StatusDasar.TERBATAS,
            ringkasan_tindakan=("Susun RKAS bersama komite sekolah.",),
            penjelasan="Penjelasan.",
            sitasi=(_sitasi(status_keberlakuan=StatusKeberlakuan.DIUBAH),),
            catatan_keberlakuan="",
            penafian="Keputusan akhir pada kepala sekolah.",
            versi=_versi(),
        )
    assert "keberlakuan" in str(galat.value).lower()


def test_sitasi_diubah_dengan_catatan_diterima() -> None:
    tanggapan = Tanggapan(
        id_pesan="msg_1",
        status_dasar=StatusDasar.TERBATAS,
        ringkasan_tindakan=("Susun RKAS bersama komite sekolah.",),
        penjelasan="Penjelasan.",
        sitasi=(
            _sitasi(
                status_keberlakuan=StatusKeberlakuan.DIUBAH,
                rujukan_pengganti="Permendikdasmen Nomor 4 Tahun 2026",
            ),
        ),
        catatan_keberlakuan="Pasal ini telah diubah; rujuk peraturan pengubahnya.",
        penafian="Keputusan akhir pada kepala sekolah.",
        versi=_versi(),
    )
    assert tanggapan.catatan_keberlakuan


def test_catatan_keberlakuan_kosong_ketika_seluruh_sitasi_berlaku() -> None:
    """D-14: "kosong bila seluruh sumber berstatus `berlaku`".

    Catatan yang terisi tanpa sebab akan diabaikan pembacanya, dan yang
    diabaikan tidak menjaga apa pun ketika ia sungguh perlu.
    """
    with pytest.raises(ValidationError):
        Tanggapan(
            id_pesan="msg_1",
            status_dasar=StatusDasar.TERBATAS,
            ringkasan_tindakan=("Susun RKAS bersama komite sekolah.",),
            penjelasan="Penjelasan.",
            sitasi=(_sitasi(),),
            catatan_keberlakuan="Ada yang diubah.",
            penafian="Keputusan akhir pada kepala sekolah.",
            versi=_versi(),
        )


def test_sitasi_wajib_membawa_bagian() -> None:
    """**FR-F11**, titik kritis T2 pada D-02: tautan mengarah ke pasal, bukan
    ke dokumen utuh. `penanda_bagian` sudah wajib sejak fitur 007; di sini ia
    wajib pada penampilannya."""
    with pytest.raises(ValidationError):
        _sitasi(bagian="")


# ------------------------------------------------------------------------ R-09


def test_bacaan_lanjutan_tempat_satu_satunya_bagi_indeks_metadata() -> None:
    """**R-09, C-02, D-14 Bagian 6.**

    `BacaanLanjutan` sengaja **tidak** memiliki bidang yang dimiliki `Sitasi` —
    tidak ada `bagian`, tidak ada `status_keberlakuan`. Ia bukan sitasi yang
    lebih lemah melainkan hal lain: D-07 Bagian 7 menyatakan isinya "tidak
    dipakai menyusun jawaban", dan bentuk yang berbeda membuat kekeliruan
    memindahkannya tertangkap tipe.
    """
    assert set(BacaanLanjutan.model_fields) == {"judul", "tautan"}
    assert "bagian" not in BacaanLanjutan.model_fields
    assert "status_keberlakuan" not in BacaanLanjutan.model_fields


def test_sitasi_dan_bacaan_lanjutan_bertipe_berbeda() -> None:
    """Bidang `sitasi` tidak menerima `BacaanLanjutan`.

    Tanpa pembedaan tipe, memindahkan sumber `indeks_metadata` ke `sitasi`
    adalah satu baris yang tidak menggagalkan apa pun sampai audit lisensi.
    """
    with pytest.raises(ValidationError):
        Tanggapan(
            id_pesan="msg_1",
            status_dasar=StatusDasar.TERBATAS,
            ringkasan_tindakan=("Susun RKAS bersama komite sekolah.",),
            penjelasan="Penjelasan.",
            sitasi=(BacaanLanjutan(judul="Artikel", tautan="https://a.contoh/x"),),  # type: ignore[arg-type]
            penafian="Keputusan akhir pada kepala sekolah.",
            versi=_versi(),
        )


# ------------------------------------------------------------------------ R-11


def test_butir_ringkasan_melampaui_dua_puluh_kata_ditolak() -> None:
    """NFR-19, C-13. Ia teks yang dibaca kepala sekolah di sela kegiatan."""
    with pytest.raises(ValidationError):
        Tanggapan(
            id_pesan="msg_1",
            status_dasar=StatusDasar.TERBATAS,
            ringkasan_tindakan=(" ".join(["kata"] * 21) + ".",),
            penjelasan="Penjelasan.",
            penafian="Keputusan akhir pada kepala sekolah.",
            versi=_versi(),
        )


def test_lebih_dari_tiga_butir_ringkasan_ditolak() -> None:
    """D-07 Bagian 5.1 dan FR-F05: maksimal 3 butir."""
    with pytest.raises(ValidationError):
        Tanggapan(
            id_pesan="msg_1",
            status_dasar=StatusDasar.TERBATAS,
            ringkasan_tindakan=("Satu.", "Dua.", "Tiga.", "Empat."),
            penjelasan="Penjelasan.",
            penafian="Keputusan akhir pada kepala sekolah.",
            versi=_versi(),
        )
