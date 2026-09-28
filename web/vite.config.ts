// Konfigurasi Vite dan Vitest — fitur 027, ADR-09.
//
// Peladen pengembangan meneruskan `/api` ke `make jalan` (127.0.0.1:8000).
// Asal yang sama membuat CORS tidak dibutuhkan, dan CORS adalah perubahan
// backend yang R-16 larang (`plan.md` Bagian 1). `vite preview` memakai
// penerusan yang sama.
import react from "@vitejs/plugin-react";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

/**
 * CSP `index.html` menolak skrip sisipan, dan peladen pengembangan menyisipkan
 * satu — pembuka penyegaran React. Tanpa pelonggaran ini `vite` pada mesin
 * sendiri memuat layar kosong.
 *
 * Pelonggarannya hanya `'unsafe-inline'` pada `script-src`, hanya pada
 * `serve` — peladen yang mengikat 127.0.0.1 saja. Hasil `vite build` membawa
 * CSP apa adanya, dan `halaman.test.ts` memeriksa berkas sumbernya.
 */
function cspPengembangan(): Plugin {
  return {
    name: "csp-pengembangan",
    apply: "serve",
    transformIndexHtml: (html) =>
      html.replace("script-src 'self'", "script-src 'self' 'unsafe-inline'"),
  };
}

export default defineConfig({
  plugins: [react(), cspPengembangan()],
  server: {
    host: "127.0.0.1",
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    // Secara bawaan Vitest mengganti isi CSS dengan untai kosong — juga
    // `gaya.css?raw`. Uji kontras lalu memeriksa nol pasangan dan lulus;
    // ujinya sendiri yang menuntut pasangan > 0 yang menangkapnya (KB-132).
    css: { include: [/\.css(\?|$)/] },
  },
});
