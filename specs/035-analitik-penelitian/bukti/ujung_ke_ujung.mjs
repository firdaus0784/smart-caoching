// Bukti ujung ke ujung fitur 035 — T-7, `plan.md` Bagian 8.2.
//
// Di LUAR `make check`: Playwright alat global, psql dan perkakas penarikan
// dijalankan dari akar repositori.
//
// NASKAH: naskah **uji** persetujuan dipasang sementara pada
// `web/public/naskah/` lalu dihapus; tidak pernah di-commit (KB-164).
//
// `make jalan` menandai setiap peristiwa `pengembangan` (fitur 034, K-4), dan
// analitik memisahkannya dari metrik (R-05). Bukti ini karena itu memeriksa
// pemisahan itu sendiri: metrik keterlibatan kosong, integritas menghitung
// peristiwa pengembangan, dan ekspor hanya memuatnya bila diminta tegas.
//
// Prasyarat, dari akar repositori:
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <pengguna> --peran pengguna
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <peneliti> --peran peneliti
//   (naskah uji dipasang)  npm --prefix web run build
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   PENGGUNA=<id> SANDI_PENGGUNA=<sandi> PENELITI=<id> SANDI_PENELITI=<sandi> \
//     PGHOST=/tmp PGPORT=55432 PGUSER=pengelola \
//     node specs/035-analitik-penelitian/bukti/ujung_ke_ujung.mjs

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
const PYTHON = process.env.PYTHON_BUKTI ?? ".venv/bin/python";
const { PENGGUNA, SANDI_PENGGUNA, PENELITI, SANDI_PENELITI } = process.env;
if (!PENGGUNA || !SANDI_PENGGUNA || !PENELITI || !SANDI_PENELITI) {
  throw new Error("PENGGUNA, SANDI_PENGGUNA, PENELITI, SANDI_PENELITI wajib diisi");
}
const KELUAR = dirname(fileURLToPath(import.meta.url));
const HARI_INI = new Date(Date.now() + 7 * 3600 * 1000).toISOString().slice(0, 10); // tanggal WIB

const masalah = [];
function pastikan(syarat, pesan) {
  if (syarat) console.log(`ok  : ${pesan}`);
  else {
    masalah.push(pesan);
    console.error(`GAGAL: ${pesan}`);
  }
}
const psql = (kueri) => execFileSync("psql", ["-d", "smart_coaching", "-At"], { encoding: "utf-8", input: kueri }).trim();

const peramban = await chromium.launch();
const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 }, acceptDownloads: true });
const h = await konteks.newPage();
h.on("console", (p) => p.type() === "error" && masalah.push(`konsol: ${p.text()}`));
h.on("pageerror", (g) => masalah.push(`halaman: ${g.message}`));
const judul = (nama) => h.getByRole("heading", { name: nama, exact: true });
const tombol = (nama) => h.getByRole("button", { name: nama, exact: true });

async function masuk(akun, sandi) {
  await judul("Masuk").waitFor();
  await h.getByLabel("Nama pengguna").fill(akun);
  await h.getByLabel("Sandi", { exact: true }).fill(sandi);
  await tombol("Masuk").click();
}

// ── A · pengguna beraktivitas dengan persetujuan ─────────────────────
await h.goto(ALAMAT);
await masuk(PENGGUNA, SANDI_PENGGUNA);
await judul("Persetujuan penelitian").waitFor();
await tombol("Saya setuju").click();
for (const nama of ["Yang dapat dibantu", "Alat bantu, bukan penentu", "Bila dasarnya tidak ada"]) {
  await judul(nama).waitFor();
  await tombol("Lanjut").click();
}
await judul("Menjaga data").waitFor();
await tombol("Mulai mengisi profil").click();
await judul("Profil sekolah").waitFor();
await h.getByLabel("Jabatan").fill("Kepala Sekolah");
await h.getByLabel("Masa kerja (tahun)").fill("3");
await h.getByLabel("Jumlah rombongan belajar").fill("6");
await h.getByLabel("Jumlah pendidik dan tenaga kependidikan").fill("9");
await h.getByLabel("Visitasi").check();
await h.getByLabel("Wilayah (kabupaten atau kota)").fill("Kabupaten Sumedang");
for (const label of ["Kurikulum dan pembelajaran", "Keuangan dan pembiayaan", "Penjaminan mutu dan akreditasi"]) {
  await h.getByLabel(label).check();
}
await tombol("Simpan dan mulai bertanya").click();
await judul("Tanya").waitFor();
await h.getByLabel("Pertanyaan Anda").fill("Bagaimana menyusun jadwal supervisi akademik yang adil?");
const jawab = h.waitForResponse((r) => r.url().endsWith("/tanya") && r.request().method() === "POST");
await tombol("Kirim pertanyaan").click();
await jawab;
await tombol("Keluar").first().click();
await masuk(PENGGUNA, SANDI_PENGGUNA);
await h.getByRole("navigation").waitFor();
await tombol("Keluar").first().click();

