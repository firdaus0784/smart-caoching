"""Penjaga keselarasan kontrak web — T-3 fitur 027, R-19, C-20.

Bentuk tanggapan `/api/v1/tanya` ditulis dua kali: model pydantic pada
`src/rag/jawaban/tanggapan.py` dan antarmuka TypeScript pada
`web/src/kontrak.ts`. TypeScript tidak dapat mengimpor model pydantic, maka
penulisan ganda itu disengaja — tetapi dua daftar yang menggambarkan hal yang
sama akan hanyut. Pemeriksa ini membuat hanyutnya menjatuhkan V-03, alih-alih
muncul sebagai layar kosong di lapangan.

Yang dibandingkan dua hal:

- **Nama bidang** tiap antarmuka terhadap `model_fields` model sebangun, dua
  arah. Bidang yang berganti nama muncul sebagai satu yang hilang dan satu
  yang lebih — keduanya dilaporkan.
- **Nilai enum** `StatusDasar` dan `StatusKeberlakuan` terhadap enum Python
  (AG-04).

Tipe bidang tidak dibandingkan. Penerjemahan tipe pydantic ke TypeScript
adalah pekerjaan pengurai, dan pengurai yang setengah jadi melaporkan bersih
pada kasus yang tidak dikenalinya. Sisi tipe dijaga pada saat berjalan oleh
`apakahTanggapan` di `web/src/klien.ts`, yang diuji `vitest` pada V-01.

## Batas yang diakui terbuka

Pemeriksa membaca bentuk yang ditulis `kontrak.ts`: `export interface Nama {`,
satu bidang `readonly` per baris, dan `export type Nama = "a" | "b";`.
Antarmuka yang ditulis dengan bentuk lain tidak dikenali — dan dilaporkan
**tidak ditemukan**, bukan dilewati.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

from pydantic import BaseModel
from src.api.percakapan import Giliran
from src.kamus.segmen import StatusKeberlakuan
from src.rag.jawaban.tanggapan import (
    BacaanLanjutan,
    KlaimTampil,
    Sitasi,
    StatusDasar,
    Tanggapan,
    Versi,
)

from perkakas.pemeriksa.ast_aturan import Temuan

BERKAS_KONTRAK = Path("web") / "src" / "kontrak.ts"

MODEL: tuple[type[BaseModel], ...] = (
    Tanggapan,
    Versi,
    KlaimTampil,
    Sitasi,
    BacaanLanjutan,
    # Fitur 028: bentuk riwayat D-14 Bagian 4.3 — giliran tanpa tanggapan (C-07).
    Giliran,
)
ENUM: tuple[type[Enum], ...] = (StatusDasar, StatusKeberlakuan)

_ANTARMUKA = re.compile(r"^export interface (\w+) \{\n(.*?)^\}", re.MULTILINE | re.DOTALL)
_BIDANG = re.compile(r"^\s*readonly\s+(\w+)\??\s*:", re.MULTILINE)
_TIPE = re.compile(r"^export type (\w+) =(.*?);", re.MULTILINE | re.DOTALL)
_LITERAL = re.compile(r'"([^"]*)"')


def periksa_kontrak_web(akar: Path) -> list[Temuan]:
    """Nama bidang dan nilai enum `kontrak.ts` wajib sama dengan modelnya."""
    web = akar / "web"
    if not (web / "package.json").is_file():
        return []
    berkas = akar / BERKAS_KONTRAK
    if not berkas.is_file():
        return [
            Temuan(
                BERKAS_KONTRAK,
                0,
                "web/src/kontrak.ts tidak ada — layar tidak memiliki bentuk tanggapan "
                "yang dapat dibandingkan dengan model (C-20)",
            )
        ]
    isi = berkas.read_text(encoding="utf-8")
    antarmuka = {m.group(1): set(_BIDANG.findall(m.group(2))) for m in _ANTARMUKA.finditer(isi)}
    tipe = {m.group(1): set(_LITERAL.findall(m.group(2))) for m in _TIPE.finditer(isi)}

    temuan: list[Temuan] = []
    for model in MODEL:
        temuan.extend(
            _banding(model.__name__, "bidang", set(model.model_fields), antarmuka, "interface")
        )
    for enum in ENUM:
        nilai = {str(anggota.value) for anggota in enum}
        temuan.extend(_banding(enum.__name__, "nilai", nilai, tipe, "type"))
    return temuan


def _banding(
    nama: str, jenis: str, diharapkan: set[str], terbaca: dict[str, set[str]], kata: str
) -> list[Temuan]:
    if nama not in terbaca:
        return [
            Temuan(
                BERKAS_KONTRAK,
                0,
                f"`export {kata} {nama}` tidak ditemukan pada kontrak.ts — "
                "bentuk yang tidak dikenali dilaporkan, bukan dilewati",
            )
        ]
    ada = terbaca[nama]
    temuan: list[Temuan] = []
    if hilang := sorted(diharapkan - ada):
        temuan.append(
            Temuan(
                BERKAS_KONTRAK,
                0,
                f"{nama}: {jenis} {', '.join(map(repr, hilang))} ada pada model tetapi "
                "hilang dari kontrak.ts",
            )
        )
    if lebih := sorted(ada - diharapkan):
        temuan.append(
            Temuan(
                BERKAS_KONTRAK,
                0,
                f"{nama}: {jenis} {', '.join(map(repr, lebih))} ada pada kontrak.ts tetapi "
                "tidak ada pada model — C-20 melarang bentuk tanggapan bertambah",
            )
        )
    return temuan
