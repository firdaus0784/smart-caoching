"""Jalur penyematan korpus — R-01 s.d. R-11 fitur 026, TK-57.

Fitur 019 membangun sisi **pembacaan** indeks vektor: `SumberVektor` mencari
segmen terdekat dengan kueri. Modul ini sisi **penulisannya** — yang sebelum
fitur 026 tidak dimiliki baris pembangunan mana pun, sehingga vektor diisi
perkakas SQL dan berkas uji alih-alih kode yang disebarkan.

Akibat yang TK-57 catat: R-06 fitur 019 menuntut versi penyemat tercatat pada
setiap keluaran yang **membentuk indeks**, dan tanpa pembentukan indeks tidak
ada yang mencatat apa pun. Indeks dapat dibangun dua kali dengan model berbeda
tanpa satu catatan pun yang membedakannya.

## Letaknya di `src/ingest/`, dan itu diputus Gerbang 1

Tepi `ingest → llm` dan `ingest → nlp` sudah ada dan tertulis pada
`AGENTS.md`; `kamus`, `logbook`, dan `penyimpanan` lapisan terbuka. Nol tepi
arah baru. Dua kemungkinan lain ditolak: `src/rag/` akan memberi hak tulis
kepada lapisan yang C-17 justru batasi, dan `src/penyimpanan/` lapisan di
bawah yang tidak boleh memanggil `llm`.

## Waktu disuntikkan, tidak diambil dari jam

Versi indeks berupa cap waktu (Keputusan Gerbang 1 K-2). Fungsi yang memanggil
`datetime.now()` sendiri tidak dapat diuji **nilainya** — hanya polanya, dan
uji atas pola lulus juga pada penyusun yang selalu mengembalikan tanggal yang
sama. `sekarang` karena itu diserahkan pemanggil, bentuk yang sejajar dengan
`Penyemat` pada R-04.

## Mengapa cap waktu, bukan cacah naik

Cacah menuntut keadaan tersimpan; keadaan tersimpan dapat disetel ulang; dan
cacah yang tersetel ulang **memakai kembali nomor versi yang sudah pernah
dipakai** — tanpa galat, sehingga dua percobaan berbeda tercatat pada versi
indeks yang sama. Cap waktu tidak dapat terpakai ulang dan tidak menuntut
keadaan apa pun.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import VersiPenyemat

BENTUK_WAKTU_VERSI: Final = "%Y%m%dT%H%M%SZ"
"""Cap waktu pada versi indeks, selalu UTC — KM-01.

Huruf `Z` ditulis harfiah dan bukan hasil pemformatan zona: ia baru benar
sesudah waktunya diubah ke UTC, dan `susun_versi_indeks` yang memastikannya.
"""


def susun_versi_indeks(indeks_tujuan: IndeksTujuan, *, sekarang: Callable[[], datetime]) -> str:
    """Versi indeks bagi satu pembangunan — K-2, RT-05, D-07 Bagian 3.3.

    Berbentuk `<indeks>-<YYYYMMDDTHHMMSSZ>`. Bagian indeks dibaca dari nilai
    enumnya, **bukan** dari nama skema basis data: yang disusun di sini label
    percobaan, bukan pengenal tabel, dan menyalin nama skema ke sini akan
    membuat dua tempat menyatakan hal yang sama.

    Waktu berzona lain **diubah** ke UTC, tidak ditolak — KM-01 menuntut
    penyimpanan dalam UTC, bukan menuntut pemanggil sudah mengubahnya. Waktu
    tanpa zona ditolak: ia tidak dapat diubah tanpa menebak zonanya, dan
    tebakan itu tidak pernah terlihat pada hasilnya.
    """
    saat = sekarang()
    if saat.tzinfo is None:
        raise ValueError(
            "waktu pembangunan indeks wajib berzona — waktu tanpa zona tidak "
            "dapat diubah ke UTC tanpa menebak, dan tebakannya tidak terbaca "
            "pada versi yang dihasilkan (KM-01)"
        )
    return f"{indeks_tujuan.value}-{saat.astimezone(UTC).strftime(BENTUK_WAKTU_VERSI)}"


class HasilPenyematan(BaseModel):
    """Apa yang satu pembangunan indeks kerjakan, beserta versinya.

    ## Tiga bidang hitungan, bukan satu

    `tersemat` sendirian tidak dapat dibedakan dari indeks yang sebagian
    segmennya **dilewati** karena bertext kosong, dan pembedaan itu yang
    memberi tahu apakah yang bermasalah korpusnya atau jalurnya.

    `tersisa_tanpa_vektor` dibaca sesudah penjalanan: nol berarti indeks penuh.
    Ia bukan turunan kedua bidang lain — segmen dapat bertambah di antara
    pembacaan dan penulisan, dan angka yang dihitung ulang dari bidang lain
    akan menyatakan keadaan yang sudah lewat sebagai keadaan sekarang.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    indeks_tujuan: IndeksTujuan
    versi_indeks: str = Field(min_length=1)
    versi_penyemat: VersiPenyemat
    tersemat: int = Field(ge=0)
    """Segmen yang vektornya benar-benar ditulis pada penjalanan ini."""
    dilewati_teks_kosong: int = Field(ge=0)
    """Segmen yang dilewati sebab teksnya kosong — R-05.

    Dilewati **dan dihitung**. Menyematkannya menjadi vektor nol tidak
    menghasilkan galat; ia menghasilkan tetangga terdekat yang salah.
    """
    tersisa_tanpa_vektor: int = Field(ge=0)
    """Segmen yang masih belum tersemat sesudah penjalanan ini selesai."""
