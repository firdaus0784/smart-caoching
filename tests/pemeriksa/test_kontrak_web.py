"""Penjaga keselarasan kontrak web — T-3 fitur 027, R-19, C-20.

TypeScript tidak dapat mengimpor model pydantic, sehingga bentuk tanggapan
`/api/v1/tanya` ditulis dua kali. Dua daftar yang menggambarkan hal yang sama
akan hanyut; pemeriksa ini membuat hanyutnya menjatuhkan V-03 alih-alih
muncul sebagai layar kosong di lapangan.

Tiap uji kegagalan memeriksa **bidang yang disebut**, bukan hanya bahwa ada
temuan (KB-098): pemeriksa yang menyalak karena sebab lain lulus uji yang
hanya menghitung.
"""

from __future__ import annotations

from pathlib import Path

from perkakas.pemeriksa.kontrak_web import periksa_kontrak_web

AKAR = Path(__file__).resolve().parents[2]
KONTRAK_NYATA = AKAR / "web" / "src" / "kontrak.ts"


def _akar(tmp_path: Path, isi: str) -> Path:
    src = tmp_path / "web" / "src"
    src.mkdir(parents=True)
    (tmp_path / "web" / "package.json").write_text("{}", encoding="utf-8")
    (src / "kontrak.ts").write_text(isi, encoding="utf-8")
    return tmp_path


def _nyata() -> str:
    return KONTRAK_NYATA.read_text(encoding="utf-8")


def test_kontrak_repositori_selaras() -> None:
    # Pasangan uji kegagalan di bawah: pemeriksa yang selalu menyalak juga
    # lulus uji-uji itu.
    assert periksa_kontrak_web(AKAR) == []


def test_bidang_hilang_ditolak(tmp_path: Path) -> None:
    isi = _nyata().replace("  readonly penafian: string;\n", "", 1)
    assert isi != _nyata()

    temuan = periksa_kontrak_web(_akar(tmp_path, isi))

    assert len(temuan) == 1
    assert "Tanggapan" in temuan[0].pesan
    assert "penafian" in temuan[0].pesan
    assert "hilang" in temuan[0].pesan


def test_bidang_lebih_ditolak(tmp_path: Path) -> None:
    # Bentuk yang dilarang C-20: `skor_keyakinan` tampak tidak berbahaya dan
    # memindahkan penilaian dari sistem ke klien.
    isi = _nyata().replace(
        "  readonly penafian: string;\n",
        "  readonly penafian: string;\n  readonly skor_keyakinan: number;\n",
        1,
    )

    temuan = periksa_kontrak_web(_akar(tmp_path, isi))

    assert len(temuan) == 1
    assert "skor_keyakinan" in temuan[0].pesan
    assert "tidak ada pada model" in temuan[0].pesan


def test_bidang_berganti_nama_ditolak_kedua_arah(tmp_path: Path) -> None:
    isi = _nyata().replace("  readonly bagian: string;", "  readonly pasal: string;", 1)
    assert isi != _nyata()

    temuan = periksa_kontrak_web(_akar(tmp_path, isi))
    pesan = " | ".join(t.pesan for t in temuan)

    assert len(temuan) == 2
    assert "Sitasi" in pesan
    assert "'bagian'" in pesan
    assert "'pasal'" in pesan


def test_nilai_enum_bergeser_ditolak(tmp_path: Path) -> None:
    # AG-04: daftar nilai enum tidak diubah. Nilai yang hanya ada di layar
    # tidak pernah datang dari peladen, dan nilai yang hilang di layar datang
    # tanpa tampilan.
    isi = _nyata().replace('"terbatas"', '"lemah"', 1)
    assert isi != _nyata()

    temuan = periksa_kontrak_web(_akar(tmp_path, isi))
    pesan = " | ".join(t.pesan for t in temuan)

    assert "StatusDasar" in pesan
    assert "'terbatas'" in pesan
    assert "'lemah'" in pesan


def test_antarmuka_hilang_ditolak(tmp_path: Path) -> None:
    awal = _nyata().index("export interface Versi")
    akhir = _nyata().index("}", awal) + 1
    isi = _nyata()[:awal] + _nyata()[akhir:]

    temuan = periksa_kontrak_web(_akar(tmp_path, isi))

    assert len(temuan) == 1
    assert "Versi" in temuan[0].pesan
    assert "tidak ditemukan" in temuan[0].pesan


def test_kontrak_hilang_dari_web_yang_ada_ditolak(tmp_path: Path) -> None:
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "package.json").write_text("{}", encoding="utf-8")

    temuan = periksa_kontrak_web(tmp_path)

    assert len(temuan) == 1
    assert "kontrak.ts" in temuan[0].pesan


def test_pohon_tanpa_web_tidak_diperiksa(tmp_path: Path) -> None:
    # Akar tiruan uji V-03 yang lain tidak memuat `web/`. Pohon repositori
    # sendiri selalu memuatnya, dan uji pertama di atas menjaga sisi itu.
    assert periksa_kontrak_web(tmp_path) == []
