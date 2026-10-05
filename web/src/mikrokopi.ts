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

  // Navigasi — D-05 Bagian 3.1 pada fitur 013 (K-7): dua tujuan sampai isi
  // "Milik saya" dibangun pada baris 031 dan 032.
  labelNavigasi: "Navigasi utama",
  navBeranda: "Beranda",
  navTanya: "Tanya",

  // D-05 S-05 Beranda — fitur 013.
  judulBeranda: "Butir hari ini",
  berandaMemuat: "Butir hari ini sedang dimuat.",
  berandaBelumPrioritas: "Butir muncul setelah Anda menetapkan prioritas pengelolaan.",
  berandaBelumAda: "Belum ada bacaan untuk prioritas Anda. Bacaan muncul setelah kurator menyetujuinya.",
  berandaHabis: "Butir hari ini sudah tampil semua. Bacaan baru muncul setelah kurator menyetujuinya.",
  berandaGangguan: "Butir hari ini belum dapat dimuat. Coba lagi sebentar lagi.",
  berandaLuringSalinan: "Sedang tidak terhubung. Ini salinan butir hari ini dari perangkat Anda.",
  berandaLuringKosong: "Sedang tidak terhubung. Butir hari ini belum pernah dimuat di perangkat ini.",
  tombolTanyaCepat: "Ajukan pertanyaan",

  // D-05 S-06 Detail butir — fitur 013.
  butirMemuat: "Butir sedang dimuat.",
  butirTidakAda: "Butir ini sudah tidak tersedia.",
  butirGangguan: "Butir belum dapat dimuat. Coba lagi sebentar lagi.",
  butirLuringSalinan: "Sedang tidak terhubung. Ini salinan yang tersimpan di perangkat Anda.",
  butirLuringKosong: "Sedang tidak terhubung. Butir ini belum tersimpan di perangkat ini.",
  judulMengapaRelevan: "Mengapa relevan untuk sekolah Anda",
  judulIntiTemuan: "Inti temuan",
  judulImplikasi: "Yang dapat Anda lakukan",
  judulSumber: "Sumber",
  bukaHalamanSumber: "Buka halaman sumber",
  teksPenuhTertutup: "Teks lengkapnya tidak ditampilkan karena lisensi sumbernya tidak mengizinkan.",
  tombolBelumRelevan: "Belum relevan",
  labelAlasanBelumRelevan: "Mengapa butir ini belum relevan bagi sekolah Anda?",
  tombolKirimAlasan: "Kirim",
  tombolBatal: "Batal",
  tombolKembaliBeranda: "Kembali ke beranda",
  alasanDitolak: "Tulis alasan singkat tanpa nomor pribadi, lalu kirim lagi.",
  alasanLuring: "Sedang tidak terhubung. Alasan Anda belum terkirim dan masih ada di isian.",
  alasanGangguan: "Alasan belum terkirim. Isian Anda masih ada, coba kirim lagi.",

  // D-05 S-15 Antrean kurasi dan S-16 Penyuntingan — fitur 013. Kurator
  // dikenali tanpa rute baru (K-8); skor relevansi tidak tampil (BT-24, C-16).
  akunTidakDikenali: "Akun Anda tidak dapat membuka bagian mana pun di aplikasi ini.",
  judulKurasi: "Antrean kurasi",
  judulMenunggu: "Menunggu putusan",
  judulSedangTayang: "Sedang tayang",
  kurasiMemuat: "Antrean sedang dimuat.",
  antreanKosong: "Antrean kosong. Kandidat masuk setelah lolos penyaringan oleh tim.",
  tayangKosong: "Belum ada butir yang tayang.",
  kurasiGangguan: "Antrean belum dapat dimuat. Coba lagi sebentar lagi.",
  kurasiLuring: "Sedang tidak terhubung. Putusan Anda belum terkirim.",
  perluTinjauan: "Perlu ditinjau: data sumbernya diperbarui.",
  tombolSetujui: "Setujui",
  tombolSunting: "Sunting",
  tombolTolak: "Tolak",
  tombolTunda: "Tunda",
  tombolTarik: "Tarik",
  tombolKirimPutusan: "Kirim putusan",
  labelCatatan: "Catatan singkat",
  labelAlasanTolak: "Alasan penolakan",
  labelKembaliPada: "Kembali ke antrean pada",
  labelPemicu: "Sebab penarikan",
  labelStatusTerkini: "Status regulasi sekarang",
  labelAngkaBermakna: "Angka pada sumber berubah bermakna",
  putusanBelumLengkap: "Lengkapi isian putusan, lalu kirim lagi.",
  putusanDitolak:
    "Putusan belum dapat dicatat. Periksa isian. Bila regulasinya tidak berlaku lagi, pilih Tolak.",
  putusanSudahDiambil: "Butir ini sudah diputus atau ditarik. Daftar sudah dimuat ulang.",
  putusanGangguan: "Putusan belum tercatat karena gangguan di sistem kami. Coba lagi.",
  judulSunting: "Sunting parafrase",
  labelJudul: "Judul",
  labelAlasanRelevansi: "Mengapa relevan untuk sekolah",
  labelIntiTemuan: "Inti temuan",
  labelImplikasi: "Implikasi tindakan, satu per baris",
  keteranganTetap: "Bagian berikut tidak dapat disunting karena mengubah butirnya, bukan parafrasenya.",
  tombolSimpanSetujui: "Simpan dan setujui",
} as const;

