"""Pemeriksa bahasa antarmuka — C-13, NFR-19, `docs/D05.md` Bagian 10.

C-13 berbunyi: kalimat ≤ 20 kata, istilah teknis dijelaskan pada kemunculan
pertama, tanpa singkatan yang tidak diuraikan. D-05 Bagian 10 menambahkan tiga
larangan tegas, dua di antaranya terbaca mesin: tanpa tanda seru pada pesan
yang berkaitan dengan kelalaian pengguna, dan tanpa kata "gagal", "belum
tuntas", atau "terlambat".

## Mengapa dibangun sebelum `web/` ada

C-13 terdaftar `fitur_pengunci="013 penyempurnaan antarmuka"` sejak fitur 001.
Catatan L8 pemeriksa C-14 memerintahkan dua pasal tersisa **ditinjau tiap
fitur**, dan menuliskan pertanyaan tinjauannya: *"apakah kaidah bahasa
antarmuka dapat diperiksa atas mikrokopi D-05 sebelum layarnya dibangun"*.

Jawabannya lebih tegas daripada yang pertanyaan itu duga: untai yang menghadap
pengguna **sudah ada di dalam `src/` hari ini** — penafian jawaban, pesan di
luar domain, tiga pesan lapisan HTTP, lima pesan jalur ekstraksi. Seluruhnya
kode yang disebarkan dan seluruhnya terikat C-13. Menunggu `web/` berarti
membiarkannya berjalan tanpa penjaga.

Bentuknya sama dengan C-17 dan C-18 pada fitur 001: aturan berdiri lebih dulu,
menunggu pemanggil yang kelak wajib mematuhinya.

## Dua aturan, dan mengapa yang kedua yang memberi gigi

**Aturan 1 memeriksa isi.** Panjang kalimat, tanda seru, kata terlarang, kode
galat, singkatan sistem.

**Aturan 2 memeriksa bentuk.** Aturan 1 sendirian dapat dilewati siapa pun yang
menulis untai harfiah langsung pada jalan keluar alih-alih memakai tetapan
terdaftar — dan itu justru yang paling mungkin terjadi saat menambal galat
dengan tergesa. Karena itu jalan keluar yang menghadap pengguna tidak boleh
menerima untai harfiah sama sekali. Yang dijaga bukan kata-katanya melainkan
tidak adanya pintu samping.

## Singkatan mana yang dilarang, dan mengapa bukan semuanya

Menyapu seluruh singkatan akan menyalak pada RKAS, BOS, dan SPJ — yang justru
lebih dipahami kepala sekolah daripada tim ini. Pemeriksa yang menyalak keliru
adalah pemeriksa yang dimatikan orang; pelajaran itu sudah tertulis pada
`ruang_lingkup.py`.

Yang dilarang singkatan **sistem**, bukan singkatan domain. Batas ini diakui
terbuka: singkatan domain yang benar-benar asing tetap lolos, dan yang
menangkapnya uji keterbacaan BT-20 bersama persona P1 dan P3 — bukan mesin.

## `web/` — fitur 027 T-4

Kedua aturan berlaku juga pada frontend, dengan bentuk yang sejajar.
Aturan 1 membaca **setiap** untai pada `web/src/mikrokopi.ts` — seluruh isi
berkas itu menghadap pengguna, sehingga kesepakatan awalan nama tidak
dibutuhkan. Aturan 2 menolak teks harfiah pada `.tsx` di luar berkas itu:
teks JSX, untai pada atribut yang dibaca pengguna (`aria-label`, `title`,
`placeholder`, `alt`, …), untai sebagai anak JSX, dan untai berkalimat di
mana pun pada berkas itu.

Pohon sintaks dibaca `teks_web.mjs` dengan pengurai `rolldown` — bagian
`vite` yang sudah terkunci — sebab pola teks tidak dapat membedakan teks JSX
dari perbandingan `a > b`. Batasnya: untai satu kata di luar JSX lolos Aturan
2, sebab ia tidak dapat dibedakan dari nilai enum seperti `"kuat"`.

## Batas lain yang diakui terbuka

Pemeriksa membaca tetapan tingkat modul. Untai yang disusun saat jalan —
sambungan antar-untai, hasil pemformatan — tidak terbaca, sejalan RP-01 dan
RP-05. C-13 karena itu **belum sepenuhnya** terjaga mesin, dan bagian layarnya
tetap menunggu fitur 013. Yang berpindah adalah pasal ini dari "tidak
diperiksa sama sekali" menjadi "diperiksa pada permukaan yang sudah ada".
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

DIPERIKSA = ("src", "web")
"""`perkakas/` memuat daftar kata terlarang ini sendiri; `tests/` memuat
pelanggaran buatan yang memang harus ada."""

AWALAN_MENGHADAP_PENGGUNA = ("PESAN", "PENAFIAN", "MIKROKOPI")
"""Tetapan yang isinya sampai ke mata pengguna. Kesepakatan penamaan, dan
Aturan 2 yang membuatnya tidak dapat dilewati.

