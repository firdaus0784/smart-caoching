/**
 * Layar S-09 Tanya — T-5 fitur 027, R-01 s.d. R-10.
 *
 * Kolaboratornya disuntikkan — pemanggil `fetch`, simpanan lokal, dan
 * penyalin — sehingga seluruh keadaan diuji tanpa peladen dan tanpa
 * peramban sungguhan (`plan.md` Bagian 6.1).
 *
 * Keadaan D-05 Bagian 7 yang berlaku bagi S-09: KL-A memuat, KL-B kosong
 * pertama kali, KL-D galat sistem, KL-E luring, dan KL-G tidak ditemukan —
 * yang terakhir **bukan** keadaan galat; ia jawaban sah yang ditampilkan
 * `BlokJawaban` yang sama (R-04). KL-C dan KL-F tidak berlaku (`spec.md`).
 */

import { useState, type FormEvent } from "react";

import { bacaDraf, hapusDraf, simpanDraf, type Simpanan } from "../draf";
import { tanya, type Pemanggil } from "../klien";
import type { JenisGalat, Tanggapan } from "../kontrak";
import { MIKROKOPI, PESAN_GALAT } from "../mikrokopi";
import { BlokJawaban } from "./BlokJawaban";

type Keadaan =
  | { readonly jenis: "kosong" }
  | { readonly jenis: "memuat" }
  | { readonly jenis: "jawaban"; readonly tanggapan: Tanggapan }
  | { readonly jenis: "galat"; readonly galat: JenisGalat; readonly tersimpan: boolean };

/** Galat yang pulih dengan mengirim ulang. Dua yang lain pulih dengan menulis
 * ulang pertanyaan atau tidak pulih dari layar ini, dan kalimatnya sudah
 * menyebut tindakannya. */
const DAPAT_DICOBA_LAGI: ReadonlySet<JenisGalat> = new Set<JenisGalat>(["luring", "sistem"]);

export interface PropertiLayarTanya {
  readonly pemanggil: Pemanggil;
  readonly simpanan: Simpanan | null;
  readonly salin: (teks: string) => Promise<void>;
}

export function LayarTanya({ pemanggil, simpanan, salin }: PropertiLayarTanya) {
  const [pertanyaan, setPertanyaan] = useState(() => bacaDraf(simpanan));
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "kosong" });

  function ubah(teks: string) {
    setPertanyaan(teks);
    simpanDraf(simpanan, teks);
  }

  async function ajukan() {
    const teks = pertanyaan.trim();
    if (teks === "" || keadaan.jenis === "memuat") return;
    setKeadaan({ jenis: "memuat" });
    const hasil = await tanya(teks, pemanggil);
    if (hasil.jenis === "jawaban") {
      hapusDraf(simpanan);
      setKeadaan({ jenis: "jawaban", tanggapan: hasil.tanggapan });
      return;
    }
    // R-09: draf ditulis ulang pada saat galat, dan "tersimpan" hanya
    // dinyatakan bila simpanan lokal memang menerimanya (M-6, M-14).
    const tersimpan = simpanDraf(simpanan, pertanyaan);
    setKeadaan({ jenis: "galat", galat: hasil.galat, tersimpan });
  }

  function kirim(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    void ajukan();
  }

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulLayar}</h1>

      <form className="isian-pertanyaan" onSubmit={kirim}>
        <label htmlFor="pertanyaan">{MIKROKOPI.labelPertanyaan}</label>
        <p id="petunjuk-pertanyaan">{MIKROKOPI.petunjukPertanyaan}</p>
        <textarea
          aria-describedby="petunjuk-pertanyaan"
          id="pertanyaan"
          onChange={(e) => ubah(e.target.value)}
          rows={3}
          value={pertanyaan}
        />
        <button disabled={keadaan.jenis === "memuat"} type="submit">
          {MIKROKOPI.tombolKirim}
        </button>
      </form>

      {keadaan.jenis === "kosong" && (
        <section className="kosong">
          <h2>{MIKROKOPI.kosongJudul}</h2>
          <p>{MIKROKOPI.kosongIsi}</p>
        </section>
      )}

      {keadaan.jenis === "memuat" && (
        <>
          <p className="tersembunyi" role="status">
            {MIKROKOPI.memuat}
          </p>
          <div aria-busy="true" className="kerangka" data-testid="kerangka-jawaban">
            <div className="kerangka-penanda" />
            <div className="kerangka-baris" />
            <div className="kerangka-baris" />
            <div className="kerangka-baris pendek" />
          </div>
        </>
      )}

      {keadaan.jenis === "galat" && (
        <div className="galat" role="alert">
          <p>
            {keadaan.tersimpan
              ? PESAN_GALAT[keadaan.galat].tersimpan
              : PESAN_GALAT[keadaan.galat].tidakTersimpan}
          </p>
          {DAPAT_DICOBA_LAGI.has(keadaan.galat) && (
            <button onClick={() => void ajukan()} type="button">
              {MIKROKOPI.tombolCobaLagi}
            </button>
          )}
        </div>
      )}

      {keadaan.jenis === "jawaban" && <BlokJawaban salin={salin} tanggapan={keadaan.tanggapan} />}
    </main>
  );
}
