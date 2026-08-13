"""Ekspor telemetri — R-03, R-08, FR-J03.

FR-J03: *"Data telemetri dapat diekspor sebagai CSV/Parquet untuk analisis di
R/Python."*

## Separuh yang dibangun, dan separuh yang dinyatakan tertahan

**CSV dibangun** memakai `csv` pada pustaka baku — nol ketergantungan.

**Parquet tidak dibangun.** Ia menuntut `pyarrow`, yang belum ada pada
`ketergantungan-disetujui.toml`, dan C-12 tidak mengenal pengecualian. Yang
tertahan **dinyatakan** — `parquet_tertahan()` mengembalikan alasannya beserta
apa yang ditunggunya, alih-alih fungsi itu tidak ada sama sekali.

Perbedaannya bukan formalitas: fungsi yang tidak ada terbaca sebagai fitur yang
tidak pernah diminta, sedangkan alasan yang dapat dipanggil terbaca sebagai
utang yang dapat ditagih. Bentuk yang sama dengan `_MENUNGGU_L4` pada
`saring.py` (010) dan `_MENUNGGU_FITUR_020` pada validator (008).

## Kolom ekspor tidak memuat identitas

Berkas ekspor berpindah tangan — ke R, ke Python, ke lampiran surel. Ia tempat
paling mungkin data pribadi keluar dari sistem, dan justru di sana pemeriksaan
paling mudah terlupa.

Kolomnya karena itu **diturunkan dari bidang `Peristiwa`**, yang sejak
bentuknya tidak memiliki `id_pengguna`. Menuliskan daftar kolom sendiri akan
membuat ekspor dapat menambah kolom yang modelnya tidak punya.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Sequence
from io import StringIO

from src.telemetri.peristiwa import Peristiwa

KOLOM: tuple[str, ...] = tuple(Peristiwa.model_fields)
"""Kolom ekspor — **diturunkan dari model**, bukan ditulis ulang.

Daftar yang ditulis ulang dapat menambah kolom yang modelnya tidak punya, dan
kolom yang paling mungkin ditambahkan seseorang adalah `id_pengguna` — sebab
analisis terasa lebih mudah dengannya. Yang menutupnya bukan disiplin
melainkan penurunan ini.
"""

ALASAN_PARQUET_TERTAHAN = (
    "ekspor Parquet menuntut pyarrow, yang belum ada pada "
    "ketergantungan-disetujui.toml — menunggu keputusan C-12"
)
"""Alasan separuh FR-J03 belum dibangun, beserta apa yang ditunggunya.

Alasan yang tidak menyebut apa yang ditunggu adalah alasan yang tidak dapat
ditagih.
"""


def parquet_tertahan() -> str:
    """Mengapa ekspor Parquet belum ada — lihat uraian modul.

    Fungsi ini ada **justru agar ketiadaannya terbaca**. Ekspor Parquet yang
    hilang tanpa keterangan terbaca sebagai fitur yang tidak pernah diminta.
    """
    return ALASAN_PARQUET_TERTAHAN


def ke_csv(peristiwa: Sequence[Peristiwa] | Iterable[Peristiwa]) -> str:
    """Susun CSV dari peristiwa — FR-J03 separuh.

    `properti` ditulis sebagai JSON pada satu kolom: memekarkannya menjadi
    kolom-kolom akan membuat lebar berkas bergantung pada peristiwa mana yang
    kebetulan terekam, dan dua ekspor dari dua pekan tidak dapat ditumpuk.

    Waktu ditulis ISO-8601 berzona (KM-01). Analisis di R yang membaca waktu
    tanpa zona akan menafsirkannya sebagai waktu setempat mesin pembaca.
    """
    keluaran = StringIO()
    penulis = csv.writer(keluaran, lineterminator="\n")
    penulis.writerow(KOLOM)
    for satu in peristiwa:
        penulis.writerow(
            [
                satu.pseudonim,
                satu.jenis.value,
                satu.waktu.isoformat(),
                json.dumps(satu.properti, ensure_ascii=False, sort_keys=True),
                satu.versi_aplikasi,
                satu.versi_model,
            ]
        )
    return keluaran.getvalue()
