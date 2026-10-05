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
 * profil null                 → S-03 → S-04 → S-09
 * selainnya                   → S-05 Beranda (fitur 013)
 * ```
 *
 * Sesudah aktivasi pertama pengguna tetap mendarat di S-09 (R-07 fitur 030);
 * pembukaan berikutnya mendarat di S-05 (D-05 0.6). Navigasi utama dua
 * tujuan — Beranda dan Tanya (K-7 fitur 013); "Milik saya" tampil ketika
 * isinya dibangun.
 *
 * Luring atau galat lain saat memeriksa tetap membuka Tanya (K-6): pengguna
 * masih dapat menulis draf (KL-E), dan aktivasi ditanyakan lagi lain kali.
 *
 * **Kurator dikenali tanpa rute baru (K-8 fitur 013).** Ringkasan akun hanya
 * terbuka bagi peran `pengguna`; 403 di sana diikuti `GET /kurasi/antrean`.
 * 200 membuka S-15; selainnya kalimat bahwa akun tidak dikenali, beserta
 * tombol keluar. Rute "siapa saya" tidak ditambahkan (AG-02).
 */

import { useEffect, useState } from "react";

import { LayarPengenalan } from "./aktivasi/LayarPengenalan";
import { LayarPersetujuan } from "./aktivasi/LayarPersetujuan";
import { LayarProfil } from "./aktivasi/LayarProfil";
import { hapusDraf, type Simpanan } from "./draf";
import { bacaAntrean, bacaRingkasan, keluar, muatNaskah, type Pemanggil } from "./klien";
import type { Antrean, HasilNaskah, KeadaanPersetujuan, Ringkasan } from "./kontrak";
import { LayarKurasi } from "./kurasi/LayarKurasi";
import { LayarMasuk } from "./masuk/LayarMasuk";
import { MIKROKOPI } from "./mikrokopi";
import { LayarBeranda } from "./penemuan/LayarBeranda";
import { LayarButir } from "./penemuan/LayarButir";
import { hapusSalinan } from "./penemuan/salinan";
import { lupakanPercakapan } from "./percakapan";
import { LayarTanya } from "./tanya/LayarTanya";

type Tahap =
  | { readonly jenis: "memeriksa" }
  | { readonly jenis: "masuk"; readonly pemberitahuan: string | null }
  | {
      readonly jenis: "persetujuan";
      readonly keadaan: KeadaanPersetujuan;
      readonly naskah: HasilNaskah;
      /** Dari mana S-02 dibuka: alur aktivasi, atau tautan pada layar utama. */
      readonly asal: "aktivasi" | "tanya" | "beranda";
      readonly profilAda: boolean;
    }
  | { readonly jenis: "pengenalan" }
  | { readonly jenis: "profil" }
  | { readonly jenis: "beranda" }
  | { readonly jenis: "butir"; readonly idButir: string }
  | { readonly jenis: "kurasi"; readonly antrean: Antrean }
  | { readonly jenis: "kurasi_galat"; readonly luring: boolean }
  | { readonly jenis: "tidak_dikenali" }
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
          asal: "aktivasi",
          profilAda: r.profil !== null,
        };
      }
    }
    return r.profil === null ? { jenis: "pengenalan" } : { jenis: "beranda" };
  }

  async function periksa(): Promise<Tahap> {
    const hasil = await bacaRingkasan(pemanggil);
    if (hasil.jenis === "ringkasan") return tahapDari(hasil.ringkasan);
    if (hasil.galat === "belum_masuk") return { jenis: "masuk", pemberitahuan: null };
    if (hasil.galat !== "tidak_berhak") return { jenis: "tanya" };
    // K-8: akun bukan pengguna — mungkin kurator.
    const antrean = await bacaAntrean(pemanggil);
    if (antrean.jenis === "antrean") return { jenis: "kurasi", antrean: antrean.antrean };
    if (antrean.jenis === "galat" && antrean.galat === "belum_masuk") {
      return { jenis: "masuk", pemberitahuan: null };
    }
    if (antrean.jenis === "galat" && (antrean.galat === "luring" || antrean.galat === "sistem")) {
      return { jenis: "kurasi_galat", luring: antrean.galat === "luring" };
    }
    return { jenis: "tidak_dikenali" };
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

  async function bukaPersetujuan(asal: "tanya" | "beranda") {
    const [hasil, naskah] = await Promise.all([bacaRingkasan(pemanggil), muatNaskah(pemanggil)]);
    if (hasil.jenis !== "ringkasan") return;
    setTahap({
      jenis: "persetujuan",
      keadaan: hasil.ringkasan.persetujuan,
      naskah,
      asal,
      profilAda: hasil.ringkasan.profil !== null,
    });
  }

  async function keluarkan() {
    await keluar(pemanggil);
    // K-6: peramban sekolah dapat dipakai bergantian — termasuk salinan
    // butir hari ini, yang memperlihatkan prioritas penggunanya (fitur 013).
    hapusDraf(simpanan);
    lupakanPercakapan(simpanan);
    hapusSalinan(simpanan);
    setTahap({ jenis: "masuk", pemberitahuan: null });
  }

  const perluMasuk = () => setTahap({ jenis: "masuk", pemberitahuan: MIKROKOPI.perluMasukLagiSaja });

  function navigasi(aktif: "beranda" | "tanya") {
    return (
      <nav aria-label={MIKROKOPI.labelNavigasi} className="navigasi">
        <button
          aria-current={aktif === "beranda" ? "page" : undefined}
          onClick={() => setTahap({ jenis: "beranda" })}
          type="button"
        >
          {MIKROKOPI.navBeranda}
        </button>
        <button
          aria-current={aktif === "tanya" ? "page" : undefined}
          onClick={() => setTahap({ jenis: "tanya" })}
          type="button"
        >
          {MIKROKOPI.navTanya}
        </button>
      </nav>
    );
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
        dariTanya={tahap.asal !== "aktivasi"}
        keadaan={tahap.keadaan}
        naskah={tahap.naskah}
        pemanggil={pemanggil}
        selesai={(r) => {
          // Menolak pun melanjutkan alur (FR-A05); dari layar utama, kembali ke sana.
          const profilAda = r === null ? tahap.profilAda : r.profil !== null;
          if (tahap.asal !== "aktivasi") setTahap({ jenis: tahap.asal });
          else setTahap(profilAda ? { jenis: "beranda" } : { jenis: "pengenalan" });
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
  if (tahap.jenis === "kurasi") {
    return (
      <LayarKurasi
        awal={tahap.antrean}
        belumMasuk={perluMasuk}
        keluar={() => void keluarkan()}
        pemanggil={pemanggil}
      />
    );
  }
  if (tahap.jenis === "kurasi_galat" || tahap.jenis === "tidak_dikenali") {
    return (
      <main className="layar-tanya">
        <div className="galat" role="alert">
          <p>
            {tahap.jenis === "tidak_dikenali"
              ? MIKROKOPI.akunTidakDikenali
              : tahap.luring
                ? MIKROKOPI.kurasiLuring
                : MIKROKOPI.kurasiGangguan}
          </p>
          {tahap.jenis === "kurasi_galat" && (
            <button onClick={() => void periksa().then(setTahap)} type="button">
              {MIKROKOPI.tombolCobaLagi}
            </button>
          )}
        </div>
        <button className="tombol-kedua" onClick={() => void keluarkan()} type="button">
          {MIKROKOPI.tombolKeluar}
        </button>
      </main>
    );
  }
  if (tahap.jenis === "beranda") {
    return (
      <>
        {navigasi("beranda")}
        <div className="kepala-layar">
          <button className="tombol-kedua" onClick={() => void keluarkan()} type="button">
            {MIKROKOPI.tombolKeluar}
          </button>
          <button className="tombol-kedua" onClick={() => void bukaPersetujuan("beranda")} type="button">
            {MIKROKOPI.tautanPersetujuan}
          </button>
        </div>
        <LayarBeranda
          belumMasuk={perluMasuk}
          buka={(idButir) => setTahap({ jenis: "butir", idButir })}
          keTanya={() => setTahap({ jenis: "tanya" })}
          pemanggil={pemanggil}
          simpanan={simpanan}
        />
      </>
    );
  }
  if (tahap.jenis === "butir") {
    return (
      <>
        {navigasi("beranda")}
        <LayarButir
          belumMasuk={perluMasuk}
          idButir={tahap.idButir}
          kembali={() => setTahap({ jenis: "beranda" })}
          key={tahap.idButir}
          pemanggil={pemanggil}
          simpanan={simpanan}
        />
      </>
    );
  }
  return (
    <>
    {navigasi("tanya")}
    <LayarTanya
      belumMasuk={(tersimpan) =>
        setTahap({
          jenis: "masuk",
          pemberitahuan: tersimpan ? MIKROKOPI.perluMasukLagi : MIKROKOPI.perluMasukLagiSaja,
        })
      }
      bukaPersetujuan={() => void bukaPersetujuan("tanya")}
      keluar={() => void keluarkan()}
      pemanggil={pemanggil}
      salin={salin}
      simpanan={simpanan}
    />
    </>
  );
}
