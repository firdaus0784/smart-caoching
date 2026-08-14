"""Bentuk tanggapan — R-01, R-04 s.d. R-09, R-11; C-20, `docs/D14.md` Bagian 4.1.

D-14 menyebut rute yang membawanya *"kontrak terpenting dalam sistem; ia
menjadi tempat seluruh kendali D-07 dan D-13 bertemu"*, dan menyatakan alasan
C-20 dalam satu kalimat: **"bentuk itu adalah tempat C-02, C-07, dan C-19
diwujudkan."**

Bidang tambahan yang tampak tidak berbahaya — `skor_keyakinan`,
`waktu_proses` — memindahkan penilaian dari sistem ke klien, dan klien tidak
terikat konstitusi. Karena itu `extra="forbid"`, dan karena itu pemeriksa C-20
membandingkan daftar bidangnya dengan blok JSON D-14 sungguhan.

## Penolakan berbentuk jawaban, bukan galat

D-14: keadaan `tidak_ditemukan` dan `di_luar_domain` memakai bentuk yang
**sama** dengan ringkasan dan klaim kosong — *"bentuk yang seragam inilah yang
membuat layar D-05 dapat menampilkannya sebagai jawaban sah, bukan pesan
galat."*

`tolak_domain()` dan `tidak_ditemukan()` karena itu menghasilkan `Tanggapan`
yang sah. D-02 titik kritis T3: sistem yang mengaku tidak tahu justru
memperkuat kepercayaan.

## `Sitasi` dan `BacaanLanjutan` bertipe berbeda, dan itu C-02

D-14 Bagian 6 menetapkan `bacaan_lanjutan` sebagai **tempat satu-satunya** bagi
sumber `indeks_metadata`, dan D-07 Bagian 7 menyatakan isinya "tidak dipakai
menyusun jawaban".

`BacaanLanjutan` karena itu sengaja **tidak memiliki** bidang yang dimiliki
`Sitasi` — tidak ada `bagian`, tidak ada `status_keberlakuan`. Ia bukan sitasi
yang lebih lemah melainkan hal lain. Tanpa pembedaan tipe, memindahkan sumber
berlisensi tertutup ke `sitasi` adalah satu baris yang tidak menggagalkan apa
pun sampai audit lisensi.

## `dicabut` menolak pembentukan; `diubah` menuntut catatan

D-07 Bagian 4.5 memisahkan keduanya tegas. `dicabut` ditolak di sini sebagai
**lapisan kedua** — VS-06 sudah menolaknya pada validator, dan yang lolos lewat
jalur lain tetap tidak dapat tayang. Alasannya D-07 sendiri: menjawab
berdasarkan aturan yang sudah dicabut adalah bentuk kekeliruan yang paling
merugikan, *karena jawabannya terdengar berdasar*.

`catatan_keberlakuan` wajib terisi bila ada sitasi `diubah`, **dan wajib kosong
bila tidak ada**. Yang kedua bukan kerapian: catatan yang terisi tanpa sebab
akan diabaikan pembacanya, dan yang diabaikan tidak menjaga apa pun ketika ia
sungguh perlu.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.kamus.segmen import StatusKeberlakuan
from src.rag.jawaban.domain import PESAN_DI_LUAR_DOMAIN

JUMLAH_BUTIR_RINGKASAN_MAKSIMUM = 3
"""D-07 Bagian 5.1 dan FR-F05: ringkasan tindakan maksimal 3 butir."""

JUMLAH_KATA_MAKSIMUM = 20
"""NFR-19 dan C-13: kalimat ≤ 20 kata. Batasnya "≤", bukan "<"."""

PENAFIAN_BAKU = (
    "Keputusan akhir berada pada kepala sekolah. "
    "Selalu rujuk regulasi yang berlaku sebelum memutuskan."
)
"""FR-F10. Dua kalimat, masing-masing ≤ 20 kata."""


class StatusDasar(Enum):
    """Kekuatan dasar rujukan — `docs/D14.md` Bagian 4.1.

    Keempat nilai persis seperti D-14 menamainya. Ia **bukan** salinan enum
    `src/rag/pengambilan/kecukupan.py`: yang di sana hasil tahap 7, yang di sini
    bidang tanggapan. Keduanya bernilai sama dan pemetaan di antaranya satu
    tempat — `susun.py`.
    """

    KUAT = "kuat"
    TERBATAS = "terbatas"
    TIDAK_DITEMUKAN = "tidak_ditemukan"
    DI_LUAR_DOMAIN = "di_luar_domain"


_TANPA_ISI: frozenset[StatusDasar] = frozenset(
    {StatusDasar.TIDAK_DITEMUKAN, StatusDasar.DI_LUAR_DOMAIN}
)
"""Keadaan yang menuntut ringkasan dan klaim kosong — D-14 Bagian 4.1."""


class Versi(BaseModel):
    """Versi model, indeks, dan kode — KT-06, wajib pada setiap tanggapan.

    Tanggapan tanpa versi adalah tanggapan yang tidak dapat ditelusuri ketika
    seseorang melaporkan arahan yang keliru — dan ET-11 menetapkan prosedur
    pemulihannya menuntut penelusuran siapa saja yang menerima jawaban serupa.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str = Field(min_length=1)
    indeks: str = Field(min_length=1)
    kode: str = Field(min_length=1)


