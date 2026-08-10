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

## Batas yang wajib diketahui: porsi minimum pembanding belum ditetapkan

`BatchAnotasi` menolak batch berpra-anotasi yang **tidak menyisihkan satu pun**
pembanding. Ia **tidak** menolak batch dengan seratus dokumen berpra-anotasi
dan satu pembanding — dan batch seperti itu hampir pasti tidak memenuhi maksud
FR-C10 meski memenuhi katanya.

Sebabnya bukan kelalaian: **angkanya tidak ada pada dokumen mana pun.** D-01
FR-C10 menulis "sebagian batch"; D-03 BT-13 menulis "disarankan menyisihkan
sebagian batch". C-16 melarang menetapkan ambang di luar prosedur kalibrasi
D-07 BT-29, sehingga menaruh satu angka di sini akan melahirkan ambang yang
tidak pernah dikalibrasi siapa pun — persis yang B-6 jaga.

Yang dikerjakan sebagai gantinya: porsinya **dihitung dan dilaporkan**, tidak
dinilai. `porsi_pembanding` masuk catatan batch (R-15), sehingga porsi yang
terlalu kecil terbaca dari catatan alih-alih tersembunyi di balik pemeriksaan
yang lulus.

**Butir terbuka bagi tim:** BT-13 perlu diperluas dengan porsi minimum, atau
dinyatakan tegas bahwa penilaiannya diserahkan kepada adjudikator per batch.
Sampai salah satunya diputuskan, modul ini menegakkan batas yang tertulis dan
tidak lebih.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class BatchAnotasi(BaseModel):
    """Sekumpulan dokumen yang dianotasi bersama, dengan pengendali R-13.

    Pemeriksaan pembanding dilakukan **saat batch dibentuk**, bukan sebagai
    fungsi yang dipanggil terpisah. Pemeriksaan terpisah adalah pemeriksaan
    yang dapat dilewati, dan yang paling mungkin melewatinya adalah kode yang
    ditulis ketika tenggat mendekat.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_batch: str = Field(min_length=1)
    dokumen: tuple[DokumenAnotasi, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _pembanding_sesuai_keadaan_batch(self) -> BatchAnotasi:
        """Tiga penolakan, dan ketiganya tentang hal yang sama: catatan batch
        yang menyatakan pengendalian yang tidak sungguh ada."""
        pengenal = [d.id_dokumen for d in self.dokumen]
        if len(set(pengenal)) != len(pengenal):
            raise ValueError(
                "dokumen tercatat lebih dari sekali pada satu batch — "
                "pengulangan menggeser porsi pembanding tanpa satu dokumen pun "
                "benar-benar disisihkan"
            )

        if self.memakai_pra_anotasi and self.jumlah_pembanding == 0:
            raise ValueError(
                "batch memakai pra-anotasi tetapi tidak menyisihkan satu pun "
                "dokumen pembanding — tanpa pembanding, kesepakatan yang tinggi "
                "tidak dapat dibedakan dari anotator yang menyetujui saran mesin "
                "yang sama (FR-C10, D-03 BT-13)"
            )

        if not self.memakai_pra_anotasi and self.jumlah_pembanding > 0:
            raise ValueError(
                "dokumen ditandai pembanding pada batch yang tidak memakai "
                "pra-anotasi — penandaan ini masuk hitungan porsi pembanding "
                "pada catatan batch, sehingga angkanya menyatakan pengendalian "
                "yang tidak pernah ada"
            )
        return self

    @property
    def memakai_pra_anotasi(self) -> bool:
        return any(
            d.status_pra_anotasi is StatusPraAnotasi.DENGAN_PRA_ANOTASI for d in self.dokumen
        )

    @property
    def jumlah_pembanding(self) -> int:
        return sum(1 for d in self.dokumen if d.status_pra_anotasi is StatusPraAnotasi.PEMBANDING)

    @property
    def porsi_pembanding(self) -> float | None:
        """Porsi pembanding atas seluruh batch, atau `None` bila tidak berlaku.

        **`None`, bukan 0,0.** Porsi nol pada batch yang tidak memakai
        pra-anotasi terbaca sebagai pengendalian yang hilang, padahal tidak ada
        yang perlu dikendalikan. Bentuk yang sama dengan `HasilKesepakatan`
        yang bernilai `None` ketika belum terhitung.

        Angkanya **dilaporkan, tidak dinilai** — lihat batas pada uraian modul.
        """
        if not self.memakai_pra_anotasi:
            return None
        return self.jumlah_pembanding / len(self.dokumen)
