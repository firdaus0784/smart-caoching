/**
 * S-11 Koleksi tersimpan — T-7 fitur 032, FR-G06, FR-G10, P-4 A; D-05 S-11,
 * D-14 Bagian 4.10.
 */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { JALUR_KOLEKSI, jalurSimpan, type Pemanggil } from "../klien";
import type { ButirKoleksi } from "../kontrak";
import { LABEL_JENIS_SUMBER, LABEL_KATEGORI, MIKROKOPI } from "../mikrokopi";
import { LayarKoleksi } from "./LayarKoleksi";

afterEach(cleanup);

const BUTIR: ButirKoleksi = {
  id_butir: "b-1",
  kategori: "K1",
  jenis_sumber: "riset",
  judul: "Supervisi akademik terjadwal",
  alasan_relevansi:
    "Sekolah Anda menetapkan supervisi akademik sebagai prioritas.",
  perkiraan_waktu_baca: 4,
  inti_temuan: "Supervisi yang terjadwal meningkatkan umpan balik kepada guru.",
  implikasi_tindakan: ["Susun jadwal supervisi satu semester."],
  tenggat_terkait: null,
  boleh_teks_penuh: true,
  sumber: {
    judul: "Laporan supervisi",
    penerbit: "Penerbit",
    tahun: 2025,
    tautan: null,
  },
  catatan: "Bahas di rapat guru",
  disimpan_pada: "2026-10-09T01:00:00Z",
  dasar_berubah: false,
};

const DITARIK: ButirKoleksi = {
  ...BUTIR,
  id_butir: "b-2",
  jenis_sumber: "regulasi",
  kategori: "K2",
  judul: "Aturan beban kerja guru",
  catatan: null,
  dasar_berubah: true,
};

function json(isi: unknown, status = 200): Response {
  return new Response(JSON.stringify(isi), { status });
}

function peladen(
  jawab: (jalur: string, metode: string) => Response | Promise<Response>,
) {
  const panggilan: string[] = [];
  const pemanggil: Pemanggil = async (jalur, init) => {
    const metode = init?.method ?? "GET";
    panggilan.push(`${metode} ${jalur}`);
    return jawab(jalur, metode);
  };
  return { pemanggil, panggilan };
}

function buka(pemanggil: Pemanggil) {
  const belumMasuk = vi.fn();
  render(<LayarKoleksi belumMasuk={belumMasuk} pemanggil={pemanggil} />);
  return { belumMasuk };
}

test("daftar berurutan peladen; catatan, inti, implikasi, dan sumber terbaca", async () => {
  buka(peladen(() => json({ koleksi: [BUTIR, DITARIK] })).pemanggil);
  expect(
    await screen.findByRole("heading", { level: 2, name: BUTIR.judul }),
  ).toBeTruthy();
  const kartu = screen.getAllByRole("article");
  expect(
    kartu.map((k) => within(k).getByRole("heading", { level: 2 }).textContent),
  ).toEqual([BUTIR.judul, DITARIK.judul]);
  const pertama = kartu[0]!;
  expect(within(pertama).getByText(LABEL_JENIS_SUMBER.riset)).toBeTruthy();
  expect(within(pertama).getByText("Bahas di rapat guru")).toBeTruthy();
  expect(within(pertama).getByText(BUTIR.inti_temuan)).toBeTruthy();
  expect(within(pertama).queryByText(MIKROKOPI.judulCatatanAnda)).toBeTruthy();
  expect(within(kartu[1]!).queryByText(MIKROKOPI.judulCatatanAnda)).toBeNull();
});

