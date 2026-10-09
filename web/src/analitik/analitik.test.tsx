/**
 * S-18 Analitik penelitian — T-6 fitur 035, FR-J03, FR-J04, R-04, R-05, K-5.
 *
 * Peneliti dikenali tanpa rute baru: 403 pada ringkasan akun dan antrean
 * kurasi, lalu ringkasan analitik 200. Angka `null` tidak pernah tampil
 * sebagai nol.
 */

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { Aplikasi } from "../Aplikasi";
import {
  JALUR_ANALITIK_EKSPOR,
  JALUR_ANALITIK_RINGKAS,
  JALUR_ANTREAN,
  JALUR_PROFIL,
  bacaAnalitik,
  type Pemanggil,
} from "../klien";
import type { RingkasanAnalitik } from "../kontrak";
import { LABEL_METRIK_TERTUNDA, LABEL_NILAI, MIKROKOPI, persen } from "../mikrokopi";
import { LayarAnalitik } from "./LayarAnalitik";

afterEach(cleanup);

const RINGKASAN: RingkasanAnalitik = {
  dihitung_pada: "2031-03-31T05:00:00Z",
  keterlibatan: {
    aktif_harian: [{ tanggal: "2031-03-31", pengguna: 4 }],
    aktif_mingguan: [{ mulai: "2031-03-31", pengguna: 4 }],
    retensi: [
      { hari: 1, kohort: 3, kembali: 2, rasio: 2 / 3 },
      { hari: 7, kohort: 0, kembali: 0, rasio: null },
      { hari: 30, kohort: 2, kembali: 2, rasio: 1 },
    ],
    sesi: { jumlah: 0, median_menit: null, rerata_menit: null },
  },
  penemuan: { disajikan: 0, dibuka: 0, rasio: null },
  penilaian: { per_nilai: { membantu: 3, tidak_membantu: 1, keliru: 2 } },
  penelusuran_sumber: { jawaban: 5, dibuka: 2, rasio: 0.4 },
  belum_terukur: [{ metrik: "rasio_penerapan", sebab: "Komitmen penerapan belum dibangun." }],
  integritas: {
    per_jenis: { session_start: 11 },
    per_versi_aplikasi: { "pilot-1": 20 },
    per_versi_model: { tanpa_model: 20 },
    pertama: "2031-03-01T01:00:00Z",
    terakhir: "2031-03-31T04:00:00Z",
    pengembangan: 4,
  },
};

function peladen(ekspor: () => Response | Promise<Response> = () => csv()) {
  const panggilan: string[] = [];
  const badan: unknown[] = [];
  const pemanggil: Pemanggil = async (jalur, init) => {
    panggilan.push(`${init?.method ?? "GET"} ${jalur}`);
    if (typeof init?.body === "string") badan.push(JSON.parse(init.body));
    if (jalur === JALUR_PROFIL || jalur === JALUR_ANTREAN) return new Response("{}", { status: 403 });
    if (jalur === JALUR_ANALITIK_RINGKAS) return new Response(JSON.stringify(RINGKASAN));
    if (jalur === JALUR_ANALITIK_EKSPOR) return ekspor();
    return new Response("{}", { status: 404 });
  };
  return { pemanggil, panggilan, badan };
}

function csv(): Response {
  return new Response("pseudonim,jenis\n", {
    status: 200,
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="peristiwa-2031-03-01-2031-03-31-7.csv"',
    },
  });
}

function layar(pemanggil: Pemanggil) {
  const simpan = vi.fn();
  const keluar = vi.fn();
  const belumMasuk = vi.fn();
  render(
    <LayarAnalitik awal={RINGKASAN} belumMasuk={belumMasuk} keluar={keluar} pemanggil={pemanggil} simpan={simpan} />,
  );
  return { simpan, keluar, belumMasuk };
}

describe("cangkang peneliti — K-5", () => {
  test("ringkasan akun dan antrean 403, analitik 200: S-18 tanpa navigasi pengguna", async () => {
    const p = peladen();
    render(<Aplikasi pemanggil={p.pemanggil} salin={async () => undefined} simpanan={null} />);
    expect(await screen.findByRole("heading", { level: 1, name: MIKROKOPI.judulAnalitik })).toBeTruthy();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(p.panggilan.slice(0, 3)).toEqual([
      `GET ${JALUR_PROFIL}`,
      `GET ${JALUR_ANTREAN}`,
      `GET ${JALUR_ANALITIK_RINGKAS}`,
    ]);
  });
});

