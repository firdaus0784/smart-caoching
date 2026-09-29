/**
 * Blok 9 dan 10 D-05 S-09 — T-7 fitur 028, R-09, K-2.
 *
 * Keduanya menampilkan **pertanyaan**, tidak pernah jawaban: jawaban yang
 * tersimpan menua, dan menampilkannya ulang melanggar C-07. Mengetuk
 * pertanyaan mengisi isian; pengguna yang memutuskan mengirimnya.
 */

import { useState } from "react";

import { bacaPercakapan, daftarPercakapan, type Pemanggil } from "../klien";
import type { Giliran } from "../kontrak";
import { MIKROKOPI } from "../mikrokopi";

/** K-2: bentuk daftar D-14 tidak diubah; paling banyak sepuluh dibaca. */
const TERDAHULU_MAKSIMUM = 10;

export function PertanyaanSebelumnya({
  giliran,
  pilih,
}: {
  readonly giliran: readonly Giliran[];
  readonly pilih: (pertanyaan: string) => void;
}) {
  if (giliran.length === 0) return null;
  return (
    <section className="riwayat" data-testid="pertanyaan-sebelumnya">
      <h2>{MIKROKOPI.judulPertanyaanSebelumnya}</h2>
      <p className="keterangan">{MIKROKOPI.keteranganPertanyaanSebelumnya}</p>
      <ul className="daftar-riwayat">
        {giliran.map((g) => (
          <li key={g.id_pesan}>
            <button className="butir-riwayat" onClick={() => pilih(g.pertanyaan)} type="button">
              {g.pertanyaan}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

type KeadaanTerdahulu =
  | { readonly jenis: "tertutup" }
  | { readonly jenis: "memuat" }
  | { readonly jenis: "tidak_termuat" }
  | { readonly jenis: "siap"; readonly butir: readonly { id: string; pertanyaan: string }[] };

export function PercakapanTerdahulu({
  pemanggil,
  aktif,
  buka,
}: {
  readonly pemanggil: Pemanggil;
  readonly aktif: string;
  readonly buka: (id: string) => void;
}) {
  const [keadaan, setKeadaan] = useState<KeadaanTerdahulu>({ jenis: "tertutup" });

  async function tampilkan() {
    setKeadaan({ jenis: "memuat" });
    const daftar = await daftarPercakapan(pemanggil);
    if (daftar.jenis === "galat") {
      setKeadaan({ jenis: "tidak_termuat" });
      return;
    }
    const pilihan = daftar.percakapan.filter((id) => id !== aktif).slice(0, TERDAHULU_MAKSIMUM);
    const dibaca = await Promise.all(pilihan.map((id) => bacaPercakapan(id, pemanggil)));
    const butir = dibaca.flatMap((h) =>
      h.jenis === "percakapan" && h.percakapan.giliran[0] !== undefined
        ? [{ id: h.percakapan.id_percakapan, pertanyaan: h.percakapan.giliran[0].pertanyaan }]
        : [],
    );
    setKeadaan({ jenis: "siap", butir });
  }

  if (keadaan.jenis === "tertutup") {
    return (
      <button className="tombol-kedua" onClick={() => void tampilkan()} type="button">
        {MIKROKOPI.tombolTampilkanTerdahulu}
      </button>
    );
  }
  return (
    <section aria-busy={keadaan.jenis === "memuat"} className="riwayat" data-testid="percakapan-terdahulu">
      <h2>{MIKROKOPI.judulPercakapanTerdahulu}</h2>
      {keadaan.jenis === "tidak_termuat" && <p>{MIKROKOPI.terdahuluTidakTermuat}</p>}
      {keadaan.jenis === "siap" && keadaan.butir.length === 0 && <p>{MIKROKOPI.terdahuluKosong}</p>}
      {keadaan.jenis === "siap" && keadaan.butir.length > 0 && (
        <ul className="daftar-riwayat">
          {keadaan.butir.map((b) => (
            <li key={b.id}>
              <button className="butir-riwayat" onClick={() => buka(b.id)} type="button">
                {b.pertanyaan}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
