// Konfigurasi Vite dan Vitest — fitur 027, ADR-09.
//
// Peladen pengembangan meneruskan `/api` ke `make jalan` (127.0.0.1:8000).
// Asal yang sama membuat CORS tidak dibutuhkan, dan CORS adalah perubahan
// backend yang R-16 larang (`plan.md` Bagian 1).
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
