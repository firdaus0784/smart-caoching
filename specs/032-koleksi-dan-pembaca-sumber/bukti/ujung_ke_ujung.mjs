// Bukti ujung ke ujung fitur 032 — T-8, `plan.md` Bagian 10.2.
//
// Di LUAR `make check`: Playwright alat global, psql dijalankan sebagai
// pengelola untuk membaca apa yang tersimpan — bukan untuk mengubahnya.
//
// DUA HAL BUATAN, dinyatakan, bukan disamarkan:
//
// 1. **Jawaban S-09 buatan naskah ini.** Jalur penjawab `make jalan` belum
//    dirakit (jawabannya selalu `tidak_ditemukan`, tanpa sitasi), sehingga
//    `POST /tanya` dicegat dan dijawab tanggapan berbentuk D-14 Bagian 4.1 yang
//    menyebut dua dokumen korpus. Yang diuji di sini perjalanan dari baris
//    sitasi ke pembaca sumber; tanggapan itu tidak pernah sampai ke peladen.
// 2. **Isi korpus ditanam sebagai pengelola** — dokumen, catatan metadata,
//    dan segmen — sebab perkakas ingesti terhadap PostgreSQL adalah baris 037
//    (TK-83). Status `doc_bukti_032` dicatat lewat jalur sungguhan:
//    `perkakas.kurasi status`.
//
// NASKAH: naskah **uji** persetujuan dipasang sementara pada
// `web/public/naskah/` lalu dihapus; tidak pernah di-commit (KB-164).
//
// Prasyarat, dari akar repositori:
//   akun pengguna, kurator, peneliti lewat `perkakas.akun buat`
//   kandidat `b-032-regulasi` dan `b-032-riset` lewat `perkakas.kurasi isi`
//   dokumen `doc_bukti_032` (berstatus) dan `doc_tanpa_status_032` di korpus
//   `perkakas.kurasi status --dokumen doc_bukti_032 --status berlaku`
//   (naskah uji dipasang)  npm --prefix web run build
//   PGHOST=/tmp PGPORT=55432 uv run python -m perkakas.jalankan_lokal --riwayat postgres
//   (di web/) npx vite preview --host 127.0.0.1 --port 4173 --strictPort
//   PENGGUNA=… SANDI_PENGGUNA=… KURATOR=… SANDI_KURATOR=… PENELITI=… SANDI_PENELITI=… \
//     PGHOST=/tmp PGPORT=55432 PGUSER=pengelola node specs/032-koleksi-dan-pembaca-sumber/bukti/ujung_ke_ujung.mjs

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
const CATATAN = "Bahas pada rapat guru hari Senin.";
const TEKS_SEGMEN = "Kepala sekolah menyusun rencana kerja tahunan bersama guru dan komite sekolah.";

const TANGGAPAN_BUATAN = {
  id_pesan: "msg_bukti_032",
  status_dasar: "kuat",
  ringkasan_tindakan: ["Susun rencana kerja tahunan bersama guru."],
  penjelasan: "Tanggapan buatan naskah bukti: jalur penjawab titik jalan belum dirakit.",
  klaim: [{ teks: "Rencana kerja disusun bersama guru.", id_segmen: ["seg_bukti_032_a"] }],
  sitasi: [
    {
      id_dokumen: "doc_bukti_032",
      judul: "Permendikdasmen Nomor 1 Tahun 2026",
      penerbit: "Kemendikdasmen",
      tahun: 2026,
      bagian: "Pasal 7 ayat (2)",
      status_keberlakuan: "berlaku",
      rujukan_pengganti: null,
      tautan: "https://jdih.contoh.go.id/permendikdasmen-1-2026",
    },
    {
      id_dokumen: "doc_tanpa_status_032",
      judul: "Permendikdasmen Nomor 9 Tahun 2025",
      penerbit: "Kemendikdasmen",
      tahun: 2025,
      bagian: "Pasal 3",
      status_keberlakuan: "berlaku",
      rujukan_pengganti: null,
      tautan: null,
    },
  ],
  bacaan_lanjutan: [],
  catatan_keberlakuan: "",
  penafian: "Keputusan akhir berada pada kepala sekolah.",
  versi: { model: "bukti-tanpa-model", indeks: "bukti", kode: "bukti" },
};

