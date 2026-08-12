"""Uji penarikan butir tayang — B-3 fitur 010, R-10, FR-I06, D-06 Bagian 7.5.

Tiga pemicu, dan **dua di antaranya menarik sedangkan satu tidak**. Perbedaan
itu yang paling mudah hilang: sebuah penarikan yang menyapu ketiganya lulus
setiap uji yang hanya menanyakan "apakah butir ditarik", dan akibatnya feed
kehilangan isi setiap kali sebuah angka pada dokumen sumber diperbarui.

| Pemicu | Tindakan |
|---|---|
| Regulasi sumber dicabut **atau diubah** | Ditarik otomatis |
| Kekeliruan isi dilaporkan pengguna | Ditarik dalam 1 hari kerja |
| Data sumber diperbarui | **Ditandai perlu tinjauan, tetap tayang** |
"""

import re
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.ingest.kurasi.penarikan import (
    GalatPenarikan,
    Pemicu,
    TindakanPenarikan,
    tinjau,
)
from src.ingest.kurasi.putusan import (
    ButirTayang,
    JenisPutusan,
    PeranKurasi,
    Putusan,
)
from src.ingest.kurasi.tetapan import TENGGAT_PENARIKAN_HARI_KERJA
from src.kamus.segmen import StatusKeberlakuan
from src.nlp.anotasi.skema import KategoriMasalah

AKAR = Path(__file__).resolve().parents[3]


def _tayang(**ganti: object) -> ButirTayang:
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
    return ButirTayang(
        butir=ButirPengetahuan(**argumen),  # type: ignore[arg-type]
        putusan=Putusan(
            jenis=JenisPutusan.SETUJUI,
            id_butir=str(argumen["id_butir"]),
            peran_pemutus=PeranKurasi.KURATOR,
            waktu=datetime(2026, 8, 12, 3, 0, tzinfo=UTC),
        ),
    )


# ------------------------------------------------ R-10 · regulasi dicabut/diubah


@pytest.mark.parametrize(
    "status", [StatusKeberlakuan.DICABUT, StatusKeberlakuan.DIUBAH]
)
def test_butir_ditarik_saat_regulasi_dicabut_atau_diubah(
    status: StatusKeberlakuan,
) -> None:
    """**Uji terpenting berkas ini** — D-06 Bagian 7.5 menyebut **keduanya**.

    Menariknya hanya pada `dicabut` akan membiarkan butir yang bersandar pada
    pasal yang sudah berubah tetap tayang, dan itu tepat bentuk kekeliruan yang
    C-07 larang: sistem mengarahkan kepala sekolah dengan ketentuan yang tidak
    lagi berlaku sebagaimana tertulis.
    """
    hasil = tinjau(
        _tayang(), pemicu=Pemicu.REGULASI_SUMBER_BERUBAH, status_terkini=status
    )
    assert hasil.tindakan is TindakanPenarikan.DITARIK


def test_regulasi_yang_masih_berlaku_bukan_pemicu() -> None:
    """Pemicu yang menyala tanpa perubahan akan menarik butir yang sehat setiap
    kali seseorang menjalankan peninjauan bulanan D-06 Bagian 7.2."""
    with pytest.raises(GalatPenarikan):
        tinjau(
            _tayang(),
            pemicu=Pemicu.REGULASI_SUMBER_BERUBAH,
            status_terkini=StatusKeberlakuan.BERLAKU,
        )


def test_pemicu_regulasi_wajib_membawa_status_terkini() -> None:
    """Tanpa status terkini, "regulasi berubah" hanya dugaan — dan dugaan yang
    menarik butir mengosongkan feed tanpa dasar."""
    with pytest.raises(GalatPenarikan):
        tinjau(_tayang(), pemicu=Pemicu.REGULASI_SUMBER_BERUBAH)


def test_kurator_diberi_tahu_menyusun_pengganti() -> None:
    """D-06 Bagian 7.5: *"kurator diberi tahu untuk menyusun penggantinya"*.

    Penarikan tanpa penggantinya adalah pengurangan isi feed yang permanen, dan
    D-02 titik kritis T5 mengukur akibatnya.
    """
    hasil = tinjau(
        _tayang(),
        pemicu=Pemicu.REGULASI_SUMBER_BERUBAH,
        status_terkini=StatusKeberlakuan.DICABUT,
    )
    assert hasil.kurator_menyusun_pengganti