describe("S-18", () => {
  test("M-10: angka null tampil sebagai belum dapat dihitung, tidak pernah nol", () => {
    layar(peladen().pemanggil);
    const retensi = screen.getByRole("table", { name: MIKROKOPI.judulRetensi });
    const baris = within(retensi).getAllByRole("row");
    expect(baris[1]?.textContent).toContain(persen(2 / 3));
    expect(baris[2]?.textContent).toContain(MIKROKOPI.belumDapatDihitung);
    expect(baris[2]?.textContent).not.toContain(persen(0));
    const penemuan = screen.getByRole("table", { name: MIKROKOPI.judulPenemuanAnalitik });
    expect(penemuan.textContent).toContain(MIKROKOPI.belumDapatDihitung);
    const sesi = screen.getByRole("table", { name: MIKROKOPI.judulSesi });
    expect(sesi.textContent).toContain(MIKROKOPI.belumDapatDihitung);
  });

  test("R-04: metrik belum terukur tampil bernama beserta sebabnya", () => {
    layar(peladen().pemanggil);
    expect(screen.getByText(LABEL_METRIK_TERTUNDA.rasio_penerapan)).toBeTruthy();
    expect(screen.getByText("Komitmen penerapan belum dibangun.")).toBeTruthy();
  });

  test("fitur 036: penilaian per nilai, berurutan tiga nilai", () => {
    layar(peladen().pemanggil);
    const tabel = screen.getByRole("table", { name: MIKROKOPI.judulPenilaianAnalitik });
    const baris = within(tabel).getAllByRole("row").slice(1).map((b) => b.textContent);
    expect(baris).toEqual([
      `${LABEL_NILAI.membantu}3`,
      `${LABEL_NILAI.tidak_membantu}1`,
      `${LABEL_NILAI.keliru}2`,
    ]);
  });

  test("fitur 032: rasio penelusuran sumber — jawaban, sumber dibuka, rasio", () => {
    layar(peladen().pemanggil);
    const tabel = screen.getByRole("table", { name: MIKROKOPI.judulPenelusuranAnalitik });
    const baris = within(tabel).getAllByRole("row").slice(1).map((b) => b.textContent);
    expect(baris).toEqual([
      `${MIKROKOPI.labelJawabanDisajikan}5`,
      `${MIKROKOPI.labelSumberDibuka}2`,
      `${MIKROKOPI.kolomRasio}${persen(0.4)}`,
    ]);
  });

  test("fitur 032: ringkasan tanpa penelusuran sumber ditolak klien, bukan ditampilkan separuh", async () => {
    const { penelusuran_sumber: _, ...lama } = RINGKASAN;
    const pemanggil: Pemanggil = async () => new Response(JSON.stringify(lama));
    expect(await bacaAnalitik(pemanggil)).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("R-05: integritas menyebut peristiwa pengembangan yang dipisah", () => {
    layar(peladen().pemanggil);
    const integritas = screen.getByRole("table", { name: MIKROKOPI.judulIntegritas });
    expect(within(integritas).getByText(MIKROKOPI.labelPengembangan).parentElement?.textContent).toContain("4");
  });

  test("unduh CSV: rentang dan pilihan terkirim, berkas diserahkan dengan namanya", async () => {
    const p = peladen();
    const { simpan } = layar(p.pemanggil);
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelDari), { target: { value: "2031-03-01" } });
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSampai), { target: { value: "2031-03-31" } });
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolUnduhCsv }));
    await waitFor(() => expect(simpan).toHaveBeenCalledTimes(1));
    expect(p.badan).toEqual([{ dari: "2031-03-01", sampai: "2031-03-31", termasuk_pengembangan: false }]);
    expect(simpan.mock.calls[0]?.[1]).toBe("peristiwa-2031-03-01-2031-03-31-7.csv");
  });

  test("pengembangan ikut hanya bila dicentang tegas", async () => {
    const p = peladen();
    const { simpan } = layar(p.pemanggil);
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelDari), { target: { value: "2031-03-01" } });
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSampai), { target: { value: "2031-03-02" } });
    fireEvent.click(screen.getByLabelText(MIKROKOPI.labelTermasukPengembangan));
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolUnduhCsv }));
    await waitFor(() => expect(simpan).toHaveBeenCalled());
    expect(p.badan).toEqual([{ dari: "2031-03-01", sampai: "2031-03-02", termasuk_pengembangan: true }]);
  });

  test("rentang kosong tidak dikirim", () => {
    const p = peladen();
    layar(p.pemanggil);
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolUnduhCsv }));
    expect(screen.getByRole("alert").textContent).toBe(MIKROKOPI.eksporRentang);
    expect(p.panggilan).toEqual([]);
  });

  test("400 dari peladen, luring, dan gangguan: kalimatnya masing-masing", async () => {
    for (const [jawab, pesan] of [
      [() => new Response("{}", { status: 400 }), MIKROKOPI.eksporRentang],
      [() => Promise.reject(new TypeError("Failed to fetch")), MIKROKOPI.eksporLuring],
      [() => new Response("{}", { status: 500 }), MIKROKOPI.eksporGangguan],
    ] as const) {
      const { simpan } = layar(peladen(jawab).pemanggil);
      fireEvent.change(screen.getByLabelText(MIKROKOPI.labelDari), { target: { value: "2031-03-01" } });
      fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSampai), { target: { value: "2031-03-02" } });
      fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolUnduhCsv }));
      expect((await screen.findByRole("alert")).textContent).toBe(pesan);
      expect(simpan).not.toHaveBeenCalled();
      cleanup();
    }
  });

  test("401 menyerahkan ke cangkang; Keluar tersedia", async () => {
    const { belumMasuk, keluar } = layar(peladen(() => new Response("{}", { status: 401 })).pemanggil);
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelDari), { target: { value: "2031-03-01" } });
    fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSampai), { target: { value: "2031-03-02" } });
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolUnduhCsv }));
    await waitFor(() => expect(belumMasuk).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKeluar }));
    expect(keluar).toHaveBeenCalled();
  });
});
