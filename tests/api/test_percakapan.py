"""Uji riwayat percakapan — C-1 fitur 021, R-13, R-14, FR-F09.

## Yang diuji bukan bahwa riwayat dapat mencatat

Yang diuji: riwayat **tidak menyimpan** salinan tanggapan, **tidak dapat**
disunting, dan **tidak dapat** menyimpan pertanyaan bermuatan data pribadi.

Yang pertama adalah keputusan yang paling mudah dibalik dan paling mahal bila
dibalik: tanggapan yang tersimpan menua, status keberlakuan sitasinya berubah
ketika regulasi sumbernya dicabut, dan riwayat yang menayangkan salinan lama
melanggar C-07 lewat pintu yang tidak dijaga siapa pun.
"""

from datetime import UTC, datetime

import pytest

from src.api.percakapan import GalatPercakapan, Giliran, Percakapan

SAAT = datetime(2026, 8, 13, 3, 0, tzinfo=UTC)


def _percakapan() -> Percakapan:
    percakapan = Percakapan("PCK-1")
    percakapan.catat(
        pertanyaan="Bagaimana menyusun jadwal supervisi akademik?",
        id_pesan="PSN-1",
        waktu=SAAT,
    )
    return percakapan


# --------------------------------------------- R-13 · rujukan, bukan salinan


def test_giliran_tidak_memiliki_bidang_bagi_tanggapan() -> None:
    """**Uji terpenting berkas ini, dan ia diuji sebagai ketiadaan bidang.**

    Bidang yang ada akan terisi. Tanggapan yang tersimpan menua — status
    keberlakuan sitasinya berubah ketika regulasi sumbernya dicabut, dan fitur
    010 memang menariknya. Riwayat yang menayangkan salinan lama menayangkan
    klaim atas regulasi yang tidak berlaku, dan validator tidak pernah
    dipanggil ulang sebab tidak ada yang dianggap sedang menjawab.
    """
    assert set(Giliran.model_fields) == {"pertanyaan", "id_pesan", "waktu"}


def test_giliran_menyimpan_rujukan_pesan() -> None:
    (giliran,) = _percakapan().giliran
    assert giliran.id_pesan == "PSN-1"
    assert giliran.pertanyaan.startswith("Bagaimana")
    assert giliran.waktu == SAAT


def test_bidang_tambahan_ditolak() -> None:
    """`extra="forbid"`. Bidang `tanggapan` yang ditambahkan seseorang kelak
    akan lolos diam-diam tanpa ini, dan tidak satu uji perilaku pun gagal."""
    with pytest.raises(Exception):
        Giliran(
            pertanyaan="Bagaimana menyusun jadwal supervisi?",
            id_pesan="PSN-1",
            waktu=SAAT,
            tanggapan="tersalin",  # type: ignore[call-arg]
        )


def test_urutan_giliran_terjaga() -> None:
    """"Melanjutkan sesi sebelumnya" (FR-F09) menuntut urutannya, dan urutan
    yang tidak diuji adalah urutan yang berubah ketika penyimpanannya diganti."""
    percakapan = _percakapan()
    percakapan.catat(pertanyaan="Berapa lama supervisi berlangsung?", id_pesan="PSN-2", waktu=SAAT)
    assert [g.id_pesan for g in percakapan.giliran] == ["PSN-1", "PSN-2"]


# ----------------------------------------------------------- R-14 · tambah-saja


def test_permukaan_tanpa_cara_menyunting_maupun_menghapus() -> None:
    """Sifat tambah-saja ditegakkan **permukaan modul**, bukan tata tertib.

    Yang tidak disediakan tidak dapat dipanggil karena lupa. Bentuk yang sama
    dengan `JejakArea` (002), `JejakKurasi` (010), dan `Telemetri` (012).
    """
    terlarang = {"sunting", "hapus", "ubah", "ganti", "kosongkan", "timpa"}
    tersedia = {n for n in dir(Percakapan) if not n.startswith("_")}
    assert not (tersedia & terlarang)


