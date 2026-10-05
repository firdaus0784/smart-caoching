/**
 * Pemanggil `POST /api/v1/tanya` — T-3 fitur 027, R-10, R-16, R-17.
 *
 * `fetch` disuntikkan, bentuk yang sama dengan `Penyemat` dan `sekarang` pada
 * fitur 026: seluruh perilaku di bawah diuji tanpa peladen.
 *
 * Dua janji yang dipegang berkas ini:
 *
 * - Hasil galat **tidak pernah** membawa status HTTP maupun isi badan peladen.
 *   Layar menampilkan kalimat dari mikrokopi menurut `JenisGalat`, sehingga
 *   tidak ada jalan bagi kode galat atau rincian teknis mencapai pengguna
 *   (R-10, D-05 Bagian 10).
 * - Tanggapan 200 yang bentuknya tidak persis D-14 Bagian 4.1 ditolak utuh
 *   sebagai galat sistem, bukan ditampilkan separuh. Jawaban tanpa sitasi yang
 *   tampil karena satu bidang hilang adalah pelanggaran C-01 yang dibuat layar.
 */

import type {
  Antrean,
  Beranda,
  ButirLengkap,
  ButirRingkas,
  HasilAntrean,
  HasilBeranda,
  HasilButir,
  JenisSumberButir,
  KandidatTampil,
  KategoriMasalah,
  KeadaanBeranda,
  Pemicu,
  PermintaanTarik,
  Suntingan,
  SumberButir,
  TayangTampil,
  HasilBaca,
  HasilDaftar,
  HasilMasuk,
  HasilNaskah,
  HasilRingkasan,
  KeadaanPersetujuan,
  Naskah,
  PermintaanProfil,
  Ringkasan,
  HasilTanya,
  JenisGalat,
  SatuPercakapan,
  StatusDasar,
  StatusKeberlakuan,
  Tanggapan,
} from "./kontrak";

export const JALUR_TANYA = "/api/v1/tanya";
export const JALUR_PERCAKAPAN = "/api/v1/percakapan";
export const JALUR_MASUK = "/api/v1/auth/masuk";
export const JALUR_KELUAR = "/api/v1/auth/keluar";
export const JALUR_PROFIL = "/api/v1/saya/profil";
export const JALUR_PRIORITAS = "/api/v1/saya/prioritas";
export const JALUR_PERSETUJUAN = "/api/v1/saya/persetujuan";
export const JALUR_BERANDA = "/api/v1/beranda";
export const JALUR_ANTREAN = "/api/v1/kurasi/antrean";
/** Berkas statis yang diisi tim (K-4 fitur 030), bukan rute API. */
export const JALUR_NASKAH = "/naskah/persetujuan.json";

export type Pemanggil = (jalur: string, init?: RequestInit) => Promise<Response>;

const STATUS_DASAR: readonly StatusDasar[] = [
  "kuat",
  "terbatas",
  "tidak_ditemukan",
  "di_luar_domain",
];

/** `dicabut` sengaja tidak ada: sitasi berstatus dicabut tidak pernah sah (C-07). */
const STATUS_SITASI_SAH: readonly StatusKeberlakuan[] = ["berlaku", "diubah"];

/** Satu permintaan: badan JSON bila berhasil, atau jenis galat bagi layar.
 * Status HTTP dan isi badan galat tidak pernah keluar dari sini (R-10). */
async function ambil(
  pemanggil: Pemanggil,
  jalur: string,
  init?: RequestInit,
): Promise<{ readonly badan: unknown } | { readonly galat: JenisGalat }> {
  let jawaban: Response;
  try {
    // Tanpa tajuk autentikasi: sesi berupa kuki `HttpOnly` yang dikirim
    // peramban sendiri dan tidak terbaca kode ini (R-17 fitur 027, P-2 fitur 029).
    jawaban = await pemanggil(jalur, init);
  } catch {
    return { galat: "luring" };
  }
  if (!jawaban.ok) return { galat: petakanStatus(jawaban.status) };
  try {
    return { badan: await jawaban.json() };
  } catch {
    return { galat: "sistem" };
  }
}

