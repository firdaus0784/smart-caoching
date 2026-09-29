// Bukti ujung ke ujung fitur 028 — T-8, `plan.md` Bagian 8.2.
//
// Di LUAR `make check`, sama dengan fitur 027: Playwright alat global.
//
// Prasyarat, dari akar repositori:
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   npm --prefix web run build
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   node specs/028-penyambungan-riwayat-percakapan/bukti/ujung_ke_ujung.mjs
//
// Seluruh jawaban SUNGGUHAN dari `make jalan` dengan korpus kosong — karena
// itu selalu `tidak_ditemukan`. Yang dibuktikan di sini riwayatnya, bukan
// jawabannya. Riwayat tersimpan pada PostgreSQL sebagai `peran_riwayat`.

import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
const KELUAR = dirname(fileURLToPath(import.meta.url));
const penanda = Date.now().toString(36);
const P1 = `Bagaimana menyusun jadwal supervisi akademik? (${penanda})`;
const P2 = `Siapa yang perlu dilibatkan dalam supervisi? (${penanda})`;
const P3 = `Bagaimana memantau program literasi? (${penanda})`;

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
const kiriman = [];
const tak_ada = [];
h.on("response", (r) => {
  if (r.status() === 404) tak_ada.push(new URL(r.url()).pathname);
});
h.on("request", (r) => {
  if (r.method() === "POST" && r.url().endsWith("/api/v1/tanya")) kiriman.push(JSON.parse(r.postData()));
});

async function tanyakan(teks) {
  const sebelum = kiriman.length;
  await h.getByLabel("Pertanyaan Anda").fill(teks);
  await h.getByRole("button", { name: "Kirim pertanyaan" }).click();
  await h.getByTestId("blok-jawaban").waitFor();
  await h.waitForFunction((n) => n > 0, kiriman.length - sebelum);
  await h.getByTestId("pertanyaan-sebelumnya").getByRole("button", { name: teks }).waitFor();
}

// ── 1. dua pertanyaan pada satu percakapan ──
await h.goto(ALAMAT);
await tanyakan(P1);
await tanyakan(P2);
pastikan(kiriman[0].id_percakapan === kiriman[1].id_percakapan, "dua pertanyaan, satu pengenal percakapan");

// ── 2. muat ulang: percakapan berlanjut, blok 9 dibaca dari peladen ──
await h.reload();
const blok9 = h.getByTestId("pertanyaan-sebelumnya");
await blok9.getByRole("button", { name: P2 }).waitFor();
pastikan((await blok9.getByRole("button").count()) === 2, "sesudah muat ulang blok 9 memuat kedua pertanyaan");
pastikan(!(await blok9.textContent()).includes("Belum ada dokumen rujukan"), "blok 9 tanpa isi jawaban");
await h.screenshot({ path: join(KELUAR, "berlanjut-sesudah-muat-ulang.png"), fullPage: true });

// ── 3. mengetuk pertanyaan lama mengisi isian, tidak mengirim ──
const terkirim = kiriman.length;
await blok9.getByRole("button", { name: P1 }).click();
await h.waitForTimeout(300);
pastikan((await h.getByLabel("Pertanyaan Anda").inputValue()) === P1, "ketuk mengisi isian");
pastikan(kiriman.length === terkirim, "ketuk tidak mengirim");

// ── 4. percakapan baru, lalu percakapan terdahulu ──
await h.getByRole("button", { name: "Percakapan baru" }).click();
await tanyakan(P3);
pastikan(kiriman.at(-1).id_percakapan !== kiriman[0].id_percakapan, "percakapan baru, pengenal baru");
await h.getByRole("button", { name: "Tampilkan percakapan terdahulu" }).click();
const blok10 = h.getByTestId("percakapan-terdahulu");
await blok10.getByRole("button", { name: P1 }).waitFor();
pastikan(true, "blok 10 memuat percakapan lama, berupa pertanyaan pertamanya");
await h.screenshot({ path: join(KELUAR, "percakapan-terdahulu.png"), fullPage: true });

await blok10.getByRole("button", { name: P1 }).click();
await blok9.getByRole("button", { name: P2 }).waitFor();
await tanyakan(`Lanjutan percakapan lama (${penanda})`);
pastikan(kiriman.at(-1).id_percakapan === kiriman[0].id_percakapan, "membuka percakapan lama melanjutkannya");

// ── 5. pertanyaan berdata pribadi ditolak (R-15, K-3) ──
const sebelumNik = kiriman.length;
await h.getByLabel("Pertanyaan Anda").fill("NIK guru saya 3201234567890123, bagaimana mutasinya?");
await h.getByRole("button", { name: "Kirim pertanyaan" }).click();
const peringatan = await h.getByRole("alert").textContent();
pastikan(peringatan.includes("tanpa nomor pribadi"), `K-3: "${peringatan.trim()}"`);
pastikan(kiriman.length === sebelumNik + 1, "permintaan terkirim, ditolak peladen");
await h.screenshot({ path: join(KELUAR, "data-pribadi-ditolak.png"), fullPage: true });

await peramban.close();

console.log("respons 404:", JSON.stringify(tak_ada));

// Galat konsol yang diharapkan: 400 atas pertanyaan berdata pribadi.
const nyata = masalah.filter((m) => !/status of 400/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
console.log(`penanda percakapan uji: ${penanda}`);
