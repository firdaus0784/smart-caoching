"""Penghitungan konsep dan relasi yang sah — R-03, R-06, R-07, D-06 Bagian 11.2.

**Modul ini tentang cara melapor, bukan cara menghitung.** Menghitung anggota
himpunan tidak menuntut satu berkas; yang menuntutnya adalah menolak
melaporkan satu angka.

D-06 Bagian 11.2 menyatakan sebabnya: *"Tanpa aturan ini, target 500 dapat
dipenuhi dengan konsep yang tidak berguna, dan angka MK-06 menjadi angka tanpa
isi."* MK-06 adalah syarat Definisi Selesai dengan tenggat bulan 8, dan
menambah baris tabel jauh lebih cepat daripada menyusun definisi.

## Dua angka, selalu bersama

Laporan yang hanya menyebut "512 konsep" tidak dapat dibedakan antara 512
konsep berdefinisi dan 512 baris tabel. Melaporkan keduanya membuat selisihnya
terbaca — dan **selisih itulah yang memberi tahu berapa banyak pekerjaan yang
tersisa**, satu-satunya angka yang berguna bagi orang yang menjadwalkan.

Karena itu `HasilHitung` tidak memiliki bidang bernama `jumlah` saja. Bidang
tunggal adalah bidang yang pembacanya anggap sebagai yang ia harapkan, dan
yang ia harapkan adalah yang lebih besar.

Bentuk yang sama dengan `terperiksa` fitur 015, `terhitung` fitur 003,
`bendera_terkumpul` fitur 016, dan kedua rerata bernama fitur 004.

## Tiga syarat sah, dan ketiganya dari D-06 Bagian 11.2

| Syarat | Aturan D-06 |
|---|---|
| Definisi terisi | "Konsep tanpa definisi tidak dihitung" |
| Terhubung dokumen sumber | FR-E03, ditegakkan tipe pada `skema.py` |
| Sumber terkurasi | "Konsep dari bahan karantina tidak sah — konsekuensi C-03" |

Syarat kedua tidak diperiksa di sini: `Konsep` tidak dapat dibentuk tanpa
dokumen sumber, sehingga memeriksanya ulang berarti dua tempat yang menegakkan
aturan yang sama — dan yang kedua akan lupa diperbarui.

**Relasi tidak punya syarat "berdefinisi".** D-06 Bagian 11.2 menuntutnya
berjenis salah satu dari tujuh dan membawa dokumen rujukannya; keduanya
ditegakkan tipe. Yang tersisa: relasi yang **kedua ujungnya konsep sah**.
Relasi menuju konsep tanpa definisi bukan relasi yang dapat diperiksa siapa
pun, dan menghitungnya menaikkan angka MK-06 lewat pintu belakang.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.rag.ontologi.skema import Konsep, Ontologi, Relasi


class HasilHitung(BaseModel):
    """Jumlah sah **dan** jumlah mentah — lihat uraian modul.

    Tidak ada bidang bernama `jumlah` saja. Yang membaca satu angka membacanya
    sebagai yang ia harapkan.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    konsep_sah: int = Field(ge=0)
    konsep_mentah: int = Field(ge=0)
    relasi_sah: int = Field(ge=0)
    relasi_mentah: int = Field(ge=0)

    @property
    def konsep_tanpa_definisi(self) -> int:
        """Selisih yang memberi tahu berapa banyak pekerjaan yang tersisa."""
        return self.konsep_mentah - self.konsep_sah

    @property
    def relasi_tak_sah(self) -> int:
        return self.relasi_mentah - self.relasi_sah


def konsep_sah(konsep: Konsep) -> bool:
    """Tiga syarat D-06 Bagian 11.2; yang ketiga ditegakkan tipe.

    `sumber_terkurasi` adalah C-03 yang merambat: konsep dari bahan karantina
    membawa isinya ke ontologi, dan ontologi diekspor untuk HKI dan publikasi.
    """
    return konsep.berdefinisi and konsep.sumber_terkurasi


def relasi_sah(relasi: Relasi, pengenal_sah: frozenset[str]) -> bool:
    """Relasi sah bila **kedua ujungnya** konsep sah.

    Memeriksa satu ujung meloloskan relasi yang menuju konsep tanpa definisi,
    dan relasi seperti itu menaikkan angka MK-06 lewat pintu belakang.
    """
    return relasi.konsep_asal in pengenal_sah and relasi.konsep_tujuan in pengenal_sah


def hitung_ontologi(ontologi: Ontologi) -> HasilHitung:
    """Dua angka bagi masing-masing — R-07, D-06 Bagian 11.2."""
    sah = frozenset(k.id_konsep for k in ontologi.konsep if konsep_sah(k))
    return HasilHitung(
        konsep_sah=len(sah),
        konsep_mentah=len(ontologi.konsep),
        relasi_sah=sum(1 for r in ontologi.relasi if relasi_sah(r, sah)),
        relasi_mentah=len(ontologi.relasi),
    )
