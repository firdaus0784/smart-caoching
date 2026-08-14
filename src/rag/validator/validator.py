"""Penyusun validator — R-06, R-09, R-10, R-11, R-12; D-07 Bagian 6.

Menjalankan kesembilan pemeriksaan D-07 Bagian 6.1, menerapkan tabel tindakan
Bagian 6.2, dan — bila seluruhnya lulus — membentuk `JawabanTervalidasi`.

## Tiga pemeriksaan yang belum dapat dijalankan, dan mengapa itu tertulis

VS-03 dan VS-05 menunggu model sematan serta ambang BT-29; VS-07 menunggu model
NER. Ketiganya **tidak dilewati diam-diam**: masing-masing menghasilkan
`HasilPemeriksaan` berstatus `BELUM_DAPAT_DIPERIKSA` dengan alasan yang menyebut
apa yang ditunggunya.

Validator yang mengembalikan lulus atas kesembilannya tidak dapat dibedakan
dari validator yang benar — dan ia tinggal di komponen yang D-04 ADR-04 sebut
terpenting dalam sistem. Itu TA-01 pada tempat paling berbahaya.

Akibatnya langsung dan disengaja: **sistem ini tidak dapat menayangkan jawaban
apa pun sampai fitur 020 selesai.** D-07 Bagian 1 menetapkan arahnya —
*"jawaban yang salah lebih merugikan daripada jawaban yang tidak ada."*

## `tervalidasi` adalah sifat terhitung, bukan bidang

Bidang dapat diisi `True` oleh pemanggil yang lelah, dan pemanggil yang lelah
adalah keadaan yang wajar pada bulan kelima. Sifat terhitung menuntut
kesembilan pemeriksaan berstatus `LULUS`, dan tidak ada cara menuliskannya
selain membuat kesembilannya lulus.

## `JawabanTervalidasi` hanya dibentuk modul ini

Mengikuti ADR-13, yang membatasi pembentukan `Instruksi` pada satu modul dan
sudah punya pemeriksa. Fitur 009 kemudian **tidak memiliki cara** menayangkan
jawaban yang belum lewat validator — bukan dilarang, melainkan tidak bisa.

C-01 tetap tidak berpindah karena bentuk ini saja: verifikasi yang C-01 tuntut
mencakup VS-03, dan tanpa VS-03 yang ditegakkan hanyalah bahwa setiap klaim
menyebut id segmen yang sungguh ada.

## Dua tingkat tindakan, mengikuti D-07 Bagian 6.2

- **VS-04, VS-06, VS-09** → jawaban dibuang **tanpa perbaikan**, dicatat
  sebagai insiden. Tidak ada penurunan klaim, tidak ada penyusunan ulang.
- **VS-01, VS-02, VS-08** → klaim bermasalah dibuang atau diturunkan; bila
  ringkasan tindakan menjadi kosong, seluruh jawaban dibatalkan.

Urutannya menentukan: insiden diperiksa lebih dulu, sebab jawaban yang gagal
VS-04 tidak boleh "diperbaiki" menjadi jawaban yang lolos.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from src.rag.validator.keluaran import KeluaranModel, Klaim, SegmenRujukan
from src.rag.validator.pemeriksaan import HasilPemeriksaan, KodePemeriksaan, Status
from src.rag.validator.penyimpangan import periksa_penyimpangan
from src.rag.validator.sitasi import (
    periksa_dasar_klaim,
    periksa_indeks_metadata,
    periksa_keberlakuan,
    periksa_peringkat_klaim,
    periksa_rujukan_nyata,
)

KODE_INSIDEN: frozenset[KodePemeriksaan] = frozenset(
    {KodePemeriksaan.VS_04, KodePemeriksaan.VS_06, KodePemeriksaan.VS_09}
)
"""Kegagalan yang membuang seluruh jawaban tanpa perbaikan — D-07 Bagian 6.2.

