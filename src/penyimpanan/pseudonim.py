"""Peta pseudonim — R-09, C-05, KA-03, RE-05, D-04 Bagian 7.1 dan Bagian 11.

C-05 berbunyi: *"Kunci pemetaan pseudonim tidak berada pada basis data yang
sama dengan data perilaku, dan tidak terjangkau dari layanan aplikasi."*

## Dua tuntutan, dan yang kedua yang ditegakkan modul ini

Tuntutan pertama — basis data terpisah — adalah keputusan penyebaran (D-09),
bukan keputusan kode. Yang dapat ditegakkan kode adalah tuntutan kedua:
**tidak terjangkau layanan aplikasi.**

Wujudnya `KredensialPseudonim` sebagai **tipe tersendiri**, bukan nilai lain
pada `Kredensial`. Perbedaannya menentukan:

- **Nilai lain pada tipe yang sama** dijaga pemeriksaan saat jalan. Kekeliruan
  meneruskan kredensial yang salah baru terlihat ketika pemeriksaannya
  berjalan — dan pemeriksaan yang lupa dipanggil tidak menghasilkan galat apa
  pun.
- **Tipe berbeda** tidak dapat dipakaikan oleh kekeliruan pengetikan mana pun.
  Yang tidak cocok tipenya tidak sampai ke pemeriksaan.

Bentuk yang sama dengan `IndeksTujuan` yang sengaja bukan nilai ketiga pada
`Area` (fitur 006), dan alasannya sejajar.

## Peta pseudonim sengaja bukan nilai ketiga pada `Area`

Menambahkan `Area.PETA_PSEUDONIM` akan terasa rapi dan **dilarang AG-04**:
`Area` mewujudkan `dokumen_sumber.area_simpan` milik `docs/D14.md` Bagian 5.1,
yang bernilai `karantina` atau `korpus` saja.

Alasannya bukan sekadar formal. Area adalah tempat **dokumen** berada; peta
pseudonim bukan dokumen. Menaruhnya pada sumbu yang sama membuat kredensial
yang berhak membaca korpus tampak sebanding dengan kredensial yang berhak
membaca identitas — dan kesebandingan itu yang C-05 tolak.

## `src/` tidak membentuk kredensial ini, dan itulah pasalnya

Tidak ada satu pun pembentukan `KredensialPseudonim` pada `src/`. Ia dibentuk
hanya pada uji dan kelak pada lingkungan penelitian yang terpisah — dijalankan
peneliti, bukan layanan aplikasi. Itulah wujud "tidak terjangkau dari layanan
aplikasi", dan pemeriksa C-05 menegakkannya.

## Batas yang diakui terbuka

Ini pembacaan bentuk kode dan pemisahan tipe. Ia tidak menghalangi seseorang
menjalankan modul ini dari proses yang sama dengan layanan aplikasi bila ia
memang berniat; yang menutup sisanya adalah pemisahan basis data pada D-09 dan
klausul RE-05 pada nota kesepahaman. Kendali berlapis, dan tidak satu lapis
pun cukup sendiri.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.penyimpanan.sambungan import SambunganAktif


class GalatPseudonim(Exception):
    """Permintaan tidak dapat dilayani peta pseudonim."""


class KredensialPseudonim(BaseModel):
    """Kemampuan membaca peta pseudonim — **tipe tersendiri**.

    Sengaja tidak mewarisi maupun menyerupai `Kredensial`. Kesamaan bentuk akan
    mengundang seseorang menuliskan fungsi yang menerima keduanya, dan fungsi
    semacam itu adalah tempat C-05 runtuh tanpa terlihat.

    Beku: kemampuan yang dapat disunting saat jalan bukan pemisahan melainkan
    penanda.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    nama: str = Field(min_length=1)


class PetaPseudonim:
    """Pemetaan pengguna ke pseudonim — `peta_pseudonim` D-04 Bagian 7.1.

    Setiap pembacaan menuntut `KredensialPseudonim`. Tidak ada jalur yang
    membacanya tanpa kredensial, dan tidak ada nilai bawaan bagi kredensialnya
    — parameter berbawaan di sini akan berubah menjadi "tanpa kredensial
    berarti boleh" pada pemanggilan pertama yang lupa mengisinya.
    """

    def __init__(self) -> None:
        self._peta: dict[str, str] = {}

    def daftarkan(
        self, id_pengguna: str, pseudonim: str, *, kredensial: KredensialPseudonim
    ) -> None:
        """Catat satu pemetaan. Menimpa pemetaan yang sudah ada ditolak.

        Pseudonim yang berpindah pemilik membuat data perilaku lama tertaut ke
        orang yang keliru — dan itu kekeliruan yang tidak dapat diperbaiki
        sesudah pemetaan lamanya hilang.
        """
        self._pastikan_berwenang(kredensial)
        if not id_pengguna or not pseudonim:
            raise GalatPseudonim("pemetaan menuntut id pengguna dan pseudonim")
        if id_pengguna in self._peta:
            raise GalatPseudonim("pemetaan pseudonim tidak dapat ditimpa")
        if pseudonim in set(self._peta.values()):
            raise GalatPseudonim("pseudonim sudah dipakai pengguna lain")
        self._peta[id_pengguna] = pseudonim

    def pseudonim_bagi(self, id_pengguna: str, *, kredensial: KredensialPseudonim) -> str | None:
        """Pseudonim seorang pengguna, atau `None` bila belum terdaftar."""
        self._pastikan_berwenang(kredensial)
        return self._peta.get(id_pengguna)

    def id_pengguna_bagi(self, pseudonim: str, *, kredensial: KredensialPseudonim) -> str | None:
        """**Arah balik — inilah yang C-05 lindungi.**

        Telemetri menyimpan pseudonim; yang mengubahnya kembali menjadi
        identitas adalah fungsi ini, dan ia satu-satunya. Layanan aplikasi
        tidak memiliki tipe kredensial untuk memanggilnya.
        """
        self._pastikan_berwenang(kredensial)
        for id_pengguna, nilai in self._peta.items():
            if nilai == pseudonim:
                return id_pengguna
        return None

    @staticmethod
    def _pastikan_berwenang(kredensial: KredensialPseudonim) -> None:
        """Pemeriksaan kedua, sesudah tipe.

        Tipe sudah menutup kekeliruan pengetikan; ini menutup kredensial yang
        dibentuk tanpa nama — bentuk yang muncul ketika seseorang menyusunnya
        asal ada.
        """
        if not isinstance(kredensial, KredensialPseudonim):
            raise GalatPseudonim("peta pseudonim menuntut kredensialnya sendiri")
        if not kredensial.nama.strip():
            raise GalatPseudonim("kredensial tanpa nama tidak dapat ditelusuri")


