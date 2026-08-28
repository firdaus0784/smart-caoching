"""Pemeriksa ruang lingkup 2026 — C-14, `docs/D01.md` Bagian 4.2.

C-14 berbunyi: fitur pada `docs/D01.md` Bagian 4.2 tidak dibangun pada siklus
2026, **dalam bentuk apa pun, termasuk kerangka kosong**. Bagian itu memuat
enam baris, dan pemeriksa ini menjaga lima di antaranya.

## Baris pertama sengaja tidak diduakan

Baris gamifikasi sudah dijaga `periksa_nama_terlarang` (C-15) sejak fitur 001.
Menambahkan sapuan kedua atas kata yang sama akan menghasilkan dua daftar yang
berselisih pada hari salah satunya disunting — dan yang disunting bukan yang
diperiksa. Bentuk kekeliruan yang sama dengan `PAGU_TAYANG_PER_PENGGUNA` yang
sempat hendak ditulis ulang pada fitur 011.

## Mengapa baru dibangun sesudah fitur 012

C-14 terdaftar `fitur_pengunci="010 s.d. 013; sebagian dapat diperiksa lebih
awal"` sejak fitur 001. Sebelum fitur 010, 011, dan 012 ada, ketiadaan
personalisasi dan analitik prediktif **tidak bermakna** — ia dapat berarti
"belum dibangun" alih-alih "sengaja tidak dibangun". Sesudah ketiganya lolos
Gerbang 4, ketiadaan itu menjadi pernyataan yang dapat ditagih.

Fitur 013 belum ada, dan itu justru alasan pemeriksa ini dibangun sekarang
alih-alih sesudahnya: ia menunggu `web/` dengan aturan yang sudah berdiri,
bentuk yang sama dengan C-17 dan C-18 yang dibangun fitur 001 sebelum ada
pemanggil yang perlu dijaganya.

## Tiga aturan, dan mengapa yang ketiga berbeda bentuk

**Aturan 1 — sapuan nama pengenal.** Sama dengan C-15: hanya nama pengenal,
bukan komentar dan untai. Menjelaskan mengapa personalisasi dilarang bukan
membangun personalisasi, dan `src/pengguna/feed.py` memang menjelaskannya
empat kali. Hanya `src/` dan `web/` yang diperiksa; `perkakas/` memuat daftar
ini sendiri dan `tests/` memuat pelanggaran buatan yang memang harus ada.

**Aturan 2 — tanda tangan fungsi penyusun feed.** Larangan personalisasi
berbasis riwayat **tidak dapat** ditegakkan lewat sapuan nama: "riwayat"
dipakai sah pada `src/llm/pembungkus.py` (riwayat pemanggilan bagi pencatatan
biaya C-08) dan `src/nlp/pelatihan/lemari_uji.py` (riwayat pembukaan himpunan
uji). Sapuan atasnya akan menyalak pada keduanya, dan pemeriksa yang menyalak
keliru adalah pemeriksa yang dimatikan orang.

Yang diperiksa karena itu **bentuknya**: fungsi penyusun feed tidak boleh
menerima riwayat maupun umpan balik sebagai parameter. Fitur 011 sudah
membangun `susun_feed` demikian dan mengujinya lewat tanda tangan; aturan ini
menjadikannya berlaku bagi setiap penyusun feed berikutnya, bukan bagi satu
fungsi yang namanya ditulis pada uji.

**Aturan 3 — berkas proyek mobile native.** Bukan pertanyaan tentang bentuk
kode Python, melainkan tentang keberadaan berkas. PWA adalah bentuk yang D-01
setujui; yang dilarang aplikasi native. Keduanya dibedakan oleh berkas proyek
yang menyertainya, bukan oleh nama pengenal di dalamnya.

Batas yang diakui terbuka: pemeriksa membaca bentuk kode dan nama berkas,
sehingga fitur terlarang yang dibangun dengan penamaan yang menyamar akan
melewatinya. Sejalan PT-01 `docs/D13.md`, yang dirancang pembatasan kerugian,
bukan pencegahan sempurna. Gerbang 1 pada setiap fitur tetap tempat penolakan
yang sesungguhnya.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

TERLARANG_LINGKUP: tuple[str, ...] = (
    # Baris 3 — personalisasi berbasis profil dan riwayat, sentiment
    # analysis, recommendation system. Siklus 2027.
    "personalisasi",
    "personalization",
    "sentimen",
    "sentiment",
    "rekomendasi",
    "recommender",
    "recommendation",
    # Baris 4 — peer mentoring dan pembelajaran kolaboratif. Siklus 2028.
    "mentoring",
    "kolaboratif",
    "collaborative",
    # Baris 5 — integrasi langsung SIMPATIKA/Dapodik tingkat sistem. 2028.
    "dapodik",
    "simpatika",
    # Baris 6 — analitik prediktif, voice assistant, explainable AI. 2029.
    "prediktif",
    "predictive",
    "forecasting",
    "voiceassistant",
    "asistensuara",
    "explainableai",
)
"""Dicocokkan terhadap nama pengenal yang sudah dinormalkan.

