"""Perkakas evaluasi pengambilan — T-7 fitur 040, R-01 s.d. R-08, K-7.

    python -m perkakas.evaluasi periksa --berkas <jalur>
    python -m perkakas.evaluasi bekukan --berkas <jalur> --versi <label> --pelaku <nama>
    python -m perkakas.evaluasi ukur    --berkas <jalur> --id-percobaan EXP-2026-nnn

**Berkas di luar repositori** (R-01, D-08 Bagian 5.3): jalur yang terurai ke
dalam pohon kerja ditolak sebelum dibaca.

**Peran pemuat fitur 039** (R-08): indeks utama sebagai `peran_pemanggil_llm`,
indeks metadata sebagai `peran_penjawaban`. Muatan dirakit `bangun_muatan` dan
sumbernya `SumberBM25` atas indeks leksikal utama — yang dilihat jalur
penjawab. Tanpa peran, hak, atau skema baru.

**Logbook repositori.** `bekukan` menulis satu baris L2; `ukur` satu baris L1
per putaran yang lolos pemeriksaan beku, termasuk yang gagal (R-06). Akar
logbook bukan argumen baris perintah: hanya uji dan naskah bukti yang
memanggil `utama(…, akar_logbook=…)` dengan akar sementara, agar pembekuan
rekaan tidak pernah sampai ke logbook yang tambah-saja.

**Tanpa teks** (R-07): keluaran, pesan galat, dan logbook menyebut pengenal
pertanyaan, dokumen, bagian, dan segmen saja. Perkakas tidak menulis log.

Kode keluar: 0 berhasil; 1 ditolak peladen; 2 masukan tidak sah — termasuk
belum beku dan komposisi menyimpang; 3 diukur dengan kebocoran indeks.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, TextIO

from src.api.penjawab_korpus import bangun_muatan
from src.kamus.segmen import IndeksTujuan
from src.logbook.versi import BELUM_BERLAKU
from src.penyimpanan.korpus_penjawab import MuatanKorpus, PemuatKorpusPostgres
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN
from src.penyimpanan.sambungan import SambunganAktif
from src.rag.evaluasi.gold_set import KOMPOSISI_D08, GalatBerkas, GoldSet, urai
from src.rag.evaluasi.jejak import (
    GalatPembekuan,
    VersiGoldSet,
    bekukan,
    catat_putaran,
    hasil_l1,
    id_percobaan_terpakai,
    konfigurasi_l1,
    pembekuan,
    pembukaan_berikutnya,
)
from src.rag.evaluasi.kunci import SegmenDikenal, periksa_korpus
from src.rag.evaluasi.metrik import K_PRESISI, K_RECALL, Nilai, TigaMetrik
from src.rag.evaluasi.pengukur import HasilPutaran, ukur
from src.rag.pengambilan.bm25 import SumberBM25
from src.rag.pengambilan.tetapan import JUMLAH_KANDIDAT_PER_SUMBER

from perkakas.pengambilan import PERAN_INDEKS

AKAR_REPO: Final = Path(__file__).resolve().parents[1]
AKAR_LOGBOOK: Final = AKAR_REPO / "logbook"
TIDAK_TERBACA: Final = "tidak-terbaca"
_ID_PERCOBAAN: Final = re.compile(r"EXP-\d{4}-\d{3}")
_UTAMA, _METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA


class _Tolak(Exception):
    """Masukan tidak sah; pesannya tanpa teks pertanyaan."""


def versi_kode_git(akar: Path = AKAR_REPO) -> str:
    """Penanda commit; berakhiran `+ubahan` bila pohon kerja di luar `logbook/`
    berubah — versi kode yang tidak dapat diulang dinyatakan, bukan disamarkan."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=akar,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        ubah = subprocess.run(
            ["git", "status", "--porcelain", "--", ".", ":(exclude)logbook"],
            cwd=akar,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover - tanpa git
        return TIDAK_TERBACA
    return sha + ("+ubahan" if ubah else "")