class KlaimTampil(BaseModel):
    """Satu klaim beserta segmen pendukungnya, sebagaimana tampil.

    `peringkat_kepercayaan` **tidak ada di sini**. D-14 Bagian 4.1 menyatakan
    artinya pada klaim campuran adalah keputusan **BT-64**, bukan keputusan
    pelaksana, dan ketiga pilihan yang mungkin mengubah apa yang dilihat kepala
    sekolah pada klaim yang sama. Ia ditambahkan ketika BT-64 diputuskan.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    teks: str = Field(min_length=1)
    id_segmen: tuple[str, ...] = Field(min_length=1)


class Sitasi(BaseModel):
    """Satu sumber yang menjadi dasar jawaban — D-07 Bagian 7, FR-F03."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_dokumen: str = Field(min_length=1)
    judul: str = Field(min_length=1)
    penerbit: str = Field(min_length=1)
    tahun: int = Field(gt=0)
    bagian: str = Field(min_length=1)
    """Pasal, ayat, butir, atau subjudul — FR-F11, titik kritis T2 pada D-02."""
    status_keberlakuan: StatusKeberlakuan
    rujukan_pengganti: str | None = None
    tautan: str | None = None

    @model_validator(mode="after")
    def _tidak_dicabut(self) -> Sitasi:
        """`dicabut` tidak dapat menjadi sitasi — lapisan kedua sesudah VS-06."""
        if self.status_keberlakuan is StatusKeberlakuan.DICABUT:
            raise ValueError(
                "sitasi dari regulasi berstatus dicabut tidak dapat dibentuk — "
                "menjawab berdasarkan aturan yang sudah dicabut adalah kekeliruan "
                "yang paling merugikan, karena jawabannya terdengar berdasar "
                "(C-07, KL-07, D-07 Bagian 4.5)"
            )
        return self


