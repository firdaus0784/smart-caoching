"""Penyaringan otomatis berlapis — R-03 s.d. R-06, FR-I07, D-06 Bagian 6.

Empat lapis, dijalankan berurutan; *"kandidat yang gugur tidak melanjutkan ke
lapis berikutnya."*

| Lapis | Kriteria | Tindakan bila gugur |
|---|---|---|
| L1 · Lisensi | Terbaca dan diizinkan | Dibuang, **tidak disimpan** (PP-01) |
| L2 · Kebaruan | Bukan duplikat, bukan versi lama | Dibuang; versi lebih baru menggantikan |
| L3 · Keberlakuan | Regulasi berstatus berlaku | Disimpan sebagai rujukan historis (KL-07) |
| L4 · Relevansi | Skor K1–K8 melampaui ambang | Kolam cadangan |

## L4 belum dapat dijalankan, dan itu menahan — bukan meloloskan, bukan membuang

Skor relevansi menuntut klasifikasi K1–K8 (fitur 017) **dan** ambang yang D-06
serahkan ke BT-24, uji ingesti percobaan bulan 3.

`HasilSaring` karena itu bernilai **tiga**: `LOLOS`, `GUGUR`, `MENUNGGU`.
Pengulangan keenam pola yang sama — `HasilSistem` (015), `HasilKesepakatan`
(003), `bendera` (016), `Nilai` (004), `HasilHitung` (005), `Status` validator
(008) — dan di sini ia menahan hal yang berbeda dari lima sebelumnya.

Lima kali sebelumnya pola ini menahan **laporan yang keliru**. Di sini ia
menahan **pilihan yang tidak boleh diambil tanpa dasar**. D-06 Bagian 6
menyebut kedua akibat yang salah dan tidak menyebut mana yang lebih ringan:

> Ambang terlalu longgar **membanjiri antrean kurasi**; terlalu ketat membuat
> **feed kekurangan isi** dan memicu titik kritis T5 pada D-02.

Kandidat yang membanjiri antrean berhadapan dengan kurator yang hanya punya
empat jam per minggu (D-06 Bagian 7.2), dan gerbang yang antreannya membanjir
akan dilewati orang — yang dilewati bersamanya adalah C-06.

`MENUNGGU` satu-satunya jawaban yang tidak memilih di antara keduanya.

## Perbedaan antara dibuang dan disimpan

D-06 memisahkan keduanya tegas, dan pemisahannya bukan gradasi:

- **L1 gugur → dibuang, tidak disimpan.** PP-01. Butir berlisensi tidak jelas
  yang tersimpan adalah butir yang kelak diangkat seseorang yang tidak tahu
  mengapa ia ada di sana.
- **L2 gugur → dibuang.** Duplikat tidak menambah apa pun.
- **L3 gugur → disimpan sebagai rujukan historis**, tidak masuk antrean tayang.
  Regulasi yang dicabut tetap berguna untuk menelusuri mengapa sebuah ketentuan
  berubah; yang dilarang adalah ia menjadi dasar jawaban (C-07).
- **L4 gugur → kolam cadangan**, dapat diangkat bila prioritas pengguna
  berubah.

Keempat tindakan itu berbeda, dan menyamakannya menjadi "gugur" akan
kehilangan tiga di antaranya.
"""

from __future__ import annotations

from collections.abc import Container
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from src.ingest.kurasi.butir import ButirPengetahuan
from src.kamus.segmen import StatusKeberlakuan
from src.penyimpanan.indeks import StatusLisensi, lisensi_dari_metadata

_MENUNGGU_L4 = (
    "skor relevansi menuntut klasifikasi K1–K8 (fitur 017) dan ambang BT-24, "
    "uji ingesti percobaan bulan 3 (C-16)"
)
"""Alasan L4 belum dapat dijalankan, menyebut **apa** yang ditunggunya.

Alasan yang tidak menyebut apa yang ditunggu adalah alasan yang tidak dapat
ditagih — bentuk yang sama dengan `_MENUNGGU_FITUR_020` pada fitur 008.
"""


class Lapis(Enum):
    """Keempat lapis D-06 Bagian 6, berurutan."""

    L1_LISENSI = "L1"
    L2_KEBARUAN = "L2"
    L3_KEBERLAKUAN = "L3"
    L4_RELEVANSI = "L4"


