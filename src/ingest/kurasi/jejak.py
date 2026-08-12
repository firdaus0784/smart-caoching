"""Jejak audit kurasi — R-09, R-13, FR-I05, C-05, KM-03.

FR-I05: *"Sistem mencatat jejak audit setiap tindakan kurasi (siapa, kapan,
apa, alasan)."* Empat bidang, tidak lebih.

## "Siapa" berarti peran

C-05 memisahkan kunci pemetaan pseudonim dari data perilaku; KM-03 melarang
data pribadi masuk catatan. Yang perlu ditelusuri sebuah putusan adalah
**kewenangannya**, bukan siapa yang duduk pada kewenangan itu hari itu.

Ditegakkan tipe, bukan pemeriksaan atas untai: `peran` bertipe `PeranKurasi`,
sehingga tidak ada tempat bagi nama untuk masuk. Pemeriksaan atas untai akan
meloloskan nama yang tidak dikenali daftarnya, dan nama yang tidak dikenali
justru yang paling mungkin milik orang sungguhan.

## Alasan penolakan tetap berkode di jejak

Putusan tolak mencatat kode TL-nya sebagai alasan, dan **catatan bebas di
sampingnya ditolak**. Kolom berkode yang berdampingan dengan untai bebas akan
menjadi hiasan: alasan yang sesungguhnya ditulis pada untainya, sedangkan
kolom kode tetap dapat dijumlahkan tanpa lagi berarti — dan D-06 Bagian 7.4
membakukannya justru agar penolakan menjadi data perbaikan.

Biayanya diakui: kurator yang ingin menambahkan rincian pada sebuah penolakan
tidak dapat melakukannya di sini. Yang tersedia baginya adalah memilih kode
yang tepat, dan bila tidak ada kode yang tepat maka yang kurang adalah daftar
TL — itu perubahan pada D-06, bukan pada baris jejak.

## Tambah-saja, dan bukan lewat `src/logbook/`

`src/logbook/` menegakkan C-09 atas **catatan percobaan** `docs/D10.md`, dan
D-10 tidak memiliki buku bagi jejak kurasi. Menulis jejak operasional ke sana
akan mencampur rekaman penelitian dengan data jalannya sistem.

Sifat tambah-sajanya diwarisi dari tempat lain: `JejakArea` pada
`src/ingest/jejak.py`, yang permukaannya sengaja tidak menyediakan cara
menyunting maupun menghapus. Yang tidak disediakan tidak dapat dipanggil
karena lupa.

Batas yang diakui terbuka: modul ini menyimpan baris di memori. Penyimpanan
tetapnya melewati `src/penyimpanan/` ketika tabel kurasi `docs/D14.md` Bagian
5 dibangun, dan itu bukan pekerjaan fitur ini.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.ingest.data_pribadi import nama_pola_yang_cocok
from src.ingest.kurasi.putusan import JenisPutusan, PeranKurasi, Putusan


class GalatJejakKurasi(Exception):
    """Baris jejak tidak layak ditulis.

    Pesannya sengaja **tidak pernah mengutip catatan yang ditolaknya**. Galat
    yang mengulang muatannya memindahkan kebocoran dari jejak ke log, yaitu
    kebalikan persis dari maksudnya — sama dengan `GalatJejak` fitur 002.
    """


@dataclass(frozen=True)
class BarisKurasi:
    """Satu tindakan kurasi — empat bidang FR-I05.

    Beku: baris jejak yang dapat diubah setelah ditulis tidak membuktikan apa
    pun tentang saat ia ditulis, dan justru itu yang ditanyakan seseorang yang
    menelusuri sebuah putusan.
    """

    peran: PeranKurasi
    """Siapa — peran, bukan orang (C-05, KM-03, R-13)."""
    waktu: datetime
    """Kapan — diambil dari putusan, bukan dari jam penulisan.

    Dua stempel waktu yang dapat berselisih menimbulkan pertanyaan mana yang
    berlaku, dan pertanyaan itu tidak memiliki jawaban yang tertulis di mana
    pun. `Putusan.waktu` sudah wajib berzona UTC.
    """
    id_butir: str
    """Apa — butir yang dinilai."""
    jenis: JenisPutusan
    """Apa — putusan yang diambil."""
    alasan: str
    """Mengapa — kode TL bagi penolakan, catatan kurator bagi selebihnya."""


class JejakKurasi:
    """Tambah saja. Sengaja tanpa metode menyunting maupun menghapus."""

    def __init__(self) -> None:
        self._baris: list[BarisKurasi] = []

    @property
    def baris(self) -> tuple[BarisKurasi, ...]:
        """Salinan beku.

        Daftar yang dikembalikan apa adanya dapat ditambahi maupun dikosongkan
        pemanggil, dan sifat tambah-saja kemudian hanya berlaku bagi yang sopan.
        """
        return tuple(self._baris)

    def catat(self, putusan: Putusan, *, catatan: str = "") -> None:
        """Tulis satu baris — R-09.

        Seluruh pemeriksaan berjalan **sebelum** baris ditambahkan. Galat yang
        tetap menulis barisnya membocorkan justru yang dilarangnya.
        """
        alasan = self._alasan(putusan, catatan)
        self._pastikan_tanpa_data_pribadi(alasan)
        self._baris.append(
            BarisKurasi(
                peran=putusan.peran_pemutus,
                waktu=putusan.waktu,
                id_butir=putusan.id_butir,
                jenis=putusan.jenis,
                alasan=alasan,
            )
        )

    @staticmethod
    def _alasan(putusan: Putusan, catatan: str) -> str:
        """Kode TL bagi penolakan; catatan kurator bagi selebihnya.

        Keduanya wajib terisi: "alasan" salah satu dari empat bidang FR-I05,
        dan persetujuan tanpa alasan adalah baris jejak yang tidak menjelaskan
        apa pun.
        """
        if putusan.alasan_tolak is not None:
            if catatan.strip():
                raise GalatJejakKurasi(
                    "penolakan sudah membawa alasannya sebagai kode baku — catatan "
                    "bebas di sampingnya membuat kode itu berhenti berarti (D-06 "
                    "Bagian 7.4, FR-I02)"
                )
            return putusan.alasan_tolak.value
        if not catatan.strip():
            raise GalatJejakKurasi(
                f"putusan {putusan.jenis.value} wajib menyertakan alasan — FR-I05 "
                "menuntut keempat bidang, dan yang kosong tidak menjelaskan apa pun"
            )
        return catatan.strip()

    @staticmethod
    def _pastikan_tanpa_data_pribadi(alasan: str) -> None:
        """R-13 — **tolak, jangan saring.**

        Menyaring diam-diam menghasilkan baris yang tampak bersih sementara
        penulisnya tidak pernah tahu ia hampir membocorkan sesuatu, dan ia akan
        menulisnya lagi.

        Nama polanya disebutkan pada galat; **nilainya tidak pernah**.
        """
        nama = nama_pola_yang_cocok(alasan)
        if nama is not None:
            raise GalatJejakKurasi(
                f"catatan memuat {nama} — sebutkan jenis temuannya, jangan salin nilainya"
            )
