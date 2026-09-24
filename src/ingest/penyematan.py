"""Jalur penyematan korpus — R-01 s.d. R-11 fitur 026, TK-57.

Fitur 019 membangun sisi **pembacaan** indeks vektor: `SumberVektor` mencari
segmen terdekat dengan kueri. Modul ini sisi **penulisannya** — yang sebelum
fitur 026 tidak dimiliki baris pembangunan mana pun, sehingga vektor diisi
perkakas SQL dan berkas uji alih-alih kode yang disebarkan.

Akibat yang TK-57 catat: R-06 fitur 019 menuntut versi penyemat tercatat pada
setiap keluaran yang **membentuk indeks**, dan tanpa pembentukan indeks tidak
ada yang mencatat apa pun. Indeks dapat dibangun dua kali dengan model berbeda
tanpa satu catatan pun yang membedakannya.

## Letaknya di `src/ingest/`, dan itu diputus Gerbang 1

Tepi `ingest → llm` dan `ingest → nlp` sudah ada dan tertulis pada
`AGENTS.md`; `kamus`, `logbook`, dan `penyimpanan` lapisan terbuka. Nol tepi
arah baru. Dua kemungkinan lain ditolak: `src/rag/` akan memberi hak tulis
kepada lapisan yang C-17 justru batasi, dan `src/penyimpanan/` lapisan di
bawah yang tidak boleh memanggil `llm`.

## Waktu disuntikkan, tidak diambil dari jam

Versi indeks berupa cap waktu (Keputusan Gerbang 1 K-2). Fungsi yang memanggil
`datetime.now()` sendiri tidak dapat diuji **nilainya** — hanya polanya, dan
uji atas pola lulus juga pada penyusun yang selalu mengembalikan tanggal yang
sama. `sekarang` karena itu diserahkan pemanggil, bentuk yang sejajar dengan
`Penyemat` pada R-04.

## Mengapa cap waktu, bukan cacah naik

Cacah menuntut keadaan tersimpan; keadaan tersimpan dapat disetel ulang; dan
cacah yang tersetel ulang **memakai kembali nomor versi yang sudah pernah
dipakai** — tanpa galat, sehingga dua percobaan berbeda tercatat pada versi
indeks yang sama. Cap waktu tidak dapat terpakai ulang dan tidak menuntut
keadaan apa pun.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from src.kamus.segmen import IndeksTujuan
from src.llm.sematan import Penyemat, VersiPenyemat
from src.logbook.artefak import KomposisiSumber, VersiIndeks
from src.logbook.penulis import tambah_versi_artefak
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.sambungan import SambunganAktif
from src.penyimpanan.skema_indeks import (
    KOLOM_VEKTOR_SEMATAN,
    KOLOM_VERSI_SEMATAN,
    SKEMA_INDEKS,
    TABEL_SEGMEN,
    bilangan_dari_baris,
    pastikan_dimensi_cocok,
    untai_vektor,
)

BENTUK_WAKTU_VERSI: Final = "%Y%m%dT%H%M%SZ"
"""Cap waktu pada versi indeks, selalu UTC — KM-01.

Huruf `Z` ditulis harfiah dan bukan hasil pemformatan zona: ia baru benar
sesudah waktunya diubah ke UTC, dan `susun_versi_indeks` yang memastikannya.
"""


def susun_versi_indeks(indeks_tujuan: IndeksTujuan, *, sekarang: Callable[[], datetime]) -> str:
    """Versi indeks bagi satu pembangunan — K-2, RT-05, D-07 Bagian 3.3.

    Berbentuk `<indeks>-<YYYYMMDDTHHMMSSZ>`. Bagian indeks dibaca dari nilai
    enumnya, **bukan** dari nama skema basis data: yang disusun di sini label
    percobaan, bukan pengenal tabel, dan menyalin nama skema ke sini akan
    membuat dua tempat menyatakan hal yang sama.

    Waktu berzona lain **diubah** ke UTC, tidak ditolak — KM-01 menuntut
    penyimpanan dalam UTC, bukan menuntut pemanggil sudah mengubahnya. Waktu
    tanpa zona ditolak: ia tidak dapat diubah tanpa menebak zonanya, dan
    tebakan itu tidak pernah terlihat pada hasilnya.
    """
    saat = sekarang()
    if saat.tzinfo is None:
        raise ValueError(
            "waktu pembangunan indeks wajib berzona — waktu tanpa zona tidak "
            "dapat diubah ke UTC tanpa menebak, dan tebakannya tidak terbaca "
            "pada versi yang dihasilkan (KM-01)"
        )
    return f"{indeks_tujuan.value}-{saat.astimezone(UTC).strftime(BENTUK_WAKTU_VERSI)}"


class HasilPenyematan(BaseModel):
    """Apa yang satu pembangunan indeks kerjakan, beserta versinya.

    ## Tiga bidang hitungan, bukan satu

    `tersemat` sendirian tidak dapat dibedakan dari indeks yang sebagian
    segmennya **dilewati** karena bertext kosong, dan pembedaan itu yang
    memberi tahu apakah yang bermasalah korpusnya atau jalurnya.

    `tersisa_tanpa_vektor` dibaca sesudah penjalanan: nol berarti indeks penuh.
    Ia bukan turunan kedua bidang lain — segmen dapat bertambah di antara
    pembacaan dan penulisan, dan angka yang dihitung ulang dari bidang lain
    akan menyatakan keadaan yang sudah lewat sebagai keadaan sekarang.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    indeks_tujuan: IndeksTujuan
    versi_indeks: str = Field(min_length=1)
    versi_penyemat: VersiPenyemat
    tersemat: int = Field(ge=0)
    """Segmen yang vektornya benar-benar ditulis pada penjalanan ini."""
    dilewati_teks_kosong: int = Field(ge=0)
    """Segmen yang dilewati sebab teksnya kosong — R-05.

    Dilewati **dan dihitung**. Menyematkannya menjadi vektor nol tidak
    menghasilkan galat; ia menghasilkan tetangga terdekat yang salah.
    """
    tersisa_tanpa_vektor: int = Field(ge=0)
    """Segmen yang masih belum tersemat sesudah penjalanan ini selesai."""