def test_giliran_yang_dikembalikan_tidak_dapat_diubah_pemanggil() -> None:
    giliran = _percakapan().giliran
    assert isinstance(giliran, tuple)
    with pytest.raises(AttributeError):
        giliran.append(giliran[0])  # type: ignore[attr-defined]


def test_giliran_beku() -> None:
    (giliran,) = _percakapan().giliran
    with pytest.raises(Exception):
        giliran.id_pesan = "PSN-9"  # type: ignore[misc]


# ------------------------------------------------------------- KM-03 · penjagaan


@pytest.mark.parametrize(
    "pertanyaan",
    [
        "Bagaimana melapor untuk NIK 3273010101800001?",
        "Nomor saya 081234567890, tolong dihubungi.",
    ],
)
def test_pertanyaan_bermuatan_data_pribadi_ditolak(pertanyaan: str) -> None:
    """**Tolak, jangan saring.** Menyaring diam-diam menghasilkan baris yang
    tampak bersih sementara penulisnya tidak pernah tahu ia hampir membocorkan
    sesuatu, dan ia akan menulisnya lagi."""
    with pytest.raises(GalatPercakapan):
        Percakapan("PCK-1").catat(pertanyaan=pertanyaan, id_pesan="PSN-1", waktu=SAAT)


def test_galat_tidak_mengulang_muatan_yang_ditolaknya() -> None:
    """Galat yang mengutip pertanyaannya memindahkan kebocoran dari riwayat ke
    log — kebalikan persis dari maksudnya. Ditemukan pada fitur 012 sebagai
    kebocoran lewat `ValidationError` pydantic, bukan lewat pesan buatan
    sendiri (KB-049)."""
    with pytest.raises(GalatPercakapan) as galat:
        Percakapan("PCK-1").catat(
            pertanyaan="Nomor saya 081234567890.", id_pesan="PSN-1", waktu=SAAT
        )
    assert "081234567890" not in str(galat.value)
    assert "telepon" in str(galat.value)


def test_baris_ditolak_tidak_meninggalkan_setengah_catatan() -> None:
    """Seluruh pemeriksaan berjalan **sebelum** baris ditambahkan."""
    percakapan = Percakapan("PCK-1")
    with pytest.raises(GalatPercakapan):
        percakapan.catat(pertanyaan="Nomor saya 081234567890.", id_pesan="PSN-1", waktu=SAAT)
    assert percakapan.giliran == ()


# ------------------------------------------------------------------- bentuk lain


def test_waktu_wajib_berzona_utc() -> None:
    """Waktu tanpa zona tidak dapat dibandingkan dengan waktu berzona, dan
    perbandingan itu yang menyusun urutan giliran."""
    with pytest.raises(GalatPercakapan) as galat:
        Percakapan("PCK-1").catat(
            pertanyaan="Bagaimana menyusun jadwal supervisi?",
            id_pesan="PSN-1",
            waktu=datetime(2026, 8, 13, 3, 0),
        )
    assert "UTC" in str(galat.value)


def test_pertanyaan_kosong_ditolak_dengan_pesan_yang_menyebut_sebabnya() -> None:
    """Penolakan bentuk **wajib** menyebut apa yang kurang — berbeda dari
    penolakan KM-03, yang tidak boleh membawa keterangan apa pun. Pesan yang
    tidak menyebutnya membuat pemanggil menebak."""
    with pytest.raises(GalatPercakapan) as galat:
        Percakapan("PCK-1").catat(pertanyaan="", id_pesan="PSN-1", waktu=SAAT)
    assert "tidak lengkap" in str(galat.value)


def test_percakapan_tanpa_pengenal_ditolak() -> None:
    with pytest.raises(GalatPercakapan):
        Percakapan("   ")


def test_percakapan_membawa_pengenalnya() -> None:
    assert Percakapan("PCK-7").id_percakapan == "PCK-7"


def test_giliran_tanpa_id_pengguna() -> None:
    """Sama dengan `Peristiwa` fitur 012: yang tidak ada tidak dapat terisi.
    Pemilik percakapan adalah kunci penyimpanannya, dan pemetaan itu tinggal di
    `src/penyimpanan/` bersama kunci pseudonim yang C-05 pisahkan."""
    assert "id_pengguna" not in Giliran.model_fields
