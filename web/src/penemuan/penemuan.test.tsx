/**
 * S-05 Beranda dan S-06 Detail butir — T-7 fitur 013, R-06, R-11, R-12, R-13, P-7.
 *
 * Ketujuh keadaan D-05 Bagian 7 diuji sebagai perilaku layar, bukan sebagai
 * keberadaan komponen. Peladen palsu menjawab bentuk D-14 Bagian 4.6.
 */

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import type { Simpanan } from "../draf";
import {
  JALUR_BERANDA,
  TAJUK_TUJUAN,
  TUJUAN_SALINAN,
  apakahBeranda,
  jalurButir,
  jalurTolakButir,
  type Pemanggil,
} from "../klien";
import type { Beranda, ButirLengkap, ButirRingkas } from "../kontrak";
import { LABEL_JENIS_SUMBER, MIKROKOPI, waktuBaca } from "../mikrokopi";
import { LayarBeranda } from "./LayarBeranda";
import { LayarButir } from "./LayarButir";
import { hapusSalinan, salinanBeranda, salinanButir, simpanBeranda, simpanButir } from "./salinan";

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

const RINGKAS: ButirRingkas = {
  id_butir: "b-1",
  kategori: "K1",
  jenis_sumber: "riset",
  judul: "Supervisi akademik terjadwal",
  alasan_relevansi: "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
  perkiraan_waktu_baca: 4,
};

const LENGKAP: ButirLengkap = {
  ...RINGKAS,
  inti_temuan: "Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
  implikasi_tindakan: ["Susun jadwal supervisi satu semester.", "Bagikan jadwal kepada guru."],
  tenggat_terkait: null,
  boleh_teks_penuh: true,
  sumber: { judul: "Laporan supervisi", penerbit: "Penerbit", tahun: 2025, tautan: "https://contoh.go.id/a" },
};

const BERISI: Beranda = { keadaan: "berisi", butir: [RINGKAS] };

function json(isi: unknown, status = 200): Response {
  return new Response(JSON.stringify(isi), { status });
}

/** Peladen palsu: jawaban per jalur, dan pencatat panggilan. */
function peladen(jawab: Record<string, () => Response | Promise<Response>>) {
  const panggilan: string[] = [];
  const badan: unknown[] = [];
  const tujuan: (string | null)[] = [];
  const pemanggil: Pemanggil = async (jalur, init) => {
    panggilan.push(`${init?.method ?? "GET"} ${jalur}`);
    tujuan.push(new Headers(init?.headers).get(TAJUK_TUJUAN));
    if (typeof init?.body === "string") badan.push(JSON.parse(init.body));
    const satu = jawab[jalur];
    if (satu === undefined) return json({}, 500);
    return satu();
  };
  return { pemanggil, panggilan, badan, tujuan };
}

const luring = () => Promise.reject(new TypeError("Failed to fetch"));

function beranda(pemanggil: Pemanggil, simpanan: Simpanan | null = simpananPeta()) {
  const buka = vi.fn();
  const keTanya = vi.fn();
  const belumMasuk = vi.fn();
  render(
    <LayarBeranda
      belumMasuk={belumMasuk}
      buka={buka}
      keTanya={keTanya}
      pemanggil={pemanggil}
      simpanan={simpanan}
    />,
  );
  return { buka, keTanya, belumMasuk };
}

// ── S-05 ─────────────────────────────────────────────────────────────

test("KL-A: kerangka kartu selama memuat, bukan pemutar", () => {
  beranda(() => new Promise(() => undefined));
  expect(screen.getByRole("status").textContent).toBe(MIKROKOPI.berandaMemuat);
  expect(screen.getByTestId("kerangka-beranda").getAttribute("aria-busy")).toBe("true");
});

test("berisi: kartu menyebut jenis sumber, judul, alasan, waktu baca — tanpa kode kategori", async () => {
  const { buka } = beranda(peladen({ [JALUR_BERANDA]: () => json(BERISI) }).pemanggil);
  const kartu = await screen.findByRole("button", { name: new RegExp(RINGKAS.judul) });
  expect(kartu.textContent).toContain(LABEL_JENIS_SUMBER.riset);
  expect(kartu.textContent).toContain(RINGKAS.alasan_relevansi);
  expect(kartu.textContent).toContain(waktuBaca(4));
  expect(document.body.textContent).not.toMatch(/\bK1\b/);
  fireEvent.click(kartu);
  expect(buka).toHaveBeenCalledWith("b-1");
});

