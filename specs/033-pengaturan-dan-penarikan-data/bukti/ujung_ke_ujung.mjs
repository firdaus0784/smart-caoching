// Bukti ujung ke ujung fitur 033 — T-7, `plan.md` Bagian 10.2.
//
// Di LUAR `make check`: Playwright alat global, psql dan perkakas penarikan
// dijalankan dari akar repositori.
//
// NASKAH: bukti ini memakai **naskah uji** persetujuan dan penarikan yang
// dipasang sementara pada `web/public/naskah/` lalu dihapus. Keduanya bertanda
// tegas bukan naskah tim dan tidak pernah di-commit — agen tidak menulis
// naskah persetujuan maupun penjelasan penarikan (KB-164, P-4 B).
//
// Prasyarat, dari akar repositori:
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <kurator> --peran kurator
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <pengguna> --peran pengguna
//   (di specs/013-.../bukti/) PGHOST=/tmp PGPORT=55432 uv run python isi_antrean_bukti.py
//   (naskah uji dipasang)  npm --prefix web run build
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   KURATOR=<id> SANDI_KURATOR=<sandi> PENGGUNA=<id> SANDI_PENGGUNA=<sandi> \
//     PGHOST=/tmp PGPORT=55432 PGUSER=pengelola \
//     node specs/033-pengaturan-dan-penarikan-data/bukti/ujung_ke_ujung.mjs

import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
const PYTHON = process.env.PYTHON_BUKTI ?? ".venv/bin/python";
const { KURATOR, SANDI_KURATOR, PENGGUNA, SANDI_PENGGUNA } = process.env;
if (!KURATOR || !SANDI_KURATOR || !PENGGUNA || !SANDI_PENGGUNA) {
  throw new Error("KURATOR, SANDI_KURATOR, PENGGUNA, SANDI_PENGGUNA wajib diisi");
}
const KELUAR = dirname(fileURLToPath(import.meta.url));

const masalah = [];
function pastikan(syarat, pesan) {
  if (syarat) console.log(`ok  : ${pesan}`);
  else {
    masalah.push(pesan);
    console.error(`GAGAL: ${pesan}`);
  }
}

function psql(basis, kueri, ...variabel) {
  const argumen = ["-d", basis, "-At"];
  for (const [nama, nilai] of variabel) argumen.push("-v", `${nama}=${nilai}`);
  return execFileSync("psql", argumen, { encoding: "utf-8", input: kueri }).trim();
}

const TABEL = {
  "akun.pengguna": "SELECT count(*) FROM akun.pengguna WHERE pseudonim = :'p'",
  "akun.sesi":
    "SELECT count(*) FROM akun.sesi s JOIN akun.pengguna a ON a.id = s.id_pengguna WHERE a.pseudonim = :'p'",
  "pengguna.profil_sekolah": "SELECT count(*) FROM pengguna.profil_sekolah WHERE id_pengguna = :'p'",
  "pengguna.prioritas_manajerial":
    "SELECT count(*) FROM pengguna.prioritas_manajerial WHERE id_pengguna = :'p'",
  "pengguna.persetujuan": "SELECT count(*) FROM pengguna.persetujuan WHERE id_pengguna = :'p'",
  "riwayat.percakapan": "SELECT count(*) FROM riwayat.percakapan WHERE pemilik = :'p'",
  "riwayat.giliran":
    "SELECT count(*) FROM riwayat.giliran g JOIN riwayat.percakapan c USING (id_percakapan) WHERE c.pemilik = :'p'",
  "penemuan.tayang_harian": "SELECT count(*) FROM penemuan.tayang_harian WHERE id_pengguna = :'p'",
  "penemuan.belum_relevan": "SELECT count(*) FROM penemuan.belum_relevan WHERE id_pengguna = :'p'",
  "telemetri.peristiwa": "SELECT count(*) FROM telemetri.peristiwa WHERE pseudonim = :'p'",
};

function hitung(pseudonim) {
  const hasil = {};
  for (const [tabel, kueri] of Object.entries(TABEL)) {
    hasil[tabel] = Number(psql("smart_coaching", `${kueri};`, ["p", pseudonim]));
  }
  return hasil;
}

const peramban = await chromium.launch();
const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 } });
const h = await konteks.newPage();
h.on("console", (p) => p.type() === "error" && masalah.push(`konsol: ${p.text()}`));
h.on("pageerror", (g) => masalah.push(`halaman: ${g.message}`));
const judul = (nama) => h.getByRole("heading", { name: nama, exact: true });
const tombol = (nama) => h.getByRole("button", { name: nama, exact: true });
const baris = (nama) => h.getByRole("listitem").filter({ has: h.getByRole("heading", { name: nama }) });
const kartu = () => h.locator(".daftar-butir .kartu-butir");
const nav = (nama) => h.getByRole("navigation").getByRole("button", { name: nama });

async function masuk(akun, sandi) {
  await judul("Masuk").waitFor();
  await h.getByLabel("Nama pengguna").fill(akun);
  await h.getByLabel("Sandi", { exact: true }).fill(sandi);
  await tombol("Masuk").click();
}

