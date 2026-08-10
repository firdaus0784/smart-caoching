"""Lemari himpunan uji — R-06, PU-01, D-08 Bagian 4.2.

PU-01 berbunyi: **data uji tidak pernah menyentuh proses pelatihan atau
penyetelan.** D-08 menambahkan bahwa himpunan uji "dibuka satu kali" saat
evaluasi akhir.

**Pelanggarannya tidak pernah disengaja, dan itu yang membuat modul ini ada.**
Ia terjadi ketika seseorang sekadar melihat hasil uji untuk memutuskan
konfigurasi berikutnya — satu kali, untuk memastikan arahnya benar. Sesudah
itu angka yang masuk naskah bukan lagi hasil pada data tersembunyi, sebab
konfigurasi yang menghasilkannya dipilih dengan melihat data itu. Dan tidak
ada satu pun jejak yang menunjukkannya: tidak ada galat, tidak ada angka yang
janggal, tidak ada berkas yang berubah.

## Mencatat, bukan melarang

KB-028 memutuskan pembukaan tetap diizinkan (pilihan C). Alasannya bukan
kelonggaran: penjagaan yang menghalangi pekerjaan sah — mengulang evaluasi
karena galat perkakas — akan dilucuti seseorang, dan **cara melucutinya
adalah membuat pembagian baru**, yang justru menghapus jejaknya. Yang tersisa
sesudah itu bukan penjagaan mana pun.

Yang dituntut karena itu: setiap pembukaan tercatat beserta alasannya, dan
hitungannya ikut pada catatan percobaan (fitur ini C-1) yang menjadi bahan
naskah. Angka yang dilaporkan bersama "himpunan uji dibuka empat kali" adalah
angka yang pembacanya dapat nilai sendiri.

## Hanya himpunan uji

`latih` dan `validasi` dibaca lewat atribut biasa. Menjaga ketiganya akan
membuat pencatatan menjadi kebisingan — himpunan latih dibaca pada setiap
epoch — dan pencatatan yang bising adalah pencatatan yang tidak ada yang
membaca.

## Batas yang diakui

Hitungan disimpan **dalam ingatan proses**, bukan pada berkas. Hitungan yang
melintasi sesi menuntut pembacaan kembali catatan L1, dan itu pekerjaan
penyusun laporan — bukan modul ini. Yang dijamin di sini: sepanjang satu
percobaan, tidak ada pembukaan yang luput dari catatannya.

Pembacaan langsung `pembagian.uji` melewati modul ini tanpa satu galat pun.
Yang menghalanginya bukan bahasa melainkan pemeriksa pada
`tests/nlp/test_lemari_uji.py` — bentuk yang sama dengan pemeriksa impor
tunggal `pytesseract` fitur 015.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.nlp.pelatihan.pembagian import PembagianData

PANJANG_ALASAN_MINIMUM = 8
"""Ambang rendah dengan sengaja.

Ia menghalangi kelalaian — "ok", "cek" — bukan orang yang memang hendak
menyamarkan maksudnya. Yang kedua tidak dapat dihalangi kode mana pun, dan
berpura-pura sebaliknya menghasilkan rasa aman yang keliru.
"""


class GalatLemariUji(Exception):
    """Pembukaan himpunan uji tidak dapat dicatat sebagaimana mestinya."""


@dataclass(frozen=True)
class Pembukaan:
    """Satu pembukaan himpunan uji, beserta alasan dan waktunya.

    Beku: riwayat yang dapat disunting adalah riwayat yang akan disunting
    ketika hitungannya memalukan.
    """

    alasan: str
    waktu: datetime


@dataclass
class LemariUji:
    """Pemegang satu pembagian data, dan **satu-satunya jalan sah** ke
    himpunan ujinya.

    Sengaja tidak beku: hitungan pembukaan berubah, dan itu justru gunanya.
    Yang beku adalah tiap `Pembukaan` di dalamnya.
    """

    pembagian: PembagianData
    _riwayat: list[Pembukaan] = field(default_factory=list, repr=False)

    @property
    def latih(self) -> frozenset[str]:
        """Dibaca bebas — lihat uraian modul."""
        return self.pembagian.latih

    @property
    def validasi(self) -> frozenset[str]:
        """Dibaca bebas. Ia memang dipakai memilih konfigurasi (D-08)."""
        return self.pembagian.validasi

    @property
    def jumlah_pembukaan(self) -> int:
        return len(self._riwayat)

    @property
    def riwayat(self) -> tuple[Pembukaan, ...]:
        """Salinan beku. Daftar yang dikembalikan apa adanya dapat ditambah
        maupun dikosongkan pemanggil, dan riwayat yang dapat dikosongkan bukan
        riwayat."""
        return tuple(self._riwayat)

    def buka(self, alasan: str) -> frozenset[str]:
        """Buka himpunan uji, dan **catat pembukaannya** — R-06.

        Alasannya wajib dan diperiksa panjangnya. Pembukaan tanpa alasan
        menjadi deret angka tanpa arti pada laporan, dan deret angka tanpa arti
        tidak membedakan evaluasi akhir dari mengintip.

        Tidak pernah menolak selain karena alasan yang tidak memadai. Lihat
        uraian modul: yang menolak akan dilucuti, dan cara melucutinya
        menghapus jejaknya.
        """
        bersih = alasan.strip()
        if len(bersih) < PANJANG_ALASAN_MINIMUM:
            raise GalatLemariUji(
                f"alasan pembukaan himpunan uji terlalu pendek ({len(bersih)} huruf, "
                f"minimum {PANJANG_ALASAN_MINIMUM}) — yang menilai pembukaan ini "
                "adalah pembaca laporannya kelak, dan ia hanya punya alasan yang "
                "tertulis (PU-01, D-08 Bagian 4.2)"
            )
        self._riwayat.append(Pembukaan(alasan=bersih, waktu=datetime.now(UTC)))
        return self.pembagian.uji