Dibandingkan peka huruf besar-kecil. `pesan` sebagai peubah setempat atau
parameter karena itu tidak tersapu, dan menyapunya akan menyalak pada setiap
penerus pesan."""

BATAS_KATA = 20
"""NFR-19. Inklusif: dua puluh kata diterima, dua puluh satu tidak."""

KATA_TERLARANG = ("gagal", "belum tuntas", "terlambat")
"""D-05 Bagian 10 larangan kedua."""

SINGKATAN_SISTEM = (
    "API",
    "HTTP",
    "HTTPS",
    "JSON",
    "JSONL",
    "LLM",
    "OCR",
    "RAG",
    "NER",
    "SQL",
    "URL",
    "URI",
    "UUID",
    "ID",
    "PII",
    "CSV",
    "XML",
)
"""Singkatan yang pembacanya tidak wajib tahu. Singkatan domain — RKAS, BOS,
SPJ, EDS, ANBK — sengaja tidak di sini."""

FUNGSI_JALAN_KELUAR = ("_galat",)
"""Fungsi yang isinya menjadi badan tanggapan bagi pengguna."""

KUNCI_PESAN = "pesan"
"""Kunci pada `content=` yang isinya ditayangkan. D-14 Bagian 4."""

_KODE_GALAT = re.compile(r"\b(?:kode|error|galat)\s*[:\-]?\s*\d{3}\b", re.IGNORECASE)
_PEMISAH_KALIMAT = re.compile(r"[.!?]+")


def _kalimat(teks: str) -> list[str]:
    return [k.strip() for k in _PEMISAH_KALIMAT.split(teks) if k.strip()]


def _menghadap_pengguna(nama: str) -> bool:
    """Perbandingan **peka huruf besar-kecil**, dan itu yang menyaringnya.

    Syarat `nama.isupper()` sempat ditulis di sini dan dibuang: uji mutasi
    membuktikannya tidak mengubah perilaku apa pun — `startswith` atas awalan
    berhuruf kapital sudah menolak peubah setempat bernama `pesan` — sementara
    ia justru **melubangi** pemeriksa dengan meloloskan `PESAN_Pengguna`.
    Syarat yang tidak menambah penolakan tetapi menambah kelolosan adalah
    syarat yang lebih buruk daripada tidak ada.
    """
    return nama.startswith(AWALAN_MENGHADAP_PENGGUNA)


def untai_menghadap_pengguna(akar: Path) -> list[tuple[Path, int, str, str]]:
    """Kumpulkan seluruh untai yang menghadap pengguna beserta tempatnya.

    Terpisah dari pemeriksaannya agar uji dapat membuktikan pemeriksa
    **menemukan sesuatu** — pemeriksa yang tidak menemukan apa pun akan
    melaporkan bersih dengan sama meyakinkannya.
    """
    hasil: list[tuple[Path, int, str, str]] = []
    for cabang in (akar / d for d in DIPERIKSA):
        if not cabang.is_dir():
            continue
        for berkas in berkas_python(cabang):
            try:
                pohon = ast.parse(berkas.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for simpul in ast.walk(pohon):
                nama, nilai = _tetapan(simpul)
                if nama is None or nilai is None or not _menghadap_pengguna(nama):
                    continue
                for baris, teks in _untai_pada(nilai):
                    hasil.append((berkas, baris, nama, teks))
    return hasil


def _tetapan(simpul: ast.AST) -> tuple[str | None, ast.expr | None]:
    """Tetapan pada tingkat mana pun — modul, kelas, maupun fungsi.

    Menyusuri tingkat modul saja pernah melewatkan dua untai sungguhan:
    `GalatLayananModel.PESAN_PENGGUNA` dan `GalatAksesDitolak.PESAN_PENGGUNA`,
    keduanya atribut kelas. Kesepakatan penamaannya benar; yang keliru
    kedalaman penyusuran. Dicatat karena bentuk kekeliruan ini tidak terlihat
    dari hasil yang bersih.
    """
    if isinstance(simpul, ast.Assign) and len(simpul.targets) == 1:
        sasaran = simpul.targets[0]
        if isinstance(sasaran, ast.Name):
            return sasaran.id, simpul.value
    if isinstance(simpul, ast.AnnAssign) and isinstance(simpul.target, ast.Name):
        return simpul.target.id, simpul.value
    return None, None


def _untai_pada(nilai: ast.expr) -> list[tuple[int, str]]:
    """Untai harfiah di dalam sebuah nilai — termasuk nilai di dalam dict."""
    keluar: list[tuple[int, str]] = []
    if isinstance(nilai, ast.Constant) and isinstance(nilai.value, str):
        keluar.append((nilai.lineno, nilai.value))
    elif isinstance(nilai, ast.JoinedStr):
        pass  # disusun saat jalan — batas yang diakui terbuka
    elif isinstance(nilai, ast.BinOp):
        keluar += _untai_pada(nilai.left) + _untai_pada(nilai.right)
    elif isinstance(nilai, ast.Dict):
        for isi in nilai.values:
            keluar += _untai_pada(isi)
    elif isinstance(nilai, ast.List | ast.Tuple | ast.Set):
        for isi in nilai.elts:
            keluar += _untai_pada(isi)
    return keluar


def _periksa_isi(berkas: Path, baris: int, nama: str, teks: str) -> list[Temuan]:
    temuan: list[Temuan] = []
    padat = " ".join(teks.split())

    for kalimat in _kalimat(padat):
        jumlah = len(kalimat.split())
        if jumlah > BATAS_KATA:
            temuan.append(
                Temuan(
                    berkas,
                    baris,
                    f"{nama}: kalimat {jumlah} kata, batas {BATAS_KATA} (C-13, NFR-19)",
                )
            )

    if "!" in padat:
        temuan.append(
            Temuan(berkas, baris, f"{nama}: memuat tanda seru (D-05 Bagian 10 larangan pertama)")
        )

    rendah = padat.lower()
    for kata in KATA_TERLARANG:
        if kata in rendah:
            temuan.append(
                Temuan(
                    berkas, baris, f"{nama}: memuat kata {kata!r} (D-05 Bagian 10 larangan kedua)"
                )
            )

    if _KODE_GALAT.search(padat):
        temuan.append(Temuan(berkas, baris, f"{nama}: memuat kode galat (AGENTS.md Gaya)"))

    for singkat in SINGKATAN_SISTEM:
        if re.search(rf"\b{re.escape(singkat)}\b", padat):
            temuan.append(
                Temuan(
                    berkas,
                    baris,
                    f"{nama}: memuat singkatan sistem {singkat!r} tanpa uraian (C-13)",
                )
            )

    return temuan


def _periksa_bentuk(akar: Path) -> list[Temuan]:
    """Aturan 2 — jalan keluar tidak boleh menerima untai harfiah."""
    temuan: list[Temuan] = []
    for cabang in (akar / d for d in DIPERIKSA):
        if not cabang.is_dir():
            continue
        for berkas in berkas_python(cabang):
            try:
                pohon = ast.parse(berkas.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for simpul in ast.walk(pohon):
                if not isinstance(simpul, ast.Call):
                    continue
                temuan += _periksa_panggilan(berkas, simpul)
    return temuan


def _periksa_panggilan(berkas: Path, simpul: ast.Call) -> list[Temuan]:
    temuan: list[Temuan] = []
    nama = simpul.func.id if isinstance(simpul.func, ast.Name) else ""

    if nama in FUNGSI_JALAN_KELUAR:
        for argumen in simpul.args:
            if isinstance(argumen, ast.Constant) and isinstance(argumen.value, str):
                temuan.append(
                    Temuan(
                        berkas,
                        argumen.lineno,
                        f"{nama}() menerima untai harfiah — wajib menunjuk tetapan "
                        f"ber-awalan {AWALAN_MENGHADAP_PENGGUNA[0]} (C-13)",
                    )
                )

    for kata_kunci in simpul.keywords:
        if kata_kunci.arg != "content" or not isinstance(kata_kunci.value, ast.Dict):
            continue
        for kunci, isi in zip(kata_kunci.value.keys, kata_kunci.value.values, strict=True):
            if not (isinstance(kunci, ast.Constant) and kunci.value == KUNCI_PESAN):
                continue
            if isinstance(isi, ast.Constant) and isinstance(isi.value, str):
                temuan.append(
                    Temuan(
                        berkas,
                        isi.lineno,
                        f"content[{KUNCI_PESAN!r}] menerima untai harfiah — wajib "
                        f"menunjuk tetapan (C-13)",
                    )
                )
    return temuan


BERKAS_MIKROKOPI = Path("web") / "src" / "mikrokopi.ts"
PENGUMPUL_WEB = Path(__file__).with_name("teks_web.mjs")


class GalatPengumpulWeb(Exception):
    """Pengumpul teks `web/` tidak dapat dijalankan — gerbang gagal, bukan dilewati."""


def kumpulkan_teks_web(akar: Path, *, node: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """Untai `mikrokopi.ts` dan teks harfiah `.tsx`, dibaca pengurai sungguhan.

    Terpisah dari pemeriksaannya dengan alasan yang sama dengan
    `untai_menghadap_pengguna`: uji dapat membuktikan pengumpulnya
    **menemukan sesuatu**.
    """
    # Absolut: `createRequire` pada pengumpul menolak jalur relatif, dan
    # `make check` memanggil dengan akar relatif (KB-130).
    web = (akar / "web").resolve()
    if not (web / "node_modules").is_dir():
        raise GalatPengumpulWeb("web/node_modules tidak ada — jalankan `make setup`")
    node = node or shutil.which("node")
    if node is None:
        raise GalatPengumpulWeb(
            "node tidak ditemukan — pasang Node.js 22 beserta npm, lalu jalankan `make setup`"
        )
    try:
        hasil = subprocess.run(
            [node, str(PENGUMPUL_WEB), str(web)],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as galat:
        raise GalatPengumpulWeb(f"pengumpul teks web/ tidak dapat dijalankan: {galat}") from galat
    if hasil.returncode != 0:
        # Node menutup galat tak tertangkap dengan baris versinya; baris
        # galatnya sendiri yang berguna bagi pembaca laporan.
        baris = hasil.stderr.strip().splitlines()
        sebab = next((b for b in baris if "Error" in b), (baris or ["tanpa keluaran"])[-1])
        raise GalatPengumpulWeb(f"pengumpul teks web/ berhenti: {sebab}")
    data: dict[str, list[dict[str, Any]]] = json.loads(hasil.stdout)
    return data


def periksa_bahasa_web(akar: Path, *, node: str | None = None) -> list[Temuan]:
    """C-13 atas `web/` — T-4 fitur 027, R-12.

    Aturan 1 atas setiap untai `web/src/mikrokopi.ts`; Aturan 2 menolak teks
    harfiah pada `.tsx` di luar berkas itu. Tanpa Node, **gagal** — sejajar
    V-01: gerbang yang lulus tanpa melihat `web/` adalah laporan palsu.
    """
    web = akar / "web"
    if not (web / "package.json").is_file():
        return []
    if not (akar / BERKAS_MIKROKOPI).is_file():
        return [
            Temuan(
                BERKAS_MIKROKOPI,
                0,
                "mikrokopi.ts tidak ada — teks antarmuka tidak memiliki tempat yang dapat "
                "diperiksa (C-13, R-12)",
            )
        ]
    try:
        data = kumpulkan_teks_web(akar, node=node)
    except GalatPengumpulWeb as galat:
        return [Temuan(web, 0, str(galat))]

    temuan = [
        Temuan(Path("web") / g["berkas"], 0, f"berkas tidak dapat diurai: {g['pesan']}")
        for g in data["galat_urai"]
    ]
    if not data["mikrokopi"]:
        temuan.append(
            Temuan(
                BERKAS_MIKROKOPI,
                0,
                "pengumpul tidak menemukan satu untai pun pada mikrokopi.ts — laporan bersih "
                "atas nol untai adalah laporan palsu",
            )
        )
    for butir in data["mikrokopi"]:
        temuan += _periksa_isi(
            Path("web") / butir["berkas"], butir["baris"], "mikrokopi", butir["teks"]
        )
    for butir in data["harfiah"]:
        temuan.append(
            Temuan(
                Path("web") / butir["berkas"],
                butir["baris"],
                f"{butir['jenis']} {butir['teks']!r} ditulis harfiah — teks antarmuka wajib "
                "berasal dari mikrokopi.ts (C-13, R-12)",
            )
        )
    return temuan


def periksa_bahasa_antarmuka(akar: Path) -> list[Temuan]:
    """C-13 pada `src/` dan, sejak fitur 027, pada `web/`."""
    temuan: list[Temuan] = []
    for berkas, baris, nama, teks in untai_menghadap_pengguna(akar):
        temuan += _periksa_isi(berkas, baris, nama, teks)
    return temuan + _periksa_bentuk(akar) + periksa_bahasa_web(akar)
