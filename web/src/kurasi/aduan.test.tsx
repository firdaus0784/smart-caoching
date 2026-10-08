/**
 * S-17 Aduan jawaban dan cangkang kurator — T-7 fitur 036, R-06; D-05 0.7,
 * D-14 Bagian 4.9.
 */

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";

import { Aplikasi } from "../Aplikasi";
import type { Simpanan } from "../draf";
import { JALUR_ADUAN, JALUR_ANTREAN, JALUR_PROFIL, jalurTindakLanjut, type Pemanggil } from "../klien";
import type { AduanTampil } from "../kontrak";
import { LABEL_TINDAK_LANJUT, MIKROKOPI, PENANDA_DASAR } from "../mikrokopi";

afterEach(cleanup);

function simpananPeta(): Simpanan {
  const isi = new Map<string, string>();
  return {
    getItem: (k) => isi.get(k) ?? null,
    setItem: (k, v) => void isi.set(k, v),
    removeItem: (k) => void isi.delete(k),
  };
}

const ADUAN: AduanTampil = {
  nomor: 12,
  diadukan_pada: "2026-10-08T03:00:00Z",
  pertanyaan: "Bagaimana menyusun jadwal supervisi?",
  alasan: "Pasalnya sudah diubah.",
  tanggapan: {
    status_dasar: "kuat",
    ringkasan_tindakan: ["Susun jadwal supervisi bersama guru."],
    penjelasan: "Supervisi akademik dilakukan terjadwal.",
    klaim: [],
    sitasi: [],
    bacaan_lanjutan: [],
    catatan_keberlakuan: "",
    penafian: "Keputusan akhir berada pada kepala sekolah.",
    versi: { model: "m", indeks: "i", kode: "k" },
  },
};

interface Peladen {
  aduan: AduanTampil[];
  panggilan: string[];
  badan: unknown[];
  jawabTindak: () => Response;
  pemanggil: Pemanggil;
}

function peladen(awal: AduanTampil[] = [ADUAN]): Peladen {
  const p: Peladen = {
    aduan: awal,
    panggilan: [],
    badan: [],
    jawabTindak: () => new Response(JSON.stringify({ aduan: p.aduan })),
    pemanggil: async () => new Response("{}", { status: 500 }),
  };
  p.pemanggil = async (jalur, init) => {
    p.panggilan.push(`${init?.method ?? "GET"} ${jalur}`);
    if (typeof init?.body === "string") p.badan.push(JSON.parse(init.body));
    if (jalur === JALUR_PROFIL) return new Response("{}", { status: 403 });
    if (jalur === JALUR_ANTREAN) return new Response(JSON.stringify({ menunggu: [], tayang: [] }));
    if (jalur === JALUR_ADUAN) return new Response(JSON.stringify({ aduan: p.aduan }));
    if (p.aduan.some((a) => jalur === jalurTindakLanjut(a.nomor))) {
      p.aduan = [];
      return p.jawabTindak();
    }
    return new Response("{}", { status: 500 });
  };
  return p;
}

async function bukaAduan(p: Peladen): Promise<void> {
  render(<Aplikasi pemanggil={p.pemanggil} salin={async () => undefined} simpanan={simpananPeta()} />);
  await screen.findByRole("heading", { name: MIKROKOPI.judulKurasi });
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolAduanJawaban }));
  await screen.findByRole("heading", { level: 1, name: MIKROKOPI.judulAduan });
}

async function kartu(): Promise<HTMLElement> {
  const teks = await screen.findByText(ADUAN.pertanyaan);
  const satu = teks.closest("li");
  if (satu === null) throw new Error("kartu aduan tidak ditemukan");
  return satu;
}

describe("cangkang kurator", () => {
  test("dua tombol setara, tanpa navigasi pengguna; aduan dimuat saat dibuka", async () => {
    const p = peladen();
    await bukaAduan(p);
    expect(screen.getByRole("button", { name: MIKROKOPI.tombolAntreanKurasi })).toBeTruthy();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(p.panggilan).toContain(`GET ${JALUR_ADUAN}`);
  });

  test("kembali ke antrean", async () => {
    await bukaAduan(peladen());
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolAntreanKurasi }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulKurasi })).toBeTruthy();
  });
});

