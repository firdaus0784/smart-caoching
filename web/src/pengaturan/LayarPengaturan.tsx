/**
 * Layar S-14 Pengaturan — T-6 fitur 033, FR-A06, NFR-09, RE-04, K-6.
 *
 * Tiga bagian: profil dan prioritas (formulir S-04 dalam mode sunting, lewat
 * rute fitur 030), persetujuan penelitian (S-02 yang sama), dan penarikan data.
 *
 * ## Penarikan tidak terkirim tanpa konfirmasi
 *
 * Tombol pertama hanya membuka konfirmasi. Konfirmasi menyebut akibatnya dan
 * memberi dua pilihan **setara bentuknya** — tanpa pilihan yang ditonjolkan,
 * tanpa rasa bersalah atau kehilangan sebagai pendorong (D-05 Bagian 10,
 * RE-04). Luring tidak diantrekan: permintaan yang menghapus tidak boleh
 * terkirim diam-diam kemudian.
 *
 * ## Kalimat penjelasan milik tim (P-4 B)
 *
 * Bila tim memasang `naskah/penarikan.json`, judul dan paragrafnya tampil apa
 * adanya. Tanpa berkas itu, daftar yang dihapus dan yang tidak tetap tampil,
 * dan penarikan tetap dapat diminta — hak peserta tidak menunggu naskah.
 */

import { useEffect, useState } from "react";

import { LayarProfil } from "../aktivasi/LayarProfil";
import { JALUR_NASKAH_PENARIKAN, bacaRingkasan, muatNaskah, tarikData, type Pemanggil } from "../klien";
import type { HasilNaskah, KeadaanPersetujuan, Ringkasan } from "../kontrak";
import { DATA_DITARIK, DATA_TIDAK_DITARIK, MIKROKOPI } from "../mikrokopi";

type Keadaan =
  | { readonly jenis: "memuat" }
  | { readonly jenis: "galat" }
  | { readonly jenis: "siap"; readonly ringkasan: Ringkasan }
  | { readonly jenis: "profil"; readonly ringkasan: Ringkasan };

type Penarikan = "tertutup" | "konfirmasi" | "mengirim";

const KALIMAT_PERSETUJUAN: Readonly<Record<KeadaanPersetujuan, string | null>> = {
  diberikan: MIKROKOPI.sudahSetuju,
  belum_diminta: null,
  ditolak: null,
  dicabut: null,
};