class BacaanLanjutan(BaseModel):
    """Rujukan bacaan dari `indeks_metadata` — D-14 Bagian 6, FR-D06.

    **Sengaja tidak memiliki bidang `Sitasi`.** Lihat uraian modul: ia bukan
    sitasi yang lebih lemah melainkan hal lain, dan bentuk yang berbeda membuat
    kekeliruan memindahkannya tertangkap tipe.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    judul: str = Field(min_length=1)
    tautan: str = Field(min_length=1)


class Tanggapan(BaseModel):
    """Tanggapan `/api/v1/tanya` — `docs/D14.md` Bagian 4.1, C-20.

    Bidangnya persis D-14, tidak kurang dan tidak lebih. Pemeriksa C-20
    membandingkannya dengan blok JSON pada dokumen itu sendiri.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_pesan: str = Field(min_length=1)
    status_dasar: StatusDasar
    ringkasan_tindakan: tuple[str, ...] = ()
    penjelasan: str = ""
    klaim: tuple[KlaimTampil, ...] = ()
    sitasi: tuple[Sitasi, ...] = ()
    bacaan_lanjutan: tuple[BacaanLanjutan, ...] = ()
    catatan_keberlakuan: str = ""
    penafian: str = Field(min_length=1)
    versi: Versi

    @field_validator("penafian")
    @classmethod
    def _penafian_berisi(cls, nilai: str) -> str:
        """FR-F10. Penafian yang boleh kosong adalah penafian yang akan kosong
        pada tanggapan yang disusun tergesa."""
        if not nilai.strip():
            raise ValueError("penafian tidak boleh kosong (FR-F10)")
        return nilai

    @model_validator(mode="after")
    def _bentuk_sah(self) -> Tanggapan:
        """Empat aturan bentuk — lihat uraian modul."""
        if self.status_dasar in _TANPA_ISI and (self.ringkasan_tindakan or self.klaim):
            raise ValueError(
                f"status {self.status_dasar.value} menuntut ringkasan tindakan dan "
                "klaim kosong — bentuk yang seragam itu yang membuat layar D-05 "
                "menampilkannya sebagai jawaban sah, bukan pesan galat (D-14 Bagian 4.1)"
            )
        if len(self.ringkasan_tindakan) > JUMLAH_BUTIR_RINGKASAN_MAKSIMUM:
            raise ValueError(
                f"ringkasan tindakan melampaui {JUMLAH_BUTIR_RINGKASAN_MAKSIMUM} butir "
                "(D-07 Bagian 5.1, FR-F05)"
            )
        for butir in self.ringkasan_tindakan:
            if len(butir.split()) > JUMLAH_KATA_MAKSIMUM:
                raise ValueError(
                    f"butir ringkasan melampaui {JUMLAH_KATA_MAKSIMUM} kata (NFR-19, C-13)"
                )
        ada_diubah = any(s.status_keberlakuan is StatusKeberlakuan.DIUBAH for s in self.sitasi)
        if ada_diubah and not self.catatan_keberlakuan.strip():
            raise ValueError(
                "ada sitasi berstatus diubah tetapi catatan keberlakuan kosong — "
                "FR-F14 mewajibkan penanda beserta rujukan pengubahnya"
            )
        if not ada_diubah and self.catatan_keberlakuan.strip():
            raise ValueError(
                "catatan keberlakuan terisi tanpa satu pun sitasi berstatus diubah — "
                "catatan yang terisi tanpa sebab akan diabaikan pembacanya, dan yang "
                "diabaikan tidak menjaga apa pun ketika ia sungguh perlu"
            )
        return self

    @classmethod
    def tolak_domain(cls, *, id_pesan: str, versi: Versi) -> Tanggapan:
        """Penolakan cakupan domain — FR-F13, tahap 1 D-07 Bagian 4.1.

        Berbentuk **jawaban**, bukan galat: ia menyebutkan cakupan sistem, dan
        D-05 menampilkannya sebagai jawaban sah.
        """
        return cls(
            id_pesan=id_pesan,
            status_dasar=StatusDasar.DI_LUAR_DOMAIN,
            penjelasan=PESAN_DI_LUAR_DOMAIN,
            penafian=PENAFIAN_BAKU,
            versi=versi,
        )

    @classmethod
    def tidak_ditemukan(
        cls, *, id_pesan: str, versi: Versi, bacaan_lanjutan: tuple[BacaanLanjutan, ...] = ()
    ) -> Tanggapan:
        """Balasan tidak-ditemukan — FR-F04.

        `bacaan_lanjutan` tetap boleh terisi: sumber `indeks_metadata` dapat
        ditawarkan meski tidak ada dasar yang cukup untuk menjawab, dan D-07
        Bagian 7 menetapkan blok itu memang bukan dasar jawaban.
        """
        return cls(
            id_pesan=id_pesan,
            status_dasar=StatusDasar.TIDAK_DITEMUKAN,
            bacaan_lanjutan=bacaan_lanjutan,
            penafian=PENAFIAN_BAKU,
            versi=versi,
        )
