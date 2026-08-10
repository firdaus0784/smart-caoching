"""Pembacaan berkas ekspor Label Studio — R-01 s.d. R-08, KB-023, KB-025.

**Kode kita tidak mengimpor Label Studio, tidak memanggilnya, dan tidak
mengenal API-nya.** KB-020 menetapkan ia layanan terpisah; yang dibaca di sini
hanyalah berkas JSON biasa yang dihasilkan tombol ekspornya. Batas itu yang
membuat kenaikan versi perangkatnya menjadi persoalan satu modul, bukan
persoalan seluruh sistem.

## Penguraian tidak pernah sebagian

Setiap kunci diambil dengan **indeks, bukan `.get()` bernilai bawaan.** Kunci
yang hilang menaikkan `GalatBentukEkspor` yang menyebut kunci **dan letak
tugasnya**, dan satu tugas yang rusak menggagalkan seluruh berkas.

Alasannya bukan kerewelan. Label Studio dapat naik versi tanpa kita, dan
penguraian yang toleran menghasilkan korpus yang sebagian bidangnya hilang
tanpa satu galat pun. Bidang yang paling mungkin hilang adalah bidang yang
jarang terisi — yaitu bendera — dan salah satu bendera menyatakan data pribadi
lolos anonimisasi (`bocor_pii`, diperiksa harian pada KM-05).

Melewati tugas yang rusak lebih buruk lagi: korpusnya kurang satu dokumen
tanpa seorang pun tahu, dan dokumen yang hilang adalah dokumen yang bentuknya
tidak biasa — justru yang perlu dilihat orang.

## Yang Label Studio bawa, dan yang tidak

Diperiksa terhadap berkas sungguhan pada KB-023, bukan terhadap dokumentasi:

| Dibawa | Tidak dibawa |
|---|---|
| `value.start` / `value.end` — **indeks karakter** | `versi_skema` |
| `completed_by` — bilangan bulat id pengguna | `bendera` |
| `predictions` — kosong bila tanpa pra-anotasi | `status_pra_anotasi` |

Kunci `teks` pada `data` adalah nama yang `plan.md` Bagian 3 tetapkan. Proyek
yang memakai nama lain ditolak di sini, sebab dokumen tanpa teks membuat
seluruh pemeriksaan rentang lolos karena tidak ada yang diperiksa.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

KUNCI_TEKS = "teks"
"""Nama bidang teks pada `data`, ditetapkan `plan.md` Bagian 3."""


class GalatBentukEkspor(Exception):
    """Bentuk berkas ekspor tidak sesuai yang dikenali.

    Satu tipe bagi seluruh keadaan, dan pesannya yang membedakan. Tipe galat
    per keadaan akan menggoda pemanggil menangkap sebagiannya saja, dan yang
    tertangkap sebagian adalah penguraian sebagian dengan nama lain.
    """


@dataclass(frozen=True)
class AnotasiMentah:
    """Satu anotasi apa adanya dari berkas ekspor, belum menjadi tipe kita.

    Sengaja mentah. Perubahan menjadi `RentangEntitas` dan `PutusanKategori`
    menuntut versi skema dan tabel anotator yang hanya diketahui pemanggil,
    sehingga memaksakannya di sini akan menuntut modul ini menebak keduanya.
    """

    id: int
    id_pengguna: int
    dibatalkan: bool
    hasil: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class TugasMentah:
    """Satu dokumen beserta seluruh anotasinya."""

    id: int
    teks: str
    anotasi: tuple[AnotasiMentah, ...]
    prediksi: tuple[dict[str, Any], ...]


def _ambil(wadah: Any, kunci: str, letak: str) -> Any:
    """Ambil satu kunci, atau gagal dengan menyebut kunci dan letaknya."""
    if not isinstance(wadah, dict):
        raise GalatBentukEkspor(
            f"{letak}: diharapkan objek dengan kunci {kunci!r}, "
            f"yang ditemukan {type(wadah).__name__}"
        )
    if kunci not in wadah:
        raise GalatBentukEkspor(
            f"{letak}: kunci {kunci!r} tidak ada — bentuk berkas ekspor berubah, "
            "dan penguraian sebagian menghasilkan korpus yang kekurangan bidang "
            "tanpa satu galat pun"
        )
    return wadah[kunci]


def _daftar(nilai: Any, kunci: str, letak: str) -> list[Any]:
    if not isinstance(nilai, list):
        raise GalatBentukEkspor(
            f"{letak}: {kunci!r} diharapkan berupa daftar, yang ditemukan {type(nilai).__name__}"
        )
    return nilai


def urai_ekspor(isi: list[dict[str, Any]]) -> tuple[TugasMentah, ...]:
    """Ubah isi berkas ekspor menjadi tugas mentah — R-02.

    Gagal tegas pada bentuk apa pun yang tidak dikenali, dan **tidak pernah
    mengurai sebagian**: satu tugas yang rusak menggagalkan seluruh berkas.
    """
    if not isinstance(isi, list):
        raise GalatBentukEkspor(
            "berkas ekspor Label Studio diharapkan berupa daftar tugas, "
            f"yang ditemukan {type(isi).__name__}"
        )

    return tuple(_urai_tugas(tugas, f"tugas ke-{i}") for i, tugas in enumerate(isi))


def _urai_tugas(mentah: Any, letak: str) -> TugasMentah:
    id_tugas = _ambil(mentah, "id", letak)
    data = _ambil(mentah, "data", letak)
    teks = _ambil(data, KUNCI_TEKS, f"{letak} bidang data")
    if not isinstance(teks, str) or not teks:
        raise GalatBentukEkspor(
            f"{letak}: bidang {KUNCI_TEKS!r} kosong atau bukan untai — dokumen "
            "tanpa teks membuat seluruh pemeriksaan rentang lolos karena tidak "
            "ada yang diperiksa"
        )

    anotasi = _daftar(_ambil(mentah, "annotations", letak), "annotations", letak)
    prediksi = _daftar(_ambil(mentah, "predictions", letak), "predictions", letak)

    return TugasMentah(
        id=id_tugas,
        teks=teks,
        anotasi=tuple(_urai_anotasi(a, f"{letak} anotasi ke-{i}") for i, a in enumerate(anotasi)),
        prediksi=tuple(prediksi),
    )


def _urai_anotasi(mentah: Any, letak: str) -> AnotasiMentah:
    hasil = _daftar(_ambil(mentah, "result", letak), "result", letak)
    return AnotasiMentah(
        id=_ambil(mentah, "id", letak),
        id_pengguna=_ambil(mentah, "completed_by", letak),
        dibatalkan=bool(_ambil(mentah, "was_cancelled", letak)),
        hasil=tuple(hasil),
    )