test("M-17, P-4 A: penanda dasar berubah tampil sebelum isi, hanya pada butir itu", async () => {
  buka(peladen(() => json({ koleksi: [BUTIR, DITARIK] })).pemanggil);
  await screen.findByRole("heading", { level: 2, name: DITARIK.judul });
  const [pertama, kedua] = screen.getAllByRole("article");
  expect(
    within(pertama!).queryByText(MIKROKOPI.penandaDasarBerubah),
  ).toBeNull();
  const penanda = within(kedua!).getByText(MIKROKOPI.penandaDasarBerubah);
  const isi = within(kedua!).getByText(DITARIK.inti_temuan);
  const judul = within(kedua!).getByRole("heading", { level: 2 });
  expect(
    penanda.compareDocumentPosition(judul) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
  expect(
    penanda.compareDocumentPosition(isi) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
});

test("FR-G10: penyaring kategori dan jenis sumber dikirim sebagai kueri", async () => {
  const p = peladen(() => json({ koleksi: [] }));
  buka(p.pemanggil);
  await screen.findByText(MIKROKOPI.koleksiKosong);
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSaringKategori), {
    target: { value: "K2" },
  });
  await screen.findByText(MIKROKOPI.koleksiTersaringKosong);
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSaringJenis), {
    target: { value: "regulasi" },
  });
  await waitFor(() =>
    expect(p.panggilan.at(-1)).toBe(
      `GET ${JALUR_KOLEKSI}?kategori=K2&jenis_sumber=regulasi`,
    ),
  );
  expect(p.panggilan[0]).toBe(`GET ${JALUR_KOLEKSI}`);
  expect(screen.getByRole("option", { name: LABEL_KATEGORI.K2 })).toBeTruthy();
});

test("keluarkan: DELETE, kartu hilang, kalimatnya tampil", async () => {
  const p = peladen((_, metode) =>
    metode === "DELETE"
      ? new Response(null, { status: 204 })
      : json({ koleksi: [BUTIR] }),
  );
  buka(p.pemanggil);
  fireEvent.click(
    await screen.findByRole("button", { name: MIKROKOPI.tombolKeluarkan }),
  );
  expect(await screen.findByText(MIKROKOPI.butirDikeluarkan)).toBeTruthy();
  expect(
    screen.queryByRole("heading", { level: 2, name: BUTIR.judul }),
  ).toBeNull();
  expect(p.panggilan).toContain(`DELETE ${jalurSimpan("b-1")}`);
});

test("keluarkan yang sudah tidak ada pun menghilangkan kartunya; luring tidak", async () => {
  const p = peladen((_, metode) =>
    metode === "DELETE" ? json({}, 404) : json({ koleksi: [BUTIR] }),
  );
  buka(p.pemanggil);
  fireEvent.click(
    await screen.findByRole("button", { name: MIKROKOPI.tombolKeluarkan }),
  );
  await waitFor(() =>
    expect(
      screen.queryByRole("heading", { level: 2, name: BUTIR.judul }),
    ).toBeNull(),
  );
  cleanup();
  const q = peladen((_, metode) =>
    metode === "DELETE"
      ? Promise.reject(new TypeError("Failed to fetch"))
      : json({ koleksi: [BUTIR] }),
  );
  buka(q.pemanggil);
  fireEvent.click(
    await screen.findByRole("button", { name: MIKROKOPI.tombolKeluarkan }),
  );
  expect(
    await screen.findByText(MIKROKOPI.keluarkanBelumTerkirim),
  ).toBeTruthy();
  expect(
    screen.getByRole("heading", { level: 2, name: BUTIR.judul }),
  ).toBeTruthy();
});

test("KL-E luring, KL-D gangguan dengan Coba lagi, 401 ke cangkang", async () => {
  buka(
    peladen(() => Promise.reject(new TypeError("Failed to fetch"))).pemanggil,
  );
  expect(await screen.findByText(MIKROKOPI.koleksiLuring)).toBeTruthy();
  cleanup();
  let ke = 0;
  buka(
    peladen(() => (ke++ === 0 ? json({}, 500) : json({ koleksi: [BUTIR] })))
      .pemanggil,
  );
  expect(await screen.findByText(MIKROKOPI.koleksiGangguan)).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: MIKROKOPI.tombolCobaLagi }),
  );
  expect(
    await screen.findByRole("heading", { level: 2, name: BUTIR.judul }),
  ).toBeTruthy();
  cleanup();
  const { belumMasuk } = buka(peladen(() => json({}, 401)).pemanggil);
  await waitFor(() => expect(belumMasuk).toHaveBeenCalled());
});

test("tanggapan yang bentuknya tidak dikenali ditolak utuh", async () => {
  buka(
    peladen(() => json({ koleksi: [{ ...BUTIR, dasar_berubah: "ya" }] }))
      .pemanggil,
  );
  expect(await screen.findByText(MIKROKOPI.koleksiGangguan)).toBeTruthy();
});
