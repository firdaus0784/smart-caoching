"""Uji gerbang perekaman — B-1 fitur 012, R-04, R-05, R-07, **C-04**.

C-04: *"Telemetri tidak merekam bagi pengguna tanpa persetujuan aktif.
Pencabutan menghentikan perekaman seketika."*

## Yang diuji di sini sebagian besar adalah penolakan

Gerbang yang merekam dapat dibuktikan dengan satu uji. Gerbang yang **tidak**
merekam bagi tiga keadaan lain menuntut tiga, dan yang keempat menuntut
rangkaian — sebab "seketika" adalah pernyataan tentang urutan waktu, bukan
tentang satu panggilan.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from src.pengguna.persetujuan import KeadaanPersetujuan
from src.telemetri.gerbang import HasilPerekaman, Telemetri, rekam
from src.telemetri.peristiwa import JenisPeristiwa, Peristiwa

AKAR = Path(__file__).resolve().parents[2]

WAKTU = datetime(2026, 8, 13, 4, 0, tzinfo=UTC)


def _rekam(
    keadaan: KeadaanPersetujuan = KeadaanPersetujuan.DIBERIKAN, **ganti: object
) -> tuple[HasilPerekaman, Peristiwa | None]:
    argumen: dict[str, object] = {
        "pseudonim": "PSD-a1",
        "jenis": JenisPeristiwa.QUESTION_ASKED,
        "waktu": WAKTU,
        "properti": {"kategori": "K3"},
        "versi_aplikasi": "0.12.0",
        "versi_model": "tiruan-0",
    }
    argumen.update(ganti)
    return rekam(keadaan=keadaan, **argumen)  # type: ignore[arg-type]


# ------------------------------------------------------------ R-04 · C-04


def test_persetujuan_diberikan_merekam() -> None:
    hasil, peristiwa = _rekam()
    assert hasil is HasilPerekaman.DIREKAM
    assert peristiwa is not None
    assert peristiwa.pseudonim == "PSD-a1"


@pytest.mark.parametrize(
    "keadaan",
    [
        KeadaanPersetujuan.BELUM_DIMINTA,
        KeadaanPersetujuan.DITOLAK,
        KeadaanPersetujuan.DICABUT,
    ],
)
def test_ketiga_keadaan_lain_tidak_merekam(keadaan: KeadaanPersetujuan) -> None:
    """**Uji terpenting berkas ini**, dan ia dijalankan tiga kali.

    Ketiganya diuji terpisah. Uji yang hanya memakai `DITOLAK` lulus juga pada
    gerbang yang meloloskan `BELUM_DIMINTA` — dan `BELUM_DIMINTA` adalah
    keadaan setiap pengguna pada hari pertama.
    """
    hasil, peristiwa = _rekam(keadaan)
    assert hasil is HasilPerekaman.DILEWATI_TANPA_PERSETUJUAN
    assert peristiwa is None


def test_seluruh_keadaan_disapu_bukan_daftar_yang_disalin() -> None:
    """Keadaan kelima yang ditambahkan kelak menyalakan uji ini, bukan lolos
    sebagai keadaan yang tidak ditangani siapa pun."""
    for keadaan in KeadaanPersetujuan:
        hasil, peristiwa = _rekam(keadaan)
        if keadaan.boleh_merekam:
            assert hasil is HasilPerekaman.DIREKAM, keadaan
            assert peristiwa is not None
        else:
            assert peristiwa is None, keadaan


def test_keadaan_wajib_diisi_pemanggil() -> None:
    """Tanpa nilai bawaan. Parameter berbawaan `DIBERIKAN` akan membatalkan
    C-04 pada setiap pemanggilan yang lupa mengisinya, dan tidak satu uji
    perilaku pun gagal karenanya."""
    with pytest.raises(TypeError):
        rekam(  # type: ignore[call-arg]
            pseudonim="PSD-a1",
            jenis=JenisPeristiwa.QUESTION_ASKED,
            waktu=WAKTU,
            properti={},
            versi_aplikasi="0.12.0",
            versi_model="tiruan-0",
        )


# ---------------------------------------------------- R-05 · seketika, bukan nanti


def test_pencabutan_menghentikan_pada_panggilan_berikutnya() -> None:
    """**"Seketika" adalah pernyataan tentang urutan waktu.**

    Diuji sebagai rangkaian, bukan satu panggilan: rekam, cabut, rekam lagi.
    Gerbang yang menyimpan salinan keadaan saat sesi dibuka akan tetap merekam
    peristiwa kedua — dan tidak satu uji panggilan-tunggal pun melihatnya.
    """
    telemetri = Telemetri()
    telemetri.catat(
        keadaan=KeadaanPersetujuan.DIBERIKAN,
        pseudonim="PSD-a1",
        jenis=JenisPeristiwa.SESSION_START,
        waktu=WAKTU,
        properti={},
        versi_aplikasi="0.12.0",
        versi_model="tiruan-0",
    )
    assert len(telemetri.peristiwa) == 1

    hasil = telemetri.catat(
        keadaan=KeadaanPersetujuan.DICABUT,
        pseudonim="PSD-a1",
        jenis=JenisPeristiwa.QUESTION_ASKED,
        waktu=WAKTU,
        properti={},
        versi_aplikasi="0.12.0",
        versi_model="tiruan-0",
    )
    assert hasil is HasilPerekaman.DILEWATI_TANPA_PERSETUJUAN
    assert len(telemetri.peristiwa) == 1


def test_gerbang_tidak_menyimpan_keadaan_persetujuan() -> None:
    """Bentuk yang menjamin uji di atas tetap berarti.

    Gerbang yang menyimpan keadaan dapat lulus uji rangkaian di atas hari ini
    dan berhenti lulus ketika seseorang menambahkan penyegaran — sedangkan
    gerbang yang tidak memiliki tempat menyimpannya tidak dapat.
    """
    telemetri = Telemetri()
    tersimpan = [n for n in vars(telemetri) if "keadaan" in n or "persetujuan" in n]
    assert tersimpan == []


def test_pencabutan_tidak_menghapus_yang_sudah_terekam() -> None:
    """Peristiwa yang terekam sebelum pencabutan **tetap ada**.

    C-04 menghentikan perekaman; ia tidak memerintahkan penghapusan surut.
    Penghapusan mengikuti KM-02 dan permintaan penarikan data, yang jalurnya
    berbeda dan menuntut keputusan manusia.
    """
    telemetri = Telemetri()
    telemetri.catat(
        keadaan=KeadaanPersetujuan.DIBERIKAN,
        pseudonim="PSD-a1",
        jenis=JenisPeristiwa.SESSION_START,
        waktu=WAKTU,
        properti={},
        versi_aplikasi="0.12.0",
        versi_model="tiruan-0",
    )
    telemetri.catat(
        keadaan=KeadaanPersetujuan.DICABUT,
        pseudonim="PSD-a1",
        jenis=JenisPeristiwa.SESSION_END,
        waktu=WAKTU,
        properti={},
        versi_aplikasi="0.12.0",
        versi_model="tiruan-0",
    )
    assert len(telemetri.peristiwa) == 1


# ------------------------------------- tiga keadaan hasil, bukan dua


def test_properti_cacat_bukan_pengguna_yang_menolak() -> None:
    """**Pengulangan ketujuh pola "tiga keadaan, bukan dua".**

    Menyamakan `DITOLAK_PROPERTI` dengan `DILEWATI_TANPA_PERSETUJUAN` membuat
    pelanggaran KM-03 terhitung sebagai pengguna yang menolak — lalu laporan
    partisipasi keliru, dan kekeliruan KM-03 tidak pernah terlihat sebab ia
    tersembunyi di balik angka yang tampak wajar.
    """
    hasil, peristiwa = _rekam(properti={"nama": "apa pun"})
    assert hasil is HasilPerekaman.DITOLAK_PROPERTI
    assert hasil is not HasilPerekaman.DILEWATI_TANPA_PERSETUJUAN
    assert peristiwa is None


def test_tiga_hasil_tidak_kurang_tidak_lebih() -> None:
    assert len(HasilPerekaman) == 3


def test_properti_cacat_pada_pengguna_tanpa_persetujuan_dilaporkan_sebagai_apa() -> None:
    """Urutan pemeriksaan dinyatakan, bukan dibiarkan kebetulan.

    Persetujuan diperiksa **lebih dulu**: pengguna yang tidak menyetujui tidak
    boleh membuat isi peristiwanya diperiksa sama sekali, sebab pemeriksaan
    itu sendiri menyentuh muatan yang seharusnya tidak diproses.
    """
    hasil, peristiwa = _rekam(KeadaanPersetujuan.DITOLAK, properti={"nama": "apa pun"})
    assert hasil is HasilPerekaman.DILEWATI_TANPA_PERSETUJUAN
    assert peristiwa is None


# ------------------------------------------------------------ R-07 · tambah-saja


def test_telemetri_tanpa_cara_menyunting_maupun_menghapus() -> None:
    """Yang tidak disediakan tidak dapat dipanggil karena lupa. Bentuk yang
    sama dengan `JejakKurasi` (010) dan `src/logbook/penulis.py`."""
    terlarang = {"sunting", "hapus", "ubah", "ganti", "kosongkan", "timpa"}
    tersedia = {n for n in dir(Telemetri) if not n.startswith("_")}
    assert not (tersedia & terlarang)


def test_peristiwa_yang_dikembalikan_tidak_dapat_diubah_pemanggil() -> None:
    telemetri = Telemetri()
    telemetri.catat(
        keadaan=KeadaanPersetujuan.DIBERIKAN,
        pseudonim="PSD-a1",
        jenis=JenisPeristiwa.SESSION_START,
        waktu=WAKTU,
        properti={},
        versi_aplikasi="0.12.0",
        versi_model="tiruan-0",
    )
    assert isinstance(telemetri.peristiwa, tuple)
    with pytest.raises(AttributeError):
        telemetri.peristiwa.append(telemetri.peristiwa[0])  # type: ignore[attr-defined]


def test_gerbang_satu_satunya_yang_membentuk_peristiwa() -> None:
    """C-04 melekat pada bentuk. Sapuan atas `src/` mencari **pemanggilan**
    `Peristiwa(...)`, bukan penyebutan namanya.

    Pernyataan lengkapnya ditegakkan pemeriksa C-04 (tugas C-2), yang membaca
    pohon sintaks alih-alih teks. Uji ini menyatakan niatnya di tempat yang
    dibaca orang, dan sengaja tidak berpura-pura menggantikan pemeriksanya.
    """
    import ast

    pembentuk = []
    for jalur in (AKAR / "src").rglob("*.py"):
        pohon = ast.parse(jalur.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if (
                isinstance(simpul, ast.Call)
                and isinstance(simpul.func, ast.Name)
                and simpul.func.id == "Peristiwa"
            ):
                pembentuk.append(jalur.name)
    assert pembentuk == ["gerbang.py"]
