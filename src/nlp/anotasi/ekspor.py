"""Ekspor korpus — R-09 s.d. R-12, FR-C06, D-03 Bagian 15.

Berkas yang dihasilkan modul ini **dilampirkan naskah dan dibaca orang di luar
tim**. Itu yang menentukan seluruh keputusan di dalamnya: yang di sini tidak
dapat dijelaskan lewat percakapan, sebab yang membacanya tidak ada di ruangan.

## Tiga hal yang dijaga, dan hanya yang pertama terbaca dari kebutuhannya

**Nama bidang sama persis dengan D-03 Bagian 15.** Bidang yang namanya
bergeser menghasilkan berkas yang terbaca wajar dan tidak dapat dipakai
perkakas mana pun tanpa disunting.

**Bendera yang tidak terkumpul ditulis `null`, bukan `[]`.** `[]` menyatakan
korpus sudah diperiksa dan bersih dari `bocor_pii` — data pribadi yang lolos
anonimisasi. Pembedaan itu dibawa sepanjang jalan dari `impor_ls` sampai ke
sini justru karena di sinilah ia paling mudah hilang: penulis JSON yang wajar
akan mengubah `None` menjadi daftar kosong tanpa berpikir.

**Dokumen beranotasi ganda tidak diekspor sebelum diadjudikasi.** D-03
menetapkan satu baris mewakili satu dokumen, sedangkan dokumen beranotasi
ganda membawa dua putusan yang mungkin berbeda. Memilih salah satunya berarti
memilih berdasarkan urutan penyimpanan Label Studio, bukan berdasarkan
adjudikasi — dan pilihan itu tidak meninggalkan jejak apa pun pada berkasnya.

Ia **dilaporkan**, tidak dibuang diam-diam. Korpus yang diam-diam kehilangan
dokumen beranotasi ganda kehilangan justru dokumen yang paling banyak
dikerjakan orang, dan selisihnya baru terlihat ketika seseorang membandingkan
dua angka yang tidak pernah dilaporkan bersama.

## Modul ini tidak menulis berkas, dan itu bukan pilihan gaya

`src/nlp/` berada pada jalur penjawaban menurut `perkakas/pemeriksa/
tanpa_kemampuan_bertindak.py`, dan **C-17 melarang akses tulis dari sana**.
Bentuk pertama modul ini menulis berkas sendiri; pemeriksa C-17 menjatuhkannya
pada `make check`, dan yang diperbaiki rancangannya — bukan pemeriksanya.

Yang dikembalikan karena itu adalah **barisnya**, dan penulisannya pekerjaan
pemanggil di luar `src/`. Batas itu berharga melampaui kepatuhan formal:
modul yang tidak dapat menulis tidak dapat menimpa korpus yang sudah dibekukan
karena satu pemanggilan yang keliru.

## Yang tidak dibawa Label Studio dan diminta dari pemanggil

`sumber` dan `tanggal_anotasi`. Keduanya wajib; ketiadaannya menggagalkan
ekspor alih-alih menghasilkan objek kosong. Korpus yang menyatakan asal
dokumen sebagai `{}` menyatakan sesuatu yang tidak diketahui siapa pun.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from src.nlp.anotasi.impor_ls import DokumenTeranotasi, HasilImpor


class GalatEkspor(Exception):
    """Korpus tidak dapat diekspor tanpa kehilangan atau mengarang keterangan."""


@dataclass(frozen=True)
class SumberDokumen:
    """Asal dokumen — D-03 Bagian 15 bidang `sumber`.

    Tidak dibawa Label Studio. Diberikan pemanggil dari kanal masuknya
    dokumen, dan itu satu-satunya tempat keterangan ini benar-benar diketahui.
    """

    jenis: str
    tahun: int
    instansi_penerbit: str


@dataclass(frozen=True)
class HasilEksporJsonl:
    """Baris yang siap ditulis, dan **apa yang tidak ada di dalamnya**.

    Bagian kedua yang membuat tipe ini ada. Jumlah baris dapat dihitung siapa
    pun; yang tidak dapat dihitung dari berkasnya adalah dokumen yang tidak ada
    di sana.

    `baris` sengaja berupa untai yang sudah jadi, bukan objek yang menunggu
    diserialkan. Serialisasi yang dilakukan pemanggil adalah serialisasi yang
    dapat berbeda dari yang diuji di sini.
    """

    baris: tuple[str, ...]
    tertunda_adjudikasi: tuple[str, ...]

    def tulis(self, berkas: Path) -> None:
        """**Sengaja tidak disediakan** — lihat uraian modul.

        Dituliskan sebagai metode yang menolak supaya penambahannya kelak
        menjadi keputusan, bukan kelalaian.
        """
        raise NotImplementedError(
            "modul ini tidak menulis berkas: C-17 melarang akses tulis dari "
            "jalur penjawaban, dan src/nlp berada di sana. Tulis `baris` dari "
            "pemanggil di luar src/"
        )


def ekspor_jsonl(
    hasil: HasilImpor,
    *,
    sumber: dict[str, SumberDokumen],
    tanggal_anotasi: date,
) -> HasilEksporJsonl:
    """Susun korpus sebagai baris JSONL — R-09, R-12, D-03 Bagian 15.

    Satu baris satu dokumen. Dokumen beranotasi ganda **tidak disusun** dan
    namanya dikembalikan; ia menunggu adjudikasi.

    Tidak menulis berkas — lihat uraian modul.
    """
    baris: list[str] = []
    tertunda: list[str] = []

    for dokumen in hasil.dokumen:
        if dokumen.anotasi_ganda:
            tertunda.append(dokumen.id_dokumen)
            continue
        baris.append(
            json.dumps(
                _baris(dokumen, hasil, sumber, tanggal_anotasi),
                ensure_ascii=False,
                sort_keys=True,
            )
        )

    return HasilEksporJsonl(baris=tuple(baris), tertunda_adjudikasi=tuple(tertunda))


def _baris(
    dokumen: DokumenTeranotasi,
    hasil: HasilImpor,
    sumber: dict[str, SumberDokumen],
    tanggal_anotasi: date,
) -> dict[str, object]:
    if dokumen.id_dokumen not in sumber:
        raise GalatEkspor(
            f"dokumen {dokumen.id_dokumen!r} tidak punya keterangan sumber — "
            "asal dokumen tidak dibawa Label Studio, dan korpus yang "
            "menyatakannya sebagai objek kosong menyatakan sesuatu yang tidak "
            "diketahui siapa pun (D-03 Bagian 15)"
        )

    putusan = dokumen.putusan[0] if dokumen.putusan else None
    anotator = putusan.id_anotator if putusan else _anotator_rentang(dokumen)

    return {
        "doc_id": dokumen.id_dokumen,
        "sumber": asdict(sumber[dokumen.id_dokumen]),
        "teks": dokumen.teks,
        "entitas": [
            {"mulai": r.mulai, "akhir": r.akhir, "label": r.label.value, "teks": r.teks_rentang}
            for r in dokumen.rentang
        ],
        "kategori_utama": putusan.kategori_utama.value if putusan else None,
        "kategori_sekunder": (
            putusan.kategori_sekunder.value if putusan and putusan.kategori_sekunder else None
        ),
        "anotator": anotator,
        "anotasi_ganda": dokumen.anotasi_ganda,
        # `None` bukan `[]` — lihat uraian modul. Ini baris yang paling mudah
        # "dirapikan" menjadi daftar kosong oleh pembaca berikutnya.
        "bendera": None if dokumen.bendera is None else sorted(b.value for b in dokumen.bendera),
        "versi_skema": str(hasil.versi_skema),
        "tanggal_anotasi": tanggal_anotasi.isoformat(),
    }


def _anotator_rentang(dokumen: DokumenTeranotasi) -> str | None:
    """Kode anotator dari rentangnya, bagi dokumen tanpa putusan kategori.

    Dokumen yang hanya dianotasi entitasnya tanpa kategori adalah keadaan yang
    sah — D-03 memisahkan kedua tugas — dan bidang `anotator` tetap wajib ada.
    """
    return dokumen.rentang[0].id_anotator if dokumen.rentang else None
