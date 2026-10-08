"""Analitik penelitian — T-4 fitur 035, R-03 s.d. R-07; K-2, K-3; D-14 Bagian 4.8.

## Dihitung saat diminta

Setiap angka dihitung dari peristiwa pada pemanggilan ini. Tidak ada metrik
yang disimpan: angka tersimpan tidak ikut terhapus ketika peserta menarik
datanya (fitur 033), dan tidak ikut berubah ketika definisinya diperbaiki.

## `pengembangan` dipisah, bukan dibuang

Peristiwa dari titik jalan pengembangan (`versi_aplikasi = pengembangan`,
fitur 034) tidak masuk satu metrik pun, tetapi **dihitung** pada integritas —
yang disaring tanpa dihitung tidak dapat diperiksa.

## Retensi

Kohort = tanggal WIB peristiwa pertama pseudonim. Penyebut hari ke-N: kohort
yang tanggalnya + N tidak melewati hari ini. Pembilang: yang berperistiwa
**tepat** pada tanggal kohort + N. Kohort yang belum berumur N hari tidak
dihitung "tidak kembali" — ia belum dapat kembali (P-2).

## `null`, bukan nol

Rasio tanpa penyebut, median tanpa sesi, waktu tanpa peristiwa: `None`. Nol
berarti "diukur dan tidak ada"; `None` berarti "belum dapat diukur". Menyamakan
keduanya adalah cara laporan penelitian berbohong tanpa satu angka pun salah.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from src.api.hari import WIB, tanggal_wib
from src.kamus.penilaian import NilaiPenilaian
from src.penyimpanan.analitik import CatatanEkspor, PenyimpanAnalitik
from src.penyimpanan.telemetri import BarisPeristiwa
from src.telemetri.ekspor import ke_csv

VERSI_PENGEMBANGAN: Final = "pengembangan"
"""Penanda versi titik jalan pengembangan (fitur 034, K-4) — kesamaannya dengan
penanda pada titik jalan dijaga uji, bukan impor: `src/` tidak mengimpor
perkakas pengembangan."""

HARI_RETENSI: Final = (1, 7, 30)
"""D-01 Bagian 9.1 apa adanya."""

PESAN_EKSPOR_TIDAK_SAH: Final = "Rentang tanggal belum sesuai. Periksa tanggal awal dan akhir."
"""C-13: ≤ 20 kata, tanpa mengutip masukan."""


class MetrikTertunda(Enum):
    """Metrik D-01 Bagian 9.1 yang peristiwanya belum terekam."""

    RASIO_PENUNTASAN = "rasio_penuntasan"
    RASIO_PENELUSURAN_SUMBER = "rasio_penelusuran_sumber"
    RASIO_VERIFIKASI = "rasio_verifikasi"
    RASIO_KOMITMEN = "rasio_komitmen"
    RASIO_PENERAPAN = "rasio_penerapan"
    # `akurasi_qa` keluar pada fitur 036 (P-4 B): `answer_rated` kini terekam,
    # dan jumlahnya tampil pada `RingkasanPenilaian` — tanpa rasio "ketepatan"
    # yang definisinya belum ditetapkan D-08.


SEBAB_TERTUNDA: Final[dict[MetrikTertunda, str]] = {
    MetrikTertunda.RASIO_PENUNTASAN: (
        "Lama baca hanya teramati di peramban, dan rute penerimanya belum diputus."
    ),
    MetrikTertunda.RASIO_PENELUSURAN_SUMBER: (
        "Sumber yang dibuka belum terekam; pembaca sumber belum dibangun."
    ),
    MetrikTertunda.RASIO_VERIFIKASI: "Pemeriksaan pemahaman belum dibangun.",
    MetrikTertunda.RASIO_KOMITMEN: "Komitmen penerapan belum dibangun.",
    MetrikTertunda.RASIO_PENERAPAN: "Komitmen penerapan belum dibangun.",
}


# ── bentuk tanggapan — D-14 Bagian 4.8 ───────────────────────────────


class _Tanggapan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AktifHarian(_Tanggapan):
    tanggal: date
    pengguna: int


class AktifMingguan(_Tanggapan):
    mulai: date
    pengguna: int


class Retensi(_Tanggapan):
    hari: int
    kohort: int
    kembali: int
    rasio: float | None


class RingkasanSesi(_Tanggapan):
    jumlah: int
    median_menit: float | None
    rerata_menit: float | None


class Keterlibatan(_Tanggapan):
    aktif_harian: list[AktifHarian]
    aktif_mingguan: list[AktifMingguan]
    retensi: list[Retensi]
    sesi: RingkasanSesi


class RasioPenemuan(_Tanggapan):
    disajikan: int
    dibuka: int
    rasio: float | None


class RingkasanPenilaian(_Tanggapan):
    """Jumlah per nilai atas penilaian **terakhir** tiap pesan (fitur 036, KB-228)."""

    per_nilai: dict[str, int]


class BelumTerukur(_Tanggapan):
    metrik: MetrikTertunda
    sebab: str


class Integritas(_Tanggapan):
    per_jenis: dict[str, int]
    per_versi_aplikasi: dict[str, int]
    per_versi_model: dict[str, int]
    pertama: datetime | None
    terakhir: datetime | None
    pengembangan: int


class RingkasanAnalitik(_Tanggapan):
    dihitung_pada: datetime
    keterlibatan: Keterlibatan
    penemuan: RasioPenemuan
    penilaian: RingkasanPenilaian
    belum_terukur: list[BelumTerukur]
    integritas: Integritas


class PermintaanEkspor(BaseModel):
    """Badan `POST /analitik/ekspor` — tanggal WIB, inklusif."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    dari: date
    sampai: date
    termasuk_pengembangan: bool = False

    @model_validator(mode="after")
    def _berurutan(self) -> PermintaanEkspor:
        if self.dari > self.sampai:
            raise ValueError("rentang terbalik")
        return self


