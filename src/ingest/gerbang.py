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

Batas yang dinyatakan terbuka pada fitur 002 — pencabutan segmen dari indeks
— tidak pernah dibangun fitur 006 maupun 007 (TK-84). Sejak fitur 037 segmen
dokumen yang keluar dari korpus ikut terhapus dari kedua indeks dalam
pernyataan pemindahannya.

**Keadaan tinggal pada catatan, aturan tinggal di sini** (fitur 037, P-1 A).
Kamus di memori fitur 002 diganti `CatatanGerbang`: pelaksana memori bagi uji
dan pengembangan, PostgreSQL bagi perkakas yang dijalankan per perintah.
Keadaannya diturunkan dari catatan tambah-saja. Tanpa catatan yang diberikan,
gerbang memakai pelaksana memori di atas penyimpan dokumennya — jalur fitur
002 apa adanya.

**Teks disamarkan sebelum apa pun** (P-5 A): enam pengenal berpola diganti
token D-03, pemeriksa pola berjalan atas teks tersamar, dan teks aslinya tidak
diteruskan ke penyimpan mana pun. Nama dan alamat tidak tersamarkan (BT-70).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.ingest.adversarial import Temuan, periksa_pola
from src.ingest.dokumen import Dokumen, StatusAnonimisasi, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.jejak import JejakArea
from src.ingest.peringkat import JenisSumber
from src.kamus.segmen import Peringkat
from src.nlp.anonimisasi.samaran import samarkan
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import MetadataDokumen, PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenDiKorpus, GalatDokumenTidakAda
from src.penyimpanan.karantina import (
    CatatanGerbang,
    CatatanGerbangMemori,
    CatatanPenerimaan,
    KeadaanKarantina,
    TemuanPola,
)
from src.penyimpanan.kredensial import Kredensial


class GalatGerbang(Exception):
    """Syarat gerbang tidak terpenuhi.

    Berbeda dari `GalatAksesDitolak`: yang ini berarti kredensialnya memadai
    tetapi keadaan dokumennya belum layak berpindah.
    """


@dataclass(frozen=True)
class HasilTerima:
    """Yang diketahui `terima` tentang unggahannya sendiri — jumlah, tanpa
    nilai maupun kutipan. Peran ingesti tidak dapat membaca karantina, sehingga
    ringkasan ini satu-satunya laporan bagi pengunggah (fitur 037)."""

    samaran: dict[str, int]
    jumlah_temuan: int


@dataclass(frozen=True)
class RingkasanKarantina:
    """Satu baris perintah `daftar` perkakas — tanpa teks maupun kutipan."""

    dokumen: Dokumen
    jumlah_temuan: int
    ditinjau: bool
    samaran: dict[str, int]