def penanda_model(versi: VersiPenyemat) -> str:
    """Nilai yang ditulis ke `versi_model_sematan` — nama **dan** versi.

    **Ditemukan saat menulis T-5.** T-4 semula menulis `versi_model` saja,
    sehingga `model-a/1.0` dan `model-b/1.0` tercatat sama persis dan R-09
    tidak dapat membedakannya. Model yang berbeda dengan untai versi yang
    kebetulan sama bukan kasus buatan: "1.0" adalah versi pertama hampir
    setiap model.

    Garis miring dipilih karena tidak muncul pada nama model yang lazim
    maupun pada untai versi; penanda yang dapat dibaca dua cara bukan penanda.
    """
    return f"{versi.nama_model}/{versi.versi_model}"


SEGMEN_PER_KUMPULAN: Final = 64
"""Berapa segmen disemat sekali jalan.

**Bukan ambang.** Ia tidak menentukan jawaban apa pun — mengubahnya mengubah
berapa kali peladen dihubungi, bukan segmen mana yang terpilih. Dinamai apa
adanya justru agar ia tidak terbaca sebagai nilai yang C-16 jaga; nilai yang
dinamai "ambang" tunduk pada prosedur kalibrasi BT-29, dan nilai ini tidak
berhak atas perhatian itu.
"""


