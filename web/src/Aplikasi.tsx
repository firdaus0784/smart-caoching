/**
 * Cangkang aplikasi — T-8 fitur 029: S-01 Masuk atau S-09 Tanya.
 *
 * Saat dibuka, cangkang memanggil `GET /api/v1/percakapan` — rute yang sudah
 * ada — untuk mengetahui apakah sesinya sah. 401 membuka S-01; selainnya
 * membuka Tanya. Tidak ada rute "siapa saya" yang ditambahkan (AG-02).
 *
 * Luring saat dibuka tetap membuka Tanya: pengguna masih dapat menulis draf
 * (KL-E), dan bila sesinya ternyata tidak sah, pengiriman pertama yang
 * menjawab 401 membuka S-01 dengan draf yang tetap tersimpan.
 */

import { useEffect, useState } from "react";

import { hapusDraf, type Simpanan } from "./draf";
import { daftarPercakapan, keluar, type Pemanggil } from "./klien";
import { LayarMasuk } from "./masuk/LayarMasuk";
import { MIKROKOPI } from "./mikrokopi";
import { lupakanPercakapan } from "./percakapan";
import { LayarTanya } from "./tanya/LayarTanya";

type Tahap =
  | { readonly jenis: "memeriksa" }
  | { readonly jenis: "masuk"; readonly pemberitahuan: string | null }
  | { readonly jenis: "tanya" };

export interface PropertiAplikasi {
  readonly pemanggil: Pemanggil;
  readonly simpanan: Simpanan | null;
  readonly salin: (teks: string) => Promise<void>;
}

export function Aplikasi({ pemanggil, simpanan, salin }: PropertiAplikasi) {
  const [tahap, setTahap] = useState<Tahap>({ jenis: "memeriksa" });

  useEffect(() => {
    let berlaku = true;
    void daftarPercakapan(pemanggil).then((hasil) => {
      if (!berlaku) return;
      const belum = hasil.jenis === "galat" && hasil.galat === "belum_masuk";
      setTahap(belum ? { jenis: "masuk", pemberitahuan: null } : { jenis: "tanya" });
    });
    return () => {
      berlaku = false;
    };
  }, [pemanggil]);

  async function keluarkan() {
    await keluar(pemanggil);
    // K-6: peramban sekolah dapat dipakai bergantian.
    hapusDraf(simpanan);
    lupakanPercakapan(simpanan);
    setTahap({ jenis: "masuk", pemberitahuan: null });
  }

  if (tahap.jenis === "memeriksa") {
    return (
      <main className="layar-tanya">
        <p role="status">{MIKROKOPI.memeriksaAkun}</p>
      </main>
    );
  }
  if (tahap.jenis === "masuk") {
    return (
      <LayarMasuk
        berhasil={() => setTahap({ jenis: "tanya" })}
        pemanggil={pemanggil}
        pemberitahuan={tahap.pemberitahuan}
      />
    );
  }
  return (
    <LayarTanya
      belumMasuk={(tersimpan) =>
        setTahap({
          jenis: "masuk",
          pemberitahuan: tersimpan ? MIKROKOPI.perluMasukLagi : MIKROKOPI.perluMasukLagiSaja,
        })
      }
      keluar={() => void keluarkan()}
      pemanggil={pemanggil}
      salin={salin}
      simpanan={simpanan}
    />
  );
}