def _penghurai() -> argparse.ArgumentParser:
    penghurai = argparse.ArgumentParser(
        prog="python -m perkakas.evaluasi",
        description="Pemeriksaan, pembekuan, dan pengukuran gold set U3, tanpa teks.",
    )
    sub = penghurai.add_subparsers(dest="perintah", required=True)
    periksa = sub.add_parser("periksa", help="bentuk dan kunci terhadap korpus")
    periksa.add_argument("--berkas", required=True)
    beku = sub.add_parser("bekukan", help="catat sidik dan komposisi ke logbook L2")
    beku.add_argument("--berkas", required=True)
    beku.add_argument("--versi", required=True)
    beku.add_argument("--pelaku", required=True)
    ukur_ = sub.add_parser("ukur", help="satu putaran U3 atas gold set beku")
    ukur_.add_argument("--berkas", required=True)
    ukur_.add_argument("--id-percobaan", required=True)
    return penghurai


def _baca(jalur: str, akar_repo: Path) -> GoldSet:
    nyata = Path(jalur).resolve()
    if nyata.is_relative_to(akar_repo.resolve()):
        raise _Tolak(
            "berkas gold set berada di dalam repositori; "
            "D-08 Bagian 5.3 menuntutnya disimpan di luar"
        )
    try:
        teks = nyata.read_bytes().decode("utf-8-sig")
    except OSError as g:
        raise _Tolak(f"berkas tidak dapat dibaca ({type(g).__name__})") from g
    except UnicodeDecodeError as g:
        raise _Tolak("berkas bukan UTF-8") from g
    try:
        return urai(teks)
    except GalatBerkas as g:
        raise _Tolak("berkas tidak sah:\n" + str(g)) from g


async def _muat(sambung: Callable[[str], SambunganAktif]) -> tuple[MuatanKorpus, MuatanKorpus]:
    utama = await PemuatKorpusPostgres(sambung(PERAN_INDEKS[_UTAMA])).muat(PEMANGGIL_LLM, _UTAMA)
    metadata = await PemuatKorpusPostgres(sambung(PERAN_INDEKS[_METADATA])).muat(
        PENJAWABAN, _METADATA
    )
    return utama, metadata


def _segmen(*muatan: MuatanKorpus) -> dict[str, SegmenDikenal]:
    return {
        b.id_segmen: SegmenDikenal(b.id_segmen, b.id_dokumen, b.penanda_bagian)
        for m in muatan
        for b in m.baris
    }


def _ringkas_berkas(gold: GoldSet, keluar: TextIO) -> None:
    print(f"Sidik: {gold.sidik}.", file=keluar)
    print(
        f"Pertanyaan: {len(gold.pertanyaan)}; bernomor regulasi: "
        f"{gold.jumlah_bernomor_regulasi()}.",
        file=keluar,
    )
    ada = gold.komposisi()
    print(
        "Komposisi per jenis (ada/D-08 Bagian 5.1): "
        + ", ".join(f"{j.value} {ada[j]}/{n}" for j, n in KOMPOSISI_D08.items())
        + ".",
        file=keluar,
    )
    print(
        "Komposisi per kategori: "
        + ", ".join(f"{k} {n}" for k, n in gold.komposisi_kategori().items())
        + ".",
        file=keluar,
    )


async def _periksa_korpus(
    gold: GoldSet, sambung: Callable[[str], SambunganAktif], keluar: TextIO
) -> bool:
    utama, metadata = await _muat(sambung)
    temuan = periksa_korpus(gold, _segmen(utama, metadata).values())
    if temuan:
        print(f"Kunci bermasalah: {len(temuan)}.", file=keluar)
        for t in temuan:
            print(f"- {t}", file=keluar)
    return not temuan


def _periksa(gold: GoldSet, sambung: Callable[[str], SambunganAktif], keluar: TextIO) -> int:
    _ringkas_berkas(gold, keluar)
    if not asyncio.run(_periksa_korpus(gold, sambung, keluar)):
        return 2
    menyimpang = gold.penyimpangan()
    print(
        "Dapat dibekukan: "
        + ("tidak — komposisi menyimpang dari D-08 Bagian 5.1." if menyimpang else "ya."),
        file=keluar,
    )
    return 0


