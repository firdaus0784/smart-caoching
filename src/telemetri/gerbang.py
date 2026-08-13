"""Gerbang perekaman telemetri — R-04, R-05, R-07, **C-04**, FR-J05.

C-04 berbunyi: *"Telemetri tidak merekam bagi pengguna tanpa persetujuan
aktif. Pencabutan menghentikan perekaman seketika."*

## C-04 adalah bentuk, bukan pemeriksaan

Pemeriksaan yang menegakkannya berbunyi "sebelum merekam, periksa
persetujuan" — dan pemeriksaan semacam itu ada pada **setiap** tempat
perekaman. Satu tempat yang lupa memuatnya tidak menghasilkan galat apa pun;
ia menghasilkan data yang lebih lengkap, dan data yang lebih lengkap tidak
pernah terasa seperti kekeliruan sampai audit etik.

Karena itu `Peristiwa` **hanya dibentuk di sini**. Fitur yang merekam
kemudian tidak memiliki cara merekam tanpa melewati gerbang — bukan dilarang,
melainkan tidak bisa. Bentuk keempat sesudah `Instruksi` (ADR-13),
`JawabanTervalidasi` (008), dan `ButirTayang` (010); yang menjaga batasnya
pemeriksa C-04.

## Keadaan persetujuan adalah argumen, dan itu yang membuat "seketika" bekerja

`rekam()` menerima `KeadaanPersetujuan` **setiap kali dipanggil**, dan modul
ini tidak memiliki tempat menyimpannya.

Salinan yang diambil saat sesi dibuka akan tetap bernilai `DIBERIKAN` sesudah
pengguna mencabut di tengah sesi — dan "pencabutan menghentikan perekaman
seketika" berubah menjadi "pada sesi berikutnya" **tanpa seorang pun mengubah
satu baris logika**. Itu bentuk pelanggaran yang paling sunyi, dan satu-satunya
yang menutupnya adalah tidak menyediakan tempat menyimpannya.

## Galat bukan bentuk yang dipakai

Pengguna yang tidak menyetujui **bukan keadaan galat**. Ia keadaan yang sah dan
diharapkan — FR-A05 menjamin menolak tidak mengurangi akses fitur inti.

Gerbang yang melempar galat akan mengundang pemanggil membungkusnya dengan
`try`, dan pada akhirnya seseorang menuliskan `except: pass` di sekeliling
seluruh pemanggilan telemetri — lalu kekeliruan lain ikut tertelan. Bentuk
kembalian dua nilai mengikuti `terapkan()` (010) dan `validasi()` (008).

## Tiga hasil, bukan dua

`DITOLAK_PROPERTI` sengaja terpisah dari `DILEWATI_TANPA_PERSETUJUAN`.
Menyamakannya membuat pelanggaran KM-03 terhitung sebagai pengguna yang
menolak — lalu laporan partisipasi keliru, **dan kekeliruan KM-03 tidak pernah
terlihat** sebab ia tersembunyi di balik angka yang tampak wajar.

## Urutan pemeriksaan dinyatakan

Persetujuan diperiksa **lebih dulu**. Pengguna yang tidak menyetujui tidak
boleh membuat isi peristiwanya diperiksa sama sekali: pemeriksaan itu sendiri
menyentuh muatan yang seharusnya tidak diproses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from src.pengguna.persetujuan import KeadaanPersetujuan
from src.telemetri.peristiwa import JenisPeristiwa, Peristiwa


class HasilPerekaman(Enum):
    """Tiga hasil, dan yang ketiga bukan ragam yang kedua — lihat uraian modul."""

    DIREKAM = "direkam"
    DILEWATI_TANPA_PERSETUJUAN = "dilewati_tanpa_persetujuan"
    DITOLAK_PROPERTI = "ditolak_properti"


def rekam(
    *,
    keadaan: KeadaanPersetujuan,
    pseudonim: str,
    jenis: JenisPeristiwa,
    waktu: datetime,
    properti: dict[str, Any],
    versi_aplikasi: str,
    versi_model: str,
) -> tuple[HasilPerekaman, Peristiwa | None]:
    """Susun satu peristiwa bila persetujuan mengizinkan — C-04.

    `keadaan` **tanpa nilai bawaan**. Parameter berbawaan `DIBERIKAN` akan
    membatalkan pasal ini pada setiap pemanggilan yang lupa mengisinya, dan
    tidak satu uji perilaku pun gagal karenanya.

    Mengembalikan hasilnya selalu, dan peristiwanya **hanya bila boleh**.
    Pemanggil yang hanya membaca nilai kedua tidak memiliki apa pun untuk
    disimpan ketika persetujuan tidak mengizinkan.
    """
    if not keadaan.boleh_merekam:
        return HasilPerekaman.DILEWATI_TANPA_PERSETUJUAN, None

    try:
        peristiwa = Peristiwa(
            pseudonim=pseudonim,
            jenis=jenis,
            waktu=waktu,
            properti=properti,
            versi_aplikasi=versi_aplikasi,
            versi_model=versi_model,
        )
    except ValueError:
        # Galatnya sengaja **tidak diteruskan maupun dicatat isinya**: ia
        # membawa keterangan tentang muatan yang baru saja ditolak, dan
        # meneruskannya memindahkan kebocoran dari basis data ke penanganan
        # galat pemanggil. Yang perlu diketahui pemanggil adalah bahwa
        # propertinya ditolak, bukan apa isinya.
        return HasilPerekaman.DITOLAK_PROPERTI, None

    return HasilPerekaman.DIREKAM, peristiwa


class Telemetri:
    """Kumpulan peristiwa — tambah saja.

    Sengaja tanpa metode menyunting maupun menghapus (R-07). Penghapusan
    mengikuti KM-02 dan permintaan penarikan data, yang jalurnya berbeda dan
    menuntut keputusan manusia.

    **Tidak menyimpan keadaan persetujuan.** Lihat uraian modul.
    """

    def __init__(self) -> None:
        self._peristiwa: list[Peristiwa] = []

    @property
    def peristiwa(self) -> tuple[Peristiwa, ...]:
        """Salinan beku — daftar yang dikembalikan apa adanya dapat ditambahi
        maupun dikosongkan pemanggil."""
        return tuple(self._peristiwa)

    def catat(
        self,
        *,
        keadaan: KeadaanPersetujuan,
        pseudonim: str,
        jenis: JenisPeristiwa,
        waktu: datetime,
        properti: dict[str, Any],
        versi_aplikasi: str,
        versi_model: str,
    ) -> HasilPerekaman:
        """Rekam satu peristiwa bila diizinkan; laporkan hasilnya selalu.

        Pencabutan berlaku pada panggilan **ini**, bukan pada sesi berikutnya:
        `keadaan` diteruskan tiap kali dan tidak pernah disimpan.
        """
        hasil, peristiwa = rekam(
            keadaan=keadaan,
            pseudonim=pseudonim,
            jenis=jenis,
            waktu=waktu,
            properti=properti,
            versi_aplikasi=versi_aplikasi,
            versi_model=versi_model,
        )
        if peristiwa is not None:
            self._peristiwa.append(peristiwa)
        return hasil