# --------------------------------------------- R-10 · kekeliruan isi dilaporkan


def test_kekeliruan_dilaporkan_menarik_dengan_tenggat_satu_hari_kerja() -> None:
    hasil = tinjau(_tayang(), pemicu=Pemicu.KEKELIRUAN_ISI_DILAPORKAN)
    assert hasil.tindakan is TindakanPenarikan.DITARIK
    assert hasil.tenggat_hari_kerja == TENGGAT_PENARIKAN_HARI_KERJA


def test_kekeliruan_dilaporkan_dapat_tayang_ulang_setelah_perbaikan() -> None:
    """D-06 Bagian 7.5 membedakannya dari penarikan regulasi: *"ditayangkan
    ulang setelah perbaikan atau ditolak permanen"*.

    Penarikan yang selalu permanen membuat setiap aduan pengguna menghapus satu
    butir, dan pengguna yang mengadu dua kali kehilangan lebih banyak daripada
    yang diam.
    """
    hasil = tinjau(_tayang(), pemicu=Pemicu.KEKELIRUAN_ISI_DILAPORKAN)
    assert hasil.dapat_tayang_ulang


def test_penarikan_regulasi_tidak_bertenggat_hari_kerja() -> None:
    """Otomatis, bukan dijadwalkan. Tenggat pada penarikan otomatis akan
    membaca seperti izin menunda sehari."""
    hasil = tinjau(
        _tayang(),
        pemicu=Pemicu.REGULASI_SUMBER_BERUBAH,
        status_terkini=StatusKeberlakuan.DICABUT,
    )
    assert hasil.tenggat_hari_kerja is None


# ----------------------------------------- R-10 · data sumber diperbarui menahan


def test_data_sumber_diperbarui_menandai_tetapi_tidak_menarik() -> None:
    """**Pemicu ketiga tidak menarik**, dan itu yang paling mudah hilang.

    Penarikan yang menyapu ketiga pemicu lulus setiap uji yang hanya
    menanyakan "apakah butir ditarik". Yang membedakannya hanya uji yang
    menuntut sebuah pemicu **tidak** menarik.
    """
    hasil = tinjau(_tayang(), pemicu=Pemicu.DATA_SUMBER_DIPERBARUI)
    assert hasil.tindakan is TindakanPenarikan.DITANDAI_PERLU_TINJAUAN
    assert hasil.tindakan is not TindakanPenarikan.DITARIK


def test_data_sumber_diperbarui_menarik_bila_angka_berubah_bermakna() -> None:
    """D-06 Bagian 7.5: *"tetap tayang sampai ditinjau, **kecuali angkanya
    berubah bermakna**"*.

    "Bermakna" adalah penilaian kurator, bukan perbandingan yang dapat dihitung
    modul ini — karena itu ia diserahkan pemanggil, sama seperti
    `id_dokumen_dikenal` pada `saring.py`.
    """
    hasil = tinjau(
        _tayang(),
        pemicu=Pemicu.DATA_SUMBER_DIPERBARUI,
        angka_berubah_bermakna=True,
    )
    assert hasil.tindakan is TindakanPenarikan.DITARIK


def test_angka_berubah_bermakna_tidak_berlaku_pada_pemicu_lain() -> None:
    """Bendera yang diterima setiap pemicu akan dipakai untuk melunakkan
    penarikan regulasi — dan itu C-07 yang dilewati lewat pintu samping."""
    with pytest.raises(GalatPenarikan):
        tinjau(
            _tayang(),
            pemicu=Pemicu.KEKELIRUAN_ISI_DILAPORKAN,
            angka_berubah_bermakna=True,
        )


# ------------------------------------- D-06 Bagian 7.5 · koleksi tidak dihapus


@pytest.mark.parametrize(
    ("pemicu", "tambahan"),
    [
        (
            Pemicu.REGULASI_SUMBER_BERUBAH,
            {"status_terkini": StatusKeberlakuan.DICABUT},
        ),
        (Pemicu.KEKELIRUAN_ISI_DILAPORKAN, {}),
        (Pemicu.DATA_SUMBER_DIPERBARUI, {}),
    ],
)
def test_butir_tetap_terlihat_pada_koleksi_pengguna(
    pemicu: Pemicu, tambahan: dict[str, object]
) -> None:
    """D-06 Bagian 7.5: *"Menghapus dari koleksi tanpa penjelasan akan merusak
    kepercayaan yang dibangun sepanjang J1 sampai J4."*

    Ditarik berarti berhenti tayang pada feed, **bukan** hilang dari koleksi
    orang yang sudah menyimpannya. Ketiga pemicu diuji, sebab yang menghapus
    diam-diam kelak adalah pemicu yang tidak seorang pun ingat menguji.
    """
    hasil = tinjau(_tayang(), pemicu=pemicu, **tambahan)  # type: ignore[arg-type]
    assert hasil.tetap_terlihat_pada_koleksi


