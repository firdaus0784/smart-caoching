"""Gerbang karantina — R-03, R-04, R-05, FR-B05, FR-B07, ET-04, KD-02, ADR-06.

Dokumen masuk selalu ke karantina, dan hanya keluar lewat persetujuan
verifikator manusia yang tercatat. `terima` sengaja **tidak menerima parameter
area**: jalan yang tidak ada tidak dapat ditempuh keliru.

**Tiga gerbang berdiri sendiri, dan ketiganya wajib dilewati:**

1. Persetujuan pemilik dokumen (ET-04) — dinilai `Dokumen.boleh_masuk_korpus`
2. Verifikasi anonimisasi oleh manusia (FR-B05) — `setujui` di sini
3. Pemeriksa pola instruksi adversarial (FR-B08) — Fase C

Menggabungkannya menjadi satu pemeriksaan akan membuat satu kelonggaran
membuka ketiganya. Verifikator menilai anonimisasi; ia **tidak dapat
menggantikan** persetujuan pemilik, dan itu ditegakkan di sini bukan
diserahkan pada kedisiplinan.

**Penarikan persetujuan mengeluarkan dokumen dari korpus** (KB-014), bukan
sekadar mencegahnya masuk. Persetujuan yang ditarik tetapi dokumennya tetap
dipakai bukan penarikan.

Batas yang dinyatakan terbuka: fitur ini belum memiliki indeks pengambilan,
sehingga pencabutan segmen dari indeks menjadi kewajiban fitur 006 dan 007.
Tanpa itu, penarikan tampak tuntas padahal segmennya masih terindeks.
"""

from __future__ import annotations

from collections.abc import Callable

from src.ingest.adversarial import Temuan, periksa_pola
from src.ingest.dokumen import Dokumen, StatusAnonimisasi, StatusPersetujuan
from src.llm.tipe import Peringkat
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial import Kredensial


class GalatGerbang(Exception):
    """Syarat gerbang tidak terpenuhi.

    Berbeda dari `GalatAksesDitolak`: yang ini berarti kredensialnya memadai
    tetapi keadaan dokumennya belum layak berpindah.
    """


