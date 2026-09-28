import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import type { Pemanggil } from "../klien";
import type { Tanggapan } from "../kontrak";
import { bacaDraf, type Simpanan } from "../draf";
import { MIKROKOPI, PENANDA_DASAR, PESAN_GALAT } from "../mikrokopi";
import { LayarTanya } from "./LayarTanya";

afterEach(cleanup);

const DASAR: Tanggapan = {
  id_pesan: "pesan-1",
  status_dasar: "kuat",
  ringkasan_tindakan: [
    "Susun jadwal supervisi bersama guru.",
    "Umumkan jadwal di rapat pekan ini.",
  ],
  penjelasan: "Supervisi akademik dilakukan terjadwal dan diketahui guru.",
  klaim: [{ teks: "Supervisi terjadwal.", id_segmen: ["seg-1"] }],
  sitasi: [
    {
      id_dokumen: "dok-1",
      judul: "Peraturan Menteri Nomor 1",
      penerbit: "Kementerian Pendidikan",
      tahun: 2026,
      bagian: "Pasal 7 ayat (2)",
      status_keberlakuan: "berlaku",
      rujukan_pengganti: null,
      tautan: "https://contoh.go.id/permen-1",
    },
  ],
  bacaan_lanjutan: [],
  catatan_keberlakuan: "",
  penafian: "Keputusan akhir berada pada kepala sekolah.",
  versi: { model: "m", indeks: "i", kode: "k" },
};

const TIDAK_DITEMUKAN: Tanggapan = {
  ...DASAR,
  status_dasar: "tidak_ditemukan",
  ringkasan_tindakan: [],
  penjelasan: "",
  klaim: [],
  sitasi: [],
};

const DI_LUAR_DOMAIN: Tanggapan = {
  ...TIDAK_DITEMUKAN,
  status_dasar: "di_luar_domain",
  penjelasan: "Layanan ini menjawab persoalan pengelolaan sekolah dasar.",
};

function simpananPeta(): Simpanan {
  const isi = new Map<string, string>();
  return {
    getItem: (k) => isi.get(k) ?? null,
    setItem: (k, v) => void isi.set(k, v),
    removeItem: (k) => void isi.delete(k),
  };
}

const simpananMenolak: Simpanan = {
  getItem: () => null,
  setItem: () => {
    throw new DOMException("kuota penuh", "QuotaExceededError");
  },
  removeItem: () => undefined,
};

function balasan(status: number, badan: unknown): Pemanggil {
  return async () => new Response(JSON.stringify(badan), { status });
}

const putus: Pemanggil = async () => {
  throw new TypeError("Failed to fetch");
};

function pasang(
  pemanggil: Pemanggil,
  simpanan: Simpanan | null = simpananPeta(),
  salin: (teks: string) => Promise<void> = async () => undefined,
) {
  return render(<LayarTanya pemanggil={pemanggil} simpanan={simpanan} salin={salin} />);
}

function ketik(teks: string): void {
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelPertanyaan), { target: { value: teks } });
}

function kirim(): void {
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolKirim }));
}

async function tanyaDan(tanggapan: Tanggapan): Promise<HTMLElement> {
  pasang(balasan(200, tanggapan));
  ketik("Bagaimana menyusun jadwal supervisi?");
  kirim();
  return screen.findByTestId("blok-jawaban");
}

