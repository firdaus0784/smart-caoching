"""Pelaksana `make check` — V-01 s.d. V-06, R-14.

Enam gerbang `docs/D12.md` Bagian 5, dijalankan berurutan dan dilaporkan
seluruhnya. Pelaksana tidak berhenti pada kegagalan pertama: mengetahui
seluruh yang salah dalam satu jalan lebih berguna daripada mengetahui yang
pertama, dan gerbang yang menyembunyikan sisanya mendorong perbaikan
sepotong-sepotong.

Catatan atas V-02. `docs/D12.md` menulis "tidak ada pelanggaran C-01 s.d.
C-07" karena bagian itu disusun sebelum D-13 terbit dan sebelum C-17 s.d. C-20
ada. Yang dijalankan di sini adalah **seluruh** C-01 s.d. C-20, mengikuti
`constitution.md` dan `AGENTS.md`. Pembaruan D-12 dikerjakan pada tugas E-3
dan dicatat sebagai temuan AK-12.

Catatan kinerja yang diketahui: rangkaian uji berjalan dua kali — sekali pada
V-01, sekali lagi lewat pemeriksa C-11 di dalam V-02. Menghilangkan
pengulangan itu menuntut penyaluran keadaan antar-gerbang, dan pada ukuran
sekarang biayanya tidak sebanding dengan kerumitannya.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from perkakas.kepatuhan.jalankan import Keadaan, susun_laporan
from perkakas.pemeriksa.ast_aturan import Temuan
from perkakas.pemeriksa.cakupan import periksa_cakupan
from perkakas.pemeriksa.gerbang_v import (
    periksa_keamanan_statis,
    periksa_ketertelusuran,
    periksa_rahasia,
)
from perkakas.pemeriksa.ketergantungan import periksa_ketergantungan
from perkakas.pemeriksa.ketergantungan_sistem import periksa_ketergantungan_sistem
from perkakas.pemeriksa.konsistensi_dokumen import (
    periksa_kode_menggantung,
    periksa_konsistensi_dokumen,
)
from perkakas.pemeriksa.perintah_selaras import periksa_perintah_selaras
from perkakas.pemeriksa.placeholder import periksa_placeholder


@dataclass(frozen=True)
class HasilGerbang:
    kode: str
    judul: str
    temuan: list[Temuan]
    catatan: str = ""

    @property
    def lulus(self) -> bool:
        return not self.temuan


def _v01(akar: Path) -> HasilGerbang:
    """Seluruh uji lulus; cakupan tidak turun."""
    hasil = subprocess.run(
        ["uv", "run", "pytest", "-q"],
        cwd=akar,
        capture_output=True,
        text=True,
        check=False,
    )
    temuan: list[Temuan] = []
    if hasil.returncode != 0:
        ringkas = hasil.stdout.strip().splitlines()[-1:] or ["uji gagal"]
        temuan.append(Temuan(akar, 0, f"rangkaian uji gagal: {ringkas[0]}"))
    temuan.extend(periksa_cakupan(akar))
    return HasilGerbang("V-01", "seluruh uji lulus; cakupan tidak turun", temuan)


def _v02(akar: Path) -> HasilGerbang:
    """Tidak ada pelanggaran pasal konstitusi."""
    laporan = susun_laporan(akar)
    temuan = [
        Temuan(akar, 0, f"{b.kode}: {b.keterangan}") for b in laporan if b.keadaan is Keadaan.GAGAL
    ]
    belum = sum(1 for b in laporan if b.keadaan is Keadaan.BELUM)
    return HasilGerbang(
        "V-02",
        "tidak ada pelanggaran C-01 s.d. C-20",
        temuan,
        catatan=f"{belum} pasal belum dapat diperiksa — lihat `make compliance`",
    )


def _v03(akar: Path) -> HasilGerbang:
    """Ketertelusuran ke kode kebutuhan dan keselarasan dokumen.

    Dua pemeriksa terakhir ditambahkan fitur 014. Sampai saat itu keselarasan
    antardokumen hanya tertangkap pembacaan manusia, dan TK-45 menunjukkan
    batasnya: register `docs/D00.md` Bagian 2 tertinggal pada tujuh dokumen
    tanpa satu pun aturan dilanggar.
    """
    temuan = [
        *periksa_ketertelusuran(akar),
        *periksa_placeholder(akar / "AGENTS.md"),
        *periksa_perintah_selaras(akar),
        *periksa_konsistensi_dokumen(akar),
        *periksa_kode_menggantung(akar),
    ]
    return HasilGerbang("V-03", "ketertelusuran dan keselarasan dokumen", temuan)


def _v04(akar: Path) -> HasilGerbang:
    """Dua pemeriksa, bukan satu — R-13, KB-017.

    `periksa_ketergantungan` menutup pohon paket Python; mesin OCR berada di
    luarnya karena ia program sistem. Yang kedua membawa catatan, bukan hanya
    temuan: lingkungan tanpa mesin terpasang bukan pelanggaran, tetapi juga
    bukan lulus, dan perbedaan itu wajib terbaca pada laporan.
    """
    sistem = periksa_ketergantungan_sistem(akar)
    return HasilGerbang(
        "V-04",
        "tidak ada ketergantungan baru tanpa persetujuan",
        [*periksa_ketergantungan(akar), *sistem.temuan],
        catatan="" if sistem.terperiksa else sistem.catatan,
    )


def _v05(akar: Path) -> HasilGerbang:
    return HasilGerbang("V-05", "pemindaian keamanan statis bersih", periksa_keamanan_statis(akar))


def _v06(akar: Path) -> HasilGerbang:
    return HasilGerbang("V-06", "tanpa rahasia, kunci, atau data pribadi", periksa_rahasia(akar))


GERBANG = (_v01, _v02, _v03, _v04, _v05, _v06)


def jalankan_semua(akar: Path) -> list[HasilGerbang]:
    return [gerbang(akar) for gerbang in GERBANG]


def main() -> int:
    akar = Path(__file__).resolve().parents[2]
    hasil = jalankan_semua(akar)

    for gerbang in hasil:
        tanda = "lulus" if gerbang.lulus else "GAGAL"
        print(f"{gerbang.kode}  {tanda:<5}  {gerbang.judul}")
        for temuan in gerbang.temuan[:10]:
            print(f"          {temuan}")
        if len(gerbang.temuan) > 10:
            print(f"          (dan {len(gerbang.temuan) - 10} temuan lagi)")
        if gerbang.catatan:
            print(f"          catatan: {gerbang.catatan}")

    gagal = [g.kode for g in hasil if not g.lulus]
    if gagal:
        print(f"\nmake check GAGAL pada: {', '.join(gagal)}")
        return 1

    print(f"\nmake check lulus — {len(hasil)} gerbang")
    return 0


if __name__ == "__main__":
    sys.exit(main())
