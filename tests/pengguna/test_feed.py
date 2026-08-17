"""Uji feed penemuan — B-1 dan B-2 fitur 011, R-01 s.d. R-08, R-18.

## Yang diuji bukan bahwa feed dapat menayangkan

Yang diuji: feed **tidak menayangkan** butir di luar prioritas, **tidak
melampaui** pagu harian, **tidak menuliskan** angkanya sendiri, dan **tidak
menawarkan** teks penuh butir berlisensi tertutup.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.ingest.kurasi.putusan import ButirTayang, JenisPutusan, PeranKurasi, Putusan
from src.ingest.kurasi.tetapan import PAGU_TAYANG_PER_PENGGUNA
from src.nlp.anotasi.skema import KategoriMasalah
from src.pengguna.feed import (
    LISENSI_TERBUKA,
    GalatFeed,
    butir_bertenggat_dekat,
    susun_feed,
    tandai_belum_relevan,
)
from src.pengguna.prioritas import PrioritasManajerial

AKAR = Path(__file__).resolve().parents[2]
SAAT = datetime(2026, 8, 16, 3, 0, tzinfo=UTC)

PRIORITAS = PrioritasManajerial(
    id_pengguna="PGN-1",
    kategori=(KategoriMasalah.K1, KategoriMasalah.K2, KategoriMasalah.K3),
)


def _butir(
    nomor: int,
    kategori: KategoriMasalah = KategoriMasalah.K1,
    lisensi: str = "CC-BY",
    tenggat: date | None = None,
) -> ButirPengetahuan:
    return ButirPengetahuan(
        id_butir=f"BTR-{nomor}",
        jenis_sumber=JenisSumberButir.RISET,
        judul=f"Butir {nomor}",
        alasan_relevansi="Relevan bagi pengelolaan supervisi di sekolah Anda.",
        inti_temuan="Supervisi terjadwal menaikkan mutu pembelajaran.",
        implikasi_tindakan=("Susun jadwal supervisi bulanan.",),
        perkiraan_waktu_baca=5,
        kategori=kategori,
        id_dokumen_sumber=f"DOK-{nomor}",
        lisensi=lisensi,
        tanggal_akses=date(2026, 8, 1),
        tenggat_terkait=tenggat,
    )


def _tayang(butir: ButirPengetahuan) -> ButirTayang:
    return ButirTayang(
        butir=butir,
        putusan=Putusan(
            jenis=JenisPutusan.SETUJUI,
            id_butir=butir.id_butir,
            peran_pemutus=PeranKurasi.KURATOR,
            waktu=SAAT,
        ),
    )


# ------------------------------------------------- R-01 · penyaringan prioritas


def test_butir_di_luar_prioritas_tidak_tayang() -> None:
    """**Uji terpenting berkas ini.**

    FR-G01 menyaring terhadap prioritas yang pengguna pilih sendiri. Butir di
    luar prioritas yang tetap tayang membuat pilihan itu tidak berakibat apa
    pun — dan feed berubah menjadi daftar terbaru.
    """
    tersedia = (_tayang(_butir(1, KategoriMasalah.K7)),)
    assert susun_feed(prioritas=PRIORITAS, tersedia=tersedia) == ()


def test_butir_dalam_prioritas_tayang() -> None:
    hasil = susun_feed(prioritas=PRIORITAS, tersedia=(_tayang(_butir(1, KategoriMasalah.K2)),))
    assert [f.butir.id_butir for f in hasil] == ["BTR-1"]


def test_urutan_mengikuti_urutan_prioritas_pengguna() -> None:
    """Posisi kategori pada `PrioritasManajerial` adalah urutan yang pengguna
    pilih sendiri (FR-A03). Feed yang mengabaikannya membuat pilihan itu tidak
    berakibat apa pun."""
    tersedia = (
        _tayang(_butir(3, KategoriMasalah.K3)),
        _tayang(_butir(1, KategoriMasalah.K1)),
        _tayang(_butir(2, KategoriMasalah.K2)),
    )
    hasil = susun_feed(prioritas=PRIORITAS, tersedia=tersedia)
    assert [f.butir.kategori for f in hasil] == [
        KategoriMasalah.K1,
        KategoriMasalah.K2,
        KategoriMasalah.K3,
    ]


def test_pengguna_tanpa_prioritas_melihat_feed_kosong_bukan_acak() -> None:
    """Bukan feed acak. Ketiadaan prioritas berarti *onboarding* belum selesai,
    dan butir acak menyembunyikan itu dari penggunanya maupun dari yang
    memeriksa."""
    assert susun_feed(prioritas=None, tersedia=(_tayang(_butir(1)),)) == ()


# ------------------------------------------------- R-05, R-06 · pagu tayang


def test_pagu_harian_tidak_dilampaui() -> None:
    tersedia = tuple(_tayang(_butir(n)) for n in range(1, 8))
    assert len(susun_feed(prioritas=PRIORITAS, tersedia=tersedia)) == PAGU_TAYANG_PER_PENGGUNA


def test_pagu_memperhitungkan_yang_sudah_tayang_hari_ini() -> None:
    tersedia = tuple(_tayang(_butir(n)) for n in range(1, 8))
    hasil = susun_feed(prioritas=PRIORITAS, tersedia=tersedia, sudah_tayang_hari_ini=2)
    assert len(hasil) == PAGU_TAYANG_PER_PENGGUNA - 2


def test_pagu_habis_menghasilkan_feed_kosong() -> None:
    tersedia = tuple(_tayang(_butir(n)) for n in range(1, 8))
    assert (
        susun_feed(
            prioritas=PRIORITAS,
            tersedia=tersedia,
            sudah_tayang_hari_ini=PAGU_TAYANG_PER_PENGGUNA,
        )
        == ()
    )


def test_pagu_dibaca_dari_tetapan_fitur_010_bukan_ditulis_ulang() -> None:
    """**Angka kedua akan benar hari ini lalu berselisih pada hari salah
    satunya disetel — dan yang disetel bukan yang diperiksa.**

    `PAGU_TAYANG_PER_PENGGUNA` terdaftar pada pemeriksa C-16 sejak fitur 010.
    """
    naskah = (AKAR / "src" / "pengguna" / "feed.py").read_text(encoding="utf-8")
    assert "from src.ingest.kurasi.tetapan import PAGU_TAYANG_PER_PENGGUNA" in naskah
    assert "PAGU_TAYANG_PER_PENGGUNA = " not in naskah


def test_jumlah_tayang_negatif_ditolak() -> None:
    with pytest.raises(GalatFeed):
        susun_feed(prioritas=PRIORITAS, tersedia=(), sudah_tayang_hari_ini=-1)


# ------------------------------------------------------ R-08 · FR-G08, C-02


def test_butir_berlisensi_tertutup_tidak_boleh_teks_penuh() -> None:
    """Lapis kedua FR-G08. Layar tidak boleh menawarkan unduhan, dan kesimpulan
    yang diambil layar akan diambil berbeda oleh layar berikutnya."""
    hasil = susun_feed(
        prioritas=PRIORITAS, tersedia=(_tayang(_butir(1, lisensi="Berlisensi tertutup")),)
    )
    assert hasil[0].boleh_teks_penuh is False


def test_butir_berlisensi_terbuka_boleh_teks_penuh() -> None:
    hasil = susun_feed(prioritas=PRIORITAS, tersedia=(_tayang(_butir(1, lisensi="CC-BY")),))
    assert hasil[0].boleh_teks_penuh is True


def test_lisensi_ditulis_sebagai_daftar_yang_diizinkan() -> None:
    """Daftar larangan meloloskan lisensi yang belum dikenalnya, dan lisensi
    yang belum dikenal justru yang paling mungkin menutup."""
    assert "CC-BY" in LISENSI_TERBUKA
    hasil = susun_feed(
        prioritas=PRIORITAS, tersedia=(_tayang(_butir(1, lisensi="Lisensi Baru 2027")),)
    )
    assert hasil[0].boleh_teks_penuh is False


def test_butir_feed_tidak_memiliki_bidang_teks_penuh() -> None:
    """`ButirPengetahuan` tidak memiliki bidang teks penuh sama sekali sejak
    fitur 010 — bentuk yang menutupnya, bukan pemeriksaan."""
    from src.pengguna.feed import ButirFeed

    assert set(ButirFeed.model_fields) == {"butir", "boleh_teks_penuh"}
    assert "teks_penuh" not in ButirPengetahuan.model_fields


# --------------------------------------------------------- R-07 · umpan balik


def test_umpan_balik_tanpa_alasan_ditolak() -> None:
    """Umpan balik tanpa alasan tidak dapat dipakai memperbaiki penyaringan,
    dan yang tidak dapat dipakai memperbaiki apa pun sebaiknya tidak diminta."""
    with pytest.raises(GalatFeed):
        tandai_belum_relevan(id_pengguna="PGN-1", id_butir="BTR-1", alasan="   ")


def test_umpan_balik_tercatat() -> None:
    hasil = tandai_belum_relevan(
        id_pengguna="PGN-1", id_butir="BTR-1", alasan="Akreditasi baru selesai bulan lalu."
    )
    assert hasil.id_butir == "BTR-1"


def test_umpan_balik_tanpa_id_pengguna_ditolak_dengan_pesan_umum() -> None:
    """Cabang penolakan yang **bukan** KM-03 — `id_pengguna` kosong tidak
    membawa muatan yang perlu disebutkan jenisnya, dan pesannya karena itu
    generik alih-alih menyebut jenis pengenal."""
    with pytest.raises(GalatFeed) as galat:
        tandai_belum_relevan(id_pengguna="", id_butir="BTR-1", alasan="alasan yang jelas")
    assert "belum lengkap" in str(galat.value)


def test_umpan_balik_bermuatan_data_pribadi_ditolak() -> None:
    with pytest.raises(GalatFeed) as galat:
        tandai_belum_relevan(
            id_pengguna="PGN-1", id_butir="BTR-1", alasan="Hubungi 081234567890 dahulu."
        )
    assert "081234567890" not in str(galat.value)


def test_umpan_balik_tidak_mengubah_penyaringan_otomatis() -> None:
    """**C-14.** Penyaringan yang menyesuaikan diri terhadap perilaku adalah
    personalisasi berbasis riwayat, yang D-01 Bagian 4.2 tempatkan di luar
    siklus 2026. `susun_feed` tidak menerima umpan balik sama sekali."""
    import inspect

    parameter = set(inspect.signature(susun_feed).parameters)
    assert parameter == {"prioritas", "tersedia", "sudah_tayang_hari_ini"}
    assert "umpan_balik" not in parameter
    assert "riwayat" not in parameter


# ------------------------------------------------- FR-G09 · setengah, dan disebut


def test_tenggat_dekat_hanya_dari_butir_yang_membawanya_sendiri() -> None:
    """Bagian yang menuntut kalender manajerial D-02 Bagian 5 belum dapat
    dibangun — kalendernya belum berbentuk yang terbaca mesin. Dinyatakan
    setengah dan disebut setengahnya, alih-alih dilewatkan utuh."""
    hasil = susun_feed(
        prioritas=PRIORITAS,
        tersedia=(
            _tayang(_butir(1, tenggat=date(2026, 8, 20))),
            _tayang(_butir(2, KategoriMasalah.K2)),
        ),
    )
    dekat = butir_bertenggat_dekat(hasil, sampai=date(2026, 8, 31))
    assert [f.butir.id_butir for f in dekat] == ["BTR-1"]


def test_tanpa_tenggat_tidak_ikut() -> None:
    hasil = susun_feed(prioritas=PRIORITAS, tersedia=(_tayang(_butir(1)),))
    assert butir_bertenggat_dekat(hasil, sampai=date(2026, 12, 31)) == ()


# ----------------------------------------------------------- R-18 · C-15


def test_feed_tanpa_bentuk_gamifikasi() -> None:
    """C-15 diuji sebagai ketiadaan pada modul feed juga — bukan hanya jurnal.
    Feed berurut dengan pagu harian adalah tempat runtun harian terasa wajar."""
    naskah = (AKAR / "src" / "pengguna" / "feed.py").read_text(encoding="utf-8")
    for terlarang in ("poin", "lencana", "peringkat", "runtun", "papan skor", "teman"):
        assert terlarang not in naskah.lower(), terlarang


def test_tidak_ada_tabel_gamifikasi_pada_seluruh_src() -> None:
    """**Sapuan lintas modul.** C-15 melarang membuat tabelnya "kosong pun
    tidak", dan larangan yang hanya diperiksa pada satu modul adalah larangan
    yang dipatuhi di satu modul."""
    terlarang = ("class Poin", "class Lencana", "class PapanPeringkat", "class Pertemanan")
    for berkas in (AKAR / "src").rglob("*.py"):
        isi = berkas.read_text(encoding="utf-8")
        for nama in terlarang:
            assert nama not in isi, f"{nama} pada {berkas}"
