/**
 * S-15 Antrean kurasi, S-16 Penyuntingan, cangkang kurator — T-8 fitur 013,
 * R-09, R-11, R-12; K-6, K-8; D-14 Bagian 4.7.
 */

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";

import { Aplikasi } from "../Aplikasi";
import type { Simpanan } from "../draf";
import { JALUR_ANTREAN, JALUR_KELUAR, JALUR_PROFIL, jalurPutusan, jalurTarik, type Pemanggil } from "../klien";
import type { Antrean, KandidatTampil, TayangTampil } from "../kontrak";
import { LABEL_ALASAN_TOLAK, LABEL_KATEGORI, LABEL_PEMICU, LABEL_STATUS, MIKROKOPI } from "../mikrokopi";

afterEach(cleanup);

function simpananPeta(): Simpanan {
  const isi = new Map<string, string>();
  return {
    getItem: (k) => isi.get(k) ?? null,
    setItem: (k, v) => void isi.set(k, v),
    removeItem: (k) => void isi.delete(k),
  };
}

const KANDIDAT: KandidatTampil = {
  id_butir: "b-1",
  kategori: "K1",
  jenis_sumber: "regulasi",
  judul: "Supervisi akademik terjadwal",
  alasan_relevansi: "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
  inti_temuan: "Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
  implikasi_tindakan: ["Susun jadwal supervisi satu semester."],
  perkiraan_waktu_baca: 4,
  tenggat_terkait: null,
  lisensi: "CC-BY",
  status_keberlakuan: "berlaku",
  sumber: { judul: "Permendikdasmen", penerbit: "Kemendikdasmen", tahun: 2025, tautan: null },
  masuk_pada: "2026-10-05T01:00:00Z",
};

const KANDIDAT_K5: KandidatTampil = {
  ...KANDIDAT,
  id_butir: "b-2",
  kategori: "K5",
  jenis_sumber: "riset",
  judul: "Pembiayaan sekolah yang transparan",
  status_keberlakuan: null,
};

const TAYANG: TayangTampil = {
  id_butir: "b-9",
  kategori: "K1",
  jenis_sumber: "regulasi",
  judul: "Penilaian kinerja guru",
  lisensi: "CC-BY",
  status_keberlakuan: "berlaku",
  tayang_pada: "2026-10-04T01:00:00Z",
  perlu_tinjauan: false,
};

interface Peladen {
  antrean: Antrean;
  badan: unknown[];
  panggilan: string[];
  jawabPutusan: () => Response | Promise<Response>;
  pemanggil: Pemanggil;
}

function peladen(awal: Antrean = { menunggu: [KANDIDAT, KANDIDAT_K5], tayang: [TAYANG] }): Peladen {
  const p: Peladen = {
    antrean: awal,
    badan: [],
    panggilan: [],
    jawabPutusan: () => new Response(JSON.stringify(p.antrean)),
    pemanggil: async () => new Response("{}", { status: 500 }),
  };
  p.pemanggil = async (jalur, init) => {
    p.panggilan.push(`${init?.method ?? "GET"} ${jalur}`);
    if (typeof init?.body === "string") p.badan.push(JSON.parse(init.body));
    if (jalur === JALUR_KELUAR) return new Response(null, { status: 204 });
    if (jalur === JALUR_PROFIL) return new Response("{}", { status: 403 });
    if (jalur === JALUR_ANTREAN) return new Response(JSON.stringify(p.antrean));
    // Dicocokkan lewat fungsi klien, bukan awalan harfiah: pemeriksa rute
    // menolak untai jalur yang tidak terpasang, termasuk pada uji (R-16).
    const ids = [...p.antrean.menunggu, ...p.antrean.tayang].map((b) => b.id_butir);
    if (ids.some((id) => jalur === jalurPutusan(id) || jalur === jalurTarik(id))) {
      if (ids.some((id) => jalur === jalurPutusan(id))) {
        p.antrean = { ...p.antrean, menunggu: p.antrean.menunggu.slice(1) };
      } else {
        p.antrean = { ...p.antrean, tayang: [] };
      }
      return p.jawabPutusan();
    }
    return new Response("{}", { status: 500 });
  };
  return p;
}

