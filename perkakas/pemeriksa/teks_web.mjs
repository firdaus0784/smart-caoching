// Pengumpul teks antarmuka `web/src` — T-4 fitur 027, R-12, C-13.
//
// Dipanggil `perkakas/pemeriksa/bahasa_antarmuka.py`; keluarannya JSON pada
// stdout. Pemeriksaannya sendiri di Python, bersama aturan C-13 lainnya —
// berkas ini hanya membaca pohon sintaks.
//
// Pengurainya `rolldown/parseAst`, bagian dari `vite` yang sudah terkunci
// pada `[npm.terkunci]` (KB-130). Pengurai sungguhan, bukan pola teks: pola
// tidak dapat membedakan teks JSX dari perbandingan `a > b` atau tipe generik.
//
// Tiga kumpulan:
//   mikrokopi — seluruh untai pada `web/src/mikrokopi.ts` (C-13 Aturan 1)
//   harfiah   — teks harfiah pada `.tsx` di luar uji (C-13 Aturan 2)
//   pengenal  — nama pengenal pengikat pada `.ts`/`.tsx` di luar uji (C-14,
//               C-15; sejak R-20 ditagih sesudah T-6, KB-133)

import { existsSync, readFileSync, readdirSync } from "node:fs";
import { createRequire } from "node:module";
import { join, relative } from "node:path";
import { pathToFileURL } from "node:url";

const [web] = process.argv.slice(2);
if (!web) {
  console.error("pemakaian: node teks_web.mjs <direktori web>");
  process.exit(2);
}

const wajib = createRequire(join(web, "package.json"));
const { parseAst } = await import(pathToFileURL(wajib.resolve("rolldown/parseAst")).href);

/** Atribut yang isinya dibaca atau didengar pengguna. */
const ATRIBUT_TEKS = new Set([
  "alt",
  "aria-label",
  "aria-description",
  "aria-placeholder",
  "aria-roledescription",
  "aria-valuetext",
  "label",
  "placeholder",
  "title",
]);

function berkasDi(dir) {
  const hasil = [];
  for (const isi of readdirSync(dir, { withFileTypes: true })) {
    const jalur = join(dir, isi.name);
    if (isi.isDirectory()) hasil.push(...berkasDi(jalur));
    else hasil.push(jalur);
  }
  return hasil.sort();
}

function pembuatBaris(sumber) {
  const awal = [0];
  for (let i = 0; i < sumber.length; i++) if (sumber[i] === "\n") awal.push(i + 1);
  return (posisi) => {
    let lo = 0;
    let hi = awal.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (awal[mid] <= posisi) lo = mid;
      else hi = mid - 1;
    }
    return lo + 1;
  };
}

/** Untai bukan teks antarmuka: sumber impor, tipe, dan kunci objek. */
function bukanTeks(simpul, induk) {
  if (!induk) return false;
  if (induk.type === "TSLiteralType") return true;
  if (
    induk.source === simpul &&
    /^(Import|Export(Named|All)?)Declaration$|^ImportExpression$/.test(induk.type)
  )
    return true;
  if ((induk.type === "Property" || induk.type === "PropertyDefinition") && induk.key === simpul)
    return true;
  return false;
}

function jalan(simpul, induk, kunjungi) {
  if (Array.isArray(simpul)) {
    for (const butir of simpul) jalan(butir, induk, kunjungi);
    return;
  }
  if (!simpul || typeof simpul !== "object" || typeof simpul.type !== "string") return;
  if (kunjungi(simpul, induk) === false) return;
  for (const [kunci, nilai] of Object.entries(simpul)) {
    if (kunci === "parent" || kunci === "loc" || kunci === "range") continue;
    if (nilai && typeof nilai === "object") jalan(nilai, simpul, kunjungi);
  }
}

function teksTemplat(simpul) {
  return simpul.quasis.map((q) => q.value.cooked ?? q.value.raw).join(" … ");
}

/**
 * Nama pengenal **pengikat** — sejajar `ast` Store pada pemeriksa Python C-14
 * dan C-15: deklarasi, parameter, kunci objek, bidang antarmuka. Bukan
 * rujukan ke nama milik pustaka, bukan komentar, bukan untai.
 */
function pengenalPengikat(program, catat) {
  const pola = (p) => {
    if (!p) return;
    if (p.type === "Identifier") catat(p.name, p.start);
    else if (p.type === "ObjectPattern")
      for (const s of p.properties) pola(s.type === "RestElement" ? s.argument : s.value);
    else if (p.type === "ArrayPattern") for (const e of p.elements) pola(e);
    else if (p.type === "RestElement") pola(p.argument);
    else if (p.type === "AssignmentPattern") pola(p.left);
    else if (p.type === "TSParameterProperty") pola(p.parameter);
  };
  const kunci = (k) => {
    if (!k) return;
    if (k.type === "Identifier") catat(k.name, k.start);
    else if (k.type === "Literal" && typeof k.value === "string") catat(k.value, k.start);
  };
  jalan(program, null, (simpul, induk) => {
    switch (simpul.type) {
      case "FunctionDeclaration":
      case "FunctionExpression":
      case "ArrowFunctionExpression":
        if (simpul.id) catat(simpul.id.name, simpul.id.start);
        for (const p of simpul.params) pola(p);
        break;
      case "ClassDeclaration":
      case "ClassExpression":
      case "TSInterfaceDeclaration":
      case "TSTypeAliasDeclaration":
      case "TSEnumDeclaration":
        if (simpul.id) catat(simpul.id.name, simpul.id.start);
        break;
      case "VariableDeclarator":
        pola(simpul.id);
        break;
      case "CatchClause":
        pola(simpul.param);
        break;
      case "MethodDefinition":
      case "PropertyDefinition":
      case "TSPropertySignature":
      case "TSMethodSignature":
        if (!simpul.computed) kunci(simpul.key);
        break;
      case "TSEnumMember":
        kunci(simpul.id);
        break;
      case "Property":
        if (induk && induk.type === "ObjectExpression" && !simpul.computed) kunci(simpul.key);
        break;
    }
    return true;
  });
}

