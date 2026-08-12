"""Penarikan butir yang sudah tayang — R-10, FR-I06, PP-04, D-06 Bagian 7.5.

Tiga pemicu, dan **dua di antaranya menarik sedangkan satu tidak**:

| Pemicu | Tindakan |
|---|---|
| Regulasi sumber dicabut **atau diubah** | Ditarik otomatis; kurator menyusun pengganti |
| Kekeliruan isi dilaporkan pengguna | Ditarik dalam 1 hari kerja; dapat tayang ulang |
| Data sumber diperbarui | Ditandai perlu tinjauan, **tetap tayang** |

Perbedaan ketiga itu yang paling mudah hilang. Penarikan yang menyapu ketiga
pemicu lulus setiap uji yang menanyakan "apakah butir ditarik", dan akibatnya
feed kehilangan isi setiap kali sebuah angka pada dokumen sumber diperbarui —
lalu titik kritis T5 pada D-02 menyala tanpa seorang pun mengerti sebabnya.

## `diubah` menarik, sama seperti `dicabut`

D-06 Bagian 7.5 menyebut keduanya pada satu baris. Butir yang bersandar pada
pasal yang sudah berubah tetap mengarahkan kepala sekolah dengan ketentuan
yang tidak lagi berlaku sebagaimana tertulis, dan itu tepat bentuk kekeliruan
yang C-07 larang.

Aturan ini sejajar dengan L3 pada `saring.py` yang juga menolak keduanya, dan
**berbeda** dari D-07 Bagian 4.5 yang mengizinkan regulasi `diubah` dipakai
menjawab dengan penanda. Yang satu mengatur ingesti dan penarikan, yang lain
mengatur penjawaban.

## Ditarik bukan berarti dihapus dari koleksi

D-06 Bagian 7.5 menutup dengan kalimat yang menentukan bentuk modul ini:

> Pengguna yang sudah menyimpan butir yang ditarik tetap dapat melihatnya
> dalam koleksi, disertai penanda bahwa dasar rujukannya telah berubah.
> Menghapus dari koleksi tanpa penjelasan akan merusak kepercayaan yang
> dibangun sepanjang J1 sampai J4.

Karena itu modul ini **tidak menyediakan cara menghapus apa pun**. Ia
menghasilkan putusan tinjauan; yang menindaknya adalah feed, dan yang dibawa
ke koleksi adalah penandanya.

## "Bermakna" diserahkan pemanggil

Pengecualian pada pemicu ketiga — *"kecuali angkanya berubah bermakna"* —
adalah penilaian kurator, bukan perbandingan yang dapat dihitung modul ini.
Ia diserahkan pemanggil sebagai bendera tegas, sama seperti
`id_dokumen_dikenal` pada `saring.py`, dan **hanya pemicu ketiga yang
menerimanya**: bendera yang diterima setiap pemicu akan dipakai untuk
melunakkan penarikan regulasi, dan itu C-07 yang dilewati lewat pintu samping.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from src.ingest.kurasi.putusan import ButirTayang
from src.ingest.kurasi.tetapan import TENGGAT_PENARIKAN_HARI_KERJA
from src.kamus.segmen import StatusKeberlakuan

_PENANDA_KOLEKSI = "Dasar rujukan butir ini telah berubah."
"""Penanda yang menyertai butir tertarik pada koleksi pengguna.

