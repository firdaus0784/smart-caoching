"""Penilaian kecukupan bukti — R-11, R-12, C-16, D-07 Bagian 4.6.

Tahap 7 pada alur D-07 Bagian 4, dan gerbang terakhir sebelum LLM dipanggil.
Keluarannya menentukan `status_dasar` pada tanggapan (`docs/D14.md` Bagian 4.1)
dan penanda keyakinan PK-04 pada layar (D-05).

## Modul ini sengaja tidak dapat dijalankan hari ini

D-07 Bagian 4.6 memberi **kriteria**, bukan **nilai**: *"Ambang tinggi dan
menengah ditetapkan pada BT-29 melalui kalibrasi terhadap gold set."* Gold set
itu BT-35, bulan 4-5.

Cara paling sunyi melanggar C-16 bukan mengubah angka melainkan menuliskan
angka awal yang tak pernah ditinjau. Ia berjalan pada hari pertama, memberi
hasil yang masuk akal, dan tidak seorang pun kembali kepadanya — sampai angka
itu masuk naskah sebagai ambang yang "dikalibrasi".

Karena itu `AmbangKecukupan` **tidak dapat dibentuk** tanpa `CatatanKalibrasi`.
Bukan gagal saat dijalankan: kegagalan saat jalan akan ditangkap seseorang
dengan nilai bawaan pada pemanggilnya, dan nilai bawaan itu yang kemudian tak
pernah ditinjau. Bentuk yang sama dengan `Kredensial` fitur 002 — *"parameter
berbawaan `None` akan berubah menjadi 'tanpa kredensial berarti tanpa batas'
pada pemanggilan pertama yang lupa mengisinya."*

## Satu penafsiran, dan ia ditulis bukan disembunyikan

D-07 Bagian 4.6 menyebut *"minimal 2 segmen relevan"* tanpa menetapkan apa yang
membuat sebuah segmen relevan. Modul ini membacanya sebagai **skor melampaui
ambang menengah**.

Alasan memilih pembacaan itu ketimbang angka tersendiri: angka tersendiri
adalah ambang ketiga, dan ambang ketiga yang tidak disebut D-07 mana pun adalah
ambang yang disetel agen. Memakai ambang yang BT-29 sudah akan tetapkan tidak
menambah satu pun angka baru.

Penafsirannya tetap wajib dikukuhkan pada BT-29 dan tercatat pada KB-035.

## Batas bawah, bukan batas atas

`tinggi` dan `menengah` wajib positif dan `tinggi` wajib di atas `menengah`.
Batas atas **tidak** ditetapkan, dan itu disengaja: skor RRF tidak berada pada
rentang 0-1 — dengan dua sumber dan k = 60, nilai tertingginya 2/61 ≈ 0,0328.
Membatasi ambang pada 0-1 tidak salah hari ini tetapi menyandera BT-29 pada
skala yang belum diputuskan; kalibrasi boleh saja menormalkan skornya lebih
dulu.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.rag.pengambilan.hibrida import HasilPengambilan
from src.rag.pengambilan.tetapan import JUMLAH_SEGMEN_RELEVAN_MINIMUM

_PROSEDUR_SAH = "BT-29"


class StatusDasar(Enum):
    """Kekuatan dasar rujukan sebuah jawaban — `docs/D14.md` Bagian 4.1.

    Empat nilai persis seperti D-14 menamainya, meski modul ini hanya
    menghasilkan tiga. `DI_LUAR_DOMAIN` adalah keputusan **tahap 1** (D-07
    Bagian 4.1, FR-F13) yang menolak pertanyaan sebelum pengambilan berjalan;
    ia dibangun pada fitur 009.

    Enum berisi tiga nilai akan menuntut penambahan nilai keempat pada fitur
    itu, dan penambahan nilai enum adalah persis yang AG-04 larang.
    """

    KUAT = "kuat"
    TERBATAS = "terbatas"
    TIDAK_DITEMUKAN = "tidak_ditemukan"
    DI_LUAR_DOMAIN = "di_luar_domain"


class CatatanKalibrasi(BaseModel):
    """Asal-usul sebuah ambang — R-12, C-16, C-09.

    Ambang tanpa asal-usul tidak dapat dibedakan dari ambang yang disetel
    seseorang, dan itu persis yang C-16 larang. Kelima bidangnya wajib.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tanggal: date
    gold_set: str = Field(min_length=1)
    """Penanda *gold set* beserta versinya — D-08 Bagian 6, BT-35.

    D-08 menetapkan *gold set* dibekukan sebelum kalibrasi dan tidak diubah
    setelahnya; tanpa penandanya, dua kalibrasi atas dua gold set berbeda
    tercatat sama.
    """
    jumlah_pertanyaan: int = Field(gt=0)
    pemutus: str = Field(min_length=1)
    prosedur: str = Field(min_length=1)
    """Prosedur yang melahirkan angkanya — wajib menyebut BT-29.

    Bidang untai bebas akan diisi "penyetelan manual" dan tetap lolos, dan
    catatan yang mencatat pelanggaran tetap catatan yang lolos. C-16 berbunyi
    "di luar prosedur kalibrasi D-07 BT-29"; penyebutannya karena itu ditegakkan.
    """

    @field_validator("gold_set", "pemutus", "prosedur")
    @classmethod
    def _tidak_hanya_spasi(cls, nilai: str) -> str:
        bersih = nilai.strip()
        if not bersih:
            raise ValueError("bidang asal-usul kalibrasi tidak boleh kosong")
        return bersih

    @field_validator("prosedur")
    @classmethod
    def _prosedur_menyebut_bt29(cls, nilai: str) -> str:
        if _PROSEDUR_SAH not in nilai:
            raise ValueError(
                f"prosedur kalibrasi wajib menyebut {_PROSEDUR_SAH} — C-16 melarang "
                "ambang disetel di luar prosedur kalibrasi D-07 BT-29"
            )
        return nilai


