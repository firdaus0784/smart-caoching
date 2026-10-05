"""Penyimpan kurasi dan penemuan — T-3 fitur 013, R-02, R-05, R-07, K-2.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL. Yang kedua
tersambung sebagai peran masing-masing (TK-64): `peran_pengisi_antrean` bagi
pengisi, `peran_kurasi` bagi kurator, `peran_penayangan` bagi penayang —
sehingga uji ini juga membuktikan hak T-2 cukup bagi pekerjaannya, dan tidak
lebih.

Basis datanya dipakai bersama modul lain, sehingga tiap uji memakai id butir
dan pemilik acak, dan hanya menilai baris miliknya sendiri.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import pytest
from src.penyimpanan.kurasi import (
    PERAN_KURASI,
    PERAN_PENGISI_ANTREAN,
    BarisKandidat,
    CatatanPutusan,
    KurasiMemori,
    KurasiPostgres,
    PengisiAntrean,
    PengisiAntreanPostgres,
    PenyimpanKurasi,
)
from src.penyimpanan.penemuan import (
    PERAN_PENAYANGAN,
    PenemuanMemori,
    PenemuanPostgres,
    PenyimpanPenemuan,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

T0 = datetime(2026, 10, 5, 1, 0, tzinfo=UTC)
HARI = date(2026, 10, 5)
KURATOR = "psd_kkkkkkkkkkkkkkkk"


def _acak(n: int = 16) -> str:
    return "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))


def _psd() -> str:
    return "psd_" + _acak()


def _kandidat(kategori: str = "K5", dokumen: str | None = None, status: str | None = None):
    id_butir = "b-" + _acak(10)
    return BarisKandidat(
        id_butir=id_butir,
        butir={"id_butir": id_butir, "judul": "Judul uji", "kategori": kategori},
        sumber={"judul": "Sumber", "penerbit": "Penerbit", "tahun": 2025, "tautan": None},
        id_dokumen_sumber=dokumen or "dok-" + _acak(8),
        kategori=kategori,
        status_keberlakuan=status,
        masuk_pada=T0,
        kembali_pada=None,
    )


def _putusan(id_butir: str, jenis: str, alasan: str = "Layak tayang", waktu: datetime = T0):
    return CatatanPutusan(
        id_butir=id_butir,
        jenis=jenis,
        peran="kurator",
        pseudonim_kurator=KURATOR,
        alasan=alasan,
        waktu=waktu,
    )


@dataclass
class Tiga:
    pengisi: PengisiAntrean
    kurasi: PenyimpanKurasi
    penemuan: PenyimpanPenemuan


@pytest.fixture(params=["memori", "postgres"])
def simpan(request: pytest.FixtureRequest) -> Tiga:
    if request.param == "memori":
        kurasi = KurasiMemori()
        return Tiga(pengisi=kurasi, kurasi=kurasi, penemuan=PenemuanMemori(kurasi))
    return Tiga(
        pengisi=PengisiAntreanPostgres(SambunganPeran(PERAN_PENGISI_ANTREAN)),  # type: ignore[arg-type]
        kurasi=KurasiPostgres(SambunganPeran(PERAN_KURASI)),  # type: ignore[arg-type]
        penemuan=PenemuanPostgres(SambunganPeran(PERAN_PENAYANGAN)),  # type: ignore[arg-type]
    )


def _id(baris: tuple[object, ...]) -> set[str]:
    return {b.id_butir for b in baris}  # type: ignore[attr-defined]


# ── antrean ──────────────────────────────────────────────────────────


def test_kandidat_masuk_antrean_sekali(simpan: Tiga) -> None:
    async def uji() -> None:
        k = _kandidat()
        assert await simpan.pengisi.tambah_kandidat(k)
        assert not await simpan.pengisi.tambah_kandidat(k)
        menunggu = await simpan.kurasi.menunggu(hari_ini=HARI)
        assert k.id_butir in _id(menunggu)
        satu = await simpan.kurasi.satu_menunggu(k.id_butir, hari_ini=HARI)
        assert satu is not None
        assert (satu.butir, satu.sumber, satu.kategori) == (k.butir, k.sumber, "K5")

    jalankan(uji())


def test_putusan_akhir_mengeluarkan_dari_antrean(simpan: Tiga) -> None:
    async def uji() -> None:
        tolak, setuju = _kandidat(), _kandidat()
        for k in (tolak, setuju):
            await simpan.pengisi.tambah_kandidat(k)
        assert await simpan.kurasi.tolak(_putusan(tolak.id_butir, "tolak", "TL-01"))
        assert await simpan.kurasi.setujui(_putusan(setuju.id_butir, "setujui"), butir=setuju.butir)
        menunggu = _id(await simpan.kurasi.menunggu(hari_ini=HARI))
        assert not {tolak.id_butir, setuju.id_butir} & menunggu
        # Putusan kedua atas butir yang sudah diputus ditolak, bukan ditimpa.
        assert not await simpan.kurasi.tolak(_putusan(setuju.id_butir, "tolak", "TL-02"))
        assert await simpan.kurasi.satu_menunggu(tolak.id_butir, hari_ini=HARI) is None

    jalankan(uji())


def test_tunda_kembali_pada_tanggalnya(simpan: Tiga) -> None:
    async def uji() -> None:
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        kembali = HARI + timedelta(days=7)
        assert await simpan.kurasi.tunda(_putusan(k.id_butir, "tunda", "Tunggu juknis"), kembali)
        assert k.id_butir not in _id(await simpan.kurasi.menunggu(hari_ini=HARI))
        sebelum = kembali - timedelta(days=1)
        assert k.id_butir not in _id(await simpan.kurasi.menunggu(hari_ini=sebelum))
        assert k.id_butir in _id(await simpan.kurasi.menunggu(hari_ini=kembali))
        # Tunda bukan putusan akhir: sesudah kembali, butir dapat disetujui.
        assert await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)

    jalankan(uji())


def test_butir_yang_tayang_adalah_naskah_putusan(simpan: Tiga) -> None:
    """Sunting lalu setujui: yang tayang hasil suntingan, sumber tetap dari kandidat."""

    async def uji() -> None:
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        sunting = {**k.butir, "judul": "Judul hasil suntingan"}
        assert await simpan.kurasi.setujui(
            _putusan(k.id_butir, "sunting_lalu_setujui"), butir=sunting
        )
        tayang = await simpan.penemuan.baca_tayang(k.id_butir)
        assert tayang is not None
        assert tayang.butir["judul"] == "Judul hasil suntingan"
        assert tayang.sumber == k.sumber
        assert tayang.tayang_pada == T0 and tayang.ditarik_pada is None

    jalankan(uji())


def test_setujui_menuntut_jenis_yang_menyetujui(simpan: Tiga) -> None:
    async def uji() -> None:
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        with pytest.raises(ValueError):
            await simpan.kurasi.setujui(_putusan(k.id_butir, "tolak", "TL-01"), butir=k.butir)
        with pytest.raises(ValueError):
            await simpan.kurasi.tolak(_putusan(k.id_butir, "setujui"))

    jalankan(uji())


def test_putusan_atas_butir_tak_dikenal(simpan: Tiga) -> None:
    async def uji() -> None:
        assert not await simpan.kurasi.tolak(_putusan("b-tak-ada-" + _acak(6), "tolak", "TL-01"))

    jalankan(uji())


@pytest.mark.parametrize("pemutus", ["ks-017", "", "psd_0123456789abcdef"])
def test_pemutus_bukan_pseudonim_ditolak(simpan: Tiga, pemutus: str) -> None:
    """K-5, C-05 — kedua pelaksana menolak sama."""
    catatan = CatatanPutusan(
        id_butir="b-x",
        jenis="tolak",
        peran="kurator",
        pseudonim_kurator=pemutus,
        alasan="TL-01",
        waktu=T0,
    )
    with pytest.raises(ValueError):
        jalankan(simpan.kurasi.tolak(catatan))


def test_waktu_tanpa_zona_ditolak(simpan: Tiga) -> None:
    with pytest.raises(ValueError):
        jalankan(simpan.kurasi.tolak(_putusan("b-x", "tolak", "TL-01", datetime(2026, 10, 5))))


# ── status regulasi dan penarikan ────────────────────────────────────


def test_status_regulasi_diperbarui_pada_kandidat_dan_tayang(simpan: Tiga) -> None:
    """K-4: satu dokumen, dua butir — satu menunggu, satu tayang."""

    async def uji() -> None:
        dokumen = "dok-" + _acak(8)
        menunggu, tayang = (
            _kandidat(dokumen=dokumen, status="berlaku"),
            _kandidat(dokumen=dokumen, status="berlaku"),
        )
        for k in (menunggu, tayang):
            await simpan.pengisi.tambah_kandidat(k)
        await simpan.kurasi.setujui(_putusan(tayang.id_butir, "setujui"), butir=tayang.butir)
        aktif = await simpan.pengisi.perbarui_status(dokumen, "dicabut")
        assert aktif == (tayang.id_butir,)
        satu = await simpan.kurasi.satu_menunggu(menunggu.id_butir, hari_ini=HARI)
        assert satu is not None and satu.status_keberlakuan == "dicabut"
        baris = await simpan.penemuan.baca_tayang(tayang.id_butir)
        assert baris is not None and baris.status_keberlakuan == "dicabut"

    jalankan(uji())


def test_status_di_luar_tiga_nilai_ditolak(simpan: Tiga) -> None:
    with pytest.raises(ValueError):
        jalankan(simpan.pengisi.perbarui_status("dok-x", "kedaluwarsa"))


def test_penarikan_otomatis_dan_oleh_kurator(simpan: Tiga) -> None:
    async def uji() -> None:
        a, b = _kandidat(), _kandidat()
        for k in (a, b):
            await simpan.pengisi.tambah_kandidat(k)
            await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        assert await simpan.pengisi.tarik_otomatis(a.id_butir, "Regulasi dicabut", sekarang=T0)
        assert not await simpan.pengisi.tarik_otomatis(a.id_butir, "Lagi", sekarang=T0)
        assert await simpan.kurasi.tarik(
            b.id_butir,
            pemicu="kekeliruan_isi_dilaporkan",
            tindakan="ditarik",
            peran="kurator",
            pseudonim_kurator=KURATOR,
            alasan="Angka keliru",
            sekarang=T0,
        )
        for k in (a, b):
            baris = await simpan.penemuan.baca_tayang(k.id_butir)
            assert baris is not None and baris.ditarik_pada == T0
        aktif = _id(await simpan.kurasi.tayang_aktif())
        assert not {a.id_butir, b.id_butir} & aktif

    jalankan(uji())


def test_ditandai_perlu_tinjauan_tetap_tayang(simpan: Tiga) -> None:
    async def uji() -> None:
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        assert await simpan.kurasi.tarik(
            k.id_butir,
            pemicu="data_sumber_diperbarui",
            tindakan="ditandai_perlu_tinjauan",
            peran="kurator",
            pseudonim_kurator=KURATOR,
            alasan="Data tahun baru terbit",
            sekarang=T0,
        )
        aktif = {b.id_butir: b for b in await simpan.kurasi.tayang_aktif()}
        assert k.id_butir in aktif
        assert aktif[k.id_butir].perlu_tinjauan_pada == T0

    jalankan(uji())


def test_penarikan_atas_butir_yang_tidak_tayang(simpan: Tiga) -> None:
    async def uji() -> None:
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        assert not await simpan.kurasi.tarik(
            k.id_butir,
            pemicu="kekeliruan_isi_dilaporkan",
            tindakan="ditarik",
            peran="kurator",
            pseudonim_kurator=KURATOR,
            alasan="x",
            sekarang=T0,
        )

    jalankan(uji())


# ── penemuan ─────────────────────────────────────────────────────────


def test_hanya_butir_tayang_aktif_tersedia(simpan: Tiga) -> None:
    """R-02: kandidat dan butir yang ditarik tidak pernah tersedia bagi feed."""

    async def uji() -> None:
        kategori = "K" + str(secrets.randbelow(8) + 1)
        tunggu, tayang, tarik = (_kandidat(kategori) for _ in range(3))
        for k in (tunggu, tayang, tarik):
            await simpan.pengisi.tambah_kandidat(k)
        for k in (tayang, tarik):
            await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        await simpan.pengisi.tarik_otomatis(tarik.id_butir, "dicabut", sekarang=T0)
        tersedia = _id(await simpan.penemuan.tayang_menurut_kategori((kategori,)))
        assert tayang.id_butir in tersedia
        assert not {tunggu.id_butir, tarik.id_butir} & tersedia
        assert await simpan.penemuan.baca_tayang(tunggu.id_butir) is None

    jalankan(uji())


def test_butir_hari_ini_tercatat_dan_dibaca_ulang(simpan: Tiga) -> None:
    """K-2: pemanggilan berikutnya membaca catatan yang sama, berurutan."""

    async def uji() -> None:
        p = _psd()
        ks = [_kandidat() for _ in range(3)]
        for k in ks:
            await simpan.pengisi.tambah_kandidat(k)
            await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        assert await simpan.penemuan.catatan_hari_ini(p, HARI) == ()
        urut = tuple(k.id_butir for k in reversed(ks))
        await simpan.penemuan.catat_hari_ini(p, HARI, urut, sekarang=T0)
        assert await simpan.penemuan.catatan_hari_ini(p, HARI) == urut
        assert await simpan.penemuan.catatan_hari_ini(p, HARI + timedelta(days=1)) == ()
        assert await simpan.penemuan.pernah_tayang(p) == frozenset(urut)
        assert await simpan.penemuan.pernah_tayang(_psd()) == frozenset()

    jalankan(uji())


def test_butir_tidak_tayang_dua_kali_bagi_orang_yang_sama(simpan: Tiga) -> None:
    async def uji() -> None:
        p = _psd()
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        await simpan.penemuan.catat_hari_ini(p, HARI, (k.id_butir,), sekarang=T0)
        # Pencatatan ganda pada hari yang sama tidak menggandakan maupun gagal —
        # dua pemanggilan beranda serentak memilih himpunan yang sama.
        await simpan.penemuan.catat_hari_ini(p, HARI, (k.id_butir,), sekarang=T0)
        assert await simpan.penemuan.catatan_hari_ini(p, HARI) == (k.id_butir,)
        # Pada hari lain butir itu tidak tercatat lagi.
        await simpan.penemuan.catat_hari_ini(
            p, HARI + timedelta(days=1), (k.id_butir,), sekarang=T0
        )
        assert await simpan.penemuan.catatan_hari_ini(p, HARI + timedelta(days=1)) == ()

    jalankan(uji())


def test_belum_relevan_tercatat(simpan: Tiga) -> None:
    async def uji() -> None:
        p = _psd()
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        assert await simpan.penemuan.ditolak(p) == frozenset()
        await simpan.penemuan.catat_belum_relevan(p, k.id_butir, "Bukan prioritas", sekarang=T0)
        await simpan.penemuan.catat_belum_relevan(p, k.id_butir, "Masih belum", sekarang=T0)
        assert await simpan.penemuan.ditolak(p) == frozenset({k.id_butir})

    jalankan(uji())


@pytest.mark.parametrize("pemilik", ["ks-017", "", "PSD_AAAAAAAAAAAAAAAA"])
def test_pemilik_penemuan_bukan_pseudonim_ditolak(simpan: Tiga, pemilik: str) -> None:
    with pytest.raises(ValueError):
        jalankan(simpan.penemuan.catat_hari_ini(pemilik, HARI, ("b-x",), sekarang=T0))
    with pytest.raises(ValueError):
        jalankan(simpan.penemuan.catat_belum_relevan(pemilik, "b-x", "alasan", sekarang=T0))


def test_alasan_kosong_ditolak(simpan: Tiga) -> None:
    with pytest.raises(ValueError):
        jalankan(simpan.penemuan.catat_belum_relevan(_psd(), "b-x", "  ", sekarang=T0))


def test_permukaan_tanpa_hapus() -> None:
    for kelas in (
        KurasiMemori,
        KurasiPostgres,
        PengisiAntreanPostgres,
        PenemuanMemori,
        PenemuanPostgres,
    ):
        nama = {n for n in dir(kelas) if not n.startswith("_")}
        assert not {n for n in nama if "hapus" in n or "ubah" in n}, kelas.__name__


def test_penayang_tidak_memiliki_cara_membaca_antrean() -> None:
    """R-02 pada permukaan: penyimpan penemuan tidak menyebut kandidat."""
    nama = {n for n in dir(PenemuanPostgres) if not n.startswith("_")}
    assert not {n for n in nama if "kandidat" in n or "menunggu" in n or "putusan" in n}


# ── penolakan bentuk — kedua pelaksana menolak sama ──────────────────


def test_putusan_tanpa_alasan_atau_peran_sah_ditolak(simpan: Tiga) -> None:
    kosong = CatatanPutusan(
        id_butir="b-x",
        jenis="tolak",
        peran="kurator",
        pseudonim_kurator=KURATOR,
        alasan="  ",
        waktu=T0,
    )
    peran_lain = CatatanPutusan(
        id_butir="b-x",
        jenis="tolak",
        peran="penanggung_jawab_teknis",
        pseudonim_kurator=KURATOR,
        alasan="TL-01",
        waktu=T0,
    )
    for catatan in (kosong, peran_lain):
        with pytest.raises(ValueError):
            jalankan(simpan.kurasi.tolak(catatan))


def test_kandidat_berbentuk_salah_ditolak(simpan: Tiga) -> None:
    sah = _kandidat()
    for salah in (
        BarisKandidat(**{**sah.__dict__, "kategori": "K9"}),
        BarisKandidat(**{**sah.__dict__, "status_keberlakuan": "kedaluwarsa"}),
        BarisKandidat(**{**sah.__dict__, "id_dokumen_sumber": " "}),
        BarisKandidat(**{**sah.__dict__, "masuk_pada": datetime(2026, 10, 5)}),
    ):
        with pytest.raises(ValueError):
            jalankan(simpan.pengisi.tambah_kandidat(salah))


def test_penarikan_berbentuk_salah_ditolak(simpan: Tiga) -> None:
    for argumen in (
        {"pemicu": "bosan", "tindakan": "ditarik", "peran": "kurator"},
        {"pemicu": "data_sumber_diperbarui", "tindakan": "dihapus", "peran": "kurator"},
        {"pemicu": "data_sumber_diperbarui", "tindakan": "ditarik", "peran": "peneliti"},
    ):
        with pytest.raises(ValueError):
            jalankan(
                simpan.kurasi.tarik(
                    "b-x", pseudonim_kurator=KURATOR, alasan="x", sekarang=T0, **argumen
                )
            )
    with pytest.raises(ValueError):
        jalankan(
            simpan.kurasi.tarik(
                "b-x",
                pemicu="data_sumber_diperbarui",
                tindakan="ditarik",
                peran="kurator",
                pseudonim_kurator="ks-017",
                alasan="x",
                sekarang=T0,
            )
        )


def test_putusan_atas_butir_tak_dikenal_ketiga_jenis(simpan: Tiga) -> None:
    async def uji() -> None:
        tak_ada = "b-tak-ada-" + _acak(6)
        assert not await simpan.kurasi.setujui(_putusan(tak_ada, "setujui"), butir={})
        assert not await simpan.kurasi.tunda(_putusan(tak_ada, "tunda"), HARI)

    jalankan(uji())


def test_status_hanya_mengenai_dokumennya_dan_tidak_menyebut_yang_ditarik(simpan: Tiga) -> None:
    async def uji() -> None:
        dokumen = "dok-" + _acak(8)
        lain, ditarik, aktif = (
            _kandidat(status="berlaku"),
            _kandidat(dokumen=dokumen, status="berlaku"),
            _kandidat(dokumen=dokumen, status="berlaku"),
        )
        for k in (lain, ditarik, aktif):
            await simpan.pengisi.tambah_kandidat(k)
            await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        await simpan.pengisi.tarik_otomatis(ditarik.id_butir, "dicabut", sekarang=T0)
        assert await simpan.pengisi.perbarui_status(dokumen, "diubah") == (aktif.id_butir,)
        tetap = await simpan.penemuan.baca_tayang(lain.id_butir)
        assert tetap is not None and tetap.status_keberlakuan == "berlaku"

    jalankan(uji())


def test_waktu_penemuan_tanpa_zona_ditolak(simpan: Tiga) -> None:
    with pytest.raises(ValueError):
        jalankan(
            simpan.penemuan.catat_hari_ini(_psd(), HARI, ("b-x",), sekarang=datetime(2026, 1, 1))
        )


def test_kolom_json_yang_bukan_objek_ditolak_terang() -> None:
    from src.penyimpanan.kurasi import json_dari

    assert json_dari('{"a": 1}') == {"a": 1}
    assert json_dari({"a": 1}) == {"a": 1}
    with pytest.raises(TypeError):
        json_dari("[1, 2]")


def test_dokumen_dikenal_bagi_lapis_l2(simpan: Tiga) -> None:
    async def uji() -> None:
        k = _kandidat()
        assert k.id_dokumen_sumber not in await simpan.pengisi.dokumen_dikenal()
        await simpan.pengisi.tambah_kandidat(k)
        assert k.id_dokumen_sumber in await simpan.pengisi.dokumen_dikenal()

    jalankan(uji())


def test_daftar_tayang_kurator_membawa_putusannya(simpan: Tiga) -> None:
    """Rute penarikan membentuk ulang `ButirTayang` dari putusan sungguhan."""

    async def uji() -> None:
        k = _kandidat()
        await simpan.pengisi.tambah_kandidat(k)
        await simpan.kurasi.setujui(_putusan(k.id_butir, "sunting_lalu_setujui"), butir=k.butir)
        aktif = {b.id_butir: b for b in await simpan.kurasi.tayang_aktif()}
        putusan = aktif[k.id_butir].putusan
        assert putusan is not None
        assert (putusan.jenis, putusan.peran, putusan.waktu) == (
            "sunting_lalu_setujui",
            "kurator",
            T0,
        )
        # Penayang menerima ketiga kolom yang sama — tanpa pemutus (KB-185).
        baris = await simpan.penemuan.baca_tayang(k.id_butir)
        assert baris is not None and baris.putusan == putusan
        assert not hasattr(baris.putusan, "pseudonim_kurator")

    jalankan(uji())


def test_butir_yang_menyusul_berurutan_di_belakang(simpan: Tiga) -> None:
    async def uji() -> None:
        p = _psd()
        ks = [_kandidat() for _ in range(3)]
        for k in ks:
            await simpan.pengisi.tambah_kandidat(k)
            await simpan.kurasi.setujui(_putusan(k.id_butir, "setujui"), butir=k.butir)
        await simpan.penemuan.catat_hari_ini(p, HARI, (ks[2].id_butir,), sekarang=T0)
        await simpan.penemuan.catat_hari_ini(
            p, HARI, (ks[0].id_butir, ks[1].id_butir), sekarang=T0, mulai=2
        )
        assert await simpan.penemuan.catatan_hari_ini(p, HARI) == (
            ks[2].id_butir,
            ks[0].id_butir,
            ks[1].id_butir,
        )

    jalankan(uji())


def test_jumlah_masuk_antrean_dalam_rentang(simpan: Tiga) -> None:
    """Bagi pagu kurasi harian TK-72 B — dihitung dari `masuk_pada`."""

    async def uji() -> None:
        awal = datetime(2050 + secrets.randbelow(900), 3, 3, 17, 0, tzinfo=UTC)
        akhir = awal + timedelta(days=1)
        assert await simpan.pengisi.jumlah_masuk(sejak=awal, sampai=akhir) == 0
        for geser in (timedelta(0), timedelta(hours=23, minutes=59), timedelta(days=1)):
            k = _kandidat()
            await simpan.pengisi.tambah_kandidat(
                BarisKandidat(**{**k.__dict__, "masuk_pada": awal + geser})
            )
        assert await simpan.pengisi.jumlah_masuk(sejak=awal, sampai=akhir) == 2

    jalankan(uji())
