import { describe, expect, test } from "vitest";

import {
  JALUR_KELUAR,
  JALUR_MASUK,
  JALUR_PERCAKAPAN,
  JALUR_TANYA,
  bacaPercakapan,
  daftarPercakapan,
  keluar,
  masuk,
  tanya,
  type Pemanggil,
} from "./klien";
import type { Tanggapan } from "./kontrak";

const ID = "3f1c9a2e-7b4d-4c1e-9a0f-2d6b8e5c1a47";

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

    await tanya("Bagaimana menyusun jadwal supervisi?", ID, pemanggil);

    expect(tercatat).toHaveLength(1);
    expect(tercatat[0]?.jalur).toBe(JALUR_TANYA);
    expect(tercatat[0]?.init?.method).toBe("POST");
    // R-17 fitur 027: tanpa token.
    // D-14 Bagian 4.1 sejak fitur 028: pertanyaan dan pengenal percakapan.
    expect(JSON.parse(String(tercatat[0]?.init?.body))).toEqual({
      pertanyaan: "Bagaimana menyusun jadwal supervisi?",
      id_percakapan: ID,
    });
    expect(JSON.stringify(tercatat[0]?.init?.headers ?? {})).not.toMatch(/authorization/i);
  });
});

describe("tanggapan sah", () => {
  test("tanggapan 200 berbentuk D-14 menjadi jawaban", async () => {
    const hasil = await tanya("x", ID, balasan(200, TANGGAPAN));
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
    const hasil = await tanya("x", ID, balasan(200, tidakDitemukan));
    expect(hasil.jenis).toBe("jawaban");
  });
});

describe("galat dipetakan ke keadaan layar", () => {
  test.each([
    // Fitur 029: 401 berarti sesi tidak sah — layar kembali ke S-01, bukan
    // menyatakan akun tidak berhak (D-14 Bagian 4.4).
    [401, "belum_masuk"],
    [403, "tidak_berhak"],
    [400, "pertanyaan_ditolak"],
    [413, "pertanyaan_ditolak"],
    [422, "pertanyaan_ditolak"],
    [404, "sistem"],
    [429, "sistem"],
    [500, "sistem"],
    [503, "sistem"],
  ] as const)("status %i menjadi %s", async (status, jenis) => {
    const hasil = await tanya("x", ID, balasan(status, { pesan: "rincian peladen" }));
    expect(hasil).toEqual({ jenis: "galat", galat: jenis });
  });

  test("hasil galat tidak membawa status maupun isi badan peladen (R-10)", async () => {
    const hasil = await tanya("x", ID, balasan(500, { pesan: "Traceback GALAT_INTERNAL" }));
    const teks = JSON.stringify(hasil);
    expect(teks).not.toContain("500");
    expect(teks).not.toContain("Traceback");
    expect(teks).not.toContain("GALAT_INTERNAL");
  });

  test("jaringan terputus menjadi luring (KL-E)", async () => {
    const putus: Pemanggil = async () => {
      throw new TypeError("Failed to fetch");
    };
    expect(await tanya("x", ID, putus)).toEqual({ jenis: "galat", galat: "luring" });
  });

  test("badan 200 yang bukan JSON menjadi galat sistem", async () => {
    const rusak: Pemanggil = async () => new Response("<html>", { status: 200 });
    expect(await tanya("x", ID, rusak)).toEqual({ jenis: "galat", galat: "sistem" });
  });
});

