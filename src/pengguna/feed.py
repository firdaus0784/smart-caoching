"""Feed penemuan — R-01 s.d. R-08; FR-G01, FR-G05, FR-G07, FR-G08.

Bidang butir, waktu baca ≤ 7 menit, dan label jenis sumber (FR-G02 s.d. FR-G04)
sudah dijaga `ButirPengetahuan` fitur 010 pada tingkat tipe. Modul ini
mengerjakan yang tersisa: **menyaring, membatasi, dan menjaga lisensi**.

## Penyaringan terhadap prioritas, bukan terhadap ketertarikan

FR-G01 menyaring terhadap prioritas manajerial yang pengguna **pilih sendiri**
saat *onboarding* (FR-A03), bukan terhadap perilakunya. Perbedaannya bukan
teknis: penyaringan berbasis riwayat adalah personalisasi, dan D-01 Bagian 4.2
menempatkannya di luar siklus 2026 — C-14 melarangnya dalam bentuk apa pun.

Akibatnya diakui dan disengaja: pengguna yang prioritasnya sempit melihat feed
yang sempit, dan yang mengubahnya adalah ia sendiri lewat profilnya. Sistem
tidak melebarkannya diam-diam karena ia banyak membuka satu kategori.

## Pengguna tanpa prioritas melihat feed kosong

Bukan feed acak. Prioritas ditetapkan saat *onboarding* dan `PrioritasManajerial`
menuntut sekurangnya tiga; ketiadaannya berarti *onboarding* belum selesai, dan
menampilkan butir acak menyembunyikan itu dari penggunanya maupun dari yang
memeriksa.

## Pagu tayang memakai tetapan fitur 010

`PAGU_TAYANG_PER_PENGGUNA` sudah bernama, bernilai 3, dan **terdaftar pada
pemeriksa C-16** sejak fitur 010. Modul ini mengimpornya. Angka kedua akan
benar hari ini lalu berselisih pada hari salah satunya disetel — dan yang
disetel bukan yang diperiksa.

## Lisensi tertutup: metadata dan parafrase, tidak pernah teks penuh

FR-G08 dan C-02. `ButirPengetahuan` tidak memiliki bidang teks penuh sama
sekali — `inti_temuan` adalah parafrase yang kurator setujui, dan itu bentuk
yang menutupnya sejak fitur 010. Yang ditambahkan di sini **lapis kedua**:
butir berlisensi tertutup ditandai agar layar tahu ia tidak boleh menawarkan
unduhan, sejalan dengan cara C-07 dijaga tiga lapis.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.ingest.kurasi.butir import ButirPengetahuan
from src.ingest.kurasi.putusan import ButirTayang
from src.ingest.kurasi.tetapan import PAGU_TAYANG_PER_PENGGUNA
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.pengguna.prioritas import PrioritasManajerial

LISENSI_TERBUKA: frozenset[str] = frozenset({"CC-BY", "CC-BY-SA", "CC0", "Domain Publik"})
"""Lisensi yang teks penuhnya boleh ditawarkan — D-06 Bagian 4.

Ditulis sebagai daftar **yang diizinkan**, bukan daftar yang dilarang. Daftar
larangan meloloskan lisensi yang belum dikenalnya, dan lisensi yang belum
dikenal justru yang paling mungkin menutup.
"""


class GalatFeed(Exception):
    """Permintaan feed atau umpan balik tidak layak diproses."""


class ButirFeed(BaseModel):
    """Satu butir sebagaimana tampil pada feed — turunan `ButirTayang`.

    Membawa `boleh_teks_penuh` sebagai bidang tersendiri alih-alih menyerahkan
    layar menyimpulkannya dari untai lisensi. Kesimpulan yang diambil layar
    akan diambil berbeda oleh layar berikutnya, dan salah satunya akan keliru
    ke arah yang longgar.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    butir: ButirPengetahuan
    boleh_teks_penuh: bool
    """FR-G08, C-02 — lapis kedua. Lihat uraian modul."""


