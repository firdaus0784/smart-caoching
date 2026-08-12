"""Butir pengetahuan — R-01, D-06 Bagian 5, FR-G02.

Dua belas bidang, dan D-06 menamai yang tersulit sekaligus paling menentukan:

> **Catatan atas `alasan_relevansi`.** Ini bidang tersulit sekaligus paling
> menentukan. Kalimat "Penelitian ini membahas supervisi akademik" tidak
> memenuhi syarat — itu deskripsi topik. Yang memenuhi: "Sekolah Anda
> menetapkan supervisi akademik sebagai prioritas, dan akreditasi berikutnya
> jatuh pada semester ini."

Perbedaan itu tidak dapat ditegakkan tipe — ia penilaian kurator, dan itulah
sebabnya gerbang kurasi ada. Yang dapat ditegakkan di sini: bidangnya wajib,
satu kalimat, dan tidak kosong.

## `KategoriMasalah` dipakai ulang, tidak ditulis ulang

D-06 Bagian 5 merujuk "D-03 Bagian 5" bagi `kategori`, dan `KategoriMasalah`
sudah mewujudkannya sejak fitur 003. Menulis enum kedua di sini akan
mengulangi kekeliruan `IndeksTujuan` yang ditulis dua kali dan lolos dua fitur
(KB-036).

Impornya lewat tepi `ingest → nlp` yang sudah tertulis pada `AGENTS.md`, dan
pemeriksa arah fitur 009 memeriksanya.

## Dua tipe, dan yang kedua adalah C-06

`ButirPengetahuan` adalah **kandidat**. `ButirTayang` adalah butir yang sudah
melewati putusan kurator, dan ia hanya dapat dibentuk `putusan.py`.

Fitur yang menayangkan feed kemudian **tidak memiliki cara** menayangkan
kandidat — bukan dilarang, melainkan tidak bisa. Bentuk yang sama dengan
`JawabanTervalidasi` fitur 008 dan `Instruksi` ADR-13.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.kamus.segmen import StatusKeberlakuan
from src.nlp.anotasi.skema import KategoriMasalah

JUMLAH_KATA_JUDUL_MAKSIMUM = 12
"""D-06 Bagian 5: judul maksimal 12 kata, tanpa singkatan tak dijelaskan (NFR-19)."""

JUMLAH_KATA_INTI_MAKSIMUM = 120
"""D-06 Bagian 5: `inti_temuan` ≤ 120 kata, parafrase penuh (KL-03)."""

JUMLAH_IMPLIKASI_MAKSIMUM = 3
"""D-06 Bagian 5: `implikasi_tindakan` 1–3 butir, berbentuk kalimat perintah."""

WAKTU_BACA_MAKSIMUM_MENIT = 7
"""D-06 Bagian 5 dan FR-G03: perkiraan waktu baca ≤ 7 menit."""


class JenisSumberButir(Enum):
    """Empat jenis yang tampil pada butir — D-06 Bagian 5, FR-G04.

    Berbeda dari `JenisSumber` pada `dokumen.py`: yang itu menamai **asal
    dokumen** dan menentukan peringkat kepercayaan (D-13 Bagian 6); yang ini
    menamai **penanda yang dilihat pengguna** pada layar S-06.

    Keduanya sengaja tidak disatukan. `dokumen_sekolah` adalah asal yang sah
    dan bukan penanda yang bermakna bagi pembaca feed.
    """

    RISET = "riset"
    REGULASI = "regulasi"
    DATA_RESMI = "data_resmi"
    PRAKTIK_BAIK = "praktik_baik"


class ButirPengetahuan(BaseModel):
    """Kandidat butir — **belum tayang**, dan namanya tidak menyiratkannya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_butir: str = Field(min_length=1)
    jenis_sumber: JenisSumberButir
    judul: str = Field(min_length=1)
    alasan_relevansi: str = Field(min_length=1)
    """Satu kalimat, menyebut ciri konkret sekolah pengguna — D-06 Bagian 5.

    Yang tidak dapat ditegakkan di sini: apakah kalimatnya menyebut ciri
    konkret atau sekadar mendeskripsikan topik. Itu penilaian kurator, dan
    itulah sebabnya gerbang kurasi ada.
    """
    inti_temuan: str = Field(min_length=1)
    implikasi_tindakan: tuple[str, ...] = Field(min_length=1)
    perkiraan_waktu_baca: int = Field(gt=0, le=WAKTU_BACA_MAKSIMUM_MENIT)
    kategori: KategoriMasalah
    id_dokumen_sumber: str = Field(min_length=1)
    """Wajib; **satu sumber saja** — PP-02.

    Butir bersumber ganda tidak dapat ditarik ketika salah satu sumbernya
    dicabut, sebab tidak ada jawaban tunggal atas apakah ia masih berdasar.
    """
    lisensi: str = Field(min_length=1)
    """Wajib terisi; kosong berarti tidak dapat tayang — KL-02.

    Ditegakkan tipe **dan** lapis L1. Yang di sini menutup butir yang disusun
    tanpa lisensi; yang di L1 menutup lisensi yang terisi tetapi tidak
    diizinkan.
    """
    status_keberlakuan: StatusKeberlakuan | None = None
    """Hanya untuk sumber regulasi — KL-07.

    `None` bagi sumber bukan regulasi, dan itu bukan nilai yang hilang: riset
    dan praktik baik tidak memiliki status keberlakuan. Memaksanya berisi akan
    membuat setiap butir riset mengaku `berlaku`, dan L3 kemudian memeriksa
    hal yang tidak berarti apa-apa.
    """
    tanggal_akses: date
    tenggat_terkait: date | None = None

    @field_validator("judul")
    @classmethod
    def _judul_ringkas(cls, nilai: str) -> str:
        if len(nilai.split()) > JUMLAH_KATA_JUDUL_MAKSIMUM:
            raise ValueError(
                f"judul melampaui {JUMLAH_KATA_JUDUL_MAKSIMUM} kata (D-06 Bagian 5, NFR-19)"
            )
        return nilai

    @field_validator("inti_temuan")
    @classmethod
    def _inti_ringkas(cls, nilai: str) -> str:
        if len(nilai.split()) > JUMLAH_KATA_INTI_MAKSIMUM:
            raise ValueError(
                f"inti temuan melampaui {JUMLAH_KATA_INTI_MAKSIMUM} kata (D-06 Bagian 5)"
            )
        return nilai

    @field_validator("implikasi_tindakan")
    @classmethod
    def _implikasi_terbatas(cls, nilai: tuple[str, ...]) -> tuple[str, ...]:
        if len(nilai) > JUMLAH_IMPLIKASI_MAKSIMUM:
            raise ValueError(
                f"implikasi tindakan melampaui {JUMLAH_IMPLIKASI_MAKSIMUM} butir "
                "(D-06 Bagian 5)"
            )
        return nilai

    @field_validator("alasan_relevansi", "judul", "inti_temuan", "lisensi")
    @classmethod
    def _tidak_hanya_spasi(cls, nilai: str) -> str:
        if not nilai.strip():
            raise ValueError("bidang wajib tidak boleh kosong (D-06 Bagian 5)")
        return nilai

    @property
    def bersumber_regulasi(self) -> bool:
        """Apakah lapis L3 berlaku bagi butir ini."""
        return self.jenis_sumber is JenisSumberButir.REGULASI