const masalah = [];
const tanggapan4xx = [];
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

async function halaman() {
  const konteks = await peramban.newContext({ viewport: { width: 360, height: 780 } });
  const h = await konteks.newPage();
  h.on("console", (p) => p.type() === "error" && masalah.push(`konsol: ${p.text()}`));
  h.on("pageerror", (g) => masalah.push(`halaman: ${g.message}`));
  // Tiap tanggapan 4xx disebut jalurnya, agar galat konsol dapat dijelaskan.
  h.on("response", (r) => r.status() >= 400 && tanggapan4xx.push(`${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}`));
  return h;
}

const judul = (h, nama, level) => h.getByRole("heading", { name: nama, exact: true, ...(level ? { level } : {}) });
const tombol = (h, nama) => h.getByRole("button", { name: nama, exact: true });

async function masuk(h, akun, sandi) {
  await h.goto(ALAMAT);
  await judul(h, "Masuk").waitFor();
  await h.getByLabel("Nama pengguna").fill(akun);
  await h.getByLabel("Sandi", { exact: true }).fill(sandi);
  await tombol(h, "Masuk").click();
}

/** Lewat `fetch` di dalam halaman kurator: kuki sesi `HttpOnly` dibawa peramban
 * sendiri, sama dengan layar S-15 (fitur 029 P-2). */
async function putusan(h, id, jalur, badan) {
  return h.evaluate(
    async ([alamat, isi]) =>
      (
        await fetch(alamat, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(isi),
        })
      ).status,
    [`/api/v1/kurasi/${id}/${jalur}`, badan],
  );
}

// ── A · kurator menyetujui kedua butir ───────────────────────────────
const kurator = await halaman();
await masuk(kurator, KURATOR, SANDI_KURATOR);
await judul(kurator, "Antrean kurasi").waitFor();
for (const id of ["b-032-regulasi", "b-032-riset"]) {
  const status = await putusan(kurator, id, "putusan", { jenis: "setujui", catatan: "Layak tayang" });
  pastikan(status === 200, `C-06: ${id} disetujui kurator (${status})`);
}

// ── B · pengguna: aktivasi, lalu S-09 → S-10 ─────────────────────────
const h = await halaman();
await masuk(h, PENGGUNA, SANDI_PENGGUNA);
await judul(h, "Persetujuan penelitian").waitFor();
await tombol(h, "Saya setuju").click();
for (const nama of ["Yang dapat dibantu", "Alat bantu, bukan penentu", "Bila dasarnya tidak ada"]) {
  await judul(h, nama).waitFor();
  await tombol(h, "Lanjut").click();
}
await judul(h, "Menjaga data").waitFor();
await tombol(h, "Mulai mengisi profil").click();
await judul(h, "Profil sekolah").waitFor();
await h.getByLabel("Jabatan").fill("Kepala Sekolah");
await h.getByLabel("Masa kerja (tahun)").fill("3");
await h.getByLabel("Jumlah rombongan belajar").fill("6");
await h.getByLabel("Jumlah pendidik dan tenaga kependidikan").fill("9");
await h.getByLabel("Visitasi").check();
await h.getByLabel("Wilayah (kabupaten atau kota)").fill("Kabupaten Sumedang");
for (const label of ["Kurikulum dan pembelajaran", "Keuangan dan pembiayaan", "Penjaminan mutu dan akreditasi"]) {
  await h.getByLabel(label).check();
}
await tombol(h, "Simpan dan mulai bertanya").click();
await judul(h, "Tanya").waitFor();

