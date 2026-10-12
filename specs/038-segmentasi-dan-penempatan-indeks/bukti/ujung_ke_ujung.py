"""Bukti ujung ke ujung fitur 038 — T-7, `plan.md` Bagian 9.2.

Di LUAR `make check`. Perkakas ingesti dan kurasi dijalankan **lewat baris
perintah**, tiap perintah tersambung sebagai perannya sendiri; pembaca sumber
dibaca lewat `make jalan` dengan sesi sungguhan; psql sebagai pengelola hanya
**membaca** tabel. Tidak ada segmen yang ditanam: seluruhnya ditulis perintah
`indeks`.

HAL BUATAN, dinyatakan, bukan disamarkan:

1. **Berkas contoh dibuat naskah ini** (`contoh-regulasi-berpasal.docx`).
   Peraturannya rekaan; pasal 4 sengaja diisi kalimat berulang agar melampaui
   500 kata dan terpecah di batas ayat.
2. **Keterangan lisensi `public domain` diberikan naskah ini**, bukan dibaca
   dari sumber sungguhan. Yang dibuktikan adalah jalannya, bukan status hukum
   dokumen mana pun.

Prasyarat, dari akar repositori:
  akun pengguna lewat `perkakas.akun buat --peran pengguna`, sandinya di berkas 600
  PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
  PENGGUNA=… SANDI_PENGGUNA=… PGHOST=/tmp PGPORT=55432 PGUSER=pengelola \\
    uv run python specs/038-segmentasi-dan-penempatan-indeks/bukti/ujung_ke_ujung.py
"""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
from pathlib import Path

import httpx
from docx import Document

AKAR = Path(__file__).resolve().parents[3]
KELUAR = Path(__file__).resolve().parent
ALAMAT = os.environ.get("ALAMAT_PELADEN", "http://127.0.0.1:8000")
PENGGUNA, SANDI = os.environ["PENGGUNA"], os.environ["SANDI_PENGGUNA"]

akhiran = secrets.token_hex(3)
TERBUKA = f"reg-038-{akhiran}-a"
TANPA_LISENSI = f"reg-038-{akhiran}-b"
KARANTINA = f"reg-038-{akhiran}-c"
PISAH = "\u2013"

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
        ["psql", "-d", "smart_coaching", "-At", "-c", kueri],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def jumlah_segmen(id_dokumen: str) -> str:
    return psql(
        f"select (select count(*) from indeks_utama.segmen_teks where id_dokumen = '{id_dokumen}')"
        f" || ':' || (select count(*) from indeks_metadata.segmen_teks "
        f"where id_dokumen = '{id_dokumen}')"
    )


ULANG = (
    "Kepala sekolah memantau pelaksanaan program dan melaporkan capaiannya kepada dinas "
    "pendidikan setiap akhir semester."
)
berkas = KELUAR / "contoh-regulasi-berpasal.docx"
dokumen = Document()
for paragraf in [
    "PERATURAN CONTOH NOMOR 2 TAHUN 2026",
    "TENTANG RENCANA KERJA SEKOLAH",
    "Menimbang: bahwa sekolah memerlukan rencana kerja yang terukur.",
    "BAB I",
    "KETENTUAN UMUM",
    "Pasal 1",
    "Rencana kerja sekolah disusun kepala sekolah bersama guru dan komite sekolah.",
    "Pasal 2",
    "(1) Rencana kerja tahunan memuat sasaran, program, dan anggaran.",
    "(2) Rencana kerja tahunan ditetapkan sebelum tahun ajaran dimulai.",
    "BAB II",
    "PEMANTAUAN",
    "Pasal 3",
    "Pemantauan dilakukan sebagaimana dimaksud dalam Pasal 2 ayat (1).",
    "Pasal 4",
    *[f"({i}) " + " ".join([ULANG] * 14) for i in (1, 2, 3)],
    "BAB III",
    "KETENTUAN PENUTUP",
    "Pasal 5",
    "Peraturan ini mulai berlaku pada tanggal diundangkan.",
]:
    dokumen.add_paragraph(paragraf)
