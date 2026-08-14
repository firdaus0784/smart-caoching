"""Persetujuan penelitian — R-05, R-06, R-08, FR-A05, C-04, D-04 Bagian 7.1.

FR-A05: *"Pengguna memberikan persetujuan penelitian (informed consent)
elektronik sebelum data perilakunya direkam, dengan opsi menolak tanpa
kehilangan akses fitur inti."*

**Modul ini adalah prasyarat C-04.** Pasal itu berbunyi *"telemetri tidak
merekam bagi pengguna tanpa persetujuan aktif; pencabutan menghentikan
perekaman seketika"*, dan `boleh_merekam` di sini adalah satu-satunya sifat
yang fitur 012 kelak tanyakan.

## Landasan yang dipinjam, dan batas peminjamannya

WMA Declaration of Helsinki (D-11 Bagian 3.6) merumuskan tiga unsur
persetujuan — **keterangan, pemahaman, kesukarelaan** — dan mengakui
dokumentasi **elektronik** sebagai bentuk yang sah. Dari ketiganya, modul ini
dapat menegakkan satu: keterangan, lewat `versi_naskah` yang wajib. Pemahaman
dan kesukarelaan ditegakkan layar dan prosedur, bukan tipe.

Peminjamannya sebagian dan dinyatakan tegas pada D-11: Helsinki menetapkan
kedudukan dirinya pada penelitian medis, dan penelitian ini bukan penelitian
medis. Yang dipinjam rumusan unsurnya, bukan rezim etiknya.

## Empat keadaan, dan dua pembedaan yang mudah hilang

Kosakatanya milik D-14 Bagian 5.1, yang sudah menetapkannya bagi persetujuan
pemilik dokumen beserta alasannya: *"`dicabut` menghentikan pemakaian
seketika; persetujuan yang tidak dapat ditarik bukan persetujuan."* Kosakata
yang sama dipakai di sini sebab ia menamai hal yang sama pada subjek berbeda.

**`BELUM_DIMINTA` bukan `DITOLAK`.** Keduanya menghentikan perekaman, dan
justru karena itu godaan menyatukannya besar. Yang pertama pekerjaan yang belum
dilakukan; yang kedua keputusan partisipan yang wajib dihormati. Laporan
partisipasi yang tidak dapat membedakan keduanya tidak dapat menjawab apakah
pengambilan data sudah lengkap.

**`DITOLAK` bukan `DICABUT`.** Helsinki menyebut hak menolak dan hak mencabut
kapan saja sebagai dua hal. Pencabutan yang dicatat sebagai penolakan membuat
data yang sudah terekam sebelum pencabutan kehilangan penjelasannya — dan
penjelasan itu justru yang dibutuhkan ketika data itu harus ditarik (KM-02).

## Keadaan dihitung, bukan disimpan

D-04 Bagian 7.1 menyimpan `disetujui` dan `dicabut_pada` sebagai dua bidang.
Bidangnya **tetap seperti D-04** — model data miliknya, bukan milik modul ini
— sedangkan keadaannya berupa sifat terhitung, dan gabungan yang mustahil
ditolak saat pembentukan:

| `disetujui` | `dicabut_pada` | Keadaan |
|---|---|---|
| — (tanpa catatan) | — | `BELUM_DIMINTA` |
| salah | kosong | `DITOLAK` |
| benar | kosong | `DIBERIKAN` |
| benar | terisi | `DICABUT` |
| **salah** | **terisi** | **ditolak saat pembentukan** |

Baris terakhir tidak berarti apa pun — tidak ada yang dicabut. Yang tidak
berarti apa pun akan ditafsirkan berbeda oleh dua pembaca, dan salah satu
tafsiran itu mengizinkan perekaman.

## Yang **tidak** ada di sini, dan itu disengaja

Tidak ada bidang, sifat, maupun fungsi yang memetakan keadaan persetujuan ke
tingkat akses. FR-A05 menjamin *"opsi menolak tanpa kehilangan akses fitur
inti"*, dan cara paling kokoh menjamin sebuah larangan adalah tidak
menyediakan alatnya. Ketiadaan itu diuji tersendiri (tugas B-2).
"""

from __future__ import annotations

