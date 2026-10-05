/**
 * Salinan luring butir hari ini — T-7 fitur 013, P-7, D-05 Bagian 8.
 *
 * "Butir hari ini disimpan lokal setelah dimuat; dapat dibaca ulang tanpa
 * koneksi" (S-05), dan "isi lengkap tersimpan bersama butir" (S-06). Butir
 * terkurasi bukan data pribadi, sehingga menyimpannya pada peramban tidak
 * menyentuh KM-03. Pola yang sama dengan `draf.ts`: penulisan yang gagal tidak
 * menjatuhkan layar dan tidak diaku tersimpan.
 *
 * Salinan dihapus saat keluar (K-6 fitur 029): peramban sekolah dapat dipakai
 * bergantian, dan prioritas seseorang terbaca dari butir yang ia terima.
 */

import type { Simpanan } from "../draf";
import { apakahBeranda, apakahButirLengkap } from "../klien";
import type { Beranda, ButirLengkap } from "../kontrak";

const KUNCI = "smart-coaching:beranda";

interface Isi {
  readonly beranda: Beranda;
  readonly butir: Readonly<Record<string, ButirLengkap>>;
}

function baca(simpanan: Simpanan | null): Isi | null {
  if (simpanan === null) return null;
  try {
    const mentah = simpanan.getItem(KUNCI);
    if (mentah === null) return null;
    const isi: unknown = JSON.parse(mentah);
    if (typeof isi !== "object" || isi === null) return null;
    const { beranda, butir } = isi as Record<string, unknown>;
    if (!apakahBeranda(beranda) || typeof butir !== "object" || butir === null) return null;
    const sah: Record<string, ButirLengkap> = {};
    for (const [kunci, nilai] of Object.entries(butir)) {
      if (apakahButirLengkap(nilai)) sah[kunci] = nilai;
    }
    return { beranda, butir: sah };
  } catch {
    return null;
  }
}

function tulis(simpanan: Simpanan | null, isi: Isi): boolean {
  if (simpanan === null) return false;
  try {
    const teks = JSON.stringify(isi);
    simpanan.setItem(KUNCI, teks);
    return simpanan.getItem(KUNCI) === teks;
  } catch {
    return false;
  }
}

/** Simpan beranda; butir lengkap yang masih termasuk hari ini dipertahankan. */
export function simpanBeranda(simpanan: Simpanan | null, beranda: Beranda): boolean {
  const lama = baca(simpanan)?.butir ?? {};
  const tetap: Record<string, ButirLengkap> = {};
  for (const b of beranda.butir) {
    const satu = lama[b.id_butir];
    if (satu !== undefined) tetap[b.id_butir] = satu;
  }
  return tulis(simpanan, { beranda, butir: tetap });
}

/** Tambahkan isi lengkap satu butir pada salinan beranda yang ada. */
export function simpanButir(simpanan: Simpanan | null, butir: ButirLengkap): boolean {
  const lama = baca(simpanan);
  if (lama === null) return false;
  return tulis(simpanan, { beranda: lama.beranda, butir: { ...lama.butir, [butir.id_butir]: butir } });
}

export function salinanBeranda(simpanan: Simpanan | null): Beranda | null {
  return baca(simpanan)?.beranda ?? null;
}

export function salinanButir(simpanan: Simpanan | null, idButir: string): ButirLengkap | null {
  return baca(simpanan)?.butir[idButir] ?? null;
}

export function hapusSalinan(simpanan: Simpanan | null): void {
  if (simpanan === null) return;
  try {
    simpanan.removeItem(KUNCI);
  } catch {
    // Salinan yang tidak dapat dihapus hanya muncul lagi saat luring.
  }
}
