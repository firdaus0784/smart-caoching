"""Metrik per kelas — R-07 s.d. R-09, FR-D04, D-08.

FR-D04 menuntut metrik dilaporkan **per kelas, bukan hanya rerata**, dengan
alasan yang tertulis pada kebutuhannya sendiri: mendeteksi kelas berperforma
rendah. Rerata menyembunyikan persis apa yang perlu dilihat, dan korpus
manajerial hampir pasti tidak seimbang — D-03 menempatkan K5 dan K7 sebagai
kategori yang mendominasi.

## Dua rerata, dan keduanya dinamai

**Makro** merata-ratakan F1 tiap kelas dengan bobot sama; **mikro**
menjumlahkan seluruh benar dan salah lebih dulu. Pada kelas tidak seimbang
keduanya berbeda tajam: sembilan puluh dokumen kelas besar yang tepat dan
sepuluh dokumen kelas kecil yang seluruhnya keliru menghasilkan mikro 0,90 dan
makro 0,47 — pada data yang sama.

Karena itu **tidak ada bidang bernama `f1` saja.** Bidang tunggal adalah
bidang yang pembacanya tidak tahu jenisnya, dan ia akan disalin ke naskah
tanpa keterangan. Yang membaca naskah tidak ada di ruangan untuk bertanya.

## Tiga keadaan pada setiap angka

Mengikuti bentuk yang sudah tiga kali terbukti — `HasilSistem` fitur 015,
`HasilKesepakatan` fitur 003, `bendera` fitur 016:

| Keadaan | Nilai |
|---|---|
| Bahannya ada dan dihitung | angka |
| Bahannya ada dan hasilnya buruk | angka, biasanya 0,0 |
| **Bahannya tidak ada** | **`None` beserta alasan** |

Kelas tanpa satu pun contoh yang dilaporkan F1 = 0,0 terbaca sebagai kelas
yang modelnya gagal total. Tindak lanjutnya menjadi melatih ulang, padahal
yang diperlukan menambah data — dan kekeliruan arah itu memakan waktu yang
tidak dimiliki penelitian delapan bulan.

Pembedaan yang lebih halus dan sama pentingnya: kelas yang **hanya muncul pada
prediksi** punya presisi 0,0 yang terhitung — bahannya ada, modelnya terlalu
berani — sedangkan recall-nya belum terhitung, sebab tidak ada satu pun contoh
sungguhan untuk ditemukan. Menyeragamkan keduanya menjadi 0,0 menyembunyikan
apa yang perlu diperbaiki.

## Mengapa tidak memakai `HasilKesepakatan` fitur 003

Bentuknya sama dan artinya berbeda. `HasilKesepakatan` menyatakan kesepakatan
antar-anotator; `Nilai` di sini menyatakan performa model terhadap acuan.
Menyatukannya akan membuat `src/nlp/pelatihan/` bergantung pada
`src/nlp/anotasi/` untuk sesuatu yang bukan anotasi — dan kelak, ketika salah
satunya perlu bidang tambahan, yang lain ikut membawanya tanpa alasan.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Nilai(BaseModel):
    """Satu angka metrik, **atau pernyataan bahwa bahannya tidak ada**.

    Tidak pernah keduanya — lihat uraian modul.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    nilai: float | None = Field(default=None, ge=0.0, le=1.0)
    alasan: str = ""

    @model_validator(mode="after")
    def _nilai_atau_alasan(self) -> Nilai:
        if self.nilai is None and not self.alasan:
            raise ValueError(
                "angka yang belum terhitung wajib menyebut alasannya — tanpa itu "
                "pembacanya menebak, dan tebakan yang paling mudah adalah "
                "'modelnya gagal'"
            )
        if self.nilai is not None and self.alasan:
            raise ValueError("angka tidak boleh membawa nilai sekaligus alasan")
        return self

    @property
    def terhitung(self) -> bool:
        return self.nilai is not None

    @classmethod
    def belum_terhitung(cls, alasan: str) -> Nilai:
        return cls(nilai=None, alasan=alasan)


class MetrikKelas(BaseModel):
    """Presisi, recall, dan F1 satu kelas, beserta jumlah contohnya.

    `jumlah_acuan` ikut dibawa karena F1 0,9 atas tiga dokumen dan atas tiga
    ratus dokumen adalah dua pernyataan yang sangat berbeda — dan hanya yang
    kedua layak masuk naskah. Bentuk yang sama dengan `jumlah_satuan` pada
    `HasilKesepakatan` fitur 003.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    presisi: Nilai
    recall: Nilai
    f1: Nilai
    jumlah_acuan: int = Field(ge=0)
    jumlah_prediksi: int = Field(ge=0)


class HasilMetrik(BaseModel):
    """Metrik lengkap: per kelas **dan** kedua rerata.

    Per kelas lebih dulu pada urutan bidang, dan itu disengaja — yang membaca
    dari atas menemukan tabelnya sebelum menemukan ringkasannya.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    per_kelas: dict[str, MetrikKelas]
    f1_makro: Nilai
    f1_mikro: Nilai
    jumlah_contoh: int = Field(gt=0)


