"""Peta pseudonim di atas basis data kedua — T-5 fitur 024, R-05, C-05.

C-05 berbunyi: *"Kunci pemetaan pseudonim tidak berada pada basis data yang
sama dengan data perilaku, dan tidak terjangkau dari layanan aplikasi."*

Dua tuntutan, dan yang menegakkan masing-masing berbeda:

| Tuntutan | Yang menegakkan | Diuji di sini |
|---|---|---|
| basis data terpisah | `REVOKE CONNECT` pada peladen | ya — peran penjawaban ditolak menyambung |
| tidak terjangkau layanan | `KredensialPseudonim` tak dapat dibentuk `src/` | pemeriksa C-05 aturan 1 |

Uji terpenting berkas ini `test_peran_penjawaban_tidak_dapat_menyambung`: ia
membuktikan keterpisahan itu **ditolak peladen**, bukan ditolak kode. Kelas
yang menjaga keterpisahan basis data dengan memeriksa nama basis datanya
sendiri hanya memeriksa untai.
"""

from __future__ import annotations

import uuid

import pytest
from src.penyimpanan.pseudonim import (
    GalatPseudonim,
    KredensialPseudonim,
    PetaPseudonimPostgres,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, psql, siapkan

siapkan()

KREDENSIAL = KredensialPseudonim(nama="peneliti")


class SambunganPseudonim:
    """Menyambung sebagai peran tertentu ke basis data pseudonim."""

    def __init__(self, peran: str, basis_data: str = "smart_coaching_pseudonim") -> None:
        self._peran = peran
        self._basis_data = basis_data

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> object:
        import asyncpg

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user=self._peran, database=self._basis_data
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> object:
        return await self._dengan("execute", kueri, *argumen)


def _peta() -> PetaPseudonimPostgres:
    return PetaPseudonimPostgres(SambunganPseudonim("peran_pseudonim"))


def _baru() -> tuple[str, str]:
    penanda = uuid.uuid4().hex[:10]
    return f"pengguna_{penanda}", f"ps_{penanda}"


# ── keterpisahan ditegakkan peladen ──────────────────────────────────


def test_peran_penjawaban_tidak_dapat_menyambung() -> None:
    """**Uji terpenting berkas ini.**

    Jalur penjawaban tidak ditolak ketika membaca tabelnya — ia ditolak
    sebelum sampai ke sana, pada saat menyambung. Itu arti "tidak terjangkau".
    """
    peta = PetaPseudonimPostgres(SambunganPseudonim("peran_penjawaban"))
    with pytest.raises(Exception) as galat:
        jalankan(peta.pseudonim_bagi("siapa pun", kredensial=KREDENSIAL))
    assert "permission denied for database" in str(galat.value).lower(), str(galat.value)


def test_peran_pseudonim_tidak_dapat_menyambung_ke_basis_data_perilaku() -> None:
    """Arah sebaliknya. Keterpisahan satu arah bukan keterpisahan."""
    peta = PetaPseudonimPostgres(SambunganPseudonim("peran_pseudonim", "smart_coaching"))
    with pytest.raises(Exception) as galat:
        jalankan(peta.pseudonim_bagi("siapa pun", kredensial=KREDENSIAL))
    assert "permission denied for database" in str(galat.value).lower(), str(galat.value)


# ── perilaku pemetaan ────────────────────────────────────────────────


def test_pemetaan_tercatat_dan_terbaca_dua_arah() -> None:
    id_pengguna, pseudonim = _baru()
    peta = _peta()
    jalankan(peta.daftarkan(id_pengguna, pseudonim, kredensial=KREDENSIAL))
    assert jalankan(peta.pseudonim_bagi(id_pengguna, kredensial=KREDENSIAL)) == pseudonim
    assert jalankan(peta.id_pengguna_bagi(pseudonim, kredensial=KREDENSIAL)) == id_pengguna


def test_pemetaan_yang_belum_ada_menghasilkan_none() -> None:
    peta = _peta()
    assert jalankan(peta.pseudonim_bagi("tidak_pernah_ada", kredensial=KREDENSIAL)) is None
    assert jalankan(peta.id_pengguna_bagi("tidak_pernah_ada", kredensial=KREDENSIAL)) is None


def test_pengguna_yang_sama_tidak_dapat_didaftarkan_dua_kali() -> None:
    id_pengguna, pseudonim = _baru()
    peta = _peta()
    jalankan(peta.daftarkan(id_pengguna, pseudonim, kredensial=KREDENSIAL))
    with pytest.raises(GalatPseudonim):
        jalankan(peta.daftarkan(id_pengguna, "ps_lain", kredensial=KREDENSIAL))


def test_pseudonim_tidak_dapat_berpindah_pemilik() -> None:
    """Pseudonim yang berpindah pemilik membuat data perilaku lama tertaut ke
    orang yang keliru — kekeliruan yang tidak dapat diperbaiki sesudah
    pemetaan lamanya hilang."""
    id_pengguna, pseudonim = _baru()
    peta = _peta()
    jalankan(peta.daftarkan(id_pengguna, pseudonim, kredensial=KREDENSIAL))
    with pytest.raises(GalatPseudonim):
        jalankan(peta.daftarkan("pengguna_lain", pseudonim, kredensial=KREDENSIAL))


def test_penolakan_datang_dari_batasan_basis_data() -> None:
    """Bukan dari pembacaan lebih dulu.

    Membaca lalu menulis meninggalkan celah antara keduanya, dan celah itu
    tepat tempat dua pendaftaran bersamaan menghasilkan satu pseudonim milik
    dua orang. Dibuktikan dengan membaca jumlah baris langsung dari peladen.
    """
    id_pengguna, pseudonim = _baru()
    peta = _peta()
    jalankan(peta.daftarkan(id_pengguna, pseudonim, kredensial=KREDENSIAL))
    with pytest.raises(GalatPseudonim):
        jalankan(peta.daftarkan(id_pengguna, "ps_lain", kredensial=KREDENSIAL))

    hasil = psql(
        "smart_coaching_pseudonim",
        "-c",
        f"select count(*) from pseudonim.peta_pseudonim where id_pengguna = '{id_pengguna}'",
    )
    assert hasil.stdout.strip() == "1", hasil.stdout


class SambunganYangMelarang:
    """Melempar bila dipakai. Penjaga atas urutan pemeriksaan."""

    async def fetchrow(self, kueri: str, *argumen: object) -> object:
        raise AssertionError("basis data disentuh sebelum kredensial diperiksa")

    async def execute(self, kueri: str, *argumen: object) -> object:
        raise AssertionError("basis data disentuh sebelum kredensial diperiksa")


KREDENSIAL_CACAT = KredensialPseudonim(nama="   ")


@pytest.mark.parametrize(
    "panggil",
    [
        pytest.param(
            lambda peta: peta.daftarkan("a", "ps_a", kredensial=KREDENSIAL_CACAT),
            id="daftarkan",
        ),
        pytest.param(
            lambda peta: peta.pseudonim_bagi("a", kredensial=KREDENSIAL_CACAT),
            id="pseudonim_bagi",
        ),
        pytest.param(
            lambda peta: peta.id_pengguna_bagi("ps_a", kredensial=KREDENSIAL_CACAT),
            id="id_pengguna_bagi",
        ),
    ],
)
def test_setiap_metode_menolak_kredensial_cacat(panggil: object) -> None:
    """**Ketiga** metode, bukan sebagian.

    Uji mutasi menemukan `daftarkan` dan `id_pengguna_bagi` tidak terjaga satu
    uji pun — dan yang kedua justru arah balik yang C-05 lindungi: ia yang
    mengubah pseudonim kembali menjadi identitas.

    Sambungan yang melempar bila dipakai membuktikan penolakannya datang
    **sebelum** basis data disentuh. Uji yang memakai sambungan sungguhan akan
    lulus juga seandainya pemeriksaan kredensial bergeser ke belakang kueri.
    """
    peta = PetaPseudonimPostgres(SambunganYangMelarang())
    with pytest.raises(GalatPseudonim, match="tidak dapat ditelusuri"):
        jalankan(panggil(peta))  # type: ignore[operator]


def test_kredensial_bernama_kosong_ditolak() -> None:
    """Pemeriksaan kedua, sesudah tipe.

    `nama=""` sudah ditolak pydantic pada pembentukannya, sehingga ia tidak
    menguji penjagaan ini sama sekali. Yang lolos pembentukan dan **wajib**
    ditolak penjagaan adalah nama berisi spasi — bentuk yang muncul ketika
    seseorang menyusun kredensial asal ada.
    """
    peta = _peta()
    with pytest.raises(GalatPseudonim, match="tidak dapat ditelusuri"):
        jalankan(peta.pseudonim_bagi("a", kredensial=KredensialPseudonim(nama="   ")))


@pytest.mark.parametrize(
    ("id_pengguna", "pseudonim"),
    [("", "ps_x"), ("pengguna_x", ""), ("", "")],
)
def test_pemetaan_kosong_ditolak_sebelum_basis_data_disentuh(
    id_pengguna: str, pseudonim: str
) -> None:
    """Ditolak sebelum kueri disusun.

    Sambungan yang melempar bila dipakai membuktikannya: bila pemeriksaan
    bergeser ke belakang `INSERT`, uji ini gagal dengan galat sambungan
    alih-alih lulus diam-diam.
    """

    peta = PetaPseudonimPostgres(SambunganYangMelarang())
    with pytest.raises(GalatPseudonim, match="menuntut id pengguna dan pseudonim"):
        jalankan(peta.daftarkan(id_pengguna, pseudonim, kredensial=KREDENSIAL))
