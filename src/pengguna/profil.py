"""Profil sekolah — R-02, R-10, R-11, R-12, FR-A02, FR-A06, D-04 Bagian 7.1.

Enam isian *onboarding*, dan D-04 Bagian 7.1 menamainya: jabatan, masa kerja,
jumlah rombel, jumlah PTK, jalur akreditasi, wilayah.

## Angka enam tidak berdasar literatur, dan modul ini tidak mengaku sebaliknya

FR-A02 menetapkan maksimal enam isian. Penelusuran 13 Agustus 2026 tidak
menemukan rujukan terverifikasi yang menetapkannya — yang ditemukan hanya
tulisan pemasaran, yang SI-03 tolak. Usul menyatakannya **penetapan tim tanpa
dasar literatur** tercatat pada D-11 Bagian 5.

Yang membuat angkanya tetap dapat dipertahankan bukan literatur melainkan
kecocokan: keenamnya persis yang D-04 Bagian 7.1 daftarkan, sehingga kode dan
model data sepakat meski angkanya belum bersandar. Prinsip yang menopangnya —
menanyakan sisanya kemudian saat relevan — memang sudah tertulis pada FR-A02
sendiri, dan itu yang bertahan bila angkanya kelak berubah.

## Nama bidang mengikuti D-14, bukan D-04

D-04 Bagian 7.1 menulis `akreditasi`; D-14 Bagian 5.1 menulis
`profil_sekolah.jalur_akreditasi` beserta maknanya — `visitasi` atau
`automasi`, memengaruhi pemicu kontekstual D-02 Bagian 5. `AGENTS.md`
menetapkan nama bidang mengikuti D-14 Bagian 5, sehingga yang dipakai
`jalur_akreditasi`.

Selisih itu **selisih dokumen**, dan usul menyelaraskan D-04 tercatat pada
D-11 Bagian 5. Ia tidak diselesaikan diam-diam di dalam kode.

## Pembaruan menghasilkan profil baru

FR-A06 mengizinkan pembaruan kapan saja. Profil yang dapat disunting di tempat
membuat "kapan ia berubah" tidak terjawab — dan penyaringan feed FR-G01
bersandar pada prioritas yang ditetapkan bersama profil, sehingga membedakan
yang lama dari yang baru bukan kerapian melainkan syarat.

`tanggal_perbarui` bernilai `None` pada profil yang baru dibuat. Itu bukan
nilai yang hilang: ia memang belum pernah diperbarui, dan mengisinya dengan
waktu pembuatan akan membuat "sudah pernah diperbarui" tidak dapat dibedakan.

## Wilayah adalah satu-satunya teks bebas, dan karena itu dijaga

KM-03 melarang bidang teks bebas menyimpan data pribadi. Pendeteksinya
**dipakai ulang** dari `src/nlp/anonimisasi/pola.py` — FR-B04, enam pengenal —
lewat tepi `pengguna → nlp`. Menyalinnya ke sini akan mengulangi kekeliruan
yang baru saja diperbaiki pada fitur 010 B-2: pola yang sama tertulis tiga
kali, dan yang tertinggal adalah yang menjaga R-11.

Batasnya diakui terbuka: pendeteksi itu tidak menangkap nama perorangan maupun
alamat, dan uraian modulnya menyatakannya tegas. Yang menahan sisanya adalah
bahwa `wilayah` diisi nama wilayah, bukan alamat.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.nlp.anonimisasi.pola import periksa_data_pribadi

BIDANG_ONBOARDING_MAKSIMUM = 6
"""Isian yang diminta saat *onboarding* — FR-A02.

**Penetapan tim tanpa dasar literatur** (SI-01 pilihan kedua, usul pada D-11
Bagian 5). Penelusuran tidak menemukan rujukan terverifikasi yang menetapkan
angka ini; yang ada hanya tulisan pemasaran, dan D-11 memuat Peffers, Hevner,
serta Landis & Koch.