Setiap kata sekurangnya tujuh aksara dan khas, sehingga tidak dapat menjadi
potongan istilah yang kamus data D-14 wajibkan — alasan yang sama dengan
C-15 memakai "papanperingkat" alih-alih "peringkat". Uji menuntut panjangnya.
"""

PARAMETER_RIWAYAT: tuple[str, ...] = (
    "riwayat",
    "history",
    "perilaku",
    "umpanbalik",
    "feedback",
    "interaksi",
)
"""Parameter yang tidak boleh diterima fungsi penyusun feed — FR-G01, C-14."""

BERKAS_MOBILE_NATIVE: tuple[str, ...] = (
    "build.gradle",
    "build.gradle.kts",
    "AndroidManifest.xml",
    "Podfile",
    "pubspec.yaml",
)
"""Berkas proyek yang menandai aplikasi native — baris 2 D-01 Bagian 4.2."""

PAKET_MOBILE_NATIVE: tuple[str, ...] = ("react-native", "expo", "capacitor", "cordova")
"""Ketergantungan yang menandai pembungkus native pada `package.json`."""

POLA_PEMISAH = re.compile(r"[_\-]|(?<=[a-z0-9])(?=[A-Z])")

DIPERIKSA = ("src", "web")


def _normal(pengenal: str) -> str:
    return pengenal.lower().replace("_", "").replace("-", "")


def _melanggar(pengenal: str) -> str | None:
    normal = _normal(pengenal)
    for kata in TERLARANG_LINGKUP:
        if kata in normal:
            return kata
    return None


def _pengenal_pada(pohon: ast.AST) -> list[tuple[str, int]]:
    """Nama kelas, fungsi, argumen, dan peubah — bukan komentar dan untai."""
    hasil: list[tuple[str, int]] = []
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            hasil.append((simpul.name, simpul.lineno))
        elif isinstance(simpul, ast.Name) and isinstance(simpul.ctx, ast.Store):
            hasil.append((simpul.id, simpul.lineno))
        elif isinstance(simpul, ast.arg):
            hasil.append((simpul.arg, simpul.lineno))
        elif isinstance(simpul, ast.Attribute) and isinstance(simpul.ctx, ast.Store):
            hasil.append((simpul.attr, simpul.lineno))
    return hasil


def _parameter_terlarang(pohon: ast.AST) -> list[tuple[str, str, int]]:
    """Parameter riwayat pada fungsi yang namanya memuat "feed"."""
    hasil: list[tuple[str, str, int]] = []
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if "feed" not in _normal(simpul.name):
            continue
        arg = simpul.args
        semua = [*arg.posonlyargs, *arg.args, *arg.kwonlyargs]
        if arg.vararg:
            semua.append(arg.vararg)
        if arg.kwarg:
            semua.append(arg.kwarg)
        for satu in semua:
            normal = _normal(satu.arg)
            for kata in PARAMETER_RIWAYAT:
                if kata in normal:
                    hasil.append((simpul.name, satu.arg, satu.lineno))
                    break
    return hasil


def _periksa_python(akar: Path) -> list[Temuan]:
    temuan: list[Temuan] = []
    for direktori in DIPERIKSA:
        cabang = akar / direktori
        if not cabang.is_dir():
            continue
        for berkas in berkas_python(cabang):
            kata = _melanggar(berkas.stem)
            if kata:
                temuan.append(
                    Temuan(
                        berkas,
                        0,
                        f"nama berkas memuat {kata!r} — C-14 melarang fitur "
                        "D-01 Bagian 4.2 dibangun pada siklus 2026, termasuk "
                        "dalam bentuk kerangka kosong",
                    )
                )
            pohon = ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))
            for pengenal, baris in _pengenal_pada(pohon):
                kata = _melanggar(pengenal)
                if kata:
                    temuan.append(
                        Temuan(
                            berkas,
                            baris,
                            f"pengenal {pengenal!r} memuat {kata!r} — C-14, "
                            "lihat docs/D01.md Bagian 4.2",
                        )
                    )
            for fungsi, parameter, baris in _parameter_terlarang(pohon):
                temuan.append(
                    Temuan(
                        berkas,
                        baris,
                        f"penyusun feed {fungsi!r} menerima parameter "
                        f"{parameter!r} — penyaringan yang menyesuaikan diri "
                        "terhadap riwayat adalah personalisasi, C-14",
                    )
                )
    return temuan


def _periksa_mobile_native(akar: Path) -> list[Temuan]:
    """Berkas proyek native, di mana pun ia diletakkan.

    Tidak dibatasi `src/` dan `web/`: proyek native yang disisipkan biasanya
    duduk pada direktorinya sendiri, dan justru itu yang dicari.
    """
    temuan: list[Temuan] = []
    for nama in BERKAS_MOBILE_NATIVE:
        for berkas in akar.rglob(nama):
            if any(bagian.startswith(".") or bagian == "node_modules" for bagian in berkas.parts):
                continue
            temuan.append(
                Temuan(
                    berkas,
                    0,
                    f"berkas proyek {nama!r} menandai aplikasi mobile native "
                    "— C-14 menempatkannya pada siklus 2028; PWA adalah "
                    "bentuk yang D-01 setujui",
                )
            )
    for berkas in akar.rglob("*.xcodeproj"):
        temuan.append(Temuan(berkas, 0, "proyek Xcode menandai aplikasi mobile native — C-14"))
    for berkas in akar.rglob("package.json"):
        if any(bagian == "node_modules" or bagian.startswith(".") for bagian in berkas.parts):
            continue
        try:
            isi = json.loads(berkas.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        bergantung: set[str] = set()
        for kunci in ("dependencies", "devDependencies"):
            nilai = isi.get(kunci)
            if isinstance(nilai, dict):
                bergantung |= set(nilai)
        for paket in PAKET_MOBILE_NATIVE:
            if any(paket in satu for satu in bergantung):
                temuan.append(
                    Temuan(
                        berkas,
                        0,
                        f"ketergantungan {paket!r} menandai pembungkus mobile "
                        "native — C-14 menempatkannya pada siklus 2028",
                    )
                )
    return temuan


def periksa_ruang_lingkup(akar: Path) -> list[Temuan]:
    """Lima dari enam baris D-01 Bagian 4.2; baris gamifikasi dijaga C-15."""
    return [*_periksa_python(akar), *_periksa_mobile_native(akar)]
