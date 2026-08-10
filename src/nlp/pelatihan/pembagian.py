"""Pembagian data latih, validasi, dan uji — R-01 s.d. R-06, FR-D07, D-08 Bagian 4.2.

**Pembagian dilakukan pada tingkat dokumen, bukan segmen.** D-08 menyebut
alasannya dengan kalimatnya sendiri: bila dua segmen dari dokumen yang sama
tersebar ke himpunan latih dan uji, model akan tampak lebih baik daripada
kenyataannya karena telah melihat konteks yang sangat mirip — "kekeliruan yang
mudah terjadi dan sulit terdeteksi setelahnya".

Yang membuatnya sulit terdeteksi: **tidak ada satu pun angka yang terlihat
janggal.** F1 naik, dan kenaikan F1 adalah hal yang semua orang harapkan.
Karena itu penjagaannya bukan kehati-hatian melainkan tipe — `PembagianData`
hanya menerima id dokumen, dan pembagian tingkat segmen tidak dapat dilakukan
tanpa mengubah tipenya.

**Dibekukan sebelum pelatihan pertama** (D-08 Bagian 4.2). Modul ini karena
itu dibangun mendahului model yang memakainya (KB-028): membangunnya belakangan
berarti pelatihan pertama berjalan atas pembagian yang disusun sambil lalu.

Porsi dimiliki D-08, bukan berkas ini. Yang ada di sini salinan yang dijaga
uji — `tests/nlp/test_pembagian_data.py` membaca `docs/D08.md` sungguhan dan
membandingkannya, sehingga salinan yang menyimpang menjatuhkan gerbang.
"""

from __future__ import annotations

import hashlib
import random

from pydantic import BaseModel, ConfigDict, Field, model_validator

PORSI: dict[str, float] = {"latih": 0.70, "validasi": 0.15, "uji": 0.15}
"""Porsi ketiga himpunan — D-08 Bagian 4.2, satu-satunya tempat angkanya ada.

Himpunan uji **dibuka satu kali** saat evaluasi akhir (D-08), dan validasi
dipakai memilih konfigurasi serta menghentikan pelatihan. Ketiganya bukan tiga
nama bagi hal yang sama.
"""


class PembagianData(BaseModel):
    """Ketiga himpunan sebagai daftar id dokumen yang beku.

    `frozenset` bukan `list`: urutan tidak berarti apa-apa di sini, dan daftar
    berurutan mengundang seseorang mengandalkan urutannya — lalu pembagian
    yang sama dengan urutan berbeda terbaca sebagai pembagian yang lain.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_pembagian: str = Field(min_length=1)
    latih: frozenset[str] = Field(min_length=1)
    validasi: frozenset[str] = Field(min_length=1)
    uji: frozenset[str] = Field(min_length=1)
    seed: int
    versi_korpus: str = Field(min_length=1)

    @model_validator(mode="after")
    def _tanpa_irisan(self) -> PembagianData:
        """Ketiga pasangan diperiksa, bukan hanya latih lawan uji.

        Kebocoran validasi ke uji lebih halus dan sama merusaknya: konfigurasi
        dipilih pada dokumen yang kemudian dipakai menilai hasilnya.
        """
        pasangan = (
            ("latih", self.latih, "validasi", self.validasi),
            ("latih", self.latih, "uji", self.uji),
            ("validasi", self.validasi, "uji", self.uji),
        )
        for nama_a, a, nama_b, b in pasangan:
            iris = sorted(a & b)
            if iris:
                raise ValueError(
                    f"dokumen berada pada {nama_a} sekaligus {nama_b}: {', '.join(iris)} — "
                    "model yang melihat dokumen yang sama pada dua himpunan tampak "
                    "lebih baik daripada kenyataannya, dan kekeliruannya tidak "
                    "meninggalkan jejak pada angka mana pun (D-08 Bagian 4.2)"
                )
        return self

    @property
    def jumlah_dokumen(self) -> int:
        return len(self.latih) + len(self.validasi) + len(self.uji)

    @property
    def sidik(self) -> str:
        """Sidik susunannya — R-04. Lihat `_sidik`."""
        return _sidik(self)


JUMLAH_DOKUMEN_MINIMUM = 20
"""Korpus terkecil yang masih menghasilkan ketiga himpunan tidak kosong.

Bukan ambang mutu dan bukan angka D-08 — ia akibat aritmetika porsinya:
15% dari 20 adalah 3, dan di bawah itu himpunan validasi atau uji jatuh ke
satu dokumen atau nol. Himpunan uji berisi satu dokumen menghasilkan F1 yang
hanya dapat bernilai 0 atau 1, dan angka seperti itu tidak menerangkan apa pun.

