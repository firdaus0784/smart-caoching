/**
 * Layar S-11 Koleksi tersimpan — T-7 fitur 032, FR-G06, FR-G10, P-4 A; D-05 S-11.
 *
 * Tujuan "Milik saya" (R-10). Dua penyaring — kategori dan jenis sumber —
 * dikirim kepada peladen sebagai kueri; layar tidak menyaring sendiri.
 *
 * Isi kartu berurutan tetap: **penanda dasar berubah** bila ada, label jenis
 * sumber dan judul, catatan, inti temuan dan implikasi, sumber, lalu
 * "Keluarkan dari koleksi". Penanda mendahului isi agar butir yang ditarik
 * tidak terbaca sebagai dasar yang masih berlaku (D-06 Bagian 7.5).
 *
 * Tanpa poin, lencana, maupun hitungan koleksi (C-15).
 */

import { useEffect, useState } from "react";

import { bacaKoleksi, keluarkanDariKoleksi, type Pemanggil } from "../klien";
import type {
  ButirKoleksi,
  JenisSumberButir,
  KategoriMasalah,
} from "../kontrak";
import {
  LABEL_JENIS_SUMBER,
  LABEL_KATEGORI,
  MIKROKOPI,
  barisSumber,
} from "../mikrokopi";

type Keadaan =
  | { readonly jenis: "memuat" }
  | { readonly jenis: "koleksi"; readonly koleksi: readonly ButirKoleksi[] }
  | { readonly jenis: "luring" }
  | { readonly jenis: "gangguan" };

const KATEGORI = Object.keys(LABEL_KATEGORI) as KategoriMasalah[];
const JENIS = Object.keys(LABEL_JENIS_SUMBER) as JenisSumberButir[];

export function LayarKoleksi({
  pemanggil,
  belumMasuk,
}: {
  readonly pemanggil: Pemanggil;
  readonly belumMasuk: () => void;
}) {
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "memuat" });
  const [kategori, setKategori] = useState<KategoriMasalah | "">("");
  const [jenis, setJenis] = useState<JenisSumberButir | "">("");
  const [percobaan, setPercobaan] = useState(0);
  const [pesan, setPesan] = useState<string | null>(null);

  useEffect(() => {
    let berlaku = true;
    const penyaring = {
      ...(kategori === "" ? {} : { kategori }),
      ...(jenis === "" ? {} : { jenis_sumber: jenis }),
    };
    void bacaKoleksi(pemanggil, penyaring).then((hasil) => {
      if (!berlaku) return;
      if (hasil.jenis === "koleksi")
        setKeadaan({ jenis: "koleksi", koleksi: hasil.koleksi });
      else if (hasil.galat === "belum_masuk") belumMasuk();
      else
        setKeadaan({ jenis: hasil.galat === "luring" ? "luring" : "gangguan" });
    });
    return () => {
      berlaku = false;
    };
  }, [pemanggil, kategori, jenis, percobaan]);

  async function keluarkan(idButir: string) {
    const hasil = await keluarkanDariKoleksi(idButir, pemanggil);
    if (hasil.jenis === "galat") {
      if (hasil.galat === "belum_masuk") belumMasuk();
      else setPesan(MIKROKOPI.keluarkanBelumTerkirim);
      return;
    }
    // Yang sudah tidak ada pun hilang dari layar — layar yang usang menyusul.
    setKeadaan((k) =>
      k.jenis === "koleksi"
        ? {
            jenis: "koleksi",
            koleksi: k.koleksi.filter((b) => b.id_butir !== idButir),
          }
        : k,
    );
    setPesan(MIKROKOPI.butirDikeluarkan);
  }

  const tersaring = kategori !== "" || jenis !== "";

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulKoleksi}</h1>

      <div className="penyaring-koleksi">
        <label htmlFor="saring-kategori">{MIKROKOPI.labelSaringKategori}</label>
        <select
          id="saring-kategori"
          onChange={(e) => setKategori(e.target.value as KategoriMasalah | "")}
          value={kategori}
        >
          <option value="">{MIKROKOPI.pilihanSemua}</option>
          {KATEGORI.map((k) => (
            <option key={k} value={k}>
              {LABEL_KATEGORI[k]}
            </option>
          ))}
        </select>
        <label htmlFor="saring-jenis">{MIKROKOPI.labelSaringJenis}</label>
        <select
          id="saring-jenis"
          onChange={(e) => setJenis(e.target.value as JenisSumberButir | "")}
          value={jenis}
        >
          <option value="">{MIKROKOPI.pilihanSemua}</option>
          {JENIS.map((j) => (
            <option key={j} value={j}>
              {LABEL_JENIS_SUMBER[j]}
            </option>
          ))}
        </select>
      </div>

      {pesan !== null && <p role="status">{pesan}</p>}

      {keadaan.jenis === "memuat" && (
        <>
          <p className="tersembunyi" role="status">
            {MIKROKOPI.koleksiMemuat}
          </p>
          <div aria-busy="true" className="kerangka">
            <div className="kerangka-baris" />
            <div className="kerangka-baris pendek" />
          </div>
        </>
      )}

      {keadaan.jenis === "gangguan" && (
        <div className="galat" role="alert">
          <p>{MIKROKOPI.koleksiGangguan}</p>
          <button
            onClick={() => {
              setKeadaan({ jenis: "memuat" });
              setPercobaan((n) => n + 1);
            }}
            type="button"
          >
            {MIKROKOPI.tombolCobaLagi}
          </button>
        </div>
      )}

      {keadaan.jenis === "luring" && (
        <section className="kosong">
          <p>{MIKROKOPI.koleksiLuring}</p>
        </section>
      )}

      {keadaan.jenis === "koleksi" && keadaan.koleksi.length === 0 && (
        <section className="kosong">
          <p>
            {tersaring
              ? MIKROKOPI.koleksiTersaringKosong
              : MIKROKOPI.koleksiKosong}
          </p>
        </section>
      )}

      {keadaan.jenis === "koleksi" &&
        keadaan.koleksi.map((b) => (
          <article className="blok-jawaban kartu-koleksi" key={b.id_butir}>
            {b.dasar_berubah && (
              <p className="penanda-dasar-berubah" role="note">
                {MIKROKOPI.penandaDasarBerubah}
              </p>
            )}
            <span className="label-sumber">
              {LABEL_JENIS_SUMBER[b.jenis_sumber]}
            </span>
            <h2>{b.judul}</h2>
            {b.catatan !== null && (
              <section>
                <h3>{MIKROKOPI.judulCatatanAnda}</h3>
                <p>{b.catatan}</p>
              </section>
            )}
            <section>
              <h3>{MIKROKOPI.judulIntiTemuan}</h3>
              <p>{b.inti_temuan}</p>
            </section>
            <section>
              <h3>{MIKROKOPI.judulImplikasi}</h3>
              <ol>
                {b.implikasi_tindakan.map((satu) => (
                  <li key={satu}>{satu}</li>
                ))}
              </ol>
            </section>
            <section>
              <h3>{MIKROKOPI.judulSumber}</h3>
              <p>
                {barisSumber(b.sumber.judul, b.sumber.penerbit, b.sumber.tahun)}
              </p>
            </section>
            <button
              className="tombol-kedua"
              onClick={() => void keluarkan(b.id_butir)}
              type="button"
            >
              {MIKROKOPI.tombolKeluarkan}
            </button>
          </article>
        ))}
    </main>
  );
}
