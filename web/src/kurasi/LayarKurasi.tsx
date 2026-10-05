/**
 * Layar S-15 Antrean kurasi — T-8 fitur 013, FR-I01, FR-I02, FR-I06, K-6.
 *
 * Satu baris per kandidat, dikelompokkan menurut kategori, dengan **empat
 * putusan setara** — Setujui · Sunting · Tolak · Tunda (D-06 Bagian 7.3).
 * Skor relevansi tidak tampil: ambangnya belum dikalibrasi (BT-24, C-16).
 * Alasan penolakan dipilih menurut kalimat D-06 Bagian 7.4; kodenya yang
 * dikirim, tidak yang ditampilkan (C-13).
 *
 * Daftar kedua "Sedang tayang" adalah tempat penarikan dimulai (K-6).
 *
 * Layar ini tidak menyimpan apa pun di peramban: putusan menuntut keadaan
 * antrean terkini (plan Bagian 8).
 */

import { useState, type FormEvent } from "react";

import { bacaAntrean, PEMICU, putuskan, tarikButir, type BadanPutusan, type Pemanggil } from "../klien";
import type {
  AlasanTolak,
  Antrean,
  HasilAntrean,
  KandidatTampil,
  KategoriMasalah,
  Pemicu,
  TayangTampil,
} from "../kontrak";
import {
  LABEL_ALASAN_TOLAK,
  LABEL_JENIS_SUMBER,
  LABEL_KATEGORI,
  LABEL_PEMICU,
  LABEL_STATUS,
  MIKROKOPI,
  keteranganKurasi,
} from "../mikrokopi";
import { LayarSunting } from "./LayarSunting";

type Pesan = { readonly untuk: string; readonly kalimat: string } | null;