const src = join(web, "src");
const keluaran = { mikrokopi: [], harfiah: [], galat_urai: [], pengenal: [] };

// `web/` tanpa `src/` menghasilkan kumpulan kosong; ketiadaan `mikrokopi.ts`
// dilaporkan pemeriksa C-13 sendiri.
for (const berkas of existsSync(src) ? berkasDi(src) : []) {
  const nama = relative(web, berkas);
  if (!/\.tsx?$/.test(berkas) || /\.test\.tsx?$/.test(berkas)) continue;
  const adalahMikrokopi = nama === join("src", "mikrokopi.ts");
  const adalahTsx = berkas.endsWith(".tsx");

  const sumber = readFileSync(berkas, "utf8");
  let program;
  try {
    program = parseAst(sumber, { lang: adalahTsx ? "tsx" : "ts" }, berkas);
  } catch (galat) {
    keluaran.galat_urai.push({ berkas: nama, pesan: String(galat.message).split("\n")[0] });
    continue;
  }
  const baris = pembuatBaris(sumber);

  pengenalPengikat(program, (namaPengenal, posisi) =>
    keluaran.pengenal.push({ berkas: nama, baris: baris(posisi), nama: namaPengenal }),
  );

  if (!adalahMikrokopi && !adalahTsx) continue;

  jalan(program, null, (simpul, induk) => {
    if (adalahMikrokopi) {
      if (simpul.type === "Literal" && typeof simpul.value === "string" && !bukanTeks(simpul, induk))
        keluaran.mikrokopi.push({ berkas: nama, baris: baris(simpul.start), teks: simpul.value });
      if (simpul.type === "TemplateLiteral")
        keluaran.mikrokopi.push({
          berkas: nama,
          baris: baris(simpul.start),
          teks: teksTemplat(simpul),
        });
      return true;
    }

    // Aturan 2 — `.tsx` di luar `mikrokopi.ts`.
    const catat = (jenis, teks, geser = 0) =>
      keluaran.harfiah.push({ berkas: nama, baris: baris(simpul.start + geser), jenis, teks });

    if (simpul.type === "JSXText") {
      // Teks JSX dimulai tepat sesudah `>`, termasuk baris baru dan spasi;
      // baris yang dilaporkan adalah baris kata pertamanya.
      const isi = simpul.value.trim();
      if (isi !== "") catat("teks JSX", isi, simpul.value.length - simpul.value.trimStart().length);
      return true;
    }
    if (simpul.type === "JSXAttribute") {
      const namaAtribut =
        simpul.name.type === "JSXNamespacedName"
          ? `${simpul.name.namespace.name}:${simpul.name.name.name}`
          : simpul.name.name;
      const nilai = simpul.value;
      if (!nilai) return false;
      if (nilai.type === "Literal" || nilai.type === "TemplateLiteral") {
        if (ATRIBUT_TEKS.has(namaAtribut))
          catat(`atribut ${namaAtribut}`, nilai.value ?? teksTemplat(nilai));
        return false; // `className="…"` dan sejenisnya bukan teks.
      }
      if (nilai.type === "JSXExpressionContainer" && ATRIBUT_TEKS.has(namaAtribut)) {
        const e = nilai.expression;
        if (e.type === "Literal" && typeof e.value === "string")
          catat(`atribut ${namaAtribut}`, e.value);
        if (e.type === "TemplateLiteral") catat(`atribut ${namaAtribut}`, teksTemplat(e));
      }
      return true;
    }
    if (simpul.type === "JSXExpressionContainer" && induk && /^JSX(Element|Fragment)$/.test(induk.type)) {
      const e = simpul.expression;
      if (e.type === "Literal" && typeof e.value === "string") catat("untai anak JSX", e.value);
      else if (e.type === "TemplateLiteral") catat("untai anak JSX", teksTemplat(e));
      else return true;
      return false;
    }
    if (
      simpul.type === "Literal" &&
      typeof simpul.value === "string" &&
      !bukanTeks(simpul, induk) &&
      /\p{L}/u.test(simpul.value) &&
      /\s/.test(simpul.value.trim())
    ) {
      catat("untai berkalimat", simpul.value);
    }
    return true;
  });
}

process.stdout.write(JSON.stringify(keluaran));
