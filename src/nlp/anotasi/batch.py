"""Batch anotasi dan pengendalian *automation bias* — R-12, R-13, R-15, FR-C10.

**Modul ini membangun pengendali sebelum yang dikendalikannya ada, dan itu
disengaja.** Pra-anotasi otomatis menunggu model NER fitur 004. *Automation
bias* — kecenderungan menerima saran mesin tanpa memeriksanya — muncul pada
hari pertama pra-anotasi dipakai, bukan setelah ia matang. Menambahkan
pengendalinya belakangan berarti batch-batch pertama berjalan tanpa
pembanding, dan batch pertama justru yang paling menentukan kebiasaan
anotator.

Urutan yang sama dengan gerbang karantina fitur 002 yang dibangun mendahului
pendeteksi data pribadi fitur 015. Alasannya pun sama: pengendali yang datang
belakangan menghadapi kebiasaan yang sudah terbentuk.

**Ini bukan kerangka kosong yang C-14 larang.** Yang dilarang C-14 adalah
membangun fitur ruang lingkup 2026 dalam bentuk apa pun termasuk kerangka
kosong. Yang ada di sini bekerja penuh hari ini: dokumen wajib membawa status
pra-anotasinya, dan batch yang menyatakan memakai pra-anotasi ditolak bila
tidak menyisihkan pembanding. Keduanya menolak masukan yang keliru sekarang
juga, tanpa satu baris pun menunggu fitur 004.

## Tiga status, dan mengapa bukan dua

| Status | Anotator melihat saran mesin? | Asalnya |
|---|---|---|
| `TANPA_PRA_ANOTASI` | tidak | batch yang memang belum memakai pra-anotasi |
| `DENGAN_PRA_ANOTASI` | ya | batch berpra-anotasi |
| `PEMBANDING` | tidak | **sengaja disisihkan** di dalam batch berpra-anotasi |

Yang pertama dan ketiga sama-sama berarti "dianotasi dari halaman kosong",
sehingga menyatukannya tampak seperti menghapus nilai yang mubazir. Yang
hilang bersamanya adalah kemampuan menghitung porsi pembanding pada batch
berpra-anotasi — dan porsi itu satu-satunya angka yang membuat pengendalian
ini berarti.

**Status tidak memiliki nilai bawaan.** Nilai bawaan apa pun akan menjadi
jawaban bagi dokumen yang statusnya sebenarnya tidak diketahui, dan dokumen
berstatus keliru lebih buruk daripada dokumen tanpa status: yang kedua
menghentikan pembacanya, yang pertama terbaca sebagai keterangan.

Tidak ada keadaan "belum diketahui" pada enum ini, dan itu keputusan yang
berlaku selama belum ada korpus teranotasi. Bila kelak dokumen dari luar
sistem ini masuk tanpa status yang tercatat, nilainya **ditambahkan sebagai
keadaan tersendiri** — bukan dipetakan ke `TANPA_PRA_ANOTASI`, yang akan
menyatakan sesuatu yang tidak diketahui siapa pun.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StatusPraAnotasi(Enum):
    """Apakah anotator melihat saran mesin saat mengerjakan dokumen ini.

    Enum sebagai tipe, bukan untai bebas (`AGENTS.md` bagian Gaya). Untai
    bebas di sini berarti "pembanding", "Pembanding", dan "kontrol" hidup
    berdampingan, lalu porsi pembanding dihitung atas salah satunya saja.
    """

    TANPA_PRA_ANOTASI = "tanpa_pra_anotasi"
    DENGAN_PRA_ANOTASI = "dengan_pra_anotasi"
    PEMBANDING = "pembanding"


class DokumenAnotasi(BaseModel):
    """Satu dokumen dalam batch anotasi, beserta status pra-anotasinya (R-12).

    Sengaja **tidak membawa anotasinya**. Dokumen di sini adalah satuan
    penjadwalan dan pengendalian, bukan wadah hasil; menaruh anotasi di
    dalamnya akan mengundang perhitungan kesepakatan dilakukan dari sini
    dengan tipe yang sudah dipisahkan `rentang.py`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_dokumen: str = Field(min_length=1)
    status_pra_anotasi: StatusPraAnotasi