def _bekukan(
    gold: GoldSet,
    versi: str,
    pelaku: str,
    sambung: Callable[[str], SambunganAktif],
    akar_logbook: Path,
    keluar: TextIO,
) -> int:
    _ringkas_berkas(gold, keluar)
    if not asyncio.run(_periksa_korpus(gold, sambung, keluar)):
        raise _Tolak("kunci tidak ditemukan pada korpus; tidak ada yang dibekukan")
    try:
        v = bekukan(akar_logbook, gold, versi=versi, pelaku=pelaku, sekarang=datetime.now(UTC))
    except GalatPembekuan as g:
        raise _Tolak(str(g)) from g
    print(
        f"Dibekukan sebagai versi {v.versi}, sidik {v.sidik}. Satu baris L2 ditulis.", file=keluar
    )
    return 0


def _rinci(nama: str, n: Nilai, *, hitungan: bool = False) -> str:
    if not n.terhitung:
        return f"{nama}: {n.persen()}"
    if hitungan:
        return f"{nama}: {n.persen()} — {n.pembilang} dari {n.penyebut}"
    return f"{nama}: {n.persen()} — {n.pembilang} atas {n.penyebut} pertanyaan"


def _tiga(label: str, t: TigaMetrik) -> str:
    return (
        f"{label}: Recall@{K_RECALL} {t.recall_8.persen()} ({t.recall_8.penyebut}), "
        f"MRR {t.mrr.persen()}, Precision@{K_PRESISI} {t.presisi_5.persen()}"
    )


def _laporan(
    putaran: HasilPutaran, beku: VersiGoldSet, pembukaan: int, versi_indeks: str, keluar: TextIO
) -> None:
    k = putaran.konfigurasi
    r = putaran.ringkasan
    print(
        f"Gold set {beku.versi}, sidik {beku.sidik}, pembukaan ke-{pembukaan} (AP-05).",
        file=keluar,
    )
    print(
        f"Konfigurasi: sumber {k.sumber}, indeks {k.indeks.value}, kedalaman {k.kedalaman}; "
        f"penyemat {k.versi_penyemat or 'tidak dipakai'}.",
        file=keluar,
    )
    print(f"Versi indeks: {versi_indeks}.", file=keluar)
    print(f"Putusan: {putaran.putusan.value}.", file=keluar)
    print(_rinci(f"Recall@{K_RECALL} (jenis A)", r.utama.recall_8, hitungan=True), file=keluar)
    print(_rinci("MRR (jenis A)", r.utama.mrr), file=keluar)
    print(_rinci(f"Precision@{K_PRESISI} (jenis A, batas bawah)", r.utama.presisi_5), file=keluar)
    print(
        _rinci("Recall bernomor regulasi (jenis A)", r.recall_bernomor, hitungan=True),
        file=keluar,
    )
    for j, t in r.per_jenis.items():
        print(_tiga(f"Jenis {j.value}", t), file=keluar)
    for kategori, t in r.per_kategori.items():
        print(_tiga(f"Kategori {kategori} (jenis A)", t), file=keluar)
    print(
        f"Kebocoran indeks: {len(putaran.kebocoran)} segmen"
        + (f" — {', '.join(putaran.kebocoran)}" if putaran.kebocoran else "")
        + ".",
        file=keluar,
    )
    print(f"Pertanyaan gagal: {len(putaran.gagal)}.", file=keluar)
    for h in putaran.gagal:
        for luput in h.luput:
            print(
                f"- {h.nilai.id} ({h.nilai.jenis.value}): kunci {luput.urutan} "
                f"{luput.kunci.dokumen}, {luput.kunci.bagian} — {luput.sebab.value}",
                file=keluar,
            )


async def _jalankan_putaran(
    gold: GoldSet, sambung: Callable[[str], SambunganAktif]
) -> tuple[HasilPutaran, str]:
    utama, metadata = await _muat(sambung)
    muatan = bangun_muatan(utama, metadata)
    putaran = await ukur(
        gold,
        SumberBM25(muatan.indeks_leksikal[_UTAMA]),
        segmen=_segmen(utama, metadata),
        layak=muatan.layak_utama,
        id_metadata=frozenset(b.id_segmen for b in metadata.baris),
    )
    return putaran, muatan.versi_indeks