function mendahului(a: Node, b: Node): boolean {
  return (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
}

// ── KL-B · kosong pertama kali ─────────────────────────────────────────

test("KL-B: layar pertama menjelaskan apa yang dapat ditanyakan", () => {
  pasang(balasan(200, DASAR));
  expect(screen.getByText(MIKROKOPI.kosongJudul)).toBeTruthy();
  expect(screen.getByText(MIKROKOPI.kosongIsi)).toBeTruthy();
});

test("pertanyaan kosong tidak dikirim", () => {
  const pemanggil = vi.fn(balasan(200, DASAR));
  pasang(pemanggil);
  ketik("   ");
  kirim();
  expect(pemanggil).not.toHaveBeenCalled();
});

// ── KL-A · memuat ──────────────────────────────────────────────────────

test("KL-A: kerangka blok jawaban tampil selama menunggu, bukan pemutar", async () => {
  pasang(() => new Promise<Response>(() => undefined));
  ketik("Pertanyaan");
  kirim();
  const kerangka = await screen.findByTestId("kerangka-jawaban");
  expect(kerangka.getAttribute("aria-busy")).toBe("true");
  expect(screen.getByRole("status").textContent).toBe(MIKROKOPI.memuat);
  expect(screen.queryByText(MIKROKOPI.kosongJudul)).toBeNull();
});

// ── Susunan jawaban · R-02, R-03 ────────────────────────────────────────

describe("susunan jawaban", () => {
  test("penanda dasar rujukan tampil sebelum ringkasan, berupa teks", async () => {
    const blok = await tanyaDan(DASAR);
    const penanda = within(blok).getByTestId("penanda-dasar");
    expect(penanda.textContent).toBe(PENANDA_DASAR.kuat);
    const butir = within(blok).getByText(DASAR.ringkasan_tindakan[0] ?? "");
    expect(mendahului(penanda, butir)).toBe(true);
  });

  test("penanda tidak memuat angka (FR-F06)", async () => {
    const blok = await tanyaDan({ ...DASAR, status_dasar: "terbatas" });
    expect(within(blok).getByTestId("penanda-dasar").textContent).not.toMatch(/\d/);
  });

  test("ringkasan paling banyak tiga butir", async () => {
    const empat = {
      ...DASAR,
      ringkasan_tindakan: ["Satu.", "Dua.", "Tiga.", "Empat yang dipotong."],
    };
    const blok = await tanyaDan(empat);
    const daftar = within(blok).getByTestId("ringkasan");
    expect(within(daftar).getAllByRole("listitem")).toHaveLength(3);
    expect(within(blok).queryByText("Empat yang dipotong.")).toBeNull();
  });

  test("penafian tampak pada jawaban normal", async () => {
    const blok = await tanyaDan(DASAR);
    expect(within(blok).getByText(DASAR.penafian)).toBeTruthy();
  });
});

// ── KL-G dan di luar domain · R-04, R-05 ───────────────────────────────

describe("tidak_ditemukan dan di_luar_domain adalah jawaban, bukan galat", () => {
  test.each([
    ["tidak_ditemukan", TIDAK_DITEMUKAN],
    ["di_luar_domain", DI_LUAR_DOMAIN],
  ] as const)("%s memakai blok jawaban yang sama dan penafiannya tampak", async (_, t) => {
    const blok = await tanyaDan(t);
    expect(within(blok).getByTestId("penanda-dasar").textContent).toBe(
      PENANDA_DASAR[t.status_dasar],
    );
    expect(within(blok).getByText(t.penafian)).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("tidak_ditemukan berpenjelasan kosong memakai kalimat pertama D-05 (K-2)", async () => {
    const blok = await tanyaDan(TIDAK_DITEMUKAN);
    expect(within(blok).getByText(MIKROKOPI.tidakDitemukanPenjelasan)).toBeTruthy();
  });

  test("di_luar_domain menampilkan penjelasan tanggapan apa adanya", async () => {
    const blok = await tanyaDan(DI_LUAR_DOMAIN);
    expect(within(blok).getByText(DI_LUAR_DOMAIN.penjelasan)).toBeTruthy();
  });
});

// ── Dasar rujukan dan bacaan lanjutan · R-06, R-07 ──────────────────────

describe("dasar rujukan", () => {
  test("baris sitasi memuat judul, tahun, dan bagian", async () => {
    const blok = await tanyaDan(DASAR);
    const rujukan = within(blok).getByTestId("dasar-rujukan");
    const teks = rujukan.textContent ?? "";
    expect(teks).toContain("Peraturan Menteri Nomor 1");
    expect(teks).toContain("2026");
    expect(teks).toContain("Pasal 7 ayat (2)");
    expect(within(rujukan).queryByText(MIKROKOPI.penandaDiubah)).toBeNull();
  });

  test("sitasi diubah menampilkan penanda, pengubah, dan catatan keberlakuan", async () => {
    const diubah: Tanggapan = {
      ...DASAR,
      sitasi: [
        {
          ...(DASAR.sitasi[0] as Tanggapan["sitasi"][number]),
          status_keberlakuan: "diubah",
          rujukan_pengganti: "Peraturan Menteri Nomor 5 Tahun 2026",
        },
      ],
      catatan_keberlakuan: "Pasal 7 diubah oleh Peraturan Menteri Nomor 5.",
    };
    const blok = await tanyaDan(diubah);
    const rujukan = within(blok).getByTestId("dasar-rujukan");
    expect(within(rujukan).getByText(MIKROKOPI.penandaDiubah)).toBeTruthy();
    expect(rujukan.textContent).toContain("Peraturan Menteri Nomor 5 Tahun 2026");
    expect(within(blok).getByText(diubah.catatan_keberlakuan)).toBeTruthy();
  });

  test("tautan berskema selain web tidak dipasang sebagai tautan", async () => {
    const jahat: Tanggapan = {
      ...DASAR,
      sitasi: [
        {
          ...(DASAR.sitasi[0] as Tanggapan["sitasi"][number]),
          tautan: "javascript:alert(1)",
        },
      ],
    };
    const blok = await tanyaDan(jahat);
    expect(within(blok).queryByRole("link")).toBeNull();
    expect(blok.innerHTML).not.toContain("javascript:");
  });

  test("bacaan lanjutan berada pada blok terpisah beserta keterangannya", async () => {
    const dengan: Tanggapan = {
      ...DASAR,
      bacaan_lanjutan: [{ judul: "Panduan Supervisi Terbitan Swasta", tautan: "https://b.id" }],
    };
    const blok = await tanyaDan(dengan);
    const bacaan = within(blok).getByTestId("bacaan-lanjutan");
    const rujukan = within(blok).getByTestId("dasar-rujukan");
    expect(within(bacaan).getByText("Panduan Supervisi Terbitan Swasta")).toBeTruthy();
    expect(within(bacaan).getByText(MIKROKOPI.keteranganBacaanLanjutan)).toBeTruthy();
    expect(rujukan.contains(bacaan)).toBe(false);
    expect(bacaan.contains(rujukan)).toBe(false);
    expect(within(rujukan).queryByText("Panduan Supervisi Terbitan Swasta")).toBeNull();
  });
});

// ── Tindakan ─────────────────────────────────────────────────────────────

test("salin ringkasan menyalin butir ringkasan dan mengabarkannya", async () => {
  const salin = vi.fn(async () => undefined);
  pasang(balasan(200, DASAR), simpananPeta(), salin);
  ketik("Pertanyaan");
  kirim();
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolSalinRingkasan }));
  expect(await screen.findByText(MIKROKOPI.salinBerhasil)).toBeTruthy();
  expect(salin).toHaveBeenCalledWith(DASAR.ringkasan_tindakan.join("\n"));
});

