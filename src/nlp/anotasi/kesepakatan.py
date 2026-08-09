"""Kesepakatan antar-anotator — R-07 s.d. R-09, FR-C02, D-03 Bagian 11.

**Dua ukuran bagi dua jenis tugas, dan itu bukan pilihan gaya.**

| Jenis tugas | Ukuran | Ambang D-03 |
|---|---|---|
| Klasifikasi dokumen | Cohen's Kappa | ≥ 0,70 |
| Anotasi rentang entitas | F1 berpasangan, pencocokan tepat | ≥ 0,75 |
| Anotasi rentang entitas | F1 berpasangan, pencocokan longgar | ≥ 0,85 |

**Cohen's Kappa tidak dipakai bagi anotasi rentang.** D-03 Bagian 11
menolaknya dengan dua rujukan literatur — Artstein & Poesio (2008) mengenai
batas penerapan koefisien kesepakatan, dan Hripcsak & Rothschild (2005)
mengenai kesesuaian F-measure ketika jumlah kesempatan negatif tidak
terdefinisi (D-11 Bagian 3.2).

Alasannya satu kalimat: Kappa memerlukan satuan analisis yang tetap dan
disepakati sebelumnya, sedangkan pada anotasi rentang **anotator menentukan
sendiri di mana rentang dimulai dan berakhir**. Jumlah "kesempatan" karena itu
tidak terdefinisi, peluang kesepakatan acak tidak dapat dihitung, dan
memaksakan Kappa menghasilkan angka yang terlihat meyakinkan tetapi tidak
bermakna.

Yang menegakkannya bukan uraian ini melainkan **tanda tangan**: `kappa_kategori`
menerima `PutusanKategori` dan tidak akan menerima `RentangEntitas`.

**Hasil yang belum terhitung bukan angka.** `HasilKesepakatan.nilai` bernilai
`None` ketika tidak ada yang dapat dibandingkan — bukan 0,0, bukan 1,0.
Keduanya angka yang dapat dibaca sebagai hasil, dan yang dapat dibaca sebagai
hasil akan disalin ke naskah sebagai bukti mutu. Bentuk yang sama dengan
`HasilSistem` fitur 015 dan dengan "belum dapat diperiksa" pada
`make compliance`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.nlp.anotasi.rentang import PutusanKategori
from src.nlp.anotasi.skema import KategoriMasalah


class HasilKesepakatan(BaseModel):
    """Satu angka kesepakatan, **atau pernyataan bahwa ia belum terhitung**.

    Tidak pernah keduanya. Hasil yang membawa nilai sekaligus alasan berarti
    dua cerita pada satu baris, dan pembaca akan memilih yang lebih
    menyenangkan.

    `jumlah_satuan` ikut dibawa karena Kappa 0,9 atas tiga dokumen dan atas
    tiga ratus dokumen adalah dua pernyataan yang sangat berbeda, dan hanya
    yang kedua layak masuk naskah.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    nilai: float | None = Field(default=None, ge=-1.0, le=1.0)
    jumlah_satuan: int = Field(ge=0)
    alasan: str = ""

    @model_validator(mode="after")
    def _nilai_atau_alasan(self) -> HasilKesepakatan:
        if self.nilai is None and not self.alasan:
            raise ValueError(
                "hasil yang belum terhitung wajib menyebut alasannya — "
                "tanpa itu pembacanya menebak, dan tebakan yang paling mudah "
                "adalah 'belum sempat dihitung'"
            )
        if self.nilai is not None and self.alasan:
            raise ValueError("hasil tidak boleh membawa nilai sekaligus alasan")
        return self

    @property
    def terhitung(self) -> bool:
        return self.nilai is not None

    @classmethod
    def belum_terhitung(cls, alasan: str) -> HasilKesepakatan:
        """Hasil yang menyatakan dirinya kosong, beserta sebabnya."""
        return cls(nilai=None, jumlah_satuan=0, alasan=alasan)

    def memenuhi(self, ambang: float) -> bool:
        """Apakah nilainya mencapai ambang — **selalu `False` bila belum
        terhitung.**

        Tanpa aturan ini, batch tanpa anotasi ganda akan lolos pemeriksaan
        ambang karena tidak ada angka yang lebih kecil daripada ambangnya.
        Itu jalan pintas yang paling menggoda ketika tenggat mendekat.
        """
        return self.nilai is not None and self.nilai >= ambang


def kappa_kategori(
    anotator_a: list[PutusanKategori], anotator_b: list[PutusanKategori]
) -> HasilKesepakatan:
    """Cohen's Kappa atas dokumen yang **keduanya** anotasi — R-07.

    Tanda tangannya menerima `PutusanKategori` dan tidak akan menerima
    `RentangEntitas`. Itu yang menegakkan D-03 Bagian 11, bukan uraian modul
    ini: penyeragaman dua ukuran menuntut mengubah tipe di sini, dan tipe yang
    berubah menuntut penjelasan.

    Dokumen yang hanya dianotasi satu pihak **dilewati**, tidak dihitung
    sebagai ketidaksepakatan. Anotasi ganda hanya 15% (FR-C02), sehingga
    memasukkan sisanya akan menurunkan Kappa atas hal yang bukan
    ketidaksepakatan.

    Empat keadaan menghasilkan hasil yang **belum terhitung**, dan tiap-tiapnya
    punya sebab yang berbeda — karena itu alasannya disebutkan, bukan
    diseragamkan:

    - tidak ada putusan sama sekali
    - tidak ada dokumen yang dianotasi keduanya
    - versi skema berbeda pada dokumen yang sama
    - hanya satu kategori dipakai kedua anotator, sehingga pe = 1

    Yang terakhir paling halus. Ketika pe = 1, pembaginya nol; melaporkannya
    1,0 akan menyatakan kesepakatan sempurna atas tugas yang tidak memiliki
    pilihan, dan itu bukan bukti apa pun.
    """
    pasangan, halangan = _pasangan_bersama(anotator_a, anotator_b)
    if pasangan is None:
        return HasilKesepakatan.belum_terhitung(halangan)
    return _kappa(pasangan)


