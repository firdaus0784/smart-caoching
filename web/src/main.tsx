/**
 * Titik masuk peramban — satu-satunya tempat kolaborator sungguhan dipasang.
 *
 * Tanpa autentikasi tiruan, tanpa token, tanpa sandi (R-17): identitas
 * ditentukan backend. Permintaan memakai asal yang sama; pada pengembangan,
 * peladen Vite meneruskan `/api` ke `make jalan`.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import type { Simpanan } from "./draf";
import "./gaya.css";
import { LayarTanya } from "./tanya/LayarTanya";

// Cangkang luring (R-15). Pendaftaran yang ditolak — peramban tanpa dukungan,
// atau asal yang bukan `https` maupun `localhost` — tidak menjatuhkan layar;
// yang hilang hanya kemampuan terbuka tanpa koneksi.
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => undefined);
}

/** `localStorage` dapat melempar galat saat sekadar diakses — mode pribadi
 * sebagian peramban. Layar tetap berjalan tanpa draf, dan tidak menyatakan
 * apa pun tersimpan. */
function simpananPeramban(): Simpanan | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

async function salinKePapan(teks: string): Promise<void> {
  if (!navigator.clipboard) throw new TypeError();
  await navigator.clipboard.writeText(teks);
}

const akar = document.getElementById("akar");
if (akar !== null) {
  createRoot(akar).render(
    <StrictMode>
      <LayarTanya
        pemanggil={(jalur, init) => fetch(jalur, init)}
        salin={salinKePapan}
        simpanan={simpananPeramban()}
      />
    </StrictMode>,
  );
}
