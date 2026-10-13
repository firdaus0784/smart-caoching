"""Perkakas pencarian korpus — T-7 fitur 039, K-7, P-1 A, R-08.

    python -m perkakas.pengambilan cari --kueri <teks> [--indeks utama|metadata]

**Satu sumber leksikal**, tanpa penyemat, tanpa model, tanpa jawaban. Ia ada
agar tim dapat memeriksa apakah pasal yang semestinya ditemukan memang
ditemukan sebelum *gold set* BT-35 dibekukan, dan agar dokumen yang perlu
diindeks ulang terlihat. Penggabungan hibrida tidak dipanggil: ADR-03 tetap
menolak pengambilan leksikal saja pada jalur penjawab.

**Satu peran per indeks**: indeks utama tersambung sebagai
`peran_pemanggil_llm`, indeks metadata sebagai `peran_penjawaban` — peran yang
sama dengan pemuat jalur penjawab, sehingga yang terlihat di sini adalah yang
terlihat oleh jalur itu. Kelayakan dibaca dari `src/api/penjawab_korpus.py`,
tidak ditulis ulang.

**Tanpa teks segmen** (R-08): keluarannya sidik, jumlah layak dan tak layak per
alasan, dokumen yang perlu diindeks ulang, lalu peringkat dengan skor,
dokumen, penanda, dan judul. Kueri tidak dikutip pada pesan galat. Perkakas
tidak menulis log.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Callable
from typing import Final, TextIO

from src.api.penjawab_korpus import bangun_muatan
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.korpus_penjawab import MuatanKorpus, PemuatKorpusPostgres
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN
from src.penyimpanan.sambungan import SambunganAktif
from src.rag.pengambilan.bm25 import SumberBM25
from src.rag.pengambilan.tetapan import JUMLAH_KANDIDAT_PER_SUMBER

PERAN_INDEKS: Final[dict[IndeksTujuan, str]] = {
    IndeksTujuan.UTAMA: "peran_pemanggil_llm",
    IndeksTujuan.METADATA: "peran_penjawaban",
}
"""Satu peran per indeks — sama dengan pemuat jalur penjawab."""

_KREDENSIAL: Final = {IndeksTujuan.UTAMA: PEMANGGIL_LLM, IndeksTujuan.METADATA: PENJAWABAN}
_KOSONG: Final = MuatanKorpus(sidik="-", baris=())


def _penghurai() -> argparse.ArgumentParser:
    penghurai = argparse.ArgumentParser(
        prog="python -m perkakas.pengambilan",
        description="Pencarian leksikal satu indeks atas korpus, tanpa teks segmen.",
    )
    sub = penghurai.add_subparsers(dest="perintah", required=True)
    cari = sub.add_parser("cari", help="peringkat segmen layak bagi sebuah kueri")
    cari.add_argument("--kueri", required=True)
    cari.add_argument(
        "--indeks", choices=[i.value for i in IndeksTujuan], default=IndeksTujuan.UTAMA.value
    )
    return penghurai


async def _cari(
    kueri: str, indeks: IndeksTujuan, sambung: Callable[[str], SambunganAktif], keluar: TextIO
) -> None:
    pemuat = PemuatKorpusPostgres(sambung(PERAN_INDEKS[indeks]))
    potret = await pemuat.muat(_KREDENSIAL[indeks], indeks)
    muatan = (
        bangun_muatan(potret, _KOSONG)
        if indeks is IndeksTujuan.UTAMA
        else bangun_muatan(_KOSONG, potret)
    )
    baris = {b.id_segmen: b for b in potret.baris}
    tak_layak = muatan.tak_layak[indeks]
    print(f"Indeks {indeks.value}, versi {indeks.value}:{potret.sidik}.", file=keluar)
    rincian = ", ".join(
        f"{a.value} {n}" for a, n in sorted(tak_layak.items(), key=lambda x: x[0].value)
    )
    print(
        f"Segmen layak: {len(potret.baris) - sum(tak_layak.values())}. "
        f"Tak layak: {sum(tak_layak.values())}{' — ' + rincian if rincian else ''}.",
        file=keluar,
    )
    if muatan.perlu_indeks_ulang:
        print(
            "Perlu diindeks ulang karena lisensinya kini tertutup: "
            + ", ".join(sorted(muatan.perlu_indeks_ulang))
            + ".",
            file=keluar,
        )
    hasil = await SumberBM25(muatan.indeks_leksikal[indeks]).cari(
        kueri, batas=JUMLAH_KANDIDAT_PER_SUMBER
    )
    print(f"Peringkat: {len(hasil.peringkat)}.", file=keluar)
    for urutan, kandidat in enumerate(hasil.peringkat, start=1):
        b = baris[kandidat.id_segmen]
        judul = b.metadata.judul if b.metadata is not None else "-"
        print(
            f"{urutan}. skor {kandidat.skor:.4f} | {b.id_dokumen} | {b.penanda_bagian} | {judul}",
            file=keluar,
        )


def utama(
    argv: list[str],
    *,
    sambung: Callable[[str], SambunganAktif],
    keluar: TextIO = sys.stdout,
    galat: TextIO = sys.stderr,
) -> int:
    """Titik masuk yang dapat diuji. Kode keluar: 0 berhasil, 1 ditolak
    peladen, 2 masukan tidak sah — sebelum menyambung."""
    try:
        argumen = _penghurai().parse_args(argv)
    except SystemExit as keluar_parser:
        return int(keluar_parser.code or 2)
    if not argumen.kueri.strip():
        print("Ditolak: kueri kosong.", file=galat)
        return 2
    try:
        asyncio.run(_cari(argumen.kueri, IndeksTujuan(argumen.indeks), sambung, keluar))
    except Exception as g:
        print(f"Ditolak peladen ({type(g).__name__}). Tidak ada yang berubah.", file=galat)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    import os

    from perkakas.ingesti import _SambunganPeran

    alamat = os.environ.get("PGHOST", "127.0.0.1"), int(os.environ.get("PGPORT", "5432"))
    raise SystemExit(utama(sys.argv[1:], sambung=lambda peran: _SambunganPeran(*alamat, peran)))