test("salinan yang ditolak peramban dikabarkan, bukan diam", async () => {
  pasang(balasan(200, DASAR), simpananPeta(), async () => {
    throw new Error("izin ditolak");
  });
  ketik("Pertanyaan");
  kirim();
  fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolSalinRingkasan }));
  expect(await screen.findByText(MIKROKOPI.salinTidakBisa)).toBeTruthy();
});

// ── KL-D dan KL-E · R-10 ────────────────────────────────────────────────

describe("galat", () => {
  test("KL-D: galat peladen tampil sebagai kalimat manusia tanpa kode", async () => {
    pasang(balasan(500, { pesan: "Traceback GALAT_INTERNAL" }));
    ketik("Pertanyaan");
    kirim();
    const peringatan = await screen.findByRole("alert");
    expect(peringatan.textContent).toContain(PESAN_GALAT.sistem.tersimpan);
    expect(document.body.textContent).not.toMatch(/500|Traceback|GALAT_INTERNAL/);
    expect(screen.getByRole("button", { name: MIKROKOPI.tombolCobaLagi })).toBeTruthy();
  });

  test("coba lagi mengirim ulang pertanyaan yang sama", async () => {
    const pemanggil = vi
      .fn<Pemanggil>()
      .mockImplementationOnce(putus)
      .mockImplementationOnce(balasan(200, DASAR));
    pasang(pemanggil);
    ketik("Pertanyaan yang sama");
    kirim();
    fireEvent.click(await screen.findByRole("button", { name: MIKROKOPI.tombolCobaLagi }));
    await screen.findByTestId("blok-jawaban");
    expect(pemanggil).toHaveBeenCalledTimes(2);
    const badan = (n: number) => JSON.parse(String(pemanggil.mock.calls[n]?.[1]?.body));
    expect(badan(1)).toEqual(badan(0));
  });

  test("KL-E: koneksi terputus dinyatakan, draf dinyatakan tersimpan", async () => {
    pasang(putus);
    ketik("Pertanyaan");
    kirim();
    expect((await screen.findByRole("alert")).textContent).toContain(
      PESAN_GALAT.luring.tersimpan,
    );
  });

  test("KL-E: tidak menyatakan tersimpan bila simpanan lokal menolak (M-14)", async () => {
    pasang(putus, simpananMenolak);
    ketik("Pertanyaan");
    kirim();
    const teks = (await screen.findByRole("alert")).textContent ?? "";
    expect(teks).toContain(PESAN_GALAT.luring.tidakTersimpan);
    expect(teks).not.toContain("tersimpan");
  });

  test("KL-D: tidak menyatakan tersimpan bila simpanan lokal tidak ada", async () => {
    pasang(balasan(503, {}), null);
    ketik("Pertanyaan");
    kirim();
    const teks = (await screen.findByRole("alert")).textContent ?? "";
    expect(teks).toContain(PESAN_GALAT.sistem.tidakTersimpan);
    expect(teks).not.toContain("tersimpan");
  });
});

