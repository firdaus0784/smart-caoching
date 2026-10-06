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

import { useEffect, useRef, useState, type FormEvent } from "react";

import { bacaDraf, hapusDraf, simpanDraf, type Simpanan } from "../draf";
import { bacaPercakapan, tanya, type Pemanggil } from "../klien";
import type { Giliran, JenisGalat, Tanggapan } from "../kontrak";
import { MIKROKOPI, PESAN_GALAT } from "../mikrokopi";
import { jadikanAktif, percakapanAktif, percakapanBaru, tandaiDikenal } from "../percakapan";
import { BlokJawaban } from "./BlokJawaban";
import { PercakapanTerdahulu, PertanyaanSebelumnya } from "./RiwayatPercakapan";

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
  /** Fitur 029: 401 pada pengiriman — cangkang membuka S-01. Argumennya
   * menyatakan apakah draf memang tersimpan. */
  readonly belumMasuk?: (tersimpan: boolean) => void;
  /** Fitur 029: tombol Keluar; tanpa ini tombolnya tidak tampil. */
  readonly keluar?: () => void;
  /** Fitur 030 P-5: membuka S-02 lagi — setuju sesudah menolak, atau mencabut. */
  readonly bukaPersetujuan?: () => void;
  /** Fitur 033 P-5: S-14, di samping Keluar. */
  readonly bukaPengaturan?: () => void;
}

export function LayarTanya({
  pemanggil,
  simpanan,
  salin,
  belumMasuk,
  keluar,
  bukaPersetujuan,
  bukaPengaturan,
}: PropertiLayarTanya) {
  const [pertanyaan, setPertanyaan] = useState(() => bacaDraf(simpanan));
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "kosong" });
  const [awal] = useState(() => percakapanAktif(simpanan));
  const [idPercakapan, setIdPercakapan] = useState(awal.id);
  // Percakapan yang baru dibangkitkan pasti belum dikenal peladen; riwayatnya
  // baru dibaca sesudah pertanyaan pertamanya (T-8, KB-147).
  const [dikenalPeladen, setDikenalPeladen] = useState(!awal.baru);
  const [giliran, setGiliran] = useState<readonly Giliran[]>([]);
  const [muatUlang, setMuatUlang] = useState(0);
  const isian = useRef<HTMLTextAreaElement>(null);

  // Blok 9: pertanyaan percakapan aktif — saat dibuka, sesudah muat ulang
  // halaman, dan sesudah tiap jawaban. Galat memuatnya tidak menjatuhkan
  // layar; bloknya sekadar tidak tampil.
  useEffect(() => {
    if (!dikenalPeladen) return undefined;
    let berlaku = true;
    void bacaPercakapan(idPercakapan, pemanggil).then((hasil) => {
      if (berlaku) setGiliran(hasil.jenis === "percakapan" ? hasil.percakapan.giliran : []);
    });
    return () => {
      berlaku = false;
    };
  }, [idPercakapan, muatUlang, pemanggil, dikenalPeladen]);

  function pilihPertanyaanLama(teks: string) {
    // Mengisi, tidak mengirim: pengguna yang memutuskan bertanya ulang.
    ubah(teks);
    isian.current?.focus();
  }

  function mulaiPercakapanBaru() {
    setIdPercakapan(percakapanBaru(simpanan));
    setDikenalPeladen(false);
    setGiliran([]);
    setKeadaan({ jenis: "kosong" });
  }

  function bukaPercakapan(id: string) {
    jadikanAktif(simpanan, id);
    setIdPercakapan(id);
    setDikenalPeladen(true);
    setKeadaan({ jenis: "kosong" });
  }

  function ubah(teks: string) {
    setPertanyaan(teks);
    simpanDraf(simpanan, teks);
  }

  async function ajukan() {
    const teks = pertanyaan.trim();
    if (teks === "" || keadaan.jenis === "memuat") return;
    setKeadaan({ jenis: "memuat" });
    const hasil = await tanya(teks, idPercakapan, pemanggil);
    if (hasil.jenis === "jawaban") {
      hapusDraf(simpanan);
      setKeadaan({ jenis: "jawaban", tanggapan: hasil.tanggapan });
      tandaiDikenal(simpanan, idPercakapan);
      setDikenalPeladen(true);
      setMuatUlang((n) => n + 1);
      return;
    }
    // R-09: draf ditulis ulang pada saat galat, dan "tersimpan" hanya
    // dinyatakan bila simpanan lokal memang menerimanya (M-6, M-14).
    const tersimpan = simpanDraf(simpanan, pertanyaan);
    if (hasil.galat === "belum_masuk" && belumMasuk !== undefined) {
      belumMasuk(tersimpan);
      return;
    }
    setKeadaan({ jenis: "galat", galat: hasil.galat, tersimpan });
  }

  function kirim(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    void ajukan();
  }

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulLayar}</h1>
      {keluar !== undefined && (
        <div className="kepala-layar">
          <button className="tombol-kedua" onClick={keluar} type="button">
            {MIKROKOPI.tombolKeluar}
          </button>
          {bukaPengaturan !== undefined && (
            <button className="tombol-kedua" onClick={bukaPengaturan} type="button">
              {MIKROKOPI.tombolPengaturan}
            </button>
          )}
        </div>
      )}
      {bukaPersetujuan !== undefined && (
        <button className="tombol-kedua" onClick={bukaPersetujuan} type="button">
          {MIKROKOPI.tautanPersetujuan}
        </button>
      )}

      <form className="isian-pertanyaan" onSubmit={kirim}>
        <label htmlFor="pertanyaan">{MIKROKOPI.labelPertanyaan}</label>
        <p id="petunjuk-pertanyaan">{MIKROKOPI.petunjukPertanyaan}</p>
        <textarea
          aria-describedby="petunjuk-pertanyaan"
          id="pertanyaan"
          onChange={(e) => ubah(e.target.value)}
          ref={isian}
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

      <PertanyaanSebelumnya giliran={giliran} pilih={pilihPertanyaanLama} />

      {(giliran.length > 0 || keadaan.jenis === "jawaban") && (
        <button className="tombol-kedua" onClick={mulaiPercakapanBaru} type="button">
          {MIKROKOPI.tombolPercakapanBaru}
        </button>
      )}

      <PercakapanTerdahulu
        aktif={idPercakapan}
        buka={bukaPercakapan}
        key={idPercakapan}
        pemanggil={pemanggil}
      />
    </main>
  );
}
