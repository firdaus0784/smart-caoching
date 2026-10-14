"""Pemeriksaan basis data UK-02, UK-04, UK-08, UK-09 — T-3 fitur 042, R-03, R-04, P-2 A.

Setiap percobaan: sambungan baru **sebagai peran yang diuji**, transaksi
dibuka, satu pernyataan, transaksi **selalu dibatalkan** — juga bila
pernyataannya berhasil. Pernyataan tulis memakai syarat yang tidak menyentuh
baris, sehingga peladen memeriksa hak tanpa mengubah apa pun. Aman diulang di
produksi (D-09 langkah 5).

Lulus **hanya** pada SQLSTATE yang diharapkan (D-08 Bagian 8 aturan
pelaksanaan). Pernyataan yang berhasil, galat lain, dan sambungan yang gagal
adalah gagal: percobaan yang gagal karena alasan lain tidak membuktikan
apa pun tentang hak.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from perkakas.kepatuhan.hasil import HasilUK, Keadaan, Konteks, gabung

BASIS_DATA: Final = "smart_coaching"
BASIS_DATA_PSEUDONIM: Final = "smart_coaching_pseudonim"
HAK_DITOLAK: Final = "42501"
KUNCI_ASING: Final = "23503"

PERAN_RAG: Final = (
    "peran_penjawaban",
    "peran_pemanggil_llm",
    "peran_penyematan",
    "peran_pengindeks",
)
"""Layanan RAG — D-08 UK-02, C-03."""

PERAN_APLIKASI: Final = (
    "peran_autentikasi",
    "peran_riwayat",
    "peran_pengguna",
    "peran_kurasi",
    "peran_penayangan",
    "peran_telemetri",
    "peran_penilaian",
    "peran_pembaca_sumber",
    "peran_koleksi",
    "peran_analitik",
    "peran_penjawaban",
    "peran_pemanggil_llm",
)
"""Layanan aplikasi dan RAG — D-08 UK-04, C-05; dicocokkan uji dengan
perakitan `perkakas/jalankan_lokal.py`."""


@dataclass(frozen=True)
class Percobaan:
    peran: str
    basis_data: str
    pernyataan: str | None
    """`None`: hanya tersambung."""
    sqlstate: str
    uraian: str


async def coba(konteks: Konteks, p: Percobaan) -> HasilUK:
    """Satu percobaan; rincian berpengenal, tanpa pesan peladen."""
    awal = f"{p.peran}: {p.uraian}"

    def hasil(keadaan: Keadaan, keterangan: str) -> HasilUK:
        return HasilUK("", keadaan, (f"{awal} — {keterangan}",))

    try:
        sambungan = await konteks.buka(p.peran, p.basis_data)
    except Exception as g:
        state = getattr(g, "sqlstate", None)
        if p.pernyataan is None and state == p.sqlstate:
            return hasil(Keadaan.LULUS, f"ditolak {state}")
        return hasil(Keadaan.GAGAL, f"sambungan gagal ({state or type(g).__name__})")
    try:
        if p.pernyataan is None:
            return hasil(Keadaan.GAGAL, f"tersambung, padahal semestinya ditolak {p.sqlstate}")
        transaksi = sambungan.transaction()
        await transaksi.start()
        try:
            await sambungan.execute(p.pernyataan)
            state = None
        except Exception as g:
            state = getattr(g, "sqlstate", None) or type(g).__name__
        finally:
            await transaksi.rollback()
    finally:
        await sambungan.close()
    if state == p.sqlstate:
        return hasil(Keadaan.LULUS, f"ditolak {state}")
    if state is None:
        return hasil(Keadaan.GAGAL, f"berhasil, padahal semestinya ditolak {p.sqlstate}")
    return hasil(Keadaan.GAGAL, f"ditolak {state}, padahal yang diharapkan {p.sqlstate}")


async def _jalankan(konteks: Konteks, kode: str, percobaan: list[Percobaan]) -> HasilUK:
    return gabung(kode, [await coba(konteks, p) for p in percobaan])


_BACA_KARANTINA: Final = (
    ("SELECT 1 FROM karantina.dokumen_sumber LIMIT 0", "baca karantina.dokumen_sumber"),
    ("SELECT 1 FROM karantina.penerimaan LIMIT 0", "baca karantina.penerimaan"),
)

_SISIP_TAYANG: Final = (
    "INSERT INTO kurasi.butir_tayang (id_butir, butir, sumber, id_dokumen_sumber, kategori, "
    "nomor_putusan, tayang_pada) VALUES ('uji-kepatuhan-tanpa-putusan', '{}', '{}', "
    "'uji-kepatuhan', 'K1', -1, now())"
)


async def periksa_uk02(konteks: Konteks) -> HasilUK:
    """Karantina tidak terjangkau layanan RAG — C-03, ADR-06."""
    return await _jalankan(
        konteks,
        "UK-02",
        [
            Percobaan(peran, BASIS_DATA, q, HAK_DITOLAK, uraian)
            for peran in PERAN_RAG
            for q, uraian in _BACA_KARANTINA
        ],
    )


async def periksa_uk04(konteks: Konteks) -> HasilUK:
    """Kunci pseudonim tidak terjangkau layanan aplikasi — C-05, KA-03."""
    return await _jalankan(
        konteks,
        "UK-04",
        [
            Percobaan(
                peran, BASIS_DATA_PSEUDONIM, None, HAK_DITOLAK, "tersambung ke basis data pseudonim"
            )
            for peran in PERAN_APLIKASI
        ],
    )


async def periksa_uk08(konteks: Konteks) -> HasilUK:
    """Butir tidak tayang tanpa putusan kurator — C-06, FR-I03."""
    return await _jalankan(
        konteks,
        "UK-08",
        [
            Percobaan(
                "peran_kurasi",
                BASIS_DATA,
                _SISIP_TAYANG,
                KUNCI_ASING,
                "sisip butir tayang tanpa putusan",
            ),
            Percobaan(
                "peran_penayangan", BASIS_DATA, _SISIP_TAYANG, HAK_DITOLAK, "sisip butir tayang"
            ),
        ],
    )


async def periksa_uk09(konteks: Konteks) -> HasilUK:
    """Pemanggil model tanpa tulis, karantina, kunci pseudonim — NFR-21, C-17."""
    llm = "peran_pemanggil_llm"
    tulis = [
        (
            "INSERT INTO korpus.dokumen_sumber (id, isi) VALUES ('uji-kepatuhan', '{}')",
            "sisip korpus",
        ),
        ("UPDATE korpus.dokumen_sumber SET isi = isi WHERE false", "ubah korpus"),
        ("DELETE FROM korpus.dokumen_sumber WHERE false", "hapus korpus"),
        (
            "INSERT INTO indeks_utama.segmen_teks (id_segmen) VALUES ('uji-kepatuhan')",
            "sisip indeks utama",
        ),
        ("UPDATE indeks_utama.segmen_teks SET teks = teks WHERE false", "ubah indeks utama"),
        ("DELETE FROM indeks_utama.segmen_teks WHERE false", "hapus indeks utama"),
    ]
    return await _jalankan(
        konteks,
        "UK-09",
        [Percobaan(llm, BASIS_DATA, q, HAK_DITOLAK, u) for q, u in tulis]
        + [Percobaan(llm, BASIS_DATA, q, HAK_DITOLAK, u) for q, u in _BACA_KARANTINA]
        + [
            Percobaan(
                llm, BASIS_DATA_PSEUDONIM, None, HAK_DITOLAK, "tersambung ke basis data pseudonim"
            )
        ],
    )
