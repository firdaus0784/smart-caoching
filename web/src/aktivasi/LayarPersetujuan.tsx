/**
 * Layar S-02 Persetujuan penelitian — T-5 fitur 030, FR-A05, C-04, P-1, P-5.
 *
 * Naskahnya dimuat dari berkas yang diisi tim dan ditampilkan apa adanya; kode
 * ini tidak memuat satu kalimat pun dari naskah ET-02. Versi yang dikirim
 * adalah versi berkas yang dimuat, sehingga peladen dapat menolak persetujuan
 * atas naskah yang tidak terpasang.
 *
 * "Saya setuju" dan "Saya tidak setuju" setara bentuknya: pilihan yang
 * ditonjolkan adalah tekanan, dan persetujuan di bawah tekanan bukan
 * persetujuan (RE-04).
 */

import { useState } from "react";

import { putuskanPersetujuan, type Pemanggil } from "../klien";
import type { HasilNaskah, KeadaanPersetujuan, Ringkasan } from "../kontrak";
import { MIKROKOPI } from "../mikrokopi";

export interface PropertiLayarPersetujuan {
  readonly pemanggil: Pemanggil;
  readonly keadaan: KeadaanPersetujuan;
  readonly naskah: HasilNaskah;
  /** `null` bila pengguna kembali tanpa memutus apa pun. */
  readonly selesai: (ringkasan: Ringkasan | null) => void;
  /** Dibuka dari layar Tanya: tombol Kembali tersedia. */
  readonly dariTanya: boolean;
}

export function LayarPersetujuan({
  pemanggil,
  keadaan,
  naskah,
  selesai,
  dariTanya,
}: PropertiLayarPersetujuan) {
  const [mengirim, setMengirim] = useState(false);
  const [gagal, setGagal] = useState(false);

  async function kirim(
    badan: { readonly versi_naskah: string; readonly disetujui: boolean } | { readonly cabut: true },
  ) {
    setMengirim(true);
    setGagal(false);
    const hasil = await putuskanPersetujuan(badan, pemanggil);
    setMengirim(false);
    if (hasil.jenis === "ringkasan") selesai(hasil.ringkasan);
    else setGagal(true);
  }

  const kembali = dariTanya && (
    <button className="tombol-kedua" onClick={() => selesai(null)} type="button">
      {MIKROKOPI.tombolKembali}
    </button>
  );

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulPersetujuan}</h1>

      {naskah.jenis === "belum_ada" ? (
        <p>{MIKROKOPI.naskahBelumAda}</p>
      ) : keadaan === "diberikan" ? (
        <>
          <p>{MIKROKOPI.sudahSetuju}</p>
          <button
            className="tombol-kedua"
            disabled={mengirim}
            onClick={() => void kirim({ cabut: true })}
            type="button"
          >
            {MIKROKOPI.tombolCabut}
          </button>
        </>
      ) : (
        <>
          <section className="naskah">
            <h2>{naskah.naskah.judul}</h2>
            {naskah.naskah.paragraf.map((isi, i) => (
              <p key={i}>{isi}</p>
            ))}
          </section>
          <p className="petunjuk">{MIKROKOPI.keteranganMenolak}</p>
          <div className="pilihan-setara">
            <button
              className="tombol-kedua"
              disabled={mengirim}
              onClick={() => void kirim({ versi_naskah: naskah.naskah.versi, disetujui: true })}
              type="button"
            >
              {MIKROKOPI.tombolSetuju}
            </button>
            <button
              className="tombol-kedua"
              disabled={mengirim}
              onClick={() => void kirim({ versi_naskah: naskah.naskah.versi, disetujui: false })}
              type="button"
            >
              {MIKROKOPI.tombolTidakSetuju}
            </button>
          </div>
        </>
      )}

      {gagal && (
        <div className="galat" role="alert">
          {MIKROKOPI.persetujuanGagal}
        </div>
      )}
      {kembali}
    </main>
  );
}