test.each([
  ["belum_ada_prioritas", MIKROKOPI.berandaBelumPrioritas],
  ["belum_ada_butir", MIKROKOPI.berandaBelumAda],
  ["habis", MIKROKOPI.berandaHabis],
] as const)("KL-B dan KL-C: keadaan %s menjelaskan, bukan sekadar kosong", async (keadaan, kalimat) => {
  beranda(peladen({ [JALUR_BERANDA]: () => json({ keadaan, butir: [] }) }).pemanggil);
  expect(await screen.findByText(kalimat)).toBeTruthy();
  expect(screen.queryAllByRole("listitem")).toHaveLength(0);
});

test("jalur cepat ke Tanya", async () => {
  const { keTanya } = beranda(peladen({ [JALUR_BERANDA]: () => json(BERISI) }).pemanggil);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolTanyaCepat }));
  expect(keTanya).toHaveBeenCalled();
});

test("KL-D: galat sistem dengan satu tindakan pemulihan", async () => {
  let kali = 0;
  beranda(
    peladen({
      [JALUR_BERANDA]: () => (++kali === 1 ? json({}, 500) : json(BERISI)),
    }).pemanggil,
  );
  expect((await screen.findByRole("alert")).textContent).toContain(MIKROKOPI.berandaGangguan);
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolCobaLagi }));
  expect(await screen.findByRole("button", { name: new RegExp(RINGKAS.judul) })).toBeTruthy();
});

test("tanggapan yang bentuknya tidak dikenali ditolak utuh", async () => {
  beranda(peladen({ [JALUR_BERANDA]: () => json({ ...BERISI, lebih: 1 }) }).pemanggil);
  expect((await screen.findByRole("alert")).textContent).toContain(MIKROKOPI.berandaGangguan);
});

test("KL-E: luring menampilkan salinan terakhir beserta keterangannya", async () => {
  const simpanan = simpananPeta();
  simpanBeranda(simpanan, BERISI);
  beranda(luring, simpanan);
  expect(await screen.findByText(MIKROKOPI.berandaLuringSalinan)).toBeTruthy();
  expect(screen.getByRole("button", { name: new RegExp(RINGKAS.judul) })).toBeTruthy();
});

test("KL-E: luring tanpa salinan mengatakannya", async () => {
  beranda(luring);
  expect(await screen.findByText(MIKROKOPI.berandaLuringKosong)).toBeTruthy();
});

test("401 menyerahkan ke cangkang", async () => {
  const { belumMasuk } = beranda(peladen({ [JALUR_BERANDA]: () => json({}, 401) }).pemanggil);
  await waitFor(() => expect(belumMasuk).toHaveBeenCalled());
});

test("P-7: beranda dan isi lengkap butirnya disimpan setelah dimuat", async () => {
  const simpanan = simpananPeta();
  beranda(
    peladen({
      [JALUR_BERANDA]: () => json(BERISI),
      [jalurButir("b-1")]: () => json(LENGKAP),
    }).pemanggil,
    simpanan,
  );
  await screen.findByRole("button", { name: new RegExp(RINGKAS.judul) });
  await waitFor(() => expect(salinanButir(simpanan, "b-1")).toEqual(LENGKAP));
  expect(salinanBeranda(simpanan)).toEqual(BERISI);
});

test("K-7 fitur 034: pengambilan latar bagi salinan bertanda salinan, beranda tidak", async () => {
  const p = peladen({
    [JALUR_BERANDA]: () => json(BERISI),
    [jalurButir("b-1")]: () => json(LENGKAP),
  });
  beranda(p.pemanggil);
  await waitFor(() => expect(p.panggilan).toContain(`GET ${jalurButir("b-1")}`));
  const latar = p.panggilan.indexOf(`GET ${jalurButir("b-1")}`);
  expect(p.tujuan[latar]).toBe(TUJUAN_SALINAN);
  expect(p.tujuan[p.panggilan.indexOf(`GET ${JALUR_BERANDA}`)]).toBeNull();
  expect(TAJUK_TUJUAN).toBe("X-Tujuan");
  expect(TUJUAN_SALINAN).toBe("salinan");
});

// ── S-06 ─────────────────────────────────────────────────────────────

function detail(pemanggil: Pemanggil, simpanan: Simpanan | null = simpananPeta()) {
  const kembali = vi.fn();
  const belumMasuk = vi.fn();
  render(
    <LayarButir
      belumMasuk={belumMasuk}
      idButir="b-1"
      kembali={kembali}
      pemanggil={pemanggil}
      simpanan={simpanan}
    />,
  );
  return { kembali, belumMasuk };
}