dokumen.save(berkas)


def terima(id_dokumen: str, *lisensi: str) -> tuple[int, str, str]:
    return perkakas(
        "ingesti",
        "terima",
        "--berkas",
        str(berkas),
        "--id",
        id_dokumen,
        "--judul",
        "Peraturan Contoh Nomor 2 Tahun 2026",
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
        *lisensi,
    )


# ── A · dua regulasi sampai korpus, satu tertahan di karantina ────────
kode, _, galat = terima(TERBUKA, "--lisensi", "public domain")
pastikan(kode == 0, "terima --lisensi, sebagai peran_ingesti")
kode, _, galat = terima(TANPA_LISENSI)
pastikan(kode == 0, "terima tanpa lisensi")
kode, _, galat = terima(KARANTINA, "--lisensi", "public domain")
pastikan(kode == 0, "terima dokumen yang tidak disetujui")
for d in (TERBUKA, TANPA_LISENSI):
    kode, _, galat = perkakas(
        "ingesti", "setujui", "--id", d, "--pelaku", "tm-002", "--alasan", "terperiksa"
    )
    pastikan(kode == 0, f"setujui {d}, sebagai peran_verifikasi")
    kode, _, _ = perkakas("kurasi", "status", "--dokumen", d, "--status", "berlaku")
    pastikan(kode == 0, f"status berlaku {d}, lewat perkakas kurasi")
pastikan(
    psql(f"select lisensi from korpus.metadata_dokumen where id_dokumen = '{TERBUKA}'")
    == "public domain",
    "P-3 A: lisensi ikut catatan metadata korpus",
)

# ── B · pratinjau, lalu indeks ────────────────────────────────────────
kode, keluar, _ = perkakas("ingesti", "indeks", "--id", TERBUKA, "--pratinjau")
pastikan(kode == 0 and "Pratinjau, tidak ada yang ditulis" in keluar, "indeks --pratinjau")
pastikan(jumlah_segmen(TERBUKA) == "0:0", "pratinjau tidak menulis")
pastikan("Rencana kerja tahunan memuat" not in keluar, "R-07: keluaran tanpa teks segmen")
penanda = [b[2:].rsplit(":", 1)[0] for b in keluar.splitlines() if b.startswith("- ")]
pastikan(
    penanda
    == [
        "Pembukaan",
        "Pasal 1",
        "Pasal 2",
        "Pasal 3",
        f"Pasal 4 ayat (1){PISAH}(2)",
        "Pasal 4 ayat (3)",
        "Pasal 5",
    ],
    "D-07 Bagian 3.2: pasal pendek berdiri sendiri, pasal panjang dipecah di batas ayat",
)
kode, keluar, _ = perkakas("ingesti", "indeks", "--id", TERBUKA)
pastikan(kode == 0 and "indeks utama" in keluar, "indeks sebagai peran_pengindeks: indeks utama")
pastikan(jumlah_segmen(TERBUKA) == "7:0", "tujuh segmen di indeks utama")
kode, keluar, _ = perkakas("ingesti", "indeks", "--id", TERBUKA)
pastikan(kode == 0 and jumlah_segmen(TERBUKA) == "7:0", "pengindeksan ulang mengganti")
kode, keluar, _ = perkakas("ingesti", "indeks", "--id", TANPA_LISENSI)
pastikan(kode == 0 and "indeks metadata" in keluar, "tanpa lisensi: indeks metadata (KL-01)")
pastikan(jumlah_segmen(TANPA_LISENSI) == "0:7", "tujuh segmen di indeks metadata")
kode, _, galat = perkakas("ingesti", "indeks", "--id", KARANTINA)
pastikan(kode == 1 and "tidak dikenal" in galat, "dokumen karantina ditolak (R-04, C-03)")
pastikan(jumlah_segmen(KARANTINA) == "0:0", "dokumen karantina tidak sampai ke indeks")

