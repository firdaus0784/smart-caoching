"""C-13 atas `web/` — T-4 fitur 027, R-12, NFR-19, D-05 Bagian 10.

Dua aturan pemeriksa bahasa antarmuka diperluas ke frontend. Aturan 1
membaca setiap untai `web/src/mikrokopi.ts`; Aturan 2 menolak teks harfiah
pada `.tsx` di luar berkas itu.

Uji yang menjalankan pengumpul memakai pohon `web/` buatan di direktori
sementara, dengan `node_modules` ditautkan ke milik repositori. Tiap uji
kegagalan memeriksa **sebab** yang dilaporkan (KB-098), dan tiap uji penolakan
berpasangan dengan uji yang membuktikan bentuk sah tidak ikut ditolak —
pemeriksa yang menyalak keliru adalah pemeriksa yang dimatikan orang.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from perkakas.pemeriksa.bahasa_antarmuka import (
    kumpulkan_teks_web,
    periksa_bahasa_antarmuka,
    periksa_bahasa_web,
)

AKAR = Path(__file__).resolve().parents[2]
WEB = AKAR / "web"

perlu_node = pytest.mark.skipif(
    shutil.which("node") is None or not (WEB / "node_modules").is_dir(),
    reason="Node atau web/node_modules tidak ada — jalankan `make setup`",
)

MIKROKOPI_SAH = (
    'export const MIKROKOPI = { judul: "Tanya", isi: "Setiap jawaban menyebut dasarnya." };\n'
)


def _pohon(tmp_path: Path, mikrokopi: str = MIKROKOPI_SAH, **tsx: str) -> Path:
    src = tmp_path / "web" / "src"
    src.mkdir(parents=True)
    shutil.copy(WEB / "package.json", tmp_path / "web" / "package.json")
    (tmp_path / "web" / "node_modules").symlink_to(WEB / "node_modules", target_is_directory=True)
    (src / "mikrokopi.ts").write_text(mikrokopi, encoding="utf-8")
    for nama, isi in tsx.items():
        (src / nama.replace("__", ".")).write_text(isi, encoding="utf-8")
    return tmp_path


def _pesan(temuan: list) -> str:  # type: ignore[type-arg]
    return " | ".join(t.pesan for t in temuan)


# ── pohon repositori ───────────────────────────────────────────────────


@perlu_node
def test_web_repositori_bersih() -> None:
    assert periksa_bahasa_web(AKAR) == []


@perlu_node
def test_akar_relatif_diterima(monkeypatch: pytest.MonkeyPatch) -> None:
    """`make check` memanggil dengan `Path(".")`. Percobaan pertama M-8
    menemukan pengumpul berhenti pada akar relatif sementara seluruh uji lain
    lulus — karena seluruhnya memakai akar absolut."""
    monkeypatch.chdir(AKAR)
    assert periksa_bahasa_web(Path(".")) == []


@perlu_node
def test_untai_mikrokopi_nyata_memang_ditemukan() -> None:
    """Pengumpul yang tidak menemukan apa pun melaporkan bersih dengan sama
    meyakinkannya — maka yang ditemukan dihitung."""
    data = kumpulkan_teks_web(AKAR)
    teks = {b["teks"] for b in data["mikrokopi"]}
    assert "Tidak ditemukan dasar rujukan" in teks
    assert "Belum ada dokumen rujukan yang memuat jawaban ini." in teks
    assert len(data["mikrokopi"]) >= 20


@perlu_node
def test_k2_tidak_ditemukan_hanya_kalimat_pertama() -> None:
    """K-2, BT-71: kalimat kedua D-05 menjanjikan saran pertanyaan yang belum
    ada pada tanggapan."""
    teks = " ".join(b["teks"] for b in kumpulkan_teks_web(AKAR)["mikrokopi"])
    assert "Berikut pertanyaan lain" not in teks


# ── Aturan 1 · isi mikrokopi.ts ─────────────────────────────────────────


@perlu_node
def test_kalimat_lebih_dari_dua_puluh_kata_ditolak(tmp_path: Path) -> None:
    panjang = " ".join(["kata"] * 21) + "."
    temuan = periksa_bahasa_web(_pohon(tmp_path, f'export const A = "{panjang}";\n'))
    assert len(temuan) == 1
    assert "21 kata" in temuan[0].pesan
    assert temuan[0].berkas == Path("web/src/mikrokopi.ts")
    assert temuan[0].baris == 1


@perlu_node
def test_kalimat_tepat_dua_puluh_kata_diterima(tmp_path: Path) -> None:
    pas = " ".join(["kata"] * 20) + "."
    assert periksa_bahasa_web(_pohon(tmp_path, f'export const A = "{pas}";\n')) == []


@perlu_node
def test_tanda_seru_ditolak(tmp_path: Path) -> None:
    temuan = periksa_bahasa_web(_pohon(tmp_path, 'export const A = "Selesai semua!";\n'))
    assert "tanda seru" in _pesan(temuan)


@perlu_node
def test_kata_terlarang_ditolak(tmp_path: Path) -> None:
    temuan = periksa_bahasa_web(_pohon(tmp_path, 'export const A = "Pengiriman gagal.";\n'))
    assert "'gagal'" in _pesan(temuan)


@perlu_node
def test_kode_galat_ditolak(tmp_path: Path) -> None:
    temuan = periksa_bahasa_web(_pohon(tmp_path, 'export const A = "Galat 500 di peladen.";\n'))
    assert "kode galat" in _pesan(temuan)


@perlu_node
def test_nomor_baris_benar_sesudah_huruf_bukan_ascii(tmp_path: Path) -> None:
    """Pengurai dapat menghitung posisi dalam bait UTF-8, sedangkan JavaScript
    dalam satuan UTF-16. Selisihnya menggeser nomor baris sesudah `·`."""
    # Empat puluh `·` bernilai delapan puluh bait: bila posisi dihitung dalam
    # bait, untai baris ketiga akan terbaca di salah satu baris pengisi.
    isi = (
        f'export const A = "Satu {"·" * 40} dua.";\n\nexport const B = "Selesai!";\n'
        + 'export const C1 = "Isi pengisi.";\n' * 6
    )
    temuan = periksa_bahasa_web(_pohon(tmp_path, isi))
    assert len(temuan) == 1
    assert temuan[0].baris == 3


@perlu_node
def test_untai_bertemplat_ikut_diperiksa(tmp_path: Path) -> None:
    isi = "export const A = (n: number) => `Ada ${n} sumber terlambat.`;\n"
    temuan = periksa_bahasa_web(_pohon(tmp_path, isi))
    assert "'terlambat'" in _pesan(temuan)


@perlu_node
def test_sumber_impor_dan_tipe_bukan_teks(tmp_path: Path) -> None:
    isi = 'import type { X } from "./gagal-terlambat";\ntype T = "gagal total!";\n' + MIKROKOPI_SAH
    assert periksa_bahasa_web(_pohon(tmp_path, isi)) == []


@perlu_node
def test_mikrokopi_tanpa_untai_ditolak(tmp_path: Path) -> None:
    temuan = periksa_bahasa_web(_pohon(tmp_path, "export const A = 1;\n"))
    assert len(temuan) == 1
    assert "nol untai" in temuan[0].pesan


# ── Aturan 2 · teks harfiah pada .tsx ───────────────────────────────────


@perlu_node
def test_teks_jsx_harfiah_ditolak(tmp_path: Path) -> None:
    tsx = "export const L = () => (\n  <p>\n    Halo kepala sekolah\n  </p>\n);\n"
    temuan = periksa_bahasa_web(_pohon(tmp_path, Layar__tsx=tsx))
    assert len(temuan) == 1
    assert "teks JSX" in temuan[0].pesan
    assert "Halo kepala sekolah" in temuan[0].pesan
    assert temuan[0].berkas == Path("web/src/Layar.tsx")
    assert temuan[0].baris == 3


@perlu_node
def test_atribut_yang_dibaca_pengguna_ditolak(tmp_path: Path) -> None:
    tsx = 'export const L = () => <button aria-label="Kirim">{"x"}</button>;\n'
    temuan = periksa_bahasa_web(_pohon(tmp_path, Layar__tsx=tsx))
    pesan = _pesan(temuan)
    assert "atribut aria-label" in pesan
    assert "untai anak JSX" in pesan


@perlu_node
def test_atribut_bukan_teks_dan_perbandingan_tidak_ditolak(tmp_path: Path) -> None:
    """Bentuk sah yang pola teks akan salah tangkap: `a > b`, tipe generik,
    `className` berspasi, dan nilai enum satu kata."""
    tsx = (
        'import { MIKROKOPI } from "./mikrokopi";\n'
        "export const L = ({ a, b }: { a: number; b: number }) => {\n"
        "  const peta = new Map<string, number>();\n"
        '  const status = a > b ? "kuat" : "terbatas";\n'
        "  return (\n"
        '    <p className="blok utama" data-status={status} title={MIKROKOPI.judul}>\n'
        "      {a > b ? MIKROKOPI.isi : null} {peta.size}\n"
        "    </p>\n"
        "  );\n"
        "};\n"
    )
    assert periksa_bahasa_web(_pohon(tmp_path, Layar__tsx=tsx)) == []


@perlu_node
def test_untai_berkalimat_di_luar_jsx_ditolak(tmp_path: Path) -> None:
    """Pintu samping: kalimat ditaruh pada peubah, lalu peubahnya ditampilkan."""
    tsx = 'const judul = "Pertanyaan Anda";\nexport const L = () => <h1>{judul}</h1>;\n'
    temuan = periksa_bahasa_web(_pohon(tmp_path, Layar__tsx=tsx))
    assert len(temuan) == 1
    assert "untai berkalimat" in temuan[0].pesan
    assert temuan[0].baris == 1


@perlu_node
def test_berkas_uji_tsx_tidak_diperiksa(tmp_path: Path) -> None:
    tsx = "export const L = () => <p>Teks yang dicari uji</p>;\n"
    assert periksa_bahasa_web(_pohon(tmp_path, Layar__test__tsx=tsx)) == []


@perlu_node
def test_tsx_yang_tidak_dapat_diurai_dilaporkan(tmp_path: Path) -> None:
    temuan = periksa_bahasa_web(_pohon(tmp_path, Layar__tsx="export const L = () => <p>;\n"))
    assert len(temuan) == 1
    assert "tidak dapat diurai" in temuan[0].pesan


# ── keadaan lingkungan ──────────────────────────────────────────────────


def test_tanpa_node_gagal_dan_menyebut_cara_memperbaikinya(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "kosong"))
    web = tmp_path / "web"
    (web / "src").mkdir(parents=True)
    (web / "node_modules").mkdir()
    (web / "package.json").write_text("{}", encoding="utf-8")
    (web / "src" / "mikrokopi.ts").write_text(MIKROKOPI_SAH, encoding="utf-8")

    temuan = periksa_bahasa_web(tmp_path)

    assert len(temuan) == 1
    assert "node tidak ditemukan" in temuan[0].pesan
    assert "make setup" in temuan[0].pesan


def test_tanpa_node_modules_gagal(tmp_path: Path) -> None:
    web = tmp_path / "web"
    (web / "src").mkdir(parents=True)
    (web / "package.json").write_text("{}", encoding="utf-8")
    (web / "src" / "mikrokopi.ts").write_text(MIKROKOPI_SAH, encoding="utf-8")

    temuan = periksa_bahasa_web(tmp_path, node="node-yang-tidak-dipanggil")

    assert len(temuan) == 1
    assert "make setup" in temuan[0].pesan


def test_web_tanpa_mikrokopi_ditolak(tmp_path: Path) -> None:
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "package.json").write_text("{}", encoding="utf-8")

    temuan = periksa_bahasa_web(tmp_path)

    assert len(temuan) == 1
    assert "mikrokopi.ts tidak ada" in temuan[0].pesan


def test_pohon_tanpa_web_tidak_diperiksa(tmp_path: Path) -> None:
    assert periksa_bahasa_web(tmp_path) == []


@perlu_node
def test_c13_membawa_pemeriksaan_web(tmp_path: Path) -> None:
    """Sambungan ke pasal: temuan `web/` sampai pada `periksa_bahasa_antarmuka`,
    yang dipanggil V-02. Pemeriksa yang benar tetapi tidak tersambung tidak
    menjaga apa pun (TK-57)."""
    akar = _pohon(tmp_path, 'export const A = "Selesai semua!";\n')
    assert "tanda seru" in _pesan(periksa_bahasa_antarmuka(akar))