Ketiganya bukan kekeliruan penyusunan melainkan tanda bahwa sesuatu di hulu
bocor: segmen yang tidak boleh terjangkau ternyata terjangkau (VS-04, VS-06),
atau keluaran model tidak dapat dipercaya sama sekali (VS-09).
"""

_MENUNGGU_FITUR_020: dict[KodePemeriksaan, str] = {
    KodePemeriksaan.VS_03: "dukungan isi klaim menuntut kemiripan semantik — "
    "menunggu model sematan (fitur 019) dan ambang BT-29",
    KodePemeriksaan.VS_05: "batas penyalinan menuntut ambang kemiripan — "
    "menunggu kalibrasi BT-29 (C-16)",
    KodePemeriksaan.VS_07: "nama perorangan menuntut pengenalan entitas bernama — "
    "menunggu model NER (fitur 017), yang menunggu korpus teranotasi",
}
"""Pemeriksaan yang belum dapat dijalankan, beserta apa yang ditunggunya.

Alasannya menyebut **fiturnya**, bukan sekadar "belum tersedia". Alasan yang
tidak menyebut apa yang ditunggu adalah alasan yang tidak dapat ditagih.
"""


def pemeriksaan_menunggu_model(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> dict[KodePemeriksaan, HasilPemeriksaan]:
    """VS-03, VS-05, dan VS-07 — **sambungan tempat fitur 020 mendarat**.

    Ia berupa fungsi, bukan daftar yang disusun sebaris di dalam `validasi`,
    justru agar sambungannya punya nama. Fitur 020 menggantikan isinya; bentuk
    kembaliannya tidak berubah, dan `validasi` tidak perlu disentuh.

    Ia menerima `keluaran` dan `segmen` yang belum dipakainya sama sekali —
    ketiga pemeriksaan itu akan membutuhkan keduanya. Menerimanya sekarang
    membuat pendaratan fitur 020 tidak mengubah tanda tangan yang sudah
    dipanggil.
    """
    return {
        kode: HasilPemeriksaan(kode=kode, status=Status.BELUM_DAPAT_DIPERIKSA, alasan=alasan)
        for kode, alasan in _MENUNGGU_FITUR_020.items()
    }


def _pemeriksaan_yang_dapat_dijalankan(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> dict[KodePemeriksaan, HasilPemeriksaan]:
    """Keenam pemeriksaan yang sudah berdiri, **berkunci kodenya**.

    Berkunci kode, bukan berupa daftar berurut. Daftar berurut membuat
    "kesembilan kode dijalankan" menjadi sifat yang kebetulan benar — ia
    bergantung pada tidak seorang pun menghapus satu baris. Pemetaan membuatnya
    dapat diperiksa: kode yang tidak menjadi kunci adalah kode yang tidak
    dijalankan, dan pemeriksa C-19 membacanya dari sini.

    Menjatuhkan VS-08 dari daftar jalannya adalah cara termudah melanggar C-19
    tanpa menyentuh satu baris logika pun.
    """
    return {
        KodePemeriksaan.VS_01: periksa_dasar_klaim(keluaran),
        KodePemeriksaan.VS_02: periksa_rujukan_nyata(keluaran, segmen=segmen),
        KodePemeriksaan.VS_04: periksa_indeks_metadata(keluaran, segmen=segmen),
        KodePemeriksaan.VS_06: periksa_keberlakuan(keluaran, segmen=segmen),
        KodePemeriksaan.VS_08: periksa_peringkat_klaim(keluaran, segmen=segmen),
        KodePemeriksaan.VS_09: periksa_penyimpangan(keluaran, segmen=segmen),
    }


class HasilValidasi(BaseModel):
    """Hasil seluruh pemeriksaan atas satu keluaran model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pemeriksaan: tuple[HasilPemeriksaan, ...]

    @property
    def tervalidasi(self) -> bool:
        """Kesembilan pemeriksaan berstatus `LULUS` — sifat, bukan bidang.

        Bidang dapat diisi `True` oleh pemanggil yang lelah. Sifat terhitung
        tidak dapat dituliskan selain dengan membuat kesembilannya lulus.

        Kelengkapan diperiksa juga: hasil yang memuat delapan pemeriksaan lulus
        bukan hasil yang tervalidasi, ia hasil yang satu pemeriksaannya hilang.
        """
        if {h.kode for h in self.pemeriksaan} != set(KodePemeriksaan):
            return False
        return all(not h.menghalangi for h in self.pemeriksaan)

    @property
    def menghalangi(self) -> tuple[HasilPemeriksaan, ...]:
        """Pemeriksaan yang gagal atau belum dapat diperiksa — R-08."""
        return tuple(h for h in self.pemeriksaan if h.menghalangi)

    @property
    def insiden_kepatuhan(self) -> tuple[KodePemeriksaan, ...]:
        """Kegagalan yang membuang jawaban tanpa perbaikan — D-07 Bagian 6.2."""
        return tuple(
            h.kode for h in self.pemeriksaan if h.status is Status.GAGAL and h.kode in KODE_INSIDEN
        )


