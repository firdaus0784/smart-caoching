// Bukti ujung ke ujung fitur 036 — T-8, `plan.md` Bagian 9.2.
//
// Di LUAR `make check`: Playwright alat global, psql dijalankan sebagai
// pengelola untuk membaca apa yang tersimpan — bukan untuk mengubahnya.
//
// NASKAH: naskah **uji** persetujuan dipasang sementara pada
// `web/public/naskah/` lalu dihapus; tidak pernah di-commit (KB-164).
//
// `make jalan` menandai setiap peristiwa `pengembangan` (fitur 034, K-4), dan
// analitik memisahkannya (R-05 fitur 035): tabel penilaian S-18 karena itu
// bernilai nol, dan `answer_rated` diperiksa langsung pada tabelnya.
//
// Prasyarat, dari akar repositori:
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <pengguna> --peran pengguna
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <kurator> --peran kurator
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.akun buat --id <peneliti> --peran peneliti
//   (naskah uji dipasang)  npm --prefix web run build
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   PENGGUNA=<id> SANDI_PENGGUNA=<sandi> KURATOR=<id> SANDI_KURATOR=<sandi> \
//     PENELITI=<id> SANDI_PENELITI=<sandi> PGHOST=/tmp PGPORT=55432 PGUSER=pengelola \
//     node specs/036-penilaian-jawaban-dan-aduan/bukti/ujung_ke_ujung.mjs

import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
const { PENGGUNA, SANDI_PENGGUNA, KURATOR, SANDI_KURATOR, PENELITI, SANDI_PENELITI } = process.env;
if (!PENGGUNA || !SANDI_PENGGUNA || !KURATOR || !SANDI_KURATOR || !PENELITI || !SANDI_PENELITI) {
  throw new Error("PENGGUNA, KURATOR, PENELITI beserta sandinya wajib diisi");
}
const KELUAR = dirname(fileURLToPath(import.meta.url));
const TANDA = Math.random().toString(36).replace(/[^a-z]/g, "").slice(0, 6);
const P_DIKIRIM = `Bagaimana dasar supervisi akademik yang adil, kasus ${TANDA}?`;
const P_TIDAK_DIKIRIM = `Bagaimana menyusun rencana kerja sekolah, kasus ${TANDA}?`;
const ALASAN = "Dasar supervisi akademik seharusnya ada.";

const masalah = [];
function pastikan(syarat, pesan) {
  if (syarat) console.log(`ok  : ${pesan}`);
  else {
    masalah.push(pesan);
    console.error(`GAGAL: ${pesan}`);
  }
}
const psql = (kueri) => execFileSync("psql", ["-d", "smart_coaching", "-At"], { encoding: "utf-8", input: kueri }).trim();
const kutip = (teks) => `'${teks.replaceAll("'", "''")}'`;

const peramban = await chromium.launch();
const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 } });
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

async function tanya(pertanyaan) {
  await h.getByLabel("Pertanyaan Anda").fill(pertanyaan);
  const jawab = h.waitForResponse((r) => r.url().endsWith("/tanya") && r.request().method() === "POST");
  await tombol("Kirim pertanyaan").click();
  const id = (await (await jawab).json()).id_pesan;
  await h.getByTestId("blok-jawaban").waitFor();
  return { id, blok: h.getByRole("group", { name: "Nilai jawaban" }) };
}

async function kirimPenilaian(blok) {
  const jawaban = h.waitForResponse((r) => r.url().includes("/penilaian") && r.request().method() === "POST");
  await blok.getByRole("button", { name: "Kirim penilaian" }).click();
  const r = await jawaban;
  await blok.getByText("Terima kasih, penilaian Anda tersimpan.").waitFor();
  return r.status();
}

// ── A · pengguna menilai dua jawaban ─────────────────────────────────
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

const pertama = await tanya(P_DIKIRIM);
pastikan((await pertama.blok.getByLabel("Kirim pertanyaan dan jawaban ini kepada kurator").count()) === 0, "P-2 B: centang tidak tampil sebelum keliru dipilih");
await tombol("Laporkan bahwa ini seharusnya ada").click();
pastikan(await pertama.blok.getByLabel("Keliru").isChecked(), "R-10: laporan seharusnya ada memilih keliru");
await pertama.blok.getByLabel("Alasan, boleh dikosongkan").fill(ALASAN);
await pertama.blok.getByLabel("Kirim pertanyaan dan jawaban ini kepada kurator").check();
pastikan((await kirimPenilaian(pertama.blok)) === 200, "penilaian keliru beserta centang tersimpan");
await h.screenshot({ path: join(KELUAR, "s09-nilai-jawaban.png"), fullPage: true });

const kedua = await tanya(P_TIDAK_DIKIRIM);
await kedua.blok.getByLabel("Keliru").check();
pastikan((await kirimPenilaian(kedua.blok)) === 200, "penilaian keliru tanpa centang tersimpan");
await tombol("Keluar").first().click();

