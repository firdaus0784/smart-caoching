"""Pemisahan indeks menurut lisensi — R-01 s.d. R-05, FR-D06, C-02, KL-01.

D-07 Bagian 3.1 menyatakannya dalam satu kalimat: **"Ini keputusan struktural,
bukan penyaringan."** Alasannya pada kalimat berikutnya — pemisahan pada
tingkat indeks membuat kekeliruan kueri tidak dapat meloloskan teks berlisensi
tertutup ke penyedia LLM.

Penyaringan saat kueri terasa cukup: satu klausa, mudah dibaca, mudah diuji.
Yang membuatnya tidak cukup adalah bahwa klausa itu ada pada **setiap** kueri,
dan satu kueri yang lupa memuatnya tidak menghasilkan galat apa pun — ia
menghasilkan jawaban yang lebih lengkap, dan jawaban yang lebih lengkap tidak
pernah terasa seperti kekeliruan sampai audit lisensi.

Bentuk yang sama dengan C-03 fitur 002: kredensial berbeda, bukan penanda
status. Enum di sini menamai tujuannya; yang menjaganya `kredensial_baku.py`
dan pemeriksa C-02.

## Dua penolakan, dan yang kedua menjaga hal lain

**Lisensi tertutup ke indeks utama ditolak** — itu yang dinamai fitur ini.

**Segmen yang anonimisasinya belum terverifikasi ditolak dari kedua indeks** —
dan itu yang mudah luput. Penegakan lisensi menyita seluruh perhatian di sini,
sementara dokumen yang anonimisasinya masih menunggu dapat masuk indeks utama
tanpa satu pun pemeriksaan menyala. Yang bocor di sana bukan lisensi melainkan
data pribadi, dan itu lebih berat.

Indeks metadata bukan tempat pembuangan bagi keduanya: segmen tak terverifikasi
ditolak dari sana juga. Menaruhnya di metadata akan terasa aman dengan alasan
ia tidak masuk konteks LLM — padahal ia tetap tersimpan.

## Nilai enum dimiliki D-14, bukan berkas ini

`IndeksTujuan` **diimpor dari `src/kamus/segmen.py`, tidak didefinisikan di
sini.** Fitur 006 mendefinisikannya di berkas ini tanpa memeriksa bahwa
`src/llm/tipe.py` sudah memuatnya sejak fitur 001; kekembaran itu ditemukan
pada fitur 008 dan diselesaikan dengan memindahkannya ke kamus. Yang membuatnya
lebih dari kerapian: enum itu tempat C-02 terbaca, dan dua definisi berarti
perubahan D-14 dapat memperbarui satu dan melewatkan yang lain.

**`IndeksTujuan` sengaja bukan nilai ketiga pada `Area`.** Indeks bukan area
penyimpanan melainkan tujuan segmen, dan D-14 sudah menamai keduanya terpisah.

## Lisensi diambil, tidak disimpulkan

D-06 aturan pelaksanaan KL-01: *"Bidang lisensi diambil dari metadata sumber,
bukan disimpulkan. Artikel tanpa keterangan lisensi yang terbaca mesin
diperlakukan sebagai tertutup. Ini pilihan konservatif yang disengaja:
kekeliruan ke arah ini hanya mengurangi jumlah butir, sedangkan kekeliruan ke
arah sebaliknya menggugurkan publikasi."*

Modul ini karena itu **tidak menyebut `JenisSumber` sama sekali**. Menyimpulkan
lisensi dari jenis sumber akan membuat artikel tertutup yang salah dikategorikan
saat kurasi ikut masuk indeks utama — dan kekeliruan kurasi tidak seharusnya
menjadi kebocoran lisensi.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.kamus.segmen import IndeksTujuan


class StatusLisensi(Enum):
    """Lisensi sumber sebuah segmen — D-06, KL-01.

    Dua nilai saja, dan ketiadaan keterangan **bukan** nilai ketiga: D-06
    menetapkan lisensi yang tidak terbaca mesin diperlakukan sebagai tertutup.
    Nilai ketiga bernama "tidak diketahui" akan mengundang seseorang
    memperlakukannya sebagai kasus tersendiri yang lebih longgar.
    """

    TERBUKA = "terbuka"
    TERTUTUP = "tertutup"


_AWALAN_TERBUKA = ("cc-by", "cc0", "cc-zero", "public domain", "pddl", "odc-by")
"""Awalan lisensi terbuka yang terbaca mesin.