def _bagi(pembilang: int, penyebut: int, alasan: str) -> Nilai:
    """Bagi, atau nyatakan bahannya tidak ada.

    Penyebut nol di sini tidak pernah berarti "nilainya nol" — ia berarti
    tidak ada satu pun contoh yang dapat menghasilkan nilai.
    """
    if penyebut == 0:
        return Nilai.belum_terhitung(alasan)
    return Nilai(nilai=pembilang / penyebut)


def hitung_metrik(
    *,
    acuan: Sequence[str],
    prediksi: Sequence[str],
    kelas: Sequence[str] | None = None,
) -> HasilMetrik:
    """Metrik per kelas beserta rerata makro dan mikro — R-07 s.d. R-09.

    `kelas` boleh tidak diberikan; bila kosong, yang dilaporkan hanya kelas
    yang benar-benar muncul. Melaporkan kelas yang tidak pernah muncul
    menghasilkan baris kosong, dan pembacanya berhenti membaca — sama dengan
    `kappa_per_kategori` fitur 003.

    Rerata makro **melewati kelas yang belum terhitung**, tidak menghitungnya
    sebagai 0,0. Memasukkannya menurunkan rerata atas kelas yang tidak pernah
    diuji, dan angka yang turun karena data yang tidak ada menyesatkan ke arah
    pesimistis — sama buruknya dengan menyesatkan ke arah sebaliknya.
    """
    if len(acuan) != len(prediksi):
        raise ValueError(
            f"panjang acuan ({len(acuan)}) dan prediksi ({len(prediksi)}) berbeda — "
            "satu prediksi akan disandingkan dengan acuan yang salah, dan seluruh "
            "angka sesudahnya menerangkan hal lain"
        )
    if not acuan:
        raise ValueError(
            "metrik atas nol contoh bukan 0,0 dan bukan 1,0 — ia bukan metrik. "
            "Hasil yang seluruh kelasnya belum terhitung terbaca seperti evaluasi "
            "yang berjalan dan tidak menemukan apa-apa"
        )

    daftar = tuple(kelas) if kelas is not None else tuple(sorted(set(acuan) | set(prediksi)))
    n_acuan = Counter(acuan)
    n_prediksi = Counter(prediksi)
    benar = Counter(a for a, p in zip(acuan, prediksi, strict=True) if a == p)

    per_kelas = {k: _metrik_kelas(k, benar[k], n_acuan[k], n_prediksi[k]) for k in daftar}

    terhitung = [m.f1.nilai for m in per_kelas.values() if m.f1.terhitung]
    f1_makro = (
        Nilai(nilai=sum(t for t in terhitung if t is not None) / len(terhitung))
        if terhitung
        else Nilai.belum_terhitung("tidak ada satu pun kelas yang dapat dihitung")
    )

    total_benar = sum(benar[k] for k in daftar)
    total = sum(n_acuan[k] for k in daftar)
    f1_mikro = _bagi(
        total_benar,
        total,
        "tidak ada satu pun contoh pada kelas yang dilaporkan",
    )

    return HasilMetrik(
        per_kelas=per_kelas,
        f1_makro=f1_makro,
        f1_mikro=f1_mikro,
        jumlah_contoh=len(acuan),
    )


def _metrik_kelas(nama: str, benar: int, jumlah_acuan: int, jumlah_prediksi: int) -> MetrikKelas:
    """Satu kelas. Ketiga angkanya punya sebab berbeda ketika belum terhitung.

    Presisi belum terhitung ketika model **tidak pernah menandai** kelas itu;
    recall belum terhitung ketika acuan **tidak pernah memuatnya**. Keduanya
    dinyatakan terpisah karena tindak lanjutnya berbeda.
    """
    presisi = _bagi(
        benar,
        jumlah_prediksi,
        f"model tidak pernah menandai kelas {nama!r}, sehingga tidak ada prediksi "
        "yang dapat dinilai ketepatannya",
    )
    recall = _bagi(
        benar,
        jumlah_acuan,
        f"acuan tidak memuat satu pun contoh kelas {nama!r}, sehingga tidak ada "
        "yang dapat ditemukan",
    )
    f1 = _bagi(
        2 * benar,
        2 * benar + (jumlah_prediksi - benar) + (jumlah_acuan - benar),
        f"kelas {nama!r} tidak muncul pada acuan maupun prediksi — melaporkannya "
        "0,0 akan menyatakan modelnya gagal total pada kelas yang tidak pernah diuji",
    )
    return MetrikKelas(
        presisi=presisi,
        recall=recall,
        f1=f1,
        jumlah_acuan=jumlah_acuan,
        jumlah_prediksi=jumlah_prediksi,
    )
