"""Pemeriksa konsistensi antardokumen — R-01 s.d. R-08, TK-45.

TK-45 menemukan register `docs/D00.md` Bagian 2 tertinggal pada tujuh dokumen
**tanpa satu pun aturan dilanggar**. D-00 Bagian 6 mewajibkan setiap kenaikan
versi dicatat pada riwayat revisi dokumen terkait, dan kewajiban itu dipenuhi
setiap kali. Kewajiban memperbarui register tidak pernah dinyatakan.

Perbaikan yang benar bukan menambah imbauan melainkan menambah pemeriksaan.
Ini AP-01 pada `docs/D04.md` diterapkan pada mekanisme kendali itu sendiri.

**Batas yang dinyatakan terbuka (RQ-03).** Pemeriksa ini memeriksa *bentuk*,
bukan makna. Dari tujuh pertanyaan pemeriksaan pada D-00 Bagian 5, hanya dua
yang terjangkau mesin — angka yang sama muncul berbeda, dan kode yang dirujuk
tanpa wujud. Lima sisanya menuntut penilaian manusia, dan fitur ini tidak
boleh menjadi alasan menunda audit itu.

**Sikap terhadap keragaman bentuk (RQ-01).** Kepala dokumen tidak seragam:
D-01 memakai `| Versi dokumen |`, sisanya `| Versi |`, dan nilainya sering
diikuti keterangan. Bila pengurai ternyata terlalu ketat, **pengurainya yang
dilonggarkan** — bukan dokumennya yang diseragamkan. Menyeragamkan dokumen
demi perkakas adalah ekor menggoyang anjing.
"""

from __future__ import annotations

import re
from pathlib import Path

from perkakas.pemeriksa.ast_aturan import Temuan

BERKAS_REGISTER = "D00.md"
JUDUL_REGISTER = "## 2. Register Dokumen"

# Baris register: | D-xx | Nama | Versi | ...
POLA_REGISTER = re.compile(
    r"^\|\s*(D-\d{2})\s*\|[^|]*\|\s*\**([0-9]+\.[0-9]+)\**\s*\|", re.MULTILINE
)

# Kepala dokumen: menerima "Versi" maupun "Versi dokumen", tebal maupun tidak,
# dengan atau tanpa keterangan di belakang angkanya.
POLA_VERSI_KEPALA = re.compile(
    r"^\|\s*Versi(?:\s+dokumen)?\s*\|\s*\**([0-9]+\.[0-9]+)", re.MULTILINE
)


def baca_register(akar_docs: Path) -> dict[str, str]:
    """Pemetaan kode dokumen ke versi menurut register.

    Galat dibiarkan naik, tidak dikembalikan sebagai pemetaan kosong: pemeriksa
    yang tidak dapat membaca bahannya lalu melapor bersih adalah laporan palsu
    (R-08).
    """
    berkas = akar_docs / BERKAS_REGISTER
    if not berkas.is_file():
        raise FileNotFoundError(f"{BERKAS_REGISTER} tidak ditemukan di {akar_docs}")

    isi = berkas.read_text(encoding="utf-8")
    if JUDUL_REGISTER not in isi:
        raise ValueError(
            f"bagian {JUDUL_REGISTER!r} tidak ditemukan — register adalah tempat "
            "pembaca memeriksa dokumen mana yang berlaku"
        )
    setelah = isi.split(JUDUL_REGISTER, 1)[1].split("\n## ", 1)[0]
    hasil = dict(POLA_REGISTER.findall(setelah))
    if not hasil:
        raise ValueError(f"bagian {JUDUL_REGISTER!r} ada tetapi tidak memuat satu pun baris")
    return hasil


def versi_kepala(berkas: Path) -> str:
    """Versi pada tabel kepala dokumen."""
    cocok = POLA_VERSI_KEPALA.search(berkas.read_text(encoding="utf-8"))
    if not cocok:
        raise ValueError(f"{berkas.name} tidak memuat baris versi yang terbaca")
    return cocok.group(1)


POLA_RIWAYAT = re.compile(r"^\|[^|]*\|\s*\**([0-9]+\.[0-9]+)\**\s*\|", re.MULTILINE)
POLA_BERKAS_DOKUMEN = re.compile(r"^D(\d{2})\.md$")


def _angka(versi: str) -> tuple[int, ...]:
    return tuple(int(b) for b in versi.split("."))


def versi_riwayat_tertinggi(berkas: Path) -> str:
    """Versi tertinggi pada tabel riwayat revisi.

    Diambil yang **tertinggi**, bukan baris pertama maupun terakhir. Urutan
    riwayat tidak seragam antardokumen — sebagian menaik, sebagian menurun —
    dan memaksakan satu urutan berarti menyeragamkan dokumen demi perkakas
    (RQ-01).
    """
    isi = berkas.read_text(encoding="utf-8")
    bagian = re.split(r"^##\s+\d*\.?\s*Riwayat Revisi", isi, maxsplit=1, flags=re.MULTILINE)
    if len(bagian) < 2:
        raise ValueError(f"{berkas.name} tidak memuat bagian Riwayat Revisi")
    versi: list[str] = POLA_RIWAYAT.findall(bagian[1])
    if not versi:
        raise ValueError(f"{berkas.name} memuat bagian Riwayat Revisi tanpa satu pun baris")
    return max(versi, key=_angka)


