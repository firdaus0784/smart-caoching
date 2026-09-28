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

import gzip
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from perkakas.kepatuhan.jalankan import Keadaan, susun_laporan
from perkakas.pemeriksa.arah_arsitektur import periksa_arah_arsitektur
from perkakas.pemeriksa.ast_aturan import Temuan
from perkakas.pemeriksa.cakupan import periksa_cakupan
from perkakas.pemeriksa.gerbang_v import (
    periksa_keamanan_statis,
    periksa_ketertelusuran,
    periksa_rahasia,
)
from perkakas.pemeriksa.hasil_jalur import periksa_hasil_jalur
from perkakas.pemeriksa.ketergantungan import periksa_ketergantungan
from perkakas.pemeriksa.ketergantungan_npm import periksa_ketergantungan_npm
from perkakas.pemeriksa.ketergantungan_sistem import periksa_ketergantungan_sistem
from perkakas.pemeriksa.konsistensi_dokumen import (
    periksa_kode_menggantung,
    periksa_konsistensi_dokumen,
    periksa_status_gerbang,
)
from perkakas.pemeriksa.kontrak_web import periksa_kontrak_web
from perkakas.pemeriksa.perintah_selaras import periksa_perintah_selaras
from perkakas.pemeriksa.placeholder import periksa_placeholder
from perkakas.pemeriksa.rute_terdaftar import periksa_rute_terdaftar


@dataclass(frozen=True)
class HasilGerbang:
    kode: str
    judul: str
    temuan: list[Temuan]
    catatan: str = ""

    @property
    def lulus(self) -> bool:
        return not self.temuan


_BARIS_SEBAB = re.compile(r"error TS\d+|\bFAIL\b|\d+ failed")


