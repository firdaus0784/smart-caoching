/**
 * Layar S-06 Detail butir — T-7 fitur 013, FR-G02, FR-G04, FR-G07, FR-G08, P-7.
 *
 * Urutan blok D-05 Bagian 6: jenis sumber, judul, **mengapa relevan di atas
 * isi**, waktu baca, inti temuan, implikasi tindakan, sumber, tindakan. Blok 8
 * hanya **Belum relevan** pada fitur 013 — Simpan milik baris 032, *knowledge
 * check* milik baris 031.
 *
 * `boleh_teks_penuh` dibaca dari peladen; tanggapan tidak membawa untai
 * lisensi sama sekali, sehingga layar tidak dapat menyimpulkannya (C-02).
 *
 * Keadaan: KL-A kerangka, KL-D Coba lagi, KL-E salinan dari simpanan lokal,
 * KL-F alasan yang belum terkirim tetap di isian, KL-G butir yang sudah tidak
 * tersedia sebagai keadaan sah — bukan galat.
 */

import { useEffect, useState, type FormEvent } from "react";

import type { Simpanan } from "../draf";
import { bacaButir, tolakButir, type Pemanggil } from "../klien";
import type { ButirLengkap } from "../kontrak";
import { LABEL_JENIS_SUMBER, MIKROKOPI, barisSumber, waktuBaca } from "../mikrokopi";
import { salinanButir, simpanButir } from "./salinan";

type Keadaan =
  | { readonly jenis: "memuat" }
  | { readonly jenis: "butir"; readonly butir: ButirLengkap; readonly salinan: boolean }
  | { readonly jenis: "tidak_ada" }
  | { readonly jenis: "luring_kosong" }
  | { readonly jenis: "gangguan" };

export function LayarButir({
  idButir,
  pemanggil,
  simpanan,
  kembali,
  belumMasuk,
}: {
  readonly idButir: string;
  readonly pemanggil: Pemanggil;
  readonly simpanan: Simpanan | null;
  readonly kembali: () => void;
  readonly belumMasuk: () => void;
}) {
  const [keadaan, setKeadaan] = useState<Keadaan>({ jenis: "memuat" });
  const [percobaan, setPercobaan] = useState(0);

  useEffect(() => {
    let berlaku = true;
    void bacaButir(idButir, pemanggil).then((hasil) => {
      if (!berlaku) return;
      if (hasil.jenis === "butir") {
        setKeadaan({ jenis: "butir", butir: hasil.butir, salinan: false });
        simpanButir(simpanan, hasil.butir);
      } else if (hasil.jenis === "tidak_ada") {
        setKeadaan({ jenis: "tidak_ada" });
      } else if (hasil.galat === "belum_masuk") {
        belumMasuk();
      } else if (hasil.galat === "luring") {
        const salinan = salinanButir(simpanan, idButir);
        setKeadaan(
          salinan === null ? { jenis: "luring_kosong" } : { jenis: "butir", butir: salinan, salinan: true },
        );
      } else {
        setKeadaan({ jenis: "gangguan" });
      }
    });
    return () => {
      berlaku = false;
    };
  }, [idButir, pemanggil, percobaan]);

  const tombolKembali = (
    <button className="tombol-kedua" onClick={kembali} type="button">
      {MIKROKOPI.tombolKembaliBeranda}
    </button>
  );

  if (keadaan.jenis === "memuat") {
    return (
      <main className="layar-tanya">
        {tombolKembali}
        <p className="tersembunyi" role="status">
          {MIKROKOPI.butirMemuat}
        </p>
        <div aria-busy="true" className="kerangka">
          <div className="kerangka-penanda" />
          <div className="kerangka-baris" />
          <div className="kerangka-baris pendek" />
        </div>
      </main>
    );
  }
  if (keadaan.jenis !== "butir") {
    return (
      <main className="layar-tanya">
        {tombolKembali}
        {keadaan.jenis === "gangguan" ? (
          <div className="galat" role="alert">
            <p>{MIKROKOPI.butirGangguan}</p>
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
        ) : (
          <section className="kosong">
            <p>
              {keadaan.jenis === "tidak_ada" ? MIKROKOPI.butirTidakAda : MIKROKOPI.butirLuringKosong}
            </p>
          </section>
        )}
      </main>
    );
  }

  const butir = keadaan.butir;
  return (
    <main className="layar-tanya">
      {tombolKembali}
      {keadaan.salinan && <p className="keterangan">{MIKROKOPI.butirLuringSalinan}</p>}
      <article className="blok-jawaban">
        <span className="label-sumber">{LABEL_JENIS_SUMBER[butir.jenis_sumber]}</span>
        <h1>{butir.judul}</h1>
        <section>
          <h2>{MIKROKOPI.judulMengapaRelevan}</h2>
          <p>{butir.alasan_relevansi}</p>
        </section>
        <p className="waktu-baca">{waktuBaca(butir.perkiraan_waktu_baca)}</p>
        <section>
          <h2>{MIKROKOPI.judulIntiTemuan}</h2>
          <p>{butir.inti_temuan}</p>
        </section>
        <section>
          <h2>{MIKROKOPI.judulImplikasi}</h2>
          <ol>
            {butir.implikasi_tindakan.map((satu) => (
              <li key={satu}>{satu}</li>
            ))}
          </ol>
        </section>
        <section>
          <h2>{MIKROKOPI.judulSumber}</h2>
          <p>{barisSumber(butir.sumber.judul, butir.sumber.penerbit, butir.sumber.tahun)}</p>
          {butir.sumber.tautan !== null && (
            <a href={butir.sumber.tautan} rel="noopener noreferrer" target="_blank">
              {MIKROKOPI.bukaHalamanSumber}
            </a>
          )}
          {!butir.boleh_teks_penuh && <p className="keterangan">{MIKROKOPI.teksPenuhTertutup}</p>}
        </section>
      </article>
      <BelumRelevan
        belumMasuk={belumMasuk}
        idButir={butir.id_butir}
        pemanggil={pemanggil}
        selesai={kembali}
        tidakAda={() => setKeadaan({ jenis: "tidak_ada" })}
      />
    </main>
  );
}

