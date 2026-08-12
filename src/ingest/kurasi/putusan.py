"""Gerbang putusan kurasi — R-02, R-07, R-08, FR-I02, FR-I03, C-06, C-07.

D-06 Bagian 7.3 memberi setiap butir **satu dari empat** putusan, dan Bagian
7.4 membakukan alasan penolakannya menjadi TL-01 s.d. TL-11.

## `ButirTayang` adalah C-06, dan ia berupa bentuk — bukan pemeriksaan

C-06 berbunyi *"Butir pengetahuan tidak tayang tanpa persetujuan kurator"*.
Pemeriksaan yang menegakkannya akan berbunyi "sebelum menayangkan, periksa
apakah butir sudah disetujui" — dan pemeriksaan semacam itu ada pada setiap
tempat penayangan, sehingga satu tempat yang lupa memuatnya tidak menghasilkan
galat apa pun. Ia menghasilkan feed yang lebih penuh, dan feed yang lebih penuh
tidak pernah terasa seperti kekeliruan.

Karena itu `ButirTayang` **hanya dibentuk modul ini**. Fitur 011 yang
menayangkan feed kelak tidak memiliki cara menayangkan kandidat — bukan
dilarang, melainkan tidak bisa. Bentuk yang sama dengan `JawabanTervalidasi`
(fitur 008) dan `Instruksi` (ADR-13); yang menjaga batasnya pemeriksa C-06.

## Persetujuan kurator tidak cukup — lapis kedua C-07

`terapkan()` menolak menayangkan butir yang regulasi sumbernya tidak berstatus
`berlaku`, meskipun kurator sudah menyetujuinya. Itu **bukan** kecurigaan
terhadap kurator.

L3 pada `saring.py` menjaga jalur ingesti, dan ia memeriksa pada saat kandidat
masuk. Antara saat itu dan saat kurator menilai terbentang antrean — D-06
Bagian 8.3 merancangnya sampai dua kali pagu harian. Regulasi yang dicabut di
tengah rentang itu lolos L3 karena L3 sudah lewat. Kurator yang menyetujuinya
tidak salah membaca; yang berubah terjadi sesudah ia membaca.

D-06 Bagian 7.4 menyediakan TL-04 bagi keadaan ini, dan galat modul ini
menyebutnya agar kurator tahu putusan mana yang seharusnya diambil.

## Keempat putusan setara

Akibatnya dibaca dari pemetaan berkunci, bukan dari rangkaian `if` yang
berakhir pada `else`. Cabang lain-lain akan memperlakukan putusan kelima yang
ditambahkan kelak sebagai putusan yang kebetulan berada paling akhir — dan
D-06 memberi keempatnya akibat yang berbeda. Bentuk yang sama dengan
`_PETA_STATUS` fitur 009.

## Yang tidak dikerjakan di sini

Pencatatan jejak kurasi FR-I05 berada pada `jejak.py` (B-2). Modul ini
menghasilkan putusan dan butir tayang; ia **tidak menulis apa pun**, sehingga
putusan yang gagal ditayangkan tidak meninggalkan setengah catatan.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from src.ingest.kurasi.butir import ButirPengetahuan
from src.kamus.segmen import StatusKeberlakuan

_BERLAKU = StatusKeberlakuan.BERLAKU
"""Satu-satunya status yang mengizinkan butir regulasi tayang — KL-07, C-07.