describe("bentuk 200 yang tidak dikenali ditolak, bukan ditampilkan separuh", () => {
  const bidang = Object.keys(TANGGAPAN) as (keyof Tanggapan)[];

  test.each(bidang)("tanpa bidang %s menjadi galat sistem", async (nama) => {
    const kurang: Record<string, unknown> = { ...TANGGAPAN };
    delete kurang[nama];
    expect(await tanya("x", ID, balasan(200, kurang))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("bidang tambahan menjadi galat sistem (C-20)", async () => {
    const lebih = { ...TANGGAPAN, skor_keyakinan: 0.9 };
    expect(await tanya("x", ID, balasan(200, lebih))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("status_dasar di luar keempat nilai menjadi galat sistem", async () => {
    const asing = { ...TANGGAPAN, status_dasar: "lemah" };
    expect(await tanya("x", ID, balasan(200, asing))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("sitasi berstatus dicabut menjadi galat sistem (C-07)", async () => {
    const dicabut = {
      ...TANGGAPAN,
      sitasi: [{ ...TANGGAPAN.sitasi[0], status_keberlakuan: "dicabut" }],
    };
    expect(await tanya("x", ID, balasan(200, dicabut))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("sitasi tanpa bagian menjadi galat sistem (FR-F11)", async () => {
    const tanpaBagian = { ...TANGGAPAN, sitasi: [{ ...TANGGAPAN.sitasi[0], bagian: undefined }] };
    expect(await tanya("x", ID, balasan(200, tanpaBagian))).toEqual({
      jenis: "galat",
      galat: "sistem",
    });
  });
});

// ── Riwayat — fitur 028 T-7 ─────────────────────────────────────────────

describe("riwayat percakapan", () => {
  const GILIRAN = { pertanyaan: "Bagaimana supervisi?", id_pesan: "p1", waktu: "2026-09-29T07:30:00Z" };

  test("daftar membaca jalur percakapan dengan GET", async () => {
    const tercatat: { jalur: string; init: RequestInit | undefined }[] = [];
    const pemanggil: Pemanggil = async (jalur, init) => {
      tercatat.push({ jalur, init });
      return new Response(JSON.stringify({ percakapan: [ID] }), { status: 200 });
    };
    expect(await daftarPercakapan(pemanggil)).toEqual({ jenis: "daftar", percakapan: [ID] });
    expect(tercatat[0]?.jalur).toBe(JALUR_PERCAKAPAN);
    expect(tercatat[0]?.init?.method ?? "GET").toBe("GET");
  });

  test("satu percakapan dibaca pada jalur bertemplat", async () => {
    let jalurDiminta = "";
    const pemanggil: Pemanggil = async (jalur) => {
      jalurDiminta = jalur;
      return new Response(JSON.stringify({ id_percakapan: ID, giliran: [GILIRAN] }), {
        status: 200,
      });
    };
    expect(await bacaPercakapan(ID, pemanggil)).toEqual({
      jenis: "percakapan",
      percakapan: { id_percakapan: ID, giliran: [GILIRAN] },
    });
    expect(jalurDiminta).toBe(`${JALUR_PERCAKAPAN}/${ID}`);
  });

  test("giliran yang membawa tanggapan ditolak (C-07)", async () => {
    const dengan = { id_percakapan: ID, giliran: [{ ...GILIRAN, tanggapan: { isi: "lama" } }] };
    expect(await bacaPercakapan(ID, balasan(200, dengan))).toEqual({
      jenis: "galat",
      galat: "sistem",
    });
  });

  test.each([
    [{ percakapan: "bukan larik" }],
    [{ percakapan: [ID], tambahan: 1 }],
    [{ percakapan: [1] }],
  ])("daftar berbentuk asing ditolak: %j", async (badan) => {
    expect(await daftarPercakapan(balasan(200, badan))).toEqual({ jenis: "galat", galat: "sistem" });
  });

  test("galat dan jaringan putus dipetakan seperti /tanya", async () => {
    expect(await daftarPercakapan(balasan(403, {}))).toEqual({ jenis: "galat", galat: "tidak_berhak" });
    expect(await bacaPercakapan(ID, balasan(404, {}))).toEqual({ jenis: "galat", galat: "sistem" });
    const putus: Pemanggil = async () => {
      throw new TypeError("Failed to fetch");
    };
    expect(await daftarPercakapan(putus)).toEqual({ jenis: "galat", galat: "luring" });
  });

  test("pengenal dikodekan pada jalur", async () => {
    let jalurDiminta = "";
    const pemanggil: Pemanggil = async (jalur) => {
      jalurDiminta = jalur;
      return new Response("{}", { status: 404 });
    };
    await bacaPercakapan("a/b", pemanggil);
    expect(jalurDiminta).toBe(`${JALUR_PERCAKAPAN}/a%2Fb`);
  });
});


// ── fitur 029 · masuk dan keluar — D-14 Bagian 4.4 ─────────────────────

describe("masuk", () => {
  test("mengirim dua bidang sebagai JSON, tanpa tajuk lain", async () => {
    const panggilan: [string, RequestInit | undefined][] = [];
    const pemanggil: Pemanggil = async (jalur, init) => {
      panggilan.push([jalur, init]);
      return new Response(null, { status: 204 });
    };
    expect(await masuk("ks-017", "abcd-efgh", pemanggil)).toEqual({ jenis: "masuk" });
    expect(panggilan).toHaveLength(1);
    const [jalur, init] = panggilan[0] ?? ["", undefined];
    expect(jalur).toBe(JALUR_MASUK);
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(String(init?.body))).toEqual({ nama_pengguna: "ks-017", sandi: "abcd-efgh" });
  });

  test.each([
    [401, { jenis: "ditolak" }],
    [400, { jenis: "ditolak" }],
    [500, { jenis: "galat", galat: "sistem" }],
    [503, { jenis: "galat", galat: "sistem" }],
  ] as const)("status %i", async (status, harapan) => {
    expect(await masuk("ks-017", "x", balasan(status, { galat: {} }))).toEqual(harapan);
  });

  test("tanpa sambungan menjadi luring", async () => {
    const putus: Pemanggil = async () => {
      throw new TypeError("Failed to fetch");
    };
    expect(await masuk("ks-017", "x", putus)).toEqual({ jenis: "galat", galat: "luring" });
  });
});

describe("keluar", () => {
  test("POST berbadan JSON kosong ke rute keluar", async () => {
    const panggilan: [string, RequestInit | undefined][] = [];
    await keluar(async (jalur, init) => {
      panggilan.push([jalur, init]);
      return new Response(null, { status: 204 });
    });
    const [jalur, init] = panggilan[0] ?? ["", undefined];
    expect(jalur).toBe(JALUR_KELUAR);
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({ "Content-Type": "application/json" });
    expect(init?.body).toBe("{}");
  });

  test("tidak melempar meski peladen tak terjangkau", async () => {
    await expect(
      keluar(async () => {
        throw new TypeError("Failed to fetch");
      }),
    ).resolves.toBeUndefined();
  });
});
