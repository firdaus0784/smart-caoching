"""Enum sifat segmen — `docs/D14.md` Bagian 5, `docs/D13.md` Bagian 6.

Ketiganya dimiliki dokumen, bukan modul. AG-04 melarang agen mengubah daftar
nilai enum, dan berkas ini tempat larangan itu paling mudah dilanggar tanpa
disadari.

## Mengapa berkas ini ada

`IndeksTujuan` sempat didefinisikan dua kali. Yang membuatnya lebih dari
kerapian: **enum itu tempat C-02 terbaca.** Dua definisi berarti perubahan
D-14 kelak dapat memperbarui satu dan melewatkan yang lain, dan tidak satu uji
pun gagal karenanya.

Sebab sesungguhnya bukan kecerobohan tunggal melainkan bahwa nilai-nilai ini
tidak punya rumah: ia bukan milik pembungkus model maupun milik lapisan
penyimpanan, sehingga lapisan berikutnya yang membutuhkannya menulis ulang
alih-alih mengimpor ke atas.
"""

from __future__ import annotations

from enum import Enum


class IndeksTujuan(Enum):
    """Indeks tempat sebuah segmen berada — `docs/D14.md` Bagian 5.

    `UTAMA` boleh masuk konteks LLM; `METADATA` tidak pernah, dan hanya muncul
    sebagai `bacaan_lanjutan` pada tanggapan (D-07 Bagian 3.1, FR-D06).
    """

    UTAMA = "utama"
    METADATA = "metadata"


class Peringkat(Enum):
    """Tingkat kepercayaan asal segmen — `docs/D13.md` Bagian 6, FR-B09.

    T3 dan T4 tidak boleh menjadi dasar **tunggal** sebuah klaim (C-19,
    FR-F15). Kata "tunggal" menentukan: D-13 Bagian 6 menyatakan T3 *"boleh
    menopang, tetapi klaim memerlukan segmen T1 atau T2"*, sehingga klaim yang
    ditopang T1 dan T3 sekaligus adalah bentuk yang **benar**, bukan
    pengecualian.
    """

    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"

    @property
    def lemah(self) -> bool:
        """Apakah peringkat ini tidak boleh menjadi dasar tunggal klaim."""
        return self in PERINGKAT_LEMAH


PERINGKAT_LEMAH: frozenset[Peringkat] = frozenset({Peringkat.T3, Peringkat.T4})
"""Peringkat yang tidak boleh menjadi dasar tunggal klaim — D-13 Bagian 6.

Dinamai di sini, bukan disusun ulang di validator. Himpunan yang disusun di
tempat pemakainya akan berbeda ketika D-13 menambah peringkat kelima, dan yang
berbeda adalah yang tidak diperbarui.
"""


class StatusKeberlakuan(Enum):
    """Status keberlakuan sebuah regulasi — `docs/D14.md` Bagian 4.1, KL-07.

    Tiga nilai, dan ketiadaan keterangan **bukan** nilai keempat. Nilai bernama
    "tidak diketahui" akan mengundang seseorang memperlakukannya sebagai kasus
    tersendiri yang lebih longgar — bentuk yang sama yang `StatusLisensi` tolak
    pada fitur 006.

    `DICABUT` diperlakukan paling tegas (D-07 Bagian 4.5): menjawab berdasarkan
    aturan yang sudah dicabut adalah bentuk kekeliruan yang paling merugikan,
    **karena jawabannya terdengar berdasar**.
    """

    BERLAKU = "berlaku"
    DIUBAH = "diubah"
    DICABUT = "dicabut"
