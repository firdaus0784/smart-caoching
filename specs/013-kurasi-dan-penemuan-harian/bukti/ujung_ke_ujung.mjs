// Bukti ujung ke ujung fitur 013 — T-9, `plan.md` Bagian 10.2.
//
// Di LUAR `make check`: Playwright alat global.
//
// ANTREAN: diisi `isi_antrean_bukti.py` di folder ini — perkakas `isi` yang
// sama dengan L4 diloloskan **khusus bukti** (TK-72 menunggu putusan tim).
// Butirnya buatan dan bertanda "(contoh bukti)".
//
// Prasyarat, dari akar repositori:
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <kurator> --peran kurator
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <pengguna> --peran pengguna
//   PGHOST=/tmp PGPORT=55432 uv run python specs/013-kurasi-dan-penemuan-harian/bukti/isi_antrean_bukti.py
//   npm --prefix web run build
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   KURATOR=<id> SANDI_KURATOR=<sandi> PENGGUNA=<id> SANDI_PENGGUNA=<sandi> \
//     node specs/013-kurasi-dan-penemuan-harian/bukti/ujung_ke_ujung.mjs

import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
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

const peramban = await chromium.launch();
const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 } });
const h = await konteks.newPage();
h.on("console", (p) => p.type() === "error" && masalah.push(`konsol: ${p.text()}`));
h.on("pageerror", (g) => masalah.push(`halaman: ${g.message}`));
const takAda = [];
h.on("response", (r) => r.status() === 404 && takAda.push(new URL(r.url()).pathname));
const judul = (nama) => h.getByRole("heading", { name: nama, exact: true });
const tombol = (nama) => h.getByRole("button", { name: nama, exact: true });
const teks = async () => (await h.textContent("body")) ?? "";
const baris = (nama) => h.getByRole("listitem").filter({ has: h.getByRole("heading", { name: nama }) });
const kartu = () => h.locator(".daftar-butir .kartu-butir");

async function masuk(akun, sandi) {
  await judul("Masuk").waitFor();
  await h.getByLabel("Nama pengguna").fill(akun);
  await h.getByLabel("Sandi", { exact: true }).fill(sandi);
  await tombol("Masuk").click();
}

async function keluar() {
  await tombol("Keluar").first().click();
  await judul("Masuk").waitFor();
}

// ── A · kurator memutus ──────────────────────────────────────────────
await h.goto(ALAMAT);
await masuk(KURATOR, SANDI_KURATOR);
await judul("Antrean kurasi").waitFor();
pastikan((await h.getByRole("navigation").count()) === 0, "K-8: kurator tanpa navigasi pengguna");
pastikan((await h.getByText("(contoh bukti)").count()) === 5, "S-15 memuat lima kandidat");
pastikan(!/\bK[1-8]\b|\bTL-\d|skor/i.test(await teks()), "S-15 tanpa kode kategori, kode TL, maupun skor");
await h.screenshot({ path: join(KELUAR, "s15-antrean.png"), fullPage: true });

async function setujui(nama) {
  const satu = baris(nama);
  await satu.getByRole("button", { name: "Setujui", exact: true }).click();
  await satu.getByLabel("Catatan singkat").fill("Layak tayang untuk bukti");
  await satu.getByRole("button", { name: "Kirim putusan" }).click();
  await h.getByRole("heading", { name: nama }).first().waitFor();
}

await setujui("Supervisi akademik terjadwal (contoh bukti)");

await baris("Pembelajaran berdiferensiasi (contoh bukti)").getByRole("button", { name: "Sunting" }).click();
await judul("Sunting parafrase").waitFor();
pastikan((await h.locator("input, textarea").count()) === 5, "S-16: empat bidang parafrase dan catatan saja");
await h.screenshot({ path: join(KELUAR, "s16-sunting.png"), fullPage: true });
await h.getByLabel("Judul", { exact: true }).fill("Pembelajaran berdiferensiasi bertahap (contoh bukti)");
await h.getByLabel("Catatan singkat").fill("Judul diperjelas");
await tombol("Simpan dan setujui").click();
await judul("Antrean kurasi").waitFor();

await setujui("Pelaporan dana sekolah (contoh bukti)");
await setujui("Persiapan akreditasi (contoh bukti)");

const tolak = baris("Program kesiswaan (contoh bukti)");
await tolak.getByRole("button", { name: "Tolak", exact: true }).click();
await tolak.getByLabel("Tidak relevan dengan konteks sekolah dasar Indonesia").check();
await tolak.getByRole("button", { name: "Kirim putusan" }).click();
await h.getByText("Antrean kosong. Kandidat masuk setelah lolos penyaringan oleh tim.").waitFor();
pastikan(
  (await h.getByText("Pembelajaran berdiferensiasi bertahap (contoh bukti)").count()) === 1,
  "suntingan yang tayang, bukan naskah asli",
);
await h.screenshot({ path: join(KELUAR, "s15-sesudah-putusan.png"), fullPage: true });
await keluar();

