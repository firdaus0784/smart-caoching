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
  labelRujukanPengganti: "Pengubahnya",
  bukaSumber: "Buka sumber",

  // K-2, BT-71: kalimat pertama D-05 Bagian 10 saja. Kalimat keduanya
  // menjanjikan saran pertanyaan, dan bidang itu belum ada pada tanggapan.
  tidakDitemukanPenjelasan: "Belum ada dokumen rujukan yang memuat jawaban ini.",

  tombolSalinRingkasan: "Salin ringkasan",
  salinBerhasil: "Ringkasan sudah disalin.",
  salinTidakBisa: "Ringkasan tidak dapat disalin di peramban ini.",

  tombolCobaLagi: "Coba lagi",
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
  tidak_berhak: {
    tersimpan: "Akun Anda tidak dapat membuka bagian ini.",
    tidakTersimpan: "Akun Anda tidak dapat membuka bagian ini.",
  },
  pertanyaan_ditolak: {
    tersimpan: "Pertanyaan belum dapat diproses. Tulis ulang dengan kalimat utuh.",
    tidakTersimpan: "Pertanyaan belum dapat diproses. Tulis ulang dengan kalimat utuh.",
  },
};

/** Satu baris sitasi — PK-03: nama dokumen · penerbit · tahun · bagian. */
export function barisSitasi(judul: string, penerbit: string, tahun: number, bagian: string): string {
  return [judul, penerbit, String(tahun), bagian].join(" · ");
}