function pasang(p: { pemanggil: Pemanggil }) {
  return render(<Aplikasi pemanggil={p.pemanggil} salin={async () => undefined} simpanan={simpananPeta()} />);
}

async function baris(judul: string): Promise<HTMLElement> {
  const kepala = await screen.findByRole("heading", { name: judul });
  const satu = kepala.closest("li");
  if (satu === null) throw new Error("baris tidak ditemukan");
  return satu;
}

// ── K-8 · cangkang ───────────────────────────────────────────────────

describe("cangkang kurator", () => {
  test("ringkasan akun 403 lalu antrean 200: S-15, tanpa navigasi pengguna", async () => {
    const p = peladen();
    pasang(p);
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulKurasi })).toBeTruthy();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(p.panggilan.slice(0, 2)).toEqual([`GET ${JALUR_PROFIL}`, `GET ${JALUR_ANTREAN}`]);
  });

  test("akun yang ditolak keduanya: kalimat dan tombol keluar saja", async () => {
    pasang({
      pemanggil: async (jalur) =>
        jalur === JALUR_KELUAR ? new Response(null, { status: 204 }) : new Response("{}", { status: 403 }),
    });
    expect(await screen.findByText(MIKROKOPI.akunTidakDikenali)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKeluar }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulMasuk })).toBeTruthy();
  });
});

test.each([
  [() => new Response("{}", { status: 500 }), MIKROKOPI.kurasiGangguan],
  [() => Promise.reject(new TypeError("Failed to fetch")), MIKROKOPI.kurasiLuring],
] as const)("cangkang kurator: antrean gagal dimuat, dengan Coba lagi", async (jawab, kalimat) => {
  let kali = 0;
  const p = peladen();
  const asli = p.pemanggil;
  pasang({
    pemanggil: async (jalur, init) =>
      jalur === JALUR_ANTREAN && ++kali === 1 ? jawab() : asli(jalur, init),
  });
  expect((await screen.findByRole("alert")).textContent).toContain(kalimat);
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolCobaLagi }));
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulKurasi })).toBeTruthy();
});

// ── S-15 ─────────────────────────────────────────────────────────────

