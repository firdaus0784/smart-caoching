import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { Aplikasi } from "./Aplikasi";
import { bacaDraf, simpanDraf, type Simpanan } from "./draf";
import {
  JALUR_BERANDA,
  JALUR_KELUAR,
  JALUR_MASUK,
  JALUR_PERCAKAPAN,
  JALUR_PROFIL,
  JALUR_TANYA,
  jalurButir,
  type Pemanggil,
} from "./klien";
import { MIKROKOPI } from "./mikrokopi";
import { percakapanAktif } from "./percakapan";

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

/** Peladen palsu: sesi sah atau tidak, dan pencatat panggilan. */
function peladen(awal: { sah: boolean }) {
  const keadaan = { ...awal };
  const panggilan: string[] = [];
  const pemanggil: Pemanggil = async (jalur, init) => {
    panggilan.push(`${init?.method ?? "GET"} ${jalur}`);
    if (jalur === JALUR_MASUK) {
      keadaan.sah = true;
      return new Response(null, { status: 204 });
    }
    if (jalur === JALUR_KELUAR) {
      keadaan.sah = false;
      return new Response(null, { status: 204 });
    }
    if (!keadaan.sah) return new Response("{}", { status: 401 });
    if (jalur === JALUR_PERCAKAPAN) return new Response(JSON.stringify({ percakapan: [] }));
    if (jalur.startsWith(JALUR_PERCAKAPAN)) {
      return new Response(JSON.stringify({ id_percakapan: jalur.split("/").pop(), giliran: [] }));
    }
    return new Response("{}", { status: 500 });
  };
  return { keadaan, panggilan, pemanggil };
}

function pasang(pemanggil: Pemanggil, simpanan: Simpanan | null = simpananPeta()) {
  return render(<Aplikasi pemanggil={pemanggil} simpanan={simpanan} salin={async () => undefined} />);
}

test("tanpa sesi sah, layar pertama adalah S-01", async () => {
  pasang(peladen({ sah: false }).pemanggil);
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulMasuk })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: MIKROKOPI.judulLayar })).toBeNull();
});

test("dengan sesi sah, layar pertama adalah Tanya", async () => {
  pasang(peladen({ sah: true }).pemanggil);
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
});

test("luring saat dibuka: layar Tanya, agar draf tetap dapat ditulis — KL-E", async () => {
  pasang(async () => {
    throw new TypeError("Failed to fetch");
  });
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
});

test("selama memeriksa, tidak ada layar yang menampilkan isian", () => {
  pasang(() => new Promise(() => undefined));
  expect(screen.getByRole("status").textContent).toBe(MIKROKOPI.memeriksaAkun);
  expect(screen.queryByRole("textbox")).toBeNull();
});

test("sesudah masuk berhasil, layar Tanya", async () => {
  pasang(peladen({ sah: false }).pemanggil);
  fireEvent.change(await screen.findByLabelText(MIKROKOPI.labelNamaPengguna), {
    target: { value: "ks-017" },
  });
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSandi), { target: { value: "x" } });
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolMasuk }));
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
});

test("401 di tengah pemakaian kembali ke S-01, dan draf tetap tersimpan", async () => {
  const { keadaan, pemanggil } = peladen({ sah: true });
  const simpanan = simpananPeta();
  pasang(async (jalur, init) => {
    if (jalur === JALUR_TANYA) {
      keadaan.sah = false;
      return new Response("{}", { status: 401 });
    }
    return pemanggil(jalur, init);
  }, simpanan);
  fireEvent.change(await screen.findByLabelText(MIKROKOPI.labelPertanyaan), {
    target: { value: "Bagaimana menyusun jadwal supervisi?" },
  });
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKirim }));
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulMasuk })).toBeTruthy();
  expect(screen.getByText(MIKROKOPI.perluMasukLagi)).toBeTruthy();
  expect(bacaDraf(simpanan)).toBe("Bagaimana menyusun jadwal supervisi?");
});

test("K-6 · M-14: Keluar mencabut sesi lalu menghapus draf dan percakapan aktif", async () => {
  const { panggilan, pemanggil } = peladen({ sah: true });
  const simpanan = simpananPeta();
  simpanDraf(simpanan, "Draf kepala sekolah sebelumnya");
  percakapanAktif(simpanan);
  expect(simpanan.isi.size).toBe(2);
  pasang(pemanggil, simpanan);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolKeluar }));
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulMasuk })).toBeTruthy();
  expect(panggilan).toContain(`POST ${JALUR_KELUAR}`);
  expect([...simpanan.isi.keys()]).toEqual([]);
});

test("Keluar tetap membersihkan peramban meski peladen tak terjangkau", async () => {
  const { pemanggil } = peladen({ sah: true });
  const simpanan = simpananPeta();
  simpanDraf(simpanan, "Draf");
  pasang(async (jalur, init) => {
    if (jalur === JALUR_KELUAR) throw new TypeError("Failed to fetch");
    return pemanggil(jalur, init);
  }, simpanan);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolKeluar }));
  expect(await screen.findByRole("heading", { name: MIKROKOPI.judulMasuk })).toBeTruthy();
  expect(bacaDraf(simpanan)).toBe("");
});