def _kappa(pasangan: Sequence[tuple[object, object]]) -> HasilKesepakatan:
    """Rumus Cohen's Kappa atas daftar pasangan putusan.

    Dipisahkan dari pemilihan dokumennya supaya rumusnya dapat diuji terhadap
    tabel yang dihitung tangan tanpa menyusun objek anotasi lebih dulu.
    """
    n = len(pasangan)
    sepakat = sum(1 for x, y in pasangan if x == y)
    po = sepakat / n

    sisi_a = Counter(x for x, _ in pasangan)
    sisi_b = Counter(y for _, y in pasangan)
    pe = sum((sisi_a[k] / n) * (sisi_b[k] / n) for k in set(sisi_a) | set(sisi_b))

    if pe >= 1.0:
        return HasilKesepakatan.belum_terhitung(
            "kedua anotator hanya memakai satu kategori — peluang kesepakatan "
            "acak menjadi satu, dan kesepakatan sempurna atas tugas tanpa "
            "pilihan bukan bukti apa pun"
        )

    return HasilKesepakatan(nilai=(po - pe) / (1 - pe), jumlah_satuan=n)


def kappa_per_kategori(
    anotator_a: list[PutusanKategori], anotator_b: list[PutusanKategori]
) -> dict[KategoriMasalah, HasilKesepakatan]:
    """Kappa satu lawan sisanya bagi tiap kategori yang muncul — R-07.

    D-03 Bagian 11 menuntutnya "untuk menemukan kategori yang batasnya kabur",
    dan kalimat berikutnya menentukan bentuk fungsi ini: kategori dengan Kappa
    rendah berulang menandakan **definisinya perlu dipertajam, bukan
    anotatornya perlu ditegur** (KM-03).

    Hasilnya karena itu dipetakan per kategori dan dibawa utuh, tidak diringkas
    menjadi satu angka terburuk. Angka terburuk memberi tahu ada yang salah;
    petanya memberi tahu di mana — dan hanya yang kedua dapat ditindaklanjuti
    dengan mempertajam definisi.

    **Hanya kategori yang muncul** yang dilaporkan. Melaporkan kedelapan
    menghasilkan tujuh baris kosong, dan pembacanya berhenti membaca.

    Peta **kosong** ketika tidak ada bahan — bukan peta berisi delapan hasil
    yang belum terhitung. Yang kedua terbaca sebagai "sudah diperiksa dan
    hasilnya nihil", padahal tidak ada yang diperiksa sama sekali.
    """
    pasangan, _ = _pasangan_bersama(anotator_a, anotator_b)
    if pasangan is None:
        return {}

    muncul = sorted({k for baris in pasangan for k in baris}, key=lambda k: k.value)
    return {
        kategori: _kappa([(x is kategori, y is kategori) for x, y in pasangan])
        for kategori in muncul
    }


def _pasangan_bersama(
    anotator_a: list[PutusanKategori], anotator_b: list[PutusanKategori]
) -> tuple[list[tuple[KategoriMasalah, KategoriMasalah]] | None, str]:
    """Putusan atas dokumen yang keduanya anotasi, beserta halangannya bila tak ada.

    **Satu tempat bagi aturan pemilihan.** `kappa_kategori` dan
    `kappa_per_kategori` memakainya sama persis; dua aturan pemilihan yang
    ditulis terpisah akan berbeda pada keadaan tepi, dan angkanya lalu tidak
    dapat dibandingkan satu sama lain — padahal justru perbandingan keduanya
    yang gunanya (KM-03).

    Mengembalikan halangan sebagai kalimat, bukan sebagai penanda: tiga
    sebabnya berbeda, dan yang membacanya perlu tahu yang mana.
    """
    if not anotator_a or not anotator_b:
        return None, "tidak ada putusan kategori untuk dibandingkan"

    oleh_a = {p.id_dokumen: p for p in anotator_a}
    oleh_b = {p.id_dokumen: p for p in anotator_b}
    bersama = sorted(set(oleh_a) & set(oleh_b))
    if not bersama:
        return None, (
            "tidak ada dokumen yang dianotasi kedua anotator — "
            "ketiadaan bahan bukan kesepakatan nol"
        )

    berbeda_versi = [d for d in bersama if oleh_a[d].versi_skema != oleh_b[d].versi_skema]
    if berbeda_versi:
        return None, (
            f"versi skema berbeda pada {len(berbeda_versi)} dokumen — "
            "membandingkan label yang artinya sudah berubah akan tampak "
            "sebagai ketidaksepakatan anotator (FR-C08)"
        )

    return [(oleh_a[d].kategori_utama, oleh_b[d].kategori_utama) for d in bersama], ""