describe("S-15 antrean", () => {
  test("dikelompokkan menurut kategori, berlabel D-03, tanpa kode maupun skor", async () => {
    pasang(peladen());
    await screen.findByRole("heading", { name: MIKROKOPI.judulKurasi });
    expect(screen.getByRole("heading", { name: LABEL_KATEGORI.K1 })).toBeTruthy();
    expect(screen.getByRole("heading", { name: LABEL_KATEGORI.K5 })).toBeTruthy();
    const teks = document.body.textContent ?? "";
    expect(teks).not.toMatch(/\bK[1-8]\b|\bTL-\d+|skor/i);
  });

  test("baris memuat judul, jenis sumber, lisensi, status regulasi", async () => {
    pasang(peladen());
    const satu = await baris(KANDIDAT.judul);
    expect(satu.textContent).toContain("Regulasi");
    expect(satu.textContent).toContain(KANDIDAT.lisensi);
    expect(satu.textContent).toContain(LABEL_STATUS.berlaku);
    expect(satu.textContent).toContain(KANDIDAT.inti_temuan);
  });

  test("empat putusan setara bentuknya", async () => {
    pasang(peladen());
    const satu = within(await baris(KANDIDAT.judul));
    const kelas = [MIKROKOPI.tombolSetujui, MIKROKOPI.tombolSunting, MIKROKOPI.tombolTolak, MIKROKOPI.tombolTunda].map(
      (nama) => satu.getByRole("button", { name: nama }).className,
    );
    expect(new Set(kelas).size).toBe(1);
  });

  test("Setujui menuntut catatan, lalu mengirim jenis dan catatan saja", async () => {
    const p = peladen();
    pasang(p);
    const satu = within(await baris(KANDIDAT.judul));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolSetujui }));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    expect(await satu.findByText(MIKROKOPI.putusanBelumLengkap)).toBeTruthy();
    expect(p.badan).toEqual([]);
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "Layak tayang" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    await waitFor(() => expect(screen.queryByRole("heading", { name: KANDIDAT.judul })).toBeNull());
    expect(p.badan).toEqual([{ jenis: "setujui", catatan: "Layak tayang" }]);
    expect(p.panggilan).toContain(`POST ${jalurPutusan("b-1")}`);
  });

  test("Tolak memilih alasan baku menurut kalimatnya; kodenya yang dikirim", async () => {
    const p = peladen();
    pasang(p);
    const satu = within(await baris(KANDIDAT.judul));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolTolak }));
    fireEvent.click(satu.getByLabelText(LABEL_ALASAN_TOLAK["TL-04"]));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    await waitFor(() => expect(p.badan).toEqual([{ jenis: "tolak", alasan_tolak: "TL-04" }]));
  });

  test("Tunda mengirim tanggal kembali dan catatan", async () => {
    const p = peladen();
    pasang(p);
    const satu = within(await baris(KANDIDAT.judul));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolTunda }));
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelKembaliPada), { target: { value: "2026-10-12" } });
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "Tunggu juknis" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    await waitFor(() =>
      expect(p.badan).toEqual([{ jenis: "tunda", catatan: "Tunggu juknis", kembali_pada: "2026-10-12" }]),
    );
  });

  test.each([
    [400, MIKROKOPI.putusanDitolak],
    [500, MIKROKOPI.putusanGangguan],
  ])("penolakan %s: kalimat tanpa kode, baris tetap", async (status, kalimat) => {
    const p = peladen();
    p.jawabPutusan = () => new Response("{}", { status });
    pasang(p);
    const satu = within(await baris(KANDIDAT.judul));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolSetujui }));
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "x" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    expect(await satu.findByText(kalimat)).toBeTruthy();
    expect(screen.getByRole("heading", { name: KANDIDAT.judul })).toBeTruthy();
  });

  test("butir yang sudah diputus orang lain: daftar dimuat ulang", async () => {
    const p = peladen();
    p.jawabPutusan = () => new Response("{}", { status: 404 });
    pasang(p);
    const satu = within(await baris(KANDIDAT.judul));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolSetujui }));
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "x" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    expect(await screen.findByText(MIKROKOPI.putusanSudahDiambil)).toBeTruthy();
    expect(p.panggilan.filter((x) => x === `GET ${JALUR_ANTREAN}`)).toHaveLength(2);
  });

  test("luring: putusan belum terkirim dinyatakan", async () => {
    const p = peladen();
    p.jawabPutusan = () => Promise.reject(new TypeError("Failed to fetch"));
    pasang(p);
    const satu = within(await baris(KANDIDAT.judul));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolSetujui }));
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "x" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    expect(await satu.findByText(MIKROKOPI.kurasiLuring)).toBeTruthy();
  });

  test("KL-B: antrean dan daftar tayang kosong", async () => {
    pasang(peladen({ menunggu: [], tayang: [] }));
    expect(await screen.findByText(MIKROKOPI.antreanKosong)).toBeTruthy();
    expect(screen.getByText(MIKROKOPI.tayangKosong)).toBeTruthy();
  });
});

// ── S-16 ─────────────────────────────────────────────────────────────

