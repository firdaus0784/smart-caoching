"""Jejak perpindahan area — R-11, R-12, D-04 Bagian 7.2, D-14 Bagian 5.1, KT-04.

Setiap perpindahan dokumen antara `karantina` dan `korpus` menghasilkan satu
baris: siapa, kapan, dari mana ke mana, dengan alasannya. Tanpa jejak ini,
sebuah dokumen yang tiba-tiba berada di korpus tidak dapat dijelaskan kepada
siapa pun, dan ADR-06 kehilangan bukti bahwa pemisahannya benar-benar berjalan.

**Terpisah dari `jejak_kurasi`** (KB-011): keduanya alur berbeda dengan pemilik
berbeda — SOP kurasi milik D-06, gerbang karantina milik ADR-06 — dan
menggabungkannya membuat setiap kueri atas salah satunya harus menyaring yang
lain.

**Tambah saja.** Tidak ada metode menyunting maupun menghapus, dan itu bentuk
kendalinya, bukan kekurangan antarmukanya. Jejak yang dapat disunting bukan
bukti; ia hanya pernyataan terakhir orang yang paling belakangan menyentuhnya.

**Alasan tidak boleh memuat data pribadi** (R-12, D-14 Bagian 5.1). Di sinilah
data pribadi paling mudah bocor tanpa disadari: alasan penolakan verifikator
berbunyi alami "memuat NIK 3211... pada halaman 3", dan menyalin potongannya
terasa membantu. Akibatnya potongan itu berpindah dari karantina ke jejak —
tempat yang justru lebih mudah dibaca daripada dokumennya.

**Ditolak, bukan disaring diam-diam.** Penyaringan menghasilkan jejak yang
tampak bersih sehingga kebiasaannya tidak pernah berubah, dan verifikator tidak
pernah tahu alasannya tidak tersimpan utuh. Galat saat menulis mengubah
kebiasaan itu sekali dan seterusnya.

Batas yang dinyatakan terbuka: pencocokan pola menangkap bentuk baku NIK, NIP,
dan nomor telepon Indonesia. Ia tidak menangkap nama orang, alamat, maupun
nomor yang ditulis terurai. Pendeteksi data pribadi yang sesungguhnya adalah
FR-B04, dan ia dibangun pada fitur 015. Lapis ini menutup bentuk yang paling
sering, bukan seluruhnya.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.area import Area


class GalatJejak(Exception):
    """Baris jejak tidak layak ditulis.

    Pesannya sengaja **tidak pernah mengutip alasan yang ditolaknya**. Galat
    yang mengulang muatannya memindahkan kebocoran dari jejak ke log, yaitu
    kebalikan persis dari maksudnya.
    """


@dataclass(frozen=True)
class Baris:
    """Satu perpindahan — tujuh bidang D-04 Bagian 7.2.

    Beku: baris jejak yang dapat diubah setelah ditulis tidak membuktikan apa
    pun tentang saat ia ditulis.

    `waktu` disimpan UTC mengikuti gaya proyek. Waktu setempat pada jejak
    membuat dua baris dari dua mesin tidak dapat diurutkan.
    """

    id_dokumen: str
    id_pelaku: str
    dari_area: Area
    ke_area: Area
    alasan: str
    waktu: datetime
    id: str = field(default_factory=lambda: str(uuid4()))


class JejakArea:
    """Tambah saja. Sengaja tanpa metode menyunting maupun menghapus."""

    def __init__(self) -> None:
        self._baris: list[Baris] = []

    def catat(
        self,
        id_dokumen: str,
        id_pelaku: str,
        dari_area: Area,
        ke_area: Area,
        alasan: str,
    ) -> None:
        """Tulis satu baris — R-11.

        Seluruh pemeriksaan berjalan **sebelum** baris ditambahkan. Galat yang
        tetap menulis barisnya membocorkan justru yang dilarangnya.

        Perpindahan yang tidak berpindah tetap dicatat: dokumen yang ditahan di
        karantina adalah putusan, dan putusan menahan sama perlu ditelusuri
        dengan putusan memindahkan.
        """
        if not id_pelaku:
            raise GalatJejak("perpindahan tanpa pelaku tidak dapat dipertanggungjawabkan")
        if not alasan:
            raise GalatJejak("perpindahan wajib menyertakan alasan")
        self._pastikan_tanpa_data_pribadi(alasan)

        self._baris.append(
            Baris(
                id_dokumen=id_dokumen,
                id_pelaku=id_pelaku,
                dari_area=dari_area,
                ke_area=ke_area,
                alasan=alasan,
                waktu=datetime.now(UTC),
            )
        )

    @staticmethod
    def _pastikan_tanpa_data_pribadi(alasan: str) -> None:
        """R-12 — tolak, jangan saring.

        Nama polanya disebutkan pada galat; **nilainya tidak pernah**. Yang
        perlu diketahui verifikator adalah jenis apa yang tersalin, bukan
        pengulangan apa yang tersalin.
        """
        temuan = periksa_data_pribadi(alasan)
        if temuan:
            raise GalatJejak(
                f"alasan memuat pengenal berjenis {temuan[0].jenis} — sebutkan jenis "
                "temuannya, jangan salin nilainya"
            )

    def baris(self) -> list[Baris]:
        """Salinan, bukan daftar aslinya.

        Kekekalan tiap baris tidak menolong bila daftarnya sendiri dapat
        dikosongkan dari luar.
        """
        return list(self._baris)
