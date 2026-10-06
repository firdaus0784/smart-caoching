// Bukti ujung ke ujung fitur 034 — T-6, `plan.md` Bagian 9.2.
//
// Di LUAR `make check`: Playwright alat global, psql untuk membaca peristiwa.
//
// NASKAH: bukti ini memakai **naskah uji** yang dipasang sementara pada
// `web/public/naskah/persetujuan.json` dan dihapus sesudahnya. Naskah itu
// bertanda tegas bukan naskah ET-02 dan tidak pernah di-commit — agen tidak
// menulis naskah persetujuan (KB-164).
//
// ANTREAN: diisi `specs/013-kurasi-dan-penemuan-harian/bukti/isi_antrean_bukti.py`;
// butirnya buatan dan bertanda "(contoh bukti)".
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
//     node specs/034-penyimpanan-dan-penyambungan-telemetri/bukti/ujung_ke_ujung.mjs

import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
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
const PERTANYAAN = "Bagaimana menyusun jadwal supervisi akademik yang adil bagi semua guru?";
const ALASAN = "Belum menjadi fokus semester ini";

const masalah = [];
function pastikan(syarat, pesan) {
  if (syarat) console.log(`ok  : ${pesan}`);
  else {
    masalah.push(pesan);
    console.error(`GAGAL: ${pesan}`);
  }
}