Dinamai agar kedua tempat yang memeriksanya — bentuk `ButirTayang` dan
`terapkan()` — membaca ketetapan yang sama. Dua penulisan `is not
StatusKeberlakuan.BERLAKU` akan berbeda pada hari salah satunya diperbarui.
"""


class GalatPutusan(Exception):
    """Putusan tidak dapat diterapkan pada butir yang menyertainya.

    Berupa galat, bukan nilai kembalian kelima: D-06 Bagian 7.3 menetapkan
    **empat** putusan, dan menambah keadaan kelima pada nilai kembalian akan
    membuat pemanggil memperlakukannya sebagai putusan yang sah. Yang terjadi
    di sini bukan putusan melainkan putusan yang tidak dapat dijalankan.
    """


class PeranKurasi(Enum):
    """Peran yang berwenang memutus — D-06 Bagian 7.1.

    **Peran, bukan orang.** C-05 dan KM-03 melarang data pribadi kurator masuk
    jejak; yang perlu ditelusuri sebuah putusan adalah kewenangannya, bukan
    siapa yang duduk pada kewenangan itu hari itu.

    Penanggung jawab teknis sengaja tidak ada di sini: D-06 Bagian 7.1 memberinya
    pemantauan antrean dan penyetelan ambang, bukan penilaian butir.
    """

    KURATOR = "kurator"
    KURATOR_PENGGANTI = "kurator_pengganti"


class JenisPutusan(Enum):
    """Empat putusan D-06 Bagian 7.3 — setiap butir menerima tepat satu."""

    SETUJUI = "setujui"
    SUNTING_LALU_SETUJUI = "sunting_lalu_setujui"
    TOLAK = "tolak"
    TUNDA = "tunda"


class AlasanTolak(Enum):
    """Kode penolakan baku D-06 Bagian 7.4 — FR-I02, FR-I05.

    Enum, bukan untai bebas. Alasan bebas mengumpul menjadi sebelas ejaan bagi
    satu alasan, dan perhitungan umpan balik penyaring kemudian menghitung
    sebelas hal berbeda — lalu tidak seorang pun tahu penyaring mana yang perlu
    diperbaiki.

    Urutannya mengikuti D-06, termasuk TL-11 yang di sana duduk di antara TL-04
    dan TL-05. Merapikannya di sini akan membuat kode ini berbeda dari
    dokumennya tanpa alasan yang tercatat.
    """

    TL_01 = "TL-01"
    TL_02 = "TL-02"
    TL_03 = "TL-03"
    TL_04 = "TL-04"
    TL_11 = "TL-11"
    TL_05 = "TL-05"
    TL_06 = "TL-06"
    TL_07 = "TL-07"
    TL_08 = "TL-08"
    TL_09 = "TL-09"
    TL_10 = "TL-10"


class Akibat(Enum):
    """Kolom akibat tabel D-06 Bagian 7.3.

    `MASUK_KOLAM` dipakai dua putusan, dan itu memang yang D-06 tetapkan:
    sunting-lalu-setujui *"disunting pada S-16, lalu masuk kolam"*. Akibatnya
    sama; jalannya yang berbeda, dan jejak B-2 yang membedakannya.
    """

    MASUK_KOLAM = "masuk_kolam"
    UMPAN_BALIK_PENYARING = "umpan_balik_penyaring"
    KEMBALI_KE_ANTREAN = "kembali_ke_antrean"

    @classmethod
    def bagi(cls, jenis: JenisPutusan) -> Akibat:
        """Akibat sebuah putusan — pemetaan berkunci, tanpa cabang lain-lain.

        Putusan yang tidak terdaftar menyalakan `KeyError`. Itu disengaja:
        putusan kelima yang ditambahkan tanpa akibatnya berhenti di sini, bukan
        mendarat pada nilai bawaan yang kebetulan aman hari itu.
        """
        return _AKIBAT[jenis]


_AKIBAT: dict[JenisPutusan, Akibat] = {
    JenisPutusan.SETUJUI: Akibat.MASUK_KOLAM,
    JenisPutusan.SUNTING_LALU_SETUJUI: Akibat.MASUK_KOLAM,
    JenisPutusan.TOLAK: Akibat.UMPAN_BALIK_PENYARING,
    JenisPutusan.TUNDA: Akibat.KEMBALI_KE_ANTREAN,
}

_MENYETUJUI = frozenset({JenisPutusan.SETUJUI, JenisPutusan.SUNTING_LALU_SETUJUI})
"""Putusan yang berakhir pada kolam butir — D-06 Bagian 7.3."""


class Putusan(BaseModel):
    """Satu putusan kurator atas satu butir — R-07.

    Beku: putusan yang dapat diubah setelah diambil tidak membuktikan apa pun
    tentang saat ia diambil, dan FR-I05 menanyakan justru itu.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    jenis: JenisPutusan
    id_butir: str = Field(min_length=1)
    peran_pemutus: PeranKurasi
    """Peran, bukan orang — C-05, KM-03, R-13."""
    waktu: AwareDatetime
    """UTC, mengikuti gaya proyek.

    Berzona wajib: waktu tanpa zona dari dua mesin tidak dapat diurutkan, dan
    urutan putusan adalah yang FR-I05 tanyakan.
    """
    alasan_tolak: AlasanTolak | None = None
    kembali_pada: date | None = None
    butir_suntingan: ButirPengetahuan | None = None
    """Naskah hasil suntingan S-16 — wajib pada sunting-lalu-setujui.

    Butir asli tetap dibawa pemanggil, sehingga keduanya dapat dibandingkan
    saat jejak ditulis. Yang tayang adalah hasil suntingannya.
    """

    @model_validator(mode="after")
    def _bidang_sesuai_jenis(self) -> Putusan:
        """Setiap jenis membawa **tepat** bidang penyertanya — kedua arah.

        Arah pertama menutup putusan yang kurang: penolakan tanpa kode tidak
        dapat menjadi umpan balik penyaring. Arah kedua menutup putusan yang
        berlebih: persetujuan yang membawa alasan penolakan adalah putusan yang
        dua bidangnya menyatakan hal berlawanan, dan pembacanya kelak memilih
        salah satunya tanpa dasar.
        """
        wajib = {
            JenisPutusan.TOLAK: ("alasan_tolak", "kode penolakan baku D-06 Bagian 7.4"),
            JenisPutusan.TUNDA: ("kembali_pada", "waktu kembali ke antrean"),
            JenisPutusan.SUNTING_LALU_SETUJUI: (
                "butir_suntingan",
                "naskah hasil suntingan S-16",
            ),
        }
        for jenis, (bidang, sebutan) in wajib.items():
            terisi = getattr(self, bidang) is not None
            if self.jenis is jenis and not terisi:
                raise ValueError(f"putusan {jenis.value} wajib membawa {sebutan}")
            if self.jenis is not jenis and terisi:
                raise ValueError(
                    f"putusan {self.jenis.value} tidak boleh membawa {sebutan}"
                )
        return self

    @model_validator(mode="after")
    def _tunda_menunjuk_ke_depan(self) -> Putusan:
        """Tunda ke tanggal yang sudah lewat mengembalikan butir ke antrean
        seketika, dan antrean yang menerima butir yang baru saja ditunda akan
        menumpuk tanpa seorang pun mengubah pagunya."""
        if self.kembali_pada is not None and self.kembali_pada <= self.waktu.date():
            raise ValueError("waktu kembali wajib sesudah tanggal putusan")
        return self

    @property
    def menyetujui(self) -> bool:
        """Apakah putusan ini berakhir pada kolam butir."""
        return self.jenis in _MENYETUJUI


