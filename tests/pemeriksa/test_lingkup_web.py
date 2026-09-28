"""C-14 dan C-15 atas TypeScript `web/` — fitur 027, R-20.

Sampai fitur 027 kedua pemeriksa menyapu `web/` tetapi hanya **berkas
Python** di dalamnya, sehingga seluruh sumber TypeScript lolos tanpa dibaca:
laporan bersih yang tidak memeriksa apa pun (TA-01). Ditemukan sesudah T-6,
saat memastikan klaim R-20 benar-benar dijaga mesin.

Yang dibaca sekarang, sejajar sisi Python: nama pengenal **pengikat** — nama
deklarasi, parameter, kunci objek, bidang antarmuka — bukan komentar dan
untai. Ditambah nama berkas `web/src` dan `web/public`, dan nama kelas atau
id pada CSS: papan peringkat yang hanya berupa gaya tetap papan peringkat.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from perkakas.pemeriksa.nama_terlarang import periksa_nama_terlarang
from perkakas.pemeriksa.ruang_lingkup import periksa_ruang_lingkup

AKAR = Path(__file__).resolve().parents[2]
WEB = AKAR / "web"

perlu_node = pytest.mark.skipif(
    shutil.which("node") is None or not (WEB / "node_modules").is_dir(),
    reason="Node atau web/node_modules tidak ada — jalankan `make setup`",
)


def _pohon(tmp_path: Path, **berkas: str) -> Path:
    web = tmp_path / "web"
    (web / "src").mkdir(parents=True)
    shutil.copy(WEB / "package.json", web / "package.json")
    (web / "node_modules").symlink_to(WEB / "node_modules", target_is_directory=True)
    (web / "src" / "mikrokopi.ts").write_text('export const A = "Tanya";\n', encoding="utf-8")
    for nama, isi in berkas.items():
        jalur = web / nama.replace("__", "/").replace("_DOT_", ".")
        jalur.parent.mkdir(parents=True, exist_ok=True)
        jalur.write_text(isi, encoding="utf-8")
    return tmp_path


def _pesan(temuan: list) -> str:  # type: ignore[type-arg]
    return " | ".join(f"{t.berkas}:{t.baris} {t.pesan}" for t in temuan)


# ── pohon repositori ───────────────────────────────────────────────────


@perlu_node
def test_web_repositori_bersih_c14_dan_c15() -> None:
    assert periksa_nama_terlarang(AKAR) == []
    assert periksa_ruang_lingkup(AKAR) == []


# ── C-15 ────────────────────────────────────────────────────────────────


@perlu_node
@pytest.mark.parametrize(
    ("isi", "kata", "baris"),
    [
        ("export function hitungPoin(): number {\n  return 1;\n}\n", "poin", 1),
        ("\nexport const LencanaPengguna = () => null;\n", "lencana", 2),
        ("export interface Profil {\n  readonly streak: number;\n}\n", "streak", 2),
        ("export const tata = { leaderboard: [] as string[] };\n", "leaderboard", 1),
        (
            "export function f(achievementBaru: string) {\n  return achievementBaru;\n}\n",
            "achievement",
            1,
        ),
        ("export type DaftarTeman = readonly string[];\n", "teman", 1),
        ("export const { badgeUtama } = { badgeUtama: 1 };\n", "badge", 1),
    ],
)
def test_c15_membaca_pengenal_typescript(tmp_path: Path, isi: str, kata: str, baris: int) -> None:
    temuan = periksa_nama_terlarang(_pohon(tmp_path, src__Layar_DOT_tsx=isi))
    pesan = _pesan(temuan)
    assert f"{kata!r}" in pesan
    assert f"web/src/Layar.tsx:{baris} " in pesan


@perlu_node
def test_c15_komentar_dan_untai_tidak_dibaca(tmp_path: Path) -> None:
    isi = '// tanpa poin dan lencana (C-15)\nexport const x = "papan peringkat poin";\n'
    assert periksa_nama_terlarang(_pohon(tmp_path, src__Layar_DOT_tsx=isi)) == []


@perlu_node
def test_c15_nama_berkas_web(tmp_path: Path) -> None:
    temuan = periksa_nama_terlarang(_pohon(tmp_path, src__PapanPeringkat_DOT_tsx="export {};\n"))
    assert "'papanperingkat'" in _pesan(temuan)


@perlu_node
def test_c15_kelas_css(tmp_path: Path) -> None:
    css = ".kartu {\n  color: red;\n}\n\n.lencana-emas {\n  color: gold;\n}\n"
    temuan = periksa_nama_terlarang(_pohon(tmp_path, src__gaya_DOT_css=css))
    pesan = _pesan(temuan)
    assert "'lencana'" in pesan
    assert "web/src/gaya.css:5 " in pesan


# ── C-14 ────────────────────────────────────────────────────────────────


@perlu_node
@pytest.mark.parametrize(
    ("isi", "kata"),
    [
        ("export function rekomendasiButir() {\n  return [];\n}\n", "rekomendasi"),
        ("export const personalisasiFeed = true;\n", "personalisasi"),
        ("export interface X {\n  readonly skorPrediktif: number;\n}\n", "prediktif"),
    ],
)
def test_c14_membaca_pengenal_typescript(tmp_path: Path, isi: str, kata: str) -> None:
    temuan = periksa_ruang_lingkup(_pohon(tmp_path, src__Layar_DOT_ts=isi))
    assert f"{kata!r}" in _pesan(temuan)


@perlu_node
def test_c14_nama_berkas_web(tmp_path: Path) -> None:
    temuan = periksa_ruang_lingkup(_pohon(tmp_path, src__Rekomendasi_DOT_tsx="export {};\n"))
    assert "'rekomendasi'" in _pesan(temuan)


# ── lingkungan ──────────────────────────────────────────────────────────


def test_tanpa_node_keduanya_gagal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Gagal, bukan lulus diam-diam — sejajar V-01 dan C-13."""
    monkeypatch.setenv("PATH", str(tmp_path / "kosong"))
    web = tmp_path / "web"
    (web / "src").mkdir(parents=True)
    (web / "node_modules").mkdir()
    (web / "package.json").write_text("{}", encoding="utf-8")

    for periksa in (periksa_nama_terlarang, periksa_ruang_lingkup):
        temuan = periksa(tmp_path)
        assert len(temuan) == 1, periksa.__name__
        assert "node tidak ditemukan" in temuan[0].pesan


def test_pohon_tanpa_web_tidak_membutuhkan_node(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path / "kosong"))
    (tmp_path / "src").mkdir()
    assert periksa_nama_terlarang(tmp_path) == []
    assert periksa_ruang_lingkup(tmp_path) == []