class Gerbang:
    """Satu-satunya jalan masuk dan keluar korpus."""

    def __init__(
        self,
        penyimpan: PenyimpanDasar,
        pemeriksa: Callable[[str], list[Temuan]] = periksa_pola,
    ) -> None:
        self.penyimpan = penyimpan
        self._pemeriksa = pemeriksa
        self._dokumen: dict[str, Dokumen] = {}
        self._area: dict[str, Area] = {}
        self._alasan: dict[str, str] = {}
        self._temuan: dict[str, list[Temuan]] = {}
        self._ditinjau: set[str] = set()

    def terima(self, dokumen: Dokumen, teks: str) -> None:
        """Terima dokumen baru — selalu ke karantina (R-03).

        Tidak menerima parameter area. Jalan yang tidak ada tidak dapat
        ditempuh keliru, dan itu lebih kuat daripada memeriksa nilainya.

        Pemeriksaan pola adversarial berjalan di sini, **sebelum** dokumen
        tersedia bagi siapa pun (KD-01). Menjalankannya saat persetujuan berarti
        dokumen yang disusupi sempat menunggu di antrean sebagai dokumen biasa.

        Teksnya wajib, bukan opsional. Pemeriksa yang tidak diberi bahan akan
        melapor bersih, dan laporan bersih yang tidak memeriksa apa pun adalah
        laporan palsu.
        """
        self._dokumen[dokumen.id] = dokumen
        self._area[dokumen.id] = Area.KARANTINA
        self._temuan[dokumen.id] = self._jalankan_pemeriksa(teks)
        self.penyimpan.tulis_dokumen(_KREDENSIAL_INGESTI, Area.KARANTINA, dokumen.id, teks)

    def _jalankan_pemeriksa(self, teks: str) -> list[Temuan]:
        """Jalankan pemeriksa; kegagalannya menahan, bukan meloloskan — R-10.

        Pemeriksa yang gagal lalu diperlakukan sebagai lulus adalah laporan
        palsu. Di sini akibatnya bukan gerbang yang keliru lulus melainkan
        dokumen yang disusupi masuk korpus.

        Kegagalannya menjadi temuan biasa, sehingga jalan pulihnya juga biasa:
        manusia meninjau lalu memutuskan. Tanpa itu, satu pemeriksa rusak
        menghentikan seluruh ingesti tanpa jalan keluar.
        """
        try:
            return list(self._pemeriksa(teks))
        except Exception as galat:
            return [
                Temuan(
                    pola=f"pemeriksa gagal berjalan: {type(galat).__name__}",
                    mulai=0,
                    akhir=0,
                    kutipan="",
                )
            ]

    def _pastikan_terbaca(self, kredensial: Kredensial, id_dokumen: str) -> Area:
        """Satu tempat penjagaan bagi **seluruh** keterangan tentang dokumen.

        Ia benar-benar melewati penyimpan, bukan menyalin aturannya. Aturan
        akses yang disalin adalah aturan kedua yang dapat lupa diperbarui —
        dan pemeriksaan Fase B menemukan saya sudah melakukannya sekali.

        Dokumen yang tidak dikenal dijawab sama dengan dokumen yang tidak
        terjangkau. Jawaban yang berbeda sudah cukup untuk menyusun daftar
        dokumen karantina.
        """
        area = self._area.get(id_dokumen)
        if area is None:
            raise GalatAksesDitolak(kredensial=kredensial, area=Area.KARANTINA, operasi="baca")
        self.penyimpan.baca_dokumen(kredensial, area, id_dokumen)
        return area

    def area(self, kredensial: Kredensial, id_dokumen: str) -> Area:
        """Area tempat dokumen berada — R-02.

        Digerbangi karena jawabannya sendiri adalah keterangan: siapa pun yang
        dapat menanyakan area sembarang id dapat menyusun daftar isi karantina
        tanpa membaca satu dokumen pun.
        """
        return self._pastikan_terbaca(kredensial, id_dokumen)

    def alasan_terakhir(self, kredensial: Kredensial, id_dokumen: str) -> str:
        """Alasan putusan terakhir — R-12.

        Digerbangi karena alasan penolakan secara alami memuat petunjuk isi
        dokumen: "memuat NIK pada halaman 3". Dokumennya berada di karantina,
        dan alasannya tidak boleh lebih mudah dijangkau daripada dokumennya.
        """
        self._pastikan_terbaca(kredensial, id_dokumen)
        return self._alasan.get(id_dokumen, "")

    def dokumen(self, kredensial: Kredensial, id_dokumen: str) -> Dokumen:
        """Metadata dokumen, digerbangi sama dengan yang lain."""
        self._pastikan_terbaca(kredensial, id_dokumen)
        return self._dokumen[id_dokumen]

    def temuan(self, kredensial: Kredensial, id_dokumen: str) -> list[Temuan]:
        """Temuan pola adversarial pada dokumen — digerbangi.

        Kutipan temuan memuat potongan isi dokumen, sehingga ia tidak boleh
        lebih mudah dijangkau daripada dokumennya sendiri.
        """
        self._pastikan_terbaca(kredensial, id_dokumen)
        return list(self._temuan.get(id_dokumen, []))

    def tinjau_temuan(
        self, kredensial: Kredensial, id_dokumen: str, id_peninjau: str, catatan: str
    ) -> None:
        """Tandai temuan sudah ditinjau manusia — FR-B08, KD-01.

        Ini gerbang ketiga, dan ia berdiri sendiri: persetujuan verifikator atas
        anonimisasi tidak menutupnya. Menggabungkan keduanya membuat satu
        kelonggaran membuka dua pintu.
        """
        self._pastikan_terbaca(kredensial, id_dokumen)
        if not id_peninjau:
            raise GalatGerbang("tinjauan tanpa nama peninjau tidak dapat ditelusuri")
        self._ditinjau.add(id_dokumen)
        self._alasan[id_dokumen] = catatan

    def peringkat(self, kredensial: Kredensial, id_dokumen: str) -> Peringkat:
        """Peringkat kepercayaan dokumen — hanya dari area yang dijangkau
        kredensial pemanggil (R-07a).

        D-13 Bagian 6 mendefinisikan T3 sebagai dokumen sekolah teranonimkan
        **dan terverifikasi**. Selama dokumen di karantina, kata kedua belum
        berlaku, sehingga peringkatnya belum sah bagi jalur penjawaban.

        Peringkat tidak dijaga sebagai rahasia tersendiri: ia melewati
        `_pastikan_terbaca`, yang benar-benar memanggil penyimpan. Versi
        pertama modul ini menyalin aturan aksesnya alih-alih memakainya, dan
        uraiannya mengklaim sebaliknya — tertangkap pemeriksaan Fase B.

        **Jawabannya seragam** bagi dokumen yang tidak terjangkau dan dokumen
        yang tidak ada. Jawaban yang berbeda sudah cukup untuk menyusun daftar
        dokumen karantina — kebocoran yang sama dengan yang A-6 tutup. Ini
        sengaja berbeda dari `baca_dokumen`: di sana "tidak ditemukan pada area
        yang boleh Anda baca" adalah keterangan yang memang hak pemanggil,
        sedangkan di sini pertanyaannya melintasi area.
        """
        self._pastikan_terbaca(kredensial, id_dokumen)
        return self._dokumen[id_dokumen].peringkat

    def setujui(
        self, kredensial: Kredensial, id_dokumen: str, id_verifikator: str, alasan: str
    ) -> None:
        """Pindahkan dokumen ke korpus atas persetujuan verifikator — R-04.

        Persetujuan tanpa nama verifikator ditolak: yang tidak dapat ditelusuri
        tidak dapat dipertanggungjawabkan.
        """
        if not id_verifikator:
            raise GalatGerbang("persetujuan tanpa nama verifikator tidak dapat ditelusuri")

        if self._temuan.get(id_dokumen) and id_dokumen not in self._ditinjau:
            raise GalatGerbang(
                "dokumen memuat pola instruksi adversarial dan belum ditinjau "
                "manusia — persetujuan anonimisasi tidak menggantikannya (FR-B08)"
            )

        dokumen = self._dokumen[id_dokumen]
        if not dokumen.boleh_masuk_korpus():
            raise GalatGerbang(
                "persetujuan pemilik dokumen belum ada atau sudah ditarik — "
                "verifikator tidak dapat menggantikannya (ET-04)"
            )

        self.penyimpan.pindahkan(kredensial, id_dokumen, Area.KARANTINA, Area.KORPUS, alasan)
        self._area[id_dokumen] = Area.KORPUS
        self._alasan[id_dokumen] = alasan
        self._dokumen[id_dokumen] = dokumen.model_copy(
            update={"status_anonimisasi": StatusAnonimisasi.TERVERIFIKASI}
        )

    def tolak(
        self, kredensial: Kredensial, id_dokumen: str, id_verifikator: str, alasan: str
    ) -> None:
        """Tahan dokumen di karantina beserta alasannya — R-05, FR-B07.

        Alasan wajib: penolakan tanpa alasan tidak dapat ditindaklanjuti
        pengunggahnya, sehingga dokumen yang sama akan diunggah ulang apa
        adanya.

        Kredensial diperiksa lebih dulu — menilai isi karantina menuntut hak
        membacanya. Versi pertama modul ini menerima parameter kredensial lalu
        tidak pernah memakainya, sehingga jalur penjawaban dapat menolak
        dokumen orang. Tertangkap pemeriksaan Fase B, bukan oleh uji.
        """
        self._pastikan_terbaca(kredensial, id_dokumen)
        if not id_verifikator:
            raise GalatGerbang("penolakan tanpa nama verifikator tidak dapat ditelusuri")
        if not alasan:
            raise GalatGerbang("penolakan wajib menyertakan alasan")

        self._area[id_dokumen] = Area.KARANTINA
        self._alasan[id_dokumen] = alasan
        self._dokumen[id_dokumen] = self._dokumen[id_dokumen].model_copy(
            update={"status_anonimisasi": StatusAnonimisasi.DITOLAK}
        )

    def cabut_persetujuan(self, id_dokumen: str, alasan: str) -> None:
        """Tarik persetujuan pemilik — dokumen keluar dari korpus (KB-014).

        **Tidak menuntut kredensial pemanggil.** Mencabut akses selalu aman:
        ia hanya mengurangi apa yang terjangkau, tidak pernah menambah. Menuntut
        izin untuk menarik izin adalah rintangan yang hanya menghambat pihak
        yang berhak.

        Kewenangannya juga bukan milik pemanggil melainkan milik pemilik
        dokumen. Memakai kredensial `VERIFIKASI` di sini akan keliru dua kali:
        ia menyiratkan verifikator yang memutuskan, dan ia menuntut hak tulis ke
        karantina yang sengaja tidak dimiliki verifikator — justru agar ia tidak
        dapat menyunting bahan yang sedang dinilainya.

        Berlaku seketika, tanpa menunggu peninjauan. Dokumen yang sudah di
        karantina tetap di sana; statusnya yang berubah, dan itu yang menutup
        jalan persetujuan ulang tanpa izin baru.
        """
        dokumen = self._dokumen[id_dokumen]
        self._dokumen[id_dokumen] = dokumen.model_copy(
            update={"status_persetujuan_pemilik": StatusPersetujuan.DICABUT}
        )
        self._alasan[id_dokumen] = alasan

        if self._area[id_dokumen] is Area.KORPUS:
            self.penyimpan.pindahkan(
                _KREDENSIAL_PENARIKAN, id_dokumen, Area.KORPUS, Area.KARANTINA, alasan
            )
            self._area[id_dokumen] = Area.KARANTINA


