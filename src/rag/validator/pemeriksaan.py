"""Kode, status, dan hasil satu pemeriksaan — R-08, R-10, D-07 Bagian 6.1.

## Tiga keadaan, dan mengapa keenam kalinya masih perlu ditulis

Tiga dari sembilan pemeriksaan D-07 Bagian 6.1 tidak dapat dibangun pada fitur
008: VS-03 dan VS-05 menunggu model sematan serta ambang BT-29, VS-07 menunggu
model NER.

Validator yang mengembalikan `True` atas kesembilannya **tidak dapat dibedakan
dari validator yang benar** — dan ia tinggal di komponen yang D-04 ADR-04 sebut
terpenting dalam sistem. Itu TA-01 pada tempat paling berbahaya: laporan bersih
yang tidak memeriksa apa pun.

`Status` karena itu bernilai tiga, bukan dua. Bentuknya sengaja sama dengan
`make compliance` — LULUS, GAGAL, BELUM-DAPAT-DIPERIKSA — sebab perkakas yang
menegakkan pelajaran itu pada proyek kini menegakkannya pada sistem.

Pola yang sama sudah dipakai lima kali: `HasilSistem` (015),
`HasilKesepakatan` (003), `bendera` (016), `Nilai` (004), `HasilHitung` (005).

## Kode pemeriksaan dimiliki D-07, bukan berkas ini

`KodePemeriksaan` memuat **kesembilan** kode D-07 Bagian 6.1, termasuk tiga
yang belum dapat dijalankan. Enum yang hanya memuat enam akan membuat
"seluruhnya lulus" berarti "keenam yang kami pilih lulus", dan tidak ada yang
dapat membaca ketiadaan ketiganya dari kode.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KodePemeriksaan(Enum):
    """Kesembilan pemeriksaan D-07 Bagian 6.1.

    Dilaporkan apa adanya pada kegagalan (R-08): D-07 Bagian 6.2 menetapkan
    setiap kegagalan memicu peristiwa `answer_rejected_validator` **beserta
    kode pemeriksaan yang gagal**, dan itu yang membuat RT-02 terukur.
    Kegagalan tanpa kodenya hanya menghasilkan angka penolakan tanpa sebab.
    """

    VS_01 = "VS-01"
    VS_02 = "VS-02"
    VS_03 = "VS-03"
    VS_04 = "VS-04"
    VS_05 = "VS-05"
    VS_06 = "VS-06"
    VS_07 = "VS-07"
    VS_08 = "VS-08"
    VS_09 = "VS-09"


class Status(Enum):
    """Tiga keadaan sebuah pemeriksaan — lihat uraian modul.

    `BELUM_DAPAT_DIPERIKSA` **bukan** ragam lulus yang lebih lemah. Ia keadaan
    tersendiri, dan jawaban yang memuat satu saja di antaranya tidak
    tervalidasi.
    """

    LULUS = "lulus"
    GAGAL = "gagal"
    BELUM_DAPAT_DIPERIKSA = "belum_dapat_diperiksa"


class HasilPemeriksaan(BaseModel):
    """Hasil satu pemeriksaan beserta alasannya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kode: KodePemeriksaan
    status: Status
    alasan: str = Field(min_length=1)
    """Selalu terisi, termasuk pada `LULUS`.

    Alasan yang hanya wajib saat gagal membuat `BELUM_DAPAT_DIPERIKSA` tidak
    terbaca sebabnya — dan sebab itulah yang menentukan fitur mana yang
    membukanya. Pada `LULUS` ia menyebut apa yang benar-benar diperiksa,
    sehingga pemeriksaan yang tidak memeriksa apa pun terbaca dari alasannya.
    """
    id_klaim_bermasalah: tuple[str, ...] = ()
    """Klaim yang menyebabkan kegagalan, bila kegagalannya per klaim.

    Kosong pada VS-04, VS-06, dan VS-09 — ketiganya membuang seluruh jawaban,
    sehingga menunjuk klaim tertentu akan menyesatkan ke arah perbaikan
    sebagian.
    """

    @model_validator(mode="after")
    def _klaim_hanya_pada_kegagalan(self) -> HasilPemeriksaan:
        """Pemeriksaan yang lulus tidak menunjuk klaim bermasalah.

        Bila ia menunjuk, salah satu dari dua hal keliru: klaimnya sebenarnya
        bermasalah dan statusnya salah, atau daftarnya sisa dari pemanggilan
        sebelumnya. Keduanya menyesatkan.
        """
        if self.status is Status.LULUS and self.id_klaim_bermasalah:
            raise ValueError(
                f"{self.kode.value} berstatus lulus tetapi menunjuk klaim bermasalah — "
                "salah satu dari keduanya keliru"
            )
        return self

    @property
    def menghalangi(self) -> bool:
        """Apakah hasil ini menghalangi jawaban dinyatakan tervalidasi.

        `GAGAL` **dan** `BELUM_DAPAT_DIPERIKSA` sama-sama menghalangi. Yang
        membedakan keduanya bukan akibatnya melainkan tindak lanjutnya: yang
        gagal menuntut jawabannya diperbaiki, yang belum dapat diperiksa
        menuntut fiturnya dibangun.
        """
        return self.status is not Status.LULUS