// ── B · pengguna: aktivasi, beranda, detail, belum relevan ───────────
await masuk(PENGGUNA, SANDI_PENGGUNA);
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
pastikan(true, "R-07 fitur 030: aktivasi pertama berakhir di Tanya");

await h.getByRole("navigation").getByRole("button", { name: "Beranda" }).click();
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
const judulKartu = await kartu().locator("strong").allTextContents();
pastikan(judulKartu.length === 3, `pagu tiga butir per hari: ${judulKartu.length}`);
pastikan(
  JSON.stringify(judulKartu) ===
    JSON.stringify([
      "Supervisi akademik terjadwal (contoh bukti)",
      "Pembelajaran berdiferensiasi bertahap (contoh bukti)",
      "Pelaporan dana sekolah (contoh bukti)",
    ]),
  `urutan mengikuti prioritas, butir tertolak tidak tampil: ${JSON.stringify(judulKartu)}`,
);
pastikan(!/\bK[1-8]\b/.test(await teks()), "S-05 tanpa kode kategori");
await h.screenshot({ path: join(KELUAR, "s05-beranda.png"), fullPage: true });

await kartu().filter({ hasText: "Pembelajaran berdiferensiasi bertahap" }).click();
await h.getByRole("heading", { level: 1, name: "Pembelajaran berdiferensiasi bertahap (contoh bukti)" }).waitFor();
pastikan((await judul("Mengapa relevan untuk sekolah Anda").count()) === 1, "S-06 blok mengapa relevan");
await h.screenshot({ path: join(KELUAR, "s06-detail.png"), fullPage: true });
await tombol("Belum relevan").click();
await h.getByLabel("Mengapa butir ini belum relevan bagi sekolah Anda?").fill("Belum menjadi fokus semester ini");
await tombol("Kirim").click();
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
pastikan((await kartu().count()) === 2, "FR-G07: butir yang belum relevan keluar dari beranda");
await h.reload();
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
pastikan((await kartu().count()) === 2, "K-2: muat ulang membaca butir hari ini yang sama");
await keluar();

// ── C · kurator menarik ──────────────────────────────────────────────
await masuk(KURATOR, SANDI_KURATOR);
await judul("Antrean kurasi").waitFor();
const tarik = baris("Supervisi akademik terjadwal (contoh bukti)");
await tarik.getByRole("button", { name: "Tarik" }).click();
await tarik.getByLabel("Isi butir keliru").check();
await tarik.getByLabel("Catatan singkat").fill("Contoh angka keliru");
await tarik.getByRole("button", { name: "Kirim putusan" }).click();
await h.waitForFunction(() => !document.body.textContent?.includes("Supervisi akademik terjadwal"));
await h.screenshot({ path: join(KELUAR, "s15-sesudah-tarik.png"), fullPage: true });
await keluar();

// ── D · pengguna: butir yang ditarik lenyap; luring membaca salinan ──
await masuk(PENGGUNA, SANDI_PENGGUNA);
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
const sisa = await kartu().locator("strong").allTextContents();
pastikan(
  JSON.stringify(sisa) === JSON.stringify(["Pelaporan dana sekolah (contoh bukti)"]),
  `M-13: butir ditarik keluar dari beranda hari itu: ${JSON.stringify(sisa)}`,
);
await h.waitForTimeout(500);
await konteks.setOffline(true);
await h.getByRole("navigation").getByRole("button", { name: "Tanya" }).click();
await h.getByRole("navigation").getByRole("button", { name: "Beranda" }).click();
await h.getByText("Sedang tidak terhubung. Ini salinan butir hari ini dari perangkat Anda.").waitFor();
pastikan((await kartu().count()) === 1, "KL-E: salinan butir hari ini terbaca tanpa koneksi");
await kartu().first().click();
await h.getByText("Sedang tidak terhubung. Ini salinan yang tersimpan di perangkat Anda.").waitFor();
pastikan(true, "KL-E: isi lengkap butir terbaca dari salinan");
await h.screenshot({ path: join(KELUAR, "s06-luring.png"), fullPage: true });
await konteks.setOffline(false);

console.log("respons 404:", JSON.stringify(takAda));
await peramban.close();
// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama, 403 atas
// ringkasan akun kurator (K-8), dan permintaan yang gagal saat luring.
const nyata = masalah.filter(
  (m) => !/status of 40[13]/.test(m) && !/ERR_INTERNET_DISCONNECTED|Failed to fetch/.test(m),
);
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