# ── metrik ───────────────────────────────────────────────────────────


def _rasio(pembilang: int, penyebut: int) -> float | None:
    return pembilang / penyebut if penyebut else None


def _senin(tanggal: date) -> date:
    return tanggal - timedelta(days=tanggal.weekday())


def _retensi(per_pemilik: dict[str, set[date]], hari_ini: date) -> list[Retensi]:
    hasil = []
    for n in HARI_RETENSI:
        kohort = kembali = 0
        for tanggal in per_pemilik.values():
            sasaran = min(tanggal) + timedelta(days=n)
            if sasaran > hari_ini:
                continue
            kohort += 1
            kembali += sasaran in tanggal
        hasil.append(Retensi(hari=n, kohort=kohort, kembali=kembali, rasio=_rasio(kembali, kohort)))
    return hasil


def _sesi(pilot: Sequence[BarisPeristiwa]) -> RingkasanSesi:
    durasi = [
        b.properti["durasi_menit"]
        for b in pilot
        if b.jenis == "session_end" and isinstance(b.properti.get("durasi_menit"), int)
    ]
    if not durasi:
        return RingkasanSesi(jumlah=0, median_menit=None, rerata_menit=None)
    return RingkasanSesi(
        jumlah=len(durasi),
        median_menit=statistics.median(durasi),
        rerata_menit=statistics.fmean(durasi),
    )


def _penilaian(pilot: Sequence[BarisPeristiwa]) -> RingkasanPenilaian:
    """Penilaian ulang menggantikan yang sebelumnya: kunci (pseudonim,
    `id_pesan`), yang terakhir menurut waktu. Properti yang tidak berbentuk
    `answer_rated` fitur 036 ditolak keras, sama dengan baris rusak lain."""
    terakhir: dict[tuple[str, str], tuple[datetime, NilaiPenilaian]] = {}
    for b in pilot:
        if b.jenis != "answer_rated":
            continue
        kunci = (b.pseudonim, str(b.properti["id_pesan"]))
        nilai = NilaiPenilaian(b.properti["nilai"])
        if kunci not in terakhir or terakhir[kunci][0] <= b.waktu:
            terakhir[kunci] = (b.waktu, nilai)
    jumlah = Counter(n for _, n in terakhir.values())
    return RingkasanPenilaian(per_nilai={n.value: jumlah[n] for n in NilaiPenilaian})


