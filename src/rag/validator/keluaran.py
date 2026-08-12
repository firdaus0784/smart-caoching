"""Kontrak keluaran model dan segmen rujukan — R-01, D-07 Bagian 5.1, D-14 4.1.

Bentuk yang divalidasi. D-07 Bagian 5.1 menyatakan alasan bentuk terstruktur
dalam satu kalimat: *"Jawaban berupa prosa bebas tidak dapat diperiksa secara
mesin, sehingga MK-07 (cakupan sitasi 100%) hanya akan menjadi klaim tanpa
bukti."*

## VS-01 sebagai bentuk, bukan sebagai pemeriksaan

`Klaim` tidak dapat dibentuk tanpa sekurangnya satu `id_segmen`. VS-01 tetap
dijalankan validator — sebab keluaran model tiba sebagai data, bukan sebagai
objek yang sudah tervalidasi — tetapi klaim yang lolos ke dalam sistem tidak
akan pernah kosong rujukannya.

Bentuk yang sama dengan `penanda_bagian` fitur 007: yang dapat ditegakkan tipe
tidak diserahkan kepada pemeriksaan saat jalan.

## Bidang mengikuti D-14, tanpa tambahan

`docs/D14.md` Bagian 4.1 adalah kontrak `/api/v1/tanya`, dan AG-03 melarang
agen menambah bidang padanya. Modul ini memodelkan **keluaran model**, yang
menjadi bahan tanggapan itu — bukan tanggapannya sendiri, yang fitur 009 susun.

Satu bidang D-14 sengaja **tidak** ada di sini:
`klaim[].peringkat_kepercayaan`. D-14 Bagian 4.1 menyatakan artinya pada klaim
campuran adalah **keputusan BT-64, bukan keputusan pelaksana**. Memodelkannya
sekarang berarti memilih salah satu dari tiga arti yang mengubah apa yang
dilihat kepala sekolah. VS-08 dirumuskan agar tidak membutuhkannya.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.kamus.segmen import IndeksTujuan, Peringkat, StatusKeberlakuan


class SegmenRujukan(BaseModel):
    """Segmen yang benar-benar diambil, sebagaimana validator melihatnya.

    Ia bukan `SegmenTerindeks` fitur 006 dan bukan `Kandidat` fitur 007:
    validator memerlukan sifat yang keduanya tidak bawa bersamaan — peringkat
    kepercayaan (VS-08), indeks asal (VS-04), status keberlakuan (VS-06), dan
    tautan sumber (VS-09).

    Menyatukannya di sini alih-alih memperluas salah satu dari keduanya
    disengaja: `SegmenTerindeks` adalah bidang penyimpanan D-14 Bagian 5, dan
    menambahkan `tautan` ke sana akan membuat lapisan penyimpanan memikul
    keperluan penyajian.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_segmen: str = Field(min_length=1)
    peringkat_kepercayaan: Peringkat
    indeks_asal: IndeksTujuan
    status_keberlakuan: StatusKeberlakuan
    tautan: str | None = None
    """Tautan sumber dari **metadata dokumen**, bukan dari keluaran model.

    VS-09 memeriksa tautan pada keluaran terhadap himpunan ini. Daftar ranah
    tepercaya ditolak sebagai gantinya: ranah tepercaya adalah daftar yang
    bertambah, dan yang bertambah akan ditambahi.
    """


class Klaim(BaseModel):
    """Satu klaim faktual beserta segmen pendukungnya — D-07 Bagian 5.1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_klaim: str = Field(min_length=1)
    teks: str = Field(min_length=1)
    id_segmen: tuple[str, ...] = Field(min_length=1)
    """Sekurangnya satu — VS-01 ditegakkan tipe.

    `tuple`, bukan `list`: klaim beku yang memuat daftar yang dapat ditambah
    anggotanya tidak beku dalam arti yang berguna (`kredensial.py` fitur 002).
    """


class KeluaranModel(BaseModel):
    """Keluaran terstruktur LLM sebelum validasi — D-07 Bagian 5.1.

    Belum tervalidasi, dan namanya menyatakannya. Yang tervalidasi bernama
    `JawabanTervalidasi` dan hanya dapat dibentuk validator.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    ringkasan_tindakan: tuple[str, ...] = ()
    """Maksimal tiga butir (D-07 Bagian 5.1).

    Boleh kosong: keadaan `tidak_ditemukan` dan `di_luar_domain` memakai bentuk
    yang sama dengan ringkasan dan klaim kosong (D-14 Bagian 4.1), dan
    keseragaman itu yang membuat layar D-05 menampilkannya sebagai jawaban sah,
    bukan pesan galat.
    """
    penjelasan: str = ""
    klaim: tuple[Klaim, ...] = ()
    catatan_keberlakuan: str = ""
    """Diisi bila ada segmen berstatus `diubah` (FR-F14, D-07 Bagian 5.1)."""
    tautan_disebut: tuple[str, ...] = ()
    """Tautan yang muncul pada keluaran model, diperiksa VS-09.

    Dipisahkan dari prosa agar pemeriksaannya tidak bergantung pada penguraian
    teks bebas. Penguraian teks bebas yang meleset satu kasus menghasilkan
    tautan yang lolos tanpa diperiksa.
    """
