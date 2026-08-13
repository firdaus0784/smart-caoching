"""Peristiwa telemetri — R-01, R-02, R-03, R-06, R-09, FR-J01, FR-J02.

Taksonomi `docs/D01.md` Bagian 9, yang menyebutnya **"luaran teknis kunci
2026"**: ia merekam perilaku belajar alami tanpa intervensi gamifikasi,
sehingga menjadi kelompok pembanding historis bagi uji efek gamifikasi 2028.

Kode yang hilang dari enum ini berarti peristiwa yang tidak pernah terekam —
dan metrik turunan Bagian 9.1 yang bersandar padanya menjadi nol yang terbaca
seperti temuan.

## Pseudonim, bukan identitas

FR-J02 menulis "id pengguna **terpseudonim**". `Peristiwa` karena itu **tidak
memiliki** bidang `id_pengguna` sama sekali — bukan memilikinya lalu
mengosongkannya. Yang tidak ada tidak dapat terisi, dan bidang yang boleh
kosong akan terisi pada pemanggilan pertama yang menganggapnya berguna.

Pemetaannya tinggal di `src/penyimpanan/pseudonim.py` (fitur 022) dan tidak
terjangkau modul ini — FR-J06 dan C-05 yang sudah berdiri.

## `properti` dijaga dua arah, dan keduanya perlu

D-14 Bagian 5.1: *"Isinya mengikuti taksonomi D-01 Bagian 9; tidak pernah
memuat data pribadi."*

- **Nilainya** disapu pendeteksi FR-B04 — nomor yang tersalin ke properti.
- **Kuncinya** ditolak bila beridentitas. Ini yang paling mudah terlewat:
  kunci beridentitas **lolos pendeteksi pola** sebab nilainya belum tentu
  berpola. `{"nama": "Siti Aminah"}` bersih menurut keenam pola dan tetap
  data pribadi.

Keduanya menyapu **hingga ke dalam**: data pribadi yang disembunyikan satu
lapis lebih dalam adalah bentuk yang paling mungkin terjadi ketika pemanggil
menyalin objek apa adanya.

## Tolak, jangan saring

Menyaring diam-diam menghasilkan peristiwa yang tampak bersih sementara
penulisnya tidak pernah tahu ia hampir membocorkan sesuatu — dan ia akan
menulisnya lagi. Galatnya menyebut **jenis** temuan, tidak pernah nilainya.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from src.nlp.anonimisasi.pola import periksa_data_pribadi

_KUNCI_BERIDENTITAS: tuple[str, ...] = (
    "id_pengguna",
    "nama",
    "surel",
    "email",
    "telepon",
    "alamat",
    "nik",
    "nip",
    "nisn",
    "nuptk",
)
"""Penggal nama kunci yang menandakan muatan beridentitas — KM-03.

Daftar hitam, dan arahnya disengaja. Daftar putih akan menuntut setiap properti
baru pada D-01 Bagian 9 didaftarkan, dan yang lupa didaftarkan justru lolos.
Di sini kekeliruan ke arah ketat hanya menuntut penamaan ulang kunci,
sedangkan kekeliruan ke arah longgar menyimpan data pribadi pada tabel yang
diekspor untuk analisis.

