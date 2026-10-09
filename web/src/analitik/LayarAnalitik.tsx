/**
 * Layar S-18 Analitik penelitian — T-6 fitur 035, FR-J03, FR-J04, K-5.
 *
 * Satu halaman tabel bagi peran peneliti, tanpa navigasi pengguna dan tanpa
 * pustaka grafik (C-12). Angka dari `GET /api/v1/analitik/ringkas` apa adanya;
 * layar tidak menghitung ulang.
 *
 * **`null` bukan nol (R-04).** Rasio tanpa penyebut, median tanpa sesi, dan
 * waktu tanpa peristiwa tampil "Belum dapat dihitung". Nol berarti diukur dan
 * tidak ada; menyamakan keduanya membuat laporan berbohong tanpa satu angka
 * pun salah.
 *
 * Ekspor: rentang tanggal, pilihan tegas menyertakan peristiwa pengembangan,
 * lalu berkas diserahkan kepada `simpan` — pada peramban, unduhan lewat
 * tautan sementara. Luring tidak diantrekan.
 */

import { useState, type FormEvent, type ReactNode } from "react";

import { NILAI_PENILAIAN, unduhEkspor, type Pemanggil } from "../klien";
import type { RingkasanAnalitik } from "../kontrak";
import {
  LABEL_METRIK_TERTUNDA,
  LABEL_NILAI,
  MIKROKOPI,
  angkaDesimal,
  dihitungPada,
  persen,
  waktuUniversal,
} from "../mikrokopi";

/** Unduhan pada peramban — tautan sementara yang langsung dilepas. */
export function simpanBerkas(isi: Blob, nama: string): void {
  const alamat = URL.createObjectURL(isi);
  const tautan = document.createElement("a");
  tautan.href = alamat;
  tautan.download = nama;
  tautan.click();
  URL.revokeObjectURL(alamat);
}

function nilaiAtau(nilai: number | null, ubah: (n: number) => string): string {
  return nilai === null ? MIKROKOPI.belumDapatDihitung : ubah(nilai);
}

function waktuAtau(iso: string | null): string {
  return iso === null ? MIKROKOPI.belumDapatDihitung : waktuUniversal(iso);
}