test("sesudah Keluar lalu masuk lagi, isian pertanyaan kosong", async () => {
  const { pemanggil } = peladen({ sah: true });
  const simpanan = simpananPeta();
  simpanDraf(simpanan, "Draf orang sebelumnya");
  pasang(pemanggil, simpanan);
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolKeluar }));
  fireEvent.change(await screen.findByLabelText(MIKROKOPI.labelNamaPengguna), {
    target: { value: "ks-018" },
  });
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSandi), { target: { value: "x" } });
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolMasuk }));
  const isian = (await screen.findByLabelText(MIKROKOPI.labelPertanyaan)) as HTMLTextAreaElement;
  expect(isian.value).toBe("");
  vi.restoreAllMocks();
});

// ── fitur 013 · Beranda, Detail butir, navigasi (K-7) ───────────────────

describe("beranda dan navigasi", () => {
  const RINGKASAN_AKTIF = {
    profil: {
      jabatan: "Kepala Sekolah",
      masa_kerja: 3,
      jumlah_rombel: 6,
      jumlah_ptk: 9,
      jalur_akreditasi: "visitasi",
      wilayah: "Kabupaten Sumedang",
    },
    prioritas: ["K1", "K2", "K3"],
    persetujuan: "ditolak",
  };
  const RINGKAS = {
    id_butir: "b-1",
    kategori: "K1",
    jenis_sumber: "riset",
    judul: "Supervisi akademik terjadwal",
    alasan_relevansi: "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
    perkiraan_waktu_baca: 4,
  };
  const LENGKAP = {
    ...RINGKAS,
    inti_temuan: "Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
    implikasi_tindakan: ["Susun jadwal supervisi satu semester."],
    tenggat_terkait: null,
    boleh_teks_penuh: true,
    sumber: { judul: "Laporan", penerbit: "Penerbit", tahun: 2025, tautan: null },
  };

  function peladenAktif(sah = { berlaku: true }) {
    const panggilan: string[] = [];
    const pemanggil: Pemanggil = async (jalur, init) => {
      panggilan.push(`${init?.method ?? "GET"} ${jalur}`);
      if (jalur === JALUR_KELUAR) return new Response(null, { status: 204 });
      if (!sah.berlaku) return new Response("{}", { status: 401 });
      if (jalur === JALUR_PROFIL) return new Response(JSON.stringify(RINGKASAN_AKTIF));
      if (jalur === JALUR_BERANDA) {
        return new Response(JSON.stringify({ keadaan: "berisi", butir: [RINGKAS] }));
      }
      if (jalur === jalurButir("b-1")) return new Response(JSON.stringify(LENGKAP));
      if (jalur === JALUR_PERCAKAPAN) return new Response(JSON.stringify({ percakapan: [] }));
      return new Response("{}", { status: 500 });
    };
    return { pemanggil, panggilan, sah };
  }

  test("pengguna aktif mendarat di Beranda, navigasi menandai halaman aktif", async () => {
    pasang(peladenAktif().pemanggil);
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulBeranda })).toBeTruthy();
    const nav = screen.getByRole("navigation", { name: MIKROKOPI.labelNavigasi });
    expect(nav.querySelector('[aria-current="page"]')?.textContent).toBe(MIKROKOPI.navBeranda);
    expect(nav.querySelectorAll("button")).toHaveLength(2);
  });

  test("Beranda → Detail → kembali; navigasi ke Tanya dan kembali", async () => {
    pasang(peladenAktif().pemanggil);
    fireEvent.click(await screen.findByRole("button", { name: new RegExp(RINGKAS.judul) }));
    expect(await screen.findByRole("heading", { level: 1, name: LENGKAP.judul })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKembaliBeranda }));
    await screen.findByRole("heading", { name: MIKROKOPI.judulBeranda });
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.navTanya }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.navBeranda }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulBeranda })).toBeTruthy();
  });

  test("jalur cepat dari Beranda membuka Tanya", async () => {
    pasang(peladenAktif().pemanggil);
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolTanyaCepat }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulLayar })).toBeTruthy();
  });

  test("Keluar dari Beranda menghapus salinan butir hari ini", async () => {
    const simpanan = simpananPeta();
    pasang(peladenAktif().pemanggil, simpanan);
    await screen.findByRole("button", { name: new RegExp(RINGKAS.judul) });
    await waitFor(() => expect(simpanan.isi.has("smart-coaching:beranda")).toBe(true));
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKeluar }));
    await screen.findByRole("heading", { name: MIKROKOPI.judulMasuk });
    expect(simpanan.isi.has("smart-coaching:beranda")).toBe(false);
  });

  test("401 pada Beranda kembali ke S-01", async () => {
    const p = peladenAktif();
    pasang(p.pemanggil);
    await screen.findByRole("heading", { name: MIKROKOPI.judulBeranda });
    p.sah.berlaku = false;
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.navTanya }));
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.navBeranda }));
    expect(await screen.findByRole("heading", { name: MIKROKOPI.judulMasuk })).toBeTruthy();
    expect(screen.getByText(MIKROKOPI.perluMasukLagiSaja)).toBeTruthy();
  });
});