/** Alasan penolakan baku D-06 Bagian 7.4 — kodenya tidak tampil (C-13).
 * Kalimat D-06 apa adanya, kecuali dua rujukan bersingkatan yang dilepas:
 * contoh "BAN-S/M" pada TL-11 dan "(NFR-19)" pada TL-07. */
export const LABEL_ALASAN_TOLAK = {
  "TL-01": "Tidak relevan dengan konteks sekolah dasar Indonesia",
  "TL-02": "Lisensi tidak jelas atau tidak mengizinkan penggunaan",
  "TL-03": "Sumber tidak kredibel atau tidak dapat ditelusuri",
  "TL-04": "Regulasi sudah dicabut atau digantikan",
  "TL-11": "Menyebut lembaga atau istilah yang sudah berganti tanpa keterangan, sehingga menyesatkan",
  "TL-05": "Parafrase terlalu dekat dengan teks asli dan sulit diperbaiki",
  "TL-06": "Isi keliru atau bertentangan dengan regulasi yang berlaku",
  "TL-07": "Terlalu teknis untuk pengguna sasaran",
  "TL-08": "Duplikat butir yang sudah tayang",
  "TL-09": "Implikasi tindakan tidak dapat dijalankan kepala sekolah",
  "TL-10": "Data sudah usang",
} as const;

/** Pemicu penarikan D-06 Bagian 7.5. */
export const LABEL_PEMICU = {
  regulasi_sumber_berubah: "Regulasi sumber dicabut atau diubah",
  kekeliruan_isi_dilaporkan: "Isi butir keliru",
  data_sumber_diperbarui: "Data sumber diperbarui",
} as const;

/** Status keberlakuan regulasi — KL-07. */
export const LABEL_STATUS = {
  berlaku: "Berlaku",
  diubah: "Diubah",
  dicabut: "Dicabut",
} as const;

/** Label jenis sumber S-06 blok 1 — FR-G04, teks bukan warna saja. */
export const LABEL_JENIS_SUMBER = {
  riset: "Riset",
  regulasi: "Regulasi",
  data_resmi: "Data Resmi",
  praktik_baik: "Praktik Baik",
} as const;

/** Perkiraan waktu baca — D-05 S-06 blok 4, "± 4 menit". */
export function waktuBaca(menit: number): string {
  return `± ${menit} menit`;
}

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

/** Satu baris sumber butir — S-06 blok 7 dan S-16: nama · penerbit · tahun. */
export function barisSumber(judul: string, penerbit: string, tahun: number): string {
  return [judul, penerbit, String(tahun)].join(" · ");
}

/** Keterangan baris kurasi — lisensi, dan status regulasi bila ada. */
export function keteranganKurasi(lisensi: string, status: string | null): string {
  const lisensiSaja = `Lisensi: ${lisensi}`;
  return status === null ? lisensiSaja : `${lisensiSaja} · Status regulasi: ${status}`;
}

/** Jenis sumber dan kategori butir pada S-16. */
export function jenisDanKategori(jenis: string, kategori: string): string {
  return `${jenis} · ${kategori}`;
}
