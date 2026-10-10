"""Enum putusan gerbang ingesti — FR-B05, FR-B07, ET-04; `docs/D14.md` Bagian 5.1.

Ditulis pada T-1 fitur 037. `jejak_area.putusan` membedakan dua peristiwa yang
arah pemindahannya sama: penolakan verifikator dan penarikan persetujuan
pemilik atas dokumen yang masih di karantina — keduanya `karantina → karantina`.
Keadaan gerbang diturunkan dari jejak ini (P-1 A), sehingga perbedaannya wajib
tercatat, bukan disimpulkan.

Nilainya milik D-14. `src/ingest/` memutuskannya dan `src/penyimpanan/`
menyimpannya; mengubah daftar nilai adalah perubahan versi kamus (KM-04), bukan
perubahan kode (AG-04).
"""

from __future__ import annotations

from enum import Enum


class PutusanGerbang(Enum):
    """Tiga putusan yang menulis jejak area. Menerima dokumen bukan putusan:
    ia tidak memindahkan apa pun dan tercatat pada penerimaan."""

    SETUJUI = "setujui"
    TOLAK = "tolak"
    CABUT_PERSETUJUAN = "cabut_persetujuan"