class JawabanTervalidasi(BaseModel):
    """Jawaban yang telah melewati seluruh pemeriksaan — R-09.

    **Hanya dibentuk `validasi()` pada modul ini.** Mengikuti ADR-13, yang
    membatasi pembentukan `Instruksi` pada satu modul. Fitur 009 tidak memiliki
    cara menayangkan jawaban yang belum lewat validator — bukan dilarang,
    melainkan tidak bisa.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    keluaran: KeluaranModel
    hasil: HasilValidasi


def validasi(
    keluaran: KeluaranModel, *, segmen: Sequence[SegmenRujukan]
) -> tuple[HasilValidasi, JawabanTervalidasi | None]:
    """Jalankan kesembilan pemeriksaan dan terapkan tabel tindakan 6.2.

    Mengembalikan hasilnya selalu, dan jawabannya **hanya bila tervalidasi**.
    Bentuk dua nilai ini disengaja: pemanggil yang hanya membaca nilai kedua
    tidak dapat menayangkan apa pun ketika validasi gagal, sedangkan hasilnya
    tetap tersedia bagi pencatatan RT-02.

    Tidak menulis apa pun dan tidak memanggil model (R-11, C-17, C-08).
    """
    berkode = {
        **_pemeriksaan_yang_dapat_dijalankan(keluaran, segmen=segmen),
        **pemeriksaan_menunggu_model(keluaran, segmen=segmen),
    }
    hilang = set(KodePemeriksaan) - set(berkode)
    if hilang:
        raise RuntimeError(
            "pemeriksaan yang tidak dijalankan: "
            f"{sorted(k.value for k in hilang)} — kesembilan kode D-07 Bagian 6.1 "
            "wajib punya hasil, dan yang hilang tidak boleh terbaca sebagai lulus"
        )
    hasil = HasilValidasi(pemeriksaan=tuple(berkode[k] for k in KodePemeriksaan))
    if not hasil.tervalidasi:
        return hasil, None
    return hasil, JawabanTervalidasi(keluaran=keluaran, hasil=hasil)


def keluaran_setelah_tindakan(
    keluaran: KeluaranModel, hasil: HasilValidasi
) -> KeluaranModel | None:
    """Terapkan tabel tindakan D-07 Bagian 6.2 — R-06.

    `None` berarti seluruh jawaban dibatalkan. Tiga jalan menuju ke sana, dan
    ketiganya berbeda sebabnya:

    1. **Insiden kepatuhan** (VS-04, VS-06, VS-09) — dibuang tanpa perbaikan.
    2. **Seluruh klaim bermasalah** — tidak ada yang tersisa untuk ditayangkan.
    3. **Ringkasan tindakan menjadi kosong** sesudah klaim dibuang.

    Ketiga diperiksa terpisah dari kedua: jawaban dapat kehilangan seluruh
    ringkasannya sementara sebagian klaimnya bertahan, dan jawaban tanpa
    ringkasan tindakan bukan jawaban manajerial.
    """
    if hasil.insiden_kepatuhan:
        return None

    bermasalah = {
        id_klaim
        for h in hasil.pemeriksaan
        if h.status is Status.GAGAL
        for id_klaim in h.id_klaim_bermasalah
    }
    tersisa: tuple[Klaim, ...] = tuple(k for k in keluaran.klaim if k.id_klaim not in bermasalah)
    if keluaran.klaim and not tersisa:
        return None
    if keluaran.klaim and not keluaran.ringkasan_tindakan:
        return None
    return keluaran.model_copy(update={"klaim": tersisa})
