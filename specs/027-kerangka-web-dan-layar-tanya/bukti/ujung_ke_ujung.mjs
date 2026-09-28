// Bukti ujung ke ujung fitur 027 — T-7, `plan.md` Bagian 6.2.
//
// Di LUAR `make check`, disengaja: Playwright alat global lingkungan ini,
// bukan ketergantungan proyek, dan gerbang yang bergantung pada alat di luar
// daftar persetujuan adalah ketergantungan tersembunyi.
//
// Prasyarat, dijalankan dari akar repositori:
//   make jalan                                   (peladen 127.0.0.1:8000)
//   npm --prefix web run build
//   npx --prefix web vite preview --host 127.0.0.1 --port 4173 --strictPort
//     (dijalankan di dalam web/)
//   node specs/027-kerangka-web-dan-layar-tanya/bukti/ujung_ke_ujung.mjs
//
// Halaman dilayani dari HASIL BUILD, sehingga CSP ketat `index.html` ikut
// teruji. Pelanggaran CSP dan galat halaman dicatat dan menggagalkan skrip.
//
// Tiga keadaan:
//   tidak-ditemukan  — tanggapan SUNGGUHAN dari `make jalan` (korpus kosong)
//   normal           — tanggapan TIRUAN disisipkan pada lapisan jaringan
//                      peramban; backend belum dapat menghasilkan `kuat`
//   luring           — peramban diputus sesudah halaman termuat, lalu dimuat
//                      ulang tanpa koneksi (cangkang dari service worker)

import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const wajib = createRequire(import.meta.url);
const { chromium } = wajib(process.env.PLAYWRIGHT_MODUL ?? "/opt/node22/lib/node_modules/playwright");

const ALAMAT = process.env.ALAMAT_WEB ?? "http://127.0.0.1:4173/";
const KELUAR = dirname(fileURLToPath(import.meta.url));

const TIRUAN = {
  id_pesan: "tiruan-bukti",
  status_dasar: "kuat",
  ringkasan_tindakan: [
    "Susun jadwal supervisi akademik bersama guru.",
    "Umumkan jadwal pada rapat pekan ini.",
    "Catat hasil supervisi pada instrumen yang sama.",
  ],
  penjelasan:
    "Supervisi akademik dilakukan terjadwal dan diketahui guru sejak awal semester. " +
    "Tanggapan ini TIRUAN untuk bukti tampilan, bukan jawaban sistem.",
  klaim: [{ teks: "Supervisi dilakukan terjadwal.", id_segmen: ["seg-tiruan-1"] }],
  sitasi: [
    {
      id_dokumen: "dok-tiruan-1",
      judul: "Peraturan Tiruan tentang Supervisi",
      penerbit: "Penerbit Tiruan",
      tahun: 2026,
      bagian: "Pasal 7 ayat (2)",
      status_keberlakuan: "diubah",
      rujukan_pengganti: "Peraturan Tiruan Nomor 5 Tahun 2026",
      tautan: null,
    },
  ],
  bacaan_lanjutan: [{ judul: "Panduan Tiruan Supervisi", tautan: "/tidak-ada" }],
  catatan_keberlakuan: "Pasal 7 diubah oleh Peraturan Tiruan Nomor 5 Tahun 2026.",
  penafian: "Keputusan akhir berada pada kepala sekolah.",
  versi: { model: "tiruan", indeks: "tiruan", kode: "tiruan" },
};

const masalah = [];

function awasi(halaman, nama) {
  halaman.on("console", (p) => {
    if (p.type() === "error") masalah.push(`${nama}: konsol: ${p.text()}`);
  });
  halaman.on("pageerror", (g) => masalah.push(`${nama}: halaman: ${g.message}`));
}

async function tanyakan(halaman, teks) {
  await halaman.getByLabel("Pertanyaan Anda").fill(teks);
  await halaman.getByRole("button", { name: "Kirim pertanyaan" }).click();
}

