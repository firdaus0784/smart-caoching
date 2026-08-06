"""Pemeriksa pemisahan area penyimpanan — C-03, R-01, R-01a, ADR-06.

C-03 berbunyi dua kalimat, dan kalimat keduanya yang paling sering dilanggar:
"Kredensial berbeda, **bukan penanda status**." Sistem yang memisahkan area
dengan satu kredensial yang berubah wujud menurut sebuah syarat sudah gagal,
meski setiap pemanggilannya kebetulan benar hari ini.

Empat aturan, dan keempatnya menutup jalan yang berbeda:

1. **Kredensial jalur penjawaban tidak membaca karantina.** `PENJAWABAN` dan
   `PEMANGGIL_LLM` — yang pertama menjawab pertanyaan pengguna, yang kedua
   menyusun konteks yang dikirim ke model. C-02 bersandar pada yang kedua: yang
   tidak dapat dibaca tidak dapat masuk konteks.
2. **Himpunan bacanya berbentuk tetapan, bukan hitungan.** Himpunan yang
   dihitung dari syarat adalah penanda status yang menyamar sebagai kredensial.
3. **Jalur penjawaban tidak membangun kredensialnya sendiri.** Tanpa aturan
   ini, aturan 1 dan 2 dapat dilewati tanpa menyentuh `kredensial_baku.py`
   sama sekali.
4. **Jalur penjawaban tidak menyebut karantina.** Sengaja lebih luas daripada
   pelanggarannya: penyebutan yang belum membaca apa pun tetap salah, karena
   langkah berikutnya tinggal satu baris.

`src/ingest/` **tidak** termasuk jalur penjawaban. Ia yang menulis karantina;
itu memang tugasnya. Penjagaan yang menutup pekerjaan sah akan dimatikan orang.

Batas yang diakui terbuka (RP-01): ini pembacaan bentuk kode. Kredensial yang
disusun lewat `getattr` atau dibaca dari berkas tetap lolos. Yang menutup sisa
itu bukan pemeriksa melainkan urutan pemeriksaan pada `src/penyimpanan/tiruan.py`,
yang menolak sebelum menyentuh data.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

JALUR_PENJAWABAN = ("src/rag", "src/llm", "src/api", "src/nlp")
"""Jalur yang C-03 sebut "layanan RAG dan pelatihan".

`src/ingest` sengaja tidak di sini, dan `src/penyimpanan` juga tidak: yang
kedua adalah lapisan yang menegakkan aturannya, bukan yang tunduk padanya.
"""

BERKAS_KREDENSIAL = Path("src") / "penyimpanan" / "kredensial_baku.py"

KREDENSIAL_TANPA_KARANTINA = ("PENJAWABAN", "PEMANGGIL_LLM")

_NAMA_KARANTINA = "KARANTINA"


def _di_jalur_penjawaban(berkas: Path, akar: Path) -> bool:
    relatif = berkas.relative_to(akar).as_posix()
    return any(relatif.startswith(j + "/") for j in JALUR_PENJAWABAN)


def _nilai_baca(simpul: ast.Call) -> ast.expr | None:
    for kata in simpul.keywords:
        if kata.arg == "baca":
            return kata.value
    return None


def _menyebut_karantina(simpul: ast.AST) -> bool:
    return any(
        (isinstance(anak, ast.Attribute) and anak.attr == _NAMA_KARANTINA)
        or (isinstance(anak, ast.Name) and anak.id == _NAMA_KARANTINA)
        for anak in ast.walk(simpul)
    )


def _berbentuk_tetapan(simpul: ast.expr) -> bool:
    """Himpunan yang tertulis apa adanya, bukan yang dihitung.

    `frozenset({Area.KORPUS})` tetapan; `frozenset(...) if syarat else ...`
    bukan. Perbedaannya bukan gaya penulisan melainkan isi C-03: yang kedua
    adalah satu kredensial yang berubah wujud, yaitu penanda status.
    """
    return not any(
        isinstance(anak, ast.IfExp | ast.BinOp | ast.BoolOp | ast.Compare)
        for anak in ast.walk(simpul)
    )


def _periksa_kredensial_baku(akar: Path) -> list[Temuan]:
    berkas = akar / BERKAS_KREDENSIAL
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "berkas kredensial baku tidak ditemukan — C-03 tidak dapat "
                "diperiksa, dan pemeriksa yang tidak menemukan bahannya melapor "
                "bersih tanpa memeriksa apa pun",
            )
        ]

    temuan: list[Temuan] = []
    pohon = ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.Assign) or not isinstance(simpul.value, ast.Call):
            continue
        nama = {t.id for t in simpul.targets if isinstance(t, ast.Name)}
        if not nama & set(KREDENSIAL_TANPA_KARANTINA):
            continue

        baca = _nilai_baca(simpul.value)
        if baca is None:
            continue
        kode = sorted(nama & set(KREDENSIAL_TANPA_KARANTINA))[0]

        if _menyebut_karantina(baca):
            temuan.append(
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"himpunan baca {kode} memuat karantina — C-03 menutup area "
                    "itu bagi jalur penjawaban, dan C-02 bersandar padanya",
                )
            )
        if not _berbentuk_tetapan(baca):
            temuan.append(
                Temuan(
                    berkas,
                    simpul.lineno,
                    f"himpunan baca {kode} dihitung dari syarat — C-03 menuntut "
                    "kredensial berbeda, bukan satu kredensial yang berubah wujud",
                )
            )
    return temuan


def _periksa_jalur_penjawaban(akar: Path) -> list[Temuan]:
    cabang = akar / "src"
    if not cabang.is_dir():
        return []

    temuan: list[Temuan] = []
    for berkas in berkas_python(cabang):
        if not _di_jalur_penjawaban(berkas, akar):
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"), filename=str(berkas))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == "Kredensial"
            ):
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        "jalur penjawaban membangun kredensialnya sendiri — "
                        "kredensial baku pada src/penyimpanan/ yang berlaku (C-03, R-01)",
                    )
                )
            elif (isinstance(simpul, ast.Attribute) and simpul.attr == _NAMA_KARANTINA) or (
                isinstance(simpul, ast.Name) and simpul.id == _NAMA_KARANTINA
            ):
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        "jalur penjawaban menyebut area karantina — C-03 "
                        "memisahkannya pada tingkat kredensial, dan penyebutan "
                        "di sini tidak punya kegunaan yang sah",
                    )
                )
    return temuan


def periksa_pemisahan_penyimpanan(akar: Path) -> list[Temuan]:
    """C-03 pada seluruh pohon.

    Pohon tanpa `src/` sama sekali menghasilkan daftar kosong; pohon dengan
    `src/` tetapi tanpa berkas kredensial baku menghasilkan temuan. Yang kedua
    adalah kegagalan diam yang paling mungkin: satu berkas berpindah nama, dan
    C-03 kembali tidak dijaga tanpa satu uji pun berubah warna.
    """
    if not (akar / "src").is_dir():
        return []
    return [*_periksa_kredensial_baku(akar), *_periksa_jalur_penjawaban(akar)]
