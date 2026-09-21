"""Penyusun pengambilan hibrida — R-07, R-13, R-14, C-02, C-17, ADR-03.

Tahap 4-5 pada alur D-07 Bagian 4: dua sumber mencari terpisah, hasilnya
digabung, lalu dipangkas ke 5-8 segmen.

## Kredensial diperiksa sebelum sumber dijalankan

**Di sinilah C-02 berhenti menjadi pernyataan dan menjadi perilaku.** Fitur 006
memberi setiap kredensial daftar indeks yang dijangkaunya; modul ini tempat
pertama daftar itu benar-benar membatasi sesuatu.

Urutannya menentukan, dan urutan yang salah tetap menghasilkan keluaran yang
benar. Menyaring hasil **sesudah** pencarian berjalan menghasilkan daftar yang
sama — tanpa segmen metadata, tampak patuh — sementara segmen itu sudah dibaca,
sudah berada di memori, dan sudah memengaruhi waktu tanggap. C-02 kalimat
kedua menolaknya dengan tepat: *"Pemisahan pada tingkat indeks, bukan
penyaringan saat kueri."*

Bentuk yang sama dengan `PenyimpanDasar` fitur 002: *"Pelaksana wajib memeriksa
kredensial **sebelum** menyentuh data. Memeriksa keberadaan lebih dulu
membocorkan keberadaan dokumen karantina lewat perbedaan galat."*

## R-05 ditegakkan sesudah penyaringan, bukan sebelumnya

Tiga sumber yang dua di antaranya tidak terjangkau kredensial adalah **satu**
sumber yang sesungguhnya. Menghitungnya sebelum penyaringan meloloskan
pengambilan leksikal saja yang ADR-03 tolak — dengan hitungan yang terlihat
benar.

## Tahap 5 dijalankan di sini, sebelum pemangkasan

`docs/D07.md` Bagian 4 baris [5]: *"Penggabungan dan pemeringkatan ulang →
5-8 segmen teratas"*. Urutannya menentukan: memeringkat ulang **sesudah**
pemangkasan berarti model tahap 5 hanya melihat delapan segmen yang sudah
dipilih penggabungan, dan segmen peringkat sembilan yang seharusnya naik tidak
pernah ditawarkan kepadanya. Pemeringkat ulang yang bekerja atas hasil
pemangkasan adalah pemeringkat ulang yang tidak dapat memperbaiki apa pun yang
paling perlu diperbaiki.

`pemeringkat` wajib diserahkan pemanggil, tanpa nilai baku. Alasannya ada pada
`peringkat_ulang.py`: parameter yang boleh dihilangkan mengembalikan jalur
mundur yang diam, dan R-05 melarangnya.

## Versi indeks per sumber, bukan satu

Dua sumber membaca dua indeks yang dibangun ulang pada waktu berbeda. Satu
bidang `versi_indeks` tunggal memaksa memilih salah satunya, dan percobaan
yang tercatat pada D-10 L1 kemudian menyebut versi yang separuh keliru — lebih
buruk daripada tanpa versi, sebab ia menuntun orang mengulang dengan indeks
yang salah.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from src.penyimpanan.kredensial import Kredensial
from src.rag.pengambilan.gabung import HasilGabungan, gabung_peringkat
from src.rag.pengambilan.kandidat import SumberKandidat
from src.rag.pengambilan.peringkat_ulang import (
    Pemeringkat,
    Pemeringkatan,
    peringkat_ulang,
)
from src.rag.pengambilan.tetapan import (
    JUMLAH_KANDIDAT_PER_SUMBER,
    JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM,
)


class AsalSumber(BaseModel):
    """Apa yang satu sumber sumbangkan pada pengambilan ini.

    Ketiga keterangan tinggal pada satu objek, bukan pada tiga pemetaan
    berkunci nama. Pemetaan sejajar dapat berbeda isinya — satu memuat sumber
    yang tidak ada pada yang lain — dan yang berbeda adalah yang tidak
    diperbarui. Pola yang sama dengan alasan `HasilSumber.peringkat_dari`
    menghitung peringkat dari posisinya alih-alih menyimpannya terpisah.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    nama_sumber: str = Field(min_length=1)
    versi_indeks: str = Field(min_length=1)
    """Versi indeks yang melayani sumber ini — R-13, D-07 Bagian 3.3, RT-05."""
    jumlah_kandidat: int = Field(ge=0)
    """Berapa kandidat sumber ini sumbangkan sebelum penggabungan.

    Dibaca saat BT-29 mengalibrasi: sumber yang selalu menyumbang nol adalah
    sumber yang tidak bekerja, dan tanpa angka ini ia tidak dapat dibedakan
    dari sumber yang bekerja atas korpus yang memang tidak memuat jawabannya.
    """