// ── A · kurator menyetujui ───────────────────────────────────────────
await h.goto(ALAMAT);
await masuk(KURATOR, SANDI_KURATOR);
await judul("Antrean kurasi").waitFor();
for (const nama of [
  "Supervisi akademik terjadwal (contoh bukti)",
  "Pembelajaran berdiferensiasi (contoh bukti)",
  "Pelaporan dana sekolah (contoh bukti)",
]) {
  const satu = baris(nama);
  await satu.getByRole("button", { name: "Setujui", exact: true }).click();
  await satu.getByLabel("Catatan singkat").fill("Layak tayang untuk bukti");
  await satu.getByRole("button", { name: "Kirim putusan" }).click();
  await h.getByRole("heading", { name: nama }).first().waitFor();
}
await tombol("Keluar").first().click();

// ── B · pengguna beraktivitas ────────────────────────────────────────
await masuk(PENGGUNA, SANDI_PENGGUNA);
await judul("Persetujuan penelitian").waitFor();
pastikan((await h.getByText("NASKAH UJI").count()) > 0, "naskah uji persetujuan, bukan naskah ET-02");
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
await nav("Beranda").click();
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
await kartu().first().click();
await h.getByRole("heading", { level: 1 }).waitFor();
await tombol("Belum relevan").click();
await h.getByLabel("Mengapa butir ini belum relevan bagi sekolah Anda?").fill("Belum menjadi fokus semester ini");
await tombol("Kirim").click();
await judul("Butir hari ini").waitFor();

// ── C · S-14: sunting profil, lalu tarik data ────────────────────────
await tombol("Pengaturan").click();
await h.getByRole("heading", { level: 1, name: "Pengaturan" }).waitFor();
await h.getByRole("heading", { name: "PENJELASAN UJI — bukan naskah tim" }).waitFor();
pastikan(true, "P-4 B: penjelasan dibaca dari berkas tim, apa adanya");
pastikan((await h.getByRole("navigation").count()) === 0, "P-5: S-14 di luar navigasi utama");
await h.screenshot({ path: join(KELUAR, "s14-pengaturan.png"), fullPage: true });
await tombol("Ubah profil dan prioritas").click();
const wilayah = h.getByLabel("Wilayah (kabupaten atau kota)");
pastikan((await wilayah.inputValue()) === "Kabupaten Sumedang", "FR-A06: isian terisi dari ringkasan");
await wilayah.fill("Kota Bandung");
await tombol("Simpan perubahan").click();
await h.getByText("Profil dan prioritas tersimpan.").waitFor();
const ringkas = await h.evaluate(async () => (await fetch("/api/v1/saya/profil")).json());
pastikan(ringkas.profil?.wilayah === "Kota Bandung", "profil tersimpan lewat rute fitur 030");

const pseudonim = psql("smart_coaching", "SELECT pseudonim FROM akun.pengguna WHERE id = :'id';", ["id", PENGGUNA]);
pastikan(/^psd_[a-z]{16}$/.test(pseudonim), "pseudonim akun terbaca oleh pengelola");
const sebelum = hitung(pseudonim);
console.log("sebelum penarikan:", JSON.stringify(sebelum));
pastikan(Object.values(sebelum).every((n) => n > 0), "setiap tabel memuat data pengguna ini");

await tombol("Tarik data saya").click();
await tombol("Ya, tarik data saya").waitFor();
await h.screenshot({ path: join(KELUAR, "s14-konfirmasi.png"), fullPage: true });
await tombol("Ya, tarik data saya").click();
await h.getByText("Permintaan penarikan data diterima. Data Anda dihapus paling lambat 14 hari.").waitFor();
await judul("Masuk").waitFor();
await h.screenshot({ path: join(KELUAR, "s01-sesudah-penarikan.png"), fullPage: true });

// ── D · masuk lagi ditolak sama dengan sandi salah ───────────────────
await masuk(PENGGUNA, SANDI_PENGGUNA);
await h.getByText("Nama pengguna atau sandi belum cocok.", { exact: false }).waitFor();
pastikan(true, "K-4: masuk sesudah meminta ditolak dengan kalimat sandi salah");
await peramban.close();

// ── E · perkakas tim ─────────────────────────────────────────────────
const lingkungan = { ...process.env };
const daftar = execFileSync(PYTHON, ["-m", "perkakas.penarikan", "daftar"], { encoding: "utf-8", env: lingkungan });
const jalankan = execFileSync(PYTHON, ["-m", "perkakas.penarikan", "jalankan"], { encoding: "utf-8", env: lingkungan });
writeFileSync(join(KELUAR, "perkakas.txt"), `$ python -m perkakas.penarikan daftar\n${daftar}\n$ python -m perkakas.penarikan jalankan\n${jalankan}`);
pastikan(!daftar.includes("psd_") && !jalankan.includes("psd_"), "R-09: keluaran perkakas tanpa pseudonim");
pastikan(/dipenuhi/.test(jalankan), "perkakas memenuhi permintaan");

const sesudah = hitung(pseudonim);
console.log("sesudah perkakas:", JSON.stringify(sesudah));
pastikan(Object.values(sesudah).every((n) => n === 0), "R-02: setiap tabel kosong dari pengguna ini");
const bukti = psql(
  "smart_coaching",
  "SELECT count(*) FROM akun.permintaan_penarikan WHERE pseudonim = :'p';",
  ["p", pseudonim],
);
pastikan(bukti === "0", "bukti permintaan tidak lagi menunjuk pseudonim");
writeFileSync(
  join(KELUAR, "jumlah.json"),
  JSON.stringify({ sebelum, sesudah }, null, 2) + "\n",
);

// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama, 403 atas
// ringkasan akun kurator (K-8 fitur 013).
const nyata = masalah.filter((m) => !/status of 40[13]/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
