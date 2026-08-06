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

from src.ingest.dokumen import Dokumen, StatusPersetujuan
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import PenyimpanDasar
from src.penyimpanan.kredensial import Kredensial


class GalatGerbang(Exception):
    """Syarat gerbang tidak terpenuhi.

    Berbeda dari `GalatAksesDitolak`: yang ini berarti kredensialnya memadai
    tetapi keadaan dokumennya belum layak berpindah.
    """


class Gerbang:
    """Satu-satunya jalan masuk dan keluar korpus."""

    def __init__(self, penyimpan: PenyimpanDasar) -> None:
        self.penyimpan = penyimpan
        self._dokumen: dict[str, Dokumen] = {}
        self._area: dict[str, Area] = {}
        self._alasan: dict[str, str] = {}

    def terima(self, dokumen: Dokumen, isi: object) -> None:
        """Terima dokumen baru — selalu ke karantina (R-03).

        Tidak menerima parameter area. Jalan yang tidak ada tidak dapat
        ditempuh keliru, dan itu lebih kuat daripada memeriksa nilainya.
        """
        self._dokumen[dokumen.id] = dokumen
        self._area[dokumen.id] = Area.KARANTINA
        self.penyimpan.tulis_dokumen(_KREDENSIAL_INGESTI, Area.KARANTINA, dokumen.id, isi)

    def area(self, id_dokumen: str) -> Area:
        return self._area[id_dokumen]

    def alasan_terakhir(self, id_dokumen: str) -> str:
        return self._alasan.get(id_dokumen, "")

    def setujui(
        self, kredensial: Kredensial, id_dokumen: str, id_verifikator: str, alasan: str
    ) -> None:
        """Pindahkan dokumen ke korpus atas persetujuan verifikator — R-04.

        Persetujuan tanpa nama verifikator ditolak: yang tidak dapat ditelusuri
        tidak dapat dipertanggungjawabkan.
        """
        if not id_verifikator:
            raise GalatGerbang("persetujuan tanpa nama verifikator tidak dapat ditelusuri")

        dokumen = self._dokumen[id_dokumen]
        if not dokumen.boleh_masuk_korpus():
            raise GalatGerbang(
                "persetujuan pemilik dokumen belum ada atau sudah ditarik — "
                "verifikator tidak dapat menggantikannya (ET-04)"
            )

        self.penyimpan.pindahkan(kredensial, id_dokumen, Area.KARANTINA, Area.KORPUS, alasan)
        self._area[id_dokumen] = Area.KORPUS
        self._alasan[id_dokumen] = alasan

    def tolak(
        self, kredensial: Kredensial, id_dokumen: str, id_verifikator: str, alasan: str
    ) -> None:
        """Tahan dokumen di karantina beserta alasannya — R-05, FR-B07.

        Alasan wajib: penolakan tanpa alasan tidak dapat ditindaklanjuti
        pengunggahnya, sehingga dokumen yang sama akan diunggah ulang apa
        adanya.
        """
        if not id_verifikator:
            raise GalatGerbang("penolakan tanpa nama verifikator tidak dapat ditelusuri")
        if not alasan:
            raise GalatGerbang("penolakan wajib menyertakan alasan")

        self._area[id_dokumen] = Area.KARANTINA
        self._alasan[id_dokumen] = alasan

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