test("blok S-06 berurutan: jenis sumber, judul, mengapa relevan di atas isi, waktu, inti, implikasi, sumber", async () => {
  detail(peladen({ [jalurButir("b-1")]: () => json(LENGKAP) }).pemanggil);
  await screen.findByRole("heading", { level: 1, name: LENGKAP.judul });
  const teks = document.body.textContent ?? "";
  const urutan = [
    LABEL_JENIS_SUMBER.riset,
    LENGKAP.judul,
    MIKROKOPI.judulMengapaRelevan,
    LENGKAP.alasan_relevansi,
    waktuBaca(4),
    MIKROKOPI.judulIntiTemuan,
    LENGKAP.inti_temuan,
    MIKROKOPI.judulImplikasi,
    MIKROKOPI.judulSumber,
  ].map((bagian) => teks.indexOf(bagian));
  expect(urutan.every((i) => i >= 0)).toBe(true);
  expect([...urutan].sort((a, b) => a - b)).toEqual(urutan);
  expect(screen.getAllByRole("listitem").map((l) => l.textContent)).toEqual([...LENGKAP.implikasi_tindakan]);
  const tautan = screen.getByRole("link", { name: MIKROKOPI.bukaHalamanSumber });
  expect(tautan.getAttribute("href")).toBe(LENGKAP.sumber.tautan);
  expect(tautan.getAttribute("rel")).toContain("noopener");
});

test("C-02: boleh_teks_penuh false menyatakan teks lengkap tidak ditampilkan", async () => {
  detail(
    peladen({ [jalurButir("b-1")]: () => json({ ...LENGKAP, boleh_teks_penuh: false }) }).pemanggil,
  );
  expect(await screen.findByText(MIKROKOPI.teksPenuhTertutup)).toBeTruthy();
});

test("boleh_teks_penuh true tidak menampilkan kalimat lisensi tertutup", async () => {
  detail(peladen({ [jalurButir("b-1")]: () => json(LENGKAP) }).pemanggil);
  await screen.findByRole("heading", { level: 1, name: LENGKAP.judul });
  expect(screen.queryByText(MIKROKOPI.teksPenuhTertutup)).toBeNull();
});

test("tanpa tautan, tidak ada tautan sumber", async () => {
  detail(
    peladen({
      [jalurButir("b-1")]: () => json({ ...LENGKAP, sumber: { ...LENGKAP.sumber, tautan: null } }),
    }).pemanggil,
  );
  await screen.findByRole("heading", { level: 1, name: LENGKAP.judul });
  expect(screen.queryByRole("link")).toBeNull();
});

test("K-7 fitur 034: membuka butir tidak bertanda salinan — itulah yang tercatat dibuka", async () => {
  const p = peladen({ [jalurButir("b-1")]: () => json(LENGKAP) });
  detail(p.pemanggil);
  await screen.findByRole("heading", { level: 1, name: LENGKAP.judul });
  expect(p.panggilan).toEqual([`GET ${jalurButir("b-1")}`]);
  expect(p.tujuan).toEqual([null]);
});

test("KL-G: butir yang sudah tidak tersedia adalah keadaan sah, bukan galat", async () => {
  const { kembali } = detail(peladen({ [jalurButir("b-1")]: () => json({}, 404) }).pemanggil);
  expect(await screen.findByText(MIKROKOPI.butirTidakAda)).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKembaliBeranda }));
  expect(kembali).toHaveBeenCalled();
});

test("KL-E: detail luring dibaca dari salinan", async () => {
  const simpanan = simpananPeta();
  simpanBeranda(simpanan, BERISI);
  simpanButir(simpanan, LENGKAP);
  detail(luring, simpanan);
  expect(await screen.findByText(MIKROKOPI.butirLuringSalinan)).toBeTruthy();
  expect(screen.getByRole("heading", { level: 1, name: LENGKAP.judul })).toBeTruthy();
});

test("KL-E: detail luring tanpa salinan", async () => {
  detail(luring);
  expect(await screen.findByText(MIKROKOPI.butirLuringKosong)).toBeTruthy();
});