export function LayarPengaturan({
  pemanggil,
  kembali,
  bukaPersetujuan,
  ditarik,
  belumMasuk,
}: {
  readonly pemanggil: Pemanggil;
  readonly kembali: () => void;
  readonly bukaPersetujuan: () => void;
  /** 202 diterima — cangkang membersihkan peramban dan membuka S-01. */
  readonly ditarik: () => void;
  readonly belumMasuk: () => void;
}) {
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "memuat" });
  const [naskah, setNaskah] = useState<HasilNaskah>({ jenis: "belum_ada" });
  const [penarikan, setPenarikan] = useState<Penarikan>("tertutup");
  const [pesan, setPesan] = useState<string | null>(null);
  const [pemberitahuan, setPemberitahuan] = useState<string | null>(null);
  const [percobaan, setPercobaan] = useState(0);

  useEffect(() => {
    let berlaku = true;
    void Promise.all([bacaRingkasan(pemanggil), muatNaskah(pemanggil, JALUR_NASKAH_PENARIKAN)]).then(
      ([hasil, n]) => {
        if (!berlaku) return;
        setNaskah(n);
        if (hasil.jenis === "ringkasan") setKeadaan({ jenis: "siap", ringkasan: hasil.ringkasan });
        else if (hasil.galat === "belum_masuk") belumMasuk();
        else setKeadaan({ jenis: "galat" });
      },
    );
    return () => {
      berlaku = false;
    };
  }, [pemanggil, percobaan]);

  async function tarik() {
    setPenarikan("mengirim");
    setPesan(null);
    const hasil = await tarikData(pemanggil);
    if (hasil.jenis === "diterima") {
      ditarik();
      return;
    }
    if (hasil.galat === "belum_masuk") {
      belumMasuk();
      return;
    }
    setPenarikan("konfirmasi");
    setPesan(hasil.galat === "luring" ? MIKROKOPI.penarikanLuring : MIKROKOPI.penarikanGangguan);
  }

  if (keadaan.jenis === "profil") {
    return (
      <LayarProfil
        awal={keadaan.ringkasan}
        labelSimpan={MIKROKOPI.tombolSimpanPerubahan}
        pemanggil={pemanggil}
        selesai={() => {
          setPemberitahuan(MIKROKOPI.profilTersimpan);
          setKeadaan({ jenis: "memuat" });
          setPercobaan((n) => n + 1);
        }}
      />
    );
  }

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulPengaturan}</h1>
      <button className="tombol-kedua" onClick={kembali} type="button">
        {MIKROKOPI.tombolKembali}
      </button>
      {pemberitahuan !== null && <p role="status">{pemberitahuan}</p>}

      {keadaan.jenis === "memuat" && <p role="status">{MIKROKOPI.pengaturanMemuat}</p>}
      {keadaan.jenis === "galat" && (
        <div className="galat" role="alert">
          <p>{MIKROKOPI.pengaturanGangguan}</p>
          <button onClick={() => setPercobaan((n) => n + 1)} type="button">
            {MIKROKOPI.tombolCobaLagi}
          </button>
        </div>
      )}

      {keadaan.jenis === "siap" && (
        <>
          <section>
            <h2>{MIKROKOPI.judulBagianProfil}</h2>
            <button
              onClick={() => {
                setPemberitahuan(null);
                setKeadaan({ jenis: "profil", ringkasan: keadaan.ringkasan });
              }}
              type="button"
            >
              {MIKROKOPI.tombolUbahProfil}
            </button>
          </section>

          <section>
            <h2>{MIKROKOPI.judulPersetujuan}</h2>
            {KALIMAT_PERSETUJUAN[keadaan.ringkasan.persetujuan] !== null && (
              <p>{KALIMAT_PERSETUJUAN[keadaan.ringkasan.persetujuan]}</p>
            )}
            <button className="tombol-kedua" onClick={bukaPersetujuan} type="button">
              {MIKROKOPI.tautanPersetujuan}
            </button>
          </section>
        </>
      )}

      <section>
        <h2>{MIKROKOPI.judulBagianPenarikan}</h2>
        <p>{MIKROKOPI.pengantarPenarikan}</p>
        {naskah.jenis === "naskah" && (
          <div className="naskah">
            <h3>{naskah.naskah.judul}</h3>
            {naskah.naskah.paragraf.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        )}
        <h3>{MIKROKOPI.judulDataDitarik}</h3>
        <ul>
          {DATA_DITARIK.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>
        <h3>{MIKROKOPI.judulDataTidakDitarik}</h3>
        <ul>
          {DATA_TIDAK_DITARIK.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>

        {penarikan === "tertutup" ? (
          <button className="tombol-kedua" onClick={() => setPenarikan("konfirmasi")} type="button">
            {MIKROKOPI.tombolTarikData}
          </button>
        ) : (
          <div className="konfirmasi" role="group">
            <p>{MIKROKOPI.konfirmasiPenarikan}</p>
            <button
              className="tombol-kedua"
              disabled={penarikan === "mengirim"}
              onClick={() => void tarik()}
              type="button"
            >
              {MIKROKOPI.tombolYaTarik}
            </button>
            <button
              className="tombol-kedua"
              disabled={penarikan === "mengirim"}
              onClick={() => {
                setPenarikan("tertutup");
                setPesan(null);
              }}
              type="button"
            >
              {MIKROKOPI.tombolBatal}
            </button>
          </div>
        )}
        {pesan !== null && (
          <div className="galat" role="alert">
            {pesan}
          </div>
        )}
      </section>
    </main>
  );
}
