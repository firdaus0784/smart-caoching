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
  HasilBaca,
  HasilDaftar,
  HasilTanya,
  JenisGalat,
  SatuPercakapan,
  StatusDasar,
  StatusKeberlakuan,
  Tanggapan,
} from "./kontrak";

export const JALUR_TANYA = "/api/v1/tanya";
export const JALUR_PERCAKAPAN = "/api/v1/percakapan";

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
    // Tanpa tajuk autentikasi dan tanpa token: identitas ditentukan backend (R-17).
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

function galat(jenis: JenisGalat): HasilTanya {
  return { jenis: "galat", galat: jenis };
}

function petakanStatus(status: number): JenisGalat {
  if (status === 401 || status === 403) return "tidak_berhak";
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