describe("S-16 penyuntingan", () => {
  test("empat bidang parafrase saja; lainnya tampil tanpa isian", async () => {
    pasang(peladen());
    fireEvent.click(within(await baris(KANDIDAT.judul)).getByRole("button", { name: MIKROKOPI.tombolSunting }));
    await screen.findByRole("heading", { name: MIKROKOPI.judulSunting });
    const isian = [...document.querySelectorAll("input, textarea")].map((e) => e.id).sort();
    expect(isian).toEqual(["sunting-alasan", "sunting-catatan", "sunting-implikasi", "sunting-inti", "sunting-judul"]);
    expect(document.body.textContent).toContain(KANDIDAT.lisensi);
    expect(document.body.textContent).toContain(MIKROKOPI.keteranganTetap);
  });

  test("Simpan dan setujui mengirim suntingan; implikasi per baris", async () => {
    const p = peladen();
    pasang(p);
    fireEvent.click(within(await baris(KANDIDAT.judul)).getByRole("button", { name: MIKROKOPI.tombolSunting }));
    await screen.findByRole("heading", { name: MIKROKOPI.judulSunting });
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelJudul), { target: { value: "Jadwal supervisi" } });
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelImplikasi), {
      target: { value: "Tetapkan jadwal.\n\n Bagikan jadwal kepada guru. " },
    });
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "Parafrase diperbaiki" } });
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolSimpanSetujui }));
    await screen.findByRole("heading", { name: MIKROKOPI.judulKurasi });
    expect(p.badan).toEqual([
      {
        jenis: "sunting_lalu_setujui",
        catatan: "Parafrase diperbaiki",
        suntingan: {
          judul: "Jadwal supervisi",
          alasan_relevansi: KANDIDAT.alasan_relevansi,
          inti_temuan: KANDIDAT.inti_temuan,
          implikasi_tindakan: ["Tetapkan jadwal.", "Bagikan jadwal kepada guru."],
        },
      },
    ]);
  });

  test("Batal kembali ke antrean tanpa mengirim", async () => {
    const p = peladen();
    pasang(p);
    fireEvent.click(within(await baris(KANDIDAT.judul)).getByRole("button", { name: MIKROKOPI.tombolSunting }));
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolBatal }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulKurasi })).toBeTruthy();
    expect(p.badan).toEqual([]);
  });
});

// ── penarikan ────────────────────────────────────────────────────────

describe("penarikan dari daftar tayang", () => {
  async function bukaTarik(p: Peladen) {
    pasang(p);
    const satu = within(await baris(TAYANG.judul));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolTarik }));
    return satu;
  }

  test("regulasi berubah menuntut status sekarang", async () => {
    const p = peladen();
    const satu = await bukaTarik(p);
    fireEvent.click(satu.getByLabelText(LABEL_PEMICU.regulasi_sumber_berubah));
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "Permen dicabut" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    expect(await satu.findByText(MIKROKOPI.putusanBelumLengkap)).toBeTruthy();
    fireEvent.click(satu.getByLabelText(LABEL_STATUS.dicabut));
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    await waitFor(() =>
      expect(p.badan).toEqual([
        { pemicu: "regulasi_sumber_berubah", catatan: "Permen dicabut", status_terkini: "dicabut" },
      ]),
    );
    expect(p.panggilan).toContain(`POST ${jalurTarik("b-9")}`);
  });

  test("pembaruan data membawa tanda perubahan bermakna", async () => {
    const p = peladen();
    const satu = await bukaTarik(p);
    fireEvent.click(satu.getByLabelText(LABEL_PEMICU.data_sumber_diperbarui));
    fireEvent.click(satu.getByLabelText(MIKROKOPI.labelAngkaBermakna));
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "Data 2026" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    await waitFor(() =>
      expect(p.badan).toEqual([
        { pemicu: "data_sumber_diperbarui", catatan: "Data 2026", angka_berubah_bermakna: true },
      ]),
    );
  });

  test("isi keliru: pemicu dan catatan saja", async () => {
    const p = peladen();
    const satu = await bukaTarik(p);
    fireEvent.click(satu.getByLabelText(LABEL_PEMICU.kekeliruan_isi_dilaporkan));
    fireEvent.change(satu.getByLabelText(MIKROKOPI.labelCatatan), { target: { value: "Angka keliru" } });
    fireEvent.click(satu.getByRole("button", { name: MIKROKOPI.tombolKirimPutusan }));
    await waitFor(() =>
      expect(p.badan).toEqual([{ pemicu: "kekeliruan_isi_dilaporkan", catatan: "Angka keliru" }]),
    );
    expect(await screen.findByText(MIKROKOPI.tayangKosong)).toBeTruthy();
  });

  test("tanda perlu tinjauan tampil sebagai kalimat", async () => {
    pasang(peladen({ menunggu: [], tayang: [{ ...TAYANG, perlu_tinjauan: true }] }));
    expect(await screen.findByText(MIKROKOPI.perluTinjauan)).toBeTruthy();
  });
});
