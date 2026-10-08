/**
 * S-09 blok 6 "Nilai jawaban" — T-7 fitur 036, R-10, P-2 B; D-05 0.7, D-14
 * Bagian 4.9.
 *
 * Diuji lewat `LayarTanya`, bukan komponennya saja: blok ini hanya berarti
 * bila tampil di bawah jawaban yang sungguh diterima, pada keempat status dasar.
 */

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { JALUR_PERCAKAPAN, JALUR_TANYA, jalurPenilaian, type Pemanggil } from "../klien";
import type { StatusDasar, Tanggapan } from "../kontrak";
import { LABEL_NILAI, MIKROKOPI } from "../mikrokopi";
import { LayarTanya } from "./LayarTanya";

afterEach(cleanup);

const JAWABAN: Tanggapan = {
  id_pesan: "pesan-1",
  status_dasar: "kuat",
  ringkasan_tindakan: ["Susun jadwal supervisi bersama guru."],
  penjelasan: "Supervisi akademik dilakukan terjadwal.",
  klaim: [{ teks: "Supervisi terjadwal.", id_segmen: ["seg-1"] }],
  sitasi: [
    {
      id_dokumen: "dok-1",
      judul: "Peraturan Menteri Nomor 1",
      penerbit: "Kementerian Pendidikan",
      tahun: 2026,
      bagian: "Pasal 7",
      status_keberlakuan: "berlaku",
      rujukan_pengganti: null,
      tautan: null,
    },
  ],
  bacaan_lanjutan: [],
  catatan_keberlakuan: "",
  penafian: "Keputusan akhir berada pada kepala sekolah.",
  versi: { model: "m", indeks: "i", kode: "k" },
};

function kosongkan(status: StatusDasar): Tanggapan {
  return { ...JAWABAN, status_dasar: status, ringkasan_tindakan: [], klaim: [], sitasi: [], penjelasan: "" };
}

interface Peladen {
  readonly pemanggil: Pemanggil;
  readonly badan: unknown[];
}

function peladen(
  tanggapan: Tanggapan = JAWABAN,
  penilaian: () => Response | Promise<Response> = () =>
    new Response(JSON.stringify({ id_pesan: "pesan-1", nilai: "keliru", kirim_ke_kurator: true })),
): Peladen {
  const badan: unknown[] = [];
  const pemanggil: Pemanggil = async (jalur, init) => {
    if (jalur.startsWith(JALUR_PERCAKAPAN)) {
      return new Response(JSON.stringify(jalur === JALUR_PERCAKAPAN ? { percakapan: [] } : { giliran: [] }));
    }
    if (jalur === JALUR_TANYA) return new Response(JSON.stringify(tanggapan));
    if (jalur === jalurPenilaian(tanggapan.id_pesan)) {
      if (typeof init?.body === "string") badan.push(JSON.parse(init.body));
      return penilaian();
    }
    return new Response("{}", { status: 500 });
  };
  return { pemanggil, badan };
}

async function tanyaDengan(p: Peladen, belumMasuk?: (tersimpan: boolean) => void): Promise<HTMLElement> {
  render(
    <LayarTanya
      {...(belumMasuk !== undefined ? { belumMasuk } : {})}
      pemanggil={p.pemanggil}
      salin={async () => undefined}
      simpanan={null}
    />,
  );
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelPertanyaan), {
    target: { value: "Bagaimana menyusun jadwal supervisi?" },
  });
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKirim }));
  await screen.findByTestId("blok-jawaban");
  return screen.getByRole("group", { name: MIKROKOPI.judulNilaiJawaban });
}

function pilih(blok: HTMLElement, nilai: keyof typeof LABEL_NILAI): void {
  fireEvent.click(within(blok).getByLabelText(LABEL_NILAI[nilai]));
}

function centang(blok: HTMLElement): HTMLInputElement | null {
  return within(blok).queryByLabelText(MIKROKOPI.labelKirimKeKurator) as HTMLInputElement | null;
}

describe("R-10: blok nilai jawaban pada keempat status dasar", () => {
  test.each<StatusDasar>(["kuat", "terbatas", "tidak_ditemukan", "di_luar_domain"])(
    "%s: tiga pilihan setara",
    async (status) => {
      const blok = await tanyaDengan(peladen(status === "kuat" ? JAWABAN : kosongkan(status)));
      for (const label of Object.values(LABEL_NILAI)) {
        expect(within(blok).getByLabelText(label)).toBeTruthy();
      }
    },
  );
});

test("M-13: centang kirim hanya bersama keliru, dan berganti nilai mengosongkannya", async () => {
  const blok = await tanyaDengan(peladen());
  expect(centang(blok)).toBeNull();
  pilih(blok, "keliru");
  const kotak = centang(blok);
  expect(kotak?.checked).toBe(false);
  fireEvent.click(kotak as HTMLInputElement);
  pilih(blok, "membantu");
  expect(centang(blok)).toBeNull();
  pilih(blok, "tidak_membantu");
  expect(centang(blok)).toBeNull();
  pilih(blok, "keliru");
  expect(centang(blok)?.checked).toBe(false);
  expect(within(blok).getByText(MIKROKOPI.keteranganTanpaKirim)).toBeTruthy();
});

