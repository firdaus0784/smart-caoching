"""Pemeriksa peringkat klaim — C-19, FR-F15, VS-08.

C-19 berbunyi: *"Klaim tidak bersandar tunggal pada segmen peringkat T3 atau
T4."*

Seperti C-16, pasal ini melarang sebuah **keadaan saat jalan**, bukan sebuah
bentuk kode — dan pemeriksa statis tidak dapat menjalankan sistemnya. Yang
dapat ditegakkan bentuk adalah **ketiadaan jalan keluar**: bila jawaban yang
tayang hanya dapat lahir dari validator, dan validator selalu menjalankan
VS-08, maka tidak ada jalur yang melewatinya.

Ketiga aturan di bawah menutup ketiga tempat jalan itu dapat dibuka, dan
masing-masing menutup lubang aturan sebelumnya.

## Tiga aturan

1. **`JawabanTervalidasi` hanya dibentuk pada `src/rag/validator/`.** Bentuk
   yang sama dengan aturan `Instruksi` ADR-13, yang sudah terbukti. Fitur 009
   kemudian tidak memiliki cara menayangkan jawaban yang belum lewat validator.
2. **Daftar pemeriksaan meliputi setiap anggota `KodePemeriksaan`.**
   Menjatuhkan VS-08 dari daftar jalannya adalah cara termudah melanggar C-19
   tanpa menyentuh satu baris logika pun — dan tidak satu uji perilaku pun
   gagal karenanya.
3. **`KodePemeriksaan` memuat persis kesembilan kode D-07 Bagian 6.1.** Tanpa
   ini, aturan 2 dapat dipuaskan dengan menghapus VS-08 dari enumnya.

Ketiganya bertingkat: aturan 3 menutup aturan 2, dan aturan 2 menutup aturan 1
yang menjaga bentuk yang isinya boleh kosong.

## Batas yang diakui terbuka

Sama dengan pemeriksa C-02, C-03, dan C-16: ini pembacaan bentuk kode.
Pembentukan lewat `getattr`, `model_construct`, atau penguraian dinamis lolos.
Yang menutup sisanya bukan pemeriksa melainkan `tervalidasi` sebagai sifat
terhitung — hasil yang kehilangan satu pemeriksaan tidak pernah tervalidasi,
betapa pun ia dibentuk.
"""

from __future__ import annotations

import ast
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan, berkas_python

BERKAS_VALIDATOR = Path("src") / "rag" / "validator" / "validator.py"
BERKAS_PEMERIKSAAN = Path("src") / "rag" / "validator" / "pemeriksaan.py"

NAMA_JAWABAN = "JawabanTervalidasi"
NAMA_ENUM_KODE = "KodePemeriksaan"
NAMA_DAFTAR_MENUNGGU = "_MENUNGGU_FITUR_020"
NAMA_KODE_C19 = "VS_08"
"""Kode yang C-19 persis tentangnya.

Aturan 2 memeriksa kelengkapan seluruh kode, dan kelengkapan itu dapat
dipuaskan dengan memindahkan sebuah kode ke daftar yang menunggu model —
ia hadir pada hasil, berstatus belum-dapat-diperiksa, dan tidak pernah
dijalankan. Bagi delapan kode lain itu keadaan yang jujur; bagi VS-08 itu
pembatalan C-19 yang terbaca seperti kejujuran.
"""

KODE_D07: frozenset[str] = frozenset(
    {"VS-01", "VS-02", "VS-03", "VS-04", "VS-05", "VS-06", "VS-07", "VS-08", "VS-09"}
)
"""Kesembilan kode D-07 Bagian 6.1.

Ditulis di sini, bukan dibaca dari enumnya. Pemeriksa yang membaca daftar dari
hal yang diperiksanya hanya membuktikan daftar sama dengan dirinya sendiri —
dan akan tetap lulus ketika VS-08 dihapus dari keduanya.
"""


def periksa_peringkat_klaim(akar: Path) -> list[Temuan]:
    """Ketiga aturan C-19 — lihat uraian modul."""
    temuan: list[Temuan] = []
    temuan.extend(_aturan_1_pembentukan_terbatas(akar))
    temuan.extend(_aturan_2_daftar_lengkap(akar))
    temuan.extend(_aturan_3_enum_persis_d07(akar))
    return temuan


def _aturan_1_pembentukan_terbatas(akar: Path) -> list[Temuan]:
    """`JawabanTervalidasi` hanya dibentuk pada modul validator."""
    diizinkan = (akar / BERKAS_VALIDATOR).resolve()
    temuan: list[Temuan] = []
    for berkas in berkas_python(akar / "src"):
        if berkas.resolve() == diizinkan:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == NAMA_JAWABAN
            ):
                temuan.append(
                    Temuan(
                        berkas,
                        simpul.lineno,
                        f"{NAMA_JAWABAN} dibentuk di luar modul validator — jawaban "
                        "yang dapat dibentuk di mana saja adalah jawaban yang dapat "
                        "tayang tanpa melewati VS-08 (C-19, FR-F15)",
                    )
                )
    return temuan


