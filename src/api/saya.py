"""Akun saya — T-4 fitur 030, R-01 s.d. R-05, R-08, R-10; K-4, K-5; D-14 Bagian 4.5.

Penerjemah antara empat rute `/saya/*` dan penyimpan pengguna. Aturan isinya
**tidak ditulis di sini**: ia milik model fitur 022 — `ProfilSekolah`,
`PrioritasManajerial`, `CatatanPersetujuan` — yang dipakai lewat tepi
`api → pengguna` (AGENTS.md, K-1). Menulis ulang batas enam isian atau tiga
sampai lima prioritas di sini akan menghasilkan dua tempat yang berselisih.

## Pemilik dari sesi

Badan permintaan tidak dapat menyebut pemilik maupun waktu: `extra="forbid"`
menolak `id_pengguna`, `tanggal_perbarui`, dan nama lain apa pun (R-02, M-1).

## Naskah persetujuan

Naskah ET-02 dibaca dari berkas berversi yang diisi tim — agen tidak
menulisnya (KB-164). Peladen menerima `versi_naskah` hanya bila sama dengan
versi berkas itu; **tanpa berkas, setiap persetujuan ditolak**, sehingga
telemetri tetap mati bagi semua orang (C-04, M-3). Berkas yang ada tetapi
rusak menghentikan penyusunan aplikasi — naskah rusak bukan naskah yang belum
ada.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from src.nlp.anotasi.skema import KategoriMasalah
from src.pengguna.persetujuan import CatatanPersetujuan, JenisPersetujuan, KeadaanPersetujuan
from src.pengguna.prioritas import PrioritasManajerial
from src.pengguna.profil import JalurAkreditasi, ProfilSekolah
from src.penyimpanan.pengguna import BarisProfil, PenyimpanPengguna

PESAN_PROFIL_TIDAK_SAH: Final = "Isian profil belum sesuai. Periksa lagi setiap isian."
PESAN_PRIORITAS_TIDAK_SAH: Final = "Pilih tiga sampai lima prioritas yang berbeda."
PESAN_PERSETUJUAN_TIDAK_SAH: Final = (
    "Persetujuan belum dapat dicatat. Muat ulang halaman, lalu coba lagi."
)
"""C-13: ≤ 20 kata, tanpa istilah teknis, **tanpa mengutip masukan** — isian
yang ditolak karena memuat nomor pribadi tidak boleh kembali lewat pesannya."""


class Naskah(BaseModel):
    """Berkas naskah ET-02 — `web/public/naskah/persetujuan.json` (K-4)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    versi: str = Field(min_length=1, pattern=r"\S")
    judul: str = Field(min_length=1)
    paragraf: list[str] = Field(min_length=1)