test("KL-D: galat sistem pada detail dengan Coba lagi", async () => {
  let kali = 0;
  detail(
    peladen({ [jalurButir("b-1")]: () => (++kali === 1 ? json({}, 500) : json(LENGKAP)) }).pemanggil,
  );
  expect((await screen.findByRole("alert")).textContent).toContain(MIKROKOPI.butirGangguan);
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolCobaLagi }));
  expect(await screen.findByRole("heading", { level: 1, name: LENGKAP.judul })).toBeTruthy();
});

test("FR-G07: belum relevan mengirim alasan lalu kembali ke beranda", async () => {
  const p = peladen({
    [jalurButir("b-1")]: () => json(LENGKAP),
    [jalurTolakButir("b-1")]: () => json({ keadaan: "habis", butir: [] }),
  });
  const { kembali } = detail(p.pemanggil);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolBelumRelevan }));
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelAlasanBelumRelevan), {
    target: { value: "Belum menjadi prioritas semester ini" },
  });
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKirimAlasan }));
  await waitFor(() => expect(kembali).toHaveBeenCalled());
  expect(p.badan).toEqual([{ alasan: "Belum menjadi prioritas semester ini" }]);
});

test("alasan kosong tidak dikirim", async () => {
  const p = peladen({ [jalurButir("b-1")]: () => json(LENGKAP) });
  detail(p.pemanggil);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolBelumRelevan }));
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKirimAlasan }));
  expect(await screen.findByText(MIKROKOPI.alasanDitolak)).toBeTruthy();
  expect(p.panggilan.filter((c) => c.startsWith("POST"))).toHaveLength(0);
});

test.each([
  [() => json({}, 400), MIKROKOPI.alasanDitolak],
  [luring, MIKROKOPI.alasanLuring],
  [() => json({}, 500), MIKROKOPI.alasanGangguan],
] as const)("KL-F: alasan yang tidak terkirim tetap di isian", async (jawab, kalimat) => {
  detail(peladen({ [jalurButir("b-1")]: () => json(LENGKAP), [jalurTolakButir("b-1")]: jawab }).pemanggil);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolBelumRelevan }));
  const isian = screen.getByLabelText(MIKROKOPI.labelAlasanBelumRelevan);
  fireEvent.change(isian, { target: { value: "Tidak sesuai jenjang" } });
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKirimAlasan }));
  expect(await screen.findByText(kalimat)).toBeTruthy();
  expect((isian as HTMLTextAreaElement).value).toBe("Tidak sesuai jenjang");
});

test("Batal menutup isian tanpa mengirim", async () => {
  const p = peladen({ [jalurButir("b-1")]: () => json(LENGKAP) });
  detail(p.pemanggil);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolBelumRelevan }));
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolBatal }));
  expect(screen.queryByLabelText(MIKROKOPI.labelAlasanBelumRelevan)).toBeNull();
  expect(p.panggilan.filter((c) => c.startsWith("POST"))).toHaveLength(0);
});

test("401 pada detail menyerahkan ke cangkang", async () => {
  const { belumMasuk } = detail(peladen({ [jalurButir("b-1")]: () => json({}, 401) }).pemanggil);
  await waitFor(() => expect(belumMasuk).toHaveBeenCalled());
});

// ── C-15 dan salinan ─────────────────────────────────────────────────

test("C-15: tidak ada poin, lencana, runtun, maupun peringkat pada kedua layar", async () => {
  beranda(peladen({ [JALUR_BERANDA]: () => json(BERISI) }).pemanggil);
  await screen.findByRole("button", { name: new RegExp(RINGKAS.judul) });
  cleanup();
  detail(peladen({ [jalurButir("b-1")]: () => json(LENGKAP) }).pemanggil);
  await screen.findByRole("heading", { level: 1, name: LENGKAP.judul });
  expect(document.body.textContent?.toLowerCase()).not.toMatch(/poin|lencana|runtun|peringkat/);
});

test("salinan rusak dibaca kosong, dan dapat dihapus", () => {
  const simpanan = simpananPeta();
  simpanan.setItem("smart-coaching:beranda", "{rusak");
  expect(salinanBeranda(simpanan)).toBeNull();
  simpanBeranda(simpanan, BERISI);
  expect(salinanBeranda(simpanan)).toEqual(BERISI);
  hapusSalinan(simpanan);
  expect(salinanBeranda(simpanan)).toBeNull();
  expect(simpanButir(simpanan, LENGKAP)).toBe(false);
  expect(simpanBeranda(null, BERISI)).toBe(false);
  expect(apakahBeranda({ keadaan: "lain", butir: [] })).toBe(false);
});