export async function tanya(
  pertanyaan: string,
  idPercakapan: string,
  pemanggil: Pemanggil,
): Promise<HasilTanya> {
  // D-14 Bagian 4.1 sejak fitur 028: pengenal percakapan dibangkitkan klien.
  const hasil = await ambil(pemanggil, JALUR_TANYA, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pertanyaan, id_percakapan: idPercakapan }),
  });
  if ("galat" in hasil) return galat(hasil.galat);
  return apakahTanggapan(hasil.badan)
    ? { jenis: "jawaban", tanggapan: hasil.badan }
    : galat("sistem");
}

/** `GET /api/v1/percakapan` — pengenal milik penanya, terbaru lebih dulu. */
export async function daftarPercakapan(pemanggil: Pemanggil): Promise<HasilDaftar> {
  const hasil = await ambil(pemanggil, JALUR_PERCAKAPAN, { method: "GET" });
  if ("galat" in hasil) return { jenis: "galat", galat: hasil.galat };
  const badan = hasil.badan;
  return objekBerkunci(badan, ["percakapan"]) && larikDari(badan["percakapan"], untai)
    ? { jenis: "daftar", percakapan: badan["percakapan"] as string[] }
    : { jenis: "galat", galat: "sistem" };
}

/** `GET /api/v1/percakapan/{id}` — giliran **tanpa jawaban** (C-07). */
export async function bacaPercakapan(
  idPercakapan: string,
  pemanggil: Pemanggil,
): Promise<HasilBaca> {
  const hasil = await ambil(pemanggil, `${JALUR_PERCAKAPAN}/${encodeURIComponent(idPercakapan)}`, {
    method: "GET",
  });
  if ("galat" in hasil) return { jenis: "galat", galat: hasil.galat };
  return apakahSatuPercakapan(hasil.badan)
    ? { jenis: "percakapan", percakapan: hasil.badan }
    : { jenis: "galat", galat: "sistem" };
}

/**
 * `POST /api/v1/auth/masuk` — fitur 029. Sandi dikirim sekali dan tidak
 * disimpan di mana pun; kuki sesinya dipasang peramban, bukan kode ini.
 */
export async function masuk(
  namaPengguna: string,
  sandi: string,
  pemanggil: Pemanggil,
): Promise<HasilMasuk> {
  let jawaban: Response;
  try {
    jawaban = await pemanggil(JALUR_MASUK, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nama_pengguna: namaPengguna, sandi }),
    });
  } catch {
    return { jenis: "galat", galat: "luring" };
  }
  if (jawaban.status === 204) return { jenis: "masuk" };
  if (jawaban.status === 401 || jawaban.status === 400) return { jenis: "ditolak" };
  return { jenis: "galat", galat: "sistem" };
}

/**
 * `POST /api/v1/auth/keluar` — sesi dicabut di peladen (R-06). Tidak pernah
 * melempar: layar membersihkan peramban apa pun hasilnya, dan sesi yang
 * gagal dicabut karena luring berakhir sendiri sesudah 30 menit diam.
 */