function BelumRelevan({
  idButir,
  pemanggil,
  selesai,
  tidakAda,
  belumMasuk,
}: {
  readonly idButir: string;
  readonly pemanggil: Pemanggil;
  readonly selesai: () => void;
  readonly tidakAda: () => void;
  readonly belumMasuk: () => void;
}) {
  const [terbuka, setTerbuka] = useState(false);
  const [alasan, setAlasan] = useState("");
  const [pesan, setPesan] = useState<string | null>(null);
  const [mengirim, setMengirim] = useState(false);

  async function kirim(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    if (alasan.trim() === "") {
      setPesan(MIKROKOPI.alasanDitolak);
      return;
    }
    setMengirim(true);
    const hasil = await tolakButir(idButir, alasan, pemanggil);
    setMengirim(false);
    if (hasil.jenis === "beranda") {
      selesai();
    } else if (hasil.jenis === "tidak_ada") {
      tidakAda();
    } else if (hasil.galat === "belum_masuk") {
      belumMasuk();
    } else if (hasil.galat === "pertanyaan_ditolak") {
      setPesan(MIKROKOPI.alasanDitolak);
    } else if (hasil.galat === "luring") {
      setPesan(MIKROKOPI.alasanLuring);
    } else {
      setPesan(MIKROKOPI.alasanGangguan);
    }
  }

  if (!terbuka) {
    return (
      <div className="tindakan">
        <button onClick={() => setTerbuka(true)} type="button">
          {MIKROKOPI.tombolBelumRelevan}
        </button>
      </div>
    );
  }
  return (
    <form className="isian-pertanyaan" onSubmit={(e) => void kirim(e)}>
      <label htmlFor="alasan-belum-relevan">{MIKROKOPI.labelAlasanBelumRelevan}</label>
      <textarea
        id="alasan-belum-relevan"
        onChange={(e) => setAlasan(e.target.value)}
        rows={2}
        value={alasan}
      />
      {pesan !== null && (
        <p className="galat" role="alert">
          {pesan}
        </p>
      )}
      <div className="tindakan">
        <button disabled={mengirim} type="submit">
          {MIKROKOPI.tombolKirimAlasan}
        </button>
        <button
          className="tombol-kedua"
          onClick={() => {
            setTerbuka(false);
            setPesan(null);
          }}
          type="button"
        >
          {MIKROKOPI.tombolBatal}
        </button>
      </div>
    </form>
  );
}
