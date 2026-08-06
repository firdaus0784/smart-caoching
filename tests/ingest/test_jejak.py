"""Uji jejak perpindahan area — R-11, R-12, D-04 Bagian 7.2, D-14 Bagian 5.1.

Dua kebutuhan yang tampak terpisah tetapi satu tempatnya: R-11 menuntut setiap
perpindahan tercatat, dan R-12 menuntut catatannya tidak memuat data pribadi.
Yang kedua ada justru karena yang pertama — alasan penolakan verifikator
berbunyi alami "memuat NIK pada halaman 3", dan godaan menyalin potongannya
besar.
"""

import dataclasses

import pytest
from src.ingest.jejak import Baris, GalatJejak, JejakArea
from src.penyimpanan.area import Area

PELAKU = "vrf_001"


def _jejak() -> JejakArea:
    return JejakArea()


def test_perpindahan_menghasilkan_satu_baris() -> None:
    """R-11 — satu perpindahan, satu baris."""
    jejak = _jejak()
    jejak.catat(
        id_dokumen="dok_001",
        id_pelaku=PELAKU,
        dari_area=Area.KARANTINA,
        ke_area=Area.KORPUS,
        alasan="anonimisasi terverifikasi",
    )
    assert len(jejak.baris()) == 1


def test_baris_memuat_tujuh_bidang_D04() -> None:
    """Tujuh bidang D-04 Bagian 7.2, tidak kurang.

    Baris tanpa `id_pelaku` mencatat bahwa sesuatu berpindah tetapi tidak siapa
    yang memindahkannya, dan itu jejak yang tidak dapat dipertanggungjawabkan.
    """
    assert set(Baris.__dataclass_fields__) == {
        "id",
        "id_dokumen",
        "id_pelaku",
        "dari_area",
        "ke_area",
        "alasan",
        "waktu",
    }


def test_waktu_disimpan_UTC() -> None:
    """Gaya proyek: waktu disimpan UTC, bukan waktu setempat."""
    from datetime import UTC

    jejak = _jejak()
    jejak.catat(
        id_dokumen="dok_001",
        id_pelaku=PELAKU,
        dari_area=Area.KARANTINA,
        ke_area=Area.KORPUS,
        alasan="anonimisasi terverifikasi",
    )
    assert jejak.baris()[0].waktu.tzinfo is UTC


