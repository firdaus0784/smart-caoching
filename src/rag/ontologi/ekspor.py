"""Ekspor ontologi sebagai JSON-LD — R-08, R-09, FR-E05, D-01 Bagian 12.2.

Berkas yang dihasilkan modul ini **dilampirkan pada pendaftaran HKI dan
naskah publikasi**. Yang membacanya tidak punya akses ke `docs/`, tidak dapat
bertanya, dan tidak ada di ruangan — itu yang menentukan seluruh keputusan di
dalamnya.

## Konteks menamai ketujuh jenis relasi

Ekspor yang menamai relasi dengan untai bebas menuntut pembacanya menebak
artinya. Konteks JSON-LD membuat berkasnya menerangkan dirinya sendiri:
`bertanggung_jawab_atas` bukan sekadar untai melainkan istilah yang terdaftar.

## Hanya yang sah diekspor

R-09. Konsep tanpa definisi tidak terhitung pada MK-06 (B-1); mengekspornya
akan membuat berkas yang dilampirkan naskah memuat lebih banyak simpul
daripada angka yang dilaporkan naskah itu sendiri. Selisih antara keduanya
adalah pertanyaan pertama yang diajukan penelaah.

## Ontologi kosong ditolak

Berkas JSON-LD berisi nol simpul terbaca seperti ekspor yang berjalan dan
tidak menemukan apa-apa — dan itu tidak dapat dibedakan dari ekspor yang gagal
diam. Bentuk yang sama dengan penolakan metrik atas nol contoh fitur 004.

## Tidak menulis berkas

`src/rag` berada pada jalur penjawaban dan C-17 melarang akses tulis dari
sana — pelajaran B-1 fitur 016. Yang dikembalikan untainya; penulisan
pekerjaan pemanggil di luar `src/`.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.rag.ontologi.hitung import HasilHitung, hitung_ontologi, konsep_sah, relasi_sah
from src.rag.ontologi.skema import JenisRelasi, Ontologi

KATA_KUNCI = "https://smart-coaching.upi.edu/ontologi#"
"""Awalan istilah ontologi ini.

Bukan alamat yang harus dapat dibuka: JSON-LD memakai IRI sebagai pengenal,
bukan sebagai tautan. Menamainya dengan alamat proyek membuat istilah kita
tidak bertabrakan dengan istilah ontologi lain pada berkas gabungan.
"""


class GalatEksporOntologi(Exception):
    """Ontologi tidak dapat diekspor tanpa menyesatkan pembacanya."""


def _konteks() -> dict[str, object]:
    """Konteks JSON-LD yang menamai ketujuh jenis relasi — R-08.

    Disusun dari enum, bukan ditulis tangan. Daftar yang ditulis tangan akan
    berbeda dari enumnya ketika FR-E02 berubah, dan yang berbeda adalah yang
    tidak diperbarui.
    """
    konteks: dict[str, object] = {
        "@vocab": KATA_KUNCI,
        "label": "http://www.w3.org/2000/01/rdf-schema#label",
        "definisi": "http://www.w3.org/2004/02/skos/core#definition",
        "dokumen_rujukan": {"@id": KATA_KUNCI + "dokumenRujukan", "@container": "@set"},
    }
    for jenis in JenisRelasi:
        konteks[jenis.value] = {"@id": KATA_KUNCI + jenis.value, "@type": "@id"}
    return konteks


def ekspor_jsonld(ontologi: Ontologi, *, versi: str) -> str:
    """Susun ontologi sah sebagai untai JSON-LD — R-08, R-09.

    `versi` wajib: berkas yang dilampirkan naskah tanpa versi tidak dapat
    dicocokkan dengan angka yang dilaporkan naskah itu, dan pencocokan itu
    pertanyaan pertama penelaah.

    Tidak menulis berkas — lihat uraian modul.
    """
    if not versi.strip():
        raise GalatEksporOntologi(
            "versi ontologi wajib diisi — berkas yang dilampirkan naskah tanpa "
            "versi tidak dapat dicocokkan dengan angka yang dilaporkan naskah itu"
        )

    hitungan = hitung_ontologi(ontologi)
    if hitungan.konsep_sah == 0:
        raise GalatEksporOntologi(
            f"ontologi tidak memuat satu pun konsep sah dari {hitungan.konsep_mentah} "
            "yang ada — berkas berisi nol simpul terbaca seperti ekspor yang "
            "berjalan dan tidak menemukan apa-apa, dan itu tidak dapat dibedakan "
            "dari ekspor yang gagal diam"
        )

    sah = frozenset(k.id_konsep for k in ontologi.konsep if konsep_sah(k))
    simpul: list[dict[str, object]] = []
    for k in ontologi.konsep:
        if k.id_konsep not in sah:
            continue
        isi: dict[str, object] = {
            "@id": KATA_KUNCI + k.id_konsep,
            "@type": KATA_KUNCI + "Konsep",
            "label": k.label,
            "definisi": k.definisi,
            "dokumen_rujukan": sorted(k.id_dokumen_rujukan),
        }
        for r in ontologi.relasi:
            if r.konsep_asal == k.id_konsep and relasi_sah(r, sah):
                isi.setdefault(r.jenis.value, [])
                tujuan = isi[r.jenis.value]
                assert isinstance(tujuan, list)
                tujuan.append(KATA_KUNCI + r.konsep_tujuan)
        simpul.append(isi)

    berkas: dict[str, object] = {
        "@context": _konteks(),
        "versi": versi,
        "jumlah_konsep_sah": hitungan.konsep_sah,
        "jumlah_relasi_sah": hitungan.relasi_sah,
        "@graph": simpul,
    }
    return json.dumps(berkas, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def tulis(berkas: Path) -> None:
    """**Sengaja tidak disediakan** — C-17, lihat uraian modul.

    Dituliskan sebagai fungsi yang menolak supaya penambahannya kelak menjadi
    keputusan, bukan kelalaian.
    """
    raise NotImplementedError(
        "modul ini tidak menulis berkas: C-17 melarang akses tulis dari jalur "
        "penjawaban, dan src/rag berada di sana"
    )


def ringkas(ontologi: Ontologi) -> HasilHitung:
    """Hitungan yang menyertai ekspor, bagi pencatatannya (R-10)."""
    return hitung_ontologi(ontologi)