// ── Draf · R-09 ─────────────────────────────────────────────────────────

describe("draf pertanyaan", () => {
  test("bertahan sesudah kiriman gagal dan muat ulang", async () => {
    const simpanan = simpananPeta();
    const pertama = pasang(putus, simpanan);
    ketik("Pertanyaan yang tidak boleh hilang");
    kirim();
    await screen.findByRole("alert");
    pertama.unmount();

    pasang(putus, simpanan);
    expect((screen.getByLabelText(MIKROKOPI.labelPertanyaan) as HTMLTextAreaElement).value).toBe(
      "Pertanyaan yang tidak boleh hilang",
    );
  });

  test("bertahan sesudah muat ulang tanpa dikirim", () => {
    const simpanan = simpananPeta();
    const pertama = pasang(putus, simpanan);
    ketik("Masih diketik");
    pertama.unmount();

    pasang(putus, simpanan);
    expect((screen.getByLabelText(MIKROKOPI.labelPertanyaan) as HTMLTextAreaElement).value).toBe(
      "Masih diketik",
    );
  });

  test("disimpan saat kiriman gagal meski simpanan sempat kosong", async () => {
    // M-6: draf wajib ditulis pada saat galat, bukan hanya saat mengetik.
    const simpanan = simpananPeta();
    pasang(putus, simpanan);
    ketik("Pertanyaan");
    simpanan.removeItem("smart-coaching:draf-tanya");
    kirim();
    await screen.findByRole("alert");
    expect(bacaDraf(simpanan)).toBe("Pertanyaan");
  });

  test("dihapus sesudah jawaban diterima; pertanyaan tetap dapat disunting", async () => {
    const simpanan = simpananPeta();
    pasang(balasan(200, DASAR), simpanan);
    ketik("Pertanyaan");
    kirim();
    await screen.findByTestId("blok-jawaban");
    expect(bacaDraf(simpanan)).toBe("");
    expect((screen.getByLabelText(MIKROKOPI.labelPertanyaan) as HTMLTextAreaElement).value).toBe(
      "Pertanyaan",
    );
  });
});