export function LayarKurasi({
  awal,
  pemanggil,
  keluar,
  belumMasuk,
}: {
  readonly awal: Antrean;
  readonly pemanggil: Pemanggil;
  readonly keluar: () => void;
  readonly belumMasuk: () => void;
}) {
  const [antrean, setAntrean] = useState<Antrean>(awal);
  const [pesan, setPesan] = useState<Pesan>(null);
  const [umum, setUmum] = useState<string | null>(null);
  const [sunting, setSunting] = useState<KandidatTampil | null>(null);

  /** Hasil satu kiriman: `true` bila tercatat. Galat tidak pernah dibaca isinya. */
  async function terima(idButir: string, hasil: HasilAntrean): Promise<boolean> {
    if (hasil.jenis === "antrean") {
      setAntrean(hasil.antrean);
      setPesan(null);
      setUmum(null);
      return true;
    }
    if (hasil.jenis === "tidak_ada") {
      const baru = await bacaAntrean(pemanggil);
      if (baru.jenis === "antrean") setAntrean(baru.antrean);
      setUmum(MIKROKOPI.putusanSudahDiambil);
      return false;
    }
    if (hasil.galat === "belum_masuk") {
      belumMasuk();
      return false;
    }
    const kalimat =
      hasil.galat === "luring"
        ? MIKROKOPI.kurasiLuring
        : hasil.galat === "pertanyaan_ditolak"
          ? MIKROKOPI.putusanDitolak
          : MIKROKOPI.putusanGangguan;
    setPesan({ untuk: idButir, kalimat });
    return false;
  }

  async function kirimPutusan(idButir: string, badan: BadanPutusan): Promise<boolean> {
    return terima(idButir, await putuskan(idButir, badan, pemanggil));
  }

  if (sunting !== null) {
    return (
      <LayarSunting
        batal={() => setSunting(null)}
        kandidat={sunting}
        kirim={async (badan) => {
          const tercatat = await kirimPutusan(sunting.id_butir, badan);
          setSunting(null);
          return tercatat;
        }}
      />
    );
  }

  const kelompok = new Map<KategoriMasalah, KandidatTampil[]>();
  for (const k of antrean.menunggu) kelompok.set(k.kategori, [...(kelompok.get(k.kategori) ?? []), k]);

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulKurasi}</h1>
      <button className="tombol-kedua" onClick={keluar} type="button">
        {MIKROKOPI.tombolKeluar}
      </button>
      {umum !== null && (
        <p className="keterangan" role="status">
          {umum}
        </p>
      )}

      <section>
        <h2>{MIKROKOPI.judulMenunggu}</h2>
        {antrean.menunggu.length === 0 && <p className="kosong">{MIKROKOPI.antreanKosong}</p>}
        {[...kelompok.entries()].map(([kategori, daftar]) => (
          <section key={kategori}>
            <h2>{LABEL_KATEGORI[kategori]}</h2>
            <ul className="daftar-butir">
              {daftar.map((k) => (
                <li className="kartu-butir" key={k.id_butir}>
                  <BarisKandidat
                    kandidat={k}
                    kirim={(badan) => kirimPutusan(k.id_butir, badan)}
                    pesan={pesan?.untuk === k.id_butir ? pesan.kalimat : null}
                    sunting={() => setSunting(k)}
                  />
                </li>
              ))}
            </ul>
          </section>
        ))}
      </section>

      <section>
        <h2>{MIKROKOPI.judulSedangTayang}</h2>
        {antrean.tayang.length === 0 && <p className="kosong">{MIKROKOPI.tayangKosong}</p>}
        <ul className="daftar-butir">
          {antrean.tayang.map((t) => (
            <li className="kartu-butir" key={t.id_butir}>
              <BarisTayang
                kirim={async (badan) => terima(t.id_butir, await tarikButir(t.id_butir, badan, pemanggil))}
                pesan={pesan?.untuk === t.id_butir ? pesan.kalimat : null}
                tayang={t}
              />
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

function Keterangan({ butir }: { readonly butir: KandidatTampil | TayangTampil }) {
  return (
    <>
      <span className="label-sumber">{LABEL_JENIS_SUMBER[butir.jenis_sumber]}</span>
      <h3>{butir.judul}</h3>
      <p className="keterangan">
        {keteranganKurasi(
          butir.lisensi,
          butir.status_keberlakuan === null ? null : LABEL_STATUS[butir.status_keberlakuan],
        )}
      </p>
    </>
  );
}

type Mode = "setujui" | "tolak" | "tunda" | null;

function BarisKandidat({
  kandidat,
  kirim,
  sunting,
  pesan,
}: {
  readonly kandidat: KandidatTampil;
  readonly kirim: (badan: BadanPutusan) => Promise<boolean>;
  readonly sunting: () => void;
  readonly pesan: string | null;
}) {
  const [mode, setMode] = useState<Mode>(null);
  const [catatan, setCatatan] = useState("");
  const [alasan, setAlasan] = useState<AlasanTolak | null>(null);
  const [kembaliPada, setKembaliPada] = useState("");
  const [kurang, setKurang] = useState(false);
  const id = kandidat.id_butir;

  function badan(): BadanPutusan | null {
    if (mode === "tolak") return alasan === null ? null : { jenis: "tolak", alasan_tolak: alasan };
    if (catatan.trim() === "") return null;
    if (mode === "tunda") {
      return kembaliPada === "" ? null : { jenis: "tunda", catatan, kembali_pada: kembaliPada };
    }
    return { jenis: "setujui", catatan };
  }

  async function ajukan(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    const satu = badan();
    setKurang(satu === null);
    if (satu !== null) await kirim(satu);
  }

  return (
    <>
      <Keterangan butir={kandidat} />
      <p>{kandidat.alasan_relevansi}</p>
      <p>{kandidat.inti_temuan}</p>
      <ul>
        {kandidat.implikasi_tindakan.map((satu) => (
          <li key={satu}>{satu}</li>
        ))}
      </ul>
      <div className="tindakan">
        {(
          [
            ["setujui", MIKROKOPI.tombolSetujui],
            ["sunting", MIKROKOPI.tombolSunting],
            ["tolak", MIKROKOPI.tombolTolak],
            ["tunda", MIKROKOPI.tombolTunda],
          ] as const
        ).map(([nilai, nama]) => (
          <button
            aria-pressed={mode === nilai}
            className="tombol-kedua"
            key={nilai}
            onClick={() => (nilai === "sunting" ? sunting() : setMode(nilai))}
            type="button"
          >
            {nama}
          </button>
        ))}
      </div>
      {mode !== null && (
        <form className="isian-pertanyaan" onSubmit={(e) => void ajukan(e)}>
          {mode === "tolak" ? (
            <fieldset>
              <legend>{MIKROKOPI.labelAlasanTolak}</legend>
              {(Object.keys(LABEL_ALASAN_TOLAK) as AlasanTolak[]).map((kode) => (
                <label key={kode}>
                  <input
                    checked={alasan === kode}
                    name={`alasan-${id}`}
                    onChange={() => setAlasan(kode)}
                    type="radio"
                  />
                  {LABEL_ALASAN_TOLAK[kode]}
                </label>
              ))}
            </fieldset>
          ) : (
            <>
              {mode === "tunda" && (
                <>
                  <label htmlFor={`kembali-${id}`}>{MIKROKOPI.labelKembaliPada}</label>
                  <input
                    id={`kembali-${id}`}
                    onChange={(e) => setKembaliPada(e.target.value)}
                    type="date"
                    value={kembaliPada}
                  />
                </>
              )}
              <label htmlFor={`catatan-${id}`}>{MIKROKOPI.labelCatatan}</label>
              <textarea
                id={`catatan-${id}`}
                onChange={(e) => setCatatan(e.target.value)}
                rows={2}
                value={catatan}
              />
            </>
          )}
          {(kurang || pesan !== null) && (
            <p className="galat" role="alert">
              {kurang ? MIKROKOPI.putusanBelumLengkap : pesan}
            </p>
          )}
          <button type="submit">{MIKROKOPI.tombolKirimPutusan}</button>
        </form>
      )}
    </>
  );
}

function BarisTayang({
  tayang,
  kirim,
  pesan,
}: {
  readonly tayang: TayangTampil;
  readonly kirim: (badan: {
    readonly pemicu: Pemicu;
    readonly catatan: string;
    readonly status_terkini?: "diubah" | "dicabut";
    readonly angka_berubah_bermakna?: boolean;
  }) => Promise<boolean>;
  readonly pesan: string | null;
}) {
  const [terbuka, setTerbuka] = useState(false);
  const [pemicu, setPemicu] = useState<Pemicu | null>(null);
  const [status, setStatus] = useState<"diubah" | "dicabut" | null>(null);
  const [bermakna, setBermakna] = useState(false);
  const [catatan, setCatatan] = useState("");
  const [kurang, setKurang] = useState(false);
  const id = tayang.id_butir;

  async function ajukan(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    const lengkap =
      pemicu !== null &&
      catatan.trim() !== "" &&
      (pemicu !== "regulasi_sumber_berubah" || status !== null);
    setKurang(!lengkap);
    if (!lengkap || pemicu === null) return;
    if (pemicu === "regulasi_sumber_berubah" && status !== null) {
      await kirim({ pemicu, catatan, status_terkini: status });
    } else if (pemicu === "data_sumber_diperbarui" && bermakna) {
      await kirim({ pemicu, catatan, angka_berubah_bermakna: true });
    } else {
      await kirim({ pemicu, catatan });
    }
  }

  return (
    <>
      <Keterangan butir={tayang} />
      {tayang.perlu_tinjauan && <p className="keterangan">{MIKROKOPI.perluTinjauan}</p>}
      <div className="tindakan">
        <button className="tombol-kedua" onClick={() => setTerbuka(true)} type="button">
          {MIKROKOPI.tombolTarik}
        </button>
      </div>
      {terbuka && (
        <form className="isian-pertanyaan" onSubmit={(e) => void ajukan(e)}>
          <fieldset>
            <legend>{MIKROKOPI.labelPemicu}</legend>
            {PEMICU.map((satu) => (
              <label key={satu}>
                <input
                  checked={pemicu === satu}
                  name={`pemicu-${id}`}
                  onChange={() => setPemicu(satu)}
                  type="radio"
                />
                {LABEL_PEMICU[satu]}
              </label>
            ))}
          </fieldset>
          {pemicu === "regulasi_sumber_berubah" && (
            <fieldset>
              <legend>{MIKROKOPI.labelStatusTerkini}</legend>
              {(["diubah", "dicabut"] as const).map((satu) => (
                <label key={satu}>
                  <input
                    checked={status === satu}
                    name={`status-${id}`}
                    onChange={() => setStatus(satu)}
                    type="radio"
                  />
                  {LABEL_STATUS[satu]}
                </label>
              ))}
            </fieldset>
          )}
          {pemicu === "data_sumber_diperbarui" && (
            <label>
              <input checked={bermakna} onChange={(e) => setBermakna(e.target.checked)} type="checkbox" />
              {MIKROKOPI.labelAngkaBermakna}
            </label>
          )}
          <label htmlFor={`catatan-tarik-${id}`}>{MIKROKOPI.labelCatatan}</label>
          <textarea
            id={`catatan-tarik-${id}`}
            onChange={(e) => setCatatan(e.target.value)}
            rows={2}
            value={catatan}
          />
          {(kurang || pesan !== null) && (
            <p className="galat" role="alert">
              {kurang ? MIKROKOPI.putusanBelumLengkap : pesan}
            </p>
          )}
          <button type="submit">{MIKROKOPI.tombolKirimPutusan}</button>
        </form>
      )}
    </>
  );
}
