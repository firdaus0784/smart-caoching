import { describe, expect, test } from "vitest";

import { bacaDraf, hapusDraf, simpanDraf, type Simpanan } from "./draf";

function simpananPeta(): Simpanan & { isi: Map<string, string> } {
  const isi = new Map<string, string>();
  return {
    isi,
    getItem: (k) => isi.get(k) ?? null,
    setItem: (k, v) => void isi.set(k, v),
    removeItem: (k) => void isi.delete(k),
  };
}

const menolak: Simpanan = {
  getItem: () => null,
  setItem: () => {
    throw new DOMException("kuota penuh", "QuotaExceededError");
  },
  removeItem: () => undefined,
};

const bisuDiam: Simpanan = {
  // Menerima tanpa galat, tetapi tidak menyimpan apa pun — mode pribadi
  // sebagian peramban berperilaku seperti ini.
  getItem: () => null,
  setItem: () => undefined,
  removeItem: () => undefined,
};

describe("simpanDraf", () => {
  test("mengembalikan benar hanya bila teksnya dapat dibaca kembali", () => {
    const s = simpananPeta();
    expect(simpanDraf(s, "Bagaimana menyusun jadwal?")).toBe(true);
    expect(bacaDraf(s)).toBe("Bagaimana menyusun jadwal?");
  });

  test("simpanan yang melempar galat menghasilkan salah, bukan galat", () => {
    expect(simpanDraf(menolak, "x")).toBe(false);
  });

  test("simpanan yang diam-diam tidak menyimpan menghasilkan salah", () => {
    expect(simpanDraf(bisuDiam, "x")).toBe(false);
  });

  test("tanpa simpanan sama sekali menghasilkan salah", () => {
    expect(simpanDraf(null, "x")).toBe(false);
  });

  test("teks kosong menghapus draf", () => {
    const s = simpananPeta();
    simpanDraf(s, "x");
    expect(simpanDraf(s, "")).toBe(true);
    expect(s.isi.size).toBe(0);
  });
});

describe("bacaDraf dan hapusDraf", () => {
  test("simpanan yang melempar galat dibaca sebagai kosong", () => {
    const rusak: Simpanan = {
      getItem: () => {
        throw new Error("akses ditolak");
      },
      setItem: () => undefined,
      removeItem: () => {
        throw new Error("akses ditolak");
      },
    };
    expect(bacaDraf(rusak)).toBe("");
    expect(() => hapusDraf(rusak)).not.toThrow();
  });

  test("tanpa simpanan dibaca sebagai kosong", () => {
    expect(bacaDraf(null)).toBe("");
  });
});