from enum import Enum

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class JenisPersetujuan(Enum):
    """Jenis persetujuan — `persetujuan.jenis` pada D-04 Bagian 7.1.

    Satu nilai pada siklus 2026. Enum sejak awal, bukan untai bebas: persetujuan
    perekaman perilaku dan persetujuan pemakaian dokumen adalah dua hal, dan
    yang kedua sudah berdiri sendiri pada `dokumen_sumber` (fitur 002).
    """

    PENELITIAN = "penelitian"


class KeadaanPersetujuan(Enum):
    """Empat keadaan — D-14 Bagian 5.1. Lihat uraian modul."""

    BELUM_DIMINTA = "belum_diminta"
    DIBERIKAN = "diberikan"
    DITOLAK = "ditolak"
    DICABUT = "dicabut"

    @property
    def boleh_merekam(self) -> bool:
        """**C-04.** Hanya `DIBERIKAN`.

        Sifat terhitung, bukan bidang. Bidang dapat diisi `True` oleh pemanggil
        yang lelah, dan yang dilewati bersamanya adalah pasal itu sendiri.
        """
        return self is KeadaanPersetujuan.DIBERIKAN

    @classmethod
    def dari(cls, catatan: CatatanPersetujuan | None) -> KeadaanPersetujuan:
        """Keadaan sebuah catatan — `None` berarti belum diminta.

        Fungsi ini ada justru agar pemanggil tidak menuliskan `if catatan is
        None` sendiri, dan tidak menyimpulkan `DITOLAK` dari ketiadaan catatan.
        Ketiadaan adalah keadaan, bukan kekosongan yang perlu ditebak.
        """
        if catatan is None:
            return cls.BELUM_DIMINTA
        if not catatan.disetujui:
            return cls.DITOLAK
        if catatan.dicabut_pada is not None:
            return cls.DICABUT
        return cls.DIBERIKAN


class CatatanPersetujuan(BaseModel):
    """Satu catatan persetujuan — enam bidang D-04 Bagian 7.1.

    Beku: catatan yang dapat disunting tidak membuktikan apa pun tentang apa
    yang partisipan setujui.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_pengguna: str = Field(min_length=1)
    jenis: JenisPersetujuan
    versi_naskah: str = Field(min_length=1)
    """Naskah yang partisipan baca — R-08.

    Helsinki menempatkan **keterangan** sebagai unsur pertama persetujuan.
    Tanpa versi naskah, tidak ada cara mengetahui keterangan apa yang dibaca —
    dan naskah ET-02 akan berubah selama penelitian berjalan.
    """
    disetujui: bool
    tanggal: AwareDatetime
    dicabut_pada: AwareDatetime | None = None
    """Bila terisi, perekaman berhenti seketika — D-14 Bagian 5.1, FR-J05."""

    @field_validator("versi_naskah")
    @classmethod
    def _naskah_dapat_ditunjuk(cls, nilai: str) -> str:
        """Spasi bukan penanda naskah. Panjang minimum saja meloloskannya, dan
        catatan yang menunjuk naskah bernama spasi tidak menunjuk apa pun."""
        if not nilai.strip():
            raise ValueError(
                "persetujuan wajib menyebut versi naskah yang dibaca partisipan (R-08)"
            )
        return nilai

    @model_validator(mode="after")
    def _gabungan_yang_mungkin(self) -> CatatanPersetujuan:
        """Penolakan tidak dapat dicabut, dan pencabutan tidak mendahului
        persetujuannya — lihat tabel pada uraian modul."""
        if self.dicabut_pada is None:
            return self
        if not self.disetujui:
            raise ValueError("penolakan tidak membawa waktu pencabutan — tidak ada yang dicabut")
        if self.dicabut_pada <= self.tanggal:
            raise ValueError(
                "pencabutan tidak dapat mendahului atau menyamai waktu persetujuan — "
                "perekaman berhenti sebelum ia diizinkan"
            )
        return self

    @property
    def keadaan(self) -> KeadaanPersetujuan:
        return KeadaanPersetujuan.dari(self)

    @property
    def boleh_merekam(self) -> bool:
        """**C-04**, dibaca dari keadaannya — satu jalur, bukan dua."""
        return self.keadaan.boleh_merekam
