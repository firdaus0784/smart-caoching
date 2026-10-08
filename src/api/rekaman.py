"""Perekam peristiwa — T-4 fitur 034, R-01 s.d. R-04, R-07, R-08; K-2, K-4, K-5.

Satu-satunya pemanggil gerbang `rekam()` fitur 012 dari rute. Ia tidak memuat
aturan C-04 sendiri; ia memastikan gerbang itu **menerima keadaan yang
benar** pada setiap pemanggilan, lalu menyimpan yang gerbang kembalikan.

## Persetujuan dibaca setiap kali (R-02)

Keadaan dibaca dari penyimpan pengguna lewat `keadaan_persetujuan()` fitur
030 pada **setiap** pemanggilan — satu jalur penafsiran. Kelas ini tidak
memiliki bidang yang dapat menyimpannya, sehingga pencabutan berlaku pada
permintaan berikutnya, bukan pada sesi berikutnya.

Metode sesi berhenti lebih dulu bila persetujuan tidak mengizinkan, sebelum
membaca peristiwa lama pemilik itu: pemeriksaan isi tidak boleh terjadi bagi
pengguna yang tidak menyetujui (uraian `gerbang.py`, "Urutan pemeriksaan").
Gerbang tetap menerima keadaan yang sama dan tetap memutus.

## Galat ditelan, dan hanya di sini (R-07)

Galat apa pun dari langkah membaca persetujuan sampai menyimpan ditangkap,
dicatat ke log operasional dengan jenis peristiwa dan kelas galatnya saja —
tanpa pseudonim, tanpa properti, tanpa pesan galat yang dapat mengutip
muatan — lalu **tidak diteruskan**. Telemetri yang menjatuhkan rute membuat
persetujuan berbiaya bagi penggunanya (FR-A05, KB-193).

## Pemilik pseudonim (C-05)

Pemilik yang diterima adalah `Identitas.pemilik` — pseudonim dari sesi —
atau, pada rute masuk, pseudonim dari sesi yang baru diterbitkan (K-5).
`pengguna.id` tidak pernah sampai ke sini.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime, timedelta
from typing import Any, Final

from src.api.autentikasi import MASA_SESI
from src.api.galat import LOG_OPERASIONAL, id_jejak_baru
from src.api.penemuan import ButirRingkas
from src.api.saya import keadaan_persetujuan
from src.api.tanya import AlasanBerhenti, HasilTanya
from src.kamus.penilaian import NilaiPenilaian
from src.pengguna.persetujuan import KeadaanPersetujuan
from src.penyimpanan.pengguna import PenyimpanPengguna
from src.penyimpanan.telemetri import BarisPeristiwa, PenyimpanTelemetri
from src.telemetri import gerbang
from src.telemetri.gerbang import HasilPerekaman
from src.telemetri.peristiwa import JenisPeristiwa

TANPA_MODEL: Final = "tanpa_model"
"""`versi_model` bagi peristiwa yang tidak melibatkan model — P-4, K-4."""

AMBANG_KUNJUNGAN_ULANG: Final = timedelta(hours=24)
"""D-01 Bagian 9 apa adanya: `return_visit` bila `session_start` terakhir
**lebih dari** 24 jam lalu."""


class Perekam:
    """Persetujuan → `rekam()` → simpan. Tidak menyimpan keadaan apa pun."""

    def __init__(
        self,
        pengguna: PenyimpanPengguna,
        telemetri: PenyimpanTelemetri,
        *,
        versi_aplikasi: str,
    ) -> None:
        if not versi_aplikasi.strip():
            raise ValueError("versi aplikasi wajib terisi (FR-J02, C-09)")
        self._pengguna = pengguna
        self._telemetri = telemetri
        self._versi_aplikasi = versi_aplikasi

    async def rekam(
        self,
        pemilik: str,
        jenis: JenisPeristiwa,
        properti: dict[str, Any],
        *,
        sekarang: datetime,
        versi_model: str = TANPA_MODEL,
    ) -> None:
        """Satu peristiwa bila persetujuan mengizinkan. Tidak pernah melempar."""
        await self._rekam_semua(pemilik, ((jenis, properti, versi_model),), sekarang)

    # ── K-6 · peristiwa Tanya dan penemuan ───────────────────────────
    #
    # Teks yang ditulis pengguna diterima di sini dan **hanya ukurannya** yang
    # menjadi properti (R-06). Satu tempat yang menerjemahkan teks menjadi
    # ukuran, agar tidak ada rute yang menyusun properti sendiri.

    async def rekam_pertanyaan(self, pemilik: str, pertanyaan: str, *, sekarang: datetime) -> None:
        """`question_asked` — panjang pertanyaan dalam karakter, bukan isinya."""
        await self.rekam(
            pemilik,
            JenisPeristiwa.QUESTION_ASKED,
            {"panjang_pertanyaan": len(pertanyaan)},
            sekarang=sekarang,
        )

    async def rekam_jawaban(
        self, pemilik: str, hasil: HasilTanya, *, waktu_tanggap_ms: int, sekarang: datetime
    ) -> None:
        """`answer_served`, dan `answer_rejected_validator` bila validator menahannya.

        Keduanya membawa versi model dari tanggapan (K-4, FR-J02). Alasan
        berhenti lain bukan penolakan validator: menamainya demikian membuat
        laporan menyalahkan validator atas korpus yang kurang (C-16).
        """
        tanggapan = hasil.tanggapan
        model = tanggapan.versi.model
        daftar: list[tuple[JenisPeristiwa, dict[str, Any], str]] = [
            (
                JenisPeristiwa.ANSWER_SERVED,
                {
                    "status_dasar": tanggapan.status_dasar.value,
                    "jumlah_sitasi": len(tanggapan.sitasi),
                    "waktu_tanggap_ms": waktu_tanggap_ms,
                },
                model,
            )
        ]
        if hasil.alasan_berhenti is AlasanBerhenti.DITAHAN_VALIDATOR:
            daftar.append(
                (
                    JenisPeristiwa.ANSWER_REJECTED_VALIDATOR,
                    {"alasan_berhenti": hasil.alasan_berhenti.value},
                    model,
                )
            )
        await self._rekam_semua(pemilik, daftar, sekarang)

    async def rekam_tayang(
        self, pemilik: str, butir: Sequence[ButirRingkas], *, sekarang: datetime
    ) -> None:
        """`discovery_served` bagi butir yang **baru** tercatat hari itu — sekali per butir."""
        if not butir:
            return
        await self._rekam_semua(
            pemilik,
            [
                (
                    JenisPeristiwa.DISCOVERY_SERVED,
                    {
                        "id_butir": b.id_butir,
                        "jenis_sumber": b.jenis_sumber.value,
                        "kategori": b.kategori.value,
                    },
                    TANPA_MODEL,
                )
                for b in butir
            ],
            sekarang,
        )

    async def rekam_dibuka(
        self,
        pemilik: str,
        id_butir: str,
        kapan_tayang: Callable[[], Awaitable[datetime | None]],
        *,
        sekarang: datetime,
    ) -> None:
        """`discovery_opened` beserta menit sejak butir pertama kali tampil baginya."""
        jenis = JenisPeristiwa.DISCOVERY_OPENED
        try:
            keadaan = await keadaan_persetujuan(self._pengguna, pemilik)
            if not keadaan.boleh_merekam:
                return
            kapan = await kapan_tayang()
            properti: dict[str, Any] = {"id_butir": id_butir}
            if kapan is not None:
                properti["menit_sejak_tayang"] = (sekarang - kapan) // timedelta(minutes=1)
            await self._simpan(keadaan, pemilik, jenis, properti, sekarang, TANPA_MODEL)
        except Exception as galat:
            _catat_gagal(jenis, galat)

    async def rekam_belum_relevan(
        self, pemilik: str, id_butir: str, alasan: str, *, sekarang: datetime
    ) -> None:
        """`discovery_dismissed` — panjang alasan, bukan isinya."""
        await self.rekam(
            pemilik,
            JenisPeristiwa.DISCOVERY_DISMISSED,
            {"id_butir": id_butir, "panjang_alasan": len(alasan)},
            sekarang=sekarang,
        )

    async def rekam_penilaian(
        self,
        pemilik: str,
        id_pesan: str,
        nilai: NilaiPenilaian,
        *,
        beralasan: bool,
        versi_model: str,
        sekarang: datetime,
    ) -> None:
        """`answer_rated` — nilai, ada tidaknya alasan, dan pesan yang dinilai.

        **Tanpa teks alasan** (P-4 B): peristiwa diekspor ke luar sistem, dan
        teks bebas adalah jalan data pribadi tak berpola keluar. `id_pesan`
        ada agar penilaian yang menggantikan dapat dikenali analitik (KB-228).
        Versi model milik tanggapan yang dinilai, bukan `tanpa_model`.
        """
        await self.rekam(
            pemilik,
            JenisPeristiwa.ANSWER_RATED,
            {"nilai": nilai.value, "beralasan": beralasan, "id_pesan": id_pesan},
            sekarang=sekarang,
            versi_model=versi_model,
        )

    async def _rekam_semua(
        self,
        pemilik: str,
        daftar: Sequence[tuple[JenisPeristiwa, dict[str, Any], str]],
        sekarang: datetime,
    ) -> None:
        """Persetujuan dibaca sekali bagi peristiwa yang lahir dari satu permintaan."""
        jenis = daftar[0][0]
        try:
            keadaan = await keadaan_persetujuan(self._pengguna, pemilik)
            for jenis, properti, versi_model in daftar:
                await self._simpan(keadaan, pemilik, jenis, properti, sekarang, versi_model)
        except Exception as galat:
            _catat_gagal(jenis, galat)

    async def mulai_sesi(
        self, cari_pemilik: Callable[[], Awaitable[str | None]], *, sekarang: datetime
    ) -> None:
        """`return_visit` bila jedanya melampaui ambang, lalu `session_start`.

        Pemilik dicari **di dalam** penjagaan galat: membaca sesi yang baru
        terbit pun bagian dari perekaman, dan kegagalannya tidak boleh
        mengubah tanggapan masuk (R-07).
        """
        jenis = JenisPeristiwa.SESSION_START
        try:
            pemilik = await cari_pemilik()
            if pemilik is None:
                return
            keadaan = await keadaan_persetujuan(self._pengguna, pemilik)
            if not keadaan.boleh_merekam:
                return
            lalu = await self._telemetri.terakhir(pemilik, jenis.value)
            if lalu is not None and sekarang - lalu > AMBANG_KUNJUNGAN_ULANG:
                jeda = {"jeda_jam": (sekarang - lalu) // timedelta(hours=1)}
                await self._simpan(
                    keadaan, pemilik, JenisPeristiwa.RETURN_VISIT, jeda, sekarang, TANPA_MODEL
                )
            await self._simpan(keadaan, pemilik, jenis, {}, sekarang, TANPA_MODEL)
        except Exception as galat:
            _catat_gagal(jenis, galat)

    async def akhiri_sesi(self, pemilik: str, *, sekarang: datetime) -> None:
        """`session_end` dengan durasi sejak `session_start` terakhir.

        Durasi tidak diisi bila awal sesinya tidak terekam, atau lebih tua dari
        `MASA_SESI` — awal seperti itu milik sesi lain, dan durasinya tebakan.
        """
        jenis = JenisPeristiwa.SESSION_END
        try:
            keadaan = await keadaan_persetujuan(self._pengguna, pemilik)
            if not keadaan.boleh_merekam:
                return
            lalu = await self._telemetri.terakhir(pemilik, JenisPeristiwa.SESSION_START.value)
            properti: dict[str, Any] = {}
            if lalu is not None and sekarang - lalu <= MASA_SESI:
                properti["durasi_menit"] = (sekarang - lalu) // timedelta(minutes=1)
            await self._simpan(keadaan, pemilik, jenis, properti, sekarang, TANPA_MODEL)
        except Exception as galat:
            _catat_gagal(jenis, galat)

    async def _simpan(
        self,
        keadaan: KeadaanPersetujuan,
        pemilik: str,
        jenis: JenisPeristiwa,
        properti: dict[str, Any],
        sekarang: datetime,
        versi_model: str,
    ) -> None:
        hasil, peristiwa = gerbang.rekam(
            keadaan=keadaan,
            pseudonim=pemilik,
            jenis=jenis,
            waktu=sekarang,
            properti=properti,
            versi_aplikasi=self._versi_aplikasi,
            versi_model=versi_model,
        )
        if hasil is HasilPerekaman.DITOLAK_PROPERTI:
            # Kekeliruan pemanggil, bukan pilihan pengguna — dicatat agar
            # terlihat, tanpa muatannya.
            LOG_OPERASIONAL.warning(
                "telemetri properti ditolak %s jenis=%s", id_jejak_baru(), jenis.value
            )
        if peristiwa is None:
            return
        await self._telemetri.tambah(
            BarisPeristiwa(
                pseudonim=peristiwa.pseudonim,
                jenis=peristiwa.jenis.value,
                waktu=peristiwa.waktu,
                properti=peristiwa.properti,
                versi_aplikasi=peristiwa.versi_aplikasi,
                versi_model=peristiwa.versi_model,
            )
        )


def _catat_gagal(jenis: JenisPeristiwa, galat: Exception) -> None:
    """Jenis peristiwa dan kelas galat saja — pesan galat dapat mengutip muatan."""
    LOG_OPERASIONAL.warning(
        "telemetri gagal %s jenis=%s galat=%s", id_jejak_baru(), jenis.value, type(galat).__name__
    )
