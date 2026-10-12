"""Pemotongan dokumen korpus menjadi segmen — T-4 fitur 038, D-07 Bagian 3.2, FR-F11.

Fungsi murni: teks masuk, potongan keluar, tanpa basis data. Indeks tujuan,
lisensi, dan pengenal ditetapkan pengindeksan (`pengindeksan.py`), bukan di
sini.

## Aturannya milik D-07 Bagian 3.2

| Aspek | Ketentuan D-07 | Di sini |
|---|---|---|
| Ukuran sasaran | 300 s.d. 500 kata | `BATAS_KATA` batas atas; `SASARAN_KATA` tidak dipaksakan |
| Tumpang tindih | 50 s.d. 80 kata | `TUMPANG_TINDIH_KATA` = 60, hanya pada jendela |
| Batas alami | pasal, ayat, butir, subjudul | pasal, lalu ayat; paragraf bagi dokumen tanpa pasal |
| Segmen pendek | pasal pendek berdiri sendiri | tidak digabung |

Uji membaca angka itu dari tabel D-07, bukan dari berkas ini (C-16). Tiga
tafsiran tercatat pada KB-267: 500 dibaca sebagai batas atas; tumpang tindih
hanya diberikan saat batas alami tidak ada — memotong di batas ayat tidak
memotong ketentuan; 60 adalah titik di dalam rentang D-07.

## Penanda bagian

Wajib (FR-F11): `Pasal 7`, `Pasal 7 ayat (1)`, `Pembukaan`, `Bagian 3`. Ayat
yang dikumpulkan berpenanda rentang `(1)`, tanda pisah, `(2)` — `_PISAH`.
Jendela teks tanpa batas alami berakhiran `, potongan i dari n`, sehingga
sitasi menunjuk satu jendela dan pembaca sumber fitur 032 — yang membaca
segmen menurut penanda yang sama persis — tidak menampilkan tumpang tindih dua
kali.

## Yang dikenali, dan yang tidak

Baris utuh `Pasal N` memulai satuan; rujukan "sebagaimana dimaksud dalam
Pasal 2" di tengah kalimat tidak. Baris `BAB`, `Bagian Kesatu`, `Paragraf 1`
adalah judul konteks: ikut ke awal pasal sesudahnya. Baris huruf besar
`PENJELASAN` dan `LAMPIRAN` membuka bagian berawalan, agar `Pasal 1` pada
penjelasan tidak berpenanda sama dengan `Pasal 1` batang tubuh. Tabel, gambar,
dan tata letak tidak dikenali — di luar cakupan fitur 038.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Final

SASARAN_KATA: Final = 300
"""Batas bawah ukuran sasaran — D-07 Bagian 3.2. Tidak dipaksakan pada pasal
pendek: D-07 sendiri menetapkan pasal pendek berdiri sendiri."""

BATAS_KATA: Final = 500
"""Batas atas ukuran sasaran — D-07 Bagian 3.2. Tidak satu segmen pun
melampauinya."""

TUMPANG_TINDIH_KATA: Final = 60
"""Di dalam rentang 50 s.d. 80 kata D-07 Bagian 3.2 — titik, bukan angka baru."""

_PISAH: Final = "\u2013"
"""Tanda pisah rentang ayat, sama dengan penulisan rentang pada D-07."""

_PASAL = re.compile(r"^\s*Pasal\s+(\d+[A-Z]?)\s*$")
_KONTEKS = re.compile(
    r"^\s*(BAB\s+[IVXLCDM]+|Bagian\s+Ke[a-z]+|Paragraf\s+\d+)\s*$",
)
_AYAT = re.compile(r"^\s*\((\d+[a-z]?)\)")
_BAGIAN_BERAWALAN: Final[dict[str, str]] = {"PENJELASAN": "Penjelasan", "LAMPIRAN": "Lampiran"}


@dataclass(frozen=True)
class Potongan:
    """Satu calon segmen: penanda bagian dan teksnya."""

    penanda: str
    teks: str


@dataclass
class _Satuan:
    nama: str
    berpasal: bool
    baris: list[str] = field(default_factory=list)


def _kata(teks: str) -> int:
    return len(teks.split())


def _awalan_bagian(baris: str) -> str | None:
    bersih = baris.strip()
    if not bersih or bersih != bersih.upper():
        return None
    kata_pertama = bersih.split()[0]
    return _BAGIAN_BERAWALAN.get(kata_pertama)


def _satuan(baris_dokumen: list[str]) -> list[_Satuan]:
    """Satuan alami berurutan. Judul konteks ditahan sampai pasal berikutnya."""
    berpasal = any(_PASAL.match(b) for b in baris_dokumen)
    hasil: list[_Satuan] = []
    awalan = ""
    kini: _Satuan | None = None
    konteks: list[str] = []

    def nama_bebas() -> str:
        return awalan or ("Pembukaan" if berpasal else "")

    for baris in baris_dokumen:
        bagian = _awalan_bagian(baris)
        if bagian is not None:
            awalan = bagian
            kini = _Satuan(nama_bebas(), berpasal=False, baris=[*konteks, baris])
            konteks = []
            hasil.append(kini)
            continue
        cocok = _PASAL.match(baris)
        if cocok:
            nama = f"Pasal {cocok.group(1)}"
            kini = _Satuan(
                f"{awalan} {nama}" if awalan else nama, berpasal=True, baris=[*konteks, baris]
            )
            konteks = []
            hasil.append(kini)
            continue
        if berpasal and (_KONTEKS.match(baris) or konteks):
            konteks.append(baris)
            continue
        if kini is None:
            kini = _Satuan(nama_bebas(), berpasal=False)
            hasil.append(kini)
        kini.baris.append(baris)
    if konteks:
        # Judul tanpa pasal sesudahnya; `konteks` hanya terisi pada dokumen
        # berpasal, sehingga satuan pasal sebelumnya selalu ada.
        hasil[-1].baris.extend(konteks)
    return hasil


def _jendela(teks: str, penanda: str) -> list[Potongan]:
    """Teks tanpa batas alami: jendela sama besar, paling banyak `BATAS_KATA`,
    bertumpang tindih sedikitnya `TUMPANG_TINDIH_KATA`. Jendela terakhir
    berakhir tepat di ujung teks."""
    kata = teks.split()
    if len(kata) <= BATAS_KATA:
        return [Potongan(penanda, teks)]
    langkah_maks = BATAS_KATA - TUMPANG_TINDIH_KATA
    n = math.ceil((len(kata) - TUMPANG_TINDIH_KATA) / langkah_maks)
    langkah = (len(kata) - TUMPANG_TINDIH_KATA) / n
    ukuran = min(BATAS_KATA, math.ceil(langkah) + TUMPANG_TINDIH_KATA)
    mulai = [round(i * langkah) for i in range(n - 1)] + [len(kata) - ukuran]
    return [
        Potongan(f"{penanda}, potongan {i} dari {n}", " ".join(kata[m : m + ukuran]))
        for i, m in enumerate(mulai, start=1)
    ]


def _kumpulkan(kelompok: list[tuple[str, list[str]]]) -> list[tuple[list[str], list[str]]]:
    """Kelompok (label, baris) berurutan dikumpulkan tanpa melampaui
    `BATAS_KATA`. Kelompok yang sendirian melampauinya tetap satu kumpulan,
    lalu dipecah jendela oleh pemanggil. `kelompok` tidak kosong."""
    hasil: list[tuple[list[str], list[str]]] = []
    label: list[str] = []
    baris: list[str] = []
    for nama, isi in kelompok:
        jumlah = sum(_kata(b) for b in isi)
        if baris and sum(_kata(b) for b in baris) + jumlah > BATAS_KATA:
            hasil.append((label, baris))
            label, baris = [], []
        label.append(nama)
        baris.extend(isi)
    hasil.append((label, baris))
    return hasil


def _potong_pasal(satuan: _Satuan) -> list[Potongan]:
    teks = "\n".join(satuan.baris)
    if _kata(teks) <= BATAS_KATA:
        return [Potongan(satuan.nama, teks)]
    kelompok: list[tuple[str, list[str]]] = []
    kepala: list[str] = []
    for baris in satuan.baris:
        cocok = _AYAT.match(baris)
        if cocok:
            kelompok.append((cocok.group(1), [*kepala, baris]))
            kepala = []
        elif kelompok:
            kelompok[-1][1].append(baris)
        else:
            kepala.append(baris)
    if not kelompok:
        return _jendela(teks, satuan.nama)
    hasil: list[Potongan] = []
    for label, isi in _kumpulkan(kelompok):
        rentang = f"({label[0]})" if len(label) == 1 else f"({label[0]}){_PISAH}({label[-1]})"
        hasil.extend(_jendela("\n".join(isi), f"{satuan.nama} ayat {rentang}"))
    return hasil


def _potong_bebas(satuan: _Satuan) -> list[Potongan]:
    kumpulan = _kumpulkan([("", [b]) for b in satuan.baris])
    hasil: list[Potongan] = []
    for k, (_, isi) in enumerate(kumpulan, start=1):
        if not satuan.nama:
            penanda = f"Bagian {k}"
        elif len(kumpulan) == 1:
            penanda = satuan.nama
        else:
            penanda = f"{satuan.nama}, bagian {k}"
        hasil.extend(_jendela("\n".join(isi), penanda))
    return hasil


def potong(teks: str) -> list[Potongan]:
    """Potongan berurutan dokumen itu. Teks hampa menghasilkan daftar kosong.

    Deterministik: teks yang sama menghasilkan potongan yang sama (R-06).
    Baris hampa dibuang; baris adalah paragraf hasil ekstraksi fitur 015.
    """
    baris = [b.strip() for b in teks.splitlines() if b.strip()]
    hasil: list[Potongan] = []
    for satuan in _satuan(baris):
        hasil.extend(_potong_pasal(satuan) if satuan.berpasal else _potong_bebas(satuan))
    return hasil
