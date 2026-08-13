"""Jalur penjawaban — R-05 s.d. R-12; C-02, C-17, C-18, C-19, C-20.

Seluruh potongan jalur ini sudah berdiri sejak fitur 009: pengambilan hibrida
(007), penilai kecukupan (007), pembungkus model (001), validator sitasi (008),
dan penyusun tanggapan (009). **Tidak ada satu pun yang menyambungkannya.**

Selama tidak ada, urutan pemanggilan hanya hidup pada `docs/D07.md` sebagai
prosa — dan prosa tidak menolak pemanggil yang melewati satu tahap. Tiga pasal
berdiri persis pada urutan itu: C-19 menuntut validasi mendahului penyusunan,
C-18 menuntut segmen tidak menempati posisi instruksi pada permintaan yang
disusun sesudah pengambilan, C-02 menuntut segmen yang tidak boleh masuk
konteks tidak pernah sampai ke pembungkus. Modul ini adalah tempat yang membuat
melewatinya **tidak mungkin**, bukan sekadar salah.

## Praproses tidak dipanggil di sini, dan itu bukan kelalaian

R-05 menyebut praproses sebagai tahap pertama. Ia berjalan **di dalam** BM25
(`src/rag/pengambilan/bm25.py`), tempat FR-B03 menaruhnya — indeks dan kueri
wajib melewati jalur yang sama, dan memanggilnya sekali lagi di sini
menghasilkan kueri yang di-*stem* dua kali. Yang tampak sebagai tahap yang
hilang sesungguhnya tahap yang bertempat tinggal satu lapis lebih dalam.

## `HasilTanya` hanya dibentuk di sini

Pemeriksanya melarang pembentukannya di mana pun pada `src/` selain modul ini
— bentuk `KredensialPseudonim` (C-05), bukan bentuk `ButirTayang` (C-06) yang
membatasi *di mana boleh*. Alasannya sejajar dengan C-05: modul yang membentuk
hasilnya sendiri sudah punya jalur yang tinggal dipanggil, sehingga
membentuknya sendiri **selalu** berarti melewati sesuatu.

## Lima alasan berhenti, bukan tiga — dan yang kelima adalah temuan fitur ini

`plan.md` Bagian 4 menyebut tiga. Dua lagi muncul saat menyambungkan jalurnya,
dan keduanya baru terlihat karena tahapnya akhirnya bersebelahan.

**Keempat: keluaran tidak terbaca.** Model dapat mengembalikan sesuatu yang
bukan kontrak D-07 Bagian 5.1. Ia bukan bukti yang kurang dan bukan penahanan
validator — validator tidak pernah sempat berjalan.

**Kelima, dan ini yang penting: `MENUNGGU_PEMERIKSAAN_MODEL`.** VS-03, VS-05,
dan VS-07 berstatus `BELUM_DAPAT_DIPERIKSA` sampai fitur 020 ada, dan
`HasilValidasi.tervalidasi` menuntut kesembilan pemeriksaan **tidak
menghalangi** — status itu menghalangi, sama seperti gagal. Akibatnya tegas dan
sebaiknya dibaca dua kali:

> **Hari ini jalur ini tidak dapat menghasilkan satu jawaban pun.** Setiap
> pertanyaan yang buktinya cukup dan keluarannya sah tetap berhenti, sebab tiga
> pemeriksaan belum dapat dijalankan.

Itu perilaku yang **benar**, dan fitur 008 memilihnya dengan sadar: pemeriksaan
yang belum berjalan tidak boleh terbaca sebagai lulus. Yang keliru adalah
membiarkannya terhitung sebagai `DITAHAN_VALIDATOR`, sebab pemiliknya berbeda —
yang satu menuntut pengambilan diperbaiki, yang lain menuntut fitur 020
dibangun. Menyamakannya menghasilkan laporan yang berbunyi "validator menahan
seluruh jawaban", dan pembacanya akan melonggarkan validator. Itu persis yang
C-16 larang, dan ia akan terjadi karena angkanya benar.

Kelimanya menghasilkan `status_dasar` yang sama pada tanggapan; D-14 Bagian 4.1
tidak menyediakan nilai keempat dan AG-03 melarang menambahnya. Yang berbeda
adalah **apa yang harus diperbaiki**.

Pengguna tetap melihat satu pesan. Perbedaannya untuk yang memperbaiki sistem,
bukan untuk yang bertanya.

## Segmen `METADATA` tidak pernah menjadi `Data`

C-02 dijaga tingkat indeks oleh kredensial, dan penyaringan di sini adalah
**lapisan kedua** — sejalan dengan cara C-07 dijaga tiga lapis. D-07 Bagian 7
menetapkan sumber `indeks_metadata` "tidak dipakai menyusun jawaban"; ia hanya
muncul sebagai `bacaan_lanjutan`. Segmen yang lolos kredensial tetapi berasal
dari indeks metadata karena itu berhenti di sini, bukan di pembungkus.

## Yang tidak dimiliki jalur ini

Tanpa parameter alat, tanpa akses tulis, tanpa pengiriman keluar (C-17).
Diwujudkan sebagai **ketiadaan**, mengikuti `src/llm/adaptor/dasar.py`:
kemampuan yang tidak dapat dinyatakan tidak dapat dipakai.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.kamus.segmen import IndeksTujuan
from src.llm.instruksi import KunciInstruksi
from src.llm.instruksi import susun as susun_instruksi
from src.llm.pembungkus import Pembungkus
from src.llm.tipe import Data, Konfigurasi
from src.penyimpanan.kredensial import Kredensial
from src.rag.jawaban.domain import ranah_di_luar_domain
from src.rag.jawaban.susun import susun
from src.rag.jawaban.tanggapan import BacaanLanjutan, Sitasi, Tanggapan, Versi
from src.rag.pengambilan.gabung import HasilGabungan
from src.rag.pengambilan.hibrida import ambil_hibrida
from src.rag.pengambilan.kandidat import SumberKandidat
from src.rag.pengambilan.kecukupan import PenilaianKecukupan
from src.rag.pengambilan.kecukupan import StatusDasar as StatusKecukupan
from src.rag.validator.keluaran import KeluaranModel, SegmenRujukan
from src.rag.validator.pemeriksaan import KodePemeriksaan
from src.rag.validator.validator import (
    HasilValidasi,
    pemeriksaan_menunggu_model,
    validasi,
)


class AlasanBerhenti(Enum):
    """Mengapa jalur tidak menghasilkan jawaban — lihat uraian modul.

    Empat nilai karena ada empat pemilik perbaikan yang berbeda. Nilai kelima
    bernama "lainnya" sengaja tidak ada: yang tidak bernama tidak dapat
    dihitung, dan yang tidak dapat dihitung tidak pernah diperbaiki.
    """

    DI_LUAR_DOMAIN = "di_luar_domain"
    """Tidak ada yang perlu diperbaiki."""
    BUKTI_TIDAK_CUKUP = "bukti_tidak_cukup"
    """Korpus kurang — perbaikannya kurasi (fitur 010)."""
    KELUARAN_TIDAK_TERBACA = "keluaran_tidak_terbaca"
    """Model tidak menuruti kontrak D-07 Bagian 5.1 — perbaikannya instruksi
    atau model, bukan korpus."""
    DITAHAN_VALIDATOR = "ditahan_validator"
    """Jawaban tidak tersitasi — perbaikannya **pengambilan**, bukan validator
    (C-16)."""
    MENUNGGU_PEMERIKSAAN_MODEL = "menunggu_pemeriksaan_model"
    """Tidak ada yang salah pada jawabannya; VS-03, VS-05, dan VS-07 belum
    dapat dijalankan — perbaikannya **fitur 020**.

    Terpisah dari `DITAHAN_VALIDATOR` justru agar laporan tidak berbunyi
    "validator menahan seluruh jawaban" pada keadaan yang sebenarnya adalah
    fitur yang belum dibangun. Lihat uraian modul.
    """


class BahanSegmen(BaseModel):
    """Segmen sebagaimana jalur ini memerlukannya.

    Dua hal yang tidak dibawa bersamaan oleh tipe mana pun yang sudah ada:
    `SegmenRujukan` (008) membawa sifat yang validator perlukan tetapi tidak
    membawa teksnya, sedangkan `Kandidat` (007) membawa skor tetapi tidak
    membawa keduanya. Menyatukannya di sini alih-alih memperluas salah satunya
    mengikuti alasan `SegmenRujukan` sendiri: tipe penyimpanan tidak dibuat
    memikul keperluan penyajian.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    rujukan: SegmenRujukan
    teks: str = Field(min_length=1)