// ── B · peneliti membuka S-18 ────────────────────────────────────────
await masuk(PENELITI, SANDI_PENELITI);
await h.getByRole("heading", { level: 1, name: "Analitik penelitian" }).waitFor();
pastikan((await h.getByRole("navigation").count()) === 0, "K-5: S-18 tanpa navigasi pengguna");
const harian = h.getByRole("table", { name: "Pengguna aktif harian" });
pastikan((await harian.textContent()).includes("Belum ada data."), "R-05: peristiwa pengembangan tidak masuk keterlibatan");
const integritas = h.getByRole("table", { name: "Integritas data" });
const baris = integritas.getByRole("row").filter({ hasText: "Peristiwa pengembangan" });
const jumlahPengembangan = Number((await baris.locator("td").nth(1).textContent()) ?? "0");
pastikan(jumlahPengembangan > 0, `R-05: integritas menghitung ${jumlahPengembangan} peristiwa pengembangan`);
pastikan((await h.getByText("Belum dapat dihitung").count()) > 0, "R-04: angka tanpa penyebut bukan nol");
pastikan((await h.getByText("Rasio penerapan", { exact: true }).count()) === 1, "R-04: metrik belum terukur bernama");
await h.screenshot({ path: join(KELUAR, "s18-analitik.png"), fullPage: true });

async function unduh(sertakan) {
  await h.getByLabel("Tanggal awal").fill(HARI_INI);
  await h.getByLabel("Tanggal akhir").fill(HARI_INI);
  const centang = h.getByLabel("Sertakan peristiwa pengembangan");
  if ((await centang.isChecked()) !== sertakan) await centang.click();
  const tunggu = h.waitForEvent("download");
  await tombol("Unduh berkas data").click();
  const berkas = await tunggu;
  const jalur = join(tmpdir(), berkas.suggestedFilename());
  await berkas.saveAs(jalur);
  const teks = readFileSync(jalur, "utf-8").trim().split("\n");
  return { nama: berkas.suggestedFilename(), kepala: teks[0], baris: teks.length - 1 };
}
const tanpa = await unduh(false);
const dengan = await unduh(true);
pastikan(tanpa.kepala === "pseudonim,jenis,waktu,properti,versi_aplikasi,versi_model", "R-06: kolom ekspor = model Peristiwa");
pastikan(tanpa.baris === 0, "R-05: tanpa centang, peristiwa pengembangan tidak terekspor");
pastikan(dengan.baris > 0, `ekspor bertanda tegas memuat ${dengan.baris} peristiwa pengembangan`);
const jejak = psql(
  `SELECT count(*) FROM telemetri.ekspor WHERE dari = '${HARI_INI}' AND jumlah_baris IN (0, ${dengan.baris}) AND diekspor_pada > now() - interval '10 minutes';`,
);
pastikan(Number(jejak) >= 2, "K-1: kedua ekspor tercatat sebelum berkasnya terkirim");
const nomorEkspor = psql("SELECT max(nomor) FROM telemetri.ekspor;");
await tombol("Keluar").click();

// ── C · pengguna menarik data; perkakas menyebut ekspor itu ──────────
await masuk(PENGGUNA, SANDI_PENGGUNA);
await tombol("Pengaturan").click();
await tombol("Tarik data saya").click();
await tombol("Ya, tarik data saya").click();
await judul("Masuk").waitFor();
await peramban.close();
const daftar = execFileSync(PYTHON, ["-m", "perkakas.penarikan", "daftar"], { encoding: "utf-8", env: process.env });
const barisku = daftar.split("\n").find((b) => b.includes("ekspor yang mungkin memuatnya")) ?? "";
pastikan(barisku.split("ekspor yang mungkin memuatnya: ")[1]?.split(", ").includes(nomorEkspor), "P-4 B: perkakas menyebut ekspor yang memuat data peserta");
pastikan(!daftar.includes("psd_"), "R-09 fitur 033: keluaran perkakas tanpa pseudonim");
const jalankan = execFileSync(PYTHON, ["-m", "perkakas.penarikan", "jalankan"], { encoding: "utf-8", env: process.env });

writeFileSync(
  join(KELUAR, "ekspor-dan-penarikan.txt"),
  [
    `Ekspor tanpa peristiwa pengembangan: ${tanpa.nama} — ${tanpa.baris} baris`,
    `Ekspor dengan peristiwa pengembangan: ${dengan.nama} — ${dengan.baris} baris`,
    `Kepala kolom: ${tanpa.kepala}`,
    "",
    "$ python -m perkakas.penarikan daftar",
    daftar.trim(),
    "",
    "$ python -m perkakas.penarikan jalankan",
    jalankan.trim(),
    "",
  ].join("\n"),
);

// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama, 403 atas
// ringkasan akun dan antrean bagi peneliti (K-5).
const nyata = masalah.filter((m) => !/status of 40[13]/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
