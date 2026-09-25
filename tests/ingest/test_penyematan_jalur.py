"""Jalur penyematan korpus di atas peladen — T-4 fitur 026.

R-01, R-03, R-04, R-05, R-06, R-07. Menuntut PostgreSQL; `make check` sudah
menuntutnya sejak 12 September 2026, sehingga tidak ada jalur dilewati.

**Urutan penjagaan yang diuji, bukan hanya hasilnya.** Penjagaan yang berjalan
sesudah baris dibaca menghasilkan keluaran yang sama persis dengan yang
berjalan sebelumnya — dan C-02 menolak yang kedua dengan kalimatnya sendiri:
*"Pemisahan pada tingkat indeks, bukan penyaringan saat kueri."*
"""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from src.ingest.penyematan import sematkan_indeks
from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import Penyemat, PenyematTiruan, VersiPenyemat
from src.penyimpanan.kredensial_baku import PENJAWABAN, PENYEMATAN
from src.penyimpanan.skema_indeks import (
    KOLOM_VEKTOR_SEMATAN,
    KOLOM_VERSI_SEMATAN,
    SKEMA_INDEKS,
    TABEL_SEGMEN,
    GalatDimensiVektor,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import DIMENSI_UJI, psql, siapkan
from tests.rag.pengambilan.test_kontrak_sumber import SambunganUji

siapkan()

SAAT = datetime(2026, 9, 23, 7, 30, 0, tzinfo=UTC)
LOGBOOK_UJI = Path(tempfile.mkdtemp(prefix="logbook-uji-"))
"""Akar logbook sementara. Uji **tidak pernah** menulis ke `logbook/`
repositori — berkas itu tambah-saja, dan baris uji di sana tidak dapat dihapus."""


def _kosongkan(tujuan: IndeksTujuan = IndeksTujuan.UTAMA) -> None:
    psql("smart_coaching", "-c", f"DELETE FROM {SKEMA_INDEKS[tujuan]}.{TABEL_SEGMEN}")


def _tanam(*segmen: tuple[str, str], tujuan: IndeksTujuan = IndeksTujuan.UTAMA) -> None:
    """Tanam segmen **tanpa vektor** — keadaan awal jalur penyematan."""
    skema = SKEMA_INDEKS[tujuan]
    for id_segmen, teks in segmen:
        psql(
            "smart_coaching",
            "-c",
            f"INSERT INTO {skema}.{TABEL_SEGMEN} "
            "(id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, "
            "penanda_bagian) VALUES "
            f"('{id_segmen}', 'DOK-1', '{teks}', 'terbuka', true, 'Pasal 1')",
        )


def _kolom(id_segmen: str, kolom: str, tujuan: IndeksTujuan = IndeksTujuan.UTAMA) -> str:
    hasil = psql(
        "smart_coaching",
        "-c",
        f"SELECT {kolom} FROM {SKEMA_INDEKS[tujuan]}.{TABEL_SEGMEN} "
        f"WHERE id_segmen = '{id_segmen}'",
    )
    return hasil.stdout.strip()


def _semat(**ganti: object):  # type: ignore[no-untyped-def]
    bidang: dict[str, object] = {
        "penyemat": PenyematTiruan(dimensi=DIMENSI_UJI),
        "indeks_tujuan": IndeksTujuan.UTAMA,
        "kredensial": PENYEMATAN,
        "sekarang": lambda: SAAT,
        "akar_logbook": LOGBOOK_UJI,
    }
    bidang.update(ganti)
    return jalankan(sematkan_indeks(SambunganUji(), **bidang))  # type: ignore[arg-type]


# ── penjagaan 1: kredensial, sebelum satu baris pun dibaca ──────────


class SambunganPencatat:
    """Mencatat apakah ia disentuh sama sekali."""

    def __init__(self) -> None:
        self.dipanggil = 0

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        self.dipanggil += 1
        raise AssertionError("peladen tidak boleh disentuh")

    async def fetch(self, kueri: str, *argumen: object) -> object:
        self.dipanggil += 1
        raise AssertionError("peladen tidak boleh disentuh")

    async def execute(self, kueri: str, *argumen: object) -> object:
        self.dipanggil += 1
        raise AssertionError("peladen tidak boleh disentuh")


def test_kredensial_tanpa_hak_tulis_ditolak_sebelum_peladen_disentuh() -> None:
    """**R-06, R-07, C-02, C-17.**

    `PENJAWABAN` menjangkau kedua indeks untuk **dibaca** — itu yang membuat
    uji ini berarti. Bila jalur ini memeriksa `boleh_baca_indeks`, ia lolos.
    """
    sambungan = SambunganPencatat()
    with pytest.raises(PermissionError):
        jalankan(
            sematkan_indeks(
                sambungan,  # type: ignore[arg-type]
                penyemat=PenyematTiruan(dimensi=DIMENSI_UJI),
                indeks_tujuan=IndeksTujuan.UTAMA,
                kredensial=PENJAWABAN,
                sekarang=lambda: SAAT,
                akar_logbook=LOGBOOK_UJI,
            )
        )
    assert sambungan.dipanggil == 0, "peladen disentuh sebelum kredensial diperiksa"


# ── penjagaan 2: dimensi, sebelum satu baris pun ditulis ────────────


def test_penyemat_berdimensi_lain_ditolak_tanpa_menulis() -> None:
    """**R-03.** Ditolak sebelum satu baris pun ditulis, bukan pada baris
    pertama yang gagal."""
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah menyusun rencana"))
    with pytest.raises(GalatDimensiVektor):
        _semat(penyemat=PenyematTiruan(dimensi=DIMENSI_UJI + 1))
    assert _kolom("SEG-A", KOLOM_VEKTOR_SEMATAN) == "", "vektor tertulis meski ditolak"


# ── jalur berjalan ──────────────────────────────────────────────────


def test_segmen_tersemat_beserta_versi_modelnya() -> None:
    """**R-01, R-02.** Vektor dan versi model tertulis bersama.

    Versi yang tertulis belakangan pada langkah terpisah dapat tertinggal bila
    penjalanan terputus di antaranya — dan baris yang bervektor tanpa versi
    tidak dapat dibedakan dari baris yang disemat model tak dikenal.
    """
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah menyusun rencana"), ("SEG-B", "supervisi akademik"))
    hasil = _semat()

    assert hasil.tersemat == 2
    assert hasil.tersisa_tanpa_vektor == 0
    assert hasil.versi_indeks == "utama-20260923T073000Z"
    assert hasil.versi_penyemat == PenyematTiruan(dimensi=DIMENSI_UJI).versi
    for id_segmen in ("SEG-A", "SEG-B"):
        assert _kolom(id_segmen, KOLOM_VEKTOR_SEMATAN) != ""
        assert _kolom(id_segmen, KOLOM_VERSI_SEMATAN) == "penyemat-tiruan/hash-sha256-1"


def test_segmen_bertext_kosong_dilewati_dan_dihitung() -> None:
    """**R-05.** Dilewati **dan dihitung**, bukan disemat menjadi vektor nol.

    Vektor nol tidak menghasilkan galat; ia menghasilkan tetangga terdekat
    yang salah, dan kesalahannya tidak pernah terlihat pada keluaran.
    """
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"), ("SEG-KOSONG", "   "))
    hasil = _semat()

    assert hasil.tersemat == 1
    assert hasil.dilewati_teks_kosong == 1
    assert hasil.tersisa_tanpa_vektor == 1, "segmen kosong wajib tetap terhitung"
    assert _kolom("SEG-KOSONG", KOLOM_VEKTOR_SEMATAN) == ""


def test_indeks_kosong_selesai_tanpa_galat() -> None:
    _kosongkan()
    hasil = _semat()
    assert (hasil.tersemat, hasil.dilewati_teks_kosong, hasil.tersisa_tanpa_vektor) == (0, 0, 0)


def test_indeks_metadata_disemat_terpisah() -> None:
    """**R-06.** Kedua indeks disemat terpisah — menyemat utama tidak
    menyentuh metadata."""
    _kosongkan(IndeksTujuan.UTAMA)
    _kosongkan(IndeksTujuan.METADATA)
    _tanam(("SEG-U", "segmen utama"), tujuan=IndeksTujuan.UTAMA)
    _tanam(("SEG-M", "segmen metadata"), tujuan=IndeksTujuan.METADATA)

    hasil = _semat(indeks_tujuan=IndeksTujuan.UTAMA)
    assert hasil.tersemat == 1
    assert hasil.versi_indeks.startswith("utama-")
    assert _kolom("SEG-M", KOLOM_VEKTOR_SEMATAN, IndeksTujuan.METADATA) == ""


# ── R-04: penyemat diserahkan pemanggil ─────────────────────────────


def test_jalur_memakai_penyemat_yang_diserahkan_pemanggil() -> None:
    """**R-04.** Bentuk uji yang sama dengan R-02 fitur 019 (KB-101): penyemat
    yang **tidak dapat ditiru bawaan**, sehingga jalur yang menyusun
    penyematnya sendiri menghasilkan keluaran yang berbeda."""

    class PenyematLain(Penyemat):
        @property
        def versi(self) -> VersiPenyemat:
            return VersiPenyemat(nama_model="penyemat-lain", versi_model="9.9")

        @property
        def dimensi(self) -> int:
            return DIMENSI_UJI

        async def sematkan(self, teks):  # type: ignore[no-untyped-def]
            return [[0.5] * DIMENSI_UJI for _ in teks]

    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"))
    hasil = _semat(penyemat=PenyematLain())

    assert hasil.versi_penyemat.nama_model == "penyemat-lain"
    assert _kolom("SEG-A", KOLOM_VERSI_SEMATAN) == "penyemat-lain/9.9"


# ── T-5: dua penjalanan — R-08, R-09 ────────────────────────────────


class PenyematBerversi(Penyemat):
    """Penyemat yang nama dan versinya ditentukan uji, dimensinya cocok."""

    def __init__(self, nama: str, versi: str) -> None:
        self._versi = VersiPenyemat(nama_model=nama, versi_model=versi)

    @property
    def versi(self) -> VersiPenyemat:
        return self._versi

    @property
    def dimensi(self) -> int:
        return DIMENSI_UJI

    async def sematkan(self, teks):  # type: ignore[no-untyped-def]
        return [[0.25] * DIMENSI_UJI for _ in teks]


def test_penjalanan_kedua_atas_indeks_penuh_tidak_menulis_apa_pun() -> None:
    """**R-08.** Aman dijalankan ulang, tanpa penanda apa pun selain `NULL`."""
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"), ("SEG-B", "supervisi"))
    _semat()
    sebelum = _kolom("SEG-A", KOLOM_VEKTOR_SEMATAN)

    kedua = _semat()
    assert kedua.tersemat == 0
    assert kedua.tersisa_tanpa_vektor == 0
    assert _kolom("SEG-A", KOLOM_VEKTOR_SEMATAN) == sebelum, "vektor lama tertimpa"


def test_indeks_separuh_dilanjutkan_tanpa_menulis_ulang_yang_sudah_ada() -> None:
    """**R-08.** Segmen yang bertambah sesudah penjalanan pertama disemat;
    yang sudah tersemat tidak disentuh."""
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"))
    _semat()
    lama = _kolom("SEG-A", KOLOM_VEKTOR_SEMATAN)

    _tanam(("SEG-B", "segmen yang datang belakangan"))
    kedua = _semat()
    assert kedua.tersemat == 1
    assert _kolom("SEG-A", KOLOM_VEKTOR_SEMATAN) == lama
    assert _kolom("SEG-B", KOLOM_VEKTOR_SEMATAN) != ""


def test_penyemat_berbeda_versi_ditolak_dan_pesannya_menyebut_keduanya() -> None:
    """**R-09.** Indeks bercampur dua model **tidak menghasilkan galat** — ia
    menghasilkan peringkat yang masuk akal dan salah, sebab jarak hanya
    bermakna di dalam satu ruang sematan. Karena itu penolakannya kebutuhan,
    bukan kehati-hatian."""
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"))
    _semat(penyemat=PenyematBerversi("model-a", "1.0"))

    _tanam(("SEG-B", "segmen baru"))
    with pytest.raises(ValueError) as galat:
        _semat(penyemat=PenyematBerversi("model-a", "2.0"))
    pesan = str(galat.value)
    assert "model-a/1.0" in pesan and "model-a/2.0" in pesan, pesan


def test_penolakan_percampuran_terjadi_sebelum_satu_baris_pun_ditulis() -> None:
    """Indeks tidak boleh tertinggal separuh bercampur. Penolakan yang
    terjadi sesudah sebagian ditulis meninggalkan persis keadaan yang R-09
    cegah."""
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"))
    _semat(penyemat=PenyematBerversi("model-a", "1.0"))
    _tanam(("SEG-B", "segmen baru"))

    with pytest.raises(ValueError):
        _semat(penyemat=PenyematBerversi("model-b", "1.0"))
    assert _kolom("SEG-B", KOLOM_VEKTOR_SEMATAN) == "", "segmen tertulis sebelum ditolak"


def test_dua_model_berbeda_dengan_untai_versi_sama_tetap_terbedakan() -> None:
    """**Ditemukan saat menulis T-5.** T-4 menyimpan `versi_model` saja pada
    `versi_model_sematan`, sehingga `model-a/1.0` dan `model-b/1.0` tercatat
    sama persis — dan R-09 tidak dapat membedakannya.

    Model yang berbeda dengan untai versi yang kebetulan sama bukan kasus
    buatan: "1.0" adalah versi pertama hampir setiap model."""
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"))
    _semat(penyemat=PenyematBerversi("model-a", "1.0"))
    assert _kolom("SEG-A", KOLOM_VERSI_SEMATAN) == "model-a/1.0"

    _tanam(("SEG-B", "segmen baru"))
    with pytest.raises(ValueError, match="model-b/1.0"):
        _semat(penyemat=PenyematBerversi("model-b", "1.0"))


# ── T-6: R-02 — setiap versi indeks yang diterbitkan tercatat pada L2 ─


def test_setiap_pembangunan_menulis_satu_baris_l2(tmp_path: Path) -> None:
    """**R-02, C-09.** Ditemukan pada T-6 karena mutasi M-8 **tidak dapat
    dipasang**: T-2 membangun penulisnya, T-4 membangun jalurnya, dan tidak
    satu tugas pun menyambungkan keduanya.

    Sifat yang dijaga: **setiap versi indeks yang diterbitkan memiliki baris
    L2.** Percobaan yang mengutip versi tanpa catatan adalah provenans yang
    putus, dan itu lebih buruk daripada catatan yang berulang.
    """
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"), ("SEG-B", "supervisi"))
    hasil = _semat(akar_logbook=tmp_path)

    baris = [
        json.loads(x)
        for x in (tmp_path / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(baris) == 1
    catatan = baris[0]
    assert catatan["artefak"] == "indeks"
    assert catatan["versi_indeks"] == hasil.versi_indeks
    assert catatan["jumlah_segmen"] == 2
    assert catatan["komposisi_sumber"] == [{"label": "terbuka", "jumlah": 2}]
    assert catatan["nama_model_sematan"] == "penyemat-tiruan"
    assert catatan["versi_model_sematan"] == "hash-sha256-1"


def test_tanggal_pembangunan_dan_versi_indeks_dari_satu_saat(tmp_path: Path) -> None:
    """Versi indeks dan tanggal pembangunan wajib dibaca dari **satu**
    pemanggilan jam. Dua pemanggilan dapat jatuh pada detik berbeda, dan
    catatan yang versinya berbunyi 07.30.00 sementara tanggalnya 07.30.01
    menyatakan dua saat bagi satu peristiwa."""
    detik = iter([datetime(2026, 9, 23, 7, 30, n, tzinfo=UTC) for n in range(10)])
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"))
    hasil = _semat(akar_logbook=tmp_path, sekarang=lambda: next(detik))

    catatan = json.loads((tmp_path / "L2-versi-artefak.jsonl").read_text(encoding="utf-8"))
    assert hasil.versi_indeks == "utama-20260923T073000Z"
    assert catatan["dibangun_pada"].startswith("2026-09-23T07:30:00"), catatan["dibangun_pada"]


def test_jumlah_segmen_l2_menghitung_indeks_bukan_penjalanan(tmp_path: Path) -> None:
    """D-10 Bagian 4 meminta **jumlah segmen indeks**. Penjalanan kedua yang
    menyemat satu segmen baru atas indeks berisi dua mencatat tiga — bukan
    satu, yang akan membuat indeks tampak menyusut."""
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"), ("SEG-B", "supervisi"))
    _semat(akar_logbook=tmp_path)
    _tanam(("SEG-C", "segmen baru"))
    _semat(akar_logbook=tmp_path)

    terakhir = json.loads(
        (tmp_path / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()[-1]
    )
    assert terakhir["jumlah_segmen"] == 3


# ── TK-63: jalur berjalan dengan peran hak minimumnya sendiri ───────


class SambunganPeranPenyematan(SambunganUji):
    """Menyambung sebagai `peran_penyematan`, bukan sebagai pengelola."""

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg
        from tests.peladen import HOST, PORT

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user="peran_penyematan", database="smart_coaching"
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()


def test_jalur_penuh_berjalan_dengan_peran_penyematan(tmp_path: Path) -> None:
    """**TK-63.** Uji hak per perintah membuktikan apa yang ditolak dan
    dibolehkan; uji ini membuktikan hak itu **cukup** bagi kode yang
    sesungguhnya — pembacaan katalog, penjagaan R-09, penulisan dua kolom,
    penghitungan komposisi.

    Peran yang lolos seluruh uji penolakan tetapi tidak cukup menjalankan
    jalurnya akan mendorong orang menjalankan penyematan dengan peran yang
    lebih luas — dan `peran_verifikasi` menjangkau karantina.
    """
    _kosongkan()
    _tanam(("SEG-A", "kepala sekolah"), ("SEG-B", "supervisi"))
    hasil = jalankan(
        sematkan_indeks(
            SambunganPeranPenyematan(),
            penyemat=PenyematTiruan(dimensi=DIMENSI_UJI),
            indeks_tujuan=IndeksTujuan.UTAMA,
            kredensial=PENYEMATAN,
            sekarang=lambda: SAAT,
            akar_logbook=tmp_path,
        )
    )
    assert hasil.tersemat == 2
    assert hasil.tersisa_tanpa_vektor == 0
