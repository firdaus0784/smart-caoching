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

/** Hasil `DELETE /api/v1/saya/data` — D-14 Bagian 4.5, fitur 033. */
export type HasilPenarikan =
  | { readonly jenis: "diterima" }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

export type HasilNaskah =
  | { readonly jenis: "naskah"; readonly naskah: Naskah }
  | { readonly jenis: "belum_ada" };

/**
 * Penemuan — D-14 Bagian 4.6, fitur 013.
 *
 * Dijaga pemeriksa kontrak V-03 terhadap model bernama sama pada
 * `src/api/penemuan.py` dan `src/ingest/kurasi/sumber.py`; enum terhadap
 * `KategoriMasalah`, `JenisSumberButir`, dan `KeadaanBeranda`.
 *
 * `ButirLengkap` ditulis rata, bukan `extends`: pemeriksa membaca bidang
 * satu per baris, dan bentuk lain dilaporkan tidak ditemukan.
 */
export type KategoriMasalah = "K1" | "K2" | "K3" | "K4" | "K5" | "K6" | "K7" | "K8";

export type JenisSumberButir = "riset" | "regulasi" | "data_resmi" | "praktik_baik";

export type KeadaanBeranda = "berisi" | "belum_ada_prioritas" | "belum_ada_butir" | "habis";

export interface SumberButir {
  readonly judul: string;
  readonly penerbit: string;
  readonly tahun: number;
  readonly tautan: string | null;
}

export interface ButirRingkas {
  readonly id_butir: string;
  readonly kategori: KategoriMasalah;
  readonly jenis_sumber: JenisSumberButir;
  readonly judul: string;
  readonly alasan_relevansi: string;
  readonly perkiraan_waktu_baca: number;
}

/** Tanpa bidang lisensi, dengan sengaja: layar tidak menyimpulkan boleh
 * tidaknya teks penuh dari untai lisensi — `boleh_teks_penuh` milik peladen. */
export interface ButirLengkap {
  readonly id_butir: string;
  readonly kategori: KategoriMasalah;
  readonly jenis_sumber: JenisSumberButir;
  readonly judul: string;
  readonly alasan_relevansi: string;
  readonly perkiraan_waktu_baca: number;
  readonly inti_temuan: string;
  readonly implikasi_tindakan: readonly string[];
  readonly tenggat_terkait: string | null;
  readonly boleh_teks_penuh: boolean;
  readonly sumber: SumberButir;
}

export interface Beranda {
  readonly keadaan: KeadaanBeranda;
  readonly butir: readonly ButirRingkas[];
}

export interface PermintaanTolak {
  readonly alasan: string;
}

export type HasilBeranda =
  | { readonly jenis: "beranda"; readonly beranda: Beranda }
  | { readonly jenis: "tidak_ada" }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

export type HasilButir =
  | { readonly jenis: "butir"; readonly butir: ButirLengkap }
  | { readonly jenis: "tidak_ada" }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

/**
 * Kurasi — D-14 Bagian 4.7, fitur 013. Dijaga terhadap model pada
 * `src/api/kurasi.py`; `AlasanTolak` dan `Pemicu` terhadap enum fitur 010.
 */
export type AlasanTolak =
  | "TL-01"
  | "TL-02"
  | "TL-03"
  | "TL-04"
  | "TL-11"
  | "TL-05"
  | "TL-06"
  | "TL-07"
  | "TL-08"
  | "TL-09"
  | "TL-10";

export type Pemicu = "regulasi_sumber_berubah" | "kekeliruan_isi_dilaporkan" | "data_sumber_diperbarui";

export interface KandidatTampil {
  readonly id_butir: string;
  readonly kategori: KategoriMasalah;
  readonly jenis_sumber: JenisSumberButir;
  readonly judul: string;
  readonly alasan_relevansi: string;
  readonly inti_temuan: string;
  readonly implikasi_tindakan: readonly string[];
  readonly perkiraan_waktu_baca: number;
  readonly tenggat_terkait: string | null;
  readonly lisensi: string;
  readonly status_keberlakuan: StatusKeberlakuan | null;
  readonly sumber: SumberButir;
  readonly masuk_pada: string;
}

