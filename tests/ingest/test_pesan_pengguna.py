"""Uji pesan galat pengguna — B-7 fitur 015, R-02, C-13, NFR-19.

C-13 menetapkan tiga hal: kalimat ≤ 20 kata, istilah teknis dijelaskan pada
kemunculan pertama, tanpa singkatan yang tidak diuraikan. Pada pesan galat
yang dibaca kepala sekolah, cara memenuhinya bukan menjelaskan istilahnya
melainkan tidak memakainya sama sekali.

Yang paling mudah bocor bukan istilah teknis melainkan **nama pustaka**.
"PdfReadError" dan "PackageNotFoundError" tidak berarti apa pun bagi kepala
sekolah, tetapi keduanya masuk ke pesan dengan sendirinya bila pesan ditulis
sambil menangani galatnya. Karena itu kumpulannya disusun sekali di satu
tempat, dan berkas ini menguji seluruhnya sekaligus.
"""

from pathlib import Path

import pytest
from src.ingest.ekstraksi.docx import PengekstrakDocx
from src.ingest.ekstraksi.galat import PESAN, GalatEkstraksi
from src.ingest.ekstraksi.pdf import PengekstrakPdf
from src.ingest.ekstraksi.xlsx import PengekstrakXlsx

BAHAN = Path(__file__).resolve().parents[1] / "bahan"

BATAS_KATA = 20

ISTILAH_TERLARANG = (
    "pdf reader",
    "parse",
    "parsing",
    "stream",
    "exception",
    "error",
    "galat",
    "null",
    "none",
    "encoding",
    "unicode",
    "xml",
    "zip",
    "ocr",
    "pypdf",
    "openpyxl",
    "docx",
    "python",
    "modul",
    "pustaka",
    "library",
)
"""Istilah yang tidak boleh muncul pada pesan yang dibaca kepala sekolah.

Memuat nama pustaka **dan** kata "galat" itu sendiri: pengguna tidak perlu
tahu bahwa yang terjadi disebut galat, ia perlu tahu apa yang harus
dilakukannya.
"""


@pytest.mark.parametrize("kunci", sorted(PESAN))
def test_setiap_pesan_paling_banyak_dua_puluh_kata(kunci: str) -> None:
    """C-13 — dihitung per kalimat, karena itu yang pasalnya sebut."""
    for kalimat in PESAN[kunci].split("."):
        assert len(kalimat.split()) <= BATAS_KATA, f"{kunci}: {kalimat!r}"


@pytest.mark.parametrize("kunci", sorted(PESAN))
def test_setiap_pesan_tanpa_istilah_teknis(kunci: str) -> None:
    rendah = PESAN[kunci].lower()
    for istilah in ISTILAH_TERLARANG:
        assert istilah not in rendah, f"{kunci} memuat {istilah!r}"


@pytest.mark.parametrize("kunci", sorted(PESAN))
def test_setiap_pesan_menyebut_yang_harus_dilakukan(kunci: str) -> None:
    """Pesan yang hanya menyatakan kegagalan membuat pengguna mengulang
    tindakan yang sama.

    Diuji dengan menuntut adanya kata kerja ajakan — bukan sempurna, tetapi
    cukup untuk menangkap pesan yang berhenti pada "tidak dapat dibaca".
    """
    rendah = PESAN[kunci].lower()
    assert any(k in rendah for k in ("mohon", "silakan", "coba", "hubungi")), PESAN[kunci]


@pytest.mark.parametrize("kunci", sorted(PESAN))
def test_setiap_pesan_tanpa_kode_galat(kunci: str) -> None:
    """`AGENTS.md`: pesan galat ke pengguna tanpa kode galat.

    Kode galat mengundang pengguna menyalinnya ke pencarian web, dan yang
    ditemukannya adalah halaman untuk pengembang.
    """
    assert not any(huruf.isdigit() for huruf in PESAN[kunci]), PESAN[kunci]


def test_pesan_bawaan_dipakai_ketika_tidak_disebut() -> None:
    galat = GalatEkstraksi("uraian teknis apa pun")
    assert galat.pesan_pengguna in PESAN.values()


@pytest.mark.parametrize(
    ("pengekstrak", "berkas"),
    [
        (PengekstrakDocx(), "kosong.docx"),
        (PengekstrakDocx(), "rusak.pdf"),
        (PengekstrakXlsx(), "kosong.xlsx"),
        (PengekstrakXlsx(), "rusak.pdf"),
        (PengekstrakPdf(), "rusak.pdf"),
        (PengekstrakPdf(), "kosong.pdf"),
        (PengekstrakPdf(), "terkunci.pdf"),
        (PengekstrakPdf(), "pindaian-tanpa-teks.pdf"),
    ],
)
def test_setiap_galat_sungguhan_membawa_pesan_dari_kumpulan(
    pengekstrak: object, berkas: str
) -> None:
    """**Uji terpenting berkas ini.**

    Kumpulan yang rapi tidak berarti apa-apa bila pengekstraknya menulis
    pesannya sendiri di tempat. Yang diuji: setiap galat yang benar-benar
    terjadi membawa pesan yang berasal dari kumpulan, bukan untai yang
    dirangkai saat itu.
    """
    with pytest.raises(GalatEkstraksi) as galat:
        pengekstrak.ekstrak(BAHAN / berkas)  # type: ignore[attr-defined]
    assert galat.value.pesan_pengguna in PESAN.values()


def test_uraian_teknis_tidak_ikut_ke_pengguna() -> None:
    """Dua pembaca dengan kebutuhan berlawanan, dua bidang terpisah.

    Pengembang perlu tahu pustaka mana yang gagal; pengguna tidak boleh
    melihatnya sama sekali.
    """
    galat = GalatEkstraksi("PackageNotFoundError pada python-docx")
    assert "PackageNotFoundError" in str(galat)
    assert "PackageNotFoundError" not in galat.pesan_pengguna
