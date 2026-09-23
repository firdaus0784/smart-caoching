"""Bentuk catatan versi artefak L2 — R-02 fitur 026, C-09, `docs/D10.md` Bagian 4.

D-10 Bagian 4 menetapkan **apa** yang dicatat bagi tiap artefak. Modul ini
memberi bentuk kepada dua barisnya yang berlaku bagi penyematan korpus:

| Artefak | Yang dicatat |
|---|---|
| Model sematan | Nama dan versi |
| Indeks | Nomor versi, tanggal pembangunan, jumlah segmen, komposisi sumber |

**Bertipe, bukan pemetaan bebas.** Alasannya sama dengan `tambah_percobaan`
yang menerima `Versi`: keterangan yang luput karena lupa tertangkap **saat
memanggil**, bukan saat seseorang membaca berkasnya berbulan kemudian dan
menemukan satu kolom kosong tanpa cara mengetahui apa yang seharusnya di sana.

## Mengapa nama model disimpan sebagai untai, bukan `VersiPenyemat`

`VersiPenyemat` tinggal di `src/llm/sematan.py`. `src/logbook/` adalah lapisan
terbuka yang diimpor lima lapisan lain, dan membuatnya bergantung pada `llm`
menjadikan dua lapisan terbuka saling bergantung — arah yang tidak dinyatakan
`AGENTS.md` dan tidak perlu ada. Pemanggil di `src/ingest/` yang memetakannya,
satu tempat.

## Komposisi yang tidak menjumlah adalah komposisi yang salah

Ia tidak menghasilkan galat pada siapa pun. Ia menghasilkan catatan percobaan
yang dua angkanya bertentangan, dan yang membacanya tidak punya cara
mengetahui mana yang benar. Karena itu penjumlahannya dijaga tipenya, bukan
diperiksa saat dibaca.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class KomposisiSumber(BaseModel):
    """Berapa segmen berasal dari satu sumber — bagian "komposisi sumber" D-10."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    label: str = Field(min_length=1)
    jumlah: int = Field(ge=0)


class VersiIndeks(BaseModel):
    """Satu pembangunan indeks, beserta model yang menyematkannya.

    Seluruh bidang wajib dan tanpa nilai baku. Nilai baku pada salah satunya
    menghasilkan catatan yang **tampak lengkap** sementara satu keterangan
    dikarang.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    artefak: Literal["indeks"] = "indeks"
    """Penanda jenis artefak pada baris L2 — D-10 Bagian 4 memuat sepuluh
    jenis, dan baris tanpa penanda tidak dapat disaring dari sembilan lainnya."""

    versi_indeks: str = Field(min_length=1)
    dibangun_pada: datetime
    jumlah_segmen: int = Field(ge=0)
    komposisi_sumber: tuple[KomposisiSumber, ...]
    nama_model_sematan: str = Field(min_length=1)
    versi_model_sematan: str = Field(min_length=1)

    @model_validator(mode="after")
    def _waktu_berzona(self) -> VersiIndeks:
        """KM-01: waktu disimpan UTC.

        Waktu tanpa zona **tampak** benar dan menjadi salah saat dibaca di
        zona lain — dan catatan percobaan dibaca orang lain, di tempat lain.
        """
        if self.dibangun_pada.tzinfo is None:
            raise ValueError("dibangun_pada wajib berzona waktu — KM-01 menuntut UTC")
        return self

    @model_validator(mode="after")
    def _komposisi_menjumlah(self) -> VersiIndeks:
        label = [k.label for k in self.komposisi_sumber]
        if len(label) != len(set(label)):
            raise ValueError(
                "komposisi memuat label kembar; dua baris berlabel sama menjumlah "
                f"benar sambil menyatakan dua hal tentang satu sumber: {sorted(label)}"
            )
        total = sum(k.jumlah for k in self.komposisi_sumber)
        if total != self.jumlah_segmen:
            raise ValueError(
                f"komposisi menjumlah {total} sedangkan jumlah_segmen "
                f"{self.jumlah_segmen} — catatan yang dua angkanya bertentangan "
                "tidak dapat dibaca sebagai bukti apa pun"
            )
        return self


KeteranganArtefak = VersiIndeks
"""Jenis artefak yang sudah memiliki bentuknya.

D-10 Bagian 4 menyenaraikan sepuluh; satu yang dibutuhkan hari ini diberi
bentuk. Sisanya menyusul bersama fitur yang menghasilkannya — bentuk yang
dibuat kosong lebih dulu adalah bentuk yang ditebak, dan tebakan pada catatan
penelitian berakhir pada kolom yang tidak pernah diisi.
"""