def test_baris_tidak_dapat_disunting() -> None:
    """Jejak yang dapat disunting bukan bukti."""
    jejak = _jejak()
    jejak.catat(
        id_dokumen="dok_001",
        id_pelaku=PELAKU,
        dari_area=Area.KARANTINA,
        ke_area=Area.KORPUS,
        alasan="anonimisasi terverifikasi",
    )
    baris = jejak.baris()[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        baris.alasan = "alasan lain"  # type: ignore[misc]


def test_daftar_yang_dikembalikan_bukan_daftar_aslinya() -> None:
    """Pemanggil yang menerima daftar aslinya dapat mengosongkannya.

    Kekekalan tiap baris tidak menolong bila daftarnya sendiri dapat dibuang.
    """
    jejak = _jejak()
    jejak.catat(
        id_dokumen="dok_001",
        id_pelaku=PELAKU,
        dari_area=Area.KARANTINA,
        ke_area=Area.KORPUS,
        alasan="anonimisasi terverifikasi",
    )
    jejak.baris().clear()
    assert len(jejak.baris()) == 1


def test_tidak_ada_jalan_menghapus_baris() -> None:
    """Dinyatakan sebagai sifat antarmukanya, bukan sebagai satu kasus.

    Metode penghapus yang ditambahkan kelak akan lolos uji yang hanya mencoba
    satu nama.
    """
    terlarang = {"hapus", "kosongkan", "sunting", "ubah", "buang", "setel_ulang"}
    assert terlarang.isdisjoint(dir(JejakArea))


def test_pelaku_wajib() -> None:
    """Perpindahan tanpa pelaku tidak dapat dipertanggungjawabkan."""
    jejak = _jejak()
    with pytest.raises(GalatJejak):
        jejak.catat(
            id_dokumen="dok_001",
            id_pelaku="",
            dari_area=Area.KARANTINA,
            ke_area=Area.KORPUS,
            alasan="anonimisasi terverifikasi",
        )


@pytest.mark.parametrize(
    "alasan",
    [
        "memuat NIK 3211012509870001 pada halaman 3",
        "NIP 196504121990031002 tertulis pada kop",
        "nomor telepon 081234567890 pada lampiran",
        "nomor telepon 0812-3456-7890 pada lampiran",
        "kontak +6281234567890 belum disamarkan",
    ],
)
def test_alasan_bermuatan_data_pribadi_ditolak(alasan: str) -> None:
    """R-12 — **ditolak, bukan disaring diam-diam.**

    Penyaringan diam-diam menghasilkan jejak yang tampak bersih, sehingga
    kebiasaan menyalin potongan data pribadi ke alasan tidak pernah berubah.
    Galat pada saat menulis mengubahnya sekali dan seterusnya.
    """
    jejak = _jejak()
    with pytest.raises(GalatJejak):
        jejak.catat(
            id_dokumen="dok_001",
            id_pelaku=PELAKU,
            dari_area=Area.KARANTINA,
            ke_area=Area.KARANTINA,
            alasan=alasan,
        )


def test_baris_tidak_tertulis_ketika_alasannya_ditolak() -> None:
    """Galat yang tetap menulis barisnya membocorkan justru yang dilarangnya."""
    jejak = _jejak()
    with pytest.raises(GalatJejak):
        jejak.catat(
            id_dokumen="dok_001",
            id_pelaku=PELAKU,
            dari_area=Area.KARANTINA,
            ke_area=Area.KARANTINA,
            alasan="memuat NIK 3211012509870001 pada halaman 3",
        )
    assert jejak.baris() == []


def test_galat_tidak_mengulang_alasan_yang_ditolaknya() -> None:
    """Pesan galat yang mengutip alasannya memindahkan kebocoran ke log.

    Ini cacat yang paling mudah dibuat pada pemeriksa semacam ini, dan
    akibatnya persis kebalikan dari maksudnya.
    """
    jejak = _jejak()
    with pytest.raises(GalatJejak) as galat:
        jejak.catat(
            id_dokumen="dok_001",
            id_pelaku=PELAKU,
            dari_area=Area.KARANTINA,
            ke_area=Area.KARANTINA,
            alasan="memuat NIK 3211012509870001 pada halaman 3",
        )
    assert "3211012509870001" not in str(galat.value)


def test_alasan_sah_tetap_diterima() -> None:
    """Penjagaan yang menolak alasan sah akan dimatikan orang.

    Alasan yang benar berbunyi seperti ini: menyebut jenis temuannya, tanpa
    menyalin nilainya.
    """
    jejak = _jejak()
    for alasan in (
        "memuat nomor induk kependudukan yang belum disamarkan",
        "terdapat nomor telepon pada lampiran, mohon disamarkan",
        "anonimisasi terverifikasi, tahun terbit 2026 sesuai kop",
    ):
        jejak.catat(
            id_dokumen="dok_001",
            id_pelaku=PELAKU,
            dari_area=Area.KARANTINA,
            ke_area=Area.KARANTINA,
            alasan=alasan,
        )
    assert len(jejak.baris()) == 3


def test_alasan_wajib() -> None:
    """Perpindahan tanpa alasan menghasilkan jejak yang tidak menjelaskan apa pun."""
    jejak = _jejak()
    with pytest.raises(GalatJejak):
        jejak.catat(
            id_dokumen="dok_001",
            id_pelaku=PELAKU,
            dari_area=Area.KARANTINA,
            ke_area=Area.KORPUS,
            alasan="",
        )


def test_id_baris_berbeda_tiap_baris() -> None:
    """Dua baris beridentitas sama tidak dapat dirujuk terpisah."""
    jejak = _jejak()
    for _ in range(3):
        jejak.catat(
            id_dokumen="dok_001",
            id_pelaku=PELAKU,
            dari_area=Area.KARANTINA,
            ke_area=Area.KARANTINA,
            alasan="ditahan menunggu tinjauan",
        )
    assert len({b.id for b in jejak.baris()}) == 3