export async function keluar(pemanggil: Pemanggil): Promise<void> {
  try {
    await pemanggil(JALUR_KELUAR, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
  } catch {
    // Lihat uraian fungsi.
  }
}

// ── fitur 030 · akun saya — D-14 Bagian 4.5 ─────────────────────────────

const KEADAAN_PERSETUJUAN: readonly KeadaanPersetujuan[] = [
  "belum_diminta",
  "diberikan",
  "ditolak",
  "dicabut",
];

async function ringkasanDari(
  jalur: string,
  pemanggil: Pemanggil,
  init?: RequestInit,
): Promise<HasilRingkasan> {
  const hasil = await ambil(pemanggil, jalur, init);
  if ("galat" in hasil) return { jenis: "galat", galat: hasil.galat };
  return apakahRingkasan(hasil.badan)
    ? { jenis: "ringkasan", ringkasan: hasil.badan }
    : { jenis: "galat", galat: "sistem" };
}

function kirimJson(metode: string, badan: unknown): RequestInit {
  return {
    method: metode,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(badan),
  };
}

export function bacaRingkasan(pemanggil: Pemanggil): Promise<HasilRingkasan> {
  return ringkasanDari(JALUR_PROFIL, pemanggil, { method: "GET" });
}

export function simpanProfil(profil: PermintaanProfil, pemanggil: Pemanggil): Promise<HasilRingkasan> {
  return ringkasanDari(JALUR_PROFIL, pemanggil, kirimJson("PUT", profil));
}

export function tetapkanPrioritas(
  kategori: readonly string[],
  pemanggil: Pemanggil,
): Promise<HasilRingkasan> {
  return ringkasanDari(JALUR_PRIORITAS, pemanggil, kirimJson("PUT", { kategori }));
}

export function putuskanPersetujuan(
  badan: { readonly versi_naskah: string; readonly disetujui: boolean } | { readonly cabut: true },
  pemanggil: Pemanggil,
): Promise<HasilRingkasan> {
  return ringkasanDari(JALUR_PERSETUJUAN, pemanggil, kirimJson("POST", badan));
}

/**
 * Naskah ET-02. Berkas yang tidak ada — termasuk peladen statis yang menjawab
 * halaman pengganti — dibaca "belum ada", bukan galat: tanpa naskah memang
 * tidak ada yang dapat disetujui, dan peladen API menolak setiap persetujuan.
 */
export async function muatNaskah(pemanggil: Pemanggil): Promise<HasilNaskah> {
  try {
    const jawaban = await pemanggil(JALUR_NASKAH, { method: "GET" });
    if (!jawaban.ok) return { jenis: "belum_ada" };
    const badan: unknown = await jawaban.json();
    return apakahNaskah(badan) ? { jenis: "naskah", naskah: badan } : { jenis: "belum_ada" };
  } catch {
    return { jenis: "belum_ada" };
  }
}

function apakahProfil(nilai: unknown): nilai is PermintaanProfil {
  return (
    objekBerkunci(nilai, [
      "jabatan",
      "masa_kerja",
      "jumlah_rombel",
      "jumlah_ptk",
      "jalur_akreditasi",
      "wilayah",
    ]) &&
    untai(nilai["jabatan"]) &&
    Number.isInteger(nilai["masa_kerja"]) &&
    Number.isInteger(nilai["jumlah_rombel"]) &&
    Number.isInteger(nilai["jumlah_ptk"]) &&
    (nilai["jalur_akreditasi"] === "visitasi" || nilai["jalur_akreditasi"] === "automasi") &&
    untai(nilai["wilayah"])
  );
}

function apakahRingkasan(nilai: unknown): nilai is Ringkasan {
  return (
    objekBerkunci(nilai, ["profil", "prioritas", "persetujuan"]) &&
    (nilai["profil"] === null || apakahProfil(nilai["profil"])) &&
    larikDari(nilai["prioritas"], untai) &&
    KEADAAN_PERSETUJUAN.includes(nilai["persetujuan"] as KeadaanPersetujuan)
  );
}

function apakahNaskah(nilai: unknown): nilai is Naskah {
  return (
    objekBerkunci(nilai, ["versi", "judul", "paragraf"]) &&
    untai(nilai["versi"]) &&
    nilai["versi"].trim() !== "" &&
    untai(nilai["judul"]) &&
    larikDari(nilai["paragraf"], untai) &&
    (nilai["paragraf"] as unknown[]).length > 0
  );
}

function galat(jenis: JenisGalat): HasilTanya {
  return { jenis: "galat", galat: jenis };
}

function petakanStatus(status: number): JenisGalat {
  if (status === 401) return "belum_masuk";
  if (status === 403) return "tidak_berhak";
  if (status === 400 || status === 413 || status === 422) return "pertanyaan_ditolak";
  return "sistem";
}

type Objek = Record<string, unknown>;

function objekBerkunci(nilai: unknown, kunci: readonly string[]): nilai is Objek {
  if (typeof nilai !== "object" || nilai === null || Array.isArray(nilai)) return false;
  const ada = Object.keys(nilai);
  return ada.length === kunci.length && kunci.every((k) => ada.includes(k));
}

function untai(nilai: unknown): nilai is string {
  return typeof nilai === "string";
}

function untaiAtauKosong(nilai: unknown): boolean {
  return nilai === null || typeof nilai === "string";
}

function larikDari(nilai: unknown, periksa: (butir: unknown) => boolean): boolean {
  return Array.isArray(nilai) && nilai.every(periksa);
}

function apakahVersi(nilai: unknown): boolean {
  return (
    objekBerkunci(nilai, ["model", "indeks", "kode"]) &&
    untai(nilai["model"]) &&
    untai(nilai["indeks"]) &&
    untai(nilai["kode"])
  );
}

function apakahKlaim(nilai: unknown): boolean {
  return (
    objekBerkunci(nilai, ["teks", "id_segmen"]) &&
    untai(nilai["teks"]) &&
    larikDari(nilai["id_segmen"], untai) &&
    (nilai["id_segmen"] as unknown[]).length > 0
  );
}

function apakahSitasi(nilai: unknown): boolean {
  return (
    objekBerkunci(nilai, [
      "id_dokumen",
      "judul",
      "penerbit",
      "tahun",
      "bagian",
      "status_keberlakuan",
      "rujukan_pengganti",
      "tautan",
    ]) &&
    untai(nilai["id_dokumen"]) &&
    untai(nilai["judul"]) &&
    untai(nilai["penerbit"]) &&
    Number.isInteger(nilai["tahun"]) &&
    untai(nilai["bagian"]) &&
    STATUS_SITASI_SAH.includes(nilai["status_keberlakuan"] as StatusKeberlakuan) &&
    untaiAtauKosong(nilai["rujukan_pengganti"]) &&
    untaiAtauKosong(nilai["tautan"])
  );
}

function apakahBacaan(nilai: unknown): boolean {
  return (
    objekBerkunci(nilai, ["judul", "tautan"]) && untai(nilai["judul"]) && untai(nilai["tautan"])
  );
}

export function apakahTanggapan(nilai: unknown): nilai is Tanggapan {
  return (
    objekBerkunci(nilai, [
      "id_pesan",
      "status_dasar",
      "ringkasan_tindakan",
      "penjelasan",
      "klaim",
      "sitasi",
      "bacaan_lanjutan",
      "catatan_keberlakuan",
      "penafian",
      "versi",
    ]) &&
    untai(nilai["id_pesan"]) &&
    STATUS_DASAR.includes(nilai["status_dasar"] as StatusDasar) &&
    larikDari(nilai["ringkasan_tindakan"], untai) &&
    untai(nilai["penjelasan"]) &&
    larikDari(nilai["klaim"], apakahKlaim) &&
    larikDari(nilai["sitasi"], apakahSitasi) &&
    larikDari(nilai["bacaan_lanjutan"], apakahBacaan) &&
    untai(nilai["catatan_keberlakuan"]) &&
    untai(nilai["penafian"]) &&
    nilai["penafian"].trim() !== "" &&
    apakahVersi(nilai["versi"])
  );
}

function apakahGiliran(nilai: unknown): boolean {
  // Kunci persis: giliran yang membawa bidang tanggapan ditolak utuh (C-07).
  return (
    objekBerkunci(nilai, ["pertanyaan", "id_pesan", "waktu"]) &&
    untai(nilai["pertanyaan"]) &&
    untai(nilai["id_pesan"]) &&
    untai(nilai["waktu"])
  );
}

function apakahSatuPercakapan(nilai: unknown): nilai is SatuPercakapan {
  return (
    objekBerkunci(nilai, ["id_percakapan", "giliran"]) &&
    untai(nilai["id_percakapan"]) &&
    larikDari(nilai["giliran"], apakahGiliran)
  );
}


// ── fitur 013 · penemuan — D-14 Bagian 4.6 ──────────────────────────────

const KATEGORI: readonly KategoriMasalah[] = ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"];
const JENIS_SUMBER: readonly JenisSumberButir[] = ["riset", "regulasi", "data_resmi", "praktik_baik"];
const KEADAAN_BERANDA: readonly KeadaanBeranda[] = [
  "berisi",
  "belum_ada_prioritas",
  "belum_ada_butir",
  "habis",
];

export function jalurButir(idButir: string): string {
  return `/api/v1/butir/${encodeURIComponent(idButir)}`;
}

export function jalurTolakButir(idButir: string): string {
  return `/api/v1/butir/${encodeURIComponent(idButir)}/tolak`;
}

/**
 * Satu permintaan bagi rute fitur 013. Berbeda dari `ambil`: 404 dibaca
 * sebagai keadaan sah `tidak_ada` (KL-G — butir yang sudah tidak tersedia
 * bukan galat sistem), bukan galat.
 */
async function ambil013(
  pemanggil: Pemanggil,
  jalur: string,
  init: RequestInit,
): Promise<
  | { readonly badan: unknown }
  | { readonly tidak_ada: true }
  | { readonly status: number }
  | { readonly galat: JenisGalat }
> {
  let jawaban: Response;
  try {
    jawaban = await pemanggil(jalur, init);
  } catch {
    return { galat: "luring" };
  }
  if (jawaban.status === 404) return { tidak_ada: true };
  if (!jawaban.ok) return { status: jawaban.status };
  try {
    return { badan: await jawaban.json() };
  } catch {
    return { galat: "sistem" };
  }
}

function apakahSumber(nilai: unknown): nilai is SumberButir {
  return (
    objekBerkunci(nilai, ["judul", "penerbit", "tahun", "tautan"]) &&
    untai(nilai["judul"]) &&
    untai(nilai["penerbit"]) &&
    Number.isInteger(nilai["tahun"]) &&
    untaiAtauKosong(nilai["tautan"])
  );
}

const KUNCI_RINGKAS = [
  "id_butir",
  "kategori",
  "jenis_sumber",
  "judul",
  "alasan_relevansi",
  "perkiraan_waktu_baca",
] as const;

function ringkasSah(nilai: Record<string, unknown>): boolean {
  return (
    untai(nilai["id_butir"]) &&
    KATEGORI.includes(nilai["kategori"] as KategoriMasalah) &&
    JENIS_SUMBER.includes(nilai["jenis_sumber"] as JenisSumberButir) &&
    untai(nilai["judul"]) &&
    untai(nilai["alasan_relevansi"]) &&
    Number.isInteger(nilai["perkiraan_waktu_baca"])
  );
}

function apakahButirRingkas(nilai: unknown): nilai is ButirRingkas {
  return objekBerkunci(nilai, KUNCI_RINGKAS) && ringkasSah(nilai);
}

export function apakahButirLengkap(nilai: unknown): nilai is ButirLengkap {
  return (
    objekBerkunci(nilai, [
      ...KUNCI_RINGKAS,
      "inti_temuan",
      "implikasi_tindakan",
      "tenggat_terkait",
      "boleh_teks_penuh",
      "sumber",
    ]) &&
    ringkasSah(nilai) &&
    untai(nilai["inti_temuan"]) &&
    larikDari(nilai["implikasi_tindakan"], untai) &&
    untaiAtauKosong(nilai["tenggat_terkait"]) &&
    typeof nilai["boleh_teks_penuh"] === "boolean" &&
    apakahSumber(nilai["sumber"])
  );
}

export function apakahBeranda(nilai: unknown): nilai is Beranda {
  return (
    objekBerkunci(nilai, ["keadaan", "butir"]) &&
    KEADAAN_BERANDA.includes(nilai["keadaan"] as KeadaanBeranda) &&
    larikDari(nilai["butir"], apakahButirRingkas)
  );
}

function berandaDari(
  hasil: Awaited<ReturnType<typeof ambil013>>,
): HasilBeranda {
  if ("galat" in hasil) return { jenis: "galat", galat: hasil.galat };
  if ("tidak_ada" in hasil) return { jenis: "tidak_ada" };
  if ("status" in hasil) return { jenis: "galat", galat: petakanStatus(hasil.status) };
  return apakahBeranda(hasil.badan)
    ? { jenis: "beranda", beranda: hasil.badan }
    : { jenis: "galat", galat: "sistem" };
}

/** `GET /api/v1/beranda` — butir hari ini. */
export async function bacaBeranda(pemanggil: Pemanggil): Promise<HasilBeranda> {
  return berandaDari(await ambil013(pemanggil, JALUR_BERANDA, { method: "GET" }));
}

/** `GET /api/v1/butir/{id}` — bentuk lengkap, atau `tidak_ada`. */
export async function bacaButir(idButir: string, pemanggil: Pemanggil): Promise<HasilButir> {
  const hasil = await ambil013(pemanggil, jalurButir(idButir), { method: "GET" });
  if ("galat" in hasil) return { jenis: "galat", galat: hasil.galat };
  if ("tidak_ada" in hasil) return { jenis: "tidak_ada" };
  if ("status" in hasil) return { jenis: "galat", galat: petakanStatus(hasil.status) };
  return apakahButirLengkap(hasil.badan)
    ? { jenis: "butir", butir: hasil.badan }
    : { jenis: "galat", galat: "sistem" };
}

/** `POST /api/v1/butir/{id}/tolak` — "belum relevan"; beranda terbaru bila diterima. */
export async function tolakButir(
  idButir: string,
  alasan: string,
  pemanggil: Pemanggil,
): Promise<HasilBeranda> {
  return berandaDari(
    await ambil013(pemanggil, jalurTolakButir(idButir), kirimJson("POST", { alasan })),
  );
}

// ── fitur 013 · kurasi — D-14 Bagian 4.7 ────────────────────────────────

const STATUS_KEBERLAKUAN: readonly StatusKeberlakuan[] = ["berlaku", "diubah", "dicabut"];

export function jalurPutusan(idButir: string): string {
  return `/api/v1/kurasi/${encodeURIComponent(idButir)}/putusan`;
}

export function jalurTarik(idButir: string): string {
  return `/api/v1/kurasi/${encodeURIComponent(idButir)}/tarik`;
}

function statusSah(nilai: unknown): boolean {
  return nilai === null || STATUS_KEBERLAKUAN.includes(nilai as StatusKeberlakuan);
}

function apakahKandidat(nilai: unknown): nilai is KandidatTampil {
  return (
    objekBerkunci(nilai, [
      "id_butir",
      "kategori",
      "jenis_sumber",
      "judul",
      "alasan_relevansi",
      "inti_temuan",
      "implikasi_tindakan",
      "perkiraan_waktu_baca",
      "tenggat_terkait",
      "lisensi",
      "status_keberlakuan",
      "sumber",
      "masuk_pada",
    ]) &&
    untai(nilai["id_butir"]) &&
    KATEGORI.includes(nilai["kategori"] as KategoriMasalah) &&
    JENIS_SUMBER.includes(nilai["jenis_sumber"] as JenisSumberButir) &&
    untai(nilai["judul"]) &&
    untai(nilai["alasan_relevansi"]) &&
    untai(nilai["inti_temuan"]) &&
    larikDari(nilai["implikasi_tindakan"], untai) &&
    Number.isInteger(nilai["perkiraan_waktu_baca"]) &&
    untaiAtauKosong(nilai["tenggat_terkait"]) &&
    untai(nilai["lisensi"]) &&
    statusSah(nilai["status_keberlakuan"]) &&
    apakahSumber(nilai["sumber"]) &&
    untai(nilai["masuk_pada"])
  );
}

function apakahTayang(nilai: unknown): nilai is TayangTampil {
  return (
    objekBerkunci(nilai, [
      "id_butir",
      "kategori",
      "jenis_sumber",
      "judul",
      "lisensi",
      "status_keberlakuan",
      "tayang_pada",
      "perlu_tinjauan",
    ]) &&
    untai(nilai["id_butir"]) &&
    KATEGORI.includes(nilai["kategori"] as KategoriMasalah) &&
    JENIS_SUMBER.includes(nilai["jenis_sumber"] as JenisSumberButir) &&
    untai(nilai["judul"]) &&
    untai(nilai["lisensi"]) &&
    statusSah(nilai["status_keberlakuan"]) &&
    untai(nilai["tayang_pada"]) &&
    typeof nilai["perlu_tinjauan"] === "boolean"
  );
}

export function apakahAntrean(nilai: unknown): nilai is Antrean {
  return (
    objekBerkunci(nilai, ["menunggu", "tayang"]) &&
    larikDari(nilai["menunggu"], apakahKandidat) &&
    larikDari(nilai["tayang"], apakahTayang)
  );
}

/** Galat tidak pernah dibaca isinya (R-10 fitur 027): penolakan regulasi
 * (R-04) dan penolakan bentuk sama-sama `pertanyaan_ditolak`, dan layar kurator
 * menampilkan status regulasi pada barisnya sendiri. */
async function antreanDari(
  pemanggil: Pemanggil,
  jalur: string,
  init: RequestInit,
): Promise<HasilAntrean> {
  const hasil = await ambil013(pemanggil, jalur, init);
  if ("galat" in hasil) return { jenis: "galat", galat: hasil.galat };
  if ("tidak_ada" in hasil) return { jenis: "tidak_ada" };
  if ("status" in hasil) return { jenis: "galat", galat: petakanStatus(hasil.status) };
  return apakahAntrean(hasil.badan)
    ? { jenis: "antrean", antrean: hasil.badan }
    : { jenis: "galat", galat: "sistem" };
}

/** `GET /api/v1/kurasi/antrean`. Juga dipakai cangkang mengenali kurator (K-8). */
export function bacaAntrean(pemanggil: Pemanggil): Promise<HasilAntrean> {
  return antreanDari(pemanggil, JALUR_ANTREAN, { method: "GET" });
}

export type BadanPutusan =
  | { readonly jenis: "setujui"; readonly catatan: string }
  | { readonly jenis: "sunting_lalu_setujui"; readonly catatan: string; readonly suntingan: Suntingan }
  | { readonly jenis: "tolak"; readonly alasan_tolak: string }
  | { readonly jenis: "tunda"; readonly catatan: string; readonly kembali_pada: string };

export function putuskan(
  idButir: string,
  badan: BadanPutusan,
  pemanggil: Pemanggil,
): Promise<HasilAntrean> {
  return antreanDari(pemanggil, jalurPutusan(idButir), kirimJson("POST", badan));
}

export function tarikButir(
  idButir: string,
  badan: PermintaanTarik,
  pemanggil: Pemanggil,
): Promise<HasilAntrean> {
  return antreanDari(pemanggil, jalurTarik(idButir), kirimJson("POST", badan));
}

/** Nilai `Pemicu` — urutan D-06 Bagian 7.5. */
export const PEMICU: readonly Pemicu[] = [
  "regulasi_sumber_berubah",
  "kekeliruan_isi_dilaporkan",
  "data_sumber_diperbarui",
];
