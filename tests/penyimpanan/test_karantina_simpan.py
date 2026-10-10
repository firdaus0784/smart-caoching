"""Catatan gerbang ingesti — T-4 fitur 037, R-03, R-06, R-09, R-11; K-1, K-3.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL. Yang kedua
tersambung **sebagai peran tiap perintah** (TK-64, TK-83): `terima` sebagai
`peran_ingesti`, putusan sebagai `peran_verifikasi`, pencabutan sebagai
`peran_penarikan_dokumen`. Uji yang tersambung sebagai pengelola tidak
membuktikan apa pun tentang peran — pelajaran yang melahirkan TK-83.

Keadaan gerbang **diturunkan** dari catatan tambah-saja (P-1 A): penerimaan
terbaru menentukan temuan, tinjauan, status anonimisasi, dan status
persetujuan.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

import pytest
from src.kamus.gerbang import PutusanGerbang
from src.penyimpanan.area import Area
from src.penyimpanan.dasar import BarisJejak, MetadataDokumen, PenyimpanDasar
from src.penyimpanan.galat import GalatAksesDitolak, GalatDokumenDiKorpus, GalatDokumenTidakAda
from src.penyimpanan.karantina import (
    PERAN_INGESTI,
    PERAN_PENARIKAN_DOKUMEN,
    PERAN_VERIFIKASI,
    CatatanGerbang,
    CatatanGerbangMemori,
    CatatanGerbangPostgres,
    CatatanPenerimaan,
    TemuanPola,
)
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.kredensial_baku import PENJAWABAN, VERIFIKASI
from src.penyimpanan.postgres import PenyimpanPostgres
from src.penyimpanan.tiruan import PenyimpanTiruan
from tests.konftes_asinkron import jalankan
from tests.peladen import psql, siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

INGESTI = Kredensial(
    nama="ingesti",
    baca=frozenset(),
    tulis=frozenset({Area.KARANTINA}),
    indeks=frozenset(),
    tulis_indeks=frozenset(),
)
PENARIKAN = Kredensial(
    nama="penarikan",
    baca=frozenset({Area.KORPUS}),
    tulis=frozenset({Area.KARANTINA}),
    indeks=frozenset(),
    tulis_indeks=frozenset(),
)
SAMARAN = {"nik": 1, "nip": 0, "nisn": 0, "nuptk": 0, "telepon": 0, "rekening": 0}
TEMUAN = (TemuanPola(pola="abaikan instruksi", mulai=0, akhir=17, kutipan="abaikan instruksi"),)
METADATA = MetadataDokumen(
    judul="Notulen rapat pleno",
    jenis="dokumen_sekolah",
    penerbit="SDN Sukamaju",
    tahun=2026,
    tingkat_kerahasiaan="internal_sekolah",
)


@dataclass
class Pelaksana:
    """Satu catatan per peran. Pada memori ketiganya objek yang sama."""

    ingesti: CatatanGerbang
    verifikasi: CatatanGerbang
    penarikan: CatatanGerbang
    teks: PenyimpanDasar
    postgres: bool


@pytest.fixture(params=["memori", "postgres"])
def pelaksana(request: pytest.FixtureRequest) -> Pelaksana:
    if request.param == "memori":
        catatan = CatatanGerbangMemori(PenyimpanTiruan())
        return Pelaksana(catatan, catatan, catatan, catatan.penyimpan, postgres=False)
    return Pelaksana(
        _catatan_pg(PERAN_INGESTI),
        _catatan_pg(PERAN_VERIFIKASI),
        _catatan_pg(PERAN_PENARIKAN_DOKUMEN),
        PenyimpanPostgres(SambunganPeran(PERAN_VERIFIKASI)),  # type: ignore[arg-type]
        postgres=True,
    )


def _catatan_pg(peran: str) -> CatatanGerbang:
    sambungan = SambunganPeran(peran)
    return CatatanGerbangPostgres(sambungan, PenyimpanPostgres(sambungan))  # type: ignore[arg-type]


def _id() -> str:
    return "dok-037-" + secrets.token_hex(4)


def _penerimaan(id_dokumen: str, **ubah: object) -> CatatanPenerimaan:
    bidang: dict[str, object] = {
        "id_dokumen": id_dokumen,
        "judul": "Notulen rapat pleno",
        "jenis": "dokumen_sekolah",
        "penerbit": "SDN Sukamaju",
        "tahun": 2026,
        "tingkat_kerahasiaan": "internal_sekolah",
        "status_persetujuan_pemilik": "diberikan",
        "samaran": SAMARAN,
        "id_penerima": "tm-001",
    }
    bidang.update(ubah)
    return CatatanPenerimaan(**bidang)  # type: ignore[arg-type]


def _terima(p: Pelaksana, id_dokumen: str, teks: str = "Notulen [NIK]", **ubah: object) -> None:
    jalankan(p.ingesti.terima(INGESTI, _penerimaan(id_dokumen, **ubah), teks, TEMUAN))


def test_terima_lalu_keadaannya_menunggu(pelaksana: Pelaksana) -> None:
    d = _id()
    _terima(pelaksana, d)
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert keadaan.penerimaan == _penerimaan(d)
    assert keadaan.area is Area.KARANTINA
    assert keadaan.temuan == TEMUAN
    assert (keadaan.ditinjau, keadaan.catatan_tinjauan) == (False, "")
    assert keadaan.status_anonimisasi == "menunggu"
    assert keadaan.persetujuan_dicabut is False
    assert keadaan.alasan_terakhir == ""
    assert jalankan(pelaksana.teks.baca_dokumen(VERIFIKASI, Area.KARANTINA, d)) == "Notulen [NIK]"


def test_dokumen_tak_dikenal_tanpa_keadaan(pelaksana: Pelaksana) -> None:
    assert jalankan(pelaksana.verifikasi.keadaan(_id())) is None


def test_unggahan_ulang_membatalkan_tinjauan_dan_mengganti_teks(pelaksana: Pelaksana) -> None:
    """R-03, bertahan antarobjek: tinjauan merujuk penerimaan, bukan dokumen.
    M-7 fitur 037 merah di sini."""
    d = _id()
    _terima(pelaksana, d)
    jalankan(pelaksana.verifikasi.tinjau(VERIFIKASI, d, "tm-002", "kutipan peraturan"))
    sesudah_tinjau = jalankan(pelaksana.verifikasi.keadaan(d))
    assert sesudah_tinjau is not None
    assert (sesudah_tinjau.ditinjau, sesudah_tinjau.catatan_tinjauan) == (
        True,
        "kutipan peraturan",
    )

    jalankan(pelaksana.ingesti.terima(INGESTI, _penerimaan(d, judul="Versi dua"), "Versi dua", ()))
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert (keadaan.ditinjau, keadaan.catatan_tinjauan, keadaan.temuan) == (False, "", ())
    assert keadaan.penerimaan.judul == "Versi dua"
    assert jalankan(pelaksana.teks.baca_dokumen(VERIFIKASI, Area.KARANTINA, d)) == "Versi dua"


def test_tolak_lalu_status_dan_alasannya(pelaksana: Pelaksana) -> None:
    d = _id()
    _terima(pelaksana, d)
    jalankan(pelaksana.verifikasi.tolak(VERIFIKASI, d, "tm-002", "nama guru pada halaman 3"))
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert (keadaan.status_anonimisasi, keadaan.area) == ("ditolak", Area.KARANTINA)
    assert keadaan.alasan_terakhir == "nama guru pada halaman 3"


def test_status_hanya_dari_penerimaan_terbaru(pelaksana: Pelaksana) -> None:
    """M-12: penolakan atas unggahan lama tidak berlaku bagi unggahan baru,
    sedangkan alasannya tetap terbaca sebagai alasan terakhir."""
    d = _id()
    _terima(pelaksana, d)
    jalankan(pelaksana.verifikasi.tolak(VERIFIKASI, d, "tm-002", "nama guru pada halaman 3"))
    _terima(pelaksana, d)
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert keadaan.status_anonimisasi == "menunggu"
    assert keadaan.alasan_terakhir == "nama guru pada halaman 3"


def test_setujui_memindahkan_dengan_metadata_dan_jejak(pelaksana: Pelaksana) -> None:
    d = _id()
    _terima(pelaksana, d)
    jalankan(
        pelaksana.verifikasi.setujui(VERIFIKASI, d, "tm-002", "anonimisasi terperiksa", METADATA)
    )
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert (keadaan.area, keadaan.status_anonimisasi) == (Area.KORPUS, "terverifikasi")
    assert jalankan(pelaksana.teks.baca_dokumen(PENJAWABAN, Area.KORPUS, d)) == "Notulen [NIK]"
    if pelaksana.postgres:
        hasil = psql(
            "smart_coaching",
            "-c",
            f"select (select count(*) from korpus.metadata_dokumen where id_dokumen = '{d}') "
            "|| ':' || (select string_agg(putusan || '/' || dari_area || '/' || ke_area "
            f"|| '/' || id_pelaku, ',') from karantina.jejak_area where id_dokumen = '{d}')",
        )
        assert hasil.stdout.split() == ["1:setujui/karantina/korpus/tm-002"]
    else:
        assert isinstance(pelaksana.teks, PenyimpanTiruan)
        assert pelaksana.teks.metadata_tercatat(d) == (METADATA,)


def test_unggahan_ulang_atas_dokumen_korpus_ditolak(pelaksana: Pelaksana) -> None:
    """R-11, TK-85 A: tidak satu catatan pun tersimpan, versi korpus utuh.
    M-10 fitur 037 merah di sini."""
    d = _id()
    _terima(pelaksana, d)
    jalankan(
        pelaksana.verifikasi.setujui(VERIFIKASI, d, "tm-002", "anonimisasi terperiksa", METADATA)
    )
    with pytest.raises(GalatDokumenDiKorpus):
        jalankan(pelaksana.ingesti.terima(INGESTI, _penerimaan(d, judul="Versi dua"), "v2", ()))
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert (keadaan.area, keadaan.penerimaan.judul) == (Area.KORPUS, "Notulen rapat pleno")
    assert jalankan(pelaksana.teks.baca_dokumen(PENJAWABAN, Area.KORPUS, d)) == "Notulen [NIK]"


def test_cabut_dari_korpus_mengeluarkan_dokumen(pelaksana: Pelaksana) -> None:
    """R-09: tanpa kredensial verifikator."""
    d = _id()
    _terima(pelaksana, d)
    jalankan(
        pelaksana.verifikasi.setujui(VERIFIKASI, d, "tm-002", "anonimisasi terperiksa", METADATA)
    )
    dari = jalankan(pelaksana.penarikan.cabut(PENARIKAN, d, "tm-003", "pemilik menarik izin"))
    assert dari is Area.KORPUS
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert (keadaan.area, keadaan.persetujuan_dicabut) == (Area.KARANTINA, True)
    with pytest.raises(GalatDokumenTidakAda):
        jalankan(pelaksana.teks.baca_dokumen(PENJAWABAN, Area.KORPUS, d))


def test_cabut_selagi_di_karantina(pelaksana: Pelaksana) -> None:
    d = _id()
    _terima(pelaksana, d)
    dari = jalankan(pelaksana.penarikan.cabut(PENARIKAN, d, "tm-003", "pemilik menarik izin"))
    assert dari is Area.KARANTINA
    keadaan = jalankan(pelaksana.verifikasi.keadaan(d))
    assert keadaan is not None
    assert (keadaan.area, keadaan.persetujuan_dicabut) == (Area.KARANTINA, True)
    assert keadaan.alasan_terakhir == "pemilik menarik izin"


def test_cabut_dokumen_tak_dikenal(pelaksana: Pelaksana) -> None:
    with pytest.raises(GalatDokumenTidakAda):
        jalankan(pelaksana.penarikan.cabut(PENARIKAN, _id(), "tm-003", "pemilik menarik izin"))


def test_putusan_atas_dokumen_tak_dikenal(pelaksana: Pelaksana) -> None:
    """Tinjauan dan penolakan tanpa penerimaan tidak mencatat apa pun."""
    d = _id()
    with pytest.raises(GalatDokumenTidakAda):
        jalankan(pelaksana.verifikasi.tinjau(VERIFIKASI, d, "tm-002", "x"))
    with pytest.raises(GalatDokumenTidakAda):
        jalankan(pelaksana.verifikasi.tolak(VERIFIKASI, d, "tm-002", "x"))
    assert jalankan(pelaksana.verifikasi.keadaan(d)) is None


def test_kredensial_diperiksa_sebelum_apa_pun(pelaksana: Pelaksana) -> None:
    """Dua lapis pada PostgreSQL: kredensial kode lebih dulu, peladen sesudahnya."""
    d = _id()
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.ingesti.terima(VERIFIKASI, _penerimaan(d), "x", ()))
    assert jalankan(pelaksana.verifikasi.keadaan(d)) is None
    _terima(pelaksana, d)
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.verifikasi.tolak(PENJAWABAN, d, "tm-002", "x"))
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.verifikasi.tinjau(INGESTI, d, "tm-002", "x"))
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.penarikan.cabut(VERIFIKASI, d, "tm-003", "x"))
    with pytest.raises(GalatAksesDitolak):
        jalankan(pelaksana.verifikasi.setujui(INGESTI, d, "tm-002", "x", METADATA))


# ── PostgreSQL saja: atomik dan segmen ──────────────────────────────────


def _pg() -> Pelaksana:
    return Pelaksana(
        _catatan_pg(PERAN_INGESTI),
        _catatan_pg(PERAN_VERIFIKASI),
        _catatan_pg(PERAN_PENARIKAN_DOKUMEN),
        PenyimpanPostgres(SambunganPeran(PERAN_VERIFIKASI)),  # type: ignore[arg-type]
        postgres=True,
    )


def test_jejak_yang_ditolak_membatalkan_pemindahan() -> None:
    """R-06, M-5: pelaku tidak berpola ditolak batasan tabel. Bila jejak
    ditulis dalam pernyataan terpisah, dokumen berpindah tanpa jejak."""
    p = _pg()
    d = _id()
    _terima(p, d)
    with pytest.raises(Exception, match="jejak_pelaku"):
        jalankan(p.verifikasi.setujui(VERIFIKASI, d, "Budi Santoso", "terperiksa", METADATA))
    keadaan = jalankan(p.verifikasi.keadaan(d))
    assert keadaan is not None
    assert (keadaan.area, keadaan.status_anonimisasi) == (Area.KARANTINA, "menunggu")
    hasil = psql(
        "smart_coaching",
        "-c",
        f"select count(*) from korpus.metadata_dokumen where id_dokumen = '{d}'",
    )
    assert hasil.stdout.split() == ["0"]


def _tanam_segmen(id_dokumen: str) -> None:
    for indeks, lisensi in (("indeks_utama", "terbuka"), ("indeks_metadata", "tertutup")):
        hasil = psql(
            "smart_coaching",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            f"insert into {indeks}.segmen_teks (id_segmen, id_dokumen, teks, lisensi, "
            f"anonimisasi_terverifikasi, penanda_bagian) values ('{id_dokumen}-{indeks}', "
            f"'{id_dokumen}', 'Rapat pleno.', '{lisensi}', true, 'Bagian 1')",
        )
        assert hasil.returncode == 0, hasil.stderr


def _jumlah_segmen(id_dokumen: str) -> str:
    return psql(
        "smart_coaching",
        "-c",
        f"select (select count(*) from indeks_utama.segmen_teks where id_dokumen = '{id_dokumen}')"
        f" + (select count(*) from indeks_metadata.segmen_teks where id_dokumen = '{id_dokumen}')",
    ).stdout.strip()


def test_cabut_menghapus_segmen_kedua_indeks() -> None:
    """TK-84 A, M-6: dokumen yang persetujuannya ditarik tidak terambil lagi."""
    p = _pg()
    d = _id()
    _terima(p, d)
    jalankan(p.verifikasi.setujui(VERIFIKASI, d, "tm-002", "anonimisasi terperiksa", METADATA))
    _tanam_segmen(d)
    assert _jumlah_segmen(d) == "2"
    jalankan(p.penarikan.cabut(PENARIKAN, d, "tm-003", "pemilik menarik izin"))
    assert _jumlah_segmen(d) == "0"


def test_pindahkan_keluar_korpus_selalu_membawa_segmen() -> None:
    """Aturan milik setiap pemindahan keluar dari korpus, bukan hanya
    pencabutan (K-3). Tersambung sebagai peran penarikan dokumen."""
    p = _pg()
    d = _id()
    _terima(p, d)
    jalankan(p.verifikasi.setujui(VERIFIKASI, d, "tm-002", "anonimisasi terperiksa", METADATA))
    _tanam_segmen(d)
    penarik = PenyimpanPostgres(SambunganPeran(PERAN_PENARIKAN_DOKUMEN))  # type: ignore[arg-type]
    jalankan(penarik.pindahkan(PENARIKAN, d, Area.KORPUS, Area.KARANTINA, "uji"))
    assert _jumlah_segmen(d) == "0"


# ── `pindahkan(jejak=)` pada kedua penyimpan dokumen ─────────────────────


@pytest.mark.parametrize(
    ("dari", "ke", "putusan"),
    [
        (Area.KORPUS, Area.KARANTINA, PutusanGerbang.SETUJUI),
        (Area.KARANTINA, Area.KORPUS, PutusanGerbang.CABUT_PERSETUJUAN),
        (Area.KARANTINA, Area.KORPUS, PutusanGerbang.TOLAK),
    ],
)
def test_jejak_yang_tidak_sesuai_arahnya_ditolak_sebelum_apa_pun(
    dari: Area, ke: Area, putusan: PutusanGerbang
) -> None:
    jejak = BarisJejak(id_pelaku="tm-002", alasan="uji", putusan=putusan)
    for penyimpan in (
        PenyimpanTiruan(),
        PenyimpanPostgres(SambunganPeran(PERAN_VERIFIKASI)),  # type: ignore[arg-type]
    ):
        with pytest.raises(ValueError):
            jalankan(penyimpan.pindahkan(VERIFIKASI, "dok-tak-ada", dari, ke, "uji", jejak=jejak))


def test_tiruan_mencatat_jejak_bersama_pemindahan() -> None:
    tiruan = PenyimpanTiruan()
    tiruan.tanam(Area.KARANTINA, "d1", "teks")
    jejak = BarisJejak(id_pelaku="tm-002", alasan="lolos", putusan=PutusanGerbang.SETUJUI)
    jalankan(tiruan.pindahkan(VERIFIKASI, "d1", Area.KARANTINA, Area.KORPUS, "lolos", jejak=jejak))
    assert tiruan.jejak_tercatat("d1") == ((Area.KARANTINA, Area.KORPUS, jejak),)
    with pytest.raises(GalatDokumenTidakAda):
        jalankan(tiruan.pindahkan(VERIFIKASI, "d2", Area.KARANTINA, Area.KORPUS, "x", jejak=jejak))
    assert tiruan.jejak_tercatat("d2") == ()
