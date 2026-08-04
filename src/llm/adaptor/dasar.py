"""Antarmuka adaptor penyedia model — R-08, ADR-11, ADR-12, C-17, C-18.

ADR-12 menetapkan pembungkus dibangun terhadap antarmuka abstrak dengan satu
adaptor tiruan; penyedia konkret belum dipilih (BT-14). Antarmuka ini sengaja
dijaga kecil — satu metode, satu bentuk permintaan, satu bentuk tanggapan —
agar penyesuaiannya ketika penyedia nyata dipasang tetap murah (RP-04).

Dua sifat bentuknya yang menjadi kendali, bukan sekadar rancangan:

**Tanpa parameter alat (C-17).** Antarmuka tidak menyediakan cara menyatakan
pemanggilan alat, pendaftaran fungsi, maupun keluaran yang dapat dieksekusi.
Kemampuan yang tidak dapat dinyatakan tidak dapat dipakai — dan itu sebabnya
`docs/D13.md` KD-09 menyebut ketiadaan kemampuan bertindak sebagai kendali
paling berdaya dalam dokumen itu.

**Posisi instruksi dan posisi data terpisah secara struktural (C-18).**
`Permintaan` memiliki dua bidang bertipe berbeda, bukan satu bidang teks yang
diisi hasil rangkaian. Tidak ada bidang yang dapat menampung keduanya, sehingga
konten terambil tidak punya jalan menuju posisi instruksi.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from src.llm.tipe import Data, Instruksi, Konfigurasi, Tanggapan


class Permintaan(BaseModel, frozen=True, extra="forbid"):
    """Permintaan ke penyedia, berbentuk objek — bukan untai.

    Bentuk objek inilah yang membuat C-18 dapat diuji mesin: "posisi
    instruksi" punya wujud yang dapat ditegaskan, sehingga uji dapat
    menyatakan untai penanda dari `data` tidak muncul pada `instruksi`. Bila
    permintaan berupa satu untai, pemeriksaan itu berubah menjadi pemeriksaan
    mata, dan UK-10 yang berambang nol kehilangan artinya.
    """

    instruksi: Instruksi
    data: tuple[Data, ...]
    konfigurasi: Konfigurasi


class AdaptorDasar(ABC):
    """Kontrak penyedia model. Satu metode, tanpa kemampuan bertindak."""

    @abstractmethod
    def kirim(self, permintaan: Permintaan) -> Tanggapan:
        """Kirim permintaan, kembalikan tanggapan.

        Pelaksana wajib memetakan `permintaan.instruksi` ke posisi instruksi
        penyedia dan `permintaan.data` ke posisi konten, **tanpa merangkai
        keduanya menjadi satu untai**. Perangkaian membatalkan C-18 pada titik
        terakhir, setelah seluruh pemisahan tipe di atasnya.
        """