async def sematkan_indeks(
    sambungan: SambunganAktif,
    *,
    penyemat: Penyemat,
    indeks_tujuan: IndeksTujuan,
    kredensial: Kredensial,
    sekarang: Callable[[], datetime],
    akar_logbook: Path,
) -> HasilPenyematan:
    """Semat seluruh segmen yang belum bervektor pada satu indeks.

    ## Urutan penjagaan menentukan, dan urutan yang salah tetap benar hasilnya

    1. **Kredensial**, sebelum peladen disentuh sama sekali (R-06, R-07).
    2. **Dimensi**, sebelum satu baris pun ditulis (R-03).
    3. Baru membaca segmen ber-`vektor_sematan` NULL (R-01).

    Penjagaan pertama memakai `boleh_tulis_indeks`, **bukan**
    `boleh_baca_indeks` — jalur penjawaban menjangkau kedua indeks untuk
    dibaca, dan menyamakan keduanya memberinya hak tulis lewat pintu belakang
    (TK-62, C-17).

    Bentuk yang sama dengan `ambil_hibrida`: menyaring sesudah kueri berjalan
    menghasilkan keluaran yang sama persis sambil barisnya sudah terbaca, sudah
    berada di memori, dan sudah memengaruhi waktu tanggap.
    """
    if not kredensial.boleh_tulis_indeks(indeks_tujuan):
        raise PermissionError(
            f"kredensial {kredensial.nama!r} tidak boleh menulis ke "
            f"{indeks_tujuan.value} — penyematan menuntut hak tulis indeks, "
            "dan hak baca tidak menggantikannya (C-17)"
        )

    versi = penyemat.versi
    await pastikan_dimensi_cocok(
        sambungan,
        dimensi_model=penyemat.dimensi,
        nama_model=versi.nama_model,
        indeks_tujuan=indeks_tujuan,
    )

    skema = SKEMA_INDEKS[indeks_tujuan]
    penanda = penanda_model(versi)

    # Penjagaan 3 — R-09. Indeks bercampur dua model tidak menghasilkan galat;
    # ia menghasilkan peringkat yang masuk akal dan salah, sebab jarak hanya
    # bermakna di dalam satu ruang sematan. Diperiksa **sebelum** membaca
    # segmen, agar penolakan tidak pernah meninggalkan indeks separuh bercampur.
    sudah_ada = await sambungan.fetch(
        f"SELECT DISTINCT {KOLOM_VERSI_SEMATAN} AS penanda FROM {skema}.{TABEL_SEGMEN} "
        f"WHERE {KOLOM_VERSI_SEMATAN} IS NOT NULL"
    )
    lain = sorted({str(b["penanda"]) for b in sudah_ada} - {penanda})
    if lain:
        raise ValueError(
            f"indeks {skema} sudah disemat dengan {', '.join(lain)}, sedangkan "
            f"penyemat yang diserahkan {penanda}. Indeks bercampur dua model "
            "menghasilkan jarak yang tidak dapat dibandingkan (R-09) — bangun ulang "
            "seluruh indeks dengan satu model, bukan melanjutkannya"
        )

    baris = await sambungan.fetch(
        f"SELECT id_segmen, teks FROM {skema}.{TABEL_SEGMEN} "
        f"WHERE {KOLOM_VEKTOR_SEMATAN} IS NULL ORDER BY id_segmen"
    )

    menunggu = [(str(b["id_segmen"]), str(b["teks"])) for b in baris]
    berisi = [(satu, teks) for satu, teks in menunggu if teks.strip()]
    dilewati = len(menunggu) - len(berisi)

    tersemat = 0
    for awal in range(0, len(berisi), SEGMEN_PER_KUMPULAN):
        kumpulan = berisi[awal : awal + SEGMEN_PER_KUMPULAN]
        vektor = await penyemat.sematkan([teks for _, teks in kumpulan])
        for (id_segmen, _), satu in zip(kumpulan, vektor, strict=True):
            # Vektor dan versi model ditulis **satu pernyataan**. Versi yang
            # ditulis belakangan dapat tertinggal bila penjalanan terputus di
            # antaranya, dan baris bervektor tanpa versi tidak dapat dibedakan
            # dari baris yang disemat model tak dikenal.
            await sambungan.execute(
                f"UPDATE {skema}.{TABEL_SEGMEN} "
                f"SET {KOLOM_VEKTOR_SEMATAN} = $1::vector, {KOLOM_VERSI_SEMATAN} = $2 "
                "WHERE id_segmen = $3",
                untai_vektor(satu),
                penanda,
                id_segmen,
            )
            tersemat += 1

    sisa = await sambungan.fetchrow(
        f"SELECT count(*) AS jumlah FROM {skema}.{TABEL_SEGMEN} "
        f"WHERE {KOLOM_VEKTOR_SEMATAN} IS NULL"
    )

    # Satu pemanggilan jam bagi versi **dan** tanggal pembangunan. Dua
    # pemanggilan dapat jatuh pada detik berbeda, dan catatan yang versinya
    # berbunyi 07.30.00 sementara tanggalnya 07.30.01 menyatakan dua saat
    # bagi satu peristiwa.
    saat = sekarang()
    versi_indeks = susun_versi_indeks(indeks_tujuan, sekarang=lambda: saat)

    # R-02, C-09 — setiap versi indeks yang diterbitkan memiliki baris L2.
    # Ditemukan pada T-6 karena mutasi M-8 **tidak dapat dipasang**: T-2
    # membangun penulisnya, T-4 membangun jalur ini, dan tidak satu tugas pun
    # menyambungkan keduanya. Penjalanan yang tidak menyemat apa pun tetap
    # mencatat: versi yang dikutip percobaan tanpa baris L2 adalah provenans
    # yang putus, dan itu lebih buruk daripada catatan yang berulang.
    komposisi = await sambungan.fetch(
        f"SELECT lisensi AS label, count(*) AS jumlah FROM {skema}.{TABEL_SEGMEN} "
        f"WHERE {KOLOM_VEKTOR_SEMATAN} IS NOT NULL GROUP BY lisensi ORDER BY lisensi"
    )
    susunan = tuple(
        KomposisiSumber(
            label=str(b["label"]),
            jumlah=bilangan_dari_baris(b, "jumlah", "komposisi tidak dapat dihitung"),
        )
        for b in komposisi
    )
    tambah_versi_artefak(
        akar_logbook,
        keterangan=VersiIndeks(
            versi_indeks=versi_indeks,
            dibangun_pada=saat.astimezone(UTC),
            # Jumlah segmen **indeks**, bukan penjalanan — D-10 Bagian 4.
            # Penjalanan kedua yang menyemat satu segmen atas indeks berisi
            # dua mencatat tiga, bukan satu.
            jumlah_segmen=sum(k.jumlah for k in susunan),
            komposisi_sumber=susunan,
            nama_model_sematan=versi.nama_model,
            versi_model_sematan=versi.versi_model,
        ),
    )

    return HasilPenyematan(
        indeks_tujuan=indeks_tujuan,
        versi_indeks=versi_indeks,
        versi_penyemat=versi,
        tersemat=tersemat,
        dilewati_teks_kosong=dilewati,
        tersisa_tanpa_vektor=bilangan_dari_baris(
            sisa, "jumlah", f"tabel {skema}.{TABEL_SEGMEN} tidak dapat dihitung"
        ),
    )
