/**
 * S-17 Aduan jawaban — T-7 fitur 036, FR-I04, R-06; D-05 0.7, D-14 Bagian 4.9.
 *
 * Satu kartu per aduan, terlama lebih dulu. Jawaban tampil lewat `BlokJawaban`
 * yang sama dengan S-09, **tanpa tindakan**: ia jawaban pada saat diadukan,
 * bukan jawaban sistem sekarang, dan keterangan tetap menyatakannya.
 *
 * Tidak ada penanda peserta di mana pun pada layar ini (C-05) — dan bukan
 * karena layar menyembunyikannya: klien menolak aduan yang membawa penaut.
 * Menambah pengetahuan tidak dilakukan di sini (C-06): tindak lanjut hanya
 * mencatat apa yang sudah dilakukan lewat jalur kurasi yang ada.
 */

import { useEffect, useId, useState, type FormEvent } from "react";

import { bacaAduan, tindakLanjutiAduan, type Pemanggil } from "../klien";
import type {
  AduanTampil,
  HasilAduan,
  PermintaanTindakLanjut,
  TindakLanjutAduan,
} from "../kontrak";
import { LABEL_TINDAK_LANJUT, MIKROKOPI, diadukanPada } from "../mikrokopi";
import { BlokJawaban } from "../tanya/BlokJawaban";

type Keadaan =
  | { readonly jenis: "memuat" }
  | { readonly jenis: "aduan"; readonly daftar: readonly AduanTampil[] }
  | { readonly jenis: "galat" };

const TINDAK_LANJUT = Object.keys(LABEL_TINDAK_LANJUT) as TindakLanjutAduan[];

export function LayarAduan({
  pemanggil,
  keluar,
  belumMasuk,
}: {
  readonly pemanggil: Pemanggil;
  readonly keluar: () => void;
  readonly belumMasuk: () => void;
}) {
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "memuat" });
  const [umum, setUmum] = useState<string | null>(null);
  const [pesan, setPesan] = useState<{
    readonly untuk: number;
    readonly kalimat: string;
  } | null>(null);

  function terapkan(hasil: HasilAduan): boolean {
    if (hasil.jenis === "aduan") {
      setKeadaan({ jenis: "aduan", daftar: hasil.aduan.aduan });
      return true;
    }
    if (hasil.jenis === "galat" && hasil.galat === "belum_masuk") {
      belumMasuk();
      return false;
    }
    setKeadaan({ jenis: "galat" });
    return false;
  }

  useEffect(() => {
    let berlaku = true;
    void bacaAduan(pemanggil).then((hasil) => {
      if (berlaku) terapkan(hasil);
    });
    return () => {
      berlaku = false;
    };
    // `terapkan` dibentuk ulang tiap render; yang menentukan hanya pemanggil.
  }, [pemanggil]);

  async function kirim(
    nomor: number,
    badan: PermintaanTindakLanjut,
  ): Promise<void> {
    const hasil = await tindakLanjutiAduan(nomor, badan, pemanggil);
    if (hasil.jenis === "aduan") {
      terapkan(hasil);
      setPesan(null);
      setUmum(null);
      return;
    }
    if (hasil.jenis === "tidak_ada") {
      terapkan(await bacaAduan(pemanggil));
      setUmum(MIKROKOPI.aduanSudahDiambil);
      return;
    }
    if (hasil.galat === "belum_masuk") {
      belumMasuk();
      return;
    }
    setPesan({
      untuk: nomor,
      kalimat:
        hasil.galat === "luring"
          ? MIKROKOPI.tindakLanjutLuring
          : hasil.galat === "pertanyaan_ditolak"
            ? MIKROKOPI.tindakLanjutDitolak
            : MIKROKOPI.tindakLanjutGangguan,
    });
  }

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulAduan}</h1>
      <button className="tombol-kedua" onClick={keluar} type="button">
        {MIKROKOPI.tombolKeluar}
      </button>
      {umum !== null && (
        <p className="keterangan" role="status">
          {umum}
        </p>
      )}
      {keadaan.jenis === "memuat" && (
        <p role="status">{MIKROKOPI.aduanMemuat}</p>
      )}
      {keadaan.jenis === "galat" && (
        <div className="galat" role="alert">
          {MIKROKOPI.aduanGangguan}
        </div>
      )}
      {keadaan.jenis === "aduan" && keadaan.daftar.length === 0 && (
        <p className="kosong">{MIKROKOPI.aduanKosong}</p>
      )}
      {keadaan.jenis === "aduan" && keadaan.daftar.length > 0 && (
        <ul className="daftar-butir">
          {keadaan.daftar.map((a) => (
            <li className="kartu-butir" key={a.nomor}>
              <KartuAduan
                aduan={a}
                kirim={(badan) => kirim(a.nomor, badan)}
                pesan={pesan?.untuk === a.nomor ? pesan.kalimat : null}
              />
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

function KartuAduan({
  aduan,
  kirim,
  pesan,
}: {
  readonly aduan: AduanTampil;
  readonly kirim: (badan: PermintaanTindakLanjut) => Promise<void>;
  readonly pesan: string | null;
}) {
  const id = useId();
  const [tindak, setTindak] = useState<TindakLanjutAduan | null>(null);
  const [catatan, setCatatan] = useState("");
  const [lokal, setLokal] = useState<string | null>(null);
  const [mengirim, setMengirim] = useState(false);

  async function simpan(peristiwa: FormEvent<HTMLFormElement>): Promise<void> {
    peristiwa.preventDefault();
    const bersih = catatan.trim();
    if (tindak === null || bersih === "") {
      setLokal(MIKROKOPI.tindakLanjutDitolak);
      return;
    }
    setLokal(null);
    setMengirim(true);
    await kirim({ tindak_lanjut: tindak, catatan: bersih });
    setMengirim(false);
  }

  const galat = lokal ?? pesan;
  return (
    <article className="kartu-aduan">
      <p className="keterangan">{diadukanPada(aduan.diadukan_pada)}</p>
      <h2>{MIKROKOPI.labelPertanyaanAduan}</h2>
      <p>{aduan.pertanyaan}</p>
      <h2>{MIKROKOPI.labelAlasanAduan}</h2>
      <p>{aduan.alasan ?? MIKROKOPI.tanpaAlasanAduan}</p>
      <p className="keterangan">{MIKROKOPI.keteranganJawabanSaatItu}</p>
      <BlokJawaban tanggapan={aduan.tanggapan} />
      <form onSubmit={(e) => void simpan(e)}>
        <fieldset>
          <legend>{MIKROKOPI.labelTindakLanjut}</legend>
          {TINDAK_LANJUT.map((t) => (
            <label key={t}>
              <input
                checked={tindak === t}
                name={`${id}-tindak`}
                onChange={() => setTindak(t)}
                type="radio"
              />
              {LABEL_TINDAK_LANJUT[t]}
            </label>
          ))}
        </fieldset>
        <label htmlFor={`${id}-catatan`}>
          {MIKROKOPI.labelCatatanTindakLanjut}
        </label>
        <textarea
          id={`${id}-catatan`}
          onChange={(e) => setCatatan(e.target.value)}
          rows={2}
          value={catatan}
        />
        <button disabled={mengirim} type="submit">
          {MIKROKOPI.tombolSimpanTindakLanjut}
        </button>
      </form>
      {galat !== null && (
        <div className="galat" role="alert">
          {galat}
        </div>
      )}
    </article>
  );
}