def periksa_web(akar: Path, *, npm: str | None = None) -> list[Temuan]:
    """Tipe dan uji `web/` — fitur 027 T-2, R-19.

    Tanpa Node, gerbang **gagal**, bukan dilewati: sejajar keputusan 12
    September atas PostgreSQL. Gerbang yang lulus tanpa melihat `web/` adalah
    laporan palsu (TA-01), dan mesin tanpa Node tidak melihatnya.

    Pesan membawa baris sebab — galat `tsc` atau ringkasan `vitest` — agar
    yang membaca laporan tahu *mengapa* merah, bukan hanya bahwa merah.
    """
    web = akar / "web"
    if not (web / "node_modules").is_dir():
        return [Temuan(web, 0, "web/node_modules tidak ada — jalankan `make setup`")]
    npm = npm or shutil.which("npm")
    if npm is None:
        return [
            Temuan(
                web,
                0,
                "npm tidak ditemukan — pasang Node.js 22 beserta npm, lalu jalankan `make setup`",
            )
        ]
    try:
        hasil = subprocess.run(
            [npm, "--prefix", str(web), "run", "periksa"],
            cwd=akar,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return [Temuan(web, 0, "pemeriksaan web/ melewati 600 detik dan dihentikan")]
    if hasil.returncode != 0:
        baris = [b.strip() for b in (hasil.stdout + hasil.stderr).splitlines() if b.strip()]
        sebab = [b for b in baris if _BARIS_SEBAB.search(b)][:5] or baris[-1:] or ["tanpa keluaran"]
        return [Temuan(web, 0, "tipe atau uji web/ gagal: " + " | ".join(sebab))]

    # T-6, R-14: anggaran muat diperiksa atas hasil build sungguhan.
    try:
        build = subprocess.run(
            [npm, "--prefix", str(web), "run", "build"],
            cwd=akar,
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return [Temuan(web, 0, "build web/ melewati 600 detik dan dihentikan")]
    if build.returncode != 0:
        keluaran = _ANSI.sub("", build.stdout + build.stderr)
        baris_build = [b.strip() for b in keluaran.splitlines() if b.strip()]
        # Vite menulis "error during build:", lalu "Build failed with N
        # error", baru sebabnya — `[UNRESOLVED_IMPORT] Could not resolve …`.
        sebab_build = [b for b in baris_build if _SEBAB_BUILD.search(b)][:3]
        ringkas = " | ".join(sebab_build or baris_build[-1:] or ["tanpa keluaran"])
        return [Temuan(web, 0, f"build web/ gagal: {ringkas}")]
    return periksa_anggaran_muat(web / "dist")


_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_SEBAB_BUILD = re.compile(r"\[[A-Z_]+\]|Could not resolve|error TS\d+|SyntaxError")


ANGGARAN_MUAT = 150 * 1024
"""Anggaran muat awal, bait terkompresi — ukuran pengganti NFR-02 (R-14).

**Penetapan tim tanpa dasar literatur** (SI-01 pilihan kedua), `plan.md`
fitur 027 Bagian 5: diturunkan dari anggapan laju 3G sekitar 0,75 Mbit/s.
Anggapan itu **wajib diverifikasi** terhadap sinyal di lokus pilot sebelum
dipakai sebagai klaim kinerja.
"""

TINGKAT_MAMPAT = 6
"""Tingkat gzip yang lazim dipakai peladen. Tingkat 9 menghasilkan angka lebih
kecil daripada yang benar-benar dikirim, dan anggaran yang dihitung terlalu
murah hati bukan anggaran."""


def periksa_anggaran_muat(dist: Path, *, batas: int = ANGGARAN_MUAT) -> list[Temuan]:
    """Jumlah ukuran terkompresi **seluruh** berkas hasil build ≤ batas.

    Seluruhnya, bukan per berkas: dua berkas yang masing-masing di bawah batas
    tetap dimuat bersama. Service worker dan manifes ikut dihitung — lebih
    ketat daripada muat awal yang sebenarnya, dan kelonggaran yang keliru
    arahnya lebih mahal daripada yang ketat.
    """
    if not (dist / "index.html").is_file():
        return [Temuan(dist, 0, "hasil build tanpa index.html — anggaran muat tidak dapat diukur")]
    total = sum(
        len(gzip.compress(b.read_bytes(), compresslevel=TINGKAT_MAMPAT))
        for b in sorted(dist.rglob("*"))
        if b.is_file()
    )
    if total <= batas:
        return []
    return [
        Temuan(
            dist,
            0,
            f"muat awal {total} bait terkompresi melampaui anggaran {batas} bait (R-14, NFR-02)",
        )
    ]


def _v01(akar: Path) -> HasilGerbang:
    """Seluruh uji lulus; cakupan tidak turun; `web/` lulus tipe dan ujinya."""
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
    # `web/` sejak fitur 027 (R-19). Sebelumnya V-01 hanya menjalankan pytest,
    # dan frontend akan lolos gerbang tanpa satu baris pun diperiksa.
    temuan.extend(periksa_web(akar))
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

    Pemeriksa arah arsitektur ditambahkan fitur 009, sesudah **tiga** tepi
    tak berdokumen ditemukan pada tiga fitur berturut-turut — `rag → nlp`
    (007), `ingest → llm` (008), dan `src/logbook/` yang diimpor lima lapisan
    tanpa pernah tercatat sama sekali. Ketiganya sah setelah ditinjau, dan itu
    yang membuatnya mengkhawatirkan: yang lolos bukan pelanggaran melainkan
    keputusan arsitektur yang tidak pernah diambil siapa pun.

    Dua pemeriksa sebelumnya ditambahkan fitur 014. Sampai saat itu keselarasan
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
        *periksa_status_gerbang(akar),
        *periksa_arah_arsitektur(akar),
        *periksa_rute_terdaftar(akar),
        *periksa_hasil_jalur(akar),
        # Fitur 027 (R-19): bentuk tanggapan ditulis dua kali, pada model dan
        # pada `web/src/kontrak.ts`; hanyutnya menjatuhkan gerbang ini.
        *periksa_kontrak_web(akar),
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
        # Paket npm `web/` sejak fitur 027 (KB-127). Sebelumnya V-04 tidak
        # mengenal npm sama sekali, dan paket frontend akan lolos gerbang
        # tanpa satu baris pun diperiksa.
        [*periksa_ketergantungan(akar), *periksa_ketergantungan_npm(akar), *sistem.temuan],
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
