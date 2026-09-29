"""Galat lapisan HTTP berbentuk D-14 Bagian 4.2 — T-5 fitur 028, R-14, TK-66.

Sejak fitur 023 peladen mengembalikan `{"pesan": …}`: tanpa kode, tanpa
`id_jejak`. Uji fitur 023 memeriksa isi pesannya, bukan bentuknya, sehingga
selisihnya dengan D-14 tidak pernah menjatuhkan gerbang (TK-66).

## Tipe bentuknya tidak ditulis ulang di sini

`KodeGalat` dan `TanggapanGalat` sudah ada pada `src/llm/galat.py` sejak fitur
001, lengkap dengan penolakan kalimat lebih dari dua puluh kata (C-13).
BT-69 merencanakan pemindahannya ke modul bersama pada fitur 009, dan itu tidak
pernah terjadi. Memindahkannya sekarang mengubah `src/llm/`, yang R-11 fitur
028 larang; menulisnya ulang di sini mengulang kekeliruan `IndeksTujuan` yang
pernah ditulis dua kali. Modul ini karena itu **memakainya** — tepi
`api → llm` sah (`AGENTS.md`) — dan BT-69 tetap terbuka.

## Log operasional

Setiap galat mencatat satu baris pada logger `smart_coaching.operasional`:
`id_jejak`, kode, rute, dan **nama kelas** sebabnya. Pesan pengecualian tidak
pernah ditulis: ia dapat memuat pertanyaan, dan pertanyaan dapat memuat data
pribadi. Log operasional terpisah dari telemetri penelitian (AP-04 D-04).
"""

from __future__ import annotations

import logging
import uuid

from fastapi.responses import JSONResponse

from src.llm.galat import KodeGalat, TanggapanGalat

LOG_OPERASIONAL = logging.getLogger("smart_coaching.operasional")


def id_jejak_baru() -> str:
    """Bentuk yang sama dengan `GalatLayananModel.id_jejak` — satu pola jejak."""
    return f"trc_{uuid.uuid4().hex[:12]}"


def tanggapan_galat(
    status: int,
    kode: KodeGalat,
    pesan_pengguna: str,
    *,
    rute: str,
    sebab: BaseException | None = None,
    id_jejak: str | None = None,
) -> JSONResponse:
    """Susun badan `{"galat": {…}}` dan catat jejaknya ke log operasional.

    `pesan_pengguna` wajib menunjuk tetapan `PESAN_*` — pemeriksa C-13 Aturan 2
    menolak untai harfiah pada argumen ini.
    """
    jejak = id_jejak or id_jejak_baru()
    LOG_OPERASIONAL.warning(
        "galat %s kode=%s status=%d rute=%s sebab=%s",
        jejak,
        kode.value,
        status,
        rute,
        type(sebab).__name__ if sebab is not None else "-",
    )
    badan = TanggapanGalat.susun(kode, pesan_pengguna, jejak)
    return JSONResponse(status_code=status, content=badan.model_dump(mode="json"))
