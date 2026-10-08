/**
 * Cangkang kurator — dua tombol setara, "Antrean kurasi" dan "Aduan jawaban"
 * (D-05 S-17, fitur 036). Bukan navigasi pengguna: kurator tidak melihat
 * beranda maupun Tanya, sama dengan cangkang fitur 013 (K-8).
 *
 * Kembali ke antrean memuatnya ulang: antrean yang dibuka pagi hari tidak
 * boleh menjadi dasar putusan sore hari.
 */

import { useState } from "react";

import { bacaAntrean, type Pemanggil } from "../klien";
import type { Antrean } from "../kontrak";
import { MIKROKOPI } from "../mikrokopi";
import { LayarAduan } from "./LayarAduan";
import { LayarKurasi } from "./LayarKurasi";

export function CangkangKurator({
  awal,
  pemanggil,
  keluar,
  belumMasuk,
}: {
  readonly awal: Antrean;
  readonly pemanggil: Pemanggil;
  readonly keluar: () => void;
  readonly belumMasuk: () => void;
}) {
  const [tampil, setTampil] = useState<"antrean" | "aduan">("antrean");
  const [antrean, setAntrean] = useState<Antrean>(awal);

  async function keAntrean(): Promise<void> {
    const hasil = await bacaAntrean(pemanggil);
    if (hasil.jenis === "antrean") setAntrean(hasil.antrean);
    if (hasil.jenis === "galat" && hasil.galat === "belum_masuk") {
      belumMasuk();
      return;
    }
    setTampil("antrean");
  }

  return (
    <>
      <div className="pilihan-kurator">
        <button
          aria-pressed={tampil === "antrean"}
          onClick={() => void keAntrean()}
          type="button"
        >
          {MIKROKOPI.tombolAntreanKurasi}
        </button>
        <button
          aria-pressed={tampil === "aduan"}
          onClick={() => setTampil("aduan")}
          type="button"
        >
          {MIKROKOPI.tombolAduanJawaban}
        </button>
      </div>
      {tampil === "antrean" ? (
        <LayarKurasi
          awal={antrean}
          belumMasuk={belumMasuk}
          key={JSON.stringify(antrean)}
          keluar={keluar}
          pemanggil={pemanggil}
        />
      ) : (
        <LayarAduan
          belumMasuk={belumMasuk}
          keluar={keluar}
          pemanggil={pemanggil}
        />
      )}
    </>
  );
}
