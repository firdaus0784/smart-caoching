"""Pemetaan jenis sumber ke peringkat kepercayaan — R-07, FR-B09, KD-08.

Pemiliknya `docs/D13.md` Bagian 6, bukan D-01. `docs/D00.md` Bagian 3
menetapkan "tingkat kepercayaan asal segmen" dimiliki D-13, dan FR-B09 sendiri
menutup kalimatnya dengan "Dasar: D-13 Bagian 6". Ketika keduanya berbeda, D-13
yang berlaku.

**Perbedaannya nyata.** D-13 menempatkan artikel berlisensi terbuka dari
penerbit terverifikasi pada T2, bersama data resmi agregat. Daftar empat nama
dalam kurung pada FR-B09 — "regulasi resmi, data resmi, dokumen sekolah
terverifikasi, konten web terkurasi" — tidak menyediakan tempat baginya, dan
pembacaan yang wajar akan menaruhnya pada "konten web terkurasi" yaitu T4.
Akibatnya seluruh kanal K-C pada `docs/D06.md` kehilangan gunanya: artikel
jurnal tidak akan pernah dapat menopang klaim. Karena itu lima jenis di sini,
bukan empat.

Peringkat yang ditetapkan di sini **belum sah** sampai gerbang verifikasi
dilewati (R-07a). Yang menahannya bukan bidang kedua melainkan area simpan
dokumennya — selama di karantina, segmennya tidak terjangkau kredensial jalur
penjawaban sama sekali.
"""

from __future__ import annotations

from enum import Enum

from src.llm.tipe import Peringkat


class JenisSumber(Enum):
    """Asal sebuah dokumen, menurut `docs/D13.md` Bagian 6 kolom Asal."""

    REGULASI_RESMI = "regulasi_resmi"
    DATA_RESMI_AGREGAT = "data_resmi_agregat"
    ARTIKEL_LISENSI_TERBUKA = "artikel_lisensi_terbuka"
    DOKUMEN_SEKOLAH = "dokumen_sekolah"
    LAPORAN_LEMBAGA = "laporan_lembaga"


_PERINGKAT: dict[JenisSumber, Peringkat] = {
    JenisSumber.REGULASI_RESMI: Peringkat.T1,
    JenisSumber.DATA_RESMI_AGREGAT: Peringkat.T2,
    JenisSumber.ARTIKEL_LISENSI_TERBUKA: Peringkat.T2,
    JenisSumber.DOKUMEN_SEKOLAH: Peringkat.T3,
    JenisSumber.LAPORAN_LEMBAGA: Peringkat.T4,
}


def peringkat_bagi(jenis: JenisSumber) -> Peringkat:
    """Peringkat kepercayaan bagi sebuah jenis sumber.

    Jenis yang belum punya peringkat menghasilkan `KeyError`, bukan T4
    diam-diam. Memberi peringkat terendah pada yang tidak dikenal terdengar
    berhati-hati, tetapi ia menyembunyikan kekeliruan konfigurasi dan
    menghasilkan dokumen yang diam-diam tidak pernah dapat menopang klaim.
    """
    return _PERINGKAT[jenis]