Ia tetap ditegakkan karena keenamnya persis daftar D-04 Bagian 7.1 — kode dan
model data sepakat meski angkanya belum bersandar.
"""


class JalurAkreditasi(Enum):
    """`profil_sekolah.jalur_akreditasi` — D-14 Bagian 5.1.

    Dua nilai, dan AG-04 melarang menambahnya. Memengaruhi pemicu kontekstual
    D-02 Bagian 5: sekolah berjalur visitasi menghadapi tenggat yang berbeda
    dari sekolah berjalur automasi.
    """

    VISITASI = "visitasi"
    AUTOMASI = "automasi"


class ProfilSekolah(BaseModel):
    """Profil sekolah pengguna — delapan bidang D-04 Bagian 7.1.

    Beku. Pembaruan menghasilkan profil baru lewat `diperbarui()`.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # Tanpa `hide_input_in_errors`, pydantic menyalin nilai masukan ke
        # dalam pesan galat — sehingga nomor yang ditolak penjagaan KM-03 pada
        # `wilayah` tetap muncul lewat jalur yang bukan pesan kita. Galat yang
        # mengulang muatannya memindahkan kebocoran dari basis data ke log.
        #
        # Cacat ini ada pada berkas ini sejak tugas A-1 dan ditemukan beberapa
        # jam kemudian oleh uji fitur 012 — penjagaannya benar, rendering
        # galatnya yang membocorkan. Sapuan pada
        # `tests/tata_kelola/test_galat_tidak_membocorkan.py` menutupnya.
        hide_input_in_errors=True,
    )

    id_pengguna: str = Field(min_length=1)
    jabatan: str = Field(min_length=1)
    masa_kerja: int = Field(ge=0)
    """Tahun. **Nol diterima** — kepala sekolah yang baru diangkat bermasa kerja
    nol tahun, dan menolaknya akan menutup justru persona yang paling
    membutuhkan pendampingan (D-02)."""
    jumlah_rombel: int = Field(gt=0)
    """Rombongan belajar. Nol menandakan isian yang belum diisi, bukan fakta —
    sekolah tanpa rombongan belajar bukan sekolah yang sedang dikelola."""
    jumlah_ptk: int = Field(gt=0)
    """Pendidik dan tenaga kependidikan. Alasan yang sama dengan `jumlah_rombel`."""
    jalur_akreditasi: JalurAkreditasi
    wilayah: str = Field(min_length=1)
    tanggal_perbarui: datetime | None = None
    """`None` berarti belum pernah diperbarui — lihat uraian modul."""

    @field_validator("jabatan", "wilayah")
    @classmethod
    def _tidak_hanya_spasi(cls, nilai: str) -> str:
        if not nilai.strip():
            raise ValueError("bidang wajib tidak boleh kosong (D-04 Bagian 7.1)")
        return nilai

    @field_validator("wilayah")
    @classmethod
    def _tanpa_data_pribadi(cls, nilai: str) -> str:
        """KM-03 dan R-11 — **tolak, jangan saring.**

        Jenisnya disebut pada galat; **nilainya tidak pernah**. Galat yang
        mengutip muatannya memindahkan kebocoran dari basis data ke log.
        """
        temuan = periksa_data_pribadi(nilai)
        if temuan:
            raise ValueError(
                f"wilayah memuat pengenal berjenis {temuan[0].jenis} — isikan nama "
                "wilayah saja"
            )
        return nilai

    def diperbarui(self, **ganti: Any) -> ProfilSekolah:
        """Profil baru dengan bidang yang diganti — FR-A06, R-10.

        Waktunya dicatat UTC (KM-01). Pemiliknya tidak dapat diganti: profil
        yang berpindah pengguna adalah profil yang tidak dapat ditelusuri
        kepada siapa pun.

        Dibentuk lewat `model_validate`, bukan `model_copy`. Yang kedua
        **melewati validator** — pembaruan yang menyisipkan nomor telepon ke
        `wilayah` akan lolos, dan R-11 hanya berlaku pada pembentukan pertama.
        """
        if "id_pengguna" in ganti:
            raise ValueError("profil tidak dapat berpindah pengguna")
        if "tanggal_perbarui" in ganti:
            raise ValueError(
                "waktu pembaruan dicatat modul ini, bukan diisi pemanggil — waktu "
                "yang diisi pemanggil dapat mendahului perubahannya"
            )
        return ProfilSekolah.model_validate(
            {**self.model_dump(), **ganti, "tanggal_perbarui": datetime.now(UTC)}
        )
