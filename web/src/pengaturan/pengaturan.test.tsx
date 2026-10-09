/**
 * S-14 Pengaturan — T-6 fitur 033, FR-A06, NFR-09, RE-04, K-6, P-4, P-5.
 *
 * Diuji lewat cangkang sungguhan: tombol Pengaturan berada di samping Keluar,
 * profil dan prioritas disimpan lewat rute fitur 030, dan penarikan data
 * tidak terkirim sebelum dikonfirmasi.
 */

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { Aplikasi } from "../Aplikasi";
import type { Simpanan } from "../draf";
import {
  JALUR_BERANDA,
  JALUR_DATA_SAYA,
  JALUR_NASKAH,
  JALUR_NASKAH_PENARIKAN,
  JALUR_PERCAKAPAN,
  JALUR_PERSETUJUAN,
  JALUR_PRIORITAS,
  JALUR_PROFIL,
  type Pemanggil,
} from "../klien";
import type { PermintaanProfil, Ringkasan } from "../kontrak";
import { DATA_DITARIK, DATA_TIDAK_DITARIK, LABEL_KATEGORI, MIKROKOPI } from "../mikrokopi";
import { salinanBeranda, simpanBeranda } from "../penemuan/salinan";

afterEach(cleanup);

function simpananPeta(): Simpanan & { readonly isi: Map<string, string> } {
  const isi = new Map<string, string>();
  return {
    isi,
    getItem: (k) => isi.get(k) ?? null,
    setItem: (k, v) => void isi.set(k, v),
    removeItem: (k) => void isi.delete(k),
  };
}

const PROFIL: PermintaanProfil = {
  jabatan: "Kepala Sekolah",
  masa_kerja: 3,
  jumlah_rombel: 6,
  jumlah_ptk: 9,
  jalur_akreditasi: "visitasi",
  wilayah: "Kabupaten Sumedang",
};

const NASKAH_PERSETUJUAN = { versi: "et02-uji", judul: "Lembar uji", paragraf: ["Paragraf uji."] };
const NASKAH_PENARIKAN = {
  versi: "penarikan-uji",
  judul: "Penjelasan uji dari tim",
  paragraf: ["Paragraf penjelasan uji dari tim."],
};

interface Peladen {
  ringkasan: Ringkasan;
  naskahPenarikan: typeof NASKAH_PENARIKAN | null;
  tarik: () => Promise<Response>;
  panggilan: string[];
  badan: Record<string, unknown>[];
  pemanggil: Pemanggil;
}

function peladen(): Peladen {
  const p: Peladen = {
    ringkasan: { profil: PROFIL, prioritas: ["K5", "K1", "K7"], persetujuan: "diberikan" },
    naskahPenarikan: null,
    tarik: async () => new Response(null, { status: 202 }),
    panggilan: [],
    badan: [],
    pemanggil: async () => new Response(null, { status: 500 }),
  };
  p.pemanggil = async (jalur, init) => {
    const metode = init?.method ?? "GET";
    p.panggilan.push(`${metode} ${jalur}`);
    const badan = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : {};
    if (init?.body) p.badan.push(badan);
    const json = (isi: unknown) => new Response(JSON.stringify(isi), { status: 200 });
    if (jalur === JALUR_NASKAH) return json(NASKAH_PERSETUJUAN);
    if (jalur === JALUR_NASKAH_PENARIKAN) {
      return p.naskahPenarikan === null
        ? new Response("<!doctype html>", { status: 200 })
        : json(p.naskahPenarikan);
    }
    if (jalur === JALUR_PROFIL && metode === "GET") return json(p.ringkasan);
    if (jalur === JALUR_PROFIL && metode === "PUT") {
      p.ringkasan = { ...p.ringkasan, profil: badan as unknown as PermintaanProfil };
      return json(p.ringkasan);
    }
    if (jalur === JALUR_PRIORITAS) {
      p.ringkasan = { ...p.ringkasan, prioritas: badan["kategori"] as string[] };
      return json(p.ringkasan);
    }
    if (jalur === JALUR_PERSETUJUAN) {
      p.ringkasan = { ...p.ringkasan, persetujuan: badan["cabut"] ? "dicabut" : "diberikan" };
      return json(p.ringkasan);
    }
    if (jalur === JALUR_DATA_SAYA && metode === "DELETE") return p.tarik();
    if (jalur === JALUR_BERANDA) return json({ keadaan: "belum_ada_butir", butir: [] });
    if (jalur === JALUR_PERCAKAPAN) return json({ percakapan: [] });
    return new Response("{}", { status: 404 });
  };
  return p;
}

function tombol(nama: string): HTMLElement {
  return screen.getByRole("button", { name: nama });
}