Bahasa Indonesia, ≤ 20 kata, tanpa istilah teknis dan tanpa kode galat —
NFR-19 dan C-13. Yang dibaca kepala sekolah adalah kalimat ini, bukan nama
pemicunya.
"""


class GalatPenarikan(Exception):
    """Peninjauan tidak dapat dijalankan atas keterangan yang diberikan.

    Berupa galat, bukan tindakan ketiga: menariknya menjadi nilai kembalian
    akan membuat pemanggil memperlakukan keterangan yang kurang sebagai
    keputusan "tidak ditarik" — dan tidak ditarik adalah salah satu jawaban
    yang sah, sehingga kekurangannya tidak akan pernah terlihat.
    """


class Pemicu(Enum):
    """Ketiga pemicu D-06 Bagian 7.5."""

    REGULASI_SUMBER_BERUBAH = "regulasi_sumber_berubah"
    KEKELIRUAN_ISI_DILAPORKAN = "kekeliruan_isi_dilaporkan"
    DATA_SUMBER_DIPERBARUI = "data_sumber_diperbarui"


class TindakanPenarikan(Enum):
    """Dua tindakan, dan yang kedua bukan penarikan yang lebih lunak.

    `DITANDAI_PERLU_TINJAUAN` berarti butir **tetap tayang**. Menyamakannya
    dengan penarikan akan mengosongkan feed setiap kali dokumen sumber
    diperbarui.
    """

    DITARIK = "ditarik"
    DITANDAI_PERLU_TINJAUAN = "ditandai_perlu_tinjauan"


@dataclass(frozen=True)
class HasilPenarikan:
    """Putusan tinjauan atas satu butir tayang."""

    pemicu: Pemicu
    tindakan: TindakanPenarikan
    alasan: str
    tenggat_hari_kerja: int | None = None
    """Terisi hanya pada penarikan yang dijadwalkan — D-06 Bagian 7.5.

    Penarikan regulasi berjalan otomatis, dan tenggat padanya akan membaca
    seperti izin menunda sehari.
    """
    dapat_tayang_ulang: bool = False
    """Aduan pengguna ditinjau, lalu ditayangkan ulang **atau** ditolak permanen.

    Penarikan yang selalu permanen membuat setiap aduan menghapus satu butir,
    dan pengguna yang mengadu dua kali kehilangan lebih banyak daripada yang
    diam.
    """
    kurator_menyusun_pengganti: bool = False
    """Penarikan tanpa penggantinya adalah pengurangan isi feed yang permanen."""

    @property
    def penanda_koleksi(self) -> str | None:
        """Penanda bagi koleksi pengguna — terisi bila butir ditarik."""
        if self.tindakan is not TindakanPenarikan.DITARIK:
            return None
        return _PENANDA_KOLEKSI

    @property
    def tetap_terlihat_pada_koleksi(self) -> bool:
        """**Selalu benar**, dan itu memang pernyataannya.

        Sifat ini tidak bercabang karena D-06 Bagian 7.5 tidak memberinya
        cabang: tidak satu pun dari ketiga pemicu menghapus butir dari koleksi
        orang yang sudah menyimpannya. Ia ditulis agar fitur 011 yang menyusun
        koleksi memiliki sesuatu yang dapat dibaca dan diuji, alih-alih sebuah
        kalimat pada dokumen yang mudah terlewat.
        """
        return True


def tinjau(
    tayang: ButirTayang,
    *,
    pemicu: Pemicu,
    status_terkini: StatusKeberlakuan | None = None,
    angka_berubah_bermakna: bool = False,
) -> HasilPenarikan:
    """Tinjau satu butir tayang terhadap sebuah pemicu — R-10.

    Pemicu dipetakan berkunci, bukan lewat rangkaian `if` yang berakhir pada
    `else`. Pemicu keempat yang ditambahkan D-06 kelak berhenti di sini pada
    `KeyError`, bukan mendarat pada cabang "tidak ditarik" yang kebetulan aman.

    Tidak menulis apa pun dan tidak menghapus apa pun — lihat uraian modul.
    """
    return _PENINJAU[pemicu](tayang, status_terkini, angka_berubah_bermakna)


def _tinjau_regulasi(
    tayang: ButirTayang,
    status_terkini: StatusKeberlakuan | None,
    angka_berubah_bermakna: bool,
) -> HasilPenarikan:
    _tolak_bendera_angka(Pemicu.REGULASI_SUMBER_BERUBAH, angka_berubah_bermakna)
    if status_terkini is None:
        raise GalatPenarikan(
            "pemicu regulasi wajib membawa status terkini — tanpa itu 'regulasi "
            "berubah' hanya dugaan, dan dugaan yang menarik butir mengosongkan feed"
        )
    if status_terkini is StatusKeberlakuan.BERLAKU:
        raise GalatPenarikan(
            "regulasi sumber masih berstatus berlaku — tidak ada yang memicu "
            "penarikan (D-06 Bagian 7.5)"
        )
    return HasilPenarikan(
        pemicu=Pemicu.REGULASI_SUMBER_BERUBAH,
        tindakan=TindakanPenarikan.DITARIK,
        alasan=(
            f"regulasi sumber {tayang.butir.id_dokumen_sumber} berstatus "
            f"{status_terkini.value} — butir ditarik otomatis (C-07, KL-07)"
        ),
        kurator_menyusun_pengganti=True,
    )


def _tinjau_kekeliruan(
    tayang: ButirTayang,
    status_terkini: StatusKeberlakuan | None,
    angka_berubah_bermakna: bool,
) -> HasilPenarikan:
    _tolak_bendera_angka(Pemicu.KEKELIRUAN_ISI_DILAPORKAN, angka_berubah_bermakna)
    return HasilPenarikan(
        pemicu=Pemicu.KEKELIRUAN_ISI_DILAPORKAN,
        tindakan=TindakanPenarikan.DITARIK,
        alasan=(
            f"kekeliruan isi butir {tayang.butir.id_butir} dilaporkan pengguna — "
            "ditinjau, lalu ditayangkan ulang atau ditolak permanen"
        ),
        tenggat_hari_kerja=TENGGAT_PENARIKAN_HARI_KERJA,
        dapat_tayang_ulang=True,
    )


def _tinjau_pembaruan_data(
    tayang: ButirTayang,
    status_terkini: StatusKeberlakuan | None,
    angka_berubah_bermakna: bool,
) -> HasilPenarikan:
    if angka_berubah_bermakna:
        return HasilPenarikan(
            pemicu=Pemicu.DATA_SUMBER_DIPERBARUI,
            tindakan=TindakanPenarikan.DITARIK,
            alasan=(
                f"angka pada dokumen sumber butir {tayang.butir.id_butir} berubah "
                "bermakna menurut kurator — butir ditarik"
            ),
            kurator_menyusun_pengganti=True,
        )
    return HasilPenarikan(
        pemicu=Pemicu.DATA_SUMBER_DIPERBARUI,
        tindakan=TindakanPenarikan.DITANDAI_PERLU_TINJAUAN,
        alasan=(
            f"data sumber butir {tayang.butir.id_butir} diperbarui — butir tetap "
            "tayang sampai ditinjau (D-06 Bagian 7.5)"
        ),
    )


def _tolak_bendera_angka(pemicu: Pemicu, angka_berubah_bermakna: bool) -> None:
    """Bendera "angka berubah bermakna" hanya milik pemicu ketiga.

    Bendera yang diterima setiap pemicu akan dipakai untuk melunakkan penarikan
    regulasi, dan itu C-07 yang dilewati lewat pintu samping.
    """
    if angka_berubah_bermakna:
        raise GalatPenarikan(
            f"pemicu {pemicu.value} tidak mengenal keterangan perubahan angka — "
            "keterangan itu milik pemicu pembaruan data sumber (D-06 Bagian 7.5)"
        )


_PENINJAU: dict[
    Pemicu,
    Callable[[ButirTayang, StatusKeberlakuan | None, bool], HasilPenarikan],
] = {
    Pemicu.REGULASI_SUMBER_BERUBAH: _tinjau_regulasi,
    Pemicu.KEKELIRUAN_ISI_DILAPORKAN: _tinjau_kekeliruan,
    Pemicu.DATA_SUMBER_DIPERBARUI: _tinjau_pembaruan_data,
}
