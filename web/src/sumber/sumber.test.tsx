/**
 * S-10 Pembaca sumber — T-7 fitur 032, R-07, P-2 A; D-05 S-10, D-14 Bagian 4.10.
 *
 * Peladen palsu menjawab bentuk D-14. Yang diuji perilaku layar: status
 * keberlakuan **sebelum** teks, keempat alasan tanpa teks, dan keadaan
 * memuat, tidak dapat dibuka, luring, serta galat.
 */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { jalurSumber, type Pemanggil } from "../klien";
import type { AlasanTanpaTeks, Sitasi, SumberTampil } from "../kontrak";
import {
  LABEL_JENIS_DOKUMEN,
  MIKROKOPI,
  STATUS_SUMBER,
  TANPA_TEKS,
  bagianDirujuk,
} from "../mikrokopi";
import { LayarSumber } from "./LayarSumber";

afterEach(cleanup);

const SITASI: Sitasi = {
  id_dokumen: "doc_permen_1",
  judul: "Permendikdasmen Nomor 1 Tahun 2026",
  penerbit: "Kemendikdasmen",
  tahun: 2026,
  bagian: "Pasal 7 ayat (2)",
  status_keberlakuan: "berlaku",
  rujukan_pengganti: null,
  tautan: "https://jdih.contoh.go.id/permen-1",
};

const SUMBER: SumberTampil = {
  id_dokumen: "doc_permen_1",
  judul: "Permendikdasmen Nomor 1 Tahun 2026",
  jenis: "regulasi_resmi",
  penerbit: "Kemendikdasmen",
  tahun: 2026,
  status_keberlakuan: "berlaku",
  rujukan_pengganti: null,
  bagian: "Pasal 7 ayat (2)",
  teks_bagian: ["Kepala sekolah menyusun rencana kerja tahunan."],
  tanpa_teks: null,
};

function json(isi: unknown, status = 200): Response {
  return new Response(JSON.stringify(isi), { status });
}

function peladen(jawab: () => Response | Promise<Response>) {
  const panggilan: string[] = [];
  const pemanggil: Pemanggil = async (jalur, init) => {
    panggilan.push(`${init?.method ?? "GET"} ${jalur}`);
    return jalur === jalurSumber(SITASI.id_dokumen, SITASI.bagian)
      ? jawab()
      : json({}, 500);
  };
  return { pemanggil, panggilan };
}

function buka(pemanggil: Pemanggil, sitasi: Sitasi = SITASI) {
  const kembali = vi.fn();
  const belumMasuk = vi.fn();
  render(
    <LayarSumber
      belumMasuk={belumMasuk}
      kembali={kembali}
      pemanggil={pemanggil}
      sitasi={sitasi}
    />,
  );
  return { kembali, belumMasuk };
}

test("jalur membawa dokumen dan bagian yang dirujuk, terkodekan", () => {
  expect(jalurSumber("doc 1", "Pasal 7 ayat (2)")).toBe(
    "/api/v1/sumber/doc%201?bagian=Pasal%207%20ayat%20(2)",
  );
});

test("KL-A lalu identitas dokumen, bagian, status, teks, dan tautan asli", async () => {
  const p = peladen(() => json(SUMBER));
  buka(p.pemanggil);
  expect(screen.getByRole("status").textContent).toBe(MIKROKOPI.sumberMemuat);
  expect(
    await screen.findByRole("heading", { level: 1, name: SUMBER.judul }),
  ).toBeTruthy();
  expect(screen.getByText(LABEL_JENIS_DOKUMEN.regulasi_resmi)).toBeTruthy();
  expect(screen.getByText(bagianDirujuk(SUMBER.bagian))).toBeTruthy();
  expect(screen.getByTestId("status-sumber").textContent).toContain(
    STATUS_SUMBER.berlaku,
  );
  expect(screen.getByTestId("teks-bagian").textContent).toContain(
    SUMBER.teks_bagian[0],
  );
  const tautan = screen.getByRole("link", { name: MIKROKOPI.bukaSumberAsli });
  expect(tautan.getAttribute("href")).toBe(SITASI.tautan);
  expect(p.panggilan).toEqual([
    `GET ${jalurSumber(SITASI.id_dokumen, SITASI.bagian)}`,
  ]);
});

test("M-16, R-07: status keberlakuan dan penggantinya tampil sebelum teks", async () => {
  buka(
    peladen(() =>
      json({
        ...SUMBER,
        status_keberlakuan: "diubah",
        rujukan_pengganti: "Permendikdasmen Nomor 2 Tahun 2027",
      }),
    ).pemanggil,
  );
  const status = await screen.findByTestId("status-sumber");
  const teks = screen.getByTestId("teks-bagian");
  expect(status.textContent).toContain(STATUS_SUMBER.diubah);
  expect(status.textContent).toContain("Permendikdasmen Nomor 2 Tahun 2027");
  expect(
    status.compareDocumentPosition(teks) & Node.DOCUMENT_POSITION_FOLLOWING,
  ).toBeTruthy();
});