def baca_naskah(berkas: Path) -> Naskah | None:
    """Naskah terpasang, atau `None` bila berkasnya belum ada.

    Berkas yang ada tetapi rusak melempar `ValueError` — diam-diam menutup
    persetujuan bagi semua orang karena satu koma yang hilang adalah kegagalan
    yang tidak terlihat siapa pun.
    """
    if not berkas.is_file():
        return None
    try:
        return Naskah.model_validate(json.loads(berkas.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, ValidationError) as galat:
        raise ValueError(f"berkas naskah persetujuan rusak: {berkas.name}") from galat


class PermintaanProfil(BaseModel):
    """Badan `PUT /saya/profil` — tepat enam isian FR-A02."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    jabatan: str
    masa_kerja: int
    jumlah_rombel: int
    jumlah_ptk: int
    jalur_akreditasi: JalurAkreditasi
    wilayah: str


class PermintaanPrioritas(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    kategori: list[KategoriMasalah]


class PermintaanPersetujuan(BaseModel):
    """Dua bentuk saja: memutus (`versi_naskah` + `disetujui`) atau `cabut: true`."""

    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    versi_naskah: str | None = None
    disetujui: bool | None = None
    cabut: bool | None = None

    @model_validator(mode="after")
    def _satu_bentuk(self) -> PermintaanPersetujuan:
        memutus = self.versi_naskah is not None and self.disetujui is not None
        if self.cabut is True and self.versi_naskah is None and self.disetujui is None:
            return self
        if memutus and self.cabut is None:
            return self
        raise ValueError("bentuk persetujuan tidak dikenal")


def profil_sah(pemilik: str, badan: Any) -> BarisProfil:
    """Validasi lewat `ProfilSekolah`; `ValueError` bila tidak sah."""
    try:
        permintaan = PermintaanProfil.model_validate(badan)
        profil = ProfilSekolah(id_pengguna=pemilik, **permintaan.model_dump())
    except ValidationError as galat:
        raise ValueError("profil tidak sah") from galat
    return BarisProfil(
        jabatan=profil.jabatan,
        masa_kerja=profil.masa_kerja,
        jumlah_rombel=profil.jumlah_rombel,
        jumlah_ptk=profil.jumlah_ptk,
        jalur_akreditasi=profil.jalur_akreditasi.value,
        wilayah=profil.wilayah,
    )


def prioritas_sah(pemilik: str, badan: Any) -> tuple[str, ...]:
    """Validasi lewat `PrioritasManajerial`; urutannya pilihan pengguna."""
    try:
        permintaan = PermintaanPrioritas.model_validate(badan)
        prioritas = PrioritasManajerial(id_pengguna=pemilik, kategori=tuple(permintaan.kategori))
    except ValidationError as galat:
        raise ValueError("prioritas tidak sah") from galat
    return tuple(k.value for k in prioritas.kategori)


async def ringkasan(simpan: PenyimpanPengguna, pemilik: str) -> dict[str, Any]:
    """Bentuk tanggapan bersama keempat rute — D-14 Bagian 4.5."""
    profil = await simpan.baca_profil(pemilik)
    prioritas = await simpan.baca_prioritas(pemilik)
    return {
        "profil": None
        if profil is None
        else {
            "jabatan": profil.isi.jabatan,
            "masa_kerja": profil.isi.masa_kerja,
            "jumlah_rombel": profil.isi.jumlah_rombel,
            "jumlah_ptk": profil.isi.jumlah_ptk,
            "jalur_akreditasi": profil.isi.jalur_akreditasi,
            "wilayah": profil.isi.wilayah,
        },
        "prioritas": list(prioritas),
        "persetujuan": (await keadaan_persetujuan(simpan, pemilik)).value,
    }


async def keadaan_persetujuan(simpan: PenyimpanPengguna, pemilik: str) -> KeadaanPersetujuan:
    """Keadaan dari catatan terbaru, lewat `KeadaanPersetujuan.dari` fitur 022 —
    satu jalur penafsiran, bukan dua."""
    baris = await simpan.baca_persetujuan(pemilik)
    if baris is None:
        return KeadaanPersetujuan.dari(None)
    return KeadaanPersetujuan.dari(
        CatatanPersetujuan(
            id_pengguna=pemilik,
            jenis=JenisPersetujuan.PENELITIAN,
            versi_naskah=baris.versi_naskah,
            disetujui=baris.disetujui,
            tanggal=baris.tanggal,
            dicabut_pada=baris.dicabut_pada,
        )
    )


async def putuskan_persetujuan(
    simpan: PenyimpanPengguna,
    pemilik: str,
    badan: Any,
    *,
    versi_naskah: str | None,
    sekarang: datetime,
) -> None:
    """Catat atau cabut; `ValueError` bila tidak dapat — termasuk tanpa naskah."""
    try:
        permintaan = PermintaanPersetujuan.model_validate(badan)
    except ValidationError as galat:
        raise ValueError("persetujuan tidak sah") from galat
    if permintaan.cabut:
        if not await simpan.cabut_persetujuan(pemilik, sekarang=sekarang):
            raise ValueError("tidak ada persetujuan yang dapat dicabut")
        return
    if versi_naskah is None or permintaan.versi_naskah != versi_naskah:
        raise ValueError("versi naskah tidak cocok dengan naskah terpasang")
    await simpan.catat_persetujuan(
        pemilik,
        versi_naskah=versi_naskah,
        disetujui=bool(permintaan.disetujui),
        sekarang=sekarang,
    )
