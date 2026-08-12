"""Pemeriksa regulasi dicabut — C-07, VS-06, KL-07, R-05.

C-07 berbunyi: *"Sistem tidak menjawab berdasarkan regulasi berstatus
dicabut."*

## Pasal ini dijaga tiga lapis, dan pemeriksanya memeriksa ketiganya

| Lapis | Tempat | Fitur |
|---|---|---|
| Penjawaban | VS-06 pada `src/rag/validator/sitasi.py` | 008 |
| Penyajian | `Sitasi` pada `src/rag/jawaban/tanggapan.py` | 009 |
| Ingesti | L3 pada `src/ingest/kurasi/saring.py` | 010 |

Memeriksa satu lapis saja akan membuat pemeriksanya **terbaca lengkap
sementara ia menjaga sepertiga** — dan penghapusan dua lapis hilir tidak
terlihat sampai ada jawaban yang tayang atas regulasi yang sudah dicabut.

Godaan memeriksa lapis yang fitur ini bangun saja nyata: L3 adalah yang paling
segar di ingatan ketika pemeriksa ini ditulis. Justru dua lapis lain yang lebih
mungkin runtuh diam-diam, sebab keduanya sudah lama berdiri dan tidak seorang
pun menyentuhnya.

**Masing-masing lapis dilaporkan terpisah.** Satu temuan gabungan akan
menyembunyikan lapis mana yang hilang, dan yang hilang menentukan seberapa jauh
regulasi yang dicabut dapat berjalan sebelum tertahan.

## Yang diperiksa pada tiap lapis

Bukan bahwa lapisnya benar — pemeriksa statis tidak dapat menyatakan itu —
melainkan bahwa lapisnya **ada**: berkasnya ada, dan status keberlakuan
sungguh dibaca di sana. Kebenarannya ditegakkan uji perilaku masing-masing
fitur; yang ditutup di sini adalah lapis yang lenyap tanpa satu uji pun gagal,
sebab uji lapis lain tetap lulus.

## Batas yang diakui terbuka

Ini pembacaan bentuk kode. Lapis yang tetap ada tetapi keliru membandingkan —
misalnya memakai `is not` di tempat `is` — lolos di sini dan tertahan uji
perilaku. Keduanya diperlukan, dan tidak satu pun cukup sendiri.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

NAMA_ENUM_STATUS = "StatusKeberlakuan"


@dataclass(frozen=True)
class Lapis:
    """Satu lapis penjagaan C-07, beserta apa yang membuktikan ia masih ada."""

    nama: str
    berkas: Path
    anggota: frozenset[str]
    """Anggota `StatusKeberlakuan` yang wajib dibaca lapis ini.

    Dinyatakan sebagai himpunan, bukan satu nama: lapis ingesti membaca
    `BERLAKU` (menolak selain itu) sedangkan dua lapis hilir membaca `DICABUT`
    (menolak persis itu). Menuntut ejaan yang sama pada ketiganya akan memaksa
    salah satunya ditulis dengan cara yang lebih lemah.
    """
    akibat_bila_hilang: str


LAPIS_C07: tuple[Lapis, ...] = (
    Lapis(
        nama="penjawaban (VS-06)",
        berkas=Path("src") / "rag" / "validator" / "sitasi.py",
        anggota=frozenset({"DICABUT"}),
        akibat_bila_hilang=(
            "jawaban yang bersitasi regulasi dicabut lolos validator dan tayang"
        ),
    ),
    Lapis(
        nama="penyajian (Sitasi)",
        berkas=Path("src") / "rag" / "jawaban" / "tanggapan.py",
        anggota=frozenset({"DICABUT"}),
        akibat_bila_hilang=(
            "tanggapan dapat menyusun sitasi atas regulasi dicabut meskipun "
            "validator menahannya"
        ),
    ),
    Lapis(
        nama="ingesti (L3)",
        berkas=Path("src") / "ingest" / "kurasi" / "saring.py",
        anggota=frozenset({"BERLAKU"}),
        akibat_bila_hilang=(
            "butir bersumber regulasi dicabut masuk antrean kurasi dan dapat "
            "disetujui"
        ),
    ),
)
"""Ketiga lapis, ditulis di sini alih-alih ditemukan dengan menyapu `src/`.

Sapuan akan menyatakan "ada tiga tempat yang membaca status keberlakuan", dan
pernyataan itu tetap benar ketika ketiganya berpindah ke satu berkas — lalu
satu penghapusan mematikan ketiganya sekaligus.
"""


def periksa_regulasi_dicabut(akar: Path) -> list[Temuan]:
    """Ketiga lapis C-07, masing-masing terpisah — lihat uraian modul."""
    temuan: list[Temuan] = []
    for lapis in LAPIS_C07:
        temuan.extend(_periksa_lapis(akar, lapis))
    return temuan


def _periksa_lapis(akar: Path, lapis: Lapis) -> list[Temuan]:
    berkas = akar / lapis.berkas
    if not berkas.is_file():
        return [
            Temuan(
                berkas,
                0,
                f"lapis C-07 {lapis.nama} tidak ditemukan — {lapis.akibat_bila_hilang} "
                "(C-07, KL-07)",
            )
        ]

    dibaca = _anggota_status_yang_dibaca(ast.parse(berkas.read_text(encoding="utf-8")))
    hilang = lapis.anggota - dibaca
    if hilang:
        return [
            Temuan(
                berkas,
                0,
                f"lapis C-07 {lapis.nama} tidak lagi membaca "
                f"{NAMA_ENUM_STATUS}.{sorted(hilang)[0]} — "
                f"{lapis.akibat_bila_hilang} (C-07, KL-07)",
            )
        ]
    return []


def _anggota_status_yang_dibaca(pohon: ast.Module) -> set[str]:
    """Anggota `StatusKeberlakuan` yang disebut berkas ini."""
    return {
        simpul.attr
        for simpul in ast.walk(pohon)
        if isinstance(simpul, ast.Attribute)
        and isinstance(simpul.value, ast.Name)
        and simpul.value.id == NAMA_ENUM_STATUS
    }