Ditulis di sini alih-alih dihitung agar galatnya dapat menyebut angkanya.
"""


class GalatPembagian(Exception):
    """Pembagian tidak dapat dibentuk atau tidak cocok dengan yang beku."""


def _sidik(bagi: PembagianData) -> str:
    """Sidik susunan pembagian — R-04.

    Dihitung dari **isi ketiga himpunan**, bukan dari jumlahnya. Sidik atas
    jumlah tidak berubah ketika satu dokumen bertukar tempat dengan dokumen
    lain, dan pertukaran itu persis yang membuat dua laporan tidak dapat
    dibandingkan.

    Id diurutkan lebih dulu: `frozenset` tidak punya urutan, dan sidik yang
    bergantung pada urutan penelusuran akan berbeda antar-jalannya program.
    """
    bahan = "|".join(
        ",".join(sorted(himpunan)) for himpunan in (bagi.latih, bagi.validasi, bagi.uji)
    )
    return "sha256:" + hashlib.sha256(bahan.encode("utf-8")).hexdigest()


def buat_pembagian(
    id_dokumen: list[str],
    *,
    seed: int,
    versi_korpus: str,
    id_pembagian: str,
) -> PembagianData:
    """Bagi korpus menurut porsi D-08, **deterministik terhadap seed** — R-05.

    Masukan diurutkan sebelum diacak. Korpus yang sama dengan urutan berbeda
    adalah korpus yang sama, dan tanpa pengurutan ini pembagian bergantung pada
    urutan berkas pada cakram — urutan yang berubah antar-mesin tanpa seorang
    pun mengubah apa pun.

    Sisa pembulatan jatuh ke himpunan latih. Korpus anotasi adalah artefak yang
    paling mahal dihasilkan proyek ini; satu dokumen yang hilang karena
    pembulatan adalah pekerjaan anotator yang dibuang tanpa jejak.
    """
    if len(set(id_dokumen)) != len(id_dokumen):
        berulang = sorted({d for d in id_dokumen if id_dokumen.count(d) > 1})
        raise GalatPembagian(
            f"dokumen tercatat lebih dari sekali pada korpus: {', '.join(berulang)} — "
            "ia akan masuk dua himpunan sekaligus, kebocoran yang sama dengan "
            "yang D-08 Bagian 4.2 peringatkan"
        )
    if len(id_dokumen) < JUMLAH_DOKUMEN_MINIMUM:
        raise GalatPembagian(
            f"korpus memuat {len(id_dokumen)} dokumen, kurang dari "
            f"{JUMLAH_DOKUMEN_MINIMUM} yang diperlukan agar ketiga himpunan "
            "tidak kosong — himpunan uji berisi satu dokumen menghasilkan F1 "
            "yang hanya dapat bernilai 0 atau 1"
        )

    acak = random.Random(seed)
    urut = sorted(id_dokumen)
    acak.shuffle(urut)

    n = len(urut)
    n_validasi = int(n * PORSI["validasi"])
    n_uji = int(n * PORSI["uji"])
    n_latih = n - n_validasi - n_uji

    return PembagianData(
        id_pembagian=id_pembagian,
        latih=frozenset(urut[:n_latih]),
        validasi=frozenset(urut[n_latih : n_latih + n_validasi]),
        uji=frozenset(urut[n_latih + n_validasi :]),
        seed=seed,
        versi_korpus=versi_korpus,
    )


def pastikan_beku(beku: PembagianData, baru: PembagianData) -> None:
    """Pembagian ulang wajib menghasilkan susunan yang sama — R-04.

    Membagi ulang bukan pelanggaran; membagi ulang **dengan hasil berbeda**
    yang pelanggaran. Penjagaan yang menolak pemeriksaan ulang yang sah akan
    dilucuti seseorang, dan yang tersisa sesudahnya bukan penjagaan mana pun.

    D-08 Bagian 4.2: pembagian dibekukan sebelum pelatihan pertama. Sesudah itu
    susunan yang berubah berarti laporan lama dan laporan baru dihitung atas
    himpunan uji yang berlainan — dan keduanya tercatat dengan nama yang sama.
    """
    if beku.sidik != baru.sidik:
        raise GalatPembagian(
            f"pembagian {beku.id_pembagian!r} sudah beku dengan sidik {beku.sidik}, "
            f"sedangkan pembagian baru bersidik {baru.sidik} — susunan yang berubah "
            "membuat laporan lama dan laporan baru dihitung atas himpunan uji yang "
            "berlainan, keduanya tercatat dengan nama yang sama (D-08 Bagian 4.2)"
        )
