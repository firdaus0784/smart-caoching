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

from pydantic import ValidationError

from src.nlp.anotasi.rentang import PutusanKategori, RentangEntitas
from src.nlp.anotasi.skema import KategoriMasalah, LabelEntitas, VersiSkema

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


class GalatImpor(Exception):
    """Isi ekspor tidak dapat diubah menjadi tipe kita.

    Dibedakan dari `GalatBentukEkspor`: yang pertama berarti berkasnya
    berbentuk lain, yang ini berarti berkasnya berbentuk benar tetapi memuat
    nilai yang tidak sah — label di luar skema, rentang yang tidak cocok.
    Pembedaannya menentukan siapa yang menindaklanjuti: yang pertama kita,
    yang kedua tim anotasi.
    """


@dataclass(frozen=True)
class DokumenTeranotasi:
    """Satu dokumen beserta seluruh anotasinya, dalam tipe milik kita."""

    id_dokumen: str
    teks: str
    rentang: tuple[RentangEntitas, ...]
    putusan: tuple[PutusanKategori, ...]


@dataclass(frozen=True)
class HasilImpor:
    """Korpus hasil impor, beserta apa yang **tidak** masuk ke dalamnya.

    `dilewati` sengaja dibawa. Dokumen yang belum dianotasi bukan kesalahan;
    korpus yang diam-diam lebih kecil daripada batchnya adalah kesalahan, dan
    selisihnya baru terlihat ketika seseorang membandingkan dua angka yang
    tidak pernah dilaporkan bersama.
    """

    dokumen: tuple[DokumenTeranotasi, ...]
    dilewati: tuple[str, ...]
    versi_skema: VersiSkema


JENIS_DIKENALI = ("labels", "choices")
"""Dua jenis hasil yang modul ini tahu artinya — `plan.md` Bagian 3."""


def impor(
    isi: list[dict[str, Any]],
    *,
    versi_skema: VersiSkema,
    kode_anotator: dict[int, str],
    bendera_terkumpul: bool,
) -> HasilImpor:
    """Ubah berkas ekspor menjadi korpus bertipe fitur 003 — R-01, R-03.

    Seluruh argumen selain isinya bersifat **kata kunci dan wajib**. Ketiganya
    adalah hal yang Label Studio tidak bawa (KB-023) dan modul ini tidak boleh
    menebak; nilai bawaan bagi salah satunya berarti korpus yang menyatakan
    sesuatu yang tidak pernah diperiksa siapa pun.

    `id_dokumen` diambil dari id tugas Label Studio apa adanya. Penamaan
    dokumen bergaya D-03 (`DOC-2026-00412`) adalah pekerjaan pengelola korpus,
    dan menebaknya di sini akan menghasilkan dua penomoran yang berbeda.
    """
    tugas = urai_ekspor(isi)
    dokumen: list[DokumenTeranotasi] = []
    dilewati: list[str] = []

    for t in tugas:
        hidup = [a for a in t.anotasi if not a.dibatalkan]
        if not hidup:
            dilewati.append(str(t.id))
            continue
        rentang: list[RentangEntitas] = []
        putusan: list[PutusanKategori] = []
        for a in hidup:
            kode = _kode_anotator(a.id_pengguna, kode_anotator)
            for hasil in a.hasil:
                _kumpulkan(hasil, t, kode, versi_skema, rentang, putusan)
        dokumen.append(
            DokumenTeranotasi(
                id_dokumen=str(t.id),
                teks=t.teks,
                rentang=tuple(rentang),
                putusan=tuple(putusan),
            )
        )

    return HasilImpor(dokumen=tuple(dokumen), dilewati=tuple(dilewati), versi_skema=versi_skema)


def _kode_anotator(id_pengguna: int, tabel: dict[int, str]) -> str:
    """Kode anonim D-03 Bagian 15, atau gagal — **tidak pernah id mentah**."""
    if id_pengguna not in tabel:
        raise GalatImpor(
            f"id pengguna Label Studio {id_pengguna} tidak ada pada tabel kode "
            "anotator — id mentah adalah pengenal yang bertahan pada berkas yang "
            "dilampirkan naskah (D-03 Bagian 15)"
        )
    return tabel[id_pengguna]


def _kumpulkan(
    hasil: dict[str, Any],
    tugas: TugasMentah,
    kode: str,
    versi_skema: VersiSkema,
    rentang: list[RentangEntitas],
    putusan: list[PutusanKategori],
) -> None:
    jenis = _ambil(hasil, "type", f"tugas {tugas.id}")
    nilai = _ambil(hasil, "value", f"tugas {tugas.id}")
    if jenis == "labels":
        rentang.append(_rentang(nilai, tugas, kode, versi_skema))
    elif jenis == "choices":
        putusan.append(_putusan(nilai, tugas, kode, versi_skema))
    else:
        raise GalatImpor(
            f"tugas {tugas.id}: jenis hasil {jenis!r} tidak dikenali — "
            "konfigurasi proyek memuat kendali yang modul ini tidak tahu "
            "artinya, dan mengabaikannya berarti membuang pekerjaan anotator"
        )


def _rentang(
    nilai: dict[str, Any], tugas: TugasMentah, kode: str, versi_skema: VersiSkema
) -> RentangEntitas:
    letak = f"tugas {tugas.id}"
    label = _satu(_ambil(nilai, "labels", letak), "labels", letak)
    if label not in {a.value for a in LabelEntitas}:
        raise GalatImpor(
            f"{letak}: label {label!r} tidak ada pada skema D-03 — konfigurasi "
            "proyek dapat disunting siapa pun yang punya akses, sehingga "
            "kecocokannya diperiksa di sini"
        )
    try:
        return RentangEntitas(
            teks_kanonik=tugas.teks,
            mulai=_ambil(nilai, "start", letak),
            akhir=_ambil(nilai, "end", letak),
            label=LabelEntitas(label),
            versi_skema=versi_skema,
            id_anotator=kode,
            teks_rentang=_ambil(nilai, "text", letak),
        )
    except ValidationError as galat:
        raise GalatImpor(
            f"{letak}: rentang tidak cocok dengan teks dokumennya — rentang yang "
            f"diperbaiki diam-diam menunjuk kata lain tanpa satu galat pun ({galat})"
        ) from galat


def _putusan(
    nilai: dict[str, Any], tugas: TugasMentah, kode: str, versi_skema: VersiSkema
) -> PutusanKategori:
    letak = f"tugas {tugas.id}"
    kategori = _satu(_ambil(nilai, "choices", letak), "choices", letak)
    if kategori not in {k.value for k in KategoriMasalah}:
        raise GalatImpor(f"{letak}: kategori {kategori!r} tidak ada pada D-03 Bagian 5")
    return PutusanKategori(
        id_dokumen=str(tugas.id),
        kategori_utama=KategoriMasalah(kategori),
        versi_skema=versi_skema,
        id_anotator=kode,
    )


def _satu(nilai: Any, kunci: str, letak: str) -> str:
    """Satu nilai dari daftar yang seharusnya berisi satu.

    Daftar berisi dua berarti konfigurasi proyek mengizinkan pilihan ganda di
    tempat yang skema kita anggap tunggal, dan mengambil yang pertama berarti
    membuang putusan anotator tanpa jejak.
    """
    daftar = _daftar(nilai, kunci, letak)
    if len(daftar) != 1:
        raise GalatImpor(
            f"{letak}: {kunci!r} berisi {len(daftar)} nilai, diharapkan satu — "
            "mengambil yang pertama berarti membuang putusan anotator tanpa jejak"
        )
    return str(daftar[0])
