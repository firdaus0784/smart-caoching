/**
 * Pengenal percakapan aktif — T-7 fitur 028, R-09, R-16, D-14 Bagian 4.1.
 *
 * Klien, bukan peladen, yang membangkitkan pengenal percakapan: tanggapan
 * `/tanya` tidak boleh bertambah bidang (C-20), sehingga peladen tidak dapat
 * mengembalikan pengenal yang ia buat (P-2).
 *
 * Disimpan pada simpanan lokal agar percakapan berlanjut sesudah muat ulang.
 * Ia **bukan** token: mengetahuinya tidak memberi akses, sebab kepemilikan
 * ditentukan identitas di peladen (R-02). Simpanan yang menolak tidak
 * menjatuhkan layar — percakapan berlanjut selama halaman terbuka saja.
 */

import type { Simpanan } from "./draf";

const KUNCI = "smart-coaching:percakapan-aktif";

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

function simpan(simpanan: Simpanan | null, id: string): void {
  try {
    simpanan?.setItem(KUNCI, id);
  } catch {
    // Lihat uraian modul: percakapan tetap berjalan selama halaman terbuka.
  }
}

export function percakapanBaru(simpanan: Simpanan | null): string {
  const id = crypto.randomUUID();
  simpan(simpanan, id);
  return id;
}

/**
 * Pengenal aktif, dan apakah ia **baru** dibangkitkan.
 *
 * `baru` memberi tahu layar bahwa peladen pasti belum mengenalnya, sehingga
 * riwayatnya tidak perlu diminta — permintaan yang pasti dijawab 404 adalah
 * permintaan sia-sia pada jaringan 3G (T-8, KB-147).
 */
export function percakapanAktif(simpanan: Simpanan | null): {
  readonly id: string;
  readonly baru: boolean;
} {
  let tersimpan: string | null = null;
  try {
    tersimpan = simpanan?.getItem(KUNCI) ?? null;
  } catch {
    tersimpan = null;
  }
  // Nilai tersimpan yang bukan UUID v4 — disunting tangan, atau dari versi
  // lain — diganti, bukan dikirim: peladen akan menolaknya (R-16).
  return tersimpan !== null && UUID_V4.test(tersimpan)
    ? { id: tersimpan, baru: false }
    : { id: percakapanBaru(simpanan), baru: true };
}

/** Dipakai layar ketika pengguna membuka percakapan terdahulu. */
export function jadikanAktif(simpanan: Simpanan | null, id: string): void {
  simpan(simpanan, id);
}

/** K-6 fitur 029: sesudah keluar, percakapan aktif tidak diwarisi orang
 * berikutnya yang memakai peramban yang sama. */
export function lupakanPercakapan(simpanan: Simpanan | null): void {
  try {
    simpanan?.removeItem(KUNCI);
  } catch {
    // Pengenal yang tertinggal tidak memberi akses: kepemilikan ditentukan
    // peladen (R-02 fitur 028). Ia hanya membuka percakapan kosong baru.
  }
}
