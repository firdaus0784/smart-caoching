"""Penilaian jawaban dan aduan kurator — T-5 fitur 036, FR-F07, FR-I04; R-01,
R-03, R-04, R-06; D-14 Bagian 4.9.

Lapisan ini menerjemahkan badan permintaan menjadi panggilan penyimpan dan
hasilnya menjadi bentuk D-14. Aturannya tiga, dan ketiganya dijaga di sini
karena hanya di sini teksnya terbaca:

- **Alasan dan catatan tanpa data pribadi berpola (KM-03).** Pendeteksi FR-B04
  dijalankan sebelum penyimpan dipanggil; yang ditolak tidak sampai ke
  penyimpan, telemetri, maupun log — pesannya tidak mengutip.
- **Kirim hanya bersama keliru (P-2 B).** Penyimpan dan batasan tabel
  menolaknya pula; di sini ia menjadi 400 yang berbahasa manusia.
- **Tanpa akibat (R-04).** Tidak ada yang dipanggil selain penyimpan: jawaban,
  pengambilan, ambang, dan beranda tidak tahu penilaian ada (C-14, C-16).

Pesan milik orang lain dan pesan yang tidak dikenal menjadi `PesanTidakAda`
yang sama; nomor aduan yang tidak berupa angka sama dengan aduan yang tidak
dikenal.
"""

from __future__ import annotations

from typing import Any, Final

from pydantic import BaseModel, ConfigDict, StrictBool, ValidationError

from src.api.hari import iso_utc
from src.kamus.penilaian import NilaiPenilaian, TindakLanjutAduan
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.penilaian import (
    BarisAduan,
    HasilPenilaian,
    PenyimpanAduan,
    PenyimpanPenilaian,
)

PESAN_PENILAIAN_TIDAK_SAH: Final = (
    "Penilaian belum terkirim. Periksa pilihan dan alasan, lalu kirim lagi."
)
PESAN_JAWABAN_TIDAK_ADA: Final = "Jawaban yang Anda nilai tidak ditemukan."
PESAN_TINDAK_LANJUT_TIDAK_SAH: Final = (
    "Tindak lanjut belum tersimpan. Pilih satu, lalu tulis catatan tanpa nomor pribadi."
)
PESAN_ADUAN_TIDAK_ADA: Final = "Aduan yang Anda cari tidak ditemukan."

PERAN_KURATOR: Final = "kurator"
"""Peran akun `kurator` D-14 mencatat tindak lanjut sebagai `kurator` — sama
dengan putusan (fitur 013, `_PERAN`)."""


class AduanTidakAda(Exception):
    """Aduan tidak dikenal, gugur, atau sudah bertindak lanjut — tak dibedakan."""


class _Ketat(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)


class PermintaanPenilaian(_Ketat):
    """Badan `POST /pesan/{id}/penilaian`. `kirim_ke_kurator` ketat: untai
    `"true"` bukan persetujuan menyerahkan pertanyaan kepada orang lain."""

    nilai: NilaiPenilaian
    alasan: str | None = None
    kirim_ke_kurator: StrictBool = False


class PermintaanTindakLanjut(_Ketat):
    tindak_lanjut: TindakLanjutAduan
    catatan: str


class _Tanggapan(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Penilaian(_Tanggapan):
    id_pesan: str
    nilai: NilaiPenilaian
    kirim_ke_kurator: bool


class AduanTampil(_Tanggapan):
    """Satu aduan pada D-14 Bagian 4.9 — tanpa penaut ke peserta (R-06)."""

    nomor: int
    diadukan_pada: str
    pertanyaan: str
    alasan: str | None
    tanggapan: dict[str, Any]


class DaftarAduan(_Tanggapan):
    aduan: list[AduanTampil]


def _bersih(teks: str | None) -> str | None:
    if teks is None or not teks.strip():
        return None
    return teks.strip()


async def nilai(
    simpan: PenyimpanPenilaian,
    id_pesan: str,
    badan: Any,
    *,
    pemilik: str,
    sekarang: Any,
) -> tuple[dict[str, Any], HasilPenilaian, PermintaanPenilaian]:
    """Catat satu penilaian. `ValueError` bagi badan yang tidak sah;
    `PesanTidakAda` dari penyimpan dibiarkan naik."""
    try:
        permintaan = PermintaanPenilaian.model_validate(badan)
    except ValidationError:
        raise ValueError("badan penilaian tidak sah") from None
    if permintaan.kirim_ke_kurator and permintaan.nilai is not NilaiPenilaian.KELIRU:
        raise ValueError("hanya penilaian keliru yang dapat dikirim kepada kurator")
    alasan = _bersih(permintaan.alasan)
    if alasan is not None and periksa_data_pribadi(alasan):
        raise ValueError("alasan memuat data pribadi berpola")
    hasil = await simpan.catat(
        pemilik=pemilik,
        id_pesan=id_pesan,
        nilai=permintaan.nilai,
        alasan=alasan,
        kirim_ke_kurator=permintaan.kirim_ke_kurator,
        waktu=sekarang,
    )
    isi = Penilaian(
        id_pesan=id_pesan, nilai=permintaan.nilai, kirim_ke_kurator=permintaan.kirim_ke_kurator
    ).model_dump(mode="json")
    return isi, hasil, permintaan.model_copy(update={"alasan": alasan})


def _tampil(a: BarisAduan) -> AduanTampil:
    return AduanTampil(
        nomor=a.nomor,
        diadukan_pada=iso_utc(a.diadukan_pada),
        pertanyaan=a.pertanyaan,
        alasan=a.alasan,
        tanggapan=dict(a.tanggapan),
    )


async def daftar_aduan(simpan: PenyimpanAduan) -> dict[str, Any]:
    """Tanggapan `GET /kurasi/aduan` dan `POST /kurasi/aduan/{id}/tindak-lanjut`."""
    return DaftarAduan(aduan=[_tampil(a) for a in await simpan.terbuka()]).model_dump(mode="json")


async def tindak_lanjuti(
    simpan: PenyimpanAduan, nomor: str, badan: Any, *, pseudonim: str, sekarang: Any
) -> None:
    """`AduanTidakAda` bagi nomor yang tidak dikenal atau tidak lagi terbuka;
    `ValueError` bagi badan yang tidak sah."""
    if not nomor.isdecimal():
        raise AduanTidakAda
    try:
        permintaan = PermintaanTindakLanjut.model_validate(badan)
    except ValidationError:
        raise ValueError("badan tindak lanjut tidak sah") from None
    catatan = permintaan.catatan.strip()
    if not catatan or periksa_data_pribadi(catatan):
        raise ValueError("catatan tindak lanjut tidak sah")
    if not await simpan.tindak_lanjut(
        int(nomor),
        tindak_lanjut=permintaan.tindak_lanjut,
        catatan=catatan,
        peran=PERAN_KURATOR,
        pseudonim_kurator=pseudonim,
        waktu=sekarang,
    ):
        raise AduanTidakAda
