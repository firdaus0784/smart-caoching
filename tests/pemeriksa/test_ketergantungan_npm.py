"""Pemeriksa ketergantungan npm — T-1 fitur 027, R-19, C-12, KB-123.

Sejajar `periksa_ketergantungan` bagi Python: `ketergantungan-disetujui.toml`
adalah rekaman pohon paket pada saat disetujui manusia, dan `package-lock.json`
dibandingkan terhadapnya. Tiga penyimpangan diperiksa terpisah — paket masuk,
paket hilang, versi bergeser — karena akibatnya berbeda.

Satu perbedaan dari sisi Python: `package-lock.json` dapat memuat **satu paket
dalam dua versi** pada jalur bersarang. Kunci pembandingnya karena itu jalur di
dalam lock, bukan nama paket; dua versi yang dikunci dengan nama akan saling
menimpa, dan pergeseran salah satunya tidak akan terlihat.
"""

from __future__ import annotations

import json
from pathlib import Path

from perkakas.pemeriksa.ketergantungan_npm import periksa_ketergantungan_npm

DISETUJUI = """
[npm]
langsung = ["react", "vite"]

[npm.terkunci]
"react" = "19.3.0"
"vite" = "8.3.1"
"vite/node_modules/esbuild" = "0.30.0"
"esbuild" = "0.25.0"
"""


def _pohon(
    tmp_path: Path,
    *,
    disetujui: str = DISETUJUI,
    langsung: dict[str, dict[str, str]] | None = None,
    terkunci: dict[str, str] | None = None,
) -> Path:
    (tmp_path / "ketergantungan-disetujui.toml").write_text(disetujui, encoding="utf-8")
    web = tmp_path / "web"
    web.mkdir()
    langsung = (
        langsung
        if langsung is not None
        else {
            "dependencies": {"react": "19.3.0"},
            "devDependencies": {"vite": "8.3.1"},
        }
    )
    (web / "package.json").write_text(json.dumps({"name": "web", **langsung}), encoding="utf-8")
    terkunci = (
        terkunci
        if terkunci is not None
        else {
            "react": "19.3.0",
            "vite": "8.3.1",
            "vite/node_modules/esbuild": "0.30.0",
            "esbuild": "0.25.0",
        }
    )
    paket: dict[str, dict[str, str]] = {"": {"name": "web"}}
    for jalur, versi in terkunci.items():
        # "vite/node_modules/esbuild" → "node_modules/vite/node_modules/esbuild"
        paket[f"node_modules/{jalur}"] = {"version": versi}
    (web / "package-lock.json").write_text(
        json.dumps({"lockfileVersion": 3, "packages": paket}), encoding="utf-8"
    )
    return tmp_path


def test_pohon_sama_bersih(tmp_path: Path) -> None:
    assert periksa_ketergantungan_npm(_pohon(tmp_path)) == []


def test_paket_langsung_di_luar_persetujuan_ditolak(tmp_path: Path) -> None:
    """Paket yang ditulis langsung pada package.json tanpa ada pada
    `[npm].langsung` — bentuk yang paling mungkin terjadi: seseorang menambah
    satu pustaka agar cepat."""
    akar = _pohon(
        tmp_path,
        langsung={
            "dependencies": {"react": "19.3.0", "lodash": "4.17.21"},
            "devDependencies": {"vite": "8.3.1"},
        },
    )
    temuan = periksa_ketergantungan_npm(akar)
    assert any("lodash" in t.pesan and "langsung" in t.pesan for t in temuan), temuan


def test_paket_masuk_pada_lock_ditolak(tmp_path: Path) -> None:
    akar = _pohon(
        tmp_path,
        terkunci={
            "react": "19.3.0",
            "vite": "8.3.1",
            "vite/node_modules/esbuild": "0.30.0",
            "esbuild": "0.25.0",
            "left-pad": "1.3.0",
        },
    )
    temuan = periksa_ketergantungan_npm(akar)
    assert any("left-pad" in t.pesan and "tanpa persetujuan" in t.pesan for t in temuan), temuan


def test_paket_hilang_dari_lock_ditolak(tmp_path: Path) -> None:
    akar = _pohon(tmp_path, terkunci={"react": "19.3.0", "vite": "8.3.1", "esbuild": "0.25.0"})
    temuan = periksa_ketergantungan_npm(akar)
    assert any("vite/node_modules/esbuild" in t.pesan and "hilang" in t.pesan for t in temuan), (
        temuan
    )


def test_versi_bersarang_bergeser_ditolak(tmp_path: Path) -> None:
    """**Alasan kunci berupa jalur.** Hanya salinan bersarang yang bergeser;
    salinan di puncak tetap. Dengan kunci nama, satu dari keduanya menimpa yang
    lain dan pergeserannya tidak terlihat."""
    akar = _pohon(
        tmp_path,
        terkunci={
            "react": "19.3.0",
            "vite": "8.3.1",
            "vite/node_modules/esbuild": "0.31.0",
            "esbuild": "0.25.0",
        },
    )
    temuan = periksa_ketergantungan_npm(akar)
    assert any("vite/node_modules/esbuild" in t.pesan and "bergeser" in t.pesan for t in temuan), (
        temuan
    )


def test_langsung_tanpa_terkunci_ditolak(tmp_path: Path) -> None:
    akar = _pohon(
        tmp_path,
        disetujui=DISETUJUI.replace(
            'langsung = ["react", "vite"]', 'langsung = ["react", "vite", "jsdom"]'
        ),
    )
    temuan = periksa_ketergantungan_npm(akar)
    assert any("jsdom" in t.pesan and "terkunci" in t.pesan for t in temuan), temuan


def test_langsung_kosong_sementara_terkunci_berisi_ditolak(tmp_path: Path) -> None:
    """Mengosongkan daftar langsung adalah cara termudah meloloskan pemeriksaan
    paket langsung — sama dengan penjagaan di sisi Python."""
    akar = _pohon(
        tmp_path, disetujui=DISETUJUI.replace('langsung = ["react", "vite"]', "langsung = []")
    )
    temuan = periksa_ketergantungan_npm(akar)
    assert any("kosong" in t.pesan for t in temuan), temuan


def test_tanpa_web_melapor_bukan_lulus(tmp_path: Path) -> None:
    """Tanpa `web/package.json` sama sekali, pemeriksa **melapor**. Pemeriksa
    yang tidak menemukan bahannya lalu diam adalah laporan palsu (TA-01)."""
    (tmp_path / "ketergantungan-disetujui.toml").write_text(DISETUJUI, encoding="utf-8")
    temuan = periksa_ketergantungan_npm(tmp_path)
    assert temuan and "package.json" in temuan[0].pesan


def test_tanpa_lock_melapor(tmp_path: Path) -> None:
    akar = _pohon(tmp_path)
    (akar / "web" / "package-lock.json").unlink()
    temuan = periksa_ketergantungan_npm(akar)
    assert temuan and "package-lock.json" in temuan[0].pesan


def test_tanpa_bagian_npm_pada_persetujuan_melapor(tmp_path: Path) -> None:
    akar = _pohon(tmp_path, disetujui='langsung = ["pydantic"]\n')
    temuan = periksa_ketergantungan_npm(akar)
    assert temuan and "[npm]" in temuan[0].pesan


def test_repositori_nyata_bersih() -> None:
    """Sapuan atas repositori sungguhan — merah bila paket npm dipasang tanpa
    persetujuannya tercatat."""
    akar = Path(__file__).resolve().parents[2]
    temuan = periksa_ketergantungan_npm(akar)
    assert temuan == [], "; ".join(str(t) for t in temuan)