class Keadaan(Enum):
    """Tiga keadaan sebuah lapis — lihat uraian modul.

    `MENUNGGU` **bukan** ragam gugur yang lebih lunak maupun lolos yang lebih
    hati-hati. Ia keadaan tersendiri: kandidat tidak masuk antrean **dan**
    tidak dibuang.
    """

    LOLOS = "lolos"
    GUGUR = "gugur"
    MENUNGGU = "menunggu"


class Tindakan(Enum):
    """Apa yang terjadi pada kandidat — D-06 Bagian 6.

    Empat tindakan berbeda, bukan satu "gugur". Menyamakannya akan kehilangan
    tiga di antaranya — lihat uraian modul.
    """

    MASUK_ANTREAN = "masuk_antrean"
    DIBUANG = "dibuang"
    RUJUKAN_HISTORIS = "rujukan_historis"
    KOLAM_CADANGAN = "kolam_cadangan"
    TERTAHAN = "tertahan"


class HasilSaring(BaseModel):
    """Hasil penyaringan satu kandidat."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lapis_terakhir: Lapis
    keadaan: Keadaan
    tindakan: Tindakan
    alasan: str = Field(min_length=1)
    """Selalu terisi, termasuk pada `LOLOS`.

    Pada `MENUNGGU` ia menyebut fitur yang membukanya; alasan yang tidak
    menyebut apa yang ditunggu adalah alasan yang tidak dapat ditagih.
    """

    @property
    def boleh_masuk_antrean(self) -> bool:
        """Hanya `MASUK_ANTREAN`.

        Sifat terhitung, bukan bidang — bidang dapat diisi `True` oleh
        pemanggil yang lelah, dan antrean yang menerima kandidat tak tersaring
        adalah antrean yang membanjiri kurator.
        """
        return self.tindakan is Tindakan.MASUK_ANTREAN


def saring(
    butir: ButirPengetahuan,
    *,
    id_dokumen_dikenal: Container[str],
    versi_lebih_baru_dari: str | None = None,
) -> HasilSaring:
    """Jalankan keempat lapis berurutan — D-06 Bagian 6.

    `id_dokumen_dikenal` dan `versi_lebih_baru_dari` diserahkan pemanggil:
    keduanya menuntut membaca kolam butir yang sudah ada, dan itu akses
    penyimpanan yang `AGENTS.md` tempatkan pada `src/penyimpanan/`.

    Kandidat yang gugur **tidak melanjutkan** ke lapis berikutnya. Itu bukan
    penghematan melainkan bagian aturannya: butir berlisensi tidak jelas tidak
    perlu diperiksa kebaruannya, dan memeriksanya berarti menyimpannya sebentar.
    """
    if lisensi_dari_metadata(butir.lisensi) is not StatusLisensi.TERBUKA:
        return HasilSaring(
            lapis_terakhir=Lapis.L1_LISENSI,
            keadaan=Keadaan.GUGUR,
            tindakan=Tindakan.DIBUANG,
            alasan="lisensi tidak terbaca mesin atau tidak diizinkan — dibuang tanpa "
            "disimpan (PP-01, KL-02)",
        )

    if versi_lebih_baru_dari is None and butir.id_dokumen_sumber in id_dokumen_dikenal:
        return HasilSaring(
            lapis_terakhir=Lapis.L2_KEBARUAN,
            keadaan=Keadaan.GUGUR,
            tindakan=Tindakan.DIBUANG,
            alasan="duplikat dokumen yang sudah ada pada kolam butir",
        )

    if (
        butir.bersumber_regulasi
        and butir.status_keberlakuan is not StatusKeberlakuan.BERLAKU
    ):
        return HasilSaring(
            lapis_terakhir=Lapis.L3_KEBERLAKUAN,
            keadaan=Keadaan.GUGUR,
            tindakan=Tindakan.RUJUKAN_HISTORIS,
            alasan="regulasi sumber tidak berstatus berlaku — disimpan sebagai rujukan "
            "historis, tidak masuk antrean tayang (KL-07, C-07)",
        )

    return HasilSaring(
        lapis_terakhir=Lapis.L4_RELEVANSI,
        keadaan=Keadaan.MENUNGGU,
        tindakan=Tindakan.TERTAHAN,
        alasan=_MENUNGGU_L4,
    )