await h.route("**/api/v1/tanya", (rute) =>
  rute.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(TANGGAPAN_BUATAN) }),
);
await h.getByLabel("Pertanyaan Anda").fill("Bagaimana menyusun rencana kerja tahunan sekolah?");
await tombol(h, "Kirim pertanyaan").click();
await h.getByTestId("blok-jawaban").waitFor();

const baris1 = "Permendikdasmen Nomor 1 Tahun 2026 · Kemendikdasmen · 2026 · Pasal 7 ayat (2)";
const baca1 = h.waitForResponse((r) => r.url().includes("/api/v1/sumber/doc_bukti_032"));
await tombol(h, baris1).click();
pastikan((await baca1).status() === 200, "S-10: pembaca sumber menjawab 200 dari peladen sungguhan");
await judul(h, "Permendikdasmen Nomor 1 Tahun 2026", 1).waitFor();
const status = h.getByTestId("status-sumber");
const teks = h.getByTestId("teks-bagian");
pastikan((await status.innerText()).includes("Masih berlaku."), "R-07: status dari catatan korpus, dicatat perkakas status");
pastikan((await teks.innerText()).includes(TEKS_SEGMEN), "P-2 A: teks bagian yang dirujuk tampil bagi regulasi publik");
const urut = await status.evaluate((s) => {
  const t = document.querySelector('[data-testid="teks-bagian"]');
  return t !== null && (s.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
});
pastikan(urut, "R-07: status keberlakuan tampil sebelum teks");
pastikan((await h.getByRole("link", { name: "Buka sumber aslinya" }).getAttribute("href")) === TANGGAPAN_BUATAN.sitasi[0].tautan, "tautan sumber asli dari baris sitasi");
await h.screenshot({ path: join(KELUAR, "s10-pembaca-sumber.png"), fullPage: true });
await tombol(h, "Kembali ke jawaban").click();
await h.getByTestId("blok-jawaban").waitFor();
pastikan(true, "kembali ke jawaban yang sama tanpa bertanya ulang");

await tombol(h, "Permendikdasmen Nomor 9 Tahun 2025 · Kemendikdasmen · 2025 · Pasal 3").click();
await judul(h, "Permendikdasmen Nomor 9 Tahun 2025", 1).waitFor();
pastikan((await h.getByTestId("status-sumber").innerText()).includes("Status keberlakuannya belum tercatat."), "TK-81 A: regulasi tanpa catatan status dinyatakan belum tercatat");
pastikan((await h.getByTestId("teks-bagian").count()) === 0, "TK-81 A: regulasi tanpa status tampil tanpa teks");
pastikan((await h.getByText("Status keberlakuan aturan ini belum tercatat. Teksnya belum ditampilkan.").count()) === 1, "kalimat tanpa teks D-05 S-10");
await tombol(h, "Kembali ke jawaban").click();
await h.unroute("**/api/v1/tanya");

// ── C · pengguna: S-06 Simpan, S-11 ──────────────────────────────────
const nav = h.getByRole("navigation", { name: "Navigasi utama" });
pastikan((await nav.getByRole("button").allInnerTexts()).join("|") === "Beranda|Tanya|Milik saya", "R-10: navigasi tiga tujuan");
await nav.getByRole("button", { name: "Beranda" }).click();
await judul(h, "Butir hari ini").waitFor();
await h.getByRole("button", { name: /Rencana kerja tahunan sekolah/ }).click();
await judul(h, "Rencana kerja tahunan sekolah", 1).waitFor();
await tombol(h, "Simpan").click();
await h.getByLabel("Catatan untuk diri sendiri (boleh kosong)").fill(CATATAN);
await tombol(h, "Simpan ke koleksi").click();
await h.getByText("Tersimpan di Koleksi saya.").waitFor();
pastikan(true, "S-06: tersimpan beserta catatan");
await h.screenshot({ path: join(KELUAR, "s06-simpan.png"), fullPage: true });
await tombol(h, "Kembali ke beranda").click();
await h.getByRole("button", { name: /Supervisi akademik terjadwal/ }).click();
await judul(h, "Supervisi akademik terjadwal", 1).waitFor();
await tombol(h, "Simpan").click();
await tombol(h, "Simpan ke koleksi").click();
await h.getByText("Tersimpan di Koleksi saya.").waitFor();

await nav.getByRole("button", { name: "Milik saya" }).click();
await judul(h, "Koleksi tersimpan", 1).waitFor();
await h.getByRole("article").nth(1).waitFor();
pastikan((await h.getByRole("article").count()) === 2, "S-11: dua butir tersimpan");
await h.getByLabel("Jenis sumber").selectOption("regulasi");
await h.getByRole("article").filter({ hasText: "Supervisi akademik terjadwal" }).waitFor({ state: "detached" });
pastikan((await h.getByRole("article").count()) === 1, "FR-G10: tersaring jenis sumber");
await h.getByLabel("Jenis sumber").selectOption("");

// ── D · kurator menarik butir yang tersimpan ─────────────────────────
const tarik = await putusan(kurator, "b-032-regulasi", "tarik", {
  pemicu: "kekeliruan_isi_dilaporkan",
  catatan: "Bukti fitur 032: ditarik sesudah disimpan peserta.",
});
pastikan(tarik === 200, `penarikan oleh kurator (${tarik})`);

await nav.getByRole("button", { name: "Beranda" }).click();
await judul(h, "Butir hari ini").waitFor();
await nav.getByRole("button", { name: "Milik saya" }).click();
const ditarik = h.getByRole("article").filter({ hasText: "Rencana kerja tahunan sekolah" });
await ditarik.waitFor();
const penanda = ditarik.getByText("Dasar rujukan butir ini telah berubah. Isinya mungkin tidak lagi berlaku.");
pastikan((await penanda.count()) === 1, "P-4 A: butir ditarik tetap terbaca berpenanda");
pastikan((await ditarik.getByText(CATATAN).count()) === 1, "P-4 A: catatan tetap terbaca");
const penandaDulu = await penanda.evaluate((p) => {
  const judulKartu = p.parentElement.querySelector("h2");
  return (p.compareDocumentPosition(judulKartu) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
});
pastikan(penandaDulu, "P-4 A: penanda sebelum judul dan isi");
await h.screenshot({ path: join(KELUAR, "s11-koleksi.png"), fullPage: true });
await h
  .getByRole("article")
  .filter({ hasText: "Supervisi akademik terjadwal" })
  .getByRole("button", { name: "Keluarkan dari koleksi" })
  .click();
await h.getByText("Butir dikeluarkan dari koleksi.").waitFor();
pastikan((await h.getByRole("article").count()) === 1, "keluarkan: satu butir tersisa");
await h.context().close();
await tombol(kurator, "Keluar").click();

// ── E · peneliti ─────────────────────────────────────────────────────
const peneliti = await halaman();
await masuk(peneliti, PENELITI, SANDI_PENELITI);
await peneliti.getByRole("heading", { level: 1, name: "Analitik penelitian" }).waitFor();
const tabel = peneliti.getByRole("table", { name: "Penelusuran sumber" });
const baris = (await tabel.getByRole("row").allInnerTexts()).slice(1).map((t) => t.replace(/\s+/g, " ").trim());
pastikan(baris.length === 3, `S-18: tabel penelusuran sumber — ${baris.join("|")}`);
await peramban.close();

// ── F · yang tersimpan ───────────────────────────────────────────────
const pseudonim = psql(`SELECT pseudonim FROM akun.pengguna WHERE id = ${kutip(PENGGUNA)};`);
const dibuka = psql(
  `SELECT string_agg((SELECT string_agg(k, ',' ORDER BY k) FROM jsonb_object_keys(properti) k) || ':' || (properti->>'id_sumber') || ':' || (properti->>'jenis_sumber') || ':' || versi_aplikasi, ' ' ORDER BY waktu) FROM telemetri.peristiwa WHERE pseudonim = ${kutip(pseudonim)} AND jenis = 'citation_opened';`,
);
pastikan(
  dibuka ===
    "id_sumber,jenis_sumber:doc_bukti_032:regulasi_resmi:pengembangan id_sumber,jenis_sumber:doc_tanpa_status_032:regulasi_resmi:pengembangan",
  `P-3 A: citation_opened berproperti D-01 (${dibuka})`,
);
const disimpan = psql(
  `SELECT string_agg(properti::text, ' ' ORDER BY waktu) FROM telemetri.peristiwa WHERE pseudonim = ${kutip(pseudonim)} AND jenis = 'discovery_saved';`,
);
pastikan(disimpan === '{"ada_catatan": true} {"ada_catatan": false}', `P-3 A: discovery_saved tanpa teks catatan (${disimpan})`);
const koleksi = psql(
  `SELECT string_agg(id_butir || ':' || coalesce(catatan, '-'), ' ') FROM penemuan.koleksi WHERE id_pengguna = ${kutip(pseudonim)};`,
);
pastikan(koleksi === `b-032-regulasi:${CATATAN}`, `koleksi tersisa satu beserta catatannya (${koleksi})`);
const statusKorpus = psql(
  "SELECT string_agg(status || ':' || coalesce(rujukan_pengganti, '-'), ' ' ORDER BY nomor) FROM korpus.status_dokumen WHERE id_dokumen = 'doc_bukti_032';",
);
pastikan(statusKorpus.split(" ").at(-1) === "berlaku:-", `TK-81 A: catatan status korpus (${statusKorpus})`);
const tayang = psql("SELECT ditarik_pada IS NOT NULL FROM kurasi.butir_tayang WHERE id_butir = 'b-032-regulasi';");
pastikan(tayang === "t", "butir yang disimpan memang ditarik pada kurasi");

writeFileSync(
  join(KELUAR, "koleksi-dan-pembaca-sumber.txt"),
  [
    "Jawaban S-09 buatan naskah bukti (jalur penjawab titik jalan belum dirakit);",
    "isi korpus ditanam sebagai pengelola (perkakas ingesti: baris 037, TK-83).",
    "",
    `citation_opened (kunci : id_sumber : jenis_sumber : versi) : ${dibuka}`,
    `discovery_saved (properti)                               : ${disimpan}`,
    `koleksi tersisa (id_butir : catatan)                     : ${koleksi}`,
    `korpus.status_dokumen doc_bukti_032 (status : pengganti)  : ${statusKorpus}`,
    `S-18 penelusuran sumber (pengembangan dipisah)           : ${baris.join(" | ")}`,
    "",
  ].join("\n"),
);

// Galat konsol yang diharapkan: 401 atas pemeriksaan sesi pertama, 403 atas
// ringkasan akun dan antrean bagi kurator dan peneliti (K-8 fitur 013, P-5 fitur
// 035), dan 404 atas riwayat percakapan yang **tidak pernah dibuat** — `/tanya`
// dicegat naskah ini, sehingga peladen tidak pernah menerima giliran pertamanya.
// 404 lain tidak dikecualikan.
console.log(`\nTanggapan 4xx yang teramati: ${tanggapan4xx.join(", ") || "tidak ada"}`);
const hanyaRiwayatDicegat = tanggapan4xx
  .filter((t) => t.startsWith("404"))
  .every((t) => t.startsWith("404 GET /api/v1/percakapan/"));
const nyata = masalah.filter(
  (m) => !/status of 40[13]/.test(m) && !(hanyaRiwayatDicegat && /status of 404/.test(m)),
);
if (nyata.length > 0) {
  console.error("\nMASALAH:\n" + nyata.join("\n"));
  process.exit(1);
}
console.log("\nSeluruh pemeriksaan lulus; tanpa pelanggaran CSP maupun galat halaman.");
