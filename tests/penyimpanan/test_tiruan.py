"""Kontrak `PenyimpanDasar` — R-01, R-02, R-03, R-04, C-03, ADR-06, ADR-12.

Tugas terpenting Fase A. Penyimpan yang memeriksa keberadaan dokumen lebih
dulu membocorkan keberadaan dokumen karantina lewat perbedaan galat, dan itu
meruntuhkan C-03 **tanpa satu pun dokumen terbaca**.

Kebocorannya halus: pemanggil yang menerima "tidak ditemukan" untuk satu id dan
"tidak berwenang" untuk id lain sudah mengetahui id mana yang ada di karantina.
Cukup satu perbedaan untuk menyusun daftar.

## Berkas ini berparameter — T-2 fitur 024

R-01 menuntut `PenyimpanPostgres` lulus rangkaian uji yang **sama** dengan
`PenyimpanTiruan`, tanpa satu pun uji diubah. Karena itu seluruh uji di bawah
menerima pelaksananya dari `PABRIK`, bukan menyusunnya sendiri.

Hari ini `PABRIK` berisi **satu** pelaksana. Itu disengaja: tugas T-2 mengubah
bentuk uji dan membuktikan hasilnya tidak berubah, sebelum pelaksana kedua
ditambahkan pada T-3. Menambah keduanya sekaligus membuat kegagalan tidak
dapat ditelusuri ke perubahan yang mana.

## Temuan T-2, dan penyelesaiannya

`GalatDokumenTidakAda` semula tinggal di `src/penyimpanan/tiruan.py` — di
dalam **pelaksana** — padahal ia bagian kontrak: R-03 menuntut galat "tidak
ada" pada area yang boleh dibaca, dan tuntutan itu berlaku bagi setiap
pelaksana.

Ia dipindahkan ke `galat.py` pada 12 September 2026 lewat Gerbang 2 tersendiri
(KB-086), sebagaimana Keputusan Gerbang 1 nomor 3 wajibkan. Bentuk `PABRIK`
yang memasok tipe galatnya sendiri **dipertahankan**: ia menampung pelaksana
yang kelak melempar galat berbeda tanpa mengubah satu pun uji di bawah, dan
membuangnya sekarang berarti membangunnya lagi pada T-3.
"""

import json
import os
import pathlib
import shutil
import subprocess
from collections.abc import Callable

import pytest
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenTidakAda
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, VERIFIKASI
from src.penyimpanan.postgres import PenyimpanPostgres
from src.penyimpanan.tiruan import PenyimpanTiruan
from tests.konftes_asinkron import jalankan

AKAR = pathlib.Path(__file__).resolve().parents[2]

Penanam = Callable[[PenyimpanDasar, Area, str, object], None]


def _susun_tiruan() -> tuple[PenyimpanDasar, Penanam, type[Exception]]:
    def tanam(penyimpan: PenyimpanDasar, area: Area, id_dokumen: str, isi: object) -> None:
        assert isinstance(penyimpan, PenyimpanTiruan)
        penyimpan.tanam(area, id_dokumen, isi)

    return PenyimpanTiruan(), tanam, GalatDokumenTidakAda


def _peladen_tersedia() -> bool:
    """Peladen PostgreSQL dapat dihubungi."""
    if shutil.which("psql") is None:
        return False
    return _psql("select 1").returncode == 0


