/**
 * Layar S-16 Penyuntingan butir — T-8 fitur 013, FR-I02, KL-03.
 *
 * Hanya **empat bidang parafrase** yang dapat disunting: judul, kalimat
 * "mengapa relevan", inti temuan, implikasi tindakan (D-06 Bagian 7.3).
 * Lisensi, sumber, kategori, dan jenis sumber tampil tanpa isian — menggantinya
 * mengubah butir, bukan parafrasenya, dan peladen menolaknya (M-11).
 */

import { useState, type FormEvent } from "react";

import type { BadanPutusan } from "../klien";
import type { KandidatTampil } from "../kontrak";
import {
  LABEL_JENIS_SUMBER,
  LABEL_KATEGORI,
  MIKROKOPI,
  barisSumber,
  jenisDanKategori,
  keteranganKurasi,
} from "../mikrokopi";

export function LayarSunting({
  kandidat,
  kirim,
  batal,
}: {
  readonly kandidat: KandidatTampil;
  readonly kirim: (badan: BadanPutusan) => Promise<boolean>;
  readonly batal: () => void;
}) {
  const [judul, setJudul] = useState(kandidat.judul);
  const [alasan, setAlasan] = useState(kandidat.alasan_relevansi);
  const [inti, setInti] = useState(kandidat.inti_temuan);
  const [implikasi, setImplikasi] = useState(kandidat.implikasi_tindakan.join("\n"));
  const [catatan, setCatatan] = useState("");
  const [kurang, setKurang] = useState(false);

  async function simpan(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    const daftar = implikasi
      .split("\n")
      .map((baris) => baris.trim())
      .filter((baris) => baris !== "");
    if (catatan.trim() === "" || daftar.length === 0) {
      setKurang(true);
      return;
    }
    await kirim({
      jenis: "sunting_lalu_setujui",
      catatan,
      suntingan: { judul, alasan_relevansi: alasan, inti_temuan: inti, implikasi_tindakan: daftar },
    });
  }

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulSunting}</h1>
      <form className="isian-pertanyaan" onSubmit={(e) => void simpan(e)}>
        <label htmlFor="sunting-judul">{MIKROKOPI.labelJudul}</label>
        <input id="sunting-judul" onChange={(e) => setJudul(e.target.value)} value={judul} />
        <label htmlFor="sunting-alasan">{MIKROKOPI.labelAlasanRelevansi}</label>
        <textarea id="sunting-alasan" onChange={(e) => setAlasan(e.target.value)} rows={2} value={alasan} />
        <label htmlFor="sunting-inti">{MIKROKOPI.labelIntiTemuan}</label>
        <textarea id="sunting-inti" onChange={(e) => setInti(e.target.value)} rows={4} value={inti} />
        <label htmlFor="sunting-implikasi">{MIKROKOPI.labelImplikasi}</label>
        <textarea
          id="sunting-implikasi"
          onChange={(e) => setImplikasi(e.target.value)}
          rows={3}
          value={implikasi}
        />
        <section className="keterangan">
          <p>{MIKROKOPI.keteranganTetap}</p>
          <p>{jenisDanKategori(LABEL_JENIS_SUMBER[kandidat.jenis_sumber], LABEL_KATEGORI[kandidat.kategori])}</p>
          <p>{keteranganKurasi(kandidat.lisensi, null)}</p>
          <p>{barisSumber(kandidat.sumber.judul, kandidat.sumber.penerbit, kandidat.sumber.tahun)}</p>
        </section>
        <label htmlFor="sunting-catatan">{MIKROKOPI.labelCatatan}</label>
        <textarea id="sunting-catatan" onChange={(e) => setCatatan(e.target.value)} rows={2} value={catatan} />
        {kurang && (
          <p className="galat" role="alert">
            {MIKROKOPI.putusanBelumLengkap}
          </p>
        )}
        <div className="tindakan">
          <button type="submit">{MIKROKOPI.tombolSimpanSetujui}</button>
          <button className="tombol-kedua" onClick={batal} type="button">
            {MIKROKOPI.tombolBatal}
          </button>
        </div>
      </form>
    </main>
  );
}
