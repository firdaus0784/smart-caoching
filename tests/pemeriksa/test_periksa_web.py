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

import shutil
from pathlib import Path

import pytest

from perkakas.pemeriksa.jalankan import periksa_web

AKAR = Path(__file__).resolve().parents[2]
WEB = AKAR / "web"

perlu_npm = pytest.mark.skipif(
    shutil.which("npm") is None or not (WEB / "node_modules").is_dir(),
    reason="Node, npm, atau web/node_modules tidak ada — jalankan `make setup`",
)


def _salin_web(tmp_path: Path) -> Path:
    """Pohon `web/` minimal yang lulus: konfigurasi repositori dan uji asapnya."""
    web = tmp_path / "web"
    (web / "src").mkdir(parents=True)
    for nama in ("package.json", "tsconfig.json", "vite.config.ts"):
        shutil.copy(WEB / nama, web / nama)
    shutil.copy(WEB / "src" / "asap.test.tsx", web / "src" / "asap.test.tsx")
    (web / "node_modules").symlink_to(WEB / "node_modules", target_is_directory=True)
    return tmp_path


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
