"""Pembangun muatan penyedia — R-07, C-18, C-02, `docs/D13.md` KD-07.

Inilah titik tempat C-18 benar-benar ditegakkan. Seluruh pemisahan tipe di
atasnya — `Instruksi` terpisah dari `Data` (D-1), konstruksi terkunci satu
modul (D-2), permintaan berbentuk objek (D-3) — akan batal di sini bila
pembangun muatan merangkai keduanya menjadi satu untai sebelum dikirim.

`docs/D13.md` Bagian 1 memaparkan mengapa itu penting. Segmen yang disusupi
teks menyerupai instruksi akan diikuti model, lalu validator sitasi
**mengesahkan** jawabannya — karena klaimnya memang didukung segmen tersebut.
Validator memeriksa provenans, bukan keabsahan (PR-03a). Yang memutus alur itu
adalah pemisahan di sini, bukan validator sesudahnya.

Dua aturan yang dijaga:

- `posisi_instruksi` diisi **persis** `Instruksi.teks`, tanpa rangkaian,
  sisipan, maupun awalan. Uji menegaskan panjangnya tidak berubah ketika data
  bertambah — pemeriksaan yang menangkap perangkaian meski penandanya tidak
  cocok persis.
- segmen dari `indeks_metadata` **tidak masuk** `posisi_konten` sama sekali
  (FR-D06, C-02). Ia hanya boleh muncul sebagai bacaan lanjutan pada tanggapan
  kepada pengguna, dan itu urusan fitur 009.
"""

from __future__ import annotations

from pydantic import BaseModel

from src.llm.adaptor.dasar import Permintaan
from src.kamus.segmen import IndeksTujuan


class BlokKonten(BaseModel, frozen=True, extra="forbid"):
    """Satu segmen pada posisi konten, beserta jejak yang diperlukan sitasi."""

    id_segmen: str
    teks: str
    peringkat: str


class MuatanPenyedia(BaseModel, frozen=True, extra="forbid"):
    """Muatan yang dikirim ke penyedia.

    Sengaja tidak memiliki bidang gabungan bernama `teks`, `prompt`, atau
    `isi`. Bidang yang dapat menampung instruksi dan konten sekaligus adalah
    jalan pintas menuju pelanggaran C-18, dan jalan pintas yang tersedia
    cenderung dipakai.
    """

    posisi_instruksi: str
    posisi_konten: tuple[BlokKonten, ...]
    model: str
    suhu: float
    batas_token: int


def susun_muatan(permintaan: Permintaan) -> MuatanPenyedia:
    """Petakan permintaan ke muatan penyedia tanpa merangkai posisinya."""
    return MuatanPenyedia(
        posisi_instruksi=permintaan.instruksi.teks,
        posisi_konten=tuple(
            BlokKonten(
                id_segmen=butir.id_segmen,
                teks=butir.teks,
                peringkat=butir.peringkat_kepercayaan.value,
            )
            for butir in permintaan.data
            if butir.indeks_asal is IndeksTujuan.UTAMA
        ),
        model=permintaan.konfigurasi.nama_model,
        suhu=permintaan.konfigurasi.suhu,
        batas_token=permintaan.konfigurasi.batas_token,
    )
