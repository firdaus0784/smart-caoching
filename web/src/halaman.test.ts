/**
 * Sifat seluruh halaman — T-6 fitur 027, R-13, R-15, R-17, R-18.
 *
 * Yang diuji berkas sungguhan yang dikirim ke peramban, dibaca sebagai teks:
 * `gaya.css`, `index.html`, `public/sw.js`, dan seluruh sumber `web/src`.
 */

import { describe, expect, test } from "vitest";

import gaya from "./gaya.css?raw";
import indeks from "../index.html?raw";
import manifes from "../public/manifest.webmanifest?raw";
import teksSw from "../public/sw.js?raw";

const SUMBER = import.meta.glob<string>(["./**/*.{ts,tsx,css}", "!./**/*.test.{ts,tsx}"], {
  query: "?raw",
  import: "default",
  eager: true,
});

// ── AK-01 s.d. AK-03 · dihitung, bukan dilihat ─────────────────────────

const TOKEN = new Map(
  [...gaya.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map((m) => [m[1] ?? "", (m[2] ?? "").trim()]),
);

const BLOK = [...gaya.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map((m) => ({
  pemilih: (m[1] ?? "").trim(),
  isi: m[2] ?? "",
}));

function token(nama: string): string {
  const nilai = TOKEN.get(nama);
  if (nilai === undefined) throw new Error(`token ${nama} tidak ada`);
  return nilai;
}

function luminans(hex: string): number {
  const cocok = /^#([0-9a-f]{6})$/i.exec(hex);
  if (!cocok) throw new Error(`warna ${hex} bukan #rrggbb`);
  const [r, g, b] = [0, 2, 4].map((i) => {
    const c = parseInt((cocok[1] ?? "").slice(i, i + 2), 16) / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** WCAG 2.1 rumus 1.4.3. */
function kontras(a: string, b: string): number {
  const [terang, gelap] = [luminans(a), luminans(b)].sort((x, y) => y - x) as [number, number];
  return (terang + 0.05) / (gelap + 0.05);
}

function varPada(isi: string, sifat: RegExp): string | null {
  const cocok = new RegExp(`(?:^|;|\\s)${sifat.source}\\s*:\\s*var\\((--[\\w-]+)\\)`).exec(isi);
  return cocok?.[1] ?? null;
}

/** Pasangan huruf-latar yang **dipakai**: dibaca dari tiap blok aturan. */
function pasanganDipakai(): [string, string, string][] {
  const pasangan: [string, string, string][] = [];
  for (const { pemilih, isi } of BLOK) {
    if (pemilih.startsWith(":root")) continue;
    const huruf = varPada(isi, /color/);
    const latar = varPada(isi, /background(?:-color)?/);
    if (huruf !== null && latar !== null) pasangan.push([pemilih, huruf, latar]);
    else if (huruf !== null)
      for (const l of ["--latar-halaman", "--latar-permukaan"]) pasangan.push([pemilih, huruf, l]);
    else if (latar !== null) pasangan.push([pemilih, "--huruf-utama", latar]);
  }
  return pasangan;
}

function piksel(nilai: string): number {
  const cocok = /^([\d.]+)(px|rem)$/.exec(nilai);
  if (!cocok) throw new Error(`ukuran ${nilai} bukan px atau rem`);
  return Number(cocok[1]) * (cocok[2] === "rem" ? 16 : 1);
}

describe("aksesibilitas — D-05 Bagian 11", () => {
  test("pasangan huruf-latar yang dipakai ditemukan (bukan nol)", () => {
    expect(pasanganDipakai().length).toBeGreaterThanOrEqual(8);
  });

  test.each(pasanganDipakai())("AK-02 %s: %s di atas %s berkontras ≥ 4,5", (_, huruf, latar) => {
    expect(kontras(token(huruf), token(latar))).toBeGreaterThanOrEqual(4.5);
  });

  test("AK-01: huruf dasar ≥ 16px dan dipakai pada body", () => {
    expect(piksel(token("--ukuran-huruf-dasar"))).toBeGreaterThanOrEqual(16);
    const body = BLOK.find((b) => b.pemilih === "body");
    expect(varPada(body?.isi ?? "", /font-size/)).toBe("--ukuran-huruf-dasar");
  });

  test("AK-03: aturan dasar tombol, tautan, dan isian memakai sasaran ketuk ≥ 44px", () => {
    expect(piksel(token("--ukuran-ketuk"))).toBeGreaterThanOrEqual(44);
    for (const elemen of ["button", "a", "textarea"]) {
      const dasar = BLOK.find((b) => b.pemilih === elemen);
      expect(varPada(dasar?.isi ?? "", /min-height/), elemen).toBe("--ukuran-ketuk");
    }
  });

  test("AK-03: tidak ada aturan lain yang menimpa tinggi ketiganya dengan nilai lain", () => {
    const tersentuh = BLOK.filter((b) => /(^|[\s,>])(button|a|textarea)\b/.test(b.pemilih));
    expect(tersentuh.length).toBeGreaterThanOrEqual(5);
    for (const { pemilih, isi } of tersentuh) {
      for (const [, sifat, nilai] of isi.matchAll(/(?:^|;|\s)((?:min-|max-)?height)\s*:\s*([^;]+)/g)) {
        expect(`${sifat}: ${(nilai ?? "").trim()}`, pemilih).toBe(`${sifat}: var(--ukuran-ketuk)`);
      }
    }
  });

  test("AK-04: penanda dasar rujukan dibedakan warna hanya sebagai penguat teks", () => {
    for (const status of ["kuat", "terbatas", "tidak_ditemukan", "di_luar_domain"]) {
      expect(gaya).toContain(`.penanda[data-status="${status}"]`);
    }
  });
});

// ── R-18 · tanpa pihak ketiga ───────────────────────────────────────────

describe("tanpa pihak ketiga saat berjalan", () => {
  const csp = /<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"/.exec(indeks)?.[1];

  test("index.html memuat CSP yang membatasi seluruh sumber ke asal sendiri", () => {
    expect(csp).toBeDefined();
    const arahan = new Map(
      (csp ?? "").split(";").map((a) => {
        const [nama, ...nilai] = a.trim().split(/\s+/);
        return [nama ?? "", nilai.join(" ")];
      }),
    );
    expect(arahan.get("default-src")).toBe("'self'");
    expect(arahan.get("script-src")).toBe("'self'");
    expect(arahan.get("connect-src")).toBe("'self'");
    expect(arahan.get("object-src")).toBe("'none'");
    expect(csp).not.toMatch(/unsafe-inline|unsafe-eval|https?:|\*/);
  });

  test("index.html, manifes, service worker, dan gaya tanpa URL mutlak", () => {
    for (const [nama, isi] of [
      ["index.html", indeks],
      ["manifest.webmanifest", manifes],
      ["sw.js", teksSw],
      ["gaya.css", gaya],
    ] as const) {
      expect(isi, nama).not.toMatch(/(?:https?:)?\/\/[a-z0-9-]+\.[a-z]/i);
    }
    expect(gaya).not.toMatch(/@import|@font-face/);
  });

  test("sumber web/src tanpa URL mutlak", () => {
    expect(Object.keys(SUMBER).length).toBeGreaterThanOrEqual(8);
    for (const [berkas, isi] of Object.entries(SUMBER)) {
      expect(isi, berkas).not.toMatch(/https?:\/\/[a-z0-9-]+\.[a-z]/i);
    }
  });
});

// ── R-17 · tanpa autentikasi tiruan ─────────────────────────────────────

/** Komentar dibuang: komentar yang menyatakan "tanpa token" bukan token. */
function tanpaKomentar(isi: string): string {
  return isi.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
}

describe("tanpa artefak autentikasi", () => {
  test("tidak ada token, sandi, kuki, maupun tajuk otorisasi pada sumber", () => {
    for (const [berkas, isi] of Object.entries(SUMBER)) {
      expect(tanpaKomentar(isi), berkas).not.toMatch(
        /document\.cookie|sessionStorage|indexedDB|Authorization|\btoken\b|password|\bsandi\b/i,
      );
    }
  });

  test("simpanan lokal hanya ditulis draf.ts, dan hanya draf pertanyaan", () => {
    const menulis = Object.entries(SUMBER).filter(([, isi]) => /\.setItem\(/.test(isi));
    expect(menulis.map(([b]) => b)).toEqual(["./draf.ts"]);
    const kunci = [...(menulis[0]?.[1] ?? "").matchAll(/"(smart-coaching:[^"]+)"/g)].map((m) => m[1]);
    expect(kunci).toEqual(["smart-coaching:draf-tanya"]);
  });
});

// ── R-15 · cangkang luring ─────────────────────────────────────────────

interface Pekerja {
  keputusanTembolok: (url: string, metode: string, asal: string) => string;
}

function muatSw(): Pekerja {
  const diri: Record<string, unknown> = {
    addEventListener: () => undefined,
    location: { origin: "https://sekolah.contoh" },
  };
  new Function("self", teksSw)(diri);
  return diri as unknown as Pekerja;
}

describe("keputusan tembolok service worker", () => {
  const { keputusanTembolok } = muatSw();
  const ASAL = "https://sekolah.contoh";

  test.each([
    ["/", "GET"],
    ["/index.html", "GET"],
    ["/assets/index-abc.js", "GET"],
    ["/assets/index-abc.css", "GET"],
    ["/manifest.webmanifest", "GET"],
  ])("cangkang %s %s: jaringan dulu, tembolok bila luring", (jalur, metode) => {
    expect(keputusanTembolok(ASAL + jalur, metode, ASAL)).toBe("jaringan-lalu-tembolok");
  });

  test.each([
    ["/api/v1/tanya", "POST"],
    ["/api/v1/tanya", "GET"],
    ["/api/v1/percakapan", "GET"],
    ["/api/v1/percakapan/abc", "GET"],
    ["/api", "GET"],
  ])("%s %s: tidak pernah ditembolok (C-07)", (jalur, metode) => {
    expect(keputusanTembolok(ASAL + jalur, metode, ASAL)).toBe("lewati");
  });

  test("permintaan selain GET dan asal lain tidak ditembolok", () => {
    expect(keputusanTembolok(`${ASAL}/`, "POST", ASAL)).toBe("lewati");
    expect(keputusanTembolok("https://lain.contoh/a.js", "GET", ASAL)).toBe("lewati");
  });

  test("jalur yang menyamar sebagai cangkang di bawah /api tetap dilewati", () => {
    expect(keputusanTembolok(`${ASAL}/api/../api/v1/tanya`, "GET", ASAL)).toBe("lewati");
    expect(keputusanTembolok(`${ASAL}/API/v1/tanya`, "GET", ASAL)).toBe("lewati");
  });
});

// ── Manifes ─────────────────────────────────────────────────────────────

test("manifes berbahasa Indonesia dan membuka layar Tanya", () => {
  const isi = JSON.parse(manifes) as Record<string, unknown>;
  expect(isi["lang"]).toBe("id");
  expect(isi["start_url"]).toBe("/");
  expect(isi["display"]).toBe("standalone");
});

test("index.html memasang manifes dan berbahasa Indonesia", () => {
  expect(indeks).toMatch(/<html lang="id">/);
  expect(indeks).toMatch(/<link rel="manifest" href="\/manifest\.webmanifest"/);
});