// ── B · kurator membuka S-17 ─────────────────────────────────────────
const pseudonimPengguna = psql(`SELECT pseudonim FROM akun.pengguna WHERE id = ${kutip(PENGGUNA)};`);
const pseudonimKurator = psql(`SELECT pseudonim FROM akun.pengguna WHERE id = ${kutip(KURATOR)};`);
await masuk(KURATOR, SANDI_KURATOR);
await judul("Antrean kurasi").waitFor();
pastikan((await h.getByRole("navigation").count()) === 0, "S-17: cangkang kurator tanpa navigasi pengguna");
await tombol("Aduan jawaban").click();
await h.getByRole("heading", { level: 1, name: "Aduan jawaban" }).waitFor();
const kartu = h.getByRole("listitem").filter({ hasText: P_DIKIRIM });
await kartu.waitFor();
pastikan((await h.getByText(P_TIDAK_DIKIRIM).count()) === 0, "P-2 B: penilaian tanpa centang tidak menjadi aduan");
pastikan((await kartu.getByText(ALASAN).count()) === 1, "S-17: alasan peserta tampil");
pastikan((await kartu.getByText("Ini jawaban pada saat diadukan, bukan jawaban sistem sekarang.").count()) === 1, "S-17: jawaban dinyatakan jawaban saat diadukan");
const teksHalaman = await h.locator("body").innerText();
pastikan(!teksHalaman.includes(PENGGUNA) && !teksHalaman.includes(pseudonimPengguna) && !teksHalaman.includes(pertama.id), "R-06: tanpa akun, pseudonim, maupun id pesan peserta");
await h.screenshot({ path: join(KELUAR, "s17-aduan.png"), fullPage: true });
await kartu.getByLabel("Sumber diajukan lewat kanal").check();
await kartu.getByLabel("Catatan tindak lanjut").fill("Sumber supervisi akademik diajukan lewat kanal regulasi.");
await kartu.getByRole("button", { name: "Simpan tindak lanjut" }).click();
await h.getByText(P_DIKIRIM).waitFor({ state: "detached" });
pastikan(true, "tindak lanjut tercatat; aduan keluar dari antrean");
await tombol("Keluar").click();

// ── C · peneliti melihat tabel penilaian ─────────────────────────────
await masuk(PENELITI, SANDI_PENELITI);
await h.getByRole("heading", { level: 1, name: "Analitik penelitian" }).waitFor();
const tabel = h.getByRole("table", { name: "Penilaian jawaban" });
const baris = (await tabel.getByRole("row").allInnerTexts()).slice(1).map((t) => t.replace(/\s+/g, " ").trim());
pastikan(baris.join("|") === "Membantu 0|Tidak membantu 0|Keliru 0", `S-18: tabel penilaian, peristiwa pengembangan terpisah — ${baris.join("|")}`);
await tombol("Keluar").click();
await peramban.close();

// ── D · yang tersimpan ───────────────────────────────────────────────
const pesan = psql(
  `SELECT count(*) FROM riwayat.pesan m JOIN riwayat.percakapan c USING (id_percakapan) WHERE c.pemilik = ${kutip(pseudonimPengguna)};`,
);
pastikan(pesan === "2", `P-1 A: ${pesan} tanggapan tercatat sebagai catatan audit`);
const aduan = psql(
  `SELECT count(*) || '/' || bool_or(tanggapan ? 'id_pesan') FROM kurasi.aduan WHERE pertanyaan IN (${kutip(P_DIKIRIM)}, ${kutip(P_TIDAK_DIKIRIM)});`,
);
pastikan(aduan === "1/false", `P-2 B, R-06: satu aduan, salinannya tanpa id_pesan (${aduan})`);
const tindak = psql(
  `SELECT t.tindak_lanjut || '/' || (t.pseudonim_kurator = ${kutip(pseudonimKurator)}) FROM kurasi.tindak_lanjut_aduan t JOIN kurasi.aduan a ON a.nomor = t.nomor_aduan WHERE a.pertanyaan = ${kutip(P_DIKIRIM)};`,
);
pastikan(tindak === "sumber_diajukan/true", `jejak tindak lanjut berperan dan berpseudonim kurator (${tindak})`);
const peristiwa = psql(
  `SELECT string_agg((SELECT string_agg(k, ',' ORDER BY k) FROM jsonb_object_keys(properti) k) || ':' || versi_aplikasi || ':' || (properti::text LIKE ${kutip(`%${ALASAN}%`)}), ' ') FROM telemetri.peristiwa WHERE pseudonim = ${kutip(pseudonimPengguna)} AND jenis = 'answer_rated';`,
);
pastikan(
  peristiwa === "beralasan,id_pesan,nilai:pengembangan:false beralasan,id_pesan,nilai:pengembangan:false",
  `P-4 B: dua answer_rated berproperti tiga, tanpa teks alasan (${peristiwa})`,
);

writeFileSync(
  join(KELUAR, "penilaian-dan-aduan.txt"),
  [
    `Pertanyaan dengan centang : ${P_DIKIRIM}`,
    `Pertanyaan tanpa centang  : ${P_TIDAK_DIKIRIM}`,
    "",
    `Tanggapan tercatat bagi peserta (riwayat.pesan) : ${pesan}`,
    `Aduan / salinan memuat id_pesan                 : ${aduan}`,
    `Tindak lanjut / pseudonim kurator dari sesi     : ${tindak}`,
    `answer_rated (kunci properti : versi : teks alasan ikut) : ${peristiwa}`,
    "",
  ].join("\n"),
);

// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama, 403 atas
// ringkasan akun dan antrean bagi kurator dan peneliti (K-8 fitur 013, P-5 fitur 035).
const nyata = masalah.filter((m) => !/status of 40[13]/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
