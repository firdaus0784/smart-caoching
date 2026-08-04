"""Pembungkus tunggal seluruh pemanggilan model — R-05, ADR-11, C-08, C-09.

ADR-11 dan C-08 menetapkan seluruh pemanggilan model melewati satu lapisan
yang mencatat versi model, konfigurasi, waktu, dan biaya. Pembungkus ini
adalah lapisan itu; aturan AST pada B-2 yang menjaga agar tidak ada jalur lain.

**Dua pencatatan yang berbeda dan tidak boleh dicampur.**

C-08 menuntut setiap pemanggilan menghasilkan catatan pemanggilan — nama dan
versi model, konfigurasi, waktu mulai dan selesai, biaya. C-09 menuntut
keluaran *eksperimen* mencatat lima bidang versi ke `logbook/`.

Menulis L1 pada setiap pemanggilan akan membanjiri rekaman penelitian dengan
ribuan baris saat pilot, dan `docs/D10.md` Bagian 3 menegaskan L1 adalah
riwayat percobaan — satu baris per percobaan, bukan per permintaan. Karena itu
`panggil` menulis L1 hanya bila diberi `id_percobaan`, dan menuntut `tujuan`
bersamanya.

Pembungkus tidak menyediakan parameter alat maupun jalur tulis ke basis data.
C-17 dan NFR-21 diwujudkan sebagai ketiadaan, bukan sebagai pemeriksaan.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.llm.adaptor.dasar import AdaptorDasar, Permintaan
from src.llm.galat import GalatLayananModel
from src.llm.tipe import Data, Instruksi, Konfigurasi, Tanggapan
from src.logbook.penulis import tambah_percobaan
from src.logbook.versi import Versi


@dataclass(frozen=True)
class CatatanPemanggilan:
    """Jejak satu pemanggilan — wujud C-08.

    Disimpan dalam ingatan pada fitur 001. Penyimpanannya ke basis data
    menyusul bersama tabel `pesan` pada fitur 009; bentuk bidangnya sudah
    disiapkan agar pemindahan itu tidak mengubah pemanggil.
    """

    nama_model: str
    versi_model: str
    suhu: float
    batas_token: int
    waktu_mulai: datetime
    waktu_selesai: datetime
    biaya: float
    id_jejak: str
    jumlah_segmen: int


class Pembungkus:
    """Satu-satunya pintu menuju model."""

    def __init__(self, adaptor: AdaptorDasar, akar_logbook: Path, versi: Versi) -> None:
        self._adaptor = adaptor
        self._akar_logbook = akar_logbook
        self._versi = versi
        self.riwayat: list[CatatanPemanggilan] = []

    def panggil(
        self,
        *,
        instruksi: Instruksi,
        data: Sequence[Data],
        konfigurasi: Konfigurasi,
        id_percobaan: str | None = None,
        tujuan: str | None = None,
    ) -> Tanggapan:
        """Kirim permintaan dan catat jejaknya.

        `instruksi` dan `data` adalah parameter terpisah bertipe berbeda; tidak
        ada parameter yang menerima keduanya (C-18, R-06).
        """
        if id_percobaan and not tujuan:
            raise ValueError(
                "percobaan tanpa tujuan tidak dapat dicatat — docs/D10.md "
                "Bagian 3 meminta satu kalimat: apa yang ingin diketahui"
            )

        permintaan = Permintaan(instruksi=instruksi, data=tuple(data), konfigurasi=konfigurasi)
        try:
            tanggapan = self._adaptor.kirim(permintaan)
        # Seluruh kegagalan penyedia diseragamkan menjadi satu bentuk yang
        # aman ditampilkan (R-09). Sebab aslinya tetap tersimpan pada galat
        # dan hanya menuju log operasional.
        except Exception as sebab:
            raise GalatLayananModel(sebab) from sebab

        self.riwayat.append(
            CatatanPemanggilan(
                nama_model=konfigurasi.nama_model,
                versi_model=tanggapan.versi_model,
                suhu=konfigurasi.suhu,
                batas_token=konfigurasi.batas_token,
                waktu_mulai=tanggapan.waktu_mulai,
                waktu_selesai=tanggapan.waktu_selesai,
                biaya=tanggapan.biaya,
                id_jejak=tanggapan.id_jejak,
                jumlah_segmen=len(permintaan.data),
            )
        )

        if id_percobaan and tujuan:
            # Versi model diambil dari tanggapan, bukan dari tetapan pembungkus:
            # yang dicatat wajib versi yang benar-benar dipakai.
            tambah_percobaan(
                self._akar_logbook,
                id_percobaan=id_percobaan,
                tujuan=tujuan,
                versi=self._versi.model_copy(update={"versi_model": tanggapan.versi_model}),
                hasil={
                    "id_jejak": tanggapan.id_jejak,
                    "biaya": tanggapan.biaya,
                    "jumlah_segmen": len(permintaan.data),
                },
            )

        return tanggapan
