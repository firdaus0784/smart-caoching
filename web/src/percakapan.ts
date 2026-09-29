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

export function percakapanAktif(simpanan: Simpanan | null): string {
  let tersimpan: string | null = null;
  try {
    tersimpan = simpanan?.getItem(KUNCI) ?? null;
  } catch {
    tersimpan = null;
  }
  // Nilai tersimpan yang bukan UUID v4 — disunting tangan, atau dari versi
  // lain — diganti, bukan dikirim: peladen akan menolaknya (R-16).
  return tersimpan !== null && UUID_V4.test(tersimpan) ? tersimpan : percakapanBaru(simpanan);
}

/** Dipakai layar ketika pengguna membuka percakapan terdahulu. */
export function jadikanAktif(simpanan: Simpanan | null, id: string): void {
  simpan(simpanan, id);
}