function pastikan(syarat, pesan) {
  if (!syarat) {
    masalah.push(pesan);
    console.error(`GAGAL: ${pesan}`);
  } else console.log(`ok  : ${pesan}`);
}

const peramban = await chromium.launch();
const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 } });

// ── tidak-ditemukan: sungguhan dari `make jalan` ──
{
  const h = await konteks.newPage();
  awasi(h, "tidak-ditemukan");
  await h.goto(ALAMAT);
  await tanyakan(h, "Bagaimana menyusun jadwal supervisi akademik?");
  const blok = h.getByTestId("blok-jawaban");
  await blok.waitFor();
  const penanda = await h.getByTestId("penanda-dasar").textContent();
  pastikan(penanda === "Tidak ditemukan dasar rujukan", `penanda sungguhan: "${penanda}"`);
  pastikan(
    (await blok.textContent()).includes("Belum ada dokumen rujukan yang memuat jawaban ini."),
    "kalimat K-2 tampil",
  );
  pastikan((await h.getByRole("alert").count()) === 0, "tidak-ditemukan bukan galat");
  await h.screenshot({ path: join(KELUAR, "tidak-ditemukan.png"), fullPage: true });
  await h.close();
}

// ── normal: tanggapan TIRUAN pada lapisan jaringan peramban ──
{
  const h = await konteks.newPage();
  awasi(h, "normal");
  await h.route("**/api/v1/tanya", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(TIRUAN) }),
  );
  await h.goto(ALAMAT);
  await tanyakan(h, "Bagaimana menyusun jadwal supervisi akademik?");
  await h.getByTestId("blok-jawaban").waitFor();
  const penanda = h.getByTestId("penanda-dasar");
  const ringkasan = h.getByTestId("ringkasan");
  const atasPenanda = (await penanda.boundingBox()).y;
  const atasRingkasan = (await ringkasan.boundingBox()).y;
  pastikan(atasPenanda < atasRingkasan, "penanda tampil di atas ringkasan");
  const tinggiTombol = (await h.getByRole("button", { name: "Salin ringkasan" }).boundingBox())
    .height;
  pastikan(tinggiTombol >= 44, `sasaran ketuk tombol salin ${tinggiTombol}px`);
  await h.screenshot({ path: join(KELUAR, "normal-tiruan.png"), fullPage: true });
  await h.close();
}

// ── luring: KL-E, lalu muat ulang tanpa koneksi (R-15, R-09) ──
{
  const h = await konteks.newPage();
  awasi(h, "luring");
  await h.goto(ALAMAT);
  await h.evaluate(() => navigator.serviceWorker.ready);
  // Muat ulang sekali selagi terhubung: service worker kini mengendalikan
  // halaman dan menyalin cangkangnya.
  await h.reload();
  await h.evaluate(() => navigator.serviceWorker.ready);
  await konteks.setOffline(true);
  await tanyakan(h, "Pertanyaan yang diketik saat sinyal hilang");
  const peringatan = await h.getByRole("alert").textContent();
  pastikan(
    peringatan.includes("Sedang tidak terhubung. Pertanyaan Anda tersimpan sebagai draf."),
    `KL-E: "${peringatan.trim()}"`,
  );
  await h.screenshot({ path: join(KELUAR, "luring.png"), fullPage: true });

  await h.reload();
  const isian = await h.getByLabel("Pertanyaan Anda").inputValue();
  pastikan(
    isian === "Pertanyaan yang diketik saat sinyal hilang",
    "cangkang terbuka tanpa koneksi dan draf bertahan sesudah muat ulang",
  );
  await h.screenshot({ path: join(KELUAR, "luring-muat-ulang.png"), fullPage: true });
  await konteks.setOffline(false);
  await h.close();
}

await peramban.close();

// Galat konsol yang diharapkan pada keadaan luring: permintaan yang memang
// gagal karena koneksi diputus. Selebihnya — pelanggaran CSP terutama — masalah.
const nyata = masalah.filter((m) => !/^luring: konsol: Failed to load resource/.test(m));
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