def test_penarikan_membawa_penanda_bagi_koleksi() -> None:
    """*"disertai penanda bahwa dasar rujukannya telah berubah"* — tanpa
    penanda, butir yang tersimpan terbaca sebagai masih berlaku."""
    hasil = tinjau(
        _tayang(),
        pemicu=Pemicu.REGULASI_SUMBER_BERUBAH,
        status_terkini=StatusKeberlakuan.DICABUT,
    )
    assert hasil.penanda_koleksi
    assert len(hasil.penanda_koleksi.split()) <= 20


def test_butir_yang_hanya_ditandai_tidak_membawa_penanda_koleksi() -> None:
    """Penanda "dasar rujukannya telah berubah" pada butir yang **masih tayang**
    memberi tahu pembaca sesuatu yang belum tentu benar.

    Data sumber yang diperbarui belum tentu mengubah dasar rujukannya — itu
    justru yang hendak ditinjau kurator. Penanda yang dipasang lebih dulu
    mendahului tinjauan itu.
    """
    hasil = tinjau(_tayang(), pemicu=Pemicu.DATA_SUMBER_DIPERBARUI)
    assert hasil.penanda_koleksi is None
    assert hasil.tetap_terlihat_pada_koleksi


def test_modul_tidak_menyediakan_cara_menghapus() -> None:
    """Yang tidak disediakan tidak dapat dipanggil karena lupa. Bentuk yang sama
    dengan `src/logbook/penulis.py` dan `JejakKurasi`."""
    isi = (AKAR / "src" / "ingest" / "kurasi" / "penarikan.py").read_text(
        encoding="utf-8"
    )
    for terlarang in ("def hapus", "def buang", "def kosongkan"):
        assert terlarang not in isi


# ------------------------------------------------- ketiga pemicu dibaca dari D-06


def _pemicu_d06() -> int:
    teks = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")
    awal = teks.index("### 7.5 Penarikan Butir yang Sudah Tayang")
    akhir = teks.index("## 8. Kapasitas Antrean")
    baris = [
        g
        for g in teks[awal:akhir].splitlines()
        if g.startswith("|") and not set(g) <= set("|-: ")
    ]
    return len(baris) - 1  # kurangi baris kepala


def test_ketiga_pemicu_d06_terwakili() -> None:
    """Pemicu keempat yang ditambahkan D-06 kelak menyalakan uji ini, bukan
    lolos sebagai keadaan yang tidak ditangani siapa pun."""
    assert _pemicu_d06() == len(Pemicu) == 3


def test_setiap_pemicu_memiliki_tindakan() -> None:
    """Pemetaan berkunci, bukan cabang lain-lain — bentuk yang sama dengan
    `Akibat.bagi` pada `putusan.py`."""
    with pytest.raises(KeyError):
        tinjau(_tayang(), pemicu="regulasi_sumber_berubah")  # type: ignore[arg-type]


def test_tenggat_dibaca_dari_d06_bagian_7_5() -> None:
    """Angkanya milik dokumen, bukan modul — R-12."""
    teks = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")
    awal = teks.index("### 7.5 Penarikan Butir yang Sudah Tayang")
    baris = next(
        g for g in teks[awal:].splitlines() if "Kekeliruan isi dilaporkan" in g
    )
    cocok = re.search(r"(\d+) hari kerja", baris)
    assert cocok is not None
    assert int(cocok.group(1)) == TENGGAT_PENARIKAN_HARI_KERJA


def test_hasil_penarikan_beku() -> None:
    hasil = tinjau(_tayang(), pemicu=Pemicu.KEKELIRUAN_ISI_DILAPORKAN)
    with pytest.raises(Exception):
        hasil.tindakan = TindakanPenarikan.DITANDAI_PERLU_TINJAUAN  # type: ignore[misc]
