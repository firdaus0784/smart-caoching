import { describe, expect, test } from "vitest";

import type { Simpanan } from "./draf";
import { percakapanAktif, percakapanBaru } from "./percakapan";

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
    expect(percakapanAktif(simpananPeta())).toMatch(UUID_V4);
  });

  test("bertahan pada simpanan yang sama — percakapan berlanjut sesudah muat ulang", () => {
    const s = simpananPeta();
    expect(percakapanAktif(s)).toBe(percakapanAktif(s));
  });

  test("percakapan baru mengganti yang aktif", () => {
    const s = simpananPeta();
    const lama = percakapanAktif(s);
    const baru = percakapanBaru(s);
    expect(baru).not.toBe(lama);
    expect(baru).toMatch(UUID_V4);
    expect(percakapanAktif(s)).toBe(baru);
  });

  test("pengenal tersimpan yang bukan UUID v4 diganti, tidak dipakai", () => {
    const s = simpananPeta();
    s.setItem("smart-coaching:percakapan-aktif", "1");
    expect(percakapanAktif(s)).toMatch(UUID_V4);
  });

  test("simpanan yang menolak tidak menjatuhkan apa pun", () => {
    expect(percakapanAktif(menolak)).toMatch(UUID_V4);
    expect(percakapanAktif(null)).toMatch(UUID_V4);
  });
});