_KREDENSIAL_INGESTI = Kredensial(
    nama="ingesti",
    baca=frozenset(),
    tulis=frozenset({Area.KARANTINA}),
)
"""Kredensial jalur ingesti: menulis ke karantina, tidak membaca apa pun.

Tidak masuk `kredensial_baku.py` karena ia bukan salah satu dari tiga peran
KD-10; ia jalur mesin yang hanya menaruh berkas masuk. Himpunan bacanya kosong
— yang tidak dapat membaca tidak dapat membocorkan.
"""

_KREDENSIAL_PENARIKAN = Kredensial(
    nama="penarikan",
    baca=frozenset({Area.KORPUS}),
    tulis=frozenset({Area.KARANTINA}),
)
"""Kredensial penarikan persetujuan: memindahkan dokumen keluar dari korpus.

Arahnya satu jurusan dan itu disengaja: ia membaca korpus dan menulis
karantina, sehingga tidak dapat dipakai memasukkan apa pun ke korpus. Kemampuan
yang hanya dapat mengurangi jangkauan tidak perlu dijaga seketat kemampuan yang
dapat menambahnya.

Terpisah dari `VERIFIKASI` karena verifikator sengaja tidak memiliki hak tulis
ke karantina — agar ia tidak dapat menyunting bahan yang sedang dinilainya.
Kebutuhan akan kredensial ini ditemukan uji, bukan dirancang lebih dulu.
"""
