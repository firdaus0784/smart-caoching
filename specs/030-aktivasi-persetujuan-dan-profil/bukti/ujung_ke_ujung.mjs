// Bukti ujung ke ujung fitur 030 — T-6, `plan.md` Bagian 9.2.
//
// Di LUAR `make check`: Playwright alat global.
//
// NASKAH: bukti ini memakai **naskah uji** yang dipasang sementara pada
// `web/public/naskah/persetujuan.json` dan dihapus sesudahnya. Naskah itu
// bertanda tegas bukan naskah ET-02 dan tidak pernah di-commit — agen tidak
// menulis naskah persetujuan (KB-164).
//
// Prasyarat, dari akar repositori:
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <akun> --peran pengguna
//   (naskah uji dipasang)  npm --prefix web run build
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   AKUN_UJI=<akun> SANDI_UJI=<sandi> node specs/030-aktivasi-persetujuan-dan-profil/bukti/ujung_ke_ujung.mjs

import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
const AKUN = process.env.AKUN_UJI;
const SANDI = process.env.SANDI_UJI;
if (!AKUN || !SANDI) throw new Error("AKUN_UJI dan SANDI_UJI wajib diisi");
const KELUAR = dirname(fileURLToPath(import.meta.url));

const masalah = [];
function pastikan(syarat, pesan) {
  if (syarat) console.log(`ok  : ${pesan}`);
  else {
    masalah.push(pesan);
    console.error(`GAGAL: ${pesan}`);
  }
}

const peramban = await chromium.launch();
const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 } });
const h = await konteks.newPage();
h.on("console", (p) => p.type() === "error" && masalah.push(`konsol: ${p.text()}`));
h.on("pageerror", (g) => masalah.push(`halaman: ${g.message}`));
const takAda = [];
h.on("response", (r) => r.status() === 404 && takAda.push(new URL(r.url()).pathname));
const judul = (nama) => h.getByRole("heading", { name: nama, exact: true });

// ── masuk ──
await h.goto(ALAMAT);
await judul("Masuk").waitFor();
await h.getByLabel("Nama pengguna").fill(AKUN);
await h.getByLabel("Sandi", { exact: true }).fill(SANDI);
await h.getByRole("button", { name: "Masuk" }).click();

// ── S-02 ──
await judul("Persetujuan penelitian").waitFor();
pastikan((await h.getByText("NASKAH UJI").count()) > 0, "S-02 menampilkan naskah dari berkas, apa adanya");
await h.screenshot({ path: join(KELUAR, "s02-persetujuan.png"), fullPage: true });
await h.getByRole("button", { name: "Saya setuju" }).click();

// ── S-03 ──
for (const nama of ["Yang dapat dibantu", "Alat bantu, bukan penentu", "Bila dasarnya tidak ada"]) {
  await judul(nama).waitFor();
  if (nama === "Alat bantu, bukan penentu") await h.screenshot({ path: join(KELUAR, "s03-pengenalan.png"), fullPage: true });
  await h.getByRole("button", { name: "Lanjut" }).click();
}
await judul("Menjaga data").waitFor();
await h.getByRole("button", { name: "Mulai mengisi profil" }).click();

// ── S-04 ──
await judul("Profil sekolah").waitFor();
await h.getByLabel("Jabatan").fill("Kepala Sekolah");
await h.getByLabel("Masa kerja (tahun)").fill("3");
await h.getByLabel("Jumlah rombongan belajar").fill("6");
await h.getByLabel("Jumlah pendidik dan tenaga kependidikan").fill("9");
await h.getByLabel("Visitasi").check();
await h.getByLabel("Wilayah (kabupaten atau kota)").fill("Kabupaten Sumedang");
for (const label of ["Keuangan dan pembiayaan", "Kurikulum dan pembelajaran", "Penjaminan mutu dan akreditasi"]) {
  await h.getByLabel(label).check();
}
pastikan(!/\bK[1-8]\b/.test((await h.textContent("body")) ?? ""), "S-04 tanpa kode K1 s.d. K8");
await h.screenshot({ path: join(KELUAR, "s04-profil.png"), fullPage: true });
await h.getByRole("button", { name: "Simpan dan mulai bertanya" }).click();

// ── S-09; muat ulang tidak mengulang aktivasi ──
await judul("Tanya").waitFor();
// Dibaca dari dalam halaman: kuki `__Host-` `Secure` hanya dikirim peramban.
const ringkas = () => h.evaluate(async () => (await fetch("/api/v1/saya/profil")).json());
const r1 = await ringkas();
pastikan(r1.persetujuan === "diberikan", `persetujuan tercatat: ${r1.persetujuan}`);
pastikan(JSON.stringify(r1.prioritas) === JSON.stringify(["K5", "K1", "K7"]), `prioritas berurutan: ${r1.prioritas}`);
pastikan(r1.profil?.wilayah === "Kabupaten Sumedang", "profil tersimpan");
await h.reload();
await judul("Tanya").waitFor();
pastikan((await judul("Persetujuan penelitian").count()) === 0, "muat ulang langsung ke Tanya");

// ── P-5: cabut dari Tanya ──
await h.getByRole("button", { name: "Persetujuan penelitian" }).click();
await h.getByText("Anda sudah menyetujui perekaman data penelitian.").waitFor();
await h.getByRole("button", { name: "Cabut persetujuan" }).click();
await judul("Tanya").waitFor();
const r2 = await ringkas();
pastikan(r2.persetujuan === "dicabut", `sesudah mencabut: ${r2.persetujuan}`);
await h.screenshot({ path: join(KELUAR, "tanya-sesudah-cabut.png"), fullPage: true });

console.log("respons 404:", JSON.stringify(takAda));
await peramban.close();
// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama — jawaban sah.
const nyata = masalah.filter((m) => !/status of 401/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