test.each<[AlasanTanpaTeks, Partial<SumberTampil>]>([
  [
    "dokumen_tidak_publik",
    { jenis: "dokumen_sekolah", status_keberlakuan: null },
  ],
  ["status_belum_tercatat", { status_keberlakuan: null }],
  [
    "dokumen_dicabut",
    {
      status_keberlakuan: "dicabut",
      rujukan_pengganti: "Permendikdasmen Nomor 2 Tahun 2027",
    },
  ],
  ["bagian_tidak_tersedia", {}],
])(
  "tanpa teks %s: kalimatnya sendiri, tanpa blok teks",
  async (alasan, ubah) => {
    buka(
      peladen(() =>
        json({ ...SUMBER, ...ubah, teks_bagian: [], tanpa_teks: alasan }),
      ).pemanggil,
    );
    expect(await screen.findByText(TANPA_TEKS[alasan])).toBeTruthy();
    expect(screen.queryByTestId("teks-bagian")).toBeNull();
  },
);

test("dicabut dinyatakan tidak berlaku beserta penggantinya", async () => {
  buka(
    peladen(() =>
      json({
        ...SUMBER,
        status_keberlakuan: "dicabut",
        rujukan_pengganti: "Permendikdasmen Nomor 2 Tahun 2027",
        teks_bagian: [],
        tanpa_teks: "dokumen_dicabut",
      }),
    ).pemanggil,
  );
  const status = await screen.findByTestId("status-sumber");
  expect(status.textContent).toContain(STATUS_SUMBER.dicabut);
  expect(status.textContent).toContain("Permendikdasmen Nomor 2 Tahun 2027");
});

test("regulasi tanpa status menyatakan belum tercatat; sumber lain tanpa status tanpa blok status", async () => {
  buka(
    peladen(() =>
      json({
        ...SUMBER,
        status_keberlakuan: null,
        teks_bagian: [],
        tanpa_teks: "status_belum_tercatat",
      }),
    ).pemanggil,
  );
  expect((await screen.findByTestId("status-sumber")).textContent).toContain(
    MIKROKOPI.statusBelumTercatat,
  );
  cleanup();
  buka(
    peladen(() =>
      json({
        ...SUMBER,
        jenis: "artikel_lisensi_terbuka",
        status_keberlakuan: null,
      }),
    ).pemanggil,
  );
  await screen.findByRole("heading", { level: 1, name: SUMBER.judul });
  expect(screen.queryByTestId("status-sumber")).toBeNull();
});

test("tanpa tautan pada sitasi, tidak ada tautan sumber asli", async () => {
  buka(peladen(() => json(SUMBER)).pemanggil, { ...SITASI, tautan: null });
  await screen.findByRole("heading", { level: 1, name: SUMBER.judul });
  expect(
    screen.queryByRole("link", { name: MIKROKOPI.bukaSumberAsli }),
  ).toBeNull();
});

test("404: dokumen tidak dapat dibuka — keadaan sah, bukan galat", async () => {
  buka(peladen(() => json({}, 404)).pemanggil);
  expect(await screen.findByText(MIKROKOPI.sumberTidakAda)).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});

test("KL-E luring dan KL-D gangguan dengan Coba lagi", async () => {
  buka(
    peladen(() => Promise.reject(new TypeError("Failed to fetch"))).pemanggil,
  );
  expect(await screen.findByText(MIKROKOPI.sumberLuring)).toBeTruthy();
  cleanup();
  let ke = 0;
  buka(peladen(() => (ke++ === 0 ? json({}, 500) : json(SUMBER))).pemanggil);
  expect(await screen.findByText(MIKROKOPI.sumberGangguan)).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: MIKROKOPI.tombolCobaLagi }),
  );
  expect(
    await screen.findByRole("heading", { level: 1, name: SUMBER.judul }),
  ).toBeTruthy();
});

test("bentuk yang tidak dikenali ditolak utuh", async () => {
  buka(peladen(() => json({ ...SUMBER, tanpa_teks: "lainnya" })).pemanggil);
  expect(await screen.findByText(MIKROKOPI.sumberGangguan)).toBeTruthy();
});

test("401 menyerahkan ke cangkang; Kembali ke jawaban", async () => {
  const { belumMasuk } = buka(peladen(() => json({}, 401)).pemanggil);
  await waitFor(() => expect(belumMasuk).toHaveBeenCalled());
  cleanup();
  const { kembali } = buka(peladen(() => json(SUMBER)).pemanggil);
  fireEvent.click(
    screen.getByRole("button", { name: MIKROKOPI.tombolKembaliJawaban }),
  );
  expect(kembali).toHaveBeenCalled();
});
