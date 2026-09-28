"""V-01 membaca `web/` — T-2 fitur 027, R-19.

Tanpa pemeriksa ini keenam gerbang melaporkan lulus tanpa pernah melihat
frontend: bentuk TA-01. Yang diuji perilaku gerbangnya, bukan cara ia
memanggil npm — dan tiap uji kegagalan memeriksa **sebab** yang dilaporkan,
bukan hanya bahwa ada temuan (KB-098): gerbang yang merah karena sebab lain
akan lolos uji yang hanya menghitung temuan.

Uji yang menjalankan npm sungguhan memakai pohon `web/` salinan di direktori
sementara, dengan `node_modules` ditautkan ke milik repositori. Pohon
repositori sendiri tidak disentuh.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from perkakas.pemeriksa.jalankan import periksa_anggaran_muat, periksa_web

AKAR = Path(__file__).resolve().parents[2]
WEB = AKAR / "web"

perlu_npm = pytest.mark.skipif(
    shutil.which("npm") is None or not (WEB / "node_modules").is_dir(),
    reason="Node, npm, atau web/node_modules tidak ada — jalankan `make setup`",
)


def _salin_web(tmp_path: Path) -> Path:
    """Salinan `web/` repositori — sumber, uji, dan konfigurasinya.

    Sejak T-6 V-01 juga menjalankan `vite build`, yang menuntut `index.html`
    dan seluruh `src/`; salinan minimal yang dipakai sebelumnya tidak lagi
    dapat dibangun.
    """
    web = tmp_path / "web"
    web.mkdir()
    for nama in ("package.json", "tsconfig.json", "vite.config.ts", "index.html"):
        shutil.copy(WEB / nama, web / nama)
    shutil.copytree(WEB / "src", web / "src")
    shutil.copytree(WEB / "public", web / "public")
    (web / "node_modules").symlink_to(WEB / "node_modules", target_is_directory=True)
    return tmp_path


def _dist(tmp_path: Path, ukuran: dict[str, int]) -> Path:
    """Hasil build buatan berisi bait acak — tidak termampatkan, sehingga
    ukuran terkompresinya dapat diramalkan."""
    dist = tmp_path / "dist"
    for nama, jumlah in ukuran.items():
        berkas = dist / nama
        berkas.parent.mkdir(parents=True, exist_ok=True)
        berkas.write_bytes(os.urandom(jumlah))
    return dist


# ── anggaran muat — T-6, R-14 ──────────────────────────────────────────


def test_anggaran_muat_di_bawah_batas_lulus(tmp_path: Path) -> None:
    dist = _dist(tmp_path, {"index.html": 500, "assets/index.js": 40_000})
    assert periksa_anggaran_muat(dist, batas=60_000) == []


def test_anggaran_muat_terlampaui_ditolak_dengan_ukurannya(tmp_path: Path) -> None:
    dist = _dist(tmp_path, {"index.html": 500, "assets/index.js": 40_000, "assets/a.css": 30_000})

    temuan = periksa_anggaran_muat(dist, batas=60_000)

    assert len(temuan) == 1
    assert "melampaui" in temuan[0].pesan
    assert "60000" in temuan[0].pesan.replace(".", "").replace(" ", "")


def test_anggaran_muat_menghitung_seluruh_berkas_bukan_satu(tmp_path: Path) -> None:
    # Dua berkas yang masing-masing di bawah batas, bersama di atasnya.
    dist = _dist(tmp_path, {"index.html": 100, "assets/a.js": 35_000, "assets/b.js": 35_000})
    assert len(periksa_anggaran_muat(dist, batas=60_000)) == 1


def test_anggaran_muat_tanpa_hasil_build_ditolak(tmp_path: Path) -> None:
    temuan = periksa_anggaran_muat(tmp_path / "dist", batas=60_000)
    assert len(temuan) == 1
    assert "index.html" in temuan[0].pesan


@perlu_npm
def test_build_yang_gagal_menjatuhkan_v01(tmp_path: Path) -> None:
    # `main.tsx` tidak diimpor uji mana pun, dan impor CSS lolos `tsc` lewat
    # deklarasi `vite/client` — sehingga tipe dan uji lulus, dan yang
    # menjatuhkan hanya build. Percobaan pertama merusak `index.html`, dan
    # uji halaman yang lebih dulu merah: sebab yang salah.
    akar = _salin_web(tmp_path)
    main = akar / "web" / "src" / "main.tsx"
    main.write_text(main.read_text(encoding="utf-8") + 'import "./tidak-ada.css";\n', "utf-8")

    temuan = periksa_web(akar)

    assert len(temuan) == 1
    assert temuan[0].pesan.startswith("build web/ gagal")
    assert "tidak-ada.css" in temuan[0].pesan


def test_tanpa_npm_v01_gagal_dan_menyebut_cara_memperbaikinya(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # PATH kosong: keadaan mesin tanpa Node. Gagal, bukan dilewati — sejajar
    # keputusan 12 September atas PostgreSQL.
    monkeypatch.setenv("PATH", str(tmp_path))
    (tmp_path / "web" / "node_modules").mkdir(parents=True)

    temuan = periksa_web(tmp_path)

    assert len(temuan) == 1
    assert "npm tidak ditemukan" in temuan[0].pesan
    assert "make setup" in temuan[0].pesan


def test_tanpa_node_modules_v01_gagal_dan_menyebut_make_setup(tmp_path: Path) -> None:
    (tmp_path / "web").mkdir()

    temuan = periksa_web(tmp_path, npm="npm-yang-tidak-akan-dipanggil")

    assert len(temuan) == 1
    assert "node_modules" in temuan[0].pesan
    assert "make setup" in temuan[0].pesan


@perlu_npm
def test_web_yang_benar_lulus(tmp_path: Path) -> None:
    # Pasangan uji kegagalan di bawah: gerbang yang selalu merah juga lulus
    # uji-uji itu.
    assert periksa_web(_salin_web(tmp_path)) == []


@perlu_npm
def test_galat_tipe_di_web_menjatuhkan_v01(tmp_path: Path) -> None:
    akar = _salin_web(tmp_path)
    (akar / "web" / "src" / "salah.ts").write_text(
        'export const jumlah: number = "tiga";\n', encoding="utf-8"
    )

    temuan = periksa_web(akar)

    assert len(temuan) == 1
    assert "error TS2322" in temuan[0].pesan
    assert "salah.ts" in temuan[0].pesan


@perlu_npm
def test_uji_web_yang_gagal_menjatuhkan_v01(tmp_path: Path) -> None:
    akar = _salin_web(tmp_path)
    (akar / "web" / "src" / "gagal.test.ts").write_text(
        'import { expect, test } from "vitest";\n'
        'test("sengaja gagal", () => { expect(1).toBe(2); });\n',
        encoding="utf-8",
    )

    temuan = periksa_web(akar)

    assert len(temuan) == 1
    # Tipe lulus; yang menjatuhkan adalah ujinya, dan laporan mengatakannya.
    assert "error TS" not in temuan[0].pesan
    assert "1 failed" in temuan[0].pesan
