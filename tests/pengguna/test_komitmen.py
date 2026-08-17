"""Uji komitmen penerapan — A-1 fitur 011, R-11 s.d. R-14, R-16; TK-51.

## Yang diuji bukan bahwa komitmen dapat disimpan

Yang diuji: komitmen **tidak dapat** berbentuk satu untai bebas, **tidak
dapat** kehilangan isyaratnya, dan **tidak dapat** dibatalkan tanpa alasan.

Yang pertama adalah keputusan TK-51 itu sendiri. Bukti *d* = 0,65 pada
Gollwitzer & Sheeran (2006) berlaku bagi rencana **jika-maka**; komitmen
bertenggat biasa tidak menanggungnya. Bila bentuknya longgar, sistemnya tetap
patuh konstitusi dan **penelitiannya yang kehilangan dasar**.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError
from src.pengguna.komitmen import (
    GalatKomitmen,
    Komitmen,
    Penerapan,
    StatusPenerapan,
    catat_penerapan,
    susun_komitmen,
)

SAAT = datetime(2026, 8, 16, 3, 0, tzinfo=UTC)
TENGGAT = date(2026, 9, 1)


def _komitmen(**ganti: object) -> Komitmen:
    argumen: dict[str, object] = {
        "id_komitmen": "KMT-1",
        "id_butir": "BTR-1",
        "isyarat": "Jika rapat komite sekolah berikutnya dibuka",
        "tindakan": "maka saya sampaikan tiga butir supervisi ini",
        "tenggat": TENGGAT,
        "dibuat": SAAT,
    }
    argumen.update(ganti)
    return susun_komitmen(**argumen)  # type: ignore[arg-type]


# ------------------------------------------- R-11, R-12 · niat pelaksanaan


def test_komitmen_tidak_memiliki_bidang_teks_bebas_tunggal() -> None:
    """**Uji terpenting berkas ini, dan ia diuji sebagai ketiadaan bidang.**

    Bidang yang ada akan terisi. Satu bidang bebas akan menerima "saya akan
    lebih rajin memantau" — kalimat yang tidak membawa satu pun sifat yang
    membuat *d* = 0,65 Gollwitzer & Sheeran (2006) berlaku, dan yang kemudian
    dihitung sebagai komitmen pada rasio penerapan.
    """
    assert set(Komitmen.model_fields) == {
        "id_komitmen",
        "id_butir",
        "isyarat",
        "tindakan",
        "tenggat",
        "dibuat",
    }


def test_isyarat_dan_tindakan_keduanya_wajib_tanpa_bawaan() -> None:
    """Bidang berbawaan lolos tanpa satu galat pun — pydantic **tidak**
    memvalidasi nilai bawaan. Komitmen tanpa isyarat kemudian terbentuk
    diam-diam sebagai komitmen yang sah."""
    assert Komitmen.model_fields["isyarat"].is_required()
    assert Komitmen.model_fields["tindakan"].is_required()


def test_komitmen_lengkap_terbentuk() -> None:
    komitmen = _komitmen()
    assert komitmen.isyarat.startswith("Jika")
    assert komitmen.tindakan.startswith("maka")
    assert komitmen.tenggat == TENGGAT


@pytest.mark.parametrize("bagian", ["isyarat", "tindakan"])
def test_bagian_yang_kosong_ditolak(bagian: str) -> None:
    with pytest.raises(GalatKomitmen):
        _komitmen(**{bagian: ""})


@pytest.mark.parametrize("bagian", ["isyarat", "tindakan"])
def test_bagian_sepatah_kata_ditolak(bagian: str) -> None:
    """Isyarat yang muat dalam sepatah kata bukan rencana melainkan penanda,
    dan yang demikian tidak dapat dibedakan dari bidang yang diisi asal."""
    with pytest.raises(GalatKomitmen):
        _komitmen(**{bagian: "besok"})


def test_tenggat_terpisah_dari_rencananya() -> None:
    """Niat pelaksanaan bersandar pada isyarat keadaan, bukan pada tanggal.
    Menyatukan keduanya membuat penggunanya menuliskan tanggal sebagai
    isyarat — dan tanggal bukan isyarat keadaan."""
    assert Komitmen.model_fields["tenggat"].annotation is date
    assert "tenggat" not in _komitmen().isyarat


def test_komitmen_beku() -> None:
    with pytest.raises(ValidationError):
        _komitmen().isyarat = "lain"  # type: ignore[misc]


def test_bidang_tambahan_ditolak_pada_dua_lapis() -> None:
    """Bidang `catatan_bebas` yang ditambahkan seseorang kelak "untuk pengguna
    yang kesulitan" ditolak **dua kali**, dan keduanya perlu.

    Tanda tangan `susun_komitmen` menolaknya sebagai `TypeError` — lapis luar,
    yang menangkap pemanggil. `extra="forbid"` menolaknya pada modelnya — lapis
    dalam, yang menangkap kode yang membentuk `Komitmen` langsung. Menguji
    lapis luar saja meninggalkan model terbuka bagi modul lain.
    """
    with pytest.raises(TypeError):
        susun_komitmen(  # type: ignore[call-arg]
            id_komitmen="KMT-1",
            id_butir="BTR-1",
            isyarat="Jika rapat komite sekolah berikutnya dibuka",
            tindakan="maka saya sampaikan tiga butir supervisi ini",
            tenggat=TENGGAT,
            dibuat=SAAT,
            catatan_bebas="saya akan lebih rajin",
        )
    with pytest.raises(ValidationError):
        Komitmen(
            id_komitmen="KMT-1",
            id_butir="BTR-1",
            isyarat="Jika rapat komite sekolah berikutnya dibuka",
            tindakan="maka saya sampaikan tiga butir supervisi ini",
            tenggat=TENGGAT,
            dibuat=SAAT,
            catatan_bebas="saya akan lebih rajin",  # type: ignore[call-arg]
        )


def test_rantai_ke_butir_tidak_putus() -> None:
    """FR-G ke FR-H adalah satu rantai. Komitmen tanpa butir asalnya tidak
    dapat dianalisis terhadap apa yang dibaca."""
    assert Komitmen.model_fields["id_butir"].is_required()


# ------------------------------------------------- R-13, R-14 · penerapan


def test_empat_status_penerapan() -> None:
    """D-01 FR-H04 menyebut empat. Menyatukan `BELUM` dengan `TIDAK_JADI`
    menghapus perbedaan antara komitmen yang tertunda dan yang dibatalkan —
    dan rasio penerapan dihitung dari perbedaan itu."""
    assert {s.value for s in StatusPenerapan} == {
        "sudah_diterapkan",
        "sedang_berjalan",
        "belum",
        "tidak_jadi",
    }


def test_tidak_jadi_menuntut_alasan() -> None:
    """**Tanpa alasan, pembatalan tidak dapat dibedakan dari kegagalan
    sistem** — dan keduanya menuntut perbaikan yang berlawanan."""
    with pytest.raises(GalatKomitmen):
        catat_penerapan(id_komitmen="KMT-1", status=StatusPenerapan.TIDAK_JADI, waktu=SAAT)


def test_tidak_jadi_dengan_alasan_diterima() -> None:
    hasil = catat_penerapan(
        id_komitmen="KMT-1",
        status=StatusPenerapan.TIDAK_JADI,
        waktu=SAAT,
        alasan="Rapat komite ditunda ke semester berikutnya.",
    )
    assert hasil.status is StatusPenerapan.TIDAK_JADI
    assert hasil.alasan


@pytest.mark.parametrize(
    "status",
    [StatusPenerapan.SUDAH_DITERAPKAN, StatusPenerapan.SEDANG_BERJALAN, StatusPenerapan.BELUM],
)
def test_ketiga_status_lain_tidak_menuntut_alasan(status: StatusPenerapan) -> None:
    """Yang belum berjalan belum punya alasan, dan menuntutnya akan membuat
    penggunanya mengarang."""
    assert catat_penerapan(id_komitmen="KMT-1", status=status, waktu=SAAT).alasan == ""


@pytest.mark.parametrize(
    "status",
    [StatusPenerapan.SUDAH_DITERAPKAN, StatusPenerapan.SEDANG_BERJALAN, StatusPenerapan.BELUM],
)
def test_alasan_pada_status_yang_tidak_memintanya_ditolak(status: StatusPenerapan) -> None:
    """Bidang yang terisi tanpa sebab akan diabaikan pembacanya, dan yang
    diabaikan tidak menjaga apa pun ketika ia sungguh perlu — bentuk yang sama
    dengan `catatan_keberlakuan` fitur 009."""
    with pytest.raises(GalatKomitmen):
        catat_penerapan(id_komitmen="KMT-1", status=status, waktu=SAAT, alasan="sudah saya lakukan")


def test_penerapan_beku_dan_tanpa_bidang_tambahan() -> None:
    hasil = catat_penerapan(id_komitmen="KMT-1", status=StatusPenerapan.BELUM, waktu=SAAT)
    assert isinstance(hasil, Penerapan)
    with pytest.raises(ValidationError):
        hasil.status = StatusPenerapan.SUDAH_DITERAPKAN  # type: ignore[misc]


def test_tenggat_lewat_tidak_menyimpulkan_status_sendiri() -> None:
    """Sistem menanyakan, tidak menyimpulkan. Status yang disimpulkan sendiri
    adalah data perilaku yang tidak pernah dilaporkan siapa pun — dan ia masuk
    ke rasio penerapan sebagai fakta."""
    permukaan = {n for n in dir(catat_penerapan) if not n.startswith("_")}
    assert "simpulkan" not in permukaan
    naskah = __import__("pathlib").Path("src/pengguna/komitmen.py").read_text(encoding="utf-8")
    assert "datetime.now" not in naskah, "status tidak boleh bergantung jam sistem"


# ------------------------------------------------------------ R-16 · KM-03


@pytest.mark.parametrize(
    "muatan",
    [
        "Jika Bu Siti menelepon 081234567890 nanti sore",
        "maka saya kirim NIK 3273010101800001 ke dinas",
    ],
)
def test_rencana_bermuatan_data_pribadi_ditolak(muatan: str) -> None:
    """Rencana sungguhan kepala sekolah menyebut orang. **Tolak, jangan
    saring** — menyaring diam-diam menghasilkan baris yang tampak bersih
    sementara penulisnya tidak pernah tahu."""
    bagian = "isyarat" if muatan.startswith("Jika") else "tindakan"
    with pytest.raises(GalatKomitmen):
        _komitmen(**{bagian: muatan})


def test_alasan_pembatalan_bermuatan_data_pribadi_ditolak() -> None:
    with pytest.raises(GalatKomitmen):
        catat_penerapan(
            id_komitmen="KMT-1",
            status=StatusPenerapan.TIDAK_JADI,
            waktu=SAAT,
            alasan="Dibatalkan, hubungi 081234567890 untuk keterangan.",
        )


def test_galat_tidak_mengulang_muatan_yang_ditolaknya() -> None:
    """Galat yang mengutip rencananya memindahkan kebocoran dari catatan ke
    log — kebalikan persis dari maksudnya (KB-049)."""
    with pytest.raises(GalatKomitmen) as galat:
        _komitmen(isyarat="Jika Bu Siti menelepon 081234567890 nanti sore")
    assert "081234567890" not in str(galat.value)
    assert "telepon" in str(galat.value)


def test_waktu_wajib_berzona() -> None:
    with pytest.raises(GalatKomitmen):
        _komitmen(dibuat=datetime(2026, 8, 16, 3, 0))


def test_waktu_penerapan_juga_wajib_berzona() -> None:
    """Cabang yang sama pada `Penerapan`, dan ia perlu diuji terpisah.

    Waktu penerapan tanpa zona tidak dapat dibandingkan dengan tenggat, dan
    perbandingan itu yang menentukan apakah jawabannya datang tepat waktu —
    bahan bagi rasio penerapan.
    """
    with pytest.raises(GalatKomitmen):
        catat_penerapan(
            id_komitmen="KMT-1",
            status=StatusPenerapan.BELUM,
            waktu=datetime(2026, 8, 16, 3, 0),
        )
