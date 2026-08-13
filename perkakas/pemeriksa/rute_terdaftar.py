"""Pemeriksa rute terdaftar — A-2 fitur 021, R-02, R-03, AG-02.

AG-02 melarang menambah rute yang tidak ada pada `docs/D14.md` Bagian 3. Uji
`tests/api/test_peran.py` sudah membandingkan `PETA_RUTE` dengan dokumen dua
arah, dan itu menutup rute yang **didaftarkan**. Yang tidak ditutupnya adalah
rute yang **tidak didaftarkan sama sekali**.

## Perbedaan itu bukan teoretis

Adaptor HTTP yang menyusul akan menuliskan jalurnya sebagai untai pada
dekoratornya sendiri. Untai yang tidak pernah masuk `PETA_RUTE` lolos kedua
arah uji itu — tabelnya tetap cocok dengan dokumen, sementara peladen melayani
rute yang tidak ada pada keduanya. Kendali peran kemudian tidak pernah
dipanggil baginya, sebab tidak ada baris yang menyebutnya.

Pemeriksa ini karena itu menyapu **untai** berbentuk jalur API di seluruh
`src/`, bukan daftar yang sudah didaftarkan.

## Yang diperiksanya hari ini, dan itu disengaja

Adaptor HTTP belum ada. Hari ini pemeriksa ini menjaga satu hal yang sudah
nyata: **tidak ada modul selain `src/api/peran.py` yang membawa untai jalur
API.** Jalur yang tersebar pada modul lain adalah jalur yang akan berselisih
dengan tabelnya, dan selisih pada jalur tidak menghasilkan galat — ia
menghasilkan permintaan yang tidak pernah sampai.

Ia sengaja **tidak diklaim** memeriksa dekorator yang belum ada. Pemeriksa yang
mengaku menjaga sesuatu yang belum ada terbaca lebih tebal daripada
kenyataannya, dan itu bentuk laporan bersih yang tidak memeriksa apa pun.

## Batas yang diakui terbuka

Jalur yang dirakit dari potongan — `f"{AWALAN}/tanya"` — lolos. Sama dengan
seluruh pemeriksa AST lain pada proyek ini (RP-01): yang dirancang adalah
pembatasan kerugian, bukan pencegahan sempurna.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_PERAN = Path("src") / "api" / "peran.py"

POLA_JALUR = re.compile(r"^/api/v\d+/")
"""Untai yang berbentuk jalur API. Awalan versi ikut agar untai lain yang
kebetulan dimulai garis miring tidak terjaring."""


def periksa_rute_terdaftar(akar: Path) -> list[Temuan]:
    """Satu aturan: untai jalur API hanya boleh berada pada `src/api/peran.py`.

    Lihat uraian modul mengapa ia bukan pengulangan uji `PETA_RUTE`.
    """
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if berkas.relative_to(akar) == BERKAS_PERAN:
            continue
        temuan.extend(_jalur_pada(berkas, akar))
    return temuan


def _jalur_pada(berkas: Path, akar: Path) -> list[Temuan]:
    try:
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    ditemukan: list[Temuan] = []
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.Constant) or not isinstance(simpul.value, str):
            continue
        if not POLA_JALUR.match(simpul.value):
            continue
        if _di_dalam_uraian(pohon, simpul):
            continue
        ditemukan.append(
            Temuan(
                berkas=berkas.relative_to(akar),
                baris=simpul.lineno,
                pesan=(
                    f"untai jalur API {simpul.value!r} berada di luar "
                    f"{BERKAS_PERAN.as_posix()} — rute yang tidak masuk `PETA_RUTE` "
                    "tidak pernah melewati kendali peran (AG-02, R-03)"
                ),
            )
        )
    return ditemukan


def _di_dalam_uraian(pohon: ast.Module, simpul: ast.Constant) -> bool:
    """Uraian modul dan docstring boleh menyebut jalur.

    Melarangnya di sana berarti melarang menjelaskan rute pada dokumentasinya
    sendiri — dan aturan yang melarang menjelaskan akan dimatikan orang.
    """
    return any(isinstance(induk, ast.Expr) and induk.value is simpul for induk in ast.walk(pohon))
