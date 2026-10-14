"""Bukti penjalan uji kepatuhan atas lingkungan pengembangan bersesi — T-6 fitur 042,
`plan.md` Bagian 9.2, R-01 s.d. R-06.

Di LUAR `make check`. Langkahnya seperti operator pada D-09 langkah 5:

1. `make jalan` bersesi — `python -m perkakas.jalankan_lokal --riwayat postgres`
   — pada porta bebas di `127.0.0.1`.
2. Akun uji dibuat dengan `python -m perkakas.akun buat`, peran pengguna,
   tanpa persetujuan penelitian. Sandinya hanya hidup di memori naskah ini dan
   **tidak pernah dicetak**.
3. Masuk lewat `POST /api/v1/auth/masuk` untuk memperoleh kuki sesi.
4. Jumlah baris setiap tabel pada kedua basis data dihitung sebagai pengelola.
5. `python -m perkakas.kepatuhan jalankan` lewat baris perintah, dari
   *worktree* git pada `HEAD`: baris L1 yang ditulis milik logbook *worktree*
   dan dibuang bersamanya, sebab logbook repositori tambah-saja dan tidak boleh
   memuat putaran bukti.
6. Jumlah baris dihitung lagi dan dibandingkan; kuki dicari pada keluaran
   dan baris L1.

HAL YANG DINYATAKAN, bukan disamarkan:

- Peladen yang dipakai peladen uji bersama; isinya sisa uji lain, bukan
  korpus sungguhan. Yang dibuktikan cara kerja penjalan, bukan kepatuhan
  sebuah penyebaran.
- **Satu dokumen REKAAN ditanam pengelola** sebelum putaran, langsung lewat
  SQL, sebab peladen uji tidak memuat sumber yang dapat dibuka dan tanpanya
  UK-05 belum dapat diperiksa. Ia dihapus menurut id-nya sesudah putaran.
- Akun uji tetap ada sesudahnya, seperti akun uji operator.

Prasyarat, dari akar repositori:
  PGHOST=/tmp PGPORT=55432 PGUSER=pengelola \\
    uv run python specs/042-penjalan-uji-kepatuhan/bukti/penjalan_lokal.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import asyncpg  # type: ignore[import-untyped]
import httpx

AKAR = Path(__file__).resolve().parents[3]
KELUAR = Path(__file__).resolve().with_name("penjalan-lokal.txt")
PY = sys.executable
SEMENTARA = Path(tempfile.mkdtemp(prefix="bukti-042-"))
POHON = SEMENTARA / "pohon"
BASIS_DATA = ("smart_coaching", "smart_coaching_pseudonim")

baris_keluar: list[str] = []
masalah: list[str] = []


def tulis(teks: str = "") -> None:
    print(teks)
    baris_keluar.append(teks)


def pastikan(syarat: bool, pesan: str) -> None:
    tulis(("ok   : " if syarat else "GAGAL: ") + pesan)
    if not syarat:
        masalah.append(pesan)


def porta_bebas() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


async def hitung_semua() -> dict[str, int]:
    hasil: dict[str, int] = {}
    for nama in BASIS_DATA:
        sambungan = await asyncpg.connect(
            host=os.environ["PGHOST"],
            port=int(os.environ["PGPORT"]),
            user=os.environ["PGUSER"],
            database=nama,
        )
        try:
            tabel = await sambungan.fetch(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' "
                "AND table_schema NOT IN ('pg_catalog', 'information_schema') "
                "ORDER BY 1, 2"
            )
            for t in tabel:
                jumlah = await sambungan.fetchval(
                    f'SELECT count(*) FROM "{t["table_schema"]}"."{t["table_name"]}"'
                )
                hasil[f"{nama}:{t['table_schema']}.{t['table_name']}"] = int(jumlah)
        finally:
            await sambungan.close()
    return hasil


async def pengelola(*perintah: tuple[str, tuple[object, ...]]) -> None:
    sambungan = await asyncpg.connect(
        host=os.environ["PGHOST"],
        port=int(os.environ["PGPORT"]),
        user=os.environ["PGUSER"],
        database=BASIS_DATA[0],
    )
    try:
        async with sambungan.transaction():
            for kueri, argumen in perintah:
                await sambungan.execute(kueri, *argumen)
    finally:
        await sambungan.close()


def tanam(id_dokumen: str) -> None:
    """Dokumen rekaan berlisensi terbuka, publik, berlaku, satu segmen."""
    asyncio.run(
        pengelola(
            (
                "INSERT INTO korpus.dokumen_sumber (id, isi) VALUES ($1, to_jsonb($2::text))",
                (id_dokumen, "Teks rekaan fitur 042."),
            ),
            (
                "INSERT INTO korpus.metadata_dokumen (id_dokumen, judul, jenis, penerbit, "
                "tahun, tingkat_kerahasiaan, lisensi, tautan) "
                "VALUES ($1, $2, 'regulasi_resmi', 'Penerbit Rekaan', 2026, 'publik', "
                "'CC BY 4.0', NULL)",
                (id_dokumen, "Peraturan Rekaan Nomor 42 Tahun 2026"),
            ),
            (
                "INSERT INTO korpus.status_dokumen (id_dokumen, status) VALUES ($1, 'berlaku')",
                (id_dokumen,),
            ),
            (
                "INSERT INTO indeks_utama.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
                "anonimisasi_terverifikasi, penanda_bagian) "
                "VALUES ($1 || ':0001', $1, 'Teks rekaan fitur 042.', 'terbuka', true, 'Pasal 1')",
                (id_dokumen,),
            ),
        )
    )


def buang(id_dokumen: str) -> None:
    """Menghapus dokumen yang ditanam `tanam`, menurut id-nya saja."""
    asyncio.run(
        pengelola(
            ("DELETE FROM indeks_utama.segmen_teks WHERE id_dokumen = $1", (id_dokumen,)),
            ("DELETE FROM korpus.status_dokumen WHERE id_dokumen = $1", (id_dokumen,)),
            ("DELETE FROM korpus.metadata_dokumen WHERE id_dokumen = $1", (id_dokumen,)),
            ("DELETE FROM korpus.dokumen_sumber WHERE id = $1", (id_dokumen,)),
        )
    )


def tunggu_siap(alamat: str, proses: subprocess.Popen[bytes]) -> None:
    for _ in range(300):
        if proses.poll() is not None:
            raise SystemExit("Aplikasi berhenti sebelum siap.")
        try:
            if httpx.get(f"{alamat}/api/v1/saya/profil", timeout=1).status_code == 401:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise SystemExit("Aplikasi tidak siap dalam 30 detik.")


def id_percobaan_bebas(akar_logbook: Path) -> str:
    sys.path.insert(0, str(POHON))
    from src.rag.evaluasi.jejak import id_percobaan_terpakai

    for n in range(1, 1000):
        calon = f"EXP-2026-{n:03d}"
        if not id_percobaan_terpakai(akar_logbook, calon):
            return calon
    raise SystemExit("Tidak ada id percobaan bebas.")


def utama() -> int:
    for nama in ("PGHOST", "PGPORT", "PGUSER"):
        if nama not in os.environ:
            raise SystemExit(f"{nama} wajib disetel.")
    env = {k: v for k, v in os.environ.items() if not k.startswith("KEPATUHAN_")}

    subprocess.run(
        ["git", "worktree", "add", "--detach", str(POHON), "HEAD"],
        cwd=AKAR,
        check=True,
        capture_output=True,
    )
    porta = porta_bebas()
    alamat = f"http://127.0.0.1:{porta}"
    log_aplikasi = (SEMENTARA / "aplikasi.log").open("wb")
    aplikasi = subprocess.Popen(
        [PY, "-m", "perkakas.jalankan_lokal", "--porta", str(porta), "--riwayat", "postgres"],
        cwd=POHON,
        env=env,
        stdout=log_aplikasi,
        stderr=subprocess.STDOUT,
    )
    ditanam = False
    id_rekaan = ""
    try:
        tunggu_siap(alamat, aplikasi)
        tulis("# Bukti fitur 042 — penjalan uji kepatuhan atas lingkungan pengembangan bersesi")
        tulis()
        versi = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=POHON,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        tulis(f"Kode: worktree pada {versi}; aplikasi `jalankan_lokal --riwayat postgres`")
        tulis(f"Peladen: {os.environ['PGHOST']}:{os.environ['PGPORT']}")
        tulis()

        id_akun = "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz") for _ in range(6)) + "-042"
        buat = subprocess.run(
            [PY, "-m", "perkakas.akun", "buat", "--id", id_akun, "--peran", "pengguna"],
            cwd=POHON,
            env=env,
            capture_output=True,
            text=True,
        )
        pastikan(buat.returncode == 0, f"akun uji {id_akun} dibuat lewat `perkakas.akun buat`")
        sandi = re.findall(r"\b[2-9a-z]{4}(?:-[2-9a-z]{4}){3}\b", buat.stdout)
        pastikan(len(sandi) == 1, "sandi awal terbaca dari keluaran (tidak dicetak)")
        masuk = httpx.post(
            f"{alamat}/api/v1/auth/masuk",
            json={"nama_pengguna": id_akun, "sandi": sandi[0]},
            timeout=30,
        )
        del sandi
        pastikan(masuk.status_code == 204, f"masuk — HTTP {masuk.status_code}")
        kuki = masuk.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]

        id_rekaan = "rekaan-042-" + secrets.token_hex(3)
        tanam(id_rekaan)
        ditanam = True
        tulis(f"Dokumen rekaan ditanam: {id_rekaan}")
        sebelum = asyncio.run(hitung_semua())
        tulis(f"Tabel dihitung sebelum putaran: {len(sebelum)}")
        tulis()

        logbook = POHON / "logbook"
        id_percobaan = id_percobaan_bebas(logbook)
        berkas_l1 = logbook / "L1-percobaan.jsonl"
        l1_sebelum = berkas_l1.read_text(encoding="utf-8") if berkas_l1.exists() else ""
        putaran = subprocess.run(
            [
                PY,
                "-m",
                "perkakas.kepatuhan",
                "jalankan",
                "--lingkungan",
                "pengembangan-lokal",
                "--id-percobaan",
                id_percobaan,
            ],
            cwd=POHON,
            env={
                **env,
                "KEPATUHAN_API": alamat,
                "KEPATUHAN_AKUN": id_akun,
                "KEPATUHAN_KUKI": kuki,
            },
            capture_output=True,
            text=True,
        )
        tulis("## Keluaran penjalan, apa adanya")
        tulis()
        tulis("```")
        for b in putaran.stdout.rstrip().splitlines():
            tulis(b)
        tulis("```")
        tulis()
        tulis(f"Kode keluar: {putaran.returncode}")
        if putaran.stderr.strip():
            tulis(f"Galat baku: {putaran.stderr.strip()}")
        tulis()

        sesudah = asyncio.run(hitung_semua())
        tulis("## Pemeriksaan")
        tulis()
        pastikan(putaran.returncode == 4, "kode keluar 4 — tidak ada yang gagal, belum lengkap")
        l1_sesudah = berkas_l1.read_text(encoding="utf-8") if berkas_l1.exists() else ""
        tambahan = l1_sesudah[len(l1_sebelum) :].strip().splitlines()
        pastikan(
            l1_sesudah.startswith(l1_sebelum) and len(tambahan) == 1,
            f"satu baris L1 bertambah pada logbook worktree ({berkas_l1.name})",
        )
        baris_l1: dict[str, Any] = json.loads(tambahan[0]) if len(tambahan) == 1 else {}
        keadaan = {k: v["keadaan"] for k, v in baris_l1.get("hasil", {}).items()}
        belum = sorted(k for k, v in keadaan.items() if v == "belum dapat diperiksa")
        pastikan(
            belum == ["UK-01", "UK-03", "UK-06", "UK-11"],
            f"belum dapat diperiksa hanya keempat UK tanpa bahan: {', '.join(belum)}",
        )
        pastikan(
            sorted(k for k, v in keadaan.items() if v == "lulus")
            == [f"UK-{i:02d}" for i in (2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15)],
            "sebelas UK lainnya lulus, termasuk UK-05 atas sumber yang dapat dibuka",
        )
        pastikan(
            baris_l1.get("id_percobaan") == id_percobaan and baris_l1.get("tugas") == "kepatuhan",
            f"baris L1 ber-id {id_percobaan}, tugas kepatuhan",
        )
        pastikan(
            all(
                k in baris_l1
                for k in (
                    "versi_kode",
                    "versi_model",
                    "versi_indeks",
                    "versi_skema_anotasi",
                    "pembagian_data",
                )
            ),
            "baris L1 memuat kelima bidang versi (C-09)",
        )
        pastikan(
            kuki not in putaran.stdout + putaran.stderr + l1_sesudah,
            "kuki tidak muncul pada keluaran maupun L1 (R-05)",
        )
        berubah = {k: (sebelum.get(k), sesudah.get(k)) for k in sebelum.keys() | sesudah.keys()}
        berubah = {k: v for k, v in berubah.items() if v[0] != v[1]}
        pastikan(
            not berubah,
            f"jumlah baris {len(sebelum)} tabel pada kedua basis data sama sebelum dan "
            "sesudah putaran (R-04)",
        )
        for k, (a, b) in sorted(berubah.items()):
            tulis(f"       {k}: {a} lalu {b}")
        tulis()
        tulis("## Ringkas baris L1 (logbook worktree, dibuang)")
        tulis()
        tulis("```json")
        ringkas = {k: v for k, v in baris_l1.items() if k != "hasil"}
        ringkas["hasil"] = keadaan
        tulis(json.dumps(ringkas, ensure_ascii=False, indent=2))
        tulis("```")
    finally:
        if ditanam:
            buang(id_rekaan)
            tulis()
            tulis(f"Dokumen rekaan {id_rekaan} dihapus sesudah putaran.")
        aplikasi.terminate()
        aplikasi.wait(timeout=15)
        log_aplikasi.close()
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(POHON)], cwd=AKAR, capture_output=True
        )
        shutil.rmtree(SEMENTARA, ignore_errors=True)
    tulis()
    tulis(f"Masalah: {len(masalah)}")
    KELUAR.write_text("\n".join(baris_keluar) + "\n", encoding="utf-8")
    return 1 if masalah else 0


if __name__ == "__main__":
    raise SystemExit(utama())
