"""Skema label, kategori, dan versinya — R-01 s.d. R-04, FR-C04, FR-C05, FR-C08.

Seluruh isi modul ini ditetapkan **dari D-03**, bukan dari bentuk ekspor
perangkat anotasi mana pun (KB-021). Arah itu menentukan: tipe yang disusun
mengikuti bentuk ekspor akan berubah ketika perangkatnya naik versi, dan
korpus yang sudah dianotasi tidak ikut berubah bersamanya.

**Label dan kategori adalah tipe, bukan untai bebas.** Untai bebas berarti dua
anotator dapat menuliskan hal yang sama dengan dua ejaan — "JABATAN/PERAN" dan
"jabatan_peran" — dan kesepakatan mereka terhitung nol atas perbedaan yang
sebenarnya tidak ada.

**Urutan pemutus bukan K1 sampai K8.** D-03 A-04 menetapkan K5 → K7 → K2 → K1
→ K3 → K4 → K6 → K8: kategori dengan konsekuensi kepatuhan tertinggi lebih
dahulu, dan K8 terakhir karena hampir semua dokumen manajerial dapat dipaksa
masuk ke sana. Urutan yang disusun ulang menjadi urut angka akan tampak lebih
rapi dan menghasilkan katalog yang menumpuk pada K8.

**Mayor dan minor dibedakan** karena akibatnya berbeda (FR-C08). Kenaikan
mayor berarti arti label berubah, sehingga anotasi lama tidak lagi berarti hal
yang sama dan batch terdampak wajib dianotasi ulang. Kenaikan minor menambah
tanpa mengubah arti. Tanpa pembedaan itu, seluruh korpus dianotasi ulang
setiap kali satu label ditambahkan — dan tim yang menghadapi biaya sebesar itu
akan berhenti menaikkan versi sama sekali.
"""

from __future__ import annotations

from enum import Enum
from typing import Final

from pydantic import BaseModel, ConfigDict, Field


class LabelEntitas(Enum):
    """Delapan label entitas FR-C04. Nilainya mengikuti D-03 Bagian 4."""

    REGULASI = "REGULASI"
    PROGRAM = "PROGRAM"
    ANGGARAN = "ANGGARAN"
    JABATAN_PERAN = "JABATAN_PERAN"
    INDIKATOR_MUTU = "INDIKATOR_MUTU"
    TENGGAT_WAKTU = "TENGGAT_WAKTU"
    INSTANSI = "INSTANSI"
    DOKUMEN = "DOKUMEN"


class KategoriMasalah(Enum):
    """Delapan kategori masalah manajerial — D-03 Bagian 5.

    Definisi operasional, batas inklusi, dan batas eksklusi dimiliki D-03.
    Modul ini mewujudkan kodenya, tidak menafsirkan artinya.
    """

    K1 = "K1"
    K2 = "K2"
    K3 = "K3"
    K4 = "K4"
    K5 = "K5"
    K6 = "K6"
    K7 = "K7"
    K8 = "K8"


KATEGORI_URUTAN_PEMUTUS: Final[tuple[KategoriMasalah, ...]] = (
    KategoriMasalah.K5,
    KategoriMasalah.K7,
    KategoriMasalah.K2,
    KategoriMasalah.K1,
    KategoriMasalah.K3,
    KategoriMasalah.K4,
    KategoriMasalah.K6,
    KategoriMasalah.K8,
)
"""Urutan pemutus D-03 A-04, dipakai ketika dua kategori sama kuat.

Sengaja **tidak** urut angka. Menyusunnya ulang menjadi urut angka akan tampak
lebih rapi dan menghasilkan katalog yang menumpuk pada K8 — kategori yang
hampir semua dokumen manajerial dapat dipaksa masuk ke dalamnya.
"""


class VersiSkema(BaseModel):
    """Versi skema anotasi — FR-C08.

    Beku dan terurut. Terurut karena "versi naik" pada FR-C08 menuntut
    perbandingan yang terdefinisi; beku karena versi yang dapat diubah setelah
    melekat pada anotasi membuat penandaan batch tidak berarti.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    mayor: int = Field(ge=0)
    minor: int = Field(ge=0)

    def __str__(self) -> str:
        return f"{self.mayor}.{self.minor}"

    def __lt__(self, lain: VersiSkema) -> bool:
        return (self.mayor, self.minor) < (lain.mayor, lain.minor)

    def menuntut_anotasi_ulang(self, sebelumnya: VersiSkema) -> bool:
        """Apakah kenaikan dari `sebelumnya` ke versi ini menuntut anotasi ulang.

        Hanya kenaikan **mayor**. Perbandingan mundur menghasilkan `False`:
        ia tanda pemanggil keliru, bukan alasan menandai batch, dan menandainya
        akan membuat batch terbaru dianggap usang.
        """
        return self.mayor > sebelumnya.mayor