test("kirim: badan tepat, lalu terima kasih", async () => {
  const p = peladen();
  const blok = await tanyaDengan(p);
  expect((within(blok).getByRole("button", { name: MIKROKOPI.tombolKirimPenilaian }) as HTMLButtonElement).disabled).toBe(true);
  pilih(blok, "keliru");
  fireEvent.change(within(blok).getByLabelText(MIKROKOPI.labelAlasanPenilaian), {
    target: { value: "Pasalnya sudah diubah." },
  });
  fireEvent.click(centang(blok) as HTMLInputElement);
  fireEvent.click(within(blok).getByRole("button", { name: MIKROKOPI.tombolKirimPenilaian }));
  expect(await within(blok).findByText(MIKROKOPI.penilaianTersimpan)).toBeTruthy();
  expect(p.badan).toEqual([{ nilai: "keliru", alasan: "Pasalnya sudah diubah.", kirim_ke_kurator: true }]);
});

test("alasan kosong dikirim sebagai ketiadaan; tanpa centang tidak dikirim ke kurator", async () => {
  const p = peladen(JAWABAN, () =>
    new Response(JSON.stringify({ id_pesan: "pesan-1", nilai: "membantu", kirim_ke_kurator: false })),
  );
  const blok = await tanyaDengan(p);
  pilih(blok, "membantu");
  fireEvent.change(within(blok).getByLabelText(MIKROKOPI.labelAlasanPenilaian), { target: { value: "   " } });
  fireEvent.click(within(blok).getByRole("button", { name: MIKROKOPI.tombolKirimPenilaian }));
  await within(blok).findByText(MIKROKOPI.penilaianTersimpan);
  expect(p.badan).toEqual([{ nilai: "membantu", alasan: null, kirim_ke_kurator: false }]);
});

test("penilaian dapat diganti; yang terakhir dikirim lagi", async () => {
  const p = peladen();
  const blok = await tanyaDengan(p);
  pilih(blok, "keliru");
  fireEvent.click(within(blok).getByRole("button", { name: MIKROKOPI.tombolKirimPenilaian }));
  await within(blok).findByText(MIKROKOPI.penilaianTersimpan);
  pilih(blok, "membantu");
  fireEvent.click(within(blok).getByRole("button", { name: MIKROKOPI.tombolKirimPenilaian }));
  await waitFor(() => expect(p.badan).toHaveLength(2));
  expect(p.badan[1]).toEqual({ nilai: "membantu", alasan: null, kirim_ke_kurator: false });
});

test("tidak-ditemukan: Laporkan bahwa ini seharusnya ada memilih keliru", async () => {
  const blok = await tanyaDengan(peladen(kosongkan("tidak_ditemukan")));
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolLaporkanSeharusnyaAda }));
  expect((within(blok).getByLabelText(LABEL_NILAI.keliru) as HTMLInputElement).checked).toBe(true);
  expect(centang(blok)).not.toBeNull();
});

test("tombol laporkan hanya pada keadaan tidak-ditemukan", async () => {
  await tanyaDengan(peladen());
  expect(screen.queryByRole("button", { name: MIKROKOPI.tombolLaporkanSeharusnyaAda })).toBeNull();
});

describe("galat tidak pernah dibaca isinya", () => {
  test.each([
    ["luring", () => Promise.reject(new TypeError("Failed to fetch")), MIKROKOPI.penilaianLuring],
    ["400", () => new Response("{}", { status: 400 }), MIKROKOPI.penilaianDitolak],
    ["500", () => new Response("{}", { status: 500 }), MIKROKOPI.penilaianGangguan],
    ["404", () => new Response("{}", { status: 404 }), MIKROKOPI.penilaianTidakAda],
    ["bentuk asing", () => new Response(JSON.stringify({ pseudonim: "psd_x" })), MIKROKOPI.penilaianGangguan],
  ] as const)("%s", async (_, jawab, kalimat) => {
    const blok = await tanyaDengan(peladen(JAWABAN, jawab));
    pilih(blok, "tidak_membantu");
    fireEvent.click(within(blok).getByRole("button", { name: MIKROKOPI.tombolKirimPenilaian }));
    expect(await within(blok).findByText(kalimat)).toBeTruthy();
  });

  test("401: kembali ke layar masuk", async () => {
    const belumMasuk = vi.fn();
    const blok = await tanyaDengan(peladen(JAWABAN, () => new Response("{}", { status: 401 })), belumMasuk);
    pilih(blok, "membantu");
    fireEvent.click(within(blok).getByRole("button", { name: MIKROKOPI.tombolKirimPenilaian }));
    await waitFor(() => expect(belumMasuk).toHaveBeenCalled());
  });
});