/** Peristiwa milik akun pengguna, terlama lebih dulu — dibaca langsung dari tabel. */
function peristiwa() {
  const keluaran = execFileSync(
    "psql",
    [
      "-d",
      "smart_coaching",
      "-At",
      "-v",
      `akun=${PENGGUNA}`,
    ],
    {
      encoding: "utf-8",
      // Dari stdin, bukan `-c`: hanya begitu psql mengganti `:'akun'` dengan aman.
      input:
        "SELECT json_agg(json_build_object('jenis', jenis, 'properti', properti, " +
        "'versi_aplikasi', versi_aplikasi, 'versi_model', versi_model, 'pseudonim', pseudonim) " +
        "ORDER BY nomor) FROM telemetri.peristiwa WHERE pseudonim = " +
        "(SELECT pseudonim FROM akun.pengguna WHERE id = :'akun');",
    },
  ).trim();
  return keluaran ? JSON.parse(keluaran) : [];
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

async function keluar() {
  await tombol("Keluar").first().click();
  await judul("Masuk").waitFor();
}

async function tanya() {
  await nav("Tanya").click();
  await judul("Tanya").waitFor();
  await h.getByLabel("Pertanyaan Anda").fill(PERTANYAAN);
  const jawab = h.waitForResponse((r) => r.url().endsWith("/tanya") && r.request().method() === "POST");
  await tombol("Kirim pertanyaan").click();
  pastikan((await jawab).status() === 200, "Tanya dijawab");
}

// ── A · kurator menyetujui empat butir ───────────────────────────────
await h.goto(ALAMAT);
await masuk(KURATOR, SANDI_KURATOR);
await judul("Antrean kurasi").waitFor();
for (const nama of [
  "Supervisi akademik terjadwal (contoh bukti)",
  "Pembelajaran berdiferensiasi (contoh bukti)",
  "Pelaporan dana sekolah (contoh bukti)",
  "Persiapan akreditasi (contoh bukti)",
]) {
  const satu = baris(nama);
  await satu.getByRole("button", { name: "Setujui", exact: true }).click();
  await satu.getByLabel("Catatan singkat").fill("Layak tayang untuk bukti");
  await satu.getByRole("button", { name: "Kirim putusan" }).click();
  await h.getByRole("heading", { name: nama }).first().waitFor();
}
await keluar();
pastikan(peristiwa().length === 0, "sebelum pengguna masuk, tidak ada peristiwanya");

// ── B · pengguna menyetujui, lalu alur penuh ─────────────────────────
await masuk(PENGGUNA, SANDI_PENGGUNA);
await judul("Persetujuan penelitian").waitFor();
pastikan((await h.getByText("NASKAH UJI").count()) > 0, "naskah uji, bukan naskah ET-02");
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
// Masuk terjadi sebelum persetujuan: `session_start` sesi ini tidak terekam (C-04).
pastikan(peristiwa().length === 0, "masuk sebelum menyetujui tidak terekam");

// Keluar lalu masuk lagi agar sesi dimulai dengan persetujuan aktif.
await keluar();
await masuk(PENGGUNA, SANDI_PENGGUNA);
await h.getByRole("navigation").waitFor();
await tanya();
await nav("Beranda").click();
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
pastikan((await kartu().count()) === 3, "beranda memuat tiga butir");
await h.reload();
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
await kartu().filter({ hasText: "Pembelajaran berdiferensiasi" }).click();
await h.getByRole("heading", { level: 1, name: "Pembelajaran berdiferensiasi (contoh bukti)" }).waitFor();
await tombol("Belum relevan").click();
await h.getByLabel("Mengapa butir ini belum relevan bagi sekolah Anda?").fill(ALASAN);
await tombol("Kirim").click();
await judul("Butir hari ini").waitFor();
await keluar();

const tercatat = peristiwa();
const jenis = tercatat.map((p) => p.jenis);
console.log("peristiwa:", JSON.stringify(jenis));
pastikan(
  JSON.stringify(jenis) ===
    JSON.stringify([
      "session_end",
      "session_start",
      "discovery_served",
      "discovery_served",
      "discovery_served",
      "question_asked",
      "answer_served",
      "discovery_opened",
      "discovery_dismissed",
      "session_end",
    ]),
  "urutan sesuai alur; muat ulang tidak mencatat ulang; pengambilan latar bukan dibuka (K-7)",
);
pastikan(jenis.filter((j) => j === "discovery_opened").length === 1, "TK-74: satu butir dibuka, satu peristiwa");
pastikan(tercatat.every((p) => /^psd_[a-z]{16}$/.test(p.pseudonim)), "C-05: pemilik berpseudonim");
pastikan(tercatat.every((p) => p.versi_aplikasi === "pengembangan"), "K-4: versi aplikasi pengembangan");
const jawaban = tercatat.find((p) => p.jenis === "answer_served");
pastikan(jawaban.versi_model === "belum-dipasang-pengembangan", "K-4: versi model dari tanggapan");
pastikan(
  tercatat.filter((p) => p.jenis !== "answer_served").every((p) => p.versi_model === "tanpa_model"),
  "K-4: selebihnya tanpa_model",
);
const tanyaan = tercatat.find((p) => p.jenis === "question_asked");
pastikan(tanyaan.properti.panjang_pertanyaan === PERTANYAAN.length, "R-06: panjang pertanyaan");
const tolak = tercatat.find((p) => p.jenis === "discovery_dismissed");
pastikan(tolak.properti.panjang_alasan === ALASAN.length, "R-06: panjang alasan");
const mentah = JSON.stringify(tercatat);
pastikan(!mentah.includes("supervisi akademik yang adil") && !mentah.includes("fokus semester"), "R-06: teks pengguna tidak tersimpan");

// ── C · mencabut; permintaan berikutnya tidak menambah peristiwa ─────
await masuk(PENGGUNA, SANDI_PENGGUNA);
await nav("Tanya").click();
await judul("Tanya").waitFor();
await tombol("Persetujuan penelitian").click();
await h.getByText("Anda sudah menyetujui perekaman data penelitian.").waitFor();
await tombol("Cabut persetujuan").click();
await judul("Tanya").waitFor();
const sebelum = peristiwa().length;
await tanya();
await nav("Beranda").click();
await judul("Butir hari ini").waitFor();
await kartu().first().waitFor();
await kartu().first().click();
await h.getByRole("heading", { level: 1 }).waitFor();
await h.screenshot({ path: join(KELUAR, "sesudah-cabut-butir.png"), fullPage: true });
await tombol("Kembali ke beranda").click();
await judul("Butir hari ini").waitFor();
await keluar();
const sesudah = peristiwa();
pastikan(sesudah.length === sebelum, `C-04: sesudah mencabut tetap ${sebelum} peristiwa (${sesudah.length})`);

writeFileSync(
  join(KELUAR, "peristiwa.json"),
  JSON.stringify(
    sesudah.map(({ pseudonim, ...sisa }) => ({ pseudonim: pseudonim.slice(0, 4) + "…", ...sisa })),
    null,
    2,
  ) + "\n",
);

await peramban.close();
// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama, dan 403 atas
// ringkasan akun kurator (K-8 fitur 013) — keduanya jawaban sah.
const nyata = masalah.filter((m) => !/status of 40[13]/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
