import { describe, expect, test } from "vitest";

import { JALUR_TANYA, tanya, type Pemanggil } from "./klien";
import type { Tanggapan } from "./kontrak";

const TANGGAPAN: Tanggapan = {
  id_pesan: "pesan-1",
  status_dasar: "kuat",
  ringkasan_tindakan: ["Susun jadwal supervisi bersama guru."],
  penjelasan: "Supervisi akademik dilakukan terjadwal.",
  klaim: [{ teks: "Supervisi terjadwal.", id_segmen: ["seg-1"] }],
  sitasi: [
    {
      id_dokumen: "dok-1",
      judul: "Peraturan Menteri",
      penerbit: "Kementerian",
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

function balasan(status: number, badan: unknown): Pemanggil {
  return async () => new Response(JSON.stringify(badan), { status });
}

describe("permintaan", () => {
  test("mengirim POST berisi pertanyaan saja ke jalur tanya", async () => {
    const tercatat: { jalur: string; init: RequestInit | undefined }[] = [];
    const pemanggil: Pemanggil = async (jalur, init) => {
      tercatat.push({ jalur: String(jalur), init });
      return new Response(JSON.stringify(TANGGAPAN), { status: 200 });
    };

    await tanya("Bagaimana menyusun jadwal supervisi?", pemanggil);

    expect(tercatat).toHaveLength(1);
    expect(tercatat[0]?.jalur).toBe(JALUR_TANYA);
    expect(tercatat[0]?.init?.method).toBe("POST");
    // R-16: badan permintaan tidak bertambah bidang; R-17: tanpa token.
    expect(JSON.parse(String(tercatat[0]?.init?.body))).toEqual({
      pertanyaan: "Bagaimana menyusun jadwal supervisi?",
    });
    expect(JSON.stringify(tercatat[0]?.init?.headers ?? {})).not.toMatch(/authorization/i);
  });
});

describe("tanggapan sah", () => {
  test("tanggapan 200 berbentuk D-14 menjadi jawaban", async () => {
    const hasil = await tanya("x", balasan(200, TANGGAPAN));
    expect(hasil).toEqual({ jenis: "jawaban", tanggapan: TANGGAPAN });
  });

  test("tidak_ditemukan adalah jawaban, bukan galat (KL-G)", async () => {
    const tidakDitemukan: Tanggapan = {
      ...TANGGAPAN,
      status_dasar: "tidak_ditemukan",
      ringkasan_tindakan: [],
      klaim: [],
      sitasi: [],
      penjelasan: "",
    };
    const hasil = await tanya("x", balasan(200, tidakDitemukan));
    expect(hasil.jenis).toBe("jawaban");
  });
});

describe("galat dipetakan ke keadaan layar", () => {
  test.each([
    [401, "tidak_berhak"],
    [403, "tidak_berhak"],
    [400, "pertanyaan_ditolak"],
    [413, "pertanyaan_ditolak"],
    [422, "pertanyaan_ditolak"],
    [404, "sistem"],
    [429, "sistem"],
    [500, "sistem"],
    [503, "sistem"],
  ] as const)("status %i menjadi %s", async (status, jenis) => {
    const hasil = await tanya("x", balasan(status, { pesan: "rincian peladen" }));
    expect(hasil).toEqual({ jenis: "galat", galat: jenis });
  });

  test("hasil galat tidak membawa status maupun isi badan peladen (R-10)", async () => {
    const hasil = await tanya("x", balasan(500, { pesan: "Traceback GALAT_INTERNAL" }));
    const teks = JSON.stringify(hasil);
    expect(teks).not.toContain("500");
    expect(teks).not.toContain("Traceback");
    expect(teks).not.toContain("GALAT_INTERNAL");
  });

  test("jaringan terputus menjadi luring (KL-E)", async () => {
    const putus: Pemanggil = async () => {
      throw new TypeError("Failed to fetch");
    };
    expect(await tanya("x", putus)).toEqual({ jenis: "galat", galat: "luring" });
  });

  test("badan 200 yang bukan JSON menjadi galat sistem", async () => {
    const rusak: Pemanggil = async () => new Response("<html>", { status: 200 });
    expect(await tanya("x", rusak)).toEqual({ jenis: "galat", galat: "sistem" });
  });
});

describe("bentuk 200 yang tidak dikenali ditolak, bukan ditampilkan separuh", () => {
  const bidang = Object.keys(TANGGAPAN) as (keyof Tanggapan)[];

  test.each(bidang)("tanpa bidang %s menjadi galat sistem", async (nama) => {
    const kurang: Record<string, unknown> = { ...TANGGAPAN };
    delete kurang[nama];
    expect(await tanya("x", balasan(200, kurang))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("bidang tambahan menjadi galat sistem (C-20)", async () => {
    const lebih = { ...TANGGAPAN, skor_keyakinan: 0.9 };
    expect(await tanya("x", balasan(200, lebih))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("status_dasar di luar keempat nilai menjadi galat sistem", async () => {
    const asing = { ...TANGGAPAN, status_dasar: "lemah" };
    expect(await tanya("x", balasan(200, asing))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("sitasi berstatus dicabut menjadi galat sistem (C-07)", async () => {
    const dicabut = {
      ...TANGGAPAN,
      sitasi: [{ ...TANGGAPAN.sitasi[0], status_keberlakuan: "dicabut" }],
    };
    expect(await tanya("x", balasan(200, dicabut))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("sitasi tanpa bagian menjadi galat sistem (FR-F11)", async () => {
    const tanpaBagian = { ...TANGGAPAN, sitasi: [{ ...TANGGAPAN.sitasi[0], bagian: undefined }] };
    expect(await tanya("x", balasan(200, tanpaBagian))).toEqual({
      jenis: "galat",
      galat: "sistem",
    });
  });
});
