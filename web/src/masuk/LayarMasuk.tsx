/**
 * Layar S-01 Masuk — T-8 fitur 029, R-08, D-05 S-01.
 *
 * Akun dibuatkan tim peneliti; tidak ada pendaftaran mandiri (FR-A01) dan
 * tidak ada pemulihan lewat surel (P-7). Sandi tidak disimpan di mana pun oleh
 * kode ini: isiannya dikosongkan begitu dikirim, dan komponen ini tidak
 * menerima simpanan peramban sama sekali. Pengelola sandi peramban tetap
 * pilihan pengguna; atribut `autocomplete` membantunya.
 */

import { useState, type FormEvent } from "react";

import { masuk, type Pemanggil } from "../klien";
import { MIKROKOPI } from "../mikrokopi";

export interface PropertiLayarMasuk {
  readonly pemanggil: Pemanggil;
  readonly berhasil: () => void;
  /** Kalimat dari cangkang, misalnya sesudah sesi berakhir di tengah pemakaian. */
  readonly pemberitahuan?: string | null;
}

export function LayarMasuk({ pemanggil, berhasil, pemberitahuan = null }: PropertiLayarMasuk) {
  const [nama, setNama] = useState("");
  const [sandi, setSandi] = useState("");
  const [memeriksa, setMemeriksa] = useState(false);
  const [pesan, setPesan] = useState<string | null>(null);

  async function ajukan(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    if (memeriksa) return;
    const namaBersih = nama.trim();
    if (namaBersih === "" || sandi === "") {
      setPesan(MIKROKOPI.masukKosong);
      return;
    }
    const isian = sandi;
    // R-08: sandi tidak dipertahankan sesudah dikirim, berhasil maupun tidak.
    setSandi("");
    setMemeriksa(true);
    const hasil = await masuk(namaBersih, isian, pemanggil);
    setMemeriksa(false);
    if (hasil.jenis === "masuk") {
      berhasil();
      return;
    }
    if (hasil.jenis === "ditolak") setPesan(MIKROKOPI.masukDitolak);
    else setPesan(hasil.galat === "luring" ? MIKROKOPI.masukLuring : MIKROKOPI.masukGangguan);
  }

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulMasuk}</h1>
      {pemberitahuan !== null && <p role="status">{pemberitahuan}</p>}

      <form className="isian-pertanyaan" onSubmit={(e) => void ajukan(e)}>
        <label htmlFor="nama-pengguna">{MIKROKOPI.labelNamaPengguna}</label>
        <p className="petunjuk" id="petunjuk-nama-pengguna">
          {MIKROKOPI.petunjukNamaPengguna}
        </p>
        <input
          aria-describedby="petunjuk-nama-pengguna"
          autoCapitalize="none"
          autoComplete="username"
          autoCorrect="off"
          id="nama-pengguna"
          onChange={(e) => setNama(e.target.value)}
          spellCheck={false}
          type="text"
          value={nama}
        />
        <label htmlFor="sandi">{MIKROKOPI.labelSandi}</label>
        <input
          autoCapitalize="none"
          autoComplete="current-password"
          autoCorrect="off"
          id="sandi"
          onChange={(e) => setSandi(e.target.value)}
          spellCheck={false}
          type="password"
          value={sandi}
        />
        <button disabled={memeriksa} type="submit">
          {MIKROKOPI.tombolMasuk}
        </button>
      </form>

      {pesan !== null && (
        <div className="galat" role="alert">
          {pesan}
        </div>
      )}

      <p className="petunjuk">{MIKROKOPI.lupaSandi}</p>
    </main>
  );
}
