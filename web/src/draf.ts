/**
 * Draf pertanyaan pada simpanan lokal peramban — T-5 fitur 027, R-09.
 *
 * Simpanan lokal dapat menolak ditulis: mode pribadi, kuota penuh, atau
 * peramban yang menerima tanpa menyimpan. Kegagalannya tidak boleh
 * menjatuhkan layar — tetapi juga tidak boleh diam. `simpanDraf` karena itu
 * mengembalikan apakah draf **dapat dibaca kembali**, dan layar hanya
 * menyatakan "tersimpan" bila jawabannya benar (`plan.md` Bagian 5, M-14).
 *
 * Yang disimpan hanya teks pertanyaan yang sedang diketik, pada peramban
 * pengguna sendiri. Tanggapan tidak pernah disimpan: jawaban yang menua
 * melanggar C-07 (D-14 Bagian 4.3).
 */

export type Simpanan = Pick<Storage, "getItem" | "setItem" | "removeItem">;

const KUNCI = "smart-coaching:draf-tanya";

export function simpanDraf(simpanan: Simpanan | null, teks: string): boolean {
  if (simpanan === null) return false;
  try {
    if (teks === "") {
      simpanan.removeItem(KUNCI);
      return simpanan.getItem(KUNCI) === null;
    }
    simpanan.setItem(KUNCI, teks);
    return simpanan.getItem(KUNCI) === teks;
  } catch {
    return false;
  }
}

export function bacaDraf(simpanan: Simpanan | null): string {
  if (simpanan === null) return "";
  try {
    return simpanan.getItem(KUNCI) ?? "";
  } catch {
    return "";
  }
}

export function hapusDraf(simpanan: Simpanan | null): void {
  if (simpanan === null) return;
  try {
    simpanan.removeItem(KUNCI);
  } catch {
    // Draf yang tidak dapat dihapus tidak merugikan siapa pun: ia hanya
    // muncul lagi sebagai isian pada kunjungan berikutnya.
  }
}
