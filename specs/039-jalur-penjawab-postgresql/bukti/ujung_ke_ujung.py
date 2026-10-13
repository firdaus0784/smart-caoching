"""Bukti ujung ke ujung fitur 039 — T-8, `plan.md` Bagian 11.2.

Di LUAR `make check`. Perkakas ingesti, kurasi, dan pengambilan dijalankan
**lewat baris perintah**, tiap perintah tersambung sebagai perannya sendiri;
psql sebagai pengelola hanya **membaca** tabel — kecuali satu hal buatan di
bawah.

HAL BUATAN, dinyatakan, bukan disamarkan:

1. **Berkas contoh dibuat naskah ini** (`contoh-regulasi-039.docx`);
   peraturannya rekaan, keterangan lisensi dan tautannya diberikan naskah.
2. **Segmen dokumen berlisensi `CC-BY-SA 4.0` ditanam pengelola di indeks
   utama**, meniru keadaan sesudah pengindeksan sebelum TK-87, ketika awalan
   `cc-by` meloloskannya. Yang dibuktikan: lapis kedua menahannya,
   `cari` menyebutnya perlu diindeks ulang, dan `indeks` memindahkannya.

Prasyarat, dari akar repositori:
  PGHOST=/tmp PGPORT=55432 PGUSER=pengelola \\
    uv run python specs/039-jalur-penjawab-postgresql/bukti/ujung_ke_ujung.py
"""

from __future__ import annotations

import secrets
import subprocess
import sys
from pathlib import Path

from docx import Document

AKAR = Path(__file__).resolve().parents[3]
KELUAR = Path(__file__).resolve().parent

akhiran = secrets.token_hex(3)
TERBUKA = f"reg-039-{akhiran}-by"
NONKOMERSIAL = f"reg-039-{akhiran}-nc"
BERBAGI = f"reg-039-{akhiran}-sa"

masalah: list[str] = []
catatan: list[str] = []


def pastikan(syarat: bool, pesan: str) -> None:
    print(("ok  : " if syarat else "GAGAL: ") + pesan)
    if not syarat:
        masalah.append(pesan)


def perkakas(nama: str, *argumen: str) -> tuple[int, str, str]:
    hasil = subprocess.run(
        [sys.executable, "-m", f"perkakas.{nama}", *argumen],
        cwd=AKAR,
        capture_output=True,
        text=True,
        check=False,
    )
    catatan.append(f"$ python -m perkakas.{nama} {' '.join(argumen)}")
    catatan.append(f"[kode {hasil.returncode}]")
    catatan.extend(f"  {b}" for b in (hasil.stdout + hasil.stderr).splitlines())
    return hasil.returncode, hasil.stdout, hasil.stderr