def _aturan_2_daftar_lengkap(akar: Path) -> list[Temuan]:
    """Daftar pemeriksaan yang dijalankan meliputi setiap kode.

    Dibaca dari **kunci pemetaan** pada modul validator, bukan dari penyebutan
    bebas di mana pun. Pemetaan berkunci kode adalah yang membuat "kesembilan
    kode dijalankan" dapat diperiksa sama sekali: daftar berurut membuatnya
    sifat yang kebetulan benar, bergantung pada tidak seorang pun menghapus
    satu baris.

    VS-08 yang jatuh dari pemetaan itu melanggar C-19 tanpa menyentuh satu
    baris logika pun.
    """
    berkas = akar / BERKAS_VALIDATOR
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul validator tidak ditemukan — menghapus tempat pemeriksaan "
                "dijalankan bukan cara sah meloloskan pemeriksa ini (C-19)",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    disebut = _kunci_kode(pohon)
    menunggu = _kunci_kode_pada(pohon, NAMA_DAFTAR_MENUNGGU)

    if NAMA_KODE_C19 in menunggu:
        return [
            Temuan(
                berkas,
                0,
                f"{NAMA_KODE_C19.replace('_', '-')} dipindahkan ke daftar yang menunggu "
                "model — ia memuaskan kelengkapan tanpa pernah dijalankan, dan C-19 "
                "adalah pasal yang persis tentang pemeriksaan itu",
            )
        ]

    hilang = {k for k in KODE_D07 if k.replace("-", "_") not in disebut}
    if hilang:
        return [
            Temuan(
                berkas,
                0,
                "kode pemeriksaan tidak disebut pada modul validator: "
                f"{sorted(hilang)} — kode yang tidak disebut adalah kode yang tidak "
                "dijalankan, dan VS-08 yang jatuh dari daftar melanggar C-19 tanpa "
                "menyentuh satu baris logika pun",
            )
        ]
    return []


def _kunci_kode(pohon: ast.Module) -> set[str]:
    """Nama anggota `KodePemeriksaan` yang menjadi kunci pemetaan mana pun."""
    return {
        kunci.attr
        for simpul in ast.walk(pohon)
        if isinstance(simpul, ast.Dict)
        for kunci in simpul.keys
        if isinstance(kunci, ast.Attribute)
        and isinstance(kunci.value, ast.Name)
        and kunci.value.id == NAMA_ENUM_KODE
    }


def _kunci_kode_pada(pohon: ast.Module, nama: str) -> set[str]:
    """Kunci kode pada satu tetapan bernama tertentu."""
    for simpul in ast.walk(pohon):
        if not isinstance(simpul, ast.AnnAssign | ast.Assign):
            continue
        sasaran = (
            [simpul.target] if isinstance(simpul, ast.AnnAssign) else list(simpul.targets)
        )
        if not any(isinstance(t, ast.Name) and t.id == nama for t in sasaran):
            continue
        if simpul.value is None:
            continue
        return {
            kunci.attr
            for anak in ast.walk(simpul.value)
            if isinstance(anak, ast.Dict)
            for kunci in anak.keys
            if isinstance(kunci, ast.Attribute)
            and isinstance(kunci.value, ast.Name)
            and kunci.value.id == NAMA_ENUM_KODE
        }
    return set()


def _aturan_3_enum_persis_d07(akar: Path) -> list[Temuan]:
    """`KodePemeriksaan` memuat persis kesembilan kode D-07 Bagian 6.1."""
    berkas = akar / BERKAS_PEMERIKSAAN
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                "modul pemeriksaan tidak ditemukan — tanpa enumnya, aturan 2 tidak "
                "memeriksa apa pun (C-19)",
            )
        ]

    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    nilai: set[str] = set()
    baris = 0
    for simpul in ast.walk(pohon):
        if isinstance(simpul, ast.ClassDef) and simpul.name == NAMA_ENUM_KODE:
            baris = simpul.lineno
            for anak in simpul.body:
                if (
                    isinstance(anak, ast.Assign)
                    and isinstance(anak.value, ast.Constant)
                    and isinstance(anak.value.value, str)
                ):
                    nilai.add(anak.value.value)
    if not baris:
        return [
            Temuan(
                berkas,
                0,
                f"{NAMA_ENUM_KODE} tidak ditemukan — aturan 2 menjadi tidak berarti (C-19)",
            )
        ]
    if nilai != KODE_D07:
        return [
            Temuan(
                berkas,
                baris,
                f"{NAMA_ENUM_KODE} tidak memuat persis kesembilan kode D-07 Bagian 6.1; "
                f"kurang: {sorted(KODE_D07 - nilai)}, lebih: {sorted(nilai - KODE_D07)} — "
                "menghapus VS-08 dari enumnya memuaskan aturan 2 tanpa menjalankannya",
            )
        ]
    return []