class AmbangKecukupan(BaseModel):
    """Ambang tinggi dan menengah, beserta kalibrasi yang melahirkannya.

    **Tidak dapat dibentuk tanpa `kalibrasi`** — lihat uraian modul.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tinggi: float = Field(gt=0.0)
    menengah: float = Field(gt=0.0)
    kalibrasi: CatatanKalibrasi

    @model_validator(mode="after")
    def _tinggi_di_atas_menengah(self) -> AmbangKecukupan:
        """Terbalik, seluruh jawaban menjadi "rujukan kuat" — termasuk yang
        seharusnya ditolak. Kekeliruannya tidak menghasilkan galat, hanya
        sistem yang jauh lebih percaya diri."""
        if self.tinggi <= self.menengah:
            raise ValueError(
                "ambang tinggi wajib di atas ambang menengah; terbalik, seluruh "
                "jawaban menjadi rujukan kuat tanpa satu galat pun"
            )
        return self


class PenilaianKecukupan:
    """Tahap 7 D-07 Bagian 4.6.

    `ambang` tepat sesudah `self` dan tanpa nilai bawaan, mengikuti
    `PenyimpanDasar` fitur 002: *"Menempatkannya di akhir daftar parameter
    membuatnya terbaca sebagai renungan belakangan."*
    """

    def __init__(self, ambang: AmbangKecukupan) -> None:
        self._ambang = ambang

    def jumlah_relevan(self, hasil: HasilPengambilan) -> int:
        """Segmen yang skornya melampaui ambang menengah.

        Penafsiran atas "segmen relevan" D-07 Bagian 4.6 — lihat uraian modul.
        """
        return sum(1 for s in hasil.segmen if s.skor > self._ambang.menengah)

    def nilai(self, hasil: HasilPengambilan, *, segmen_resmi: frozenset[str]) -> StatusDasar:
        """Nilai kecukupan bukti menurut ketiga baris D-07 Bagian 4.6.

        `segmen_resmi` diserahkan pemanggil, bukan disimpulkan dari segmennya.
        Jenis sumber tinggal pada `src/ingest/`, dan `AGENTS.md` tidak memberi
        `rag` tepi ke sana — menyimpulkannya di sini akan menciptakan tepi
        ketiga tanpa keputusan gerbang, persis yang KB-034 pertanyaan 4 hindari.
        """
        if not hasil.segmen:
            return StatusDasar.TIDAK_DITEMUKAN

        tertinggi = max(s.skor for s in hasil.segmen)
        if tertinggi <= self._ambang.menengah:
            return StatusDasar.TIDAK_DITEMUKAN

        cukup_banyak = self.jumlah_relevan(hasil) >= JUMLAH_SEGMEN_RELEVAN_MINIMUM
        ada_resmi = any(s.id_segmen in segmen_resmi for s in hasil.segmen)
        if tertinggi > self._ambang.tinggi and cukup_banyak and ada_resmi:
            return StatusDasar.KUAT
        return StatusDasar.TERBATAS