# ── C · pembaca sumber `make jalan` ───────────────────────────────────
masuk = httpx.post(f"{ALAMAT}/api/v1/auth/masuk", json={"nama_pengguna": PENGGUNA, "sandi": SANDI})
pastikan(masuk.status_code == 204, f"masuk sebagai pengguna ({masuk.status_code})")
kuki = {"Cookie": f"__Host-sesi={masuk.cookies.get('__Host-sesi')}"}


def sumber(id_dokumen: str, bagian: str) -> dict[str, object]:
    hasil = httpx.get(
        f"{ALAMAT}/api/v1/sumber/{id_dokumen}", params={"bagian": bagian}, headers=kuki
    )
    catatan.append(f"GET /api/v1/sumber/{id_dokumen}?bagian={bagian} → {hasil.status_code}")
    catatan.append(f"  {hasil.text}")
    return hasil.json() if hasil.status_code == 200 else {}


badan = sumber(TERBUKA, "Pasal 2")
pastikan(
    badan.get("tanpa_teks") is None
    and badan.get("teks_bagian")
    == [
        "Pasal 2\n(1) Rencana kerja tahunan memuat sasaran, program, dan anggaran.\n"
        "(2) Rencana kerja tahunan ditetapkan sebelum tahun ajaran dimulai."
    ],
    "S-10: teks Pasal 2 tampil — dari segmen yang ditulis perintah indeks",
)
badan = sumber(TERBUKA, f"Pasal 4 ayat (1){PISAH}(2)")
pastikan(
    badan.get("tanpa_teks") is None and len(badan.get("teks_bagian") or []) == 1,
    "S-10: bagian hasil pemecahan dapat dibuka menurut penandanya",
)
badan = sumber(TANPA_LISENSI, "Pasal 2")
pastikan(
    badan.get("tanpa_teks") == "bagian_tidak_tersedia" and badan.get("teks_bagian") == [],
    "S-10: dokumen tanpa lisensi tampil tanpa teks (C-02)",
)

# ── D · yang tersimpan ────────────────────────────────────────────────
segmen = psql(
    "select string_agg(s.indeks || ' | ' || s.id_segmen || ' | ' || s.penanda_bagian || ' | ' "
    "|| s.lisensi || ' | ' || array_length(regexp_split_to_array(s.teks, '\\s+'), 1) || ' kata',"
    " E'\\n' order by s.indeks desc, s.id_segmen) from ("
    "select 'utama' indeks, id_segmen, id_dokumen, penanda_bagian, lisensi, teks "
    "from indeks_utama.segmen_teks union all select 'metadata', id_segmen, id_dokumen, "
    "penanda_bagian, lisensi, teks from indeks_metadata.segmen_teks) s "
    f"where s.id_dokumen in ('{TERBUKA}', '{TANPA_LISENSI}')"
)
pastikan(
    psql(
        "select count(*) from indeks_utama.segmen_teks where vektor_sematan is not null "
        f"and id_dokumen in ('{TERBUKA}', '{TANPA_LISENSI}')"
    )
    == "0",
    "segmen tanpa vektor — penyematan di luar cakupan (ADR-12)",
)

(KELUAR / "pengindeksan.txt").write_text(
    "Berkas contoh dan keterangan lisensinya dibuat naskah bukti; peraturannya rekaan.\n"
    "Tidak ada segmen yang ditanam: seluruhnya ditulis perintah indeks.\n\n"
    "== segmen (indeks | id_segmen | penanda | lisensi | jumlah kata) ==\n"
    f"{segmen}\n\n== jalannya perintah ==\n" + "\n".join(catatan) + "\n",
    encoding="utf-8",
)
print("Seluruh pemeriksaan lulus." if not masalah else f"GAGAL: {masalah}")
sys.exit(1 if masalah else 0)
