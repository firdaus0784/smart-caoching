/**
 * Seluruh teks antarmuka layar Tanya — T-4 fitur 027, R-12, C-13.
 *
 * SATU-SATUNYA tempat teks antarmuka. Berkas `.tsx` tidak boleh memuat teks
 * harfiah; `perkakas/pemeriksa/bahasa_antarmuka.py` menolaknya pada V-02, dan
 * memeriksa setiap untai di sini terhadap NFR-19 dan D-05 Bagian 10: kalimat
 * ≤ 20 kata, tanpa tanda seru, tanpa kata terlarang, tanpa kode galat, tanpa
 * singkatan sistem.
 *
 * Teks yang datang dari tanggapan — penjelasan, ringkasan, penafian — tidak
 * di sini: ia milik peladen dan sudah dijaga di sana.
 */

import type { JenisGalat, StatusDasar } from "./kontrak";

export const MIKROKOPI = {
  judulLayar: "Tanya",
  labelPertanyaan: "Pertanyaan Anda",
  petunjukPertanyaan: "Tulis persoalan pengelolaan sekolah dengan kalimat utuh.",
  tombolKirim: "Kirim pertanyaan",

  // KL-B — kosong pertama kali.
  kosongJudul: "Tanyakan persoalan pengelolaan sekolah Anda.",
  kosongIsi: "Setiap jawaban menyebut dokumen yang menjadi dasarnya.",

  // KL-A — memuat. Dibacakan pembaca layar; kerangkanya sendiri tanpa teks.
  memuat: "Jawaban sedang disusun.",

  judulRingkasan: "Ringkasan tindakan",
  judulPenjelasan: "Penjelasan",
  judulDasarRujukan: "Dasar rujukan",
  judulBacaanLanjutan: "Bacaan lanjutan",
  keteranganBacaanLanjutan: "Bacaan ini tidak dipakai untuk menyusun jawaban.",
  judulCatatanKeberlakuan: "Catatan keberlakuan",
  penandaDiubah: "Sudah diubah",
  bukaSumber: "Buka sumber",

  // K-2, BT-71: kalimat pertama D-05 Bagian 10 saja. Kalimat keduanya
  // menjanjikan saran pertanyaan, dan bidang itu belum ada pada tanggapan.
  tidakDitemukanPenjelasan: "Belum ada dokumen rujukan yang memuat jawaban ini.",

  tombolSalinRingkasan: "Salin ringkasan",
  salinBerhasil: "Ringkasan sudah disalin.",
  salinTidakBisa: "Ringkasan tidak dapat disalin di peramban ini.",

  tombolCobaLagi: "Coba lagi",

  // D-05 S-09 blok 9 dan 10 — fitur 028. Jawaban lama tidak pernah tampil:
  // regulasi yang menjadi dasarnya dapat dicabut sesudahnya (C-07).
  judulPertanyaanSebelumnya: "Pertanyaan sebelumnya",
  keteranganPertanyaanSebelumnya: "Ketuk pertanyaan untuk menanyakannya lagi. Jawaban lama tidak disimpan.",
  tombolPercakapanBaru: "Percakapan baru",
  judulPercakapanTerdahulu: "Percakapan terdahulu",
  tombolTampilkanTerdahulu: "Tampilkan percakapan terdahulu",
  terdahuluKosong: "Belum ada percakapan terdahulu.",
  terdahuluTidakTermuat: "Percakapan terdahulu belum dapat dimuat.",

  // D-05 S-01 Masuk — fitur 029. Satu kalimat penolakan bagi semua sebab (R-04).
  judulMasuk: "Masuk",
  labelNamaPengguna: "Nama pengguna",
  petunjukNamaPengguna: "Tertulis pada lembar akun dari tim peneliti, misalnya ks-017.",
  labelSandi: "Sandi",
  tombolMasuk: "Masuk",
  masukDitolak: "Nama pengguna atau sandi belum cocok. Periksa lagi, atau hubungi tim peneliti.",
  masukKosong: "Nama pengguna dan sandi wajib diisi.",
  masukLuring: "Sedang tidak terhubung. Coba masuk lagi saat sinyal kembali.",
  masukGangguan: "Ada gangguan di sistem kami. Coba lagi sebentar lagi.",
  lupaSandi: "Lupa sandi? Hubungi tim peneliti. Tim akan membuatkan sandi baru.",
  perluMasukLagi: "Anda perlu masuk lagi. Pertanyaan yang sedang Anda tulis tetap tersimpan.",
  perluMasukLagiSaja: "Anda perlu masuk lagi.",
  memeriksaAkun: "Sedang memeriksa akun Anda.",
  tombolKeluar: "Keluar",

  // D-05 S-02 — fitur 030. Naskahnya sendiri milik ketua peneliti (ET-02) dan
  // tidak ditulis di sini; layar memuatnya dari berkas yang diisi tim.
  judulPersetujuan: "Persetujuan penelitian",
  tautanPersetujuan: "Persetujuan penelitian",
  tombolSetuju: "Saya setuju",
  tombolTidakSetuju: "Saya tidak setuju",
  keteranganMenolak: "Menolak tidak mengurangi fitur apa pun yang dapat Anda pakai.",
  naskahBelumAda: "Naskah persetujuan belum tersedia. Anda tetap dapat memakai seluruh fitur.",
  sudahSetuju: "Anda sudah menyetujui perekaman data penelitian.",
  tombolCabut: "Cabut persetujuan",
  tombolKembali: "Kembali",
  persetujuanGagal: "Persetujuan belum dapat dicatat. Muat ulang halaman, lalu coba lagi.",

  // D-05 S-03.
  tombolLanjut: "Lanjut",
  tombolMulaiProfil: "Mulai mengisi profil",

  // D-05 S-04.
  judulProfil: "Profil sekolah",
  labelJabatan: "Jabatan",
  labelMasaKerja: "Masa kerja (tahun)",
  labelJumlahRombel: "Jumlah rombongan belajar",
  labelJumlahPtk: "Jumlah pendidik dan tenaga kependidikan",
  labelJalurAkreditasi: "Jalur akreditasi",
  jalurVisitasi: "Visitasi",
  jalurAutomasi: "Automasi",
  labelWilayah: "Wilayah (kabupaten atau kota)",
  judulPrioritas: "Prioritas pengelolaan",
  petunjukPrioritas: "Pilih tiga sampai lima, mulai dari yang paling penting.",
  prioritasJumlah: "Pilih tiga sampai lima prioritas.",
  tombolSimpanProfil: "Simpan dan mulai bertanya",
  profilDitolak: "Isian profil belum sesuai. Periksa lagi setiap isian.",
  prioritasDitolak: "Pilih tiga sampai lima prioritas yang berbeda.",
  profilGangguan: "Profil belum tersimpan. Isian Anda masih di layar, coba simpan lagi.",
} as const;