async function bukaPengaturan(p: Peladen, simpanan = simpananPeta()) {
  render(<Aplikasi pemanggil={p.pemanggil} salin={async () => undefined} simpanan={simpanan} />);
  await screen.findByRole("heading", { name: MIKROKOPI.judulBeranda });
  fireEvent.click(tombol(MIKROKOPI.tombolPengaturan));
  await screen.findByRole("heading", { level: 1, name: MIKROKOPI.judulPengaturan });
  return simpanan;
}

const tarikan = (p: Peladen) => p.panggilan.filter((c) => c.startsWith("DELETE"));

// ── letak — P-5 ────────────────────────────────────────────────────────

test("P-5: Pengaturan di samping Keluar, bukan tujuan navigasi utama", async () => {
  const p = peladen();
  render(<Aplikasi pemanggil={p.pemanggil} salin={async () => undefined} simpanan={simpananPeta()} />);
  await screen.findByRole("heading", { name: MIKROKOPI.judulBeranda });
  const pengaturan = tombol(MIKROKOPI.tombolPengaturan);
  expect(pengaturan.parentElement).toBe(tombol(MIKROKOPI.tombolKeluar).parentElement);
  const nav = screen.getByRole("navigation", { name: MIKROKOPI.labelNavigasi });
  // Tiga tujuan sejak fitur 032 (R-10); Pengaturan tidak termasuk.
  expect([...nav.querySelectorAll("button")].map((b) => b.textContent)).not.toContain(
    MIKROKOPI.tombolPengaturan,
  );
});

test("Pengaturan juga terbuka dari Tanya, dan Kembali menutupnya", async () => {
  const p = peladen();
  render(<Aplikasi pemanggil={p.pemanggil} salin={async () => undefined} simpanan={simpananPeta()} />);
  await screen.findByRole("heading", { name: MIKROKOPI.judulBeranda });
  fireEvent.click(tombol(MIKROKOPI.navTanya));
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolPengaturan }));
  await screen.findByRole("heading", { level: 1, name: MIKROKOPI.judulPengaturan });
  fireEvent.click(tombol(MIKROKOPI.tombolKembali));
  // Kembali ke tempat ia dibuka, bukan ke Beranda.
  await screen.findByRole("heading", { level: 1, name: MIKROKOPI.judulLayar });
});

// ── profil dan prioritas — FR-A06, R-07 ───────────────────────────────

test("R-07: formulir terisi dari ringkasan, tersimpan lewat rute fitur 030", async () => {
  const p = peladen();
  await bukaPengaturan(p);
  fireEvent.click(tombol(MIKROKOPI.tombolUbahProfil));
  const wilayah = await screen.findByLabelText<HTMLInputElement>(MIKROKOPI.labelWilayah);
  expect(wilayah.value).toBe(PROFIL.wilayah);
  expect(screen.getByLabelText<HTMLInputElement>(MIKROKOPI.labelJabatan).value).toBe(PROFIL.jabatan);
  expect(screen.getByLabelText<HTMLInputElement>(MIKROKOPI.jalurVisitasi).checked).toBe(true);
  expect(screen.getByLabelText<HTMLInputElement>(`1. ${LABEL_KATEGORI.K5}`).checked).toBe(true);
  expect(screen.getByLabelText<HTMLInputElement>(`3. ${LABEL_KATEGORI.K7}`).checked).toBe(true);

  fireEvent.change(wilayah, { target: { value: "Kota Bandung" } });
  fireEvent.click(tombol(MIKROKOPI.tombolSimpanPerubahan));
  await screen.findByText(MIKROKOPI.profilTersimpan);
  expect(p.panggilan).toContain(`PUT ${JALUR_PROFIL}`);
  expect(p.panggilan).toContain(`PUT ${JALUR_PRIORITAS}`);
  expect(p.ringkasan.profil?.wilayah).toBe("Kota Bandung");
  expect(p.ringkasan.prioritas).toEqual(["K5", "K1", "K7"]);
});

// ── persetujuan ───────────────────────────────────────────────────────

test("persetujuan terlihat dan dapat dicabut, lalu kembali ke Pengaturan", async () => {
  const p = peladen();
  await bukaPengaturan(p);
  expect(screen.getByText(MIKROKOPI.sudahSetuju)).toBeTruthy();
  fireEvent.click(tombol(MIKROKOPI.tautanPersetujuan));
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolCabut }));
  await screen.findByRole("heading", { level: 1, name: MIKROKOPI.judulPengaturan });
  expect(p.ringkasan.persetujuan).toBe("dicabut");
});

// ── penarikan — R-05, R-06 ────────────────────────────────────────────