def ringkasan(peristiwa: Iterable[BarisPeristiwa], *, sekarang: datetime) -> RingkasanAnalitik:
    """Ringkasan S-18 — fungsi murni atas peristiwa; lihat uraian modul."""
    semua = list(peristiwa)
    pilot = [b for b in semua if b.versi_aplikasi != VERSI_PENGEMBANGAN]

    harian: dict[date, set[str]] = {}
    mingguan: dict[date, set[str]] = {}
    per_pemilik: dict[str, set[date]] = {}
    for b in pilot:
        tanggal = tanggal_wib(b.waktu)
        harian.setdefault(tanggal, set()).add(b.pseudonim)
        mingguan.setdefault(_senin(tanggal), set()).add(b.pseudonim)
        per_pemilik.setdefault(b.pseudonim, set()).add(tanggal)

    jenis = Counter(b.jenis for b in pilot)
    return RingkasanAnalitik(
        dihitung_pada=sekarang,
        keterlibatan=Keterlibatan(
            aktif_harian=[
                AktifHarian(tanggal=t, pengguna=len(p)) for t, p in sorted(harian.items())
            ],
            aktif_mingguan=[
                AktifMingguan(mulai=t, pengguna=len(p)) for t, p in sorted(mingguan.items())
            ],
            retensi=_retensi(per_pemilik, tanggal_wib(sekarang)),
            sesi=_sesi(pilot),
        ),
        penemuan=RasioPenemuan(
            disajikan=jenis["discovery_served"],
            dibuka=jenis["discovery_opened"],
            rasio=_rasio(jenis["discovery_opened"], jenis["discovery_served"]),
        ),
        penilaian=_penilaian(pilot),
        belum_terukur=[BelumTerukur(metrik=m, sebab=SEBAB_TERTUNDA[m]) for m in MetrikTertunda],
        integritas=Integritas(
            per_jenis=dict(sorted(jenis.items())),
            per_versi_aplikasi=dict(sorted(Counter(b.versi_aplikasi for b in pilot).items())),
            per_versi_model=dict(sorted(Counter(b.versi_model for b in pilot).items())),
            pertama=min((b.waktu for b in pilot), default=None),
            terakhir=max((b.waktu for b in pilot), default=None),
            pengembangan=len(semua) - len(pilot),
        ),
    )


# ── ekspor ───────────────────────────────────────────────────────────


def _awal_hari_utc(tanggal: date) -> datetime:
    return datetime.combine(tanggal, time(0), tzinfo=WIB).astimezone(UTC)


async def ekspor(
    simpan: PenyimpanAnalitik, badan: Any, *, peneliti: str, sekarang: datetime
) -> tuple[str, str]:
    """CSV dan nama berkasnya; `ValueError` bagi badan yang tidak sah.

    Jejak tercatat **sebelum** berkas dikembalikan (K-3): penyimpan jejak yang
    gagal menggagalkan ekspor, sehingga tidak ada berkas tanpa jejak.
    """
    try:
        permintaan = PermintaanEkspor.model_validate(badan)
    except ValidationError as galat:
        raise ValueError("permintaan ekspor tidak sah") from galat
    baris = [
        b
        for b in await simpan.peristiwa(
            mulai=_awal_hari_utc(permintaan.dari),
            sebelum=_awal_hari_utc(permintaan.sampai + timedelta(days=1)),
        )
        if permintaan.termasuk_pengembangan or b.versi_aplikasi != VERSI_PENGEMBANGAN
    ]
    nomor = await simpan.catat_ekspor(
        CatatanEkspor(
            peneliti=peneliti,
            diekspor_pada=sekarang,
            dari=permintaan.dari,
            sampai=permintaan.sampai,
            termasuk_pengembangan=permintaan.termasuk_pengembangan,
            jumlah_baris=len(baris),
        )
    )
    nama = f"peristiwa-{permintaan.dari.isoformat()}-{permintaan.sampai.isoformat()}-{nomor}.csv"
    return ke_csv(baris), nama