class ButirTayang(BaseModel):
    """Butir yang telah melewati putusan kurator — R-02, C-06.

    **Hanya dibentuk `terapkan()` pada modul ini.** Yang menjaga batas itu
    pemeriksa C-06, sebab Python tidak memiliki cara menutup pembentukan sebuah
    tipe dari modul lain — lihat uraian modul.

    Penjagaannya tetap melekat pada bentuknya juga: kedua pemeriksaan di bawah
    berjalan pada pembentukan mana pun, termasuk pembentukan yang melewati
    `terapkan()`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    butir: ButirPengetahuan
    putusan: Putusan

    @model_validator(mode="after")
    def _berdasar_persetujuan(self) -> ButirTayang:
        """C-06 melekat pada bentuk, bukan pada jalur pembentukannya."""
        if not self.putusan.menyetujui:
            raise ValueError(
                f"butir tayang berdasar putusan {self.putusan.jenis.value} — "
                "hanya persetujuan kurator yang menayangkan butir (C-06, FR-I03)"
            )
        if self.putusan.id_butir != self.butir.id_butir:
            raise ValueError(
                "putusan menunjuk butir lain — butir yang tayang wajib butir yang dinilai"
            )
        return self

    @model_validator(mode="after")
    def _regulasi_sumber_berlaku(self) -> ButirTayang:
        """C-07 pada bentuknya — lihat uraian modul."""
        if not self.butir.bersumber_regulasi:
            return self
        if self.butir.status_keberlakuan is not _BERLAKU:
            raise ValueError(
                "regulasi sumber tidak berstatus berlaku — butir tidak boleh tayang "
                "(C-07, KL-07); putusan yang tepat TL-04"
            )
        return self


def terapkan(
    butir: ButirPengetahuan, putusan: Putusan
) -> tuple[Akibat, ButirTayang | None]:
    """Terapkan putusan pada butir — R-02, R-07.

    Mengembalikan akibatnya selalu, dan butir tayangnya **hanya bila putusan
    menyetujui**. Bentuk dua nilai ini disengaja dan mengikuti `validasi()`
    fitur 008: pemanggil yang hanya membaca nilai kedua tidak memiliki apa pun
    untuk ditayangkan ketika putusannya tolak atau tunda.

    Tidak menulis apa pun. Pencatatan jejak FR-I05 berada pada `jejak.py`,
    sehingga putusan yang gagal diterapkan tidak meninggalkan setengah catatan.
    """
    if putusan.id_butir != butir.id_butir:
        raise GalatPutusan(
            f"putusan menunjuk butir {putusan.id_butir}, "
            f"sedangkan yang dinilai {butir.id_butir}"
        )

    akibat = Akibat.bagi(putusan.jenis)
    if not putusan.menyetujui:
        return akibat, None

    tayang = _naskah_yang_tayang(butir, putusan)
    if tayang.bersumber_regulasi and tayang.status_keberlakuan is not _BERLAKU:
        raise GalatPutusan(
            "regulasi sumber tidak lagi berstatus berlaku sejak butir masuk antrean — "
            "putusan yang tepat TL-04 (C-07, KL-07)"
        )
    return akibat, ButirTayang(butir=tayang, putusan=putusan)


def _naskah_yang_tayang(
    butir: ButirPengetahuan, putusan: Putusan
) -> ButirPengetahuan:
    """Naskah hasil suntingan bila ada; naskah asli bila tidak.

    Menayangkan naskah sebelum suntingan akan menayangkan justru parafrase yang
    kurator anggap belum memadai — dan putusannya tetap tercatat sebagai
    "sunting lalu setujui", sehingga tidak seorang pun menemukannya.
    """
    suntingan = putusan.butir_suntingan
    if suntingan is None:
        return butir
    if suntingan.id_butir != butir.id_butir:
        raise GalatPutusan("suntingan mengganti identitas butir")
    if suntingan.id_dokumen_sumber != butir.id_dokumen_sumber:
        raise GalatPutusan(
            "suntingan mengganti dokumen sumber — itu butir lain, bukan suntingan "
            "(PP-02); penarikan FR-I06 akan menelusuri dokumen yang keliru"
        )
    return suntingan