export interface TayangTampil {
  readonly id_butir: string;
  readonly kategori: KategoriMasalah;
  readonly jenis_sumber: JenisSumberButir;
  readonly judul: string;
  readonly lisensi: string;
  readonly status_keberlakuan: StatusKeberlakuan | null;
  readonly tayang_pada: string;
  readonly perlu_tinjauan: boolean;
}

export interface Antrean {
  readonly menunggu: readonly KandidatTampil[];
  readonly tayang: readonly TayangTampil[];
}

/** Empat bidang parafrase saja (D-06 Bagian 7.3). */
export interface Suntingan {
  readonly judul: string;
  readonly alasan_relevansi: string;
  readonly inti_temuan: string;
  readonly implikasi_tindakan: readonly string[];
}

export interface PermintaanTarik {
  readonly pemicu: Pemicu;
  readonly catatan: string;
  readonly status_terkini?: StatusKeberlakuan | null;
  readonly angka_berubah_bermakna?: boolean;
}

export type HasilAntrean =
  | { readonly jenis: "antrean"; readonly antrean: Antrean }
  | { readonly jenis: "tidak_ada" }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

/**
 * Analitik penelitian — D-14 Bagian 4.8, fitur 035. Angka `null` berarti
 * belum dapat diukur, bukan nol; layar tidak menukarnya.
 */
export type MetrikTertunda =
  | "rasio_penuntasan"
  | "rasio_penelusuran_sumber"
  | "rasio_verifikasi"
  | "rasio_komitmen"
  | "rasio_penerapan"
  | "akurasi_qa";

export interface AktifHarian {
  readonly tanggal: string;
  readonly pengguna: number;
}

export interface AktifMingguan {
  readonly mulai: string;
  readonly pengguna: number;
}

export interface Retensi {
  readonly hari: number;
  readonly kohort: number;
  readonly kembali: number;
  readonly rasio: number | null;
}

export interface RingkasanSesi {
  readonly jumlah: number;
  readonly median_menit: number | null;
  readonly rerata_menit: number | null;
}

export interface Keterlibatan {
  readonly aktif_harian: readonly AktifHarian[];
  readonly aktif_mingguan: readonly AktifMingguan[];
  readonly retensi: readonly Retensi[];
  readonly sesi: RingkasanSesi;
}

export interface RasioPenemuan {
  readonly disajikan: number;
  readonly dibuka: number;
  readonly rasio: number | null;
}

export interface BelumTerukur {
  readonly metrik: MetrikTertunda;
  readonly sebab: string;
}

export interface Integritas {
  readonly per_jenis: Readonly<Record<string, number>>;
  readonly per_versi_aplikasi: Readonly<Record<string, number>>;
  readonly per_versi_model: Readonly<Record<string, number>>;
  readonly pertama: string | null;
  readonly terakhir: string | null;
  readonly pengembangan: number;
}

export interface RingkasanAnalitik {
  readonly dihitung_pada: string;
  readonly keterlibatan: Keterlibatan;
  readonly penemuan: RasioPenemuan;
  readonly belum_terukur: readonly BelumTerukur[];
  readonly integritas: Integritas;
}

export interface PermintaanEkspor {
  readonly dari: string;
  readonly sampai: string;
  readonly termasuk_pengembangan: boolean;
}

export type HasilAnalitik =
  | { readonly jenis: "ringkasan"; readonly ringkasan: RingkasanAnalitik }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };

export type HasilEkspor =
  | { readonly jenis: "berkas"; readonly isi: Blob; readonly nama: string }
  | { readonly jenis: "galat"; readonly galat: JenisGalat };