def _psql(kueri: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "psql",
            "-h",
            os.environ.get("PGHOST", "/tmp"),
            "-p",
            os.environ.get("PGPORT", "55432"),
            "-U",
            os.environ.get("PGUSER", "pengelola"),
            "-d",
            "smart_coaching",
            "-tAq",
            "-c",
            kueri,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _susun_postgres() -> tuple[PenyimpanDasar, Penanam, type[Exception]]:
    """Pelaksana sungguhan di atas peladen yang berjalan.

    Tabel dikosongkan tiap pemanggilan, bukan dibuat ulang: membuat ulang
    menghapus hak akses bawaan yang `ALTER DEFAULT PRIVILEGES` berikan, dan
    itu mengubah yang diuji.
    """
    import asyncpg

    # Penyiapan idempoten tiap pemanggilan, bukan sekali di awal berkas.
    # `test_persiapan_basis_data.py` membangun ulang basis data yang sama dari
    # nol, sehingga berkas mana pun yang menganggap tabelnya sudah ada akan
    # gagal tergantung urutan jalannya. Urutan uji bukan hal yang boleh
    # diandalkan.
    _psql("CREATE SCHEMA IF NOT EXISTS karantina; CREATE SCHEMA IF NOT EXISTS korpus;")
    berkas = AKAR / "perkakas" / "basis_data" / "04-tabel-dokumen.sql"
    subprocess.run(
        [
            "psql",
            "-h",
            os.environ.get("PGHOST", "/tmp"),
            "-p",
            os.environ.get("PGPORT", "55432"),
            "-U",
            os.environ.get("PGUSER", "pengelola"),
            "-d",
            "smart_coaching",
            "-tAq",
            "-f",
            str(berkas),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    _psql("TRUNCATE karantina.dokumen_sumber, korpus.dokumen_sumber")

    class SambunganSekaliPakai:
        """Menyambung dan menutup pada tiap panggilan.

        Sambungan **tidak disimpan**, dan itu disengaja. `jalankan` memakai
        `asyncio.run`, yang membuat gelung peristiwa baru tiap pemanggilan;
        sambungan `asyncpg` terikat pada gelung tempat ia dibuka. Menyimpannya
        membuat panggilan kedua melempar *"attached to a different loop"* —
        ditemukan dengan menjalankannya, bukan dengan membacanya.

        Boros bagi uji, dan benar. Pengumpulan sambungan urusan pemanggil
        sungguhan, bukan urusan pelaksana ini (R-06).
        """

        async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
            sambungan = await asyncpg.connect(
                host=os.environ.get("PGHOST", "/tmp"),
                port=int(os.environ.get("PGPORT", "55432")),
                user=os.environ.get("PGUSER", "pengelola"),
                database="smart_coaching",
            )
            try:
                return await getattr(sambungan, nama)(kueri, *argumen)
            finally:
                await sambungan.close()

        async def fetchrow(self, kueri: str, *argumen: object) -> object:
            return await self._dengan("fetchrow", kueri, *argumen)

        async def execute(self, kueri: str, *argumen: object) -> object:
            return await self._dengan("execute", kueri, *argumen)

    def tanam(penyimpan: PenyimpanDasar, area: Area, id_dokumen: str, isi: object) -> None:
        skema = {Area.KARANTINA: "karantina", Area.KORPUS: "korpus"}[area]
        _psql(
            f"INSERT INTO {skema}.dokumen_sumber (id, isi) VALUES "
            f"('{id_dokumen}', '{json.dumps(isi)}'::jsonb)"
        )

    return PenyimpanPostgres(SambunganSekaliPakai()), tanam, GalatDokumenTidakAda


PABRIK: dict[str, object] = {"tiruan": _susun_tiruan}
"""Pelaksana yang wajib lulus kontrak yang sama — R-01.

`postgres` ditambahkan hanya bila peladen dapat dihubungi. Ketiadaannya
**dilaporkan**, bukan didiamkan: rangkaian uji yang menguji satu pelaksana
sambil terbaca seperti menguji dua adalah laporan yang keliru (TA-01).
"""

if _peladen_tersedia():
    PABRIK["postgres"] = _susun_postgres


@pytest.fixture(params=sorted(PABRIK), ids=sorted(PABRIK))
def terisi(request: pytest.FixtureRequest) -> tuple[PenyimpanDasar, type[Exception]]:
    """Penyimpan berisi dua dokumen — satu karantina, satu korpus."""
    penyimpan, tanam, galat_tidak_ada = PABRIK[request.param]()
    tanam(penyimpan, Area.KARANTINA, "dok_karantina", {"isi": "notulen rapat"})
    tanam(penyimpan, Area.KORPUS, "dok_korpus", {"isi": "Permendikdasmen 1/2026"})
    return penyimpan, galat_tidak_ada


def test_penjawaban_membaca_korpus(terisi: tuple) -> None:
    assert jalankan(terisi[0].baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_korpus"))


def test_penjawaban_ditolak_membaca_karantina(terisi: tuple) -> None:
    """C-03, R-01a."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_karantina"))


def test_dokumen_karantina_yang_tidak_ada_juga_galat_akses(terisi: tuple) -> None:
    """**Uji terpenting berkas ini.**

    Kredensial diperiksa sebelum data disentuh, sehingga jawaban untuk id yang
    ada dan id yang tidak ada identik. Bila penyimpan memeriksa keberadaan
    lebih dulu, uji ini gagal — dan kegagalannya berarti daftar dokumen
    karantina dapat disusun dari luar.
    """
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].baca_dokumen(PENJAWABAN, Area.KARANTINA, "dok_tidak_pernah_ada"))


def test_dua_galat_tidak_dapat_dibedakan_dari_luar(terisi: tuple) -> None:
    """Perbandingan langsung, bukan dua uji terpisah yang kebetulan sama."""
    penyimpan = terisi[0]
    hasil = []
    for id_dokumen in ("dok_karantina", "dok_tidak_pernah_ada"):
        try:
            jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KARANTINA, id_dokumen))
        except GalatAksesDitolak as galat:
            hasil.append(galat.tanggapan().galat.pesan_pengguna)
    assert len(hasil) == 2
    assert hasil[0] == hasil[1]


def test_verifikasi_membaca_karantina(terisi: tuple) -> None:
    assert jalankan(terisi[0].baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina"))


def test_dokumen_tidak_ada_pada_area_yang_boleh_dibaca(terisi: tuple) -> None:
    """Ketika kredensialnya memang menjangkau, barulah keberadaan diperiksa."""
    with pytest.raises(terisi[1]):
        jalankan(terisi[0].baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_tidak_pernah_ada"))


def test_pemanggil_llm_tidak_dapat_menulis(terisi: tuple) -> None:
    """R-01b."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].tulis_dokumen(PEMANGGIL_LLM, Area.KORPUS, "dok_baru", {"isi": "x"}))


def test_penjawaban_tidak_dapat_menulis(terisi: tuple) -> None:
    """C-17."""
    with pytest.raises(GalatAksesDitolak):
        jalankan(terisi[0].tulis_dokumen(PENJAWABAN, Area.KORPUS, "dok_baru", {"isi": "x"}))


def test_verifikasi_menulis_ke_korpus(terisi: tuple) -> None:
    """Sisi positif R-04. Uji yang hanya memeriksa penolakan tidak
    membuktikan bahwa yang berhak dapat bekerja."""
    penyimpan = terisi[0]
    jalankan(penyimpan.tulis_dokumen(VERIFIKASI, Area.KORPUS, "dok_baru", {"isi": "x"}))
    assert jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_baru")) == {"isi": "x"}


def test_pindah_menuntut_baca_asal_dan_tulis_tujuan(terisi: tuple) -> None:
    """R-04."""
    penyimpan = terisi[0]
    jalankan(penyimpan.pindahkan(VERIFIKASI, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos"))
    assert jalankan(penyimpan.baca_dokumen(PENJAWABAN, Area.KORPUS, "dok_karantina"))


def test_pindah_ditolak_bagi_kredensial_penjawaban(terisi: tuple) -> None:
    with pytest.raises(GalatAksesDitolak):
        jalankan(
            terisi[0].pindahkan(PENJAWABAN, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos")
        )


def test_pindah_dokumen_yang_tidak_ada(terisi: tuple) -> None:
    with pytest.raises(terisi[1]):
        jalankan(
            terisi[0].pindahkan(
                VERIFIKASI, "dok_tidak_pernah_ada", Area.KARANTINA, Area.KORPUS, "lolos"
            )
        )


def test_dokumen_hilang_dari_area_asal_setelah_dipindah(terisi: tuple) -> None:
    """Menyalin, bukan memindahkan, meninggalkan salinan mentah di karantina —
    dan salinan itulah yang ADR-06 cegah."""
    penyimpan = terisi[0]
    jalankan(penyimpan.pindahkan(VERIFIKASI, "dok_karantina", Area.KARANTINA, Area.KORPUS, "lolos"))
    with pytest.raises(terisi[1]):
        jalankan(penyimpan.baca_dokumen(VERIFIKASI, Area.KARANTINA, "dok_karantina"))
