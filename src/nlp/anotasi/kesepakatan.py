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

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
