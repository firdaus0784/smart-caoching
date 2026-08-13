"""Riwayat percakapan — R-13, R-14, FR-F09, `docs/D14.md` Bagian 3.2.

FR-F09: *"Sistem menyimpan riwayat percakapan dan memungkinkan pengguna
melanjutkan sesi sebelumnya."*

## Riwayat menyimpan rujukan, bukan salinan tanggapan

Ini keputusan yang paling mudah dibalik dan paling mahal bila dibalik.

Tanggapan yang tersimpan **menua**. Status keberlakuan sitasinya berubah
ketika regulasi sumbernya dicabut — dan penarikan itu memang terjadi, fitur 010
membangunnya. Riwayat yang menayangkan salinan lama menayangkan klaim atas
regulasi yang tidak berlaku, melanggar C-07 lewat pintu yang tidak dijaga
siapa pun: validator tidak pernah dipanggil ulang, sebab tidak ada yang
dianggap sedang menjawab.

Yang disimpan karena itu pertanyaan dan `id_pesan`. Isinya disusun ulang saat
dibuka, melewati jalur yang sama dengan jawaban pertama.

Biayanya diakui: membuka riwayat berbiaya sama dengan bertanya. Itu bukan efek
samping yang disesali melainkan harga dari jawaban yang selalu berlaku, dan
D-02 titik kritis T1 menetapkan jawaban yang keliru lebih mahal daripada
jawaban yang lambat.

## Tambah-saja

Permukaannya tidak menyediakan cara menyunting maupun menghapus baris —
mengikuti `JejakArea` (002), `JejakKurasi` (010), dan `Telemetri` (012). Yang
tidak disediakan tidak dapat dipanggil karena lupa.

Penghapusan data pengguna (NFR-09, `DELETE /api/v1/saya/data`) adalah hal lain
dan **tidak** dibangun di sini: ia menghapus seluruh riwayat seseorang sebagai
satu tindakan bercatat, bukan menyunting baris. Menyediakan `hapus_baris` di
sini akan membuat keduanya terlihat sebagai operasi yang sama.

## Tanpa `id_pengguna`

Sama dengan `Peristiwa` fitur 012: yang tidak ada tidak dapat terisi. Pemilik
percakapan adalah kunci penyimpanannya, dan pemetaan itu tinggal di
`src/penyimpanan/` bersama kunci pseudonim yang C-05 pisahkan.

## Batas yang diakui terbuka

Di memori. Penyimpanan tetapnya menunggu penggerak PostgreSQL (C-12,
`usulan-ketergantungan.md` Bagian 9.3), dan itu bukan pekerjaan fitur ini.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.nlp.anonimisasi.pola import periksa_data_pribadi


class GalatPercakapan(Exception):
    """Baris riwayat tidak layak disimpan.

    Pesannya **tidak pernah mengutip muatan yang ditolaknya** — sama dengan
    `GalatJejak` (002) dan `GalatJejakKurasi` (010). Galat yang mengulang
    muatannya memindahkan kebocoran dari riwayat ke log, yaitu kebalikan persis
    dari maksudnya.
    """


class Giliran(BaseModel):
    """Satu pertanyaan beserta rujukan jawabannya — **bukan jawabannya**.

    Beku: baris riwayat yang dapat diubah setelah ditulis tidak membuktikan apa
    pun tentang apa yang sungguh ditanyakan.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # Tanpa ini pydantic menyalin **nilai masukan** ke dalam pesan
        # `ValidationError`, sehingga pertanyaan yang baru saja ditolak karena
        # memuat data pribadi tetap muncul — lewat jalur yang bukan pesan yang
        # kita tulis. Aturan lintas modul, `tests/tata_kelola/`, KB-049.
        hide_input_in_errors=True,
    )

    pertanyaan: str = Field(min_length=1)
    id_pesan: str = Field(min_length=1)
    """Rujukan ke tanggapan, bukan salinannya — lihat uraian modul."""
    waktu: datetime

    @field_validator("waktu")
    @classmethod
    def _berzona_utc(cls, nilai: datetime) -> datetime:
        """Waktu tanpa zona tidak dapat dibandingkan dengan waktu berzona, dan
        perbandingan itu yang menyusun urutan giliran."""
        if nilai.tzinfo is None or nilai.utcoffset() != UTC.utcoffset(None):
            raise ValueError("waktu wajib berzona UTC")
        return nilai

    @field_validator("pertanyaan")
    @classmethod
    def _tanpa_data_pribadi(cls, nilai: str) -> str:
        """KM-03 — **tolak, jangan saring.**

        Menyaring diam-diam menghasilkan baris yang tampak bersih sementara
        penulisnya tidak pernah tahu ia hampir membocorkan sesuatu, dan ia akan
        menulisnya lagi. Nama polanya disebutkan; **nilainya tidak pernah**.
        """
        temuan = periksa_data_pribadi(nilai)
        if temuan:
            raise ValueError(
                f"pertanyaan memuat pengenal berjenis {temuan[0].jenis} — sebutkan "
                "jenis temuannya, jangan salin nilainya"
            )
        return nilai


class Percakapan:
    """Satu sesi. Tambah saja, sengaja tanpa metode menyunting maupun menghapus."""

    def __init__(self, id_percakapan: str) -> None:
        if not id_percakapan.strip():
            raise GalatPercakapan("percakapan tanpa pengenal tidak dapat dilanjutkan")
        self._id = id_percakapan
        self._giliran: list[Giliran] = []

    @property
    def id_percakapan(self) -> str:
        return self._id

    @property
    def giliran(self) -> tuple[Giliran, ...]:
        """Salinan beku.

        Daftar yang dikembalikan apa adanya dapat ditambahi maupun dikosongkan
        pemanggil, dan sifat tambah-saja kemudian hanya berlaku bagi yang sopan.
        """
        return tuple(self._giliran)

    def catat(self, *, pertanyaan: str, id_pesan: str, waktu: datetime) -> None:
        """Tambahkan satu giliran — R-13.

        Seluruh pemeriksaan berjalan **sebelum** baris ditambahkan. Galat yang
        tetap menulis barisnya membocorkan justru yang dilarangnya.
        """
        try:
            giliran = Giliran(pertanyaan=pertanyaan, id_pesan=id_pesan, waktu=waktu)
        except ValidationError as sebab:
            # Rantai sebabnya **diputus** (`from None`): `ValidationError`
            # pydantic membawa keterangan tentang muatan yang baru ditolak, dan
            # jejak tumpukan yang mengulangnya memindahkan kebocoran dari
            # riwayat ke log. Bentuk yang sama dengan gerbang telemetri (012).
            raise GalatPercakapan(_pesan(sebab)) from None
        self._giliran.append(giliran)


def _pesan(sebab: ValidationError) -> str:
    """Pesan yang menyebut jenis kekeliruan tanpa mengulang muatannya.

    Dibedakan karena akibatnya berbeda: penolakan KM-03 tidak boleh membawa
    keterangan apa pun tentang muatannya, sedangkan penolakan bentuk —
    pertanyaan kosong, waktu tanpa zona — justru wajib menyebut apa yang
    kurang. Pesan yang tidak menyebutnya membuat pemanggil menebak.
    """
    teks = str(sebab)
    if "pengenal berjenis" in teks:
        jenis = teks.split("pengenal berjenis", 1)[1].split(" —", 1)[0].strip()
        return f"pertanyaan memuat pengenal berjenis {jenis} dan tidak disimpan"
    if "waktu wajib berzona UTC" in teks:
        return "waktu giliran wajib berzona UTC"
    return "giliran tidak lengkap dan tidak dapat disimpan"