class HasilTanya(BaseModel):
    """Keluaran jalur penjawaban — **hanya dibentuk `Jalur.jawab()`**.

    Ketiga isinya tidak boleh larut satu sama lain. `tanggapan` adalah yang
    dilihat pengguna; `alasan_berhenti` adalah yang dibaca orang yang
    memperbaiki sistem; `menunggu_model` adalah **utang yang dapat ditagih**,
    dan utang yang tidak muncul pada keluaran akan berhenti ditagih.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tanggapan: Tanggapan
    alasan_berhenti: AlasanBerhenti | None = None
    """`None` berarti jalur menghasilkan jawaban."""
    menunggu_model: tuple[KodePemeriksaan, ...] = ()
    """Pemeriksaan VS yang belum dapat dijalankan (FR-F16, fitur 020).

    Diteruskan apa adanya, tidak disembunyikan — pemeriksaan yang menunggu
    model adalah yang paling mudah dilupakan justru karena ia tidak pernah
    menggagalkan apa pun.
    """


class Jalur:
    """Urutan tahap D-07 Bagian 4 s.d. 6, sebagai satu tempat.

    Kolaboratornya pada `__init__` dan bahannya pada `jawab()`, mengikuti
    `PenilaianKecukupan` fitur 007. Kolaborator yang berpindah tiap panggilan
    adalah kolaborator yang dapat berbeda antar panggilan tanpa seorang pun
    memutuskannya.
    """

    def __init__(
        self,
        *,
        sumber: Sequence[SumberKandidat],
        penilai: PenilaianKecukupan,
        pembungkus: Pembungkus,
        konfigurasi: Konfigurasi,
    ) -> None:
        self._sumber = tuple(sumber)
        self._penilai = penilai
        self._pembungkus = pembungkus
        self._konfigurasi = konfigurasi

    def jawab(
        self,
        pertanyaan: str,
        *,
        kredensial: Kredensial,
        bahan: Mapping[str, BahanSegmen],
        segmen_resmi: frozenset[str],
        id_pesan: str,
        versi: Versi,
        sitasi: Sequence[Sitasi] = (),
        bacaan_lanjutan: Sequence[BacaanLanjutan] = (),
    ) -> HasilTanya:
        """Jalankan urutan tetap — R-05.

        `sitasi` dan `bacaan_lanjutan` diserahkan pemanggil, mengikuti `susun()`
        fitur 009: keduanya menuntut metadata dokumen yang tinggal di
        `src/ingest/`, dan `AGENTS.md` tidak memberi jalur ini tepi ke sana.
        """
        if not pertanyaan.strip():
            raise ValueError("pertanyaan kosong tidak dapat dijawab")

        # Tahap 1 — sebelum pengambilan. Pertanyaan di luar domain yang tetap
        # diambilkan membakar pencarian dan, lebih buruk, dapat menemukan
        # segmen yang membuatnya terlihat dapat dijawab.
        if ranah_di_luar_domain(pertanyaan) is not None:
            return HasilTanya(
                tanggapan=Tanggapan.tolak_domain(id_pesan=id_pesan, versi=versi),
                alasan_berhenti=AlasanBerhenti.DI_LUAR_DOMAIN,
            )

        hasil = ambil_hibrida(pertanyaan, kredensial=kredensial, sumber=self._sumber)
        kecukupan = self._penilai.nilai(hasil, segmen_resmi=segmen_resmi)

        # Tahap 7 — dan berhenti di sini berarti **tanpa memanggil model**.
        # Bukti yang tidak cukup lalu tetap dikirim menghasilkan jawaban yang
        # lancar dan tidak tersitasi, persis kegagalan yang C-01 larang.
        if kecukupan is StatusKecukupan.TIDAK_DITEMUKAN:
            return HasilTanya(
                tanggapan=Tanggapan.tidak_ditemukan(
                    id_pesan=id_pesan, versi=versi, bacaan_lanjutan=tuple(bacaan_lanjutan)
                ),
                alasan_berhenti=AlasanBerhenti.BUKTI_TIDAK_CUKUP,
            )

        terpakai = self._segmen_terpakai(hasil.segmen, bahan)
        keluaran = self._panggil_model(terpakai)
        if keluaran is None:
            return HasilTanya(
                tanggapan=Tanggapan.tidak_ditemukan(
                    id_pesan=id_pesan, versi=versi, bacaan_lanjutan=tuple(bacaan_lanjutan)
                ),
                alasan_berhenti=AlasanBerhenti.KELUARAN_TIDAK_TERBACA,
            )

        rujukan = tuple(b.rujukan for b in terpakai)
        hasil_validasi, tervalidasi = validasi(keluaran, segmen=rujukan)
        # Daftarnya **dibaca dari pemiliknya**, bukan ditulis ulang di sini.
        # Daftar kedua akan benar hari ini lalu tertinggal pada hari fitur 020
        # memindahkan satu kode keluar darinya — dan yang tertinggal adalah
        # yang menyatakan utang sudah lunas.
        menunggu = tuple(pemeriksaan_menunggu_model(keluaran, segmen=rujukan))

        # C-19. `susun()` tidak menerima apa pun selain `JawabanTervalidasi`,
        # sehingga cabang ini tidak punya jalan menayangkan yang ditahan
        # betapa pun ia ditulis.
        if tervalidasi is None:
            return HasilTanya(
                tanggapan=Tanggapan.tidak_ditemukan(
                    id_pesan=id_pesan, versi=versi, bacaan_lanjutan=tuple(bacaan_lanjutan)
                ),
                alasan_berhenti=_alasan_penahanan(hasil_validasi, menunggu),
                menunggu_model=menunggu,
            )

        return HasilTanya(
            tanggapan=susun(
                tervalidasi,
                id_pesan=id_pesan,
                versi=versi,
                status=kecukupan,
                sitasi=sitasi,
                bacaan_lanjutan=bacaan_lanjutan,
                catatan_keberlakuan=keluaran.catatan_keberlakuan,
            ),
            menunggu_model=menunggu,
        )

    @staticmethod
    def _segmen_terpakai(
        segmen: Sequence[HasilGabungan], bahan: Mapping[str, BahanSegmen]
    ) -> tuple[BahanSegmen, ...]:
        """Segmen yang boleh masuk konteks — lapisan kedua C-02.

        Segmen tanpa bahan dilewati, bukan diganti bahan kosong: bahan kosong
        menghasilkan `Data` bertekst kosong yang tetap dihitung model sebagai
        segmen pendukung, dan klaim yang bersandar padanya lolos VS-01.
        """
        terpakai: list[BahanSegmen] = []
        for satu in segmen:
            satu_bahan = bahan.get(satu.id_segmen)
            if satu_bahan is None:
                continue
            if satu_bahan.rujukan.indeks_asal is IndeksTujuan.METADATA:
                continue
            terpakai.append(satu_bahan)
        return tuple(terpakai)

    def _panggil_model(self, terpakai: Sequence[BahanSegmen]) -> KeluaranModel | None:
        """Tahap 8 — `None` bila keluarannya tidak terbaca sebagai kontrak.

        `instruksi` dan `data` adalah dua parameter bertipe berbeda (C-18).
        Tidak ada tempat pada pemanggilan ini yang dapat menampung keduanya.
        """
        tanggapan = self._pembungkus.panggil(
            instruksi=susun_instruksi(KunciInstruksi.PENJAWABAN),
            data=[
                Data(
                    id_segmen=b.rujukan.id_segmen,
                    teks=b.teks,
                    peringkat_kepercayaan=b.rujukan.peringkat_kepercayaan,
                    indeks_asal=b.rujukan.indeks_asal,
                )
                for b in terpakai
            ],
            konfigurasi=self._konfigurasi,
        )
        return baca_keluaran(tanggapan.teks)


def baca_keluaran(teks: str) -> KeluaranModel | None:
    """Terjemahkan keluaran model menjadi kontrak D-07 Bagian 5.1.

    **`None`, bukan galat.** Model yang tidak menuruti kontrak adalah keadaan
    yang diperkirakan D-07 Bagian 5.2 sendiri — *"IN-01 sampai IN-03 akan
    dilanggar model sesekali; itulah sebabnya validator ada."* Melempar galat
    mengundang pemanggil membungkusnya dengan `try`, dan pada akhirnya seseorang
    menuliskan `except: pass` di sekeliling seluruh jalur penjawaban.

    Bentuk yang sama dengan `HasilPerekaman` (012) dan `terapkan()` (010):
    kegagalan yang diperkirakan berbentuk nilai, bukan pengecualian.
    """
    try:
        mentah = json.loads(teks)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(mentah, dict):
        return None
    try:
        return KeluaranModel.model_validate(mentah)
    except ValidationError:
        return None


def _alasan_penahanan(hasil: HasilValidasi, menunggu: Sequence[KodePemeriksaan]) -> AlasanBerhenti:
    """Bedakan jawaban yang ditahan dari fitur yang belum dibangun.

    Yang menghalangi **hanya** pemeriksaan yang menunggu model berarti tidak
    ada yang salah pada jawabannya — yang kurang fitur 020. Bila ada satu saja
    yang lain, jawabannya sungguh ditahan dan perbaikannya pengambilan.

    Diperiksa sebagai **himpunan bagian**, bukan kesamaan: satu pemeriksaan
    menunggu model yang kelak dapat dijalankan sementara dua lainnya belum
    tetap menghasilkan penahanan yang bukan salah jawabannya.
    """
    menghalangi = {h.kode for h in hasil.pemeriksaan if h.menghalangi}
    if menghalangi and menghalangi <= set(menunggu):
        return AlasanBerhenti.MENUNGGU_PEMERIKSAAN_MODEL
    return AlasanBerhenti.DITAHAN_VALIDATOR
