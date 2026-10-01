import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { JALUR_MASUK, type Pemanggil } from "../klien";
import { MIKROKOPI } from "../mikrokopi";
import { LayarMasuk } from "./LayarMasuk";

afterEach(cleanup);

function balasan(status: number): Pemanggil {
  return async () => new Response(status === 204 ? null : "{}", { status });
}

function isiNama(teks: string): void {
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelNamaPengguna), { target: { value: teks } });
}

function isiSandi(teks: string): void {
  fireEvent.change(screen.getByLabelText(MIKROKOPI.labelSandi), { target: { value: teks } });
}

function tekanMasuk(): void {
  fireEvent.click(screen.getByRole("button", { name: MIKROKOPI.tombolMasuk }));
}

test("S-01: judul, dua isian berlabel, tombol, dan cara menghubungi tim", () => {
  render(<LayarMasuk pemanggil={balasan(204)} berhasil={() => undefined} />);
  expect(screen.getByRole("heading", { name: MIKROKOPI.judulMasuk })).toBeTruthy();
  expect(screen.getByText(MIKROKOPI.petunjukNamaPengguna)).toBeTruthy();
  expect(screen.getByText(MIKROKOPI.lupaSandi)).toBeTruthy();
});

test("R-08 · M-15: isian sandi tersamar dan dikenali pengelola sandi peramban", () => {
  render(<LayarMasuk pemanggil={balasan(204)} berhasil={() => undefined} />);
  const sandi = screen.getByLabelText(MIKROKOPI.labelSandi);
  expect(sandi.getAttribute("type")).toBe("password");
  expect(sandi.getAttribute("autocomplete")).toBe("current-password");
  const nama = screen.getByLabelText(MIKROKOPI.labelNamaPengguna);
  expect(nama.getAttribute("autocomplete")).toBe("username");
  // Papan ketik ponsel membesarkan huruf pertama; sandi dan nama akun huruf
  // kecil semua, dan peladen tidak melonggarkan pembandingan (KB-156).
  for (const isian of [nama, sandi]) {
    expect(isian.getAttribute("autocapitalize")).toBe("none");
    expect(isian.getAttribute("spellcheck")).toBe("false");
  }
});

test("isian kosong tidak dikirim", () => {
  const pemanggil = vi.fn(balasan(204));
  render(<LayarMasuk pemanggil={pemanggil} berhasil={() => undefined} />);
  isiNama("ks-017");
  tekanMasuk();
  expect(pemanggil).not.toHaveBeenCalled();
  expect(screen.getByRole("alert").textContent).toBe(MIKROKOPI.masukKosong);
});

test("berhasil memanggil `berhasil` sekali, ke rute masuk", async () => {
  const pemanggil = vi.fn(balasan(204));
  const berhasil = vi.fn();
  render(<LayarMasuk pemanggil={pemanggil} berhasil={berhasil} />);
  isiNama("ks-017");
  isiSandi("abcd-efgh-jkmn-pqrs");
  tekanMasuk();
  await vi.waitFor(() => expect(berhasil).toHaveBeenCalledTimes(1));
  expect(pemanggil.mock.calls[0]?.[0]).toBe(JALUR_MASUK);
});

test("tombol nonaktif selama memeriksa — KL-A", async () => {
  let lepas: (r: Response) => void = () => undefined;
  const pemanggil: Pemanggil = () => new Promise((r) => (lepas = r));
  render(<LayarMasuk pemanggil={pemanggil} berhasil={() => undefined} />);
  isiNama("ks-017");
  isiSandi("x");
  tekanMasuk();
  const tombol = screen.getByRole("button", { name: MIKROKOPI.tombolMasuk }) as HTMLButtonElement;
  expect(tombol.disabled).toBe(true);
  lepas(new Response("{}", { status: 401 }));
  await vi.waitFor(() => expect(tombol.disabled).toBe(false));
});

test.each([
  [401, MIKROKOPI.masukDitolak],
  [400, MIKROKOPI.masukDitolak],
  [500, MIKROKOPI.masukGangguan],
])("status %i menampilkan kalimat D-05 S-01 dan mengosongkan sandi", async (status, kalimat) => {
  const berhasil = vi.fn();
  render(<LayarMasuk pemanggil={balasan(status)} berhasil={berhasil} />);
  isiNama("ks-017");
  isiSandi("salah-salah");
  tekanMasuk();
  expect((await screen.findByRole("alert")).textContent).toBe(kalimat);
  // R-08: sandi tidak dipertahankan sesudah dikirim.
  expect((screen.getByLabelText(MIKROKOPI.labelSandi) as HTMLInputElement).value).toBe("");
  expect((screen.getByLabelText(MIKROKOPI.labelNamaPengguna) as HTMLInputElement).value).toBe("ks-017");
  expect(berhasil).not.toHaveBeenCalled();
});

test("KL-E: tanpa sambungan", async () => {
  const putus: Pemanggil = async () => {
    throw new TypeError("Failed to fetch");
  };
  render(<LayarMasuk pemanggil={putus} berhasil={() => undefined} />);
  isiNama("ks-017");
  isiSandi("x");
  tekanMasuk();
  expect((await screen.findByRole("alert")).textContent).toBe(MIKROKOPI.masukLuring);
});
