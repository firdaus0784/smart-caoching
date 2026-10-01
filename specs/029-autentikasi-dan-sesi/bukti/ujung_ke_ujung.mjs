// Bukti ujung ke ujung fitur 029 — T-9, `plan.md` Bagian 12.2.
//
// Di LUAR `make check`, sama dengan fitur 027 dan 028: Playwright alat global.
//
// Prasyarat, dari akar repositori:
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <akun> --peran pengguna
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   npm --prefix web run build
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   AKUN_UJI=<akun> SANDI_UJI=<sandi> node specs/029-autentikasi-dan-sesi/bukti/ujung_ke_ujung.mjs
//
// Yang dibuktikan: S-01 tampil tanpa sesi; penolakan satu kalimat; masuk
// memasang kuki `__Host-sesi` yang HttpOnly, Secure, dan SameSite=Strict pada
// http://127.0.0.1 — diverifikasi, bukan diandaikan (plan Bagian 12.2); sesi
// bertahan sesudah muat ulang; Keluar membersihkan peramban; dan kuki lama
// yang disalin sebelum keluar DITOLAK peladen (R-06).

import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
const API = process.env.ALAMAT_API ?? "http://127.0.0.1:8000";
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

async function percakapanDenganKuki(nilai) {
  const r = await fetch(`${API}/api/v1/percakapan`, { headers: { Cookie: `__Host-sesi=${nilai}` } });
  return r.status;
}

const peramban = await chromium.launch();
const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 } });
const h = await konteks.newPage();
h.on("console", (p) => p.type() === "error" && masalah.push(`konsol: ${p.text()}`));
h.on("pageerror", (g) => masalah.push(`halaman: ${g.message}`));

// ── 1. tanpa sesi: S-01 ──
await h.goto(ALAMAT);
await h.getByRole("heading", { name: "Masuk", exact: true }).waitFor();
pastikan((await h.getByRole("heading", { name: "Tanya", exact: true }).count()) === 0, "tanpa sesi, layar Tanya tidak tampil");
await h.screenshot({ path: join(KELUAR, "s01-masuk.png"), fullPage: true });

// ── 2. penolakan satu kalimat ──
await h.getByLabel("Nama pengguna").fill(AKUN);
await h.getByLabel("Sandi", { exact: true }).fill("salah-salah-salah-salah");
await h.getByRole("button", { name: "Masuk" }).click();
const tolak = (await h.getByRole("alert").textContent())?.trim();
pastikan(tolak === "Nama pengguna atau sandi belum cocok. Periksa lagi, atau hubungi tim peneliti.", `penolakan: "${tolak}"`);
pastikan((await h.getByLabel("Sandi", { exact: true }).inputValue()) === "", "isian sandi dikosongkan sesudah dikirim");
await h.screenshot({ path: join(KELUAR, "s01-ditolak.png"), fullPage: true });

// ── 3. masuk; atribut kuki diverifikasi pada peramban sungguhan ──
await h.getByLabel("Sandi", { exact: true }).fill(SANDI);
await h.getByRole("button", { name: "Masuk" }).click();
await h.getByRole("heading", { name: "Tanya", exact: true }).waitFor();
const kuki = (await konteks.cookies()).find((k) => k.name === "__Host-sesi");
pastikan(kuki !== undefined, "peramban MENERIMA kuki __Host-sesi pada http://127.0.0.1");
pastikan(kuki?.httpOnly === true, "kuki HttpOnly");
pastikan(kuki?.secure === true, "kuki Secure");
pastikan(kuki?.sameSite === "Strict", `kuki SameSite=${kuki?.sameSite}`);
pastikan(kuki?.path === "/", "kuki Path=/");
pastikan(!(await h.evaluate(() => document.cookie)).includes("sesi"), "kode halaman tidak dapat membaca kuki sesi");
const dirahasiakan = JSON.stringify(await h.evaluate(() => ({ ...localStorage })));
pastikan(!dirahasiakan.includes(SANDI) && !dirahasiakan.includes(kuki?.value ?? "-"), "sandi dan pengenal sesi tidak ada di simpanan lokal");

// ── 4. bertanya, muat ulang, sesi bertahan ──
await h.getByLabel("Pertanyaan Anda").fill(`Bagaimana menyusun jadwal supervisi? (${Date.now().toString(36)})`);
await h.getByRole("button", { name: "Kirim pertanyaan" }).click();
await h.getByTestId("blok-jawaban").waitFor();
await h.reload();
await h.getByRole("heading", { name: "Tanya", exact: true }).waitFor();
pastikan(true, "sesudah muat ulang tetap masuk");
await h.screenshot({ path: join(KELUAR, "tanya-sesudah-masuk.png"), fullPage: true });

// ── 5. kuki disalin, lalu keluar: kuki lama ditolak peladen (R-06) ──
const salinan = kuki?.value ?? "";
pastikan((await percakapanDenganKuki(salinan)) === 200, "kendali: kuki yang sama diterima sebelum keluar");
await h.getByLabel("Pertanyaan Anda").fill("Draf yang tidak boleh diwarisi pemakai berikutnya");
await h.getByRole("button", { name: "Keluar" }).click();
await h.getByRole("heading", { name: "Masuk", exact: true }).waitFor();
pastikan((await percakapanDenganKuki(salinan)) === 401, "R-06: kuki yang disalin sebelum keluar DITOLAK sesudahnya");
const sisa = await h.evaluate(() => Object.keys(localStorage));
pastikan(!sisa.includes("smart-coaching:draf-tanya") && !sisa.includes("smart-coaching:percakapan-aktif"), `K-6: simpanan sesudah keluar ${JSON.stringify(sisa)}`);
pastikan((await konteks.cookies()).every((k) => k.name !== "__Host-sesi"), "kuki sesi dihapus dari peramban");
await h.screenshot({ path: join(KELUAR, "sesudah-keluar.png"), fullPage: true });

await peramban.close();

// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama dan atas
// masuk dengan sandi salah — keduanya jawaban sah, bukan kegagalan.
const nyata = masalah.filter((m) => !/status of 401/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
