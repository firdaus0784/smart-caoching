// Uji asap rantai alat — T-2 fitur 027, R-19.
//
// Yang dibuktikan bukan layar, melainkan bahwa kelima alat bekerja bersama:
// TypeScript mode ketat, React, react-dom, jsdom, dan Testing Library. Uji ini
// sengaja tidak memuat kode aplikasi — layar belum ada, dan teks layar tunduk
// pada C-13 lewat `mikrokopi.ts` (T-4). Elemennya disusun di dalam uji ini.
import { render } from "@testing-library/react";
import { createElement } from "react";
import { expect, test } from "vitest";

test("React merender ke jsdom dan Testing Library dapat membacanya", () => {
  const { container } = render(createElement("output", { "data-asap": "ya" }));
  const keluaran = container.querySelector("output");
  expect(keluaran?.getAttribute("data-asap")).toBe("ya");
});
