/**
 * Layar S-10 Pembaca sumber — T-7 fitur 032, FR-F11, R-07, P-2 A; D-05 S-10.
 *
 * Dibuka dari baris sitasi S-09 dan **di dalam** layar Tanya, sehingga
 * "Kembali ke jawaban" menampilkan jawaban yang sama tanpa bertanya ulang —
 * jawaban tidak disimpan riwayat (C-07).
 *
 * Urutan tetap: identitas dokumen, bagian yang dirujuk, **status keberlakuan**
 * beserta rujukan pengganti, lalu teks bagian atau kalimat mengapa teks tidak
 * tampil. Status sebelum teks: pembaca berhak tahu sebuah aturan masih berlaku
 * sebelum membacanya. Apakah teks tampil diputus peladen (D-14 Bagian 4.10);
 * layar tidak menyimpulkannya.
 *
 * Tautan sumber asli datang dari baris sitasi — korpus tidak menyimpannya.
 */

import { useEffect, useState } from "react";

import { bacaSumber, type Pemanggil } from "../klien";
import type { Sitasi, SumberTampil } from "../kontrak";
import {
  LABEL_JENIS_DOKUMEN,
  MIKROKOPI,
  STATUS_SUMBER,
  TANPA_TEKS,
  bagianDirujuk,
  penerbitDanTahun,
  teksPenggantiSumber,
} from "../mikrokopi";

type Keadaan =
  | { readonly jenis: "memuat" }
  | { readonly jenis: "sumber"; readonly sumber: SumberTampil }
  | { readonly jenis: "tidak_ada" }
  | { readonly jenis: "luring" }
  | { readonly jenis: "gangguan" };

/** Sama dengan baris sitasi S-09: hanya tautan berskema web yang dipasang. */
function tautanAman(tautan: string | null): string | null {
  return tautan !== null && /^https?:\/\//i.test(tautan) ? tautan : null;
}

export function LayarSumber({
  sitasi,
  pemanggil,
  kembali,
  belumMasuk,
}: {
  readonly sitasi: Sitasi;
  readonly pemanggil: Pemanggil;
  readonly kembali: () => void;
  readonly belumMasuk: () => void;
}) {
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "memuat" });
  const [percobaan, setPercobaan] = useState(0);

  useEffect(() => {
    let berlaku = true;
    void bacaSumber(sitasi.id_dokumen, sitasi.bagian, pemanggil).then(
      (hasil) => {
        if (!berlaku) return;
        if (hasil.jenis === "sumber")
          setKeadaan({ jenis: "sumber", sumber: hasil.sumber });
        else if (hasil.jenis === "tidak_ada")
          setKeadaan({ jenis: "tidak_ada" });
        else if (hasil.galat === "belum_masuk") belumMasuk();
        else
          setKeadaan({
            jenis: hasil.galat === "luring" ? "luring" : "gangguan",
          });
      },
    );
    return () => {
      berlaku = false;
    };
  }, [sitasi.id_dokumen, sitasi.bagian, pemanggil, percobaan]);

  const tombolKembali = (
    <button className="tombol-kedua" onClick={kembali} type="button">
      {MIKROKOPI.tombolKembaliJawaban}
    </button>
  );

  if (keadaan.jenis === "memuat") {
    return (
      <main className="layar-tanya">
        {tombolKembali}
        <p className="tersembunyi" role="status">
          {MIKROKOPI.sumberMemuat}
        </p>
        <div aria-busy="true" className="kerangka">
          <div className="kerangka-penanda" />
          <div className="kerangka-baris" />
          <div className="kerangka-baris pendek" />
        </div>
      </main>
    );
  }
  if (keadaan.jenis === "gangguan") {
    return (
      <main className="layar-tanya">
        {tombolKembali}
        <div className="galat" role="alert">
          <p>{MIKROKOPI.sumberGangguan}</p>
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
      </main>
    );
  }
  if (keadaan.jenis !== "sumber") {
    return (
      <main className="layar-tanya">
        {tombolKembali}
        <section className="kosong">
          <p>
            {keadaan.jenis === "tidak_ada"
              ? MIKROKOPI.sumberTidakAda
              : MIKROKOPI.sumberLuring}
          </p>
        </section>
      </main>
    );
  }

  const s = keadaan.sumber;
  const tautan = tautanAman(sitasi.tautan);
  const adaStatus =
    s.status_keberlakuan !== null || s.jenis === "regulasi_resmi";
  return (
    <main className="layar-tanya">
      {tombolKembali}
      <article className="blok-jawaban pembaca-sumber">
        <span className="label-sumber">{LABEL_JENIS_DOKUMEN[s.jenis]}</span>
        <h1>{s.judul}</h1>
        <p>{penerbitDanTahun(s.penerbit, s.tahun)}</p>
        <p className="bagian-dirujuk">{bagianDirujuk(s.bagian)}</p>

        {adaStatus && (
          <section
            className="status-sumber"
            data-status={s.status_keberlakuan ?? "belum_tercatat"}
            data-testid="status-sumber"
          >
            <h2>{MIKROKOPI.judulStatusKeberlakuan}</h2>
            <p>
              {s.status_keberlakuan === null
                ? MIKROKOPI.statusBelumTercatat
                : STATUS_SUMBER[s.status_keberlakuan]}
            </p>
            {s.rujukan_pengganti !== null &&
              s.status_keberlakuan !== null &&
              s.status_keberlakuan !== "berlaku" && (
                <p>
                  {teksPenggantiSumber(
                    s.status_keberlakuan,
                    s.rujukan_pengganti,
                  )}
                </p>
              )}
          </section>
        )}

        {s.tanpa_teks === null ? (
          <section data-testid="teks-bagian">
            <h2>{MIKROKOPI.judulTeksBagian}</h2>
            {s.teks_bagian.map((teks, i) => (
              <p key={i}>{teks}</p>
            ))}
          </section>
        ) : (
          <p className="keterangan">{TANPA_TEKS[s.tanpa_teks]}</p>
        )}

        {tautan !== null && (
          <a href={tautan} rel="noopener noreferrer" target="_blank">
            {MIKROKOPI.bukaSumberAsli}
          </a>
        )}
      </article>
    </main>
  );
}
