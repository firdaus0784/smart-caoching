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
