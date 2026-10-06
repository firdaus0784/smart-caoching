/**
 * Layar S-04 Profil dan prioritas — T-5 fitur 030, FR-A02, FR-A03, K-7.
 *
 * Tepat enam isian profil, lalu tiga sampai lima prioritas yang urutannya
 * adalah urutan pilihan pengguna. Label kategori diambil dari D-03 Bagian 5
 * apa adanya; kode K1 s.d. K8 tidak pernah tampil (M-11).
 *
 * Batasnya ditegakkan peladen lewat model fitur 022; yang diperiksa di sini
 * hanya jumlah prioritas, agar permintaan yang pasti ditolak tidak dikirim.
 */

import { useState, type FormEvent } from "react";

import { simpanProfil, tetapkanPrioritas, type Pemanggil } from "../klien";
import type { JalurAkreditasi, Ringkasan } from "../kontrak";
import { LABEL_KATEGORI, MIKROKOPI } from "../mikrokopi";

type Kode = keyof typeof LABEL_KATEGORI;

const KODE = Object.keys(LABEL_KATEGORI) as Kode[];

export function LayarProfil({
  pemanggil,
  selesai,
  awal = null,
  labelSimpan = MIKROKOPI.tombolSimpanProfil,
}: {
  readonly pemanggil: Pemanggil;
  readonly selesai: () => void;
  /** Fitur 033 (FR-A06): isian terisi dari ringkasan saat disunting dari S-14. */
  readonly awal?: Ringkasan | null;
  readonly labelSimpan?: string;
}) {
  const profil = awal?.profil ?? null;
  const [jabatan, setJabatan] = useState(profil?.jabatan ?? "");
  const [masaKerja, setMasaKerja] = useState(profil === null ? "" : String(profil.masa_kerja));
  const [rombel, setRombel] = useState(profil === null ? "" : String(profil.jumlah_rombel));
  const [ptk, setPtk] = useState(profil === null ? "" : String(profil.jumlah_ptk));
  const [jalur, setJalur] = useState<JalurAkreditasi | null>(profil?.jalur_akreditasi ?? null);
  const [wilayah, setWilayah] = useState(profil?.wilayah ?? "");
  const [pilihan, setPilihan] = useState<readonly Kode[]>(() =>
    (awal?.prioritas ?? []).filter((k): k is Kode => k in LABEL_KATEGORI),
  );
  const [pesan, setPesan] = useState<string | null>(null);
  const [mengirim, setMengirim] = useState(false);

  function centang(kode: Kode) {
    setPilihan((lama) => (lama.includes(kode) ? lama.filter((k) => k !== kode) : [...lama, kode]));
  }

  async function simpan(peristiwa: FormEvent<HTMLFormElement>) {
    peristiwa.preventDefault();
    if (pilihan.length < 3 || pilihan.length > 5) {
      setPesan(MIKROKOPI.prioritasJumlah);
      return;
    }
    if (jalur === null) {
      setPesan(MIKROKOPI.profilDitolak);
      return;
    }
    setMengirim(true);
    const profil = await simpanProfil(
      {
        jabatan,
        masa_kerja: Number(masaKerja),
        jumlah_rombel: Number(rombel),
        jumlah_ptk: Number(ptk),
        jalur_akreditasi: jalur,
        wilayah,
      },
      pemanggil,
    );
    if (profil.jenis === "galat") {
      setMengirim(false);
      setPesan(profil.galat === "pertanyaan_ditolak" ? MIKROKOPI.profilDitolak : MIKROKOPI.profilGangguan);
      return;
    }
    const prioritas = await tetapkanPrioritas(pilihan, pemanggil);
    setMengirim(false);
    if (prioritas.jenis === "galat") {
      setPesan(
        prioritas.galat === "pertanyaan_ditolak" ? MIKROKOPI.prioritasDitolak : MIKROKOPI.profilGangguan,
      );
      return;
    }
    selesai();
  }

  const angka = (id: string, label: string, nilai: string, ubah: (v: string) => void) => (
    <>
      <label htmlFor={id}>{label}</label>
      <input id={id} inputMode="numeric" min={0} onChange={(e) => ubah(e.target.value)} type="number" value={nilai} />
    </>
  );

  return (
    <main className="layar-tanya">
      <h1>{MIKROKOPI.judulProfil}</h1>
      <form className="isian-pertanyaan" onSubmit={(e) => void simpan(e)}>
        <div className="isian-pertanyaan" data-testid="isian-profil">
          <label htmlFor="jabatan">{MIKROKOPI.labelJabatan}</label>
          <input id="jabatan" onChange={(e) => setJabatan(e.target.value)} type="text" value={jabatan} />
          {angka("masa-kerja", MIKROKOPI.labelMasaKerja, masaKerja, setMasaKerja)}
          {angka("jumlah-rombel", MIKROKOPI.labelJumlahRombel, rombel, setRombel)}
          {angka("jumlah-ptk", MIKROKOPI.labelJumlahPtk, ptk, setPtk)}
          <fieldset>
            <legend>{MIKROKOPI.labelJalurAkreditasi}</legend>
            <label>
              <input
                checked={jalur === "visitasi"}
                name="jalur"
                onChange={() => setJalur("visitasi")}
                type="radio"
              />
              {MIKROKOPI.jalurVisitasi}
            </label>
            <label>
              <input
                checked={jalur === "automasi"}
                name="jalur"
                onChange={() => setJalur("automasi")}
                type="radio"
              />
              {MIKROKOPI.jalurAutomasi}
            </label>
          </fieldset>
          <label htmlFor="wilayah">{MIKROKOPI.labelWilayah}</label>
          <input id="wilayah" onChange={(e) => setWilayah(e.target.value)} type="text" value={wilayah} />
        </div>

        <fieldset>
          <legend>{MIKROKOPI.judulPrioritas}</legend>
          <p className="petunjuk">{MIKROKOPI.petunjukPrioritas}</p>
          {KODE.map((kode) => {
            const urutan = pilihan.indexOf(kode);
            return (
              <label key={kode}>
                <input
                  checked={urutan >= 0}
                  disabled={urutan < 0 && pilihan.length >= 5}
                  onChange={() => centang(kode)}
                  type="checkbox"
                />
                {urutan >= 0 ? `${urutan + 1}. ${LABEL_KATEGORI[kode]}` : LABEL_KATEGORI[kode]}
              </label>
            );
          })}
        </fieldset>

        <button disabled={mengirim} type="submit">
          {labelSimpan}
        </button>
      </form>
      {pesan !== null && (
        <div className="galat" role="alert">
          {pesan}
        </div>
      )}
    </main>
  );
}
