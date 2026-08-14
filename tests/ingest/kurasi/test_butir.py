"""Uji butir pengetahuan — A-1 fitur 010, R-01, D-06 Bagian 5.

Bidangnya **dibaca dari `docs/D06.md`**, bukan disalin ke berkas ini. Uji yang
menyalin daftarnya hanya membuktikan dua salinan sama — termasuk ketika
keduanya sudah menyimpang dari pemiliknya. Bentuk yang sama dengan
`test_ambang_kesepakatan.py` (003), pemeriksa arah (009), dan pemeriksa C-20
(009).

**Satu bidang ditambahkan di luar D-06, dan ia dinyatakan tegas.** Uji di bawah
tidak sekadar mengizinkan bidang tambahan; ia menyebut namanya satu per satu.
Daftar putih yang berbunyi "boleh ada tambahan" adalah daftar yang akan
ditambahi.
"""

import re
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.ingest.kurasi.butir import (
    ButirPengetahuan,
    JenisSumberButir,
)
from src.kamus.segmen import StatusKeberlakuan
from src.nlp.anotasi.skema import KategoriMasalah

AKAR = Path(__file__).resolve().parents[3]

TAMBAHAN_SAH = {"id_butir"}
"""Bidang di luar D-06 Bagian 5, beserta alasannya.

`id_butir` — D-06 Bagian 5 menetapkan **bentuk tampilan** butir, bukan
identitasnya. Antrean kurasi, jejak audit FR-I05 ("apa"), dan penarikan FR-I06
seluruhnya menuntut cara menunjuk satu butir tertentu. Tanpa penanda, jejak
kurasi hanya dapat menyebut "sebuah butir".
"""


def _bidang_d06() -> set[str]:
    """Bidang pada tabel D-06 Bagian 5 — sumbernya, bukan salinannya."""
    teks = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")
    awal = teks.index("## 5. Format Butir Pengetahuan")
    akhir = teks.index("## 6. Aturan Penyaringan Otomatis")
    return set(re.findall(r"^\|\s*`(\w+)`\s*\|", teks[awal:akhir], re.M))


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


# ------------------------------------------------------------------------ R-01


def test_seluruh_bidang_d06_ada_pada_butir() -> None:
    """**Uji terpenting berkas ini**, dan ia membaca D-06 sungguhan.

    Dua belas bidang D-06 Bagian 5 wajib ada. Bidang yang hilang adalah bidang
    yang tidak dapat ditampilkan pada layar S-06, dan D-06 menetapkan
    keduabelasnya mengikat FR-G02.
    """
    hilang = _bidang_d06() - set(ButirPengetahuan.model_fields)
    assert not hilang, f"bidang D-06 Bagian 5 yang hilang: {sorted(hilang)}"


def test_tambahan_di_luar_d06_disebut_satu_per_satu() -> None:
    """**Bukan "boleh ada tambahan".**

    Daftar putih yang berbunyi "boleh ada tambahan" adalah daftar yang akan
    ditambahi. Yang ditambahkan wajib disebut namanya, dan alasannya tertulis
    pada `TAMBAHAN_SAH`.
    """
    tambahan = set(ButirPengetahuan.model_fields) - _bidang_d06()
    assert tambahan == TAMBAHAN_SAH, (
        f"bidang di luar D-06 Bagian 5 yang belum dinyatakan: {sorted(tambahan - TAMBAHAN_SAH)}"
    )


def test_d06_memang_terbaca() -> None:
    """Pemeriksaan yang tidak menemukan sumbernya tidak memeriksa apa pun.

    Tanpa uji ini, perubahan judul bagian pada D-06 akan membuat kedua uji di
    atas membandingkan terhadap himpunan kosong — dan keduanya lulus.
    """
    assert len(_bidang_d06()) == 12


def test_kategori_dipakai_ulang_bukan_ditulis_ulang() -> None:
    """**Pertanyaan 2 Gerbang 1.**

    D-06 Bagian 5 merujuk "D-03 Bagian 5" bagi `kategori`, dan
    `KategoriMasalah` sudah mewujudkannya sejak fitur 003. Enum kedua akan
    mengulangi kekeliruan `IndeksTujuan` yang ditulis dua kali dan lolos dua
    fitur (KB-036).
    """
    assert ButirPengetahuan.model_fields["kategori"].annotation is KategoriMasalah