def _ukur(
    gold: GoldSet,
    id_percobaan: str,
    sambung: Callable[[str], SambunganAktif],
    akar_logbook: Path,
    versi_kode: Callable[[], str],
    keluar: TextIO,
    galat: TextIO,
) -> int:
    if not _ID_PERCOBAAN.fullmatch(id_percobaan):
        raise _Tolak("id percobaan wajib berbentuk EXP-2026-nnn (D-10 Bagian 3)")
    beku = pembekuan(akar_logbook, gold.sidik)
    if beku is None:
        raise _Tolak(
            "gold set ini belum beku; bekukan lebih dulu (D-08 Bagian 5.2). Tidak ada yang dicatat"
        )
    if id_percobaan_terpakai(akar_logbook, id_percobaan):
        raise _Tolak(f"{id_percobaan} sudah tercatat pada L1")
    pembukaan = pembukaan_berikutnya(akar_logbook, beku.sidik)
    kode = versi_kode()
    mulai = time.monotonic()
    try:
        putaran, versi_indeks = asyncio.run(_jalankan_putaran(gold, sambung))
    except Exception as g:
        catat_putaran(
            akar_logbook,
            id_percobaan=id_percobaan,
            beku=beku,
            versi_kode=kode,
            versi_indeks=TIDAK_TERBACA,
            versi_model=BELUM_BERLAKU,
            konfigurasi={
                "sumber": "bm25",
                "indeks": _UTAMA.value,
                "kedalaman": JUMLAH_KANDIDAT_PER_SUMBER,
                "versi_penyemat": None,
                "k_recall": K_RECALL,
                "k_presisi": K_PRESISI,
            },
            hasil={"putusan": "TIDAK_DIUKUR"},
            status="gagal",
            catatan=f"ditolak peladen atau pemuatan gagal ({type(g).__name__})",
            durasi_detik=round(time.monotonic() - mulai),
        )
        print(
            f"Ditolak peladen ({type(g).__name__}). Putaran tercatat gagal pada L1 "
            f"sebagai {id_percobaan}.",
            file=galat,
        )
        return 1
    bocor = bool(putaran.kebocoran)
    catat_putaran(
        akar_logbook,
        id_percobaan=id_percobaan,
        beku=beku,
        versi_kode=kode,
        versi_indeks=versi_indeks,
        versi_model=putaran.konfigurasi.versi_penyemat or BELUM_BERLAKU,
        konfigurasi=konfigurasi_l1(putaran),
        hasil=hasil_l1(putaran),
        status="gagal" if bocor else "berhasil",
        catatan=(
            f"kebocoran indeks {len(putaran.kebocoran)} segmen: segmen indeks metadata "
            "di antara kandidat penyusunan (KL-01)"
            if bocor
            else ""
        ),
        durasi_detik=round(time.monotonic() - mulai),
    )
    _laporan(putaran, beku, pembukaan, versi_indeks, keluar)
    print(
        f"Tercatat pada L1 sebagai {id_percobaan} ({'gagal' if bocor else 'berhasil'}).",
        file=keluar,
    )
    return 3 if bocor else 0


def utama(
    argv: list[str],
    *,
    sambung: Callable[[str], SambunganAktif],
    keluar: TextIO = sys.stdout,
    galat: TextIO = sys.stderr,
    akar_logbook: Path = AKAR_LOGBOOK,
    akar_repo: Path = AKAR_REPO,
    versi_kode: Callable[[], str] = versi_kode_git,
) -> int:
    """Titik masuk yang dapat diuji. Kode keluar pada uraian modul."""
    try:
        argumen = _penghurai().parse_args(argv)
    except SystemExit as keluar_parser:
        return int(keluar_parser.code or 2)
    try:
        gold = _baca(argumen.berkas, akar_repo)
        if argumen.perintah == "periksa":
            return _periksa(gold, sambung, keluar)
        if argumen.perintah == "bekukan":
            return _bekukan(gold, argumen.versi, argumen.pelaku, sambung, akar_logbook, keluar)
        return _ukur(gold, argumen.id_percobaan, sambung, akar_logbook, versi_kode, keluar, galat)
    except _Tolak as g:
        print(f"Ditolak: {g}.", file=galat)
        return 2
    except Exception as g:
        print(f"Ditolak peladen ({type(g).__name__}). Tidak ada yang berubah.", file=galat)
        return 1


if __name__ == "__main__":  # pragma: no cover
    import os

    from perkakas.ingesti import _SambunganPeran

    alamat = os.environ.get("PGHOST", "127.0.0.1"), int(os.environ.get("PGPORT", "5432"))
    raise SystemExit(utama(sys.argv[1:], sambung=lambda peran: _SambunganPeran(*alamat, peran)))