Daftar putih, bukan daftar hitam. Daftar hitam meloloskan setiap sebutan yang
belum pernah terlihat, dan yang belum pernah terlihat justru yang paling
mungkin salah dibaca.
"""


def lisensi_dari_metadata(nilai: str | None) -> StatusLisensi:
    """Baca lisensi dari metadata sumber — **tidak menyimpulkan** (D-06).

    Ketiadaan keterangan, keterangan kosong, dan keterangan yang tidak dikenali
    seluruhnya menghasilkan `TERTUTUP`. Itu pilihan konservatif D-06, dan
    arahnya disengaja: kekeliruan ke arah ini hanya mengurangi jumlah butir,
    sedangkan kekeliruan ke arah sebaliknya menggugurkan publikasi.
    """
    if not nilai:
        return StatusLisensi.TERTUTUP
    bersih = nilai.strip().lower()
    if any(bersih.startswith(awalan) for awalan in _AWALAN_TERBUKA):
        return StatusLisensi.TERBUKA
    return StatusLisensi.TERTUTUP


def indeks_bagi(lisensi: StatusLisensi) -> IndeksTujuan:
    """Indeks tujuan yang ditetapkan **saat masuk**, bukan saat kueri (R-03)."""
    return IndeksTujuan.UTAMA if lisensi is StatusLisensi.TERBUKA else IndeksTujuan.METADATA


class SegmenTerindeks(BaseModel):
    """Satu segmen beserta indeks tempatnya berada.

    `anonimisasi_terverifikasi` berupa bool, bukan enum `StatusAnonimisasi`.
    Sebabnya aturan arah `AGENTS.md`: `src/penyimpanan/` adalah lapisan di
    bawah `src/ingest/`, sehingga mengimpor enumnya ke sini akan membalik
    ketergantungan. Pemetaan dari enum ke bool tetap satu tempat —
    `Dokumen.anonimisasi_mengizinkan_indeks` pada fitur 002 — sehingga nilai
    keempat yang ditambahkan D-14 kelak tidak diam-diam ikut lolos.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_segmen: str = Field(min_length=1)
    id_dokumen: str = Field(min_length=1)
    teks: str = Field(min_length=1)
    lisensi: StatusLisensi
    indeks_tujuan: IndeksTujuan
    anonimisasi_terverifikasi: bool
    penanda_bagian: str = Field(min_length=1)
    """Pasal, ayat, butir, atau subjudul — `docs/D14.md` Bagian 5, **wajib**.

    D-14 menyatakan alasannya dalam empat kata: *"tanpanya FR-F11 gagal"*.
    FR-F11 menuntut tautan sitasi mengarah ke bagian spesifik dokumen, bukan
    ke dokumen utuh, dan dasarnya titik kritis T2 pada D-02.

    Ditambahkan pada fitur 007, bukan 006. Itu kelalaian saya pada fitur 006
    dan tercatat demikian pada KB-034 — bukan keputusan yang ditinjau ulang.
    Yang menuntutnya ditutup sekarang: fitur 007 menjadi pemakai pertama
    segmen, dan segmen yang dapat diambil tetapi tidak dapat disitasi baru
    ketahuan pada fitur 009, ketika indeksnya mungkin sudah terisi.

    Tanpa nilai bawaan, dan `min_length` saja tidak cukup — ia meloloskan
    `" "`. Penanda berisi satu spasi tidak menunjuk pasal mana pun.
    """

    @field_validator("penanda_bagian")
    @classmethod
    def _penanda_menunjuk_sesuatu(cls, nilai: str) -> str:
        """Dipangkas saat masuk, bukan saat ditampilkan.

        Satu tempat, bukan setiap tempat: penanda yang tersimpan dengan spasi
        di ujung akan muncul begitu pada setiap sitasi yang menampilkannya, dan
        memangkasnya di tempat penampilan berarti memangkasnya di banyak
        tempat — salah satunya akan terlewat.
        """
        bersih = nilai.strip()
        if not bersih:
            raise ValueError(
                "penanda bagian tidak boleh kosong — D-14 Bagian 5 mewajibkannya "
                "sebab tautan sitasi harus mengarah ke pasal, bukan ke dokumen "
                "utuh (FR-F11, titik kritis T2)"
            )
        return bersih

    @model_validator(mode="after")
    def _penempatan_sah(self) -> SegmenTerindeks:
        """Dua penolakan — lihat uraian modul.

        Diperiksa **saat segmen dibentuk**, bukan saat dibaca. Segmen tertutup
        yang sempat ada di indeks utama adalah segmen yang dapat terbaca
        sebelum penyaring mana pun berjalan.
        """
        if not self.anonimisasi_terverifikasi:
            raise ValueError(
                "segmen yang anonimisasinya belum terverifikasi tidak boleh masuk "
                "indeks mana pun — termasuk indeks metadata, sebab ia tetap "
                "tersimpan meski tidak masuk konteks LLM (D-14 Bagian 5)"
            )
        if self.lisensi is StatusLisensi.TERTUTUP and self.indeks_tujuan is IndeksTujuan.UTAMA:
            raise ValueError(
                "segmen berlisensi tertutup tidak boleh masuk indeks utama — "
                "pemisahan ini struktural, bukan penyaringan, sebab satu kueri "
                "yang lupa menyaring tidak menghasilkan galat melainkan jawaban "
                "yang lebih lengkap (C-02, FR-D06, D-07 Bagian 3.1)"
            )
        return self