class PetaPseudonimPostgres:
    """Peta pseudonim di atas basis data **kedua** — T-5 fitur 024, C-05.

    ## Dua tuntutan C-05, dan yang menegakkan masing-masing

    *"Tidak berada pada basis data yang sama dengan data perilaku."* Ditegakkan
    **peladen**, bukan kelas ini: `REVOKE CONNECT` pada `01-peran-dan-basis-
    data.sql` membuat peran jalur penjawaban tidak dapat menyambung ke basis
    data ini sama sekali. Kelas yang menegakkan keterpisahan basis data dengan
    memeriksa nama basis datanya sendiri hanya memeriksa untai.

    *"Tidak terjangkau dari layanan aplikasi."* Ditegakkan `KredensialPseudonim`
    yang **tidak boleh dibentuk di mana pun pada `src/`** — dijaga pemeriksa
    C-05 aturan 1. Layanan aplikasi tidak memiliki cara membuat argumen yang
    dituntut setiap metode di sini.

    ## Mengapa kelas ini tinggal pada berkas yang sama

    Pemeriksa C-05 aturan 2 melarang `PetaPseudonim` diimpor modul lain pada
    `src/`. Menaruh varian PostgreSQL pada berkas tersendiri akan menuntut
    impor itu, dan pemeriksanya benar untuk menolaknya: modul yang mengimpor
    peta sudah cukup dekat untuk memanggilnya dengan kredensial yang
    diteruskan dari tempat lain.

    Kesamaan bentuknya dengan `PetaPseudonim` disalin dengan sadar, alasan yang
    sejajar dengan kedua tipe konfigurasi pada `sambungan.py`.
    """

    def __init__(self, sambungan: SambunganAktif) -> None:
        self._sambungan = sambungan

    async def daftarkan(
        self, id_pengguna: str, pseudonim: str, *, kredensial: KredensialPseudonim
    ) -> None:
        """Catat satu pemetaan. Menimpa pemetaan yang sudah ada ditolak.

        Penolakannya datang dari **batasan unik basis data**, bukan dari
        pembacaan lebih dulu. Membaca lalu menulis meninggalkan celah antara
        keduanya, dan celah itu tepat tempat dua pendaftaran bersamaan
        menghasilkan satu pseudonim milik dua orang.
        """
        PetaPseudonim._pastikan_berwenang(kredensial)
        if not id_pengguna or not pseudonim:
            raise GalatPseudonim("pemetaan menuntut id pengguna dan pseudonim")
        try:
            await self._sambungan.execute(
                "INSERT INTO pseudonim.peta_pseudonim (id_pengguna, pseudonim) VALUES ($1, $2)",
                id_pengguna,
                pseudonim,
            )
        except Exception as galat:  # batasan unik — kedua arah
            raise GalatPseudonim("pemetaan pseudonim tidak dapat ditimpa") from galat

    async def pseudonim_bagi(
        self, id_pengguna: str, *, kredensial: KredensialPseudonim
    ) -> str | None:
        PetaPseudonim._pastikan_berwenang(kredensial)
        baris = await self._sambungan.fetchrow(
            "SELECT pseudonim FROM pseudonim.peta_pseudonim WHERE id_pengguna = $1",
            id_pengguna,
        )
        return None if baris is None else str(baris["pseudonim"])

    async def id_pengguna_bagi(
        self, pseudonim: str, *, kredensial: KredensialPseudonim
    ) -> str | None:
        """**Arah balik — inilah yang C-05 lindungi.**

        Telemetri menyimpan pseudonim; yang mengubahnya kembali menjadi
        identitas adalah fungsi ini, dan ia satu-satunya pada pelaksana ini.
        """
        PetaPseudonim._pastikan_berwenang(kredensial)
        baris = await self._sambungan.fetchrow(
            "SELECT id_pengguna FROM pseudonim.peta_pseudonim WHERE pseudonim = $1",
            pseudonim,
        )
        return None if baris is None else str(baris["id_pengguna"])