def test_bidang_wajib_tanpa_nilai_bawaan() -> None:
    """Bidang berbawaan pada butir yang disusun tergesa akan terisi diam-diam,
    dan yang terisi diam-diam tidak pernah ditinjau kurator."""
    for bidang in (
        "jenis_sumber",
        "judul",
        "alasan_relevansi",
        "inti_temuan",
        "kategori",
        "id_dokumen_sumber",
        "lisensi",
        "tanggal_akses",
    ):
        assert ButirPengetahuan.model_fields[bidang].is_required(), bidang


def test_status_keberlakuan_boleh_kosong_bagi_sumber_bukan_regulasi() -> None:
    """`None` bukan nilai yang hilang: riset dan praktik baik tidak memiliki
    status keberlakuan.

    Memaksanya berisi akan membuat setiap butir riset mengaku `berlaku`, dan
    L3 kemudian memeriksa hal yang tidak berarti apa-apa.
    """
    butir = _butir(jenis_sumber=JenisSumberButir.RISET, status_keberlakuan=None)
    assert butir.status_keberlakuan is None
    assert not butir.bersumber_regulasi


def test_butir_regulasi_ditandai_untuk_lapis_l3() -> None:
    assert _butir(jenis_sumber=JenisSumberButir.REGULASI).bersumber_regulasi


# ----------------------------------------------------------- batas D-06 Bagian 5


def test_judul_melampaui_dua_belas_kata_ditolak() -> None:
    with pytest.raises(ValidationError):
        _butir(judul=" ".join(["kata"] * 13))


def test_judul_tepat_dua_belas_kata_diterima() -> None:
    """Batasnya "maksimal 12", bukan "kurang dari 12". Uji satu arah
    membiarkan penjagaannya digeser satu kata tanpa dasar."""
    assert _butir(judul=" ".join(["kata"] * 12))


def test_inti_temuan_melampaui_seratus_dua_puluh_kata_ditolak() -> None:
    with pytest.raises(ValidationError):
        _butir(inti_temuan=" ".join(["kata"] * 121))


def test_implikasi_tindakan_satu_sampai_tiga_butir() -> None:
    """D-06 Bagian 5: 1-3 butir. Nol berarti butir tanpa jalan keluar, dan
    TL-09 menolak butir semacam itu — "memberi kesan berpengetahuan tanpa
    memberi jalan keluar"."""
    with pytest.raises(ValidationError):
        _butir(implikasi_tindakan=())
    with pytest.raises(ValidationError):
        _butir(implikasi_tindakan=("Satu.", "Dua.", "Tiga.", "Empat."))
    assert _butir(implikasi_tindakan=("Satu.", "Dua.", "Tiga."))


def test_waktu_baca_melampaui_tujuh_menit_ditolak() -> None:
    """FR-G03 dan D-06 Bagian 5: ≤ 7 menit.

    Butir yang menuntut lebih lama tidak akan dibaca kepala sekolah di sela
    kegiatan, dan rasio penemuan D-01 Bagian 9.1 mengukurnya.
    """
    with pytest.raises(ValidationError):
        _butir(perkiraan_waktu_baca=8)
    assert _butir(perkiraan_waktu_baca=7)


def test_lisensi_kosong_ditolak() -> None:
    """KL-02: wajib terisi; kosong berarti tidak dapat tayang.

    Ditegakkan tipe **dan** lapis L1. Yang di sini menutup butir yang disusun
    tanpa lisensi; yang di L1 menutup lisensi yang terisi tetapi tidak
    diizinkan.
    """
    with pytest.raises(ValidationError):
        _butir(lisensi="   ")


def test_satu_dokumen_sumber_saja() -> None:
    """PP-02. Butir bersumber ganda tidak dapat ditarik ketika salah satu
    sumbernya dicabut, sebab tidak ada jawaban tunggal atas apakah ia masih
    berdasar."""
    assert ButirPengetahuan.model_fields["id_dokumen_sumber"].annotation is str


def test_butir_beku() -> None:
    with pytest.raises(ValidationError):
        _butir().judul = "lain"  # type: ignore[misc]


def test_bidang_tambahan_ditolak() -> None:
    with pytest.raises(ValidationError):
        _butir(skor_relevansi=0.9)
