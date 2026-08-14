"""Pemeriksa perekaman telemetri — C-04, R-04, R-05, FR-J05.

C-04 berbunyi: *"Telemetri tidak merekam bagi pengguna tanpa persetujuan
aktif. Pencabutan menghentikan perekaman seketika."*

Seperti C-06 dan C-19, pasal ini melarang sebuah **keadaan saat jalan**, dan
pemeriksa statis tidak dapat menjalankan sistemnya. Yang dapat ditegakkan
bentuk adalah **ketiadaan jalan keluar**: bila peristiwa hanya dapat lahir
dari gerbang, dan gerbang tidak dapat dipanggil tanpa keadaan persetujuan,
maka tidak ada jalur yang melewatinya.

## Tiga aturan

1. **`Peristiwa` hanya dibentuk pada `src/telemetri/gerbang.py`.** Bentuk yang
   sama dengan `ButirTayang` (C-06) dan `JawabanTervalidasi` (C-19), keduanya
   sudah terbukti.

2. **`Peristiwa` tidak memiliki bidang bernama identitas.** FR-J02 menulis "id
   pengguna **terpseudonim**"; bidang beridentitas pada modelnya membuat
   pseudonimisasi menjadi kebiasaan pemanggil alih-alih sifat tipenya.

3. **Parameter keadaan pada `rekam()` ada dan tanpa nilai bawaan.** Ini yang
   menutup dua aturan pertama: gerbang yang parameternya berbawaan `DIBERIKAN`
   memuaskan keduanya sambil membatalkan C-04 pada setiap pemanggilan yang
   lupa mengisinya — dan tidak satu uji perilaku pun gagal karenanya, sebab
   uji selalu mengisinya.

Bentuk aturan 3 sama dengan aturan `AmbangKecukupan` pada pemeriksa C-16:
parameter berbawaan yang berubah menjadi "tanpa keterangan berarti boleh".

## Yang **tidak** diperiksa, dan mengapa

Separuh kedua C-04 — "pencabutan menghentikan perekaman seketika" — tidak
terbaca AST. Yang menutupnya adalah ketiadaan tempat menyimpan keadaan pada
gerbang, dan itu ditegakkan uji perilaku beserta uji bentuk pada
`tests/telemetri/test_gerbang.py`. Pemeriksa yang mengaku memeriksanya akan
terbaca lebih tebal daripada kenyataannya.

## Batas yang diakui terbuka

Sama dengan pemeriksa C-02, C-03, C-05, C-06, C-16, dan C-19: ini pembacaan
bentuk kode. Pembentukan lewat `model_construct` atau `getattr` lolos.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_GERBANG = Path("src") / "telemetri" / "gerbang.py"
BERKAS_PERISTIWA = Path("src") / "telemetri" / "peristiwa.py"

NAMA_PERISTIWA = "Peristiwa"
NAMA_FUNGSI_REKAM = "rekam"
NAMA_TIPE_KEADAAN = "KeadaanPersetujuan"
NAMA_PARAMETER = "keadaan"

BIDANG_BERIDENTITAS: frozenset[str] = frozenset({"id_pengguna", "nama", "surel", "email", "alamat"})
"""Nama bidang yang membatalkan pseudonimisasi FR-J02 bila ada pada `Peristiwa`."""


def periksa_perekaman_telemetri(akar: Path) -> list[Temuan]:
    """Ketiga aturan C-04 — lihat uraian modul."""
    temuan: list[Temuan] = []
    temuan.extend(_aturan_1_pembentukan_terbatas(akar))
    temuan.extend(_aturan_2_tanpa_bidang_identitas(akar))
    temuan.extend(_aturan_3_keadaan_wajib_tanpa_bawaan(akar))
    return temuan


def _aturan_1_pembentukan_terbatas(akar: Path) -> list[Temuan]:
    """`Peristiwa` hanya dibentuk pada gerbang."""
    diizinkan = (akar / BERKAS_GERBANG).resolve()
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if berkas.resolve() == diizinkan:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == NAMA_PERISTIWA
            ):
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        f"{NAMA_PERISTIWA} dibentuk di luar gerbang perekaman — "
                        "peristiwa yang dapat dibentuk di mana saja adalah peristiwa "
                        "yang dapat terekam tanpa persetujuan (C-04, FR-J05)",
                    )
                )
    return temuan


def _aturan_2_tanpa_bidang_identitas(akar: Path) -> list[Temuan]:
    """`Peristiwa` tidak memiliki bidang bernama identitas — FR-J02."""
    berkas = akar / BERKAS_PERISTIWA
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul peristiwa tidak ditemukan — menghapus bentuk yang dijaga bukan "
                "cara sah meloloskan pemeriksa ini (C-04)",
            )
        ]

    kelas = _kelas_bernama(ast.parse(berkas.read_text(encoding="utf-8")), NAMA_PERISTIWA)
    if kelas is None:
        return [
            Temuan(
                berkas,
                0,
                f"{NAMA_PERISTIWA} tidak ditemukan — tipe yang hilang bukan tipe yang "
                "aman, ia tipe yang penjagaannya pindah entah ke mana (C-04)",
            )
        ]

    return [
        Temuan(
            berkas,
            simpul.lineno,
            f"{NAMA_PERISTIWA} memiliki bidang beridentitas '{simpul.target.id}' — "
            "FR-J02 menuntut id pengguna terpseudonim, dan bidang beridentitas "
            "membuat pseudonimisasi menjadi kebiasaan pemanggil alih-alih sifat "
            "tipenya (C-04, C-05)",
        )
        for simpul in kelas.body
        if isinstance(simpul, ast.AnnAssign)
        and isinstance(simpul.target, ast.Name)
        and simpul.target.id in BIDANG_BERIDENTITAS
    ]


def _aturan_3_keadaan_wajib_tanpa_bawaan(akar: Path) -> list[Temuan]:
    """Parameter keadaan ada, bertipe benar, dan tanpa nilai bawaan."""
    berkas = akar / BERKAS_GERBANG
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "gerbang perekaman tidak ditemukan — menghapus gerbang bukan cara sah "
                "meloloskan pemeriksa ini (C-04)",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.FunctionDef) or simpul.name != NAMA_FUNGSI_REKAM:
            continue
        return _periksa_parameter(berkas, simpul)

    return [
        Temuan(
            berkas,
            0,
            f"fungsi {NAMA_FUNGSI_REKAM}() tidak ditemukan pada gerbang (C-04)",
        )
    ]


def _periksa_parameter(berkas: Path, fungsi: ast.FunctionDef) -> list[Temuan]:
    argumen = [*fungsi.args.args, *fungsi.args.kwonlyargs]
    keadaan = [a for a in argumen if a.arg == NAMA_PARAMETER]
    if not keadaan:
        return [
            Temuan(
                berkas,
                fungsi.lineno,
                f"{NAMA_FUNGSI_REKAM}() tidak menerima parameter "
                f"'{NAMA_PARAMETER}' — gerbang yang tidak menanyakan persetujuan "
                "bukan gerbang (C-04)",
            )
        ]

    anotasi = keadaan[0].annotation
    if anotasi is None or NAMA_TIPE_KEADAAN not in ast.unparse(anotasi):
        return [
            Temuan(
                berkas,
                fungsi.lineno,
                f"parameter '{NAMA_PARAMETER}' tidak bertipe {NAMA_TIPE_KEADAAN} — "
                "bendera boolean dapat diisi True oleh pemanggil yang lelah, "
                "sedangkan keadaan menuntut dibaca dari catatan persetujuan (C-04)",
            )
        ]

    letak = fungsi.args.kwonlyargs.index(keadaan[0]) if keadaan[0] in fungsi.args.kwonlyargs else -1
    bawaan = fungsi.args.kw_defaults[letak] if letak >= 0 else None
    if bawaan is not None:
        return [
            Temuan(
                berkas,
                fungsi.lineno,
                f"parameter '{NAMA_PARAMETER}' memiliki nilai bawaan — parameter "
                "berbawaan akan berubah menjadi 'tanpa keterangan berarti boleh' "
                "pada pemanggilan pertama yang lupa mengisinya, dan tidak satu uji "
                "perilaku pun gagal karenanya (C-04)",
            )
        ]
    return []


def _kelas_bernama(pohon: ast.Module, nama: str) -> ast.ClassDef | None:
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ClassDef) and simpul.name == nama:
            return simpul
    return None