def psql(kueri: str) -> str:
    return subprocess.run(
        ["psql", "-d", "smart_coaching", "-At", "-v", "ON_ERROR_STOP=1", "-c", kueri],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def jumlah(id_dokumen: str) -> str:
    return psql(
        f"select (select count(*) from indeks_utama.segmen_teks where id_dokumen = '{id_dokumen}')"
        f" || ':' || (select count(*) from indeks_metadata.segmen_teks "
        f"where id_dokumen = '{id_dokumen}')"
    )


berkas = KELUAR / "contoh-regulasi-039.docx"
dokumen = Document()
for paragraf in [
    "PERATURAN CONTOH NOMOR 3 TAHUN 2026",
    "TENTANG PENGELOLAAN SARANA SEKOLAH",
    "Pasal 1",
    "Kepala sekolah menetapkan penanggung jawab sarana sekolah.",
    "Pasal 2",
    "(1) Inventarisasi sarana prasarana dilakukan setiap semester.",
    "(2) Hasil inventarisasi dilaporkan kepada komite sekolah.",
]:
    dokumen.add_paragraph(paragraf)
dokumen.save(berkas)


def terima(id_dokumen: str, lisensi: str) -> None:
    kode, _, galat = perkakas(
        "ingesti",
        "terima",
        "--berkas",
        str(berkas),
        "--id",
        id_dokumen,
        "--judul",
        f"Peraturan Contoh Nomor 3 Tahun 2026 ({lisensi})",
        "--jenis",
        "regulasi_resmi",
        "--penerbit",
        "Kementerian Contoh",
        "--tahun",
        "2026",
        "--kerahasiaan",
        "publik",
        "--persetujuan",
        "belum_diminta",
        "--pelaku",
        "tm-001",
        "--lisensi",
        lisensi,
        "--tautan",
        f"https://jdih.contoh.go.id/peraturan/{id_dokumen}",
    )
    pastikan(kode == 0, f"terima {lisensi} --tautan, sebagai peran_ingesti")
    kode, _, _ = perkakas(
        "ingesti", "setujui", "--id", id_dokumen, "--pelaku", "tm-002", "--alasan", "terperiksa"
    )
    pastikan(kode == 0, f"setujui {lisensi}, sebagai peran_verifikasi")
    kode, _, _ = perkakas("kurasi", "status", "--dokumen", id_dokumen, "--status", "berlaku")
    pastikan(kode == 0, f"status berlaku {lisensi}, lewat perkakas kurasi")


# ── A · tiga dokumen sampai korpus, tautan dan lisensi tercatat ───────
for id_dokumen, lisensi in (
    (TERBUKA, "CC BY 4.0"),
    (NONKOMERSIAL, "CC-BY-NC 4.0"),
    (BERBAGI, "CC-BY-SA 4.0"),
):
    terima(id_dokumen, lisensi)
pastikan(
    psql(f"select tautan from korpus.metadata_dokumen where id_dokumen = '{TERBUKA}'")
    == f"https://jdih.contoh.go.id/peraturan/{TERBUKA}",
    "P-5 A: tautan ikut catatan metadata korpus",
)

# ── B · indeks menurut lisensi yang dinormalkan ───────────────────────
kode, keluar, _ = perkakas("ingesti", "indeks", "--id", TERBUKA)
pastikan(kode == 0 and "indeks utama" in keluar, "TK-87: `CC BY 4.0` kini terbaca terbuka")
kode, keluar, _ = perkakas("ingesti", "indeks", "--id", NONKOMERSIAL)
pastikan(kode == 0 and "indeks metadata" in keluar, "TK-87: `CC-BY-NC 4.0` tertutup")
pastikan(jumlah(TERBUKA) == "3:0" and jumlah(NONKOMERSIAL) == "0:3", "segmen di indeks tujuannya")

# ── C · HAL BUATAN: segmen SA di indeks utama, meniru sebelum TK-87 ────
psql(
    "insert into indeks_utama.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
    "anonimisasi_terverifikasi, penanda_bagian) values "
    f"('{BERBAGI}:0003', '{BERBAGI}', 'Pasal 2 (1) Inventarisasi sarana prasarana dilakukan "
    "setiap semester.', 'terbuka', true, 'Pasal 2')"
)

# ── D · cari ──────────────────────────────────────────────────────────
kode, keluar, _ = perkakas("pengambilan", "cari", "--kueri", "inventarisasi sarana prasarana")
peringkat = [b for b in keluar.splitlines() if b[:1].isdigit()]
pastikan(kode == 0 and bool(peringkat), "cari indeks utama, sebagai peran_pemanggil_llm")
pastikan(
    TERBUKA in peringkat[0] and "Pasal 2" in peringkat[0], "pasal yang dirujuk ditemukan teratas"
)
pastikan(
    all(NONKOMERSIAL not in b and BERBAGI not in b for b in peringkat),
    "C-02: dokumen tertutup tidak masuk peringkat indeks utama",
)
ulang = [b for b in keluar.splitlines() if b.startswith("Perlu diindeks ulang")]
pastikan(
    bool(ulang) and BERBAGI in ulang[0], "lapis kedua: dokumen SA disebut perlu diindeks ulang"
)
pastikan("Inventarisasi sarana prasarana dilakukan" not in keluar, "R-08: keluaran tanpa teks")
kode, keluar, _ = perkakas(
    "pengambilan", "cari", "--kueri", "inventarisasi sarana prasarana", "--indeks", "metadata"
)
pastikan(kode == 0 and NONKOMERSIAL in keluar, "cari indeks metadata, sebagai peran_penjawaban")

# ── E · indeks ulang memindahkan segmen SA ────────────────────────────
kode, keluar, _ = perkakas("ingesti", "indeks", "--id", BERBAGI)
pastikan(kode == 0 and jumlah(BERBAGI) == "0:3", "indeks ulang: segmen SA pindah ke metadata")
kode, keluar, _ = perkakas("pengambilan", "cari", "--kueri", "inventarisasi sarana prasarana")
ulang = [b for b in keluar.splitlines() if b.startswith("Perlu diindeks ulang")]
pastikan(not ulang or BERBAGI not in ulang[0], "sesudahnya tidak lagi perlu diindeks ulang")

# ── F · yang tersimpan ────────────────────────────────────────────────
ids = f"('{TERBUKA}', '{NONKOMERSIAL}', '{BERBAGI}')"
metadata = psql(
    "select string_agg(id_dokumen || ' | ' || lisensi || ' | ' || coalesce(tautan, '-'), "
    f"E'\\n' order by id_dokumen) from korpus.metadata_dokumen where id_dokumen in {ids}"
)
segmen = psql(
    "select string_agg(s.indeks || ' | ' || s.id_segmen || ' | ' || s.penanda_bagian || ' | ' "
    "|| s.lisensi, E'\\n' order by s.indeks desc, s.id_segmen) from ("
    "select 'utama' indeks, id_segmen, id_dokumen, penanda_bagian, lisensi "
    "from indeks_utama.segmen_teks union all select 'metadata', id_segmen, id_dokumen, "
    f"penanda_bagian, lisensi from indeks_metadata.segmen_teks) s where s.id_dokumen in {ids}"
)
(KELUAR / "pengambilan.txt").write_text(
    "Berkas contoh, lisensi, dan tautannya dibuat naskah bukti; peraturannya rekaan.\n"
    "Satu segmen dokumen CC-BY-SA ditanam pengelola di indeks utama, meniru keadaan\n"
    "sebelum TK-87; perintah indeks memindahkannya.\n\n"
    f"== catatan metadata (dokumen | lisensi | tautan) ==\n{metadata}\n\n"
    f"== segmen akhir (indeks | id_segmen | penanda | lisensi) ==\n{segmen}\n\n"
    "== jalannya perintah ==\n" + "\n".join(catatan) + "\n",
    encoding="utf-8",
)
print("Seluruh pemeriksaan lulus." if not masalah else f"GAGAL: {masalah}")
sys.exit(1 if masalah else 0)