test("R-06: daftar yang dihapus dan yang tidak, sebelum apa pun dikirim", async () => {
  const p = peladen();
  await bukaPengaturan(p);
  // Fitur 032 (R-08): koleksi dan catatannya disebut di antara yang ditarik.
  expect(DATA_DITARIK.filter((d) => /koleksi/i.test(d))).toHaveLength(1);
  for (const butir of [...DATA_DITARIK, ...DATA_TIDAK_DITARIK]) {
    expect(screen.getByText(butir)).toBeTruthy();
  }
  expect(tarikan(p)).toEqual([]);
});

test("M-9: tidak terkirim sebelum konfirmasi; dua pilihan setara; Batal tidak mengirim", async () => {
  const p = peladen();
  await bukaPengaturan(p);
  fireEvent.click(tombol(MIKROKOPI.tombolTarikData));
  const ya = await screen.findByRole("button", { name: MIKROKOPI.tombolYaTarik });
  const batal = tombol(MIKROKOPI.tombolBatal);
  expect(ya.className).toBe(batal.className);
  expect(ya.getAttribute("type")).toBe(batal.getAttribute("type"));
  expect(screen.getByText(MIKROKOPI.konfirmasiPenarikan)).toBeTruthy();
  expect(tarikan(p)).toEqual([]);
  fireEvent.click(batal);
  expect(screen.queryByRole("button", { name: MIKROKOPI.tombolYaTarik })).toBeNull();
  expect(tarikan(p)).toEqual([]);
});

test("diterima: konfirmasi tegas terkirim, peramban dibersihkan, kembali ke Masuk", async () => {
  const p = peladen();
  const simpanan = simpananPeta();
  simpanBeranda(simpanan, { keadaan: "belum_ada_butir", butir: [] });
  await bukaPengaturan(p, simpanan);
  fireEvent.click(tombol(MIKROKOPI.tombolTarikData));
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolYaTarik }));
  await screen.findByText(MIKROKOPI.penarikanDiterima);
  await screen.findByRole("heading", { name: MIKROKOPI.tombolMasuk });
  expect(tarikan(p)).toEqual([`DELETE ${JALUR_DATA_SAYA}`]);
  expect(p.badan.at(-1)).toEqual({ konfirmasi: true });
  expect(salinanBeranda(simpanan)).toBeNull();
});

test("KL-E: luring tidak diantrekan dan mengatakannya", async () => {
  const p = peladen();
  p.tarik = () => Promise.reject(new TypeError("Failed to fetch"));
  await bukaPengaturan(p);
  fireEvent.click(tombol(MIKROKOPI.tombolTarikData));
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolYaTarik }));
  await screen.findByText(MIKROKOPI.penarikanLuring);
  expect(tarikan(p)).toHaveLength(1);
  expect(screen.getByRole("heading", { level: 1, name: MIKROKOPI.judulPengaturan })).toBeTruthy();
});

test("KL-D: galat sistem dengan satu tindakan pemulihan", async () => {
  const p = peladen();
  p.tarik = async () => new Response("{}", { status: 500 });
  await bukaPengaturan(p);
  fireEvent.click(tombol(MIKROKOPI.tombolTarikData));
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolYaTarik }));
  await screen.findByText(MIKROKOPI.penarikanGangguan);
  p.tarik = async () => new Response(null, { status: 202 });
  fireEvent.click(tombol(MIKROKOPI.tombolYaTarik));
  await screen.findByText(MIKROKOPI.penarikanDiterima);
});

test("401 saat menarik menyerahkan ke layar Masuk", async () => {
  const p = peladen();
  p.tarik = async () => new Response("{}", { status: 401 });
  await bukaPengaturan(p);
  fireEvent.click(tombol(MIKROKOPI.tombolTarikData));
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolYaTarik }));
  await screen.findByRole("heading", { name: MIKROKOPI.tombolMasuk });
  expect(screen.queryByText(MIKROKOPI.penarikanDiterima)).toBeNull();
});

// ── P-4 B · kalimat penjelasan milik tim ─────────────────────────────

test("P-4: penjelasan tim dibaca dari berkasnya bila ada, apa adanya", async () => {
  const p = peladen();
  p.naskahPenarikan = NASKAH_PENARIKAN;
  await bukaPengaturan(p);
  await screen.findByText(NASKAH_PENARIKAN.paragraf[0] ?? "");
  expect(screen.getByRole("heading", { name: NASKAH_PENARIKAN.judul })).toBeTruthy();
});

test("P-4: tanpa berkas tim, penarikan tetap dapat diminta dari daftar", async () => {
  const p = peladen();
  await bukaPengaturan(p);
  await waitFor(() => expect(p.panggilan).toContain(`GET ${JALUR_NASKAH_PENARIKAN}`));
  expect(screen.queryByText(NASKAH_PENARIKAN.paragraf[0] ?? "")).toBeNull();
  expect(tombol(MIKROKOPI.tombolTarikData)).toBeTruthy();
});
