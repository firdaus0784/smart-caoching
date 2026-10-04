/**
 * Cangkang aplikasi — fitur 029 dan 030: S-01, alur aktivasi J1, S-09.
 *
 * Saat dibuka, dan sesudah masuk, cangkang membaca ringkasan aktivasi
 * `GET /api/v1/saya/profil` (D-14 Bagian 4.5, K-5) — satu rute yang menjawab
 * tiga hal sekaligus: sesinya sah, persetujuan sudah ditanya, profil sudah
 * ada. Tidak ada rute "siapa saya" maupun "status aktivasi" yang ditambahkan
 * (AG-02).
 *
 * ```
 * 401                         → S-01
 * persetujuan belum_diminta   → S-02 (dilewati bila naskah belum tersedia)
 * profil null                 → S-03 → S-04
 * selainnya                   → S-09
 * ```
 *
 * Luring atau galat lain saat memeriksa tetap membuka Tanya (K-6): pengguna
 * masih dapat menulis draf (KL-E), dan aktivasi ditanyakan lagi lain kali.
 */

import { useEffect, useState } from "react";

import { LayarPengenalan } from "./aktivasi/LayarPengenalan";
import { LayarPersetujuan } from "./aktivasi/LayarPersetujuan";
import { LayarProfil } from "./aktivasi/LayarProfil";
import { hapusDraf, type Simpanan } from "./draf";
import { bacaRingkasan, keluar, muatNaskah, type Pemanggil } from "./klien";
import type { HasilNaskah, KeadaanPersetujuan, Ringkasan } from "./kontrak";
import { LayarMasuk } from "./masuk/LayarMasuk";
import { MIKROKOPI } from "./mikrokopi";
import { lupakanPercakapan } from "./percakapan";
import { LayarTanya } from "./tanya/LayarTanya";

type Tahap =
  | { readonly jenis: "memeriksa" }
  | { readonly jenis: "masuk"; readonly pemberitahuan: string | null }
  | {
      readonly jenis: "persetujuan";
      readonly keadaan: KeadaanPersetujuan;
      readonly naskah: HasilNaskah;
      readonly dariTanya: boolean;
      readonly profilAda: boolean;
    }
  | { readonly jenis: "pengenalan" }
  | { readonly jenis: "profil" }
  | { readonly jenis: "tanya" };

export interface PropertiAplikasi {
  readonly pemanggil: Pemanggil;
  readonly simpanan: Simpanan | null;
  readonly salin: (teks: string) => Promise<void>;
}

export function Aplikasi({ pemanggil, simpanan, salin }: PropertiAplikasi) {
  const [tahap, setTahap] = useState<Tahap>({ jenis: "memeriksa" });

  // Tahap sesudah ringkasan dibaca — urutan D-05 Bagian 5.1.
  async function tahapDari(r: Ringkasan): Promise<Tahap> {
    if (r.persetujuan === "belum_diminta") {
      const naskah = await muatNaskah(pemanggil);
      if (naskah.jenis === "naskah") {
        return {
          jenis: "persetujuan",
          keadaan: r.persetujuan,
          naskah,
          dariTanya: false,
          profilAda: r.profil !== null,
        };
      }
    }
    return r.profil === null ? { jenis: "pengenalan" } : { jenis: "tanya" };
  }

  async function periksa(): Promise<Tahap> {
    const hasil = await bacaRingkasan(pemanggil);
    if (hasil.jenis === "ringkasan") return tahapDari(hasil.ringkasan);
    return hasil.galat === "belum_masuk" ? { jenis: "masuk", pemberitahuan: null } : { jenis: "tanya" };
  }

  useEffect(() => {
    let berlaku = true;
    void periksa().then((berikut) => {
      if (berlaku) setTahap(berikut);
    });
    return () => {
      berlaku = false;
    };
    // `periksa` dibentuk ulang tiap render; yang menentukan hanya pemanggil.
  }, [pemanggil]);

  async function bukaPersetujuan() {
    const [hasil, naskah] = await Promise.all([bacaRingkasan(pemanggil), muatNaskah(pemanggil)]);
    if (hasil.jenis !== "ringkasan") return;
    setTahap({
      jenis: "persetujuan",
      keadaan: hasil.ringkasan.persetujuan,
      naskah,
      dariTanya: true,
      profilAda: hasil.ringkasan.profil !== null,
    });
  }

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
        berhasil={() => void periksa().then(setTahap)}
        pemanggil={pemanggil}
        pemberitahuan={tahap.pemberitahuan}
      />
    );
  }
  if (tahap.jenis === "persetujuan") {
    return (
      <LayarPersetujuan
        dariTanya={tahap.dariTanya}
        keadaan={tahap.keadaan}
        naskah={tahap.naskah}
        pemanggil={pemanggil}
        selesai={(r) => {
          // Menolak pun melanjutkan alur (FR-A05); dari Tanya, kembali ke Tanya.
          const profilAda = r === null ? tahap.profilAda : r.profil !== null;
          setTahap(tahap.dariTanya || profilAda ? { jenis: "tanya" } : { jenis: "pengenalan" });
        }}
      />
    );
  }
  if (tahap.jenis === "pengenalan") {
    return <LayarPengenalan selesai={() => setTahap({ jenis: "profil" })} />;
  }
  if (tahap.jenis === "profil") {
    return <LayarProfil pemanggil={pemanggil} selesai={() => setTahap({ jenis: "tanya" })} />;
  }
  return (
    <LayarTanya
      belumMasuk={(tersimpan) =>
        setTahap({
          jenis: "masuk",
          pemberitahuan: tersimpan ? MIKROKOPI.perluMasukLagi : MIKROKOPI.perluMasukLagiSaja,
        })
      }
      bukaPersetujuan={() => void bukaPersetujuan()}
      keluar={() => void keluarkan()}
      pemanggil={pemanggil}
      salin={salin}
      simpanan={simpanan}
    />
  );
}