/** D-05 S-03 — empat layar, diputus pada Gerbang 2 fitur 030 (K-8). Layar kedua
 * adalah satu-satunya isi yang FR-A04 wajibkan, dan tidak dapat dilewati. */
export const PENGENALAN: readonly { readonly judul: string; readonly isi: string }[] = [
  {
    judul: "Yang dapat dibantu",
    isi: "Aplikasi ini menjawab pertanyaan pengelolaan sekolah dasar. Setiap jawaban menyebut dokumen yang menjadi dasarnya.",
  },
  {
    judul: "Alat bantu, bukan penentu",
    isi: "Keputusan tetap berada pada Anda sebagai kepala sekolah. Jawaban membantu menimbang, tidak menggantikan pertimbangan Anda.",
  },
  {
    judul: "Bila dasarnya tidak ada",
    isi: "Bila tidak ada dokumen yang memuat jawabannya, aplikasi mengatakannya terus terang. Itu bukan kesalahan Anda.",
  },
  {
    judul: "Menjaga data",
    isi: "Akun Anda tidak memuat nama Anda. Jangan tulis nama orang atau nomor pribadi pada pertanyaan.",
  },
];

/** Nama kategori D-03 Bagian 5 apa adanya (K-7). Kodenya tidak pernah tampil. */
export const LABEL_KATEGORI = {
  K1: "Kurikulum dan pembelajaran",
  K2: "Kepegawaian dan tenaga kependidikan",
  K3: "Kesiswaan",
  K4: "Sarana dan prasarana",
  K5: "Keuangan dan pembiayaan",
  K6: "Kemitraan dan hubungan masyarakat",
  K7: "Penjaminan mutu dan akreditasi",
  K8: "Kepemimpinan dan budaya sekolah",
} as const;

