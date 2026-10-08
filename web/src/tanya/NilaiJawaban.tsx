/**
 * Blok 6 S-09 "Nilai jawaban" — T-7 fitur 036, FR-F07, R-10, P-2 B; D-05 0.7.
 *
 * Tiga pilihan setara. Centang "kirim kepada kurator" hanya ada bersama
 * `keliru`, dan **kosong kembali** setiap kali nilai berganti: pertanyaan
 * berpindah pembaca hanya atas tindakan pemiliknya pada saat itu, bukan atas
 * centang yang tertinggal dari pilihan sebelumnya.
 *
 * Luring tidak diantrekan — alasan yang sama dengan penarikan data: keputusan
 * menyerahkan pertanyaan kepada orang lain tidak boleh terkirim diam-diam
 * kemudian. Penilaian dapat diganti; yang terakhir berlaku.
 */

import { useId, useState, type FormEvent } from "react";

import { NILAI_PENILAIAN, nilaiJawaban, type Pemanggil } from "../klien";
import type { NilaiPenilaian, StatusDasar } from "../kontrak";
import { LABEL_NILAI, MIKROKOPI } from "../mikrokopi";

export function NilaiJawaban({
  idPesan,
  statusDasar,
  pemanggil,
  belumMasuk,
}: {
  readonly idPesan: string;
  readonly statusDasar: StatusDasar;
  readonly pemanggil: Pemanggil;
  readonly belumMasuk: () => void;
}) {
  const id = useId();
  const [nilai, setNilai] = useState<NilaiPenilaian | null>(null);
  const [alasan, setAlasan] = useState("");
  const [kirim, setKirim] = useState(false);
  const [mengirim, setMengirim] = useState(false);
  const [pesan, setPesan] = useState<string | null>(null);

  function pilih(baru: NilaiPenilaian): void {
    setNilai(baru);
    setKirim(false);
    setPesan(null);
  }

  async function serahkan(
    peristiwa: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    peristiwa.preventDefault();
    if (nilai === null) return;
    const bersih = alasan.trim();
    setMengirim(true);
    const hasil = await nilaiJawaban(
      idPesan,
      {
        nilai,
        alasan: bersih === "" ? null : bersih,
        kirim_ke_kurator: nilai === "keliru" && kirim,
      },
      pemanggil,
    );
    setMengirim(false);
    if (hasil.jenis === "tersimpan") {
      setPesan(MIKROKOPI.penilaianTersimpan);
      return;
    }
    if (hasil.jenis === "tidak_ada") {
      setPesan(MIKROKOPI.penilaianTidakAda);
      return;
    }
    if (hasil.galat === "belum_masuk") {
      belumMasuk();
      return;
    }
    setPesan(
      hasil.galat === "luring"
        ? MIKROKOPI.penilaianLuring
        : hasil.galat === "pertanyaan_ditolak"
          ? MIKROKOPI.penilaianDitolak
          : MIKROKOPI.penilaianGangguan,
    );
  }

  return (
    <form className="nilai-jawaban" onSubmit={(e) => void serahkan(e)}>
      <fieldset>
        <legend>{MIKROKOPI.judulNilaiJawaban}</legend>
        {statusDasar === "tidak_ditemukan" && (
          <button
            className="tombol-kedua"
            onClick={() => pilih("keliru")}
            type="button"
          >
            {MIKROKOPI.tombolLaporkanSeharusnyaAda}
          </button>
        )}
        <div className="pilihan-nilai">
          {NILAI_PENILAIAN.map((n) => (
            <label key={n}>
              <input
                checked={nilai === n}
                name={`${id}-nilai`}
                onChange={() => pilih(n)}
                type="radio"
              />
              {LABEL_NILAI[n]}
            </label>
          ))}
        </div>
        {nilai !== null && (
          <>
            <label htmlFor={`${id}-alasan`}>
              {MIKROKOPI.labelAlasanPenilaian}
            </label>
            <textarea
              aria-describedby={`${id}-petunjuk`}
              id={`${id}-alasan`}
              onChange={(e) => setAlasan(e.target.value)}
              rows={2}
              value={alasan}
            />
            <p className="keterangan" id={`${id}-petunjuk`}>
              {MIKROKOPI.petunjukAlasanPenilaian}
            </p>
          </>
        )}
        {nilai === "keliru" && (
          <>
            <label>
              <input
                checked={kirim}
                onChange={(e) => setKirim(e.target.checked)}
                type="checkbox"
              />
              {MIKROKOPI.labelKirimKeKurator}
            </label>
            <p className="keterangan">{MIKROKOPI.keteranganTanpaKirim}</p>
          </>
        )}
        <button disabled={nilai === null || mengirim} type="submit">
          {MIKROKOPI.tombolKirimPenilaian}
        </button>
        {pesan !== null && <p role="status">{pesan}</p>}
      </fieldset>
    </form>
  );
}
