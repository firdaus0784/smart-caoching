/**
 * Layar S-03 Pengenalan — T-5 fitur 030, FR-A04, K-8.
 *
 * Empat layar berurutan, satu gagasan per layar (AI-02). Tidak ada tombol
 * "lewati": layar kedua — sistem alat bantu, bukan penentu — adalah
 * satu-satunya isi yang FR-A04 wajibkan, dan jalan pintas yang melompatinya
 * membatalkan kewajiban itu (M-10).
 */

import { useState } from "react";

import { MIKROKOPI, PENGENALAN, langkahPengenalan } from "../mikrokopi";

export function LayarPengenalan({ selesai }: { readonly selesai: () => void }) {
  const [ke, setKe] = useState(0);
  const layar = PENGENALAN[ke];
  if (layar === undefined) return null;
  const terakhir = ke === PENGENALAN.length - 1;

  return (
    <main className="layar-tanya">
      <p className="petunjuk">{langkahPengenalan(ke + 1, PENGENALAN.length)}</p>
      <h1>{layar.judul}</h1>
      <p>{layar.isi}</p>
      <button onClick={() => (terakhir ? selesai() : setKe(ke + 1))} type="button">
        {terakhir ? MIKROKOPI.tombolMulaiProfil : MIKROKOPI.tombolLanjut}
      </button>
    </main>
  );
}