/**
 * Penanda dasar rujukan — PK-04, R-03. Teks, bukan warna saja (AK-04), dan
 * tanpa angka (FR-F06).
 *
 * `di_luar_domain` tidak disebut PK-04, yang ditulis sebelum D-14 menambahkan
 * nilai keempat. Penandanya dipilih di sini dan dicatat pada KB-130.
 */
export const PENANDA_DASAR: Readonly<Record<StatusDasar, string>> = {
  kuat: "Dasar rujukan kuat",
  terbatas: "Dasar rujukan terbatas",
  tidak_ditemukan: "Tidak ditemukan dasar rujukan",
  di_luar_domain: "Di luar cakupan layanan ini",
};

/**
 * Pesan galat — KL-D dan KL-E, R-10. Satu kalimat keadaan, satu kalimat apa
 * yang aman atau apa yang dapat dilakukan.
 *
 * Dua bentuk tiap pesan, sebab `plan.md` Bagian 5: "tersimpan" hanya
 * dinyatakan bila draf **memang** tersimpan. Simpanan lokal dapat menolak
 * ditulis, dan pernyataan aman yang tidak benar lebih buruk daripada tidak
 * ada pernyataan.
 */
export const PESAN_GALAT: Readonly<
  Record<JenisGalat, { readonly tersimpan: string; readonly tidakTersimpan: string }>
> = {
  luring: {
    tersimpan: "Sedang tidak terhubung. Pertanyaan Anda tersimpan sebagai draf.",
    tidakTersimpan: "Sedang tidak terhubung. Salin pertanyaan Anda sebelum menutup halaman ini.",
  },
  sistem: {
    tersimpan: "Ada gangguan di sistem kami. Yang Anda ketik sudah tersimpan.",
    tidakTersimpan: "Ada gangguan di sistem kami. Salin pertanyaan Anda sebelum menutup halaman ini.",
  },
  // Fitur 029. Ditampilkan hanya bila layar Tanya berdiri tanpa cangkang;
  // di dalam `Aplikasi`, 401 langsung membuka S-01.
  belum_masuk: {
    tersimpan: "Anda perlu masuk lagi. Pertanyaan yang sedang Anda tulis tetap tersimpan.",
    tidakTersimpan: "Anda perlu masuk lagi. Salin pertanyaan Anda sebelum menutup halaman ini.",
  },
  tidak_berhak: {
    tersimpan: "Akun Anda tidak dapat membuka bagian ini.",
    tidakTersimpan: "Akun Anda tidak dapat membuka bagian ini.",
  },
  // K-3 fitur 028: benar bagi kalimat yang tidak utuh maupun pertanyaan yang
  // memuat nomor pribadi — layar tidak membaca badan galat (R-10 fitur 027).
  pertanyaan_ditolak: {
    tersimpan: "Pertanyaan belum dapat diproses. Pastikan kalimatnya utuh dan tanpa nomor pribadi.",
    tidakTersimpan: "Pertanyaan belum dapat diproses. Pastikan kalimatnya utuh dan tanpa nomor pribadi.",
  },
};

/** Penanda letak pada S-03 — "Layar 2 dari 4". */
export function langkahPengenalan(ke: number, jumlah: number): string {
  return `Layar ${ke} dari ${jumlah}`;
}

/** Rujukan pengubah pada sitasi berstatus diubah — FR-F14. */
export function teksPengganti(rujukan: string): string {
  return `Pengubahnya: ${rujukan}`;
}

/** Satu baris sitasi — PK-03: nama dokumen · penerbit · tahun · bagian. */
export function barisSitasi(judul: string, penerbit: string, tahun: number, bagian: string): string {
  return [judul, penerbit, String(tahun), bagian].join(" · ");
}