function Tabel({
  judul,
  kolom,
  baris,
}: {
  readonly judul: string;
  readonly kolom: readonly string[];
  readonly baris: readonly (readonly ReactNode[])[];
}) {
  return (
    <table aria-label={judul}>
      <caption>{judul}</caption>
      <thead>
        <tr>
          {kolom.map((k) => (
            <th key={k} scope="col">
              {k}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {baris.length === 0 ? (
          <tr>
            <td colSpan={kolom.length}>{MIKROKOPI.belumAdaData}</td>
          </tr>
        ) : (
          baris.map((isi, i) => (
            <tr key={i}>
              {isi.map((sel, j) => (
                <td key={j}>{sel}</td>
              ))}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}

function hitungan(judul: string, isi: Readonly<Record<string, number>>) {
  return (
    <Tabel
      baris={Object.entries(isi).map(([kode, n]) => [kode, String(n)])}
      judul={judul}
      kolom={[MIKROKOPI.kolomKode, MIKROKOPI.kolomJumlah]}
    />
  );
}

export function LayarAnalitik({
  awal,
  pemanggil,
  keluar,
  belumMasuk,
  simpan = simpanBerkas,
}: {
  readonly awal: RingkasanAnalitik;
  readonly pemanggil: Pemanggil;
  readonly keluar: () => void;
  readonly belumMasuk: () => void;
  readonly simpan?: (isi: Blob, nama: string) => void;
}) {
  const r = awal;
  const [dari, setDari] = useState("");
  const [sampai, setSampai] = useState("");
  const [pengembangan, setPengembangan] = useState(false);
  const [mengirim, setMengirim] = useState(false);
  const [pesan, setPesan] = useState<string | null>(null);

  async function unduh(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    if (dari === "" || sampai === "" || dari > sampai) {
      setPesan(MIKROKOPI.eksporRentang);
      return;
    }
    setPesan(null);
    setMengirim(true);
    const hasil = await unduhEkspor({ dari, sampai, termasuk_pengembangan: pengembangan }, pemanggil);
    setMengirim(false);
    if (hasil.jenis === "berkas") {
      simpan(hasil.isi, hasil.nama);
      return;
    }
    if (hasil.galat === "belum_masuk") {
      belumMasuk();
      return;
    }
    setPesan(
      hasil.galat === "pertanyaan_ditolak"
        ? MIKROKOPI.eksporRentang
        : hasil.galat === "luring"
          ? MIKROKOPI.eksporLuring
          : MIKROKOPI.eksporGangguan,
    );
  }

  const k = r.keterlibatan;
  return (
    <main className="layar-tanya layar-analitik">
      <h1>{MIKROKOPI.judulAnalitik}</h1>
      <button className="tombol-kedua" onClick={keluar} type="button">
        {MIKROKOPI.tombolKeluar}
      </button>
      <p className="keterangan">{dihitungPada(r.dihitung_pada)}</p>
      <p className="keterangan">{MIKROKOPI.keteranganTanggalAnalitik}</p>

      <section>
        <h2>{MIKROKOPI.judulKeterlibatan}</h2>
        <Tabel
          baris={k.aktif_harian.map((h) => [h.tanggal, String(h.pengguna)])}
          judul={MIKROKOPI.judulAktifHarian}
          kolom={[MIKROKOPI.kolomTanggal, MIKROKOPI.kolomPengguna]}
        />
        <Tabel
          baris={k.aktif_mingguan.map((m) => [m.mulai, String(m.pengguna)])}
          judul={MIKROKOPI.judulAktifMingguan}
          kolom={[MIKROKOPI.kolomMulaiPekan, MIKROKOPI.kolomPengguna]}
        />
        <p className="keterangan">{MIKROKOPI.keteranganRetensi}</p>
        <Tabel
          baris={k.retensi.map((x) => [
            String(x.hari),
            String(x.kohort),
            String(x.kembali),
            nilaiAtau(x.rasio, persen),
          ])}
          judul={MIKROKOPI.judulRetensi}
          kolom={[MIKROKOPI.kolomHariKe, MIKROKOPI.kolomKohort, MIKROKOPI.kolomKembali, MIKROKOPI.kolomRasio]}
        />
        <Tabel
          baris={[
            [MIKROKOPI.labelJumlahSesi, String(k.sesi.jumlah)],
            [MIKROKOPI.labelMedianMenit, nilaiAtau(k.sesi.median_menit, angkaDesimal)],
            [MIKROKOPI.labelRerataMenit, nilaiAtau(k.sesi.rerata_menit, angkaDesimal)],
          ]}
          judul={MIKROKOPI.judulSesi}
          kolom={[MIKROKOPI.kolomKode, MIKROKOPI.kolomJumlah]}
        />
      </section>

      <section>
        <Tabel
          baris={[
            [MIKROKOPI.labelDisajikan, String(r.penemuan.disajikan)],
            [MIKROKOPI.labelDibuka, String(r.penemuan.dibuka)],
            [MIKROKOPI.kolomRasio, nilaiAtau(r.penemuan.rasio, persen)],
          ]}
          judul={MIKROKOPI.judulPenemuanAnalitik}
          kolom={[MIKROKOPI.kolomKode, MIKROKOPI.kolomJumlah]}
        />
      </section>

      <section>
        <Tabel
          baris={NILAI_PENILAIAN.map((n) => [LABEL_NILAI[n], String(r.penilaian.per_nilai[n])])}
          judul={MIKROKOPI.judulPenilaianAnalitik}
          kolom={[MIKROKOPI.kolomNilai, MIKROKOPI.kolomJumlah]}
        />
      </section>

      <section>
        <Tabel
          baris={[
            [MIKROKOPI.labelJawabanDisajikan, String(r.penelusuran_sumber.jawaban)],
            [MIKROKOPI.labelSumberDibuka, String(r.penelusuran_sumber.dibuka)],
            [MIKROKOPI.kolomRasio, nilaiAtau(r.penelusuran_sumber.rasio, persen)],
          ]}
          judul={MIKROKOPI.judulPenelusuranAnalitik}
          kolom={[MIKROKOPI.kolomKode, MIKROKOPI.kolomJumlah]}
        />
      </section>

      <section>
        <h2>{MIKROKOPI.judulBelumTerukur}</h2>
        <dl>
          {r.belum_terukur.map((b) => (
            <div key={b.metrik}>
              <dt>{LABEL_METRIK_TERTUNDA[b.metrik]}</dt>
              <dd>{b.sebab}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section>
        <h2>{MIKROKOPI.judulIntegritas}</h2>
        <Tabel
          baris={[
            [MIKROKOPI.labelPertama, waktuAtau(r.integritas.pertama)],
            [MIKROKOPI.labelTerakhir, waktuAtau(r.integritas.terakhir)],
            [MIKROKOPI.labelPengembangan, String(r.integritas.pengembangan)],
          ]}
          judul={MIKROKOPI.judulIntegritas}
          kolom={[MIKROKOPI.kolomKode, MIKROKOPI.kolomJumlah]}
        />
        {hitungan(MIKROKOPI.judulPerJenis, r.integritas.per_jenis)}
        {hitungan(MIKROKOPI.judulPerVersiAplikasi, r.integritas.per_versi_aplikasi)}
        {hitungan(MIKROKOPI.judulPerVersiModel, r.integritas.per_versi_model)}
      </section>

      <section>
        <h2>{MIKROKOPI.judulEkspor}</h2>
        <p className="keterangan">{MIKROKOPI.keteranganEkspor}</p>
        <form className="isian-pertanyaan" onSubmit={(e) => void unduh(e)}>
          <label htmlFor="ekspor-dari">{MIKROKOPI.labelDari}</label>
          <input id="ekspor-dari" onChange={(e) => setDari(e.target.value)} type="date" value={dari} />
          <label htmlFor="ekspor-sampai">{MIKROKOPI.labelSampai}</label>
          <input id="ekspor-sampai" onChange={(e) => setSampai(e.target.value)} type="date" value={sampai} />
          <label>
            <input checked={pengembangan} onChange={(e) => setPengembangan(e.target.checked)} type="checkbox" />
            {MIKROKOPI.labelTermasukPengembangan}
          </label>
          <button disabled={mengirim} type="submit">
            {MIKROKOPI.tombolUnduhCsv}
          </button>
        </form>
        {pesan !== null && (
          <div className="galat" role="alert">
            {pesan}
          </div>
        )}
      </section>
    </main>
  );
}