class HasilPengambilan(BaseModel):
    """Segmen yang diteruskan ke tahap berikutnya, beserta asal-usulnya."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    segmen: tuple[HasilGabungan, ...]
    pemeringkatan: Pemeringkatan
    """Siapa yang menjalankan tahap 5 — R-05, BT-30.

    Tanpa nilai baku, dengan sengaja. Jalur mundur BT-30 menghasilkan urutan
    yang sama dengan pemeringkat ulang yang berjalan tanpa mengubah apa pun,
    dan tanpa bidang ini keduanya tidak dapat dibedakan dari keluaran.
    """
    asal: tuple[AsalSumber, ...]
    """Sumber yang berpartisipasi, terurut menurut nama.

    `tuple`, bukan `dict`. `kredensial.py` menyatakan alasannya bagi seluruh
    proyek: *"Objek beku yang memuat himpunan yang dapat ditambah anggotanya
    tidak beku dalam arti yang berguna."* Pemetaan pada model beku tetap dapat
    disunting isinya, dan hasil pengambilan yang asal-usulnya dapat disunting
    adalah hasil yang catatan percobaannya tidak membuktikan apa pun.
    """

    def asal_dari(self, nama_sumber: str) -> AsalSumber | None:
        """Asal dari satu sumber; `None` bila sumber itu tidak berpartisipasi."""
        for satu in self.asal:
            if satu.nama_sumber == nama_sumber:
                return satu
        return None


async def ambil_hibrida(
    kueri: str,
    *,
    kredensial: Kredensial,
    sumber: Sequence[SumberKandidat],
    pemeringkat: Pemeringkat,
) -> HasilPengambilan:
    """Jalankan tahap 4-5 D-07 Bagian 4.

    `kredensial` tepat sesudah kueri dan wajib — mengikuti `PenyimpanDasar`
    fitur 002: *"Menempatkannya di akhir daftar parameter membuatnya terbaca
    sebagai renungan belakangan, dan yang terbaca sebagai renungan belakangan
    akan diperlakukan begitu."*
    """
    if not kueri.strip():
        raise ValueError("kueri kosong tidak dapat diambil")

    terjangkau = [s for s in sumber if kredensial.boleh_baca_indeks(s.indeks_tujuan)]

    hasil_sumber = [await s.cari(kueri, batas=JUMLAH_KANDIDAT_PER_SUMBER) for s in terjangkau]
    gabungan = gabung_peringkat(hasil_sumber)
    tahap_lima = await peringkat_ulang(kueri, gabungan, pemeringkat=pemeringkat)

    return HasilPengambilan(
        segmen=tahap_lima.segmen[:JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM],
        pemeringkatan=tahap_lima.pemeringkatan,
        asal=tuple(
            sorted(
                (
                    AsalSumber(
                        nama_sumber=h.nama_sumber,
                        versi_indeks=h.versi_indeks,
                        jumlah_kandidat=len(h.peringkat),
                    )
                    for h in hasil_sumber
                ),
                key=lambda a: a.nama_sumber,
            )
        ),
    )
