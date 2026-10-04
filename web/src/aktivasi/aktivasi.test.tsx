import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { Aplikasi } from "../Aplikasi";
import type { Simpanan } from "../draf";
import {
  JALUR_NASKAH,
  JALUR_PERCAKAPAN,
  JALUR_PERSETUJUAN,
  JALUR_PRIORITAS,
  JALUR_PROFIL,
  type Pemanggil,
} from "../klien";
import type { PermintaanProfil, Ringkasan } from "../kontrak";
import { LABEL_KATEGORI, MIKROKOPI, PENGENALAN } from "../mikrokopi";

afterEach(cleanup);

function simpananPeta(): Simpanan {
  const isi = new Map<string, string>();
  return {
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

const NASKAH = { versi: "et02-uji", judul: "Lembar informasi uji", paragraf: ["Paragraf uji satu."] };

interface Peladen {
  ringkasan: Ringkasan;
  naskah: typeof NASKAH | null;
  panggilan: string[];
  badan: Record<string, unknown>[];
  pemanggil: Pemanggil;
}

function peladen(awal: Partial<Ringkasan> = {}, naskah: typeof NASKAH | null = NASKAH): Peladen {
  const p: Peladen = {
    ringkasan: { profil: null, prioritas: [], persetujuan: "belum_diminta", ...awal },
    naskah,
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
    if (jalur === JALUR_NASKAH) {
      return p.naskah === null ? new Response("<!doctype html>", { status: 200 }) : json(p.naskah);
    }
    if (jalur === JALUR_PROFIL && metode === "GET") return json(p.ringkasan);
    if (jalur === JALUR_PROFIL && metode === "PUT") {
      p.ringkasan = { ...p.ringkasan, profil: badan as unknown as PermintaanProfil };
      return json(p.ringkasan);
    }
    if (jalur === JALUR_PRIORITAS) {
      const kategori = badan["kategori"] as string[];
      if (kategori.length < 3 || kategori.length > 5) return new Response("{}", { status: 400 });
      p.ringkasan = { ...p.ringkasan, prioritas: kategori };
      return json(p.ringkasan);
    }
    if (jalur === JALUR_PERSETUJUAN) {
      const persetujuan = badan["cabut"] ? "dicabut" : badan["disetujui"] ? "diberikan" : "ditolak";
      p.ringkasan = { ...p.ringkasan, persetujuan };
      return json(p.ringkasan);
    }
    if (jalur === JALUR_PERCAKAPAN) return json({ percakapan: [] });
    return new Response("{}", { status: 404 });
  };
  return p;
}

function pasang(p: Peladen) {
  return render(
    <Aplikasi pemanggil={p.pemanggil} salin={async () => undefined} simpanan={simpananPeta()} />,
  );
}

function tombol(nama: string): HTMLElement {
  return screen.getByRole("button", { name: nama });
}

async function lewatiPengenalan(): Promise<void> {
  for (let i = 0; i < PENGENALAN.length - 1; i++) {
    await screen.findByRole("heading", { name: PENGENALAN[i]?.judul ?? "" });
    fireEvent.click(tombol(MIKROKOPI.tombolLanjut));
  }
  await screen.findByRole("heading", { name: PENGENALAN.at(-1)?.judul ?? "" });
  fireEvent.click(tombol(MIKROKOPI.tombolMulaiProfil));
}

function isiProfil(): void {
  const isi = (label: string, nilai: string) =>
    fireEvent.change(screen.getByLabelText(label), { target: { value: nilai } });
  isi(MIKROKOPI.labelJabatan, PROFIL.jabatan);
  isi(MIKROKOPI.labelMasaKerja, String(PROFIL.masa_kerja));
  isi(MIKROKOPI.labelJumlahRombel, String(PROFIL.jumlah_rombel));
  isi(MIKROKOPI.labelJumlahPtk, String(PROFIL.jumlah_ptk));
  fireEvent.click(screen.getByLabelText(MIKROKOPI.jalurVisitasi));
  isi(MIKROKOPI.labelWilayah, PROFIL.wilayah);
}

function pilih(...kode: (keyof typeof LABEL_KATEGORI)[]): void {
  for (const k of kode) fireEvent.click(screen.getByLabelText(LABEL_KATEGORI[k]));
}

// ── alur J1 — D-05 Bagian 5.1 ──────────────────────────────────────────

describe("alur aktivasi menurut ringkasan", () => {
  test("pengguna baru: S-02, lalu S-03 empat layar, lalu S-04, lalu Tanya", async () => {
    const p = peladen();
    pasang(p);
    await screen.findByRole("heading", { name: MIKROKOPI.judulPersetujuan });
    expect(screen.getByText(NASKAH.judul)).toBeTruthy();
    fireEvent.click(tombol(MIKROKOPI.tombolSetuju));
    await lewatiPengenalan();
    await screen.findByRole("heading", { name: MIKROKOPI.judulProfil });
    isiProfil();
    pilih("K5", "K1", "K7");
    fireEvent.click(tombol(MIKROKOPI.tombolSimpanProfil));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
    expect(p.ringkasan.persetujuan).toBe("diberikan");
    expect(p.ringkasan.prioritas).toEqual(["K5", "K1", "K7"]);
    expect(p.badan).toContainEqual({ versi_naskah: NASKAH.versi, disetujui: true });
  });

  test("menolak tetap melanjutkan ke pengenalan — FR-A05", async () => {
    const p = peladen();
    pasang(p);
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolTidakSetuju }));
    await screen.findByRole("heading", { name: PENGENALAN[0]?.judul ?? "" });
    expect(p.ringkasan.persetujuan).toBe("ditolak");
  });

  test("sudah aktif: langsung Tanya", async () => {
    pasang(peladen({ profil: PROFIL, prioritas: ["K1", "K2", "K3"], persetujuan: "ditolak" }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
  });

  test("persetujuan sudah diputus tetapi profil belum: pengenalan, bukan S-02", async () => {
    pasang(peladen({ persetujuan: "diberikan" }));
    expect(await screen.findByRole("heading", { name: PENGENALAN[0]?.judul ?? "" })).toBeTruthy();
  });

  test("naskah belum tersedia: S-02 dilewati pada alur, tanpa mencatat apa pun", async () => {
    const p = peladen({}, null);
    pasang(p);
    expect(await screen.findByRole("heading", { name: PENGENALAN[0]?.judul ?? "" })).toBeTruthy();
    expect(p.panggilan.filter((x) => x.startsWith("POST"))).toEqual([]);
  });

  test("K-6: luring saat memeriksa aktivasi membuka Tanya", async () => {
    pasang({
      ...peladen(),
      pemanggil: async () => {
        throw new TypeError("Failed to fetch");
      },
    });
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
  });
});

// ── S-03 · FR-A04 ──────────────────────────────────────────────────────

describe("S-03 pengenalan", () => {
  test("tepat empat layar; layar kedua menyatakan alat bantu, bukan penentu", () => {
    expect(PENGENALAN).toHaveLength(4);
    expect(PENGENALAN[1]?.judul).toBe("Alat bantu, bukan penentu");
  });

  test("M-10: tidak ada jalan pintas melewati layar kedua", async () => {
    pasang(peladen({ persetujuan: "diberikan" }));
    await screen.findByRole("heading", { name: PENGENALAN[0]?.judul ?? "" });
    expect(screen.queryByRole("button", { name: MIKROKOPI.tombolMulaiProfil })).toBeNull();
    fireEvent.click(tombol(MIKROKOPI.tombolLanjut));
    expect(await screen.findByRole("heading", { name: PENGENALAN[1]?.judul ?? "" })).toBeTruthy();
    expect(screen.getByText(PENGENALAN[1]?.isi ?? "")).toBeTruthy();
  });
});

// ── S-04 · FR-A02, FR-A03, K-7 ─────────────────────────────────────────

describe("S-04 profil dan prioritas", () => {
  async function bukaS04(): Promise<Peladen> {
    const p = peladen({ persetujuan: "ditolak" });
    pasang(p);
    await lewatiPengenalan();
    await screen.findByRole("heading", { name: MIKROKOPI.judulProfil });
    return p;
  }

  test("tepat enam isian profil", async () => {
    await bukaS04();
    const form = screen.getByTestId("isian-profil");
    const isian = within(form).getAllByRole("textbox").length + within(form).getAllByRole("spinbutton").length;
    const radio = within(form).getAllByRole("radio");
    expect(isian + (radio.length > 0 ? 1 : 0)).toBe(6);
  });

  test("M-11: prioritas berlabel D-03 apa adanya, tanpa kode K1 s.d. K8", async () => {
    await bukaS04();
    for (const label of Object.values(LABEL_KATEGORI)) expect(screen.getByLabelText(label)).toBeTruthy();
    expect(document.body.textContent ?? "").not.toMatch(/\bK[1-8]\b/);
  });

  test("urutan prioritas mengikuti urutan pilihan", async () => {
    const p = await bukaS04();
    isiProfil();
    pilih("K8", "K2", "K4");
    fireEvent.click(tombol(MIKROKOPI.tombolSimpanProfil));
    await screen.findByRole("heading", { name: MIKROKOPI.judulLayar });
    expect(p.ringkasan.prioritas).toEqual(["K8", "K2", "K4"]);
  });

  test("kurang dari tiga prioritas tidak dikirim", async () => {
    const p = await bukaS04();
    isiProfil();
    pilih("K1", "K2");
    fireEvent.click(tombol(MIKROKOPI.tombolSimpanProfil));
    expect((await screen.findByRole("alert")).textContent).toBe(MIKROKOPI.prioritasJumlah);
    expect(p.panggilan.filter((x) => x.startsWith("PUT"))).toEqual([]);
  });

  test("pilihan keenam tidak dapat dicentang", async () => {
    await bukaS04();
    pilih("K1", "K2", "K3", "K4", "K5");
    const keenam = screen.getByLabelText(LABEL_KATEGORI.K6) as HTMLInputElement;
    expect(keenam.disabled).toBe(true);
  });

  test("profil ditolak peladen: kalimat tanpa kode, tetap di S-04", async () => {
    const p = await bukaS04();
    const asli = p.pemanggil;
    p.pemanggil = async (jalur, init) =>
      jalur === JALUR_PROFIL && init?.method === "PUT"
        ? new Response("{}", { status: 400 })
        : asli(jalur, init);
    cleanup();
    pasang(p);
    await lewatiPengenalan();
    isiProfil();
    pilih("K1", "K2", "K3");
    fireEvent.click(tombol(MIKROKOPI.tombolSimpanProfil));
    expect((await screen.findByRole("alert")).textContent).toBe(MIKROKOPI.profilDitolak);
    expect(screen.getByRole("heading", { name: MIKROKOPI.judulProfil })).toBeTruthy();
  });
});

// ── P-5 · tautan persetujuan dari S-09 ─────────────────────────────────

describe("persetujuan dari layar Tanya", () => {
  test("mencabut sesudah setuju, lalu kembali ke Tanya", async () => {
    const p = peladen({ profil: PROFIL, prioritas: ["K1", "K2", "K3"], persetujuan: "diberikan" });
    pasang(p);
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tautanPersetujuan }));
    expect(await screen.findByText(MIKROKOPI.sudahSetuju)).toBeTruthy();
    fireEvent.click(tombol(MIKROKOPI.tombolCabut));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
    expect(p.badan).toContainEqual({ cabut: true });
  });

  test("setuju sesudah menolak", async () => {
    const p = peladen({ profil: PROFIL, prioritas: ["K1", "K2", "K3"], persetujuan: "ditolak" });
    pasang(p);
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tautanPersetujuan }));
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolSetuju }));
    await screen.findByRole("heading", { name: MIKROKOPI.judulLayar });
    expect(p.ringkasan.persetujuan).toBe("diberikan");
  });

  test("naskah belum tersedia: kalimatnya dan tombol kembali, tanpa tombol setuju", async () => {
    pasang(peladen({ profil: PROFIL, prioritas: ["K1", "K2", "K3"] }, null));
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tautanPersetujuan }));
    expect(await screen.findByText(MIKROKOPI.naskahBelumAda)).toBeTruthy();
    expect(screen.queryByRole("button", { name: MIKROKOPI.tombolSetuju })).toBeNull();
    fireEvent.click(tombol(MIKROKOPI.tombolKembali));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
  });

  test("setuju dan tidak setuju setara bentuknya — tidak ada yang ditonjolkan", async () => {
    pasang(peladen());
    await screen.findByRole("heading", { name: MIKROKOPI.judulPersetujuan });
    expect(tombol(MIKROKOPI.tombolSetuju).className).toBe(tombol(MIKROKOPI.tombolTidakSetuju).className);
  });
});

test("versi naskah dikirim sebagaimana dimuat, bukan ditulis kode", async () => {
  const p = peladen({}, { ...NASKAH, versi: "versi-dari-berkas" });
  pasang(p);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolSetuju }));
  await vi.waitFor(() =>
    expect(p.badan).toContainEqual({ versi_naskah: "versi-dari-berkas", disetujui: true }),
  );
});
