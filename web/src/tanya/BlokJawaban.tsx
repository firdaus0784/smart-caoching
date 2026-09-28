/**
 * Blok jawaban berlapis — D-05 S-09, PK-02, R-02 s.d. R-07.
 *
 * SATU komponen bagi keempat nilai `status_dasar` (R-04): `tidak_ditemukan`
 * dan `di_luar_domain` memakai susunan yang sama, hanya isinya berbeda. Dua
 * komponen akan berbeda susunannya pada hari salah satunya disunting.
 *
 * Urutan blok tetap: penanda dasar rujukan → ringkasan → penjelasan →
 * catatan keberlakuan → dasar rujukan → bacaan lanjutan → tindakan →
 * penafian. Penanda **sebelum** isi: pengguna berhak tahu seberapa kuat
 * dasarnya sebelum membaca, bukan sesudah terlanjur mempercayainya.
 *
 * `klaim` dan `versi` diterima tetapi tidak ditampilkan — D-05 S-09 tidak
 * memintanya, dan arti `peringkat_kepercayaan` belum diputus (TK-40).
 */

import { useState } from "react";

import type { Tanggapan } from "../kontrak";
import { barisSitasi, MIKROKOPI, PENANDA_DASAR, teksPengganti } from "../mikrokopi";

/** D-07 Bagian 5.1, FR-F05. Peladen sudah menjaganya; lapisan kedua di sini. */
const BUTIR_RINGKASAN_MAKSIMUM = 3;

type KeadaanSalin = "diam" | "berhasil" | "tidak_bisa";

/** Tautan dari tanggapan hanya dipasang bila berskema web. Skema lain —
 * `javascript:` terutama — tidak pernah menjadi tautan yang dapat diketuk. */
function tautanAman(tautan: string | null): string | null {
  return tautan !== null && /^https?:\/\//i.test(tautan) ? tautan : null;
}

export interface PropertiBlokJawaban {
  readonly tanggapan: Tanggapan;
  readonly salin: (teks: string) => Promise<void>;
}

export function BlokJawaban({ tanggapan, salin }: PropertiBlokJawaban) {
  const [keadaanSalin, setKeadaanSalin] = useState<KeadaanSalin>("diam");

  const ringkasan = tanggapan.ringkasan_tindakan.slice(0, BUTIR_RINGKASAN_MAKSIMUM);
  const penjelasan =
    tanggapan.status_dasar === "tidak_ditemukan" && tanggapan.penjelasan.trim() === ""
      ? MIKROKOPI.tidakDitemukanPenjelasan
      : tanggapan.penjelasan;

  async function salinRingkasan() {
    try {
      await salin(ringkasan.join("\n"));
      setKeadaanSalin("berhasil");
    } catch {
      setKeadaanSalin("tidak_bisa");
    }
  }

  return (
    <article className="blok-jawaban" data-testid="blok-jawaban">
      <p className="penanda" data-status={tanggapan.status_dasar} data-testid="penanda-dasar">
        {PENANDA_DASAR[tanggapan.status_dasar]}
      </p>

      {ringkasan.length > 0 && (
        <section>
          <h2>{MIKROKOPI.judulRingkasan}</h2>
          <ol data-testid="ringkasan">
            {ringkasan.map((butir, i) => (
              <li key={i}>{butir}</li>
            ))}
          </ol>
        </section>
      )}

      {penjelasan !== "" && (
        <section>
          <h2>{MIKROKOPI.judulPenjelasan}</h2>
          <p>{penjelasan}</p>
        </section>
      )}

      {tanggapan.catatan_keberlakuan !== "" && (
        <section className="catatan-keberlakuan">
          <h2>{MIKROKOPI.judulCatatanKeberlakuan}</h2>
          <p>{tanggapan.catatan_keberlakuan}</p>
        </section>
      )}

      {tanggapan.sitasi.length > 0 && (
        <section data-testid="dasar-rujukan">
          <h2>{MIKROKOPI.judulDasarRujukan}</h2>
          <ul className="daftar-sitasi">
            {tanggapan.sitasi.map((s) => {
              const tautan = tautanAman(s.tautan);
              return (
                <li className="sitasi" key={`${s.id_dokumen}/${s.bagian}`}>
                  <span>{barisSitasi(s.judul, s.penerbit, s.tahun, s.bagian)}</span>
                  {s.status_keberlakuan !== "berlaku" && (
                    <span className="penanda-keberlakuan">{MIKROKOPI.penandaDiubah}</span>
                  )}
                  {s.rujukan_pengganti !== null && (
                    <span>{teksPengganti(s.rujukan_pengganti)}</span>
                  )}
                  {tautan !== null && (
                    <a href={tautan} rel="noreferrer" target="_blank">
                      {MIKROKOPI.bukaSumber}
                    </a>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {tanggapan.bacaan_lanjutan.length > 0 && (
        <section data-testid="bacaan-lanjutan">
          <h2>{MIKROKOPI.judulBacaanLanjutan}</h2>
          <p>{MIKROKOPI.keteranganBacaanLanjutan}</p>
          <ul>
            {tanggapan.bacaan_lanjutan.map((b) => {
              const tautan = tautanAman(b.tautan);
              return (
                <li key={b.tautan}>
                  {tautan !== null ? <a href={tautan}>{b.judul}</a> : b.judul}
                </li>
              );
            })}
          </ul>
        </section>
      )}

      {ringkasan.length > 0 && (
        <div className="tindakan">
          <button onClick={() => void salinRingkasan()} type="button">
            {MIKROKOPI.tombolSalinRingkasan}
          </button>
          {keadaanSalin === "berhasil" && <p role="status">{MIKROKOPI.salinBerhasil}</p>}
          {keadaanSalin === "tidak_bisa" && <p role="status">{MIKROKOPI.salinTidakBisa}</p>}
        </div>
      )}

      <p className="penafian">{tanggapan.penafian}</p>
    </article>
  );
}