class UmpanBalikRelevansi(BaseModel):
    """ "Belum relevan sekarang" beserta alasannya — FR-G07.

    Alasannya wajib: umpan balik tanpa alasan tidak dapat dipakai memperbaiki
    penyaringan, dan yang tidak dapat dipakai memperbaiki apa pun sebaiknya
    tidak diminta.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # Tanpa ini pydantic menyalin **nilai masukan** ke dalam pesan
        # `ValidationError`, sehingga alasan yang baru ditolak karena memuat
        # data pribadi tetap muncul lewat jalur yang bukan pesan kita sendiri.
        # Aturan lintas modul, `tests/tata_kelola/`, KB-049.
        hide_input_in_errors=True,
    )

    id_pengguna: str = Field(min_length=1)
    id_butir: str = Field(min_length=1)
    alasan: str = Field(min_length=1)

    @field_validator("alasan")
    @classmethod
    def _tanpa_data_pribadi(cls, nilai: str) -> str:
        """KM-03 — tolak, jangan saring."""
        temuan = periksa_data_pribadi(nilai)
        if temuan:
            raise ValueError(
                f"alasan memuat pengenal berjenis {temuan[0].jenis} — sebutkan "
                "jenis temuannya, jangan salin nilainya"
            )
        return nilai


def _boleh_teks_penuh(butir: ButirPengetahuan) -> bool:
    return butir.lisensi.strip() in LISENSI_TERBUKA


def susun_feed(
    *,
    prioritas: PrioritasManajerial | None,
    tersedia: tuple[ButirTayang, ...],
    sudah_tayang_hari_ini: int = 0,
) -> tuple[ButirFeed, ...]:
    """Susun feed satu pengguna — R-01, R-05, R-08.

    `sudah_tayang_hari_ini` diserahkan pemanggil, bukan dihitung dari jam
    sistem: pagu harian menuntut batas hari, dan batas hari bergantung zona
    waktu penggunanya. Modul yang membacanya sendiri akan memakai zona peladen.

    Urutan keluarannya mengikuti **urutan prioritas pengguna**, bukan urutan
    butir tersedia. Posisi kategori pada `PrioritasManajerial` adalah urutan
    yang ia pilih sendiri (FR-A03), dan feed yang mengabaikannya membuat
    pilihan itu tidak berakibat apa pun.
    """
    if sudah_tayang_hari_ini < 0:
        raise GalatFeed("jumlah butir yang sudah tayang tidak dapat negatif")
    if prioritas is None:
        return ()

    sisa = PAGU_TAYANG_PER_PENGGUNA - sudah_tayang_hari_ini
    if sisa <= 0:
        return ()

    terpilih: list[ButirFeed] = []
    for kategori in prioritas.kategori:
        for tayang in tersedia:
            if tayang.butir.kategori is not kategori:
                continue
            terpilih.append(
                ButirFeed(
                    butir=tayang.butir,
                    boleh_teks_penuh=_boleh_teks_penuh(tayang.butir),
                )
            )
            if len(terpilih) == sisa:
                return tuple(terpilih)
    return tuple(terpilih)


def tandai_belum_relevan(*, id_pengguna: str, id_butir: str, alasan: str) -> UmpanBalikRelevansi:
    """Catat "belum relevan sekarang" — R-07, FR-G07.

    Umpan balik ini **tidak** mengubah penyaringan secara otomatis. Penyaringan
    yang menyesuaikan diri terhadap perilaku adalah personalisasi berbasis
    riwayat, yang C-14 larang pada siklus ini. Ia dikumpulkan bagi kurator dan
    bagi analisis, dan itu dinyatakan agar tidak ada yang menyambungkannya
    diam-diam.
    """
    bersih = alasan.strip()
    if not bersih:
        raise GalatFeed(
            "umpan balik tanpa alasan tidak dapat dipakai memperbaiki penyaringan "
            "— dan yang tidak dapat dipakai memperbaiki apa pun sebaiknya tidak diminta"
        )
    try:
        return UmpanBalikRelevansi(id_pengguna=id_pengguna, id_butir=id_butir, alasan=bersih)
    except ValueError as sebab:
        teks = str(sebab)
        if "pengenal berjenis" in teks:
            jenis = teks.split("pengenal berjenis", 1)[1].split(" -", 1)[0].strip()
            raise GalatFeed(f"alasan memuat pengenal berjenis {jenis} dan tidak disimpan") from None
        raise GalatFeed("umpan balik belum lengkap") from None


def butir_bertenggat_dekat(butir: tuple[ButirFeed, ...], *, sampai: date) -> tuple[ButirFeed, ...]:
    """Butir yang bersinggungan dengan tenggat administratif — FR-G09, sebagian.

    Hanya bagian yang dapat dikerjakan tanpa kalender manajerial: butir yang
    **membawa sendiri** `tenggat_terkait`. Bagian yang menuntut kalender D-02
    Bagian 5 belum dapat dibangun — kalendernya belum berbentuk yang terbaca
    mesin, dan usul penambahannya sudah tercatat pada `docs/D11.md` Bagian 5.

    Dinyatakan setengah dan disebut setengahnya, alih-alih dilewatkan utuh.
    """
    return tuple(
        satu
        for satu in butir
        if satu.butir.tenggat_terkait is not None and satu.butir.tenggat_terkait <= sampai
    )
