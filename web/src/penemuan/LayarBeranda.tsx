/**
 * Layar S-05 Beranda — T-7 fitur 013, FR-G01, FR-G02, FR-G04, FR-G05, P-7.
 *
 * Butir hari ini dari `GET /api/v1/beranda` (D-14 Bagian 4.6). Yang memilih
 * dan membatasi peladen; layar tidak menyaring, mengurutkan, maupun menambah.
 * Kode kategori tidak pernah tampil (K-7 fitur 030).
 *
 * Keadaan D-05 Bagian 7: KL-A kerangka kartu, KL-B dan KL-C dari `keadaan`
 * peladen, KL-D satu tindakan pemulihan, KL-E salinan terakhir dari simpanan
 * lokal. KL-F tidak berlaku — layar ini tidak mengirim apa pun. KL-G milik
 * S-06: butir yang sudah tidak tersedia.
 */

import { useEffect, useState } from "react";

import type { Simpanan } from "../draf";
import { TUJUAN_SALINAN, bacaBeranda, bacaButir, type Pemanggil } from "../klien";
import type { Beranda, ButirRingkas } from "../kontrak";
import { LABEL_JENIS_SUMBER, MIKROKOPI, waktuBaca } from "../mikrokopi";
import { salinanBeranda, simpanBeranda, simpanButir } from "./salinan";

type Keadaan =
  | { readonly jenis: "memuat" }
  | { readonly jenis: "beranda"; readonly beranda: Beranda; readonly salinan: boolean }
  | { readonly jenis: "luring_kosong" }
  | { readonly jenis: "gangguan" };

const KALIMAT_KOSONG = {
  belum_ada_prioritas: MIKROKOPI.berandaBelumPrioritas,
  belum_ada_butir: MIKROKOPI.berandaBelumAda,
  habis: MIKROKOPI.berandaHabis,
} as const;

export function LayarBeranda({
  pemanggil,
  simpanan,
  buka,
  keTanya,
  belumMasuk,
}: {
  readonly pemanggil: Pemanggil;
  readonly simpanan: Simpanan | null;
  readonly buka: (idButir: string) => void;
  readonly keTanya: () => void;
  readonly belumMasuk: () => void;
}) {
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "memuat" });
  const [percobaan, setPercobaan] = useState(0);

  useEffect(() => {
    let berlaku = true;
    void bacaBeranda(pemanggil).then(async (hasil) => {
      if (!berlaku) return;
      if (hasil.jenis === "beranda") {
        setKeadaan({ jenis: "beranda", beranda: hasil.beranda, salinan: false });
        simpanBeranda(simpanan, hasil.beranda);
        // P-7: isi lengkap ikut disimpan agar S-06 dapat dibaca tanpa koneksi.
        // Bertanda salinan: ini bukan butir dibuka (K-7 fitur 034, TK-74).
        for (const butir of hasil.beranda.butir) {
          const lengkap = await bacaButir(butir.id_butir, pemanggil, TUJUAN_SALINAN);
          if (lengkap.jenis === "butir") simpanButir(simpanan, lengkap.butir);
        }
        return;
      }
      if (hasil.jenis === "galat" && hasil.galat === "belum_masuk") {
        belumMasuk();
        return;
      }
      if (hasil.jenis === "galat" && hasil.galat === "luring") {
        const salinan = salinanBeranda(simpanan);
        setKeadaan(
          salinan === null
            ? { jenis: "luring_kosong" }
            : { jenis: "beranda", beranda: salinan, salinan: true },
        );
        return;
      }
      setKeadaan({ jenis: "gangguan" });
    });
    return () => {
      berlaku = false;
    };
    // `belumMasuk` dan `simpanan` tidak memicu pemuatan ulang.
  }, [pemanggil, percobaan]);

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulBeranda}</h1>

      {keadaan.jenis === "memuat" && (
        <>
          <p className="tersembunyi" role="status">
            {MIKROKOPI.berandaMemuat}
          </p>
          <div aria-busy="true" className="kerangka" data-testid="kerangka-beranda">
            <div className="kerangka-baris" />
            <div className="kerangka-baris" />
            <div className="kerangka-baris pendek" />
          </div>
        </>
      )}

      {keadaan.jenis === "gangguan" && (
        <div className="galat" role="alert">
          <p>{MIKROKOPI.berandaGangguan}</p>
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

      {keadaan.jenis === "luring_kosong" && (
        <section className="kosong">
          <p>{MIKROKOPI.berandaLuringKosong}</p>
        </section>
      )}

      {keadaan.jenis === "beranda" && (
        <>
          {keadaan.salinan && <p className="keterangan">{MIKROKOPI.berandaLuringSalinan}</p>}
          {keadaan.beranda.keadaan === "berisi" ? (
            <ul className="daftar-butir">
              {keadaan.beranda.butir.map((butir) => (
                <li key={butir.id_butir}>
                  <KartuButir butir={butir} buka={buka} />
                </li>
              ))}
            </ul>
          ) : (
            <section className="kosong">
              <p>{KALIMAT_KOSONG[keadaan.beranda.keadaan]}</p>
            </section>
          )}
        </>
      )}

      <button className="tombol-kedua" onClick={keTanya} type="button">
        {MIKROKOPI.tombolTanyaCepat}
      </button>
    </main>
  );
}

function KartuButir({
  butir,
  buka,
}: {
  readonly butir: ButirRingkas;
  readonly buka: (idButir: string) => void;
}) {
  return (
    <button className="kartu-butir" onClick={() => buka(butir.id_butir)} type="button">
      <span className="label-sumber">{LABEL_JENIS_SUMBER[butir.jenis_sumber]}</span>
      <strong>{butir.judul}</strong>
      <span>{butir.alasan_relevansi}</span>
      <span className="waktu-baca">{waktuBaca(butir.perkiraan_waktu_baca)}</span>
    </button>
  );
}
