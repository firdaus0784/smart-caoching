"""Pendeteksi data pribadi berpola tetap — R-09, R-10, R-11, R-12, FR-B04.

Enam pengenal, dan hanya enam: NIK, NIP, NISN, NUPTK, nomor telepon, nomor
rekening. Keenamnya berformat baku dan berdigit tetap, sehingga `re` pada
pustaka baku memadai dan tidak ada ketergantungan yang ditambahkan.

**Yang TIDAK dideteksi modul ini, dengan contohnya:**

- **Nama perorangan** — "Dra. Siti Aminah memimpin rapat" lolos utuh
- **Alamat** — "Jalan Mawar Nomor 12, Sumedang" lolos utuh
- **Nama sekolah sebagai penunjuk orang** — "kepala SDN 1 Sukamaju" menunjuk
  satu orang tertentu bagi siapa pun yang mengenal daerah itu
- **Tanggal lahir** — "lahir 12 Maret 1978" bersama jabatan sudah cukup
  mengenali seseorang
- **Nomor yang ditulis terurai** — "tiga dua satu satu nol satu" lolos

Keduanya yang pertama menuntut pengenalan entitas bernama, dan model NER
adalah **fitur 004 pada Bulan 4** sedangkan modul ini Bulan 3. Kekurangan itu
tercatat pada `docs/D01.md` sebagai BT-70 dan diputus pada KB-017 — bukan
kelalaian, melainkan urutan pembangunan yang disadari.

**Menyatakannya di sini bukan formalitas.** Verifikator yang mengira nama
sudah tersamarkan otomatis akan memeriksa lebih longgar, dan pendeteksi yang
terbaca lebih tebal daripada kenyataannya lebih buruk daripada tidak ada
pendeteksi sama sekali. Yang menahan pada Bulan 3 adalah FR-B05 — verifikasi
manusia — beserta gerbang karantina fitur 002.

**Modul ini melapor, tidak memutuskan** (R-10). Kelayakan dokumen diputuskan
gerbang fitur 002. Pendeteksi yang juga memutuskan akan menggoda siapa pun
melonggarkan ambangnya ketika antrean menumpuk.

**Nilai yang dideteksi tidak pernah dibawa keluar** (R-11). `Temuan` sengaja
tidak memiliki bidang untuk isinya — hanya jenis dan letaknya. Pendeteksi data
pribadi yang menyalin temuannya ke log adalah kebalikan persis dari maksudnya,
dan itu cacat yang paling mudah dibuat pada modul semacam ini. Yang tidak
dapat dinyatakan tidak dapat bocor; bentuk yang sama sudah dipakai
`src/penyimpanan/catatan_akses.py`.

**Jenis adalah perkiraan terbaik; deteksinya yang menjadi jaminan.** Beberapa
pengenal tidak dapat dibedakan dari bentuknya saja — NISN berdigit 10 dan
nomor rekening berdigit 10 sampai 15 bertindih penuh pada digit kesepuluh.
Karena itu label yang mendahului nomor dibaca lebih dulu bila ada, dan bentuk
dipakai hanya ketika tidak ada label.

Ketidaktepatan jenis **tidak** merugikan: keenamnya sama-sama wajib
disamarkan, dan yang dipakai penyamaran adalah rentangnya. Yang merugikan
adalah nomor yang tidak terdeteksi sama sekali, dan itulah yang dijaga.

Daftar pola adalah **nilai awal, bukan hasil kalibrasi**. Penyetelannya
mengikuti BT-29 (C-16).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

JENIS: tuple[str, ...] = ("nik", "nip", "nisn", "nuptk", "telepon", "rekening")
"""Enam jenis yang dideteksi. Bukan untai bebas — ejaan yang berbeda pada tiap
pemakainya membuat penyaringan menurut jenis tidak dapat diandalkan."""

_TELEPON = re.compile(r"(?<![\d+])(?:\+62|62|0)8[1-9](?:[\s.-]?\d){7,10}(?!\d)")
"""Nomor telepon Indonesia. Dikenali dari bentuknya karena awalannya khas dan
tidak bertindih dengan pengenal lain."""

_DERET = re.compile(r"(?<!\d)\d{10,18}(?!\d)")
"""Deret digit panjang apa pun. Jenisnya ditentukan label dan panjangnya."""

_LABEL = re.compile(r"\b(NIK|NIP|NISN|NUPTK|rekening|rek)\b[\s.:]*$", re.IGNORECASE)
"""Label yang mendahului nomor, dibaca dari teks tepat sebelumnya.

Dokumen manajerial hampir selalu menuliskannya — "NIP 1999...", "Rekening
1234..." — dan label itu keterangan yang jauh lebih dapat dipercaya daripada
panjang digit.
"""

_MENURUT_PANJANG: dict[int, str] = {16: "nik", 18: "nip", 10: "rekening"}
"""Perkiraan ketika tidak ada label.

Digit kesepuluh diberikan ke `rekening`, bukan `nisn`, karena rentang
rekening lebih lebar dan menebak yang lebih lebar lebih sering benar. Pilihan
ini tidak mengubah apa yang disamarkan.
"""


@dataclass(frozen=True)
class Temuan:
    """Satu kemunculan data pribadi: **jenis dan letaknya, bukan nilainya**.

    Sengaja tanpa bidang untuk isi yang terdeteksi (R-11). Penyamaran
    dilakukan pemanggil dengan memotong teks aslinya memakai rentang ini.

    `mulai` dan `akhir` adalah **indeks karakter** (C-10), sama dengan seluruh
    rentang lain pada sistem ini.
    """

    jenis: str
    mulai: int
    akhir: int


def periksa_data_pribadi(teks: str) -> list[Temuan]:
    """Seluruh kemunculan enam pengenal berpola pada `teks`.

    Mengembalikan **seluruhnya**, bukan yang pertama saja: melaporkan satu
    temuan menyembunyikan luasnya, dan verifikator memutuskan dari luasnya.

    Rentang yang bertumpang tindih diselesaikan menurut urutan `_POLA` —
    yang lebih khusus menang. Tanpa itu, satu NIP dilaporkan dua kali dengan
    dua jenis yang berbeda dan verifikator melihat angka yang tidak cocok.
    """
    temuan: list[Temuan] = []
    diklaim: set[int] = set()

    for cocok in _TELEPON.finditer(teks):
        diklaim.update(range(cocok.start(), cocok.end()))
        temuan.append(Temuan(jenis="telepon", mulai=cocok.start(), akhir=cocok.end()))

    for cocok in _DERET.finditer(teks):
        if diklaim.intersection(range(cocok.start(), cocok.end())):
            continue
        jenis = _jenis_deret(teks, cocok)
        if jenis is None:
            continue
        diklaim.update(range(cocok.start(), cocok.end()))
        temuan.append(Temuan(jenis=jenis, mulai=cocok.start(), akhir=cocok.end()))

    return sorted(temuan, key=lambda t: (t.mulai, t.jenis))


def _jenis_deret(teks: str, cocok: re.Match[str]) -> str | None:
    """Label lebih dulu, panjang kemudian.

    Mengembalikan `None` bila deretnya tidak dapat dijelaskan keduanya —
    lebih baik tidak melaporkan daripada melaporkan jenis yang dikarang, sebab
    temuan yang tidak dapat dipertanggungjawabkan membuat verifikator berhenti
    mempercayai seluruh laporan.
    """
    label = _LABEL.search(teks[: cocok.start()])
    if label:
        nama = label.group(1).lower()
        return "rekening" if nama in {"rekening", "rek"} else nama
    return _MENURUT_PANJANG.get(cocok.end() - cocok.start())
