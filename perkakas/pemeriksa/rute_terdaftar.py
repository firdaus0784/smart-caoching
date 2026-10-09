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

## `web/src` — T-3 fitur 027, R-16

Sejak frontend ada, jalur API juga tertulis pada TypeScript. Aturannya lain:
setiap untai berbentuk jalur pada `web/src/**/*.{ts,tsx}` wajib rute yang
**terpasang** pada aplikasi — bukan sekadar tercantum pada D-14. D-14 memuat
29 rute; peladen melayani tiga. Layar yang memanggil rute yang tercantum tetapi
belum terpasang gagal di lapangan dengan 404, dan pemeriksa yang membandingkan
dengan dokumen saja melaporkannya bersih.

Rute terpasang dibaca dari aplikasi yang disusun `susun_aplikasi`, bukan dari
tetapan: aplikasi itulah yang melayani permintaan. Jalur bertemplat
(`${id}`) dicocokkan dengan pola (`{id}`) per ruas. Komentar tidak dibaca —
yang dicari hanya literal untai.

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

AKHIRAN_WEB = (".ts", ".tsx")

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
    temuan.extend(_periksa_web(akar))
    return temuan


_LITERAL_WEB = re.compile(r"""(["'`])(/api/v\d+/[^"'`]*)\1""")
_RUAS_PEUBAH = re.compile(r"\$\{[^}]*\}|\{[^}]*\}")


def _periksa_web(akar: Path) -> list[Temuan]:
    """Setiap jalur API pada `web/src` wajib rute terpasang — lihat uraian modul."""
    src = akar / "web" / "src"
    if not src.is_dir():
        return []
    temuan: list[Temuan] = []
    terpasang: set[str] | None = None
    for berkas in sorted(b for b in src.rglob("*") if b.suffix in AKHIRAN_WEB):
        for nomor, baris in enumerate(berkas.read_text(encoding="utf-8").splitlines(), 1):
            if baris.lstrip().startswith(("//", "*", "/*")):
                continue
            for cocok in _LITERAL_WEB.finditer(baris):
                if terpasang is None:
                    terpasang = _rute_terpasang()
                jalur = cocok.group(2)
                if not _dilayani(_pola(jalur), terpasang):
                    temuan.append(
                        Temuan(
                            berkas=berkas.relative_to(akar),
                            baris=nomor,
                            pesan=(
                                f"jalur API {jalur!r} pada web/src tidak terpasang pada "
                                "peladen — layar yang memanggilnya gagal di lapangan (R-16, AG-02)"
                            ),
                        )
                    )
    return temuan


def _pola(jalur: str) -> str:
    return _RUAS_PEUBAH.sub("{}", jalur)


def _dilayani(jalur: str, terpasang: set[str]) -> bool:
    """Cocok bila sama dengan salah satu pola, per ruas.

    Ruas `{}` pada pola menerima satu ruas apa pun pada jalur — sehingga
    `/api/v1/percakapan/abc` dilayani `/api/v1/percakapan/{id}` — tetapi
    tidak melintasi garis miring. Ditemukan T-6: pencocokan sama-persis
    menolak jalur konkret pada data uji yang sebenarnya terpasang (KB-132).
    """
    ruas = jalur.split("/")
    for pola in terpasang:
        ruas_pola = pola.split("/")
        if len(ruas_pola) == len(ruas) and all(
            p == r or (p == "{}" and r != "") for p, r in zip(ruas_pola, ruas, strict=True)
        ):
            return True
    return False


def _rute_terpasang() -> set[str]:
    """Pola jalur yang dilayani aplikasi sungguhan, dengan kolaborator kosong.

    Kolaboratornya tidak pernah dipanggil: yang dibaca hanya tabel rute.
    """
    from fastapi.routing import APIRoute
    from src.api.aplikasi import susun_aplikasi

    class _Kosong:
        async def identitas(self, permintaan: object) -> object:
            raise AssertionError("tidak dipanggil")

        async def jawab(self, pertanyaan: str, **argumen: object) -> object:
            raise AssertionError("tidak dipanggil")

    from src.penyimpanan.riwayat import RiwayatMemori

    # `masuk` diisi agar rute masuk dan keluar (fitur 029) terbaca terpasang —
    # tanpa penjaga masuk keduanya memang tidak didaftarkan.
    aplikasi = susun_aplikasi(
        jalur=_Kosong(),  # type: ignore[arg-type]
        identitas=_Kosong(),  # type: ignore[arg-type]
        riwayat=RiwayatMemori(),
        masuk=_Kosong(),  # type: ignore[arg-type]
        pengguna=_Kosong(),  # type: ignore[arg-type]
        kurasi=_Kosong(),  # type: ignore[arg-type]
        penemuan=_Kosong(),  # type: ignore[arg-type]
        # Fitur 035: rute peneliti terpasang bersama penyimpan analitik.
        analitik=_Kosong(),  # type: ignore[arg-type]
        penilaian=_Kosong(),  # type: ignore[arg-type]
        aduan=_Kosong(),  # type: ignore[arg-type]
        sumber=_Kosong(),  # type: ignore[arg-type]
    )
    return {_pola(rute.path) for rute in aplikasi.routes if isinstance(rute, APIRoute)}


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