def periksa_konsistensi_dokumen(akar: Path) -> list[Temuan]:
    """R-01 s.d. R-04. Memeriksa bentuk, bukan makna (RQ-03)."""
    docs = akar / "docs"
    berkas_register = docs / BERKAS_REGISTER

    try:
        register = baca_register(docs)
    except (FileNotFoundError, ValueError) as galat:
        return [Temuan(berkas_register, 0, str(galat))]

    temuan: list[Temuan] = []

    # R-03 dan R-04 — register dan isi direktori saling mengenal.
    pada_cakram = {
        f"D-{cocok.group(1)}": b
        for b in sorted(docs.glob("D*.md"))
        if (cocok := POLA_BERKAS_DOKUMEN.match(b.name))
    }
    for kode in sorted(set(register) - set(pada_cakram)):
        temuan.append(
            Temuan(berkas_register, 0, f"{kode} terdaftar pada register tetapi berkasnya tidak ada")
        )
    for kode in sorted(set(pada_cakram) - set(register)):
        temuan.append(
            Temuan(
                pada_cakram[kode],
                0,
                f"{kode} ada di docs/ tetapi tidak terdaftar pada register — pembaca "
                "yang memeriksa register tidak akan mengetahui dokumen ini",
            )
        )

    # R-01 dan R-02 — versi kepala, register, dan riwayat saling cocok.
    for kode, berkas in sorted(pada_cakram.items()):
        if kode not in register:
            continue
        try:
            kepala = versi_kepala(berkas)
        except ValueError as galat:
            temuan.append(Temuan(berkas, 0, str(galat)))
            continue

        if kepala != register[kode]:
            temuan.append(
                Temuan(
                    berkas,
                    0,
                    f"versi kepala {kepala} berbeda dari register {register[kode]} — "
                    "register adalah tempat pembaca memeriksa dokumen mana yang berlaku",
                )
            )

        try:
            riwayat = versi_riwayat_tertinggi(berkas)
        except ValueError as galat:
            temuan.append(Temuan(berkas, 0, str(galat)))
            continue

        if kepala != riwayat:
            temuan.append(
                Temuan(
                    berkas,
                    0,
                    f"versi kepala {kepala} berbeda dari versi tertinggi pada riwayat "
                    f"revisi {riwayat} — D-00 Bagian 6 mewajibkan setiap kenaikan versi "
                    "dicatat pada riwayat",
                )
            )

    return temuan


# Kode yang punya tempat definisi yang jelas dan dapat dikenali bentuknya.
# TK-xx didefinisikan pada sel pertama tabel temuan; ADR-xx pada judul.
# Kode lain — BT, FR, NFR — tersebar di banyak tempat dengan bentuk yang
# beragam, dan memaksakan pengenalannya akan menghasilkan kebisingan.
POLA_DEFINISI = re.compile(
    r"^\|\s*\**(TK-\d+|ADR-\d+)\**\s*\||^#{2,4}\s+\**(TK-\d+|ADR-\d+)\**\b",
    re.MULTILINE,
)
POLA_RUJUKAN = re.compile(r"\b(TK-\d+|ADR-\d+)\b")


def periksa_kode_menggantung(akar: Path) -> list[Temuan]:
    """R-05 — kode `TK-xx` atau `ADR-xx` dirujuk tanpa punya definisi.

    Definisi dicari di **seluruh** `docs/`, bukan pada dokumen yang merujuk.
    Kutipan sejarah lintas dokumen sah dan lazim — D-00 merujuk TK-07 sebagai
    pelajaran jauh setelah temuannya ditutup (RQ-02).

    Rentang seperti "TK-01 s.d. TK-11" tidak diuraikan: ia merujuk ujungnya,
    dan ujungnya selalu ada. Menguraikan rentang akan menuntut menebak maksud
    penulis, dan tebakan yang keliru menghasilkan kebisingan.
    """
    docs = akar / "docs"
    if not docs.is_dir():
        return []

    berkas_docs = sorted(docs.glob("*.md"))
    terdefinisi: set[str] = set()
    for berkas in berkas_docs:
        for pertama, kedua in POLA_DEFINISI.findall(berkas.read_text(encoding="utf-8")):
            terdefinisi.add(pertama or kedua)

    temuan: list[Temuan] = []
    for berkas in berkas_docs:
        for nomor, baris in enumerate(berkas.read_text(encoding="utf-8").splitlines(), start=1):
            for kode in POLA_RUJUKAN.findall(baris):
                if kode not in terdefinisi:
                    temuan.append(
                        Temuan(
                            berkas,
                            nomor,
                            f"{kode} dirujuk tetapi tidak memiliki definisi di mana pun "
                            "pada docs/ — kode yang dirujuk tanpa wujud adalah uji "
                            "nomor 2 pada D-00 Bagian 5",
                        )
                    )
    return temuan
