import { describe, expect, test } from "vitest";

import type { Simpanan } from "./draf";
import { percakapanAktif, percakapanBaru, tandaiDikenal } from "./percakapan";

const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

function simpananPeta(): Simpanan {
  const isi = new Map<string, string>();
  return {
    getItem: (k) => isi.get(k) ?? null,
    setItem: (k, v) => void isi.set(k, v),
    removeItem: (k) => void isi.delete(k),
  };
}

const menolak: Simpanan = {
  getItem: () => {
    throw new Error("akses ditolak");
  },
  setItem: () => {
    throw new Error("akses ditolak");
  },
  removeItem: () => undefined,
};

describe("pengenal percakapan aktif — R-09, R-16", () => {
  test("dibangkitkan sebagai UUID versi 4", () => {
    expect(percakapanAktif(simpananPeta()).id).toMatch(UUID_V4);
  });

  test("bertahan pada simpanan yang sama — percakapan berlanjut sesudah muat ulang", () => {
    const s = simpananPeta();
    const pertama = percakapanAktif(s);
    const kedua = percakapanAktif(s);
    expect(kedua.id).toBe(pertama.id);
    expect(pertama.baru).toBe(true);
    // KB-174: sebelum jawaban pertamanya, percakapan tetap **baru** sesudah
    // muat ulang. Harapan semula `false` membuat layar meminta riwayat yang
    // peladen belum kenal — 404 yang KB-147 larang, tersingkap bukti fitur 030.
    expect(kedua.baru).toBe(true);
  });

  test("sesudah ditandai dikenal, muat ulang membaca riwayatnya", () => {
    const s = simpananPeta();
    const { id } = percakapanAktif(s);
    tandaiDikenal(s, id);
    expect(percakapanAktif(s)).toEqual({ id, baru: false });
  });

  test("menandai pengenal lain tidak mengubah yang aktif", () => {
    const s = simpananPeta();
    const { id } = percakapanAktif(s);
    tandaiDikenal(s, "3f1c9a2e-7b4d-4c1e-9a0f-2d6b8e5c1a47");
    expect(percakapanAktif(s)).toEqual({ id, baru: true });
  });

  test("percakapan baru mengganti yang aktif", () => {
    const s = simpananPeta();
    const lama = percakapanAktif(s).id;
    const baru = percakapanBaru(s);
    expect(baru).not.toBe(lama);
    expect(baru).toMatch(UUID_V4);
    expect(percakapanAktif(s)).toEqual({ id: baru, baru: true });
  });

  test("pengenal tersimpan yang bukan UUID v4 diganti, tidak dipakai", () => {
    const s = simpananPeta();
    s.setItem("smart-coaching:percakapan-aktif", "1");
    const aktif = percakapanAktif(s);
    expect(aktif.id).toMatch(UUID_V4);
    expect(aktif.baru).toBe(true);
  });

  test("simpanan yang menolak tidak menjatuhkan apa pun", () => {
    expect(percakapanAktif(menolak).id).toMatch(UUID_V4);
    expect(percakapanAktif(null).id).toMatch(UUID_V4);
  });
});