Dicocokkan sebagai penggal dan tanpa membedakan huruf besar-kecil: kunci yang
ditulis `Nama_Lengkap` sama saja isinya.
"""


class JenisPeristiwa(Enum):
    """Kedua puluh kode taksonomi `docs/D01.md` Bagian 9.

    Urutannya mengikuti dokumen, bukan abjad — pembaca yang membandingkan
    keduanya berdampingan tidak perlu menerjemahkan urutan.
    """

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    QUESTION_ASKED = "question_asked"
    ANSWER_SERVED = "answer_served"
    ANSWER_REJECTED_VALIDATOR = "answer_rejected_validator"
    INJECTION_SUSPECTED = "injection_suspected"
    ANSWER_RATED = "answer_rated"
    CITATION_OPENED = "citation_opened"
    DISCOVERY_SERVED = "discovery_served"
    DISCOVERY_OPENED = "discovery_opened"
    DISCOVERY_READ_COMPLETE = "discovery_read_complete"
    DISCOVERY_DISMISSED = "discovery_dismissed"
    DISCOVERY_SAVED = "discovery_saved"
    KNOWLEDGE_CHECK_STARTED = "knowledge_check_started"
    KNOWLEDGE_CHECK_COMPLETED = "knowledge_check_completed"
    COMMITMENT_CREATED = "commitment_created"
    COMMITMENT_STATUS_UPDATED = "commitment_status_updated"
    RETURN_VISIT = "return_visit"
    SEARCH_PERFORMED = "search_performed"
    EXPORT_PERFORMED = "export_performed"


class Peristiwa(BaseModel):
    """Satu peristiwa telemetri — enam bidang FR-J02, tabel `peristiwa` D-04.

    **Hanya dibentuk `src/telemetri/gerbang.py`.** Yang menjaga batas itu
    pemeriksa C-04; lihat uraian modul gerbang.

    Beku: peristiwa yang dapat diubah sesudah terekam tidak membuktikan apa pun
    tentang apa yang terjadi.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # `hide_input_in_errors` bukan kerapian. Tanpanya pydantic menyalin
        # **nilai masukan** ke dalam pesan galat, sehingga nomor yang ditolak
        # penjagaan KM-03 tetap muncul — lewat jalur yang bukan pesan kita.
        # Galat yang mengulang muatannya memindahkan kebocoran dari basis data
        # ke log, yaitu kebalikan persis dari maksud penjagaannya.
        #
        # Ditemukan uji `test_galat_properti_tidak_mengulang_muatannya` pada
        # 13 Agustus 2026; penjagaannya sudah benar, rendering galatnya yang
        # membocorkan.
        hide_input_in_errors=True,
    )

    pseudonim: str = Field(min_length=1)
    """Penanda terpseudonim — **bukan** id pengguna (FR-J02, C-05)."""
    jenis: JenisPeristiwa
    waktu: AwareDatetime
    """UTC (KM-01). Retensi D1/D7/D30 dihitung dari urutannya."""
    properti: dict[str, Any]
    versi_aplikasi: str = Field(min_length=1)
    versi_model: str = Field(min_length=1)
    """Wajib. Peristiwa tanpa versi tidak dapat dibandingkan lintas percobaan,
    dan C-09 menuntut justru itu."""

    @field_validator("versi_aplikasi", "versi_model", "pseudonim")
    @classmethod
    def _tidak_hanya_spasi(cls, nilai: str) -> str:
        if not nilai.strip():
            raise ValueError("bidang wajib tidak boleh kosong (FR-J02)")
        return nilai

    @field_validator("properti")
    @classmethod
    def _tanpa_data_pribadi(cls, nilai: dict[str, Any]) -> dict[str, Any]:
        """Kedua arah, hingga ke dalam — lihat uraian modul."""
        _sapu(nilai)
        return nilai


def _sapu(muatan: Any) -> None:
    """Telusuri properti sampai ke daun; tolak pada temuan pertama.

    Menolak pada temuan pertama memadai: yang perlu diketahui penulis adalah
    bahwa ada, bukan berapa banyak — dan melaporkan seluruhnya menuntut
    membawa letaknya, yang mendekatkan galat pada muatannya.
    """
    if isinstance(muatan, dict):
        for kunci, nilai in muatan.items():
            _tolak_kunci_beridentitas(kunci)
            _sapu(nilai)
        return
    if isinstance(muatan, list | tuple):
        for anak in muatan:
            _sapu(anak)
        return
    if isinstance(muatan, str):
        temuan = periksa_data_pribadi(muatan)
        if temuan:
            raise ValueError(
                f"properti memuat pengenal berjenis {temuan[0].jenis} — sebutkan "
                "jenis temuannya, jangan salin nilainya (KM-03, D-14 Bagian 5.1)"
            )


def _tolak_kunci_beridentitas(kunci: str) -> None:
    """Kunci beridentitas lolos pendeteksi pola — lihat uraian modul."""
    rendah = str(kunci).lower()
    for penggal in _KUNCI_BERIDENTITAS:
        if penggal in rendah:
            raise ValueError(
                f"properti memuat kunci beridentitas '{penggal}' — telemetri "
                "menyimpan pseudonim, bukan identitas (KM-03, C-05)"
            )
