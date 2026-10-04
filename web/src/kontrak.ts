/**
 * Bentuk tanggapan `POST /api/v1/tanya` — D-14 Bagian 4.1, C-20.
 *
 * Salinan tangan model pydantic pada `src/rag/jawaban/tanggapan.py`, karena
 * TypeScript tidak dapat mengimpornya. Nama bidang dan nilai enum dijaga
 * `perkakas/pemeriksa/kontrak_web.py` pada V-03: salinan yang hanyut
 * menjatuhkan gerbang, bukan muncul sebagai layar kosong di lapangan.
 *
 * Bidang ditulis satu per baris dengan `readonly`; pemeriksa membaca bentuk
 * itu. Layar tidak mengubah tanggapan — ia hanya menampilkannya.
 */

export type StatusDasar = "kuat" | "terbatas" | "tidak_ditemukan" | "di_luar_domain";

/** `dicabut` tidak pernah tiba pada sitasi (VS-06, C-07); ia ada di sini
 * karena daftar nilai enum tidak diubah (AG-04). */
export type StatusKeberlakuan = "berlaku" | "diubah" | "dicabut";

export interface Versi {
  readonly model: string;
  readonly indeks: string;
  readonly kode: string;
}

/** `peringkat_kepercayaan` tidak ada, sama dengan modelnya — BT-64. */
export interface KlaimTampil {
  readonly teks: string;
  readonly id_segmen: readonly string[];
}

export interface Sitasi {
  readonly id_dokumen: string;
  readonly judul: string;
  readonly penerbit: string;
  readonly tahun: number;
  readonly bagian: string;
  readonly status_keberlakuan: StatusKeberlakuan;
  readonly rujukan_pengganti: string | null;
  readonly tautan: string | null;
}

/** Sengaja tanpa bidang `Sitasi` — bukan sitasi yang lebih lemah (FR-D06). */
export interface BacaanLanjutan {
  readonly judul: string;
  readonly tautan: string;
}

export interface Tanggapan {
  readonly id_pesan: string;
  readonly status_dasar: StatusDasar;
  readonly ringkasan_tindakan: readonly string[];
  readonly penjelasan: string;
  readonly klaim: readonly KlaimTampil[];
  readonly sitasi: readonly Sitasi[];
  readonly bacaan_lanjutan: readonly BacaanLanjutan[];
  readonly catatan_keberlakuan: string;
  readonly penafian: string;
  readonly versi: Versi;
}

/**
 * Keadaan galat bagi layar — D-05 Bagian 7 KL-D dan KL-E, R-10.
 *
 * Bukan badan galat peladen. Layar tidak menampilkan isi galat apa pun, maka
 * klien tidak membacanya: status HTTP dipetakan ke salah satu nilai ini, dan
 * kalimatnya datang dari mikrokopi. Bentuk badan galat peladen sendiri
 * berbeda dari D-14 Bagian 4.2 — TK-66.
 */
export type JenisGalat =
  /** KL-E — permintaan tidak sampai; draf tetap tersimpan. */
  | "luring"
  /** Sesi tidak sah atau sudah berakhir (401) — layar kembali ke S-01.
   * Fitur 029; sebelumnya 401 dan 403 sama-sama `tidak_berhak`. */
  | "belum_masuk"
  /** Peladen menolak akun ini untuk rute ini (403). */
  | "tidak_berhak"
  /** Pertanyaan ditolak sebagai masukan; dapat ditulis ulang. */
  | "pertanyaan_ditolak"
  /** KL-D — selebihnya, termasuk tanggapan yang bentuknya tidak dikenali. */
  | "sistem";

/**
 * Riwayat percakapan — D-14 Bagian 4.3, fitur 028.
 *
 * `Giliran` **tanpa tanggapan, dengan sengaja**: jawaban yang tersimpan menua,
 * dan jawaban lama yang ditampilkan ulang melanggar C-07. Membuka riwayat
 * berarti bertanya ulang. Nama bidangnya dijaga pemeriksa kontrak V-03
 * terhadap model `Giliran` pada `src/api/percakapan.py`.
 */
export interface Giliran {
  readonly pertanyaan: string;
  readonly id_pesan: string;
  readonly waktu: string;
}

export interface SatuPercakapan {
  readonly id_percakapan: string;
  readonly giliran: readonly Giliran[];
}

export type HasilDaftar =
  | { readonly jenis: "daftar"; readonly percakapan: readonly string[] }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

export type HasilBaca =
  | { readonly jenis: "percakapan"; readonly percakapan: SatuPercakapan }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

export type HasilTanya =
  | { readonly jenis: "jawaban"; readonly tanggapan: Tanggapan }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

/**
 * Hasil `POST /api/v1/auth/masuk` — D-14 Bagian 4.4, fitur 029.
 *
 * `ditolak` satu bagi semua sebab: peladen sengaja tidak membedakan akun tak
 * ada, isian salah, akun ditahan, maupun nonaktif (R-04), dan layar tidak
 * mencoba menebaknya.
 */
export type HasilMasuk =
  | { readonly jenis: "masuk" }
  | { readonly jenis: "ditolak" }
  | { readonly jenis: "galat"; readonly galat: "luring" | "sistem" };

/**
 * Akun saya — D-14 Bagian 4.5, fitur 030.
 *
 * `PermintaanProfil` dan `Naskah` dijaga pemeriksa kontrak V-03 terhadap model
 * bernama sama pada `src/api/saya.py`; `JalurAkreditasi` dan
 * `KeadaanPersetujuan` terhadap enum fitur 022.
 */
export type JalurAkreditasi = "visitasi" | "automasi";

export type KeadaanPersetujuan = "belum_diminta" | "diberikan" | "ditolak" | "dicabut";

export interface PermintaanProfil {
  readonly jabatan: string;
  readonly masa_kerja: number;
  readonly jumlah_rombel: number;
  readonly jumlah_ptk: number;
  readonly jalur_akreditasi: JalurAkreditasi;
  readonly wilayah: string;
}

/** Ringkasan aktivasi — bentuk bersama keempat rute `/saya/*` (K-5). */
export interface Ringkasan {
  readonly profil: PermintaanProfil | null;
  readonly prioritas: readonly string[];
  readonly persetujuan: KeadaanPersetujuan;
}

/** Berkas naskah ET-02 yang diisi tim — ditampilkan apa adanya (K-4). */
export interface Naskah {
  readonly versi: string;
  readonly judul: string;
  readonly paragraf: readonly string[];
}

export type HasilRingkasan =
  | { readonly jenis: "ringkasan"; readonly ringkasan: Ringkasan }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

export type HasilNaskah =
  | { readonly jenis: "naskah"; readonly naskah: Naskah }
  | { readonly jenis: "belum_ada" };