class Gerbang:
    """Satu-satunya jalan masuk dan keluar korpus."""

    def __init__(
        self,
        penyimpan: PenyimpanDasar,
        pemeriksa: Callable[[str], list[Temuan]] = periksa_pola,
        catatan: CatatanGerbang | None = None,
    ) -> None:
        """`catatan` dipilih pemanggil. Tanpanya, pelaksana memori di atas
        `penyimpan` — jalur fitur 002. Perkakas yang dijalankan per perintah
        wajib memberinya pelaksana PostgreSQL, atau keadaannya hilang bersama
        prosesnya.

        `jejak` mencatat putusan yang dijalankan objek ini; jejak yang
        bertahan tinggal pada catatan (`karantina.jejak_area`).
        """
        self.penyimpan = penyimpan
        self.jejak = JejakArea()
        self._pemeriksa = pemeriksa
        self._catatan = catatan if catatan is not None else CatatanGerbangMemori(penyimpan)

    async def terima(self, dokumen: Dokumen, teks: str, *, id_penerima: str = "") -> HasilTerima:
        """Terima dokumen baru — selalu ke karantina (R-03).

        Tidak menerima parameter area. Jalan yang tidak ada tidak dapat
        ditempuh keliru, dan itu lebih kuat daripada memeriksa nilainya.

        Pemeriksaan pola adversarial berjalan di sini, **sebelum** dokumen
        tersedia bagi siapa pun (KD-01). Menjalankannya saat persetujuan berarti
        dokumen yang disusupi sempat menunggu di antrean sebagai dokumen biasa.

        Teksnya wajib, bukan opsional. Pemeriksa yang tidak diberi bahan akan
        melapor bersih, dan laporan bersih yang tidak memeriksa apa pun adalah
        laporan palsu.

        **Unggahan membatalkan tinjauan sebelumnya.** Tinjauan menilai isi
        tertentu; isi baru adalah isi yang belum dinilai siapa pun. Tanpa
        pembatalan ini terbuka jalan pintas yang lurus: unggah versi bersih,
        minta ditinjau, lalu unggah ulang versi yang disusupi — AN-01 tepat
        pada gerbang yang dibangun menahannya. Cacat ini nyata, lolos 129 uji,
        dan tertangkap pemeriksaan Fase C.

        Pembatalannya berlaku pada setiap unggahan, **bukan hanya ketika
        temuan muncul**. Aturan yang bersyarat temuan akan gagal justru pada
        isi yang tampak bersih bagi pemeriksa — dan cakupan pemeriksa memang
        tipis (lihat `src.ingest.adversarial`).

        **Fitur 037.** Teks disamarkan lebih dulu, dan pemeriksa berjalan atas
        hasilnya, sehingga kutipan temuan tidak membawa pengenal (P-5 A).
        Dokumen yang sedang di korpus tidak dapat diunggah ulang dengan id yang
        sama (TK-85 A): versi lama akan tertinggal di korpus tanpa terjangkau
        penarikan persetujuan. `id_penerima` kode anggota tim (P-6 A); jalur
        memori fitur 002 menerimanya kosong, catatan PostgreSQL tidak.
        """
        hasil = samarkan(teks)
        temuan = self._jalankan_pemeriksa(hasil.teks)
        penerimaan = CatatanPenerimaan(
            id_dokumen=dokumen.id,
            judul=dokumen.judul,
            jenis=dokumen.jenis.value,
            penerbit=dokumen.penerbit,
            tahun=dokumen.tahun,
            tingkat_kerahasiaan=dokumen.tingkat_kerahasiaan.value,
            status_persetujuan_pemilik=dokumen.status_persetujuan_pemilik.value,
            samaran=hasil.jumlah,
            id_penerima=id_penerima,
        )
        try:
            await self._catatan.terima(
                _KREDENSIAL_INGESTI,
                penerimaan,
                hasil.teks,
                [TemuanPola(t.pola, t.mulai, t.akhir, t.kutipan) for t in temuan],
            )
        except GalatDokumenDiKorpus as galat:
            raise GalatGerbang(
                "dokumen ini sedang berada di korpus — versi baru diterima dengan id baru (TK-85 A)"
            ) from galat
        return HasilTerima(samaran=hasil.jumlah, jumlah_temuan=len(temuan))

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

    async def _pastikan_terbaca(self, kredensial: Kredensial, id_dokumen: str) -> KeadaanKarantina:
        """Satu tempat penjagaan bagi **seluruh** keterangan tentang dokumen.

        Ia benar-benar melewati penyimpan, bukan menyalin aturannya. Aturan
        akses yang disalin adalah aturan kedua yang dapat lupa diperbarui —
        dan pemeriksaan Fase B menemukan saya sudah melakukannya sekali.

        Dokumen yang tidak dikenal dijawab sama dengan dokumen yang tidak
        terjangkau. Jawaban yang berbeda sudah cukup untuk menyusun daftar
        dokumen karantina.
        """
        keadaan = await self._catatan.keadaan(id_dokumen)
        if keadaan is None:
            raise GalatAksesDitolak(kredensial=kredensial, area=Area.KARANTINA, operasi="baca")
        await self.penyimpan.baca_dokumen(kredensial, keadaan.area, id_dokumen)
        return keadaan

    async def area(self, kredensial: Kredensial, id_dokumen: str) -> Area:
        """Area tempat dokumen berada — R-02.

        Digerbangi karena jawabannya sendiri adalah keterangan: siapa pun yang
        dapat menanyakan area sembarang id dapat menyusun daftar isi karantina
        tanpa membaca satu dokumen pun.
        """
        return (await self._pastikan_terbaca(kredensial, id_dokumen)).area

    async def alasan_terakhir(self, kredensial: Kredensial, id_dokumen: str) -> str:
        """Alasan putusan terakhir — R-12.

        Digerbangi karena alasan penolakan secara alami memuat petunjuk isi
        dokumen: "memuat NIK pada halaman 3". Dokumennya berada di karantina,
        dan alasannya tidak boleh lebih mudah dijangkau daripada dokumennya.
        """
        return (await self._pastikan_terbaca(kredensial, id_dokumen)).alasan_terakhir

    async def dokumen(self, kredensial: Kredensial, id_dokumen: str) -> Dokumen:
        """Metadata dokumen, digerbangi sama dengan yang lain."""
        return _dokumen_dari(await self._pastikan_terbaca(kredensial, id_dokumen))

    async def daftar(self, kredensial: Kredensial) -> list[RingkasanKarantina]:
        """Dokumen yang kini di karantina — fitur 037, perintah `daftar`.

        Menuntut kredensial pembaca karantina **sebelum** catatan dibaca:
        daftar isi karantina adalah keterangan yang sama dengan isinya bagi
        siapa pun yang tidak berhak (C-03). Tanpa teks maupun kutipan temuan.
        """
        if not kredensial.boleh_baca(Area.KARANTINA):
            raise GalatAksesDitolak(kredensial=kredensial, area=Area.KARANTINA, operasi="baca")
        return [
            RingkasanKarantina(
                dokumen=_dokumen_dari(k),
                jumlah_temuan=len(k.temuan),
                ditinjau=k.ditinjau,
                samaran=dict(k.penerimaan.samaran),
            )
            for k in await self._catatan.daftar()
        ]

    async def samaran(self, kredensial: Kredensial, id_dokumen: str) -> dict[str, int]:
        """Jumlah samaran per jenis pada unggahan terbaru — fitur 037, P-5 A.

        Digerbangi seperti temuan: jumlah pengenal pada sebuah dokumen adalah
        keterangan tentang isinya. Nilainya tidak pernah tersimpan.
        """
        return dict((await self._pastikan_terbaca(kredensial, id_dokumen)).penerimaan.samaran)

    async def temuan(self, kredensial: Kredensial, id_dokumen: str) -> list[Temuan]:
        """Temuan pola adversarial pada dokumen — digerbangi.

        Kutipan temuan memuat potongan isi dokumen, sehingga ia tidak boleh
        lebih mudah dijangkau daripada dokumennya sendiri.
        """
        keadaan = await self._pastikan_terbaca(kredensial, id_dokumen)
        return [Temuan(t.pola, t.mulai, t.akhir, t.kutipan) for t in keadaan.temuan]

    async def tinjau_temuan(
        self, kredensial: Kredensial, id_dokumen: str, id_peninjau: str, catatan: str
    ) -> None:
        """Tandai temuan sudah ditinjau manusia — FR-B08, KD-01.

        Ini gerbang ketiga, dan ia berdiri sendiri: persetujuan verifikator atas
        anonimisasi tidak menutupnya. Menggabungkan keduanya membuat satu
        kelonggaran membuka dua pintu.

        **Dokumen tanpa temuan tidak dapat ditinjau.** Menandai "sudah
        ditinjau" pada dokumen bersih tidak tampak aneh sama sekali, dan
        justru itu yang membuatnya berguna sebagai langkah pertama jalan
        pintas unggah-ulang. Tanda yang tidak menandai apa pun sebaiknya tidak
        dapat dibuat.

        Catatan tinjauan disimpan **terpisah** dari alasan putusan verifikator.
        Versi pertama menimpanya, sehingga catatan "kutipan sah" menghapus
        "memuat NIK pada halaman 3" — verifikator berikutnya kehilangan justru
        keterangan yang paling perlu diketahuinya. Dua putusan, dua bidang.
        """
        keadaan = await self._pastikan_terbaca(kredensial, id_dokumen)
        if not id_peninjau:
            raise GalatGerbang("tinjauan tanpa nama peninjau tidak dapat ditelusuri")
        if not keadaan.temuan:
            raise GalatGerbang("dokumen tanpa temuan tidak memiliki apa pun untuk ditinjau")
        await self._catatan.tinjau(kredensial, id_dokumen, id_peninjau, catatan)

    async def catatan_tinjauan(self, kredensial: Kredensial, id_dokumen: str) -> str:
        """Catatan peninjau atas temuan — digerbangi.

        Catatan tinjauan menyebut isi dokumen karantina hampir selalu; ia
        menjelaskan mengapa sebuah kutipan dianggap sah. Ia tidak boleh lebih
        mudah dijangkau daripada kutipan yang dibicarakannya.
        """
        return (await self._pastikan_terbaca(kredensial, id_dokumen)).catatan_tinjauan

    async def sudah_ditinjau(self, kredensial: Kredensial, id_dokumen: str) -> bool:
        """Apakah temuan dokumen sudah ditinjau manusia — digerbangi.

        Jawabannya menyiratkan dokumen itu bertemuan, dan itu keterangan
        tentang isi karantina.
        """
        return (await self._pastikan_terbaca(kredensial, id_dokumen)).ditinjau

    async def peringkat(self, kredensial: Kredensial, id_dokumen: str) -> Peringkat:
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
        return _dokumen_dari(await self._pastikan_terbaca(kredensial, id_dokumen)).peringkat

    async def setujui(
        self, kredensial: Kredensial, id_dokumen: str, id_verifikator: str, alasan: str
    ) -> None:
        """Pindahkan dokumen ke korpus atas persetujuan verifikator — R-04.

        Persetujuan tanpa nama verifikator ditolak: yang tidak dapat ditelusuri
        tidak dapat dipertanggungjawabkan.

        **Jejak ditulis sebelum dokumen berpindah** (R-11). Alasan yang memuat
        data pribadi membatalkan seluruh persetujuannya, bukan hanya jejaknya:
        memindahkan dokumen lalu gagal menjejakkannya menghasilkan perubahan
        yang tidak tercatat, persis keadaan yang R-11 larang.

        **Metadata asal ikut pemindahan** (TK-82 A, fitur 032): yang tercatat
        adalah `Dokumen` yang baru saja diperiksa `boleh_masuk_korpus`, bukan
        salinan yang diketik ulang orang. Aturan gerbang tidak berubah.

        **Fitur 037: jejak diperiksa dulu, ditulis bersama pemindahan** (R-06).
        Alasan berdata pribadi tetap membatalkan persetujuan sebelum apa pun
        tersentuh; pemindahan yang gagal tidak lagi meninggalkan baris jejak
        tanpa perpindahan.
        """
        if not id_verifikator:
            raise GalatGerbang("persetujuan tanpa nama verifikator tidak dapat ditelusuri")

        keadaan = await self._catatan.keadaan(id_dokumen)
        if keadaan is None:
            raise GalatDokumenTidakAda(id_dokumen)

        if keadaan.temuan and not keadaan.ditinjau:
            raise GalatGerbang(
                "dokumen memuat pola instruksi adversarial dan belum ditinjau "
                "manusia — persetujuan anonimisasi tidak menggantikannya (FR-B08)"
            )

        dokumen = _dokumen_dari(keadaan)
        if not dokumen.boleh_masuk_korpus():
            raise GalatGerbang(
                "persetujuan pemilik dokumen belum ada atau sudah ditarik — "
                "verifikator tidak dapat menggantikannya (ET-04)"
            )

        self.jejak.periksa(id_pelaku=id_verifikator, alasan=alasan)
        await self._catatan.setujui(
            kredensial, id_dokumen, id_verifikator, alasan, _metadata(dokumen)
        )
        self.jejak.catat(
            id_dokumen=id_dokumen,
            id_pelaku=id_verifikator,
            dari_area=Area.KARANTINA,
            ke_area=Area.KORPUS,
            alasan=alasan,
        )

    async def tolak(
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

        **Fitur 037: hanya atas dokumen di karantina.** Penolakan tidak
        memindahkan apa pun; atas dokumen korpus ia hanya akan mencatat jejak
        berarah korpus ke karantina tanpa perpindahan — keadaan yang jejaknya
        sendiri menyangkal. Dokumen korpus dikeluarkan lewat pencabutan.
        """
        keadaan = await self._pastikan_terbaca(kredensial, id_dokumen)
        if not id_verifikator:
            raise GalatGerbang("penolakan tanpa nama verifikator tidak dapat ditelusuri")
        if not alasan:
            raise GalatGerbang("penolakan wajib menyertakan alasan")
        if keadaan.area is not Area.KARANTINA:
            raise GalatGerbang("dokumen sudah di korpus — keluarkan lewat pencabutan persetujuan")

        self.jejak.periksa(id_pelaku=id_verifikator, alasan=alasan)
        await self._catatan.tolak(kredensial, id_dokumen, id_verifikator, alasan)
        self.jejak.catat(
            id_dokumen=id_dokumen,
            id_pelaku=id_verifikator,
            dari_area=Area.KARANTINA,
            ke_area=Area.KARANTINA,
            alasan=alasan,
        )

    async def cabut_persetujuan(self, id_dokumen: str, id_pemohon: str, alasan: str) -> None:
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

        **`id_pemohon` wajib meski kredensial tidak.** Keduanya menjawab
        pertanyaan berbeda: kredensial menjawab "bolehkah", `id_pemohon`
        menjawab "siapa". Penarikan selalu boleh, tetapi korpus yang menyusut
        tanpa nama di jejaknya tetap korpus yang menyusut tanpa penjelasan
        (R-11).

        Yang dicatat adalah pihak yang menjalankan penarikan, bukan pemilik
        dokumen. Identitas pemilik berasal dari formulir persetujuan ET-02,
        yang belum dibangun pada fitur ini.

        **Fitur 037: satu pernyataan.** Pencatatan dan pengeluaran dari korpus
        — beserta segmennya dari kedua indeks (TK-84 A) — terjadi bersama,
        tanpa celah antara membaca area dan mencatatnya.
        """
        self.jejak.periksa(id_pelaku=id_pemohon, alasan=alasan)
        dari = await self._catatan.cabut(_KREDENSIAL_PENARIKAN, id_dokumen, id_pemohon, alasan)
        self.jejak.catat(
            id_dokumen=id_dokumen,
            id_pelaku=id_pemohon,
            dari_area=dari,
            ke_area=Area.KARANTINA,
            alasan=alasan,
        )


def _dokumen_dari(keadaan: KeadaanKarantina) -> Dokumen:
    """`Dokumen` sebagaimana gerbang memandangnya kini: metadata penerimaan
    terbaru, dengan status yang diturunkan dari catatan — bukan yang diisi
    pengunggah."""
    p = keadaan.penerimaan
    return Dokumen(
        id=p.id_dokumen,
        judul=p.judul,
        jenis=JenisSumber(p.jenis),
        penerbit=p.penerbit,
        tahun=p.tahun,
        tingkat_kerahasiaan=TingkatKerahasiaan(p.tingkat_kerahasiaan),
        status_persetujuan_pemilik=(
            StatusPersetujuan.DICABUT
            if keadaan.persetujuan_dicabut
            else StatusPersetujuan(p.status_persetujuan_pemilik)
        ),
        status_anonimisasi=StatusAnonimisasi(keadaan.status_anonimisasi),
    )


def _metadata(dokumen: Dokumen) -> MetadataDokumen:
    """Metadata asal sebagaimana dicatat korpus — nilai enum, bukan enumnya."""
    return MetadataDokumen(
        judul=dokumen.judul,
        jenis=dokumen.jenis.value,
        penerbit=dokumen.penerbit,
        tahun=dokumen.tahun,
        tingkat_kerahasiaan=dokumen.tingkat_kerahasiaan.value,
    )


_KREDENSIAL_INGESTI = Kredensial(
    nama="ingesti",
    baca=frozenset(),
    tulis=frozenset({Area.KARANTINA}),
    indeks=frozenset(),
    tulis_indeks=frozenset(),
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
    indeks=frozenset(),
    tulis_indeks=frozenset(),
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