describe("S-17", () => {
  test("kartu: waktu, pertanyaan, alasan, jawaban saat itu tanpa tindakan", async () => {
    await bukaAduan(peladen());
    const satu = await kartu();
    expect(within(satu).getByText(ADUAN.alasan as string)).toBeTruthy();
    expect(within(satu).getByText(MIKROKOPI.keteranganJawabanSaatItu)).toBeTruthy();
    expect(within(satu).getByText(PENANDA_DASAR.kuat)).toBeTruthy();
    expect(within(satu).queryByRole("button", { name: MIKROKOPI.tombolSalinRingkasan })).toBeNull();
    expect(within(satu).queryByRole("group", { name: MIKROKOPI.judulNilaiJawaban })).toBeNull();
  });

  test("tanpa alasan dan antrean kosong bernama", async () => {
    await bukaAduan(peladen([{ ...ADUAN, alasan: null }]));
    expect(within(await kartu()).getByText(MIKROKOPI.tanpaAlasanAduan)).toBeTruthy();
    cleanup();
    await bukaAduan(peladen([]));
    expect(await screen.findByText(MIKROKOPI.aduanKosong)).toBeTruthy();
  });

  test("tindak lanjut terkirim dan aduan keluar dari daftar", async () => {
    const p = peladen();
    await bukaAduan(p);
    const satu = await kartu();
    fireEvent.click(within(satu).getByLabelText(LABEL_TINDAK_LANJUT.jawaban_sesuai_dasar));
    fireEvent.change(within(satu).getByLabelText(MIKROKOPI.labelCatatanTindakLanjut), {
      target: { value: "Dasar hukumnya sudah sesuai." },
    });
    fireEvent.click(within(satu).getByRole("button", { name: MIKROKOPI.tombolSimpanTindakLanjut }));
    expect(await screen.findByText(MIKROKOPI.aduanKosong)).toBeTruthy();
    expect(p.badan).toEqual([{ tindak_lanjut: "jawaban_sesuai_dasar", catatan: "Dasar hukumnya sudah sesuai." }]);
  });

  test("tanpa pilihan atau catatan tidak dikirim", async () => {
    const p = peladen();
    await bukaAduan(p);
    const satu = await kartu();
    fireEvent.change(within(satu).getByLabelText(MIKROKOPI.labelCatatanTindakLanjut), {
      target: { value: "   " },
    });
    fireEvent.click(within(satu).getByLabelText(LABEL_TINDAK_LANJUT.di_luar_cakupan));
    fireEvent.click(within(satu).getByRole("button", { name: MIKROKOPI.tombolSimpanTindakLanjut }));
    expect(await within(satu).findByText(MIKROKOPI.tindakLanjutDitolak)).toBeTruthy();
    expect(p.panggilan.filter((c) => c.startsWith("POST"))).toEqual([]);
  });

  test("404: daftar dimuat ulang dan kurator diberi tahu", async () => {
    const p = peladen();
    p.jawabTindak = () => new Response("{}", { status: 404 });
    await bukaAduan(p);
    const satu = await kartu();
    fireEvent.click(within(satu).getByLabelText(LABEL_TINDAK_LANJUT.butir_ditarik));
    fireEvent.change(within(satu).getByLabelText(MIKROKOPI.labelCatatanTindakLanjut), {
      target: { value: "Butir sudah ditarik." },
    });
    fireEvent.click(within(satu).getByRole("button", { name: MIKROKOPI.tombolSimpanTindakLanjut }));
    expect(await screen.findByText(MIKROKOPI.aduanSudahDiambil)).toBeTruthy();
    await waitFor(() => expect(p.panggilan.filter((c) => c === `GET ${JALUR_ADUAN}`)).toHaveLength(2));
  });

  test("R-06: aduan yang membawa penaut ditolak klien", async () => {
    const p = peladen([{ ...ADUAN, tanggapan: { ...ADUAN.tanggapan, id_pesan: "msg_1" } as AduanTampil["tanggapan"] }]);
    await bukaAduan(p);
    expect(await screen.findByText(MIKROKOPI.aduanGangguan)).toBeTruthy();
    expect(screen.queryByText(ADUAN.pertanyaan)).toBeNull();
  });
});
