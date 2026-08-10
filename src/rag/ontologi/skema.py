"""Skema ontologi — R-01 s.d. R-06, FR-E02, FR-E03, D-06 Bagian 11.2.

D-06 Bagian 11.2 menyatakan alasan seluruh berkas ini dalam satu kalimat:
*"Tanpa aturan ini, target 500 dapat dipenuhi dengan konsep yang tidak
berguna, dan angka MK-06 menjadi angka tanpa isi."*

Godaannya nyata dan tidak perlu niat buruk: MK-06 adalah syarat Definisi
Selesai dengan tenggat bulan 8, dan menambah baris tabel jauh lebih cepat
daripada menyusun definisi.

## Konsep tanpa definisi terbentuk, tetapi tidak terhitung

Pembedaan yang menentukan. Konsep yang masih disusun definisinya adalah
keadaan kerja yang wajar — menolaknya akan membuat pekerjaan penyusunan
mustahil. Yang tidak boleh adalah ia ikut terhitung pada angka MK-06, dan itu
urusan `hitung.py`, bukan tipe ini.

## Relasi membawa dokumen rujukannya sendiri

R-04, dan menghemat bidang ini terasa rapi. Akibatnya: relasi "bertentangan
dengan" antara dua konsep yang masing-masing bersumber dokumen berbeda tidak
punya dokumen yang menyatakan **pertentangannya**. Klaim relasi menjadi klaim
tanpa sumber — persis yang C-01 larang pada jawaban, dan ontologi ini diekspor
untuk publikasi.

## Sumber terkurasi, bukan karantina

R-06, dan ini C-03 yang merambat ke tempat yang tidak terduga. Konsep yang
diturunkan dari dokumen karantina membawa isinya ke ontologi, dan ontologi
diekspor untuk HKI dan publikasi. Dokumen yang belum diverifikasi
anonimisasinya lolos ke berkas yang dilampirkan naskah.

`sumber_terkurasi` wajib tanpa nilai bawaan — bentuk yang sama dengan
`indeks_tujuan` fitur 006 dan `status_pra_anotasi` fitur 003.

Ketujuh jenis relasi dimiliki FR-E02, bidangnya dimiliki D-04 Bagian 7.3.
AG-04 melarang agen mengubah daftar nilai enum; berkas ini mewujudkannya.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JenisRelasi(Enum):
    """Tujuh jenis relasi FR-E02, dan hanya ketujuhnya.

    Jenis kedelapan menuntut D-01 diubah lebih dulu. Untai bebas di sini
    berarti "mengatur", "Mengatur", dan "meregulasi" hidup berdampingan, lalu
    penelusuran graf menemukan sebagian saja.
    """

    MENGATUR = "mengatur"
    BAGIAN_DARI = "bagian_dari"
    PRASYARAT = "prasyarat"
    BERDAMPAK_PADA = "berdampak_pada"
    DIUKUR_OLEH = "diukur_oleh"
    BERTANGGUNG_JAWAB_ATAS = "bertanggung_jawab_atas"
    BERTENTANGAN_DENGAN = "bertentangan_dengan"


class Konsep(BaseModel):
    """Satu konsep ontologi — D-04 Bagian 7.3 tabel `konsep`.

    `definisi` boleh kosong; ia keadaan kerja yang wajar. Yang menentukan
    apakah ia terhitung adalah `hitung.py`, bukan tipe ini.

    `id_dokumen_rujukan` **tidak boleh** kosong: FR-E03 menuntut setiap konsep
    terhubung ke sekurang-kurangnya satu dokumen sumber, dan konsep tanpa
    sumber adalah konsep yang tidak dapat diperiksa siapa pun.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_konsep: str = Field(min_length=1)
    label: str = Field(min_length=1)
    definisi: str = ""
    id_dokumen_rujukan: frozenset[str] = Field(min_length=1)
    sumber_terkurasi: bool

    @property
    def berdefinisi(self) -> bool:
        """Definisi yang hanya berisi spasi bukan definisi."""
        return bool(self.definisi.strip())


class Relasi(BaseModel):
    """Satu relasi berarah antara dua konsep — D-04 Bagian 7.3 tabel `relasi`.

    Membawa dokumen rujukannya **sendiri** (R-04) — lihat uraian modul.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_relasi: str = Field(min_length=1)
    konsep_asal: str = Field(min_length=1)
    konsep_tujuan: str = Field(min_length=1)
    jenis: JenisRelasi
    id_dokumen_rujukan: frozenset[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _tidak_menunjuk_dirinya(self) -> Relasi:
        """Relasi dari sebuah konsep ke dirinya sendiri tidak menerangkan apa
        pun, dan pada penelusuran graf ia menjadi putaran tak berujung."""
        if self.konsep_asal == self.konsep_tujuan:
            raise ValueError(
                f"relasi {self.id_relasi!r} menunjuk konsep {self.konsep_asal!r} "
                "ke dirinya sendiri — ia tidak menerangkan apa pun, dan pada "
                "penelusuran graf menjadi putaran tak berujung"
            )
        return self


class GalatOntologi(Exception):
    """Ontologi tidak dapat dibentuk sebagaimana D-06 Bagian 11.2 tuntut."""


class Ontologi(BaseModel):
    """Kumpulan konsep dan relasi yang saling terhubung — R-05.

    Relasi diperiksa menunjuk konsep yang ada **saat ontologi dibentuk**, bukan
    saat ditelusuri. Relasi menggantung yang baru ketahuan saat penelusuran
    menghasilkan graf yang sebagian jalurnya buntu — dan buntu itu terbaca
    sebagai "tidak ada hubungan", bukan sebagai cacat data.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    konsep: tuple[Konsep, ...]
    relasi: tuple[Relasi, ...]

    @model_validator(mode="after")
    def _relasi_menunjuk_konsep_yang_ada(self) -> Ontologi:
        pengenal = {k.id_konsep for k in self.konsep}
        if len(pengenal) != len(self.konsep):
            berulang = sorted(
                {
                    k.id_konsep
                    for k in self.konsep
                    if [x.id_konsep for x in self.konsep].count(k.id_konsep) > 1
                }
            )
            raise ValueError(
                f"konsep tercatat lebih dari sekali: {', '.join(berulang)} — "
                "pengulangan menggandakan hitungan MK-06 tanpa menambah satu "
                "konsep pun"
            )
        for r in self.relasi:
            hilang = [c for c in (r.konsep_asal, r.konsep_tujuan) if c not in pengenal]
            if hilang:
                raise ValueError(
                    f"relasi {r.id_relasi!r} menunjuk konsep yang tidak ada: "
                    f"{', '.join(hilang)} — relasi menggantung menghasilkan graf "
                    "yang sebagian jalurnya buntu, dan buntu itu terbaca sebagai "
                    "'tidak ada hubungan' bukan sebagai cacat data"
                )
        return self
