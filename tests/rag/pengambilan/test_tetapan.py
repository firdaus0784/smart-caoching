"""Uji rumah tetapan pengambilan — A-2 fitur 007, R-08, C-16.

C-16 berbunyi: *"Ambang tidak disetel di luar prosedur kalibrasi `docs/D07.md`
BT-29."* Berkas ini menegakkan sisi yang dapat ditegakkan sekarang — **angka
yang ada wajib dapat ditelusuri, dan angka yang belum dikalibrasi wajib tidak
ada sama sekali.**

Bedanya menentukan. D-07 Bagian 4.4 memberi nilai awal bagi jumlah kandidat
dan jumlah segmen yang diteruskan; menyalinnya bukan menyetel. D-07 Bagian 4.6
**tidak** memberi nilai bagi ambang tinggi dan menengah — ia menyerahkannya ke
BT-29 — sehingga menuliskan angka apa pun di sana adalah menyetel.

Uji terakhir berkas ini yang menjaga perbedaan itu: tidak ada tetapan bernama
ambang kecukupan pada modul ini, dan kekosongan itu yang benar.
"""

import ast
import inspect
from pathlib import Path

import pytest
import src.rag.pengambilan.tetapan as modul
from src.rag.pengambilan.tetapan import (
    JUMLAH_KANDIDAT_PER_SUMBER,
    JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM,
    JUMLAH_SEGMEN_DITERUSKAN_MINIMUM,
    JUMLAH_SUMBER_MINIMUM,
    TETAPAN_RRF_K,
)

AKAR = Path(__file__).resolve().parents[3]


def test_angka_persis_d07_bagian_4_4() -> None:
    """D-07 Bagian 4.4: kandidat BM25 20 teratas, kandidat vektor 20 teratas,
    segmen diteruskan 5–8.

    Fitur ini **mewujudkan** angka itu, tidak menciptakannya. Uji ini gagal
    bila seseorang menyetelnya tanpa melewati BT-29.
    """
    assert JUMLAH_KANDIDAT_PER_SUMBER == 20
    assert JUMLAH_SEGMEN_DITERUSKAN_MINIMUM == 5
    assert JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM == 8


def test_konstanta_rrf_dari_makalah_yang_dikutip_d07() -> None:
    """Nilai 60 berasal dari Cormack dkk. 2009 — sumber yang D-04 ADR-03 dan
    D-07 Bagian 4.4 kutip keduanya.

    Menyalin nilai dari sumber yang dokumen pengendalinya sebut **bukan**
    menyetel ambang; menuliskan angka tanpa menyebut asalnya adalah menyetel.
    Bedanya wajib terbaca dari kodenya, dan uji berikutnya menegakkannya.
    """
    assert TETAPAN_RRF_K == 60


def test_dua_angka_bernilai_sama_yang_bukan_satu_angka() -> None:
    """`JUMLAH_SUMBER_MINIMUM` (dari ADR-03) dan `JUMLAH_SEGMEN_RELEVAN_MINIMUM`
    (dari D-07 Bagian 4.6) kebetulan sama-sama 2, dan keduanya besaran yang
    sama sekali berbeda.

    Keduanya tinggal di sini justru karena itu: dari luar, satu angka yang
    tertulis dua kali dan dua angka yang kebetulan sama terlihat persis sama.
    Yang membedakannya hanya uraiannya — dan uraian itu wajib ada pada berkas
    ini, bukan pada kepala penulisnya.
    """
    from src.rag.pengambilan.tetapan import JUMLAH_SEGMEN_RELEVAN_MINIMUM

    assert JUMLAH_SUMBER_MINIMUM == JUMLAH_SEGMEN_RELEVAN_MINIMUM == 2


def test_dua_sumber_minimum_bukan_angka_yang_dapat_disetel() -> None:
    """**Bukan tetapan kalibrasi, melainkan pembacaan ADR-03.**

    ADR-03 menolak "vektor saja" dan "leksikal saja" secara tegas. Dua adalah
    jumlah jenis pengambilan yang keputusan itu tuntut, bukan angka yang
    dipilih karena bekerja baik. Menurunkannya menjadi satu berarti membatalkan
    ADR-03, bukan menyetel ambang.
    """
    assert JUMLAH_SUMBER_MINIMUM == 2


def _tetapan_publik() -> list[str]:
    return [n for n in dir(modul) if n.isupper() and not n.startswith("_")]


def test_setiap_tetapan_menyebut_sumbernya() -> None:
    """**Uji terpenting berkas ini bagi C-16.**

    Angka tanpa asal adalah angka yang disetel seseorang, dan tidak ada cara
    membedakannya dari angka yang dikutip kecuali asalnya tertulis. Diperiksa
    pada uraian yang menyertai tetapan, bukan pada komentar mana pun — komentar
    dapat berpindah, uraian melekat.
    """
    sumber = inspect.getsource(modul)
    pohon = ast.parse(sumber)
    uraian: dict[str, str] = {}
    sebelumnya: str | None = None
    for simpul in pohon.body:
        if isinstance(simpul, ast.Assign):
            nama = [t.id for t in simpul.targets if isinstance(t, ast.Name)]
            sebelumnya = nama[0] if nama else None
        elif (
            isinstance(simpul, ast.Expr)
            and isinstance(simpul.value, ast.Constant)
            and isinstance(simpul.value.value, str)
            and sebelumnya is not None
        ):
            uraian[sebelumnya] = simpul.value.value
            sebelumnya = None
        else:
            sebelumnya = None

    tanpa_sumber = []
    for nama in _tetapan_publik():
        # Tanda hubung dibuang pada kedua sisi: proyek ini menulis dokumen yang
        # sama sebagai "D-07" pada prosa dan "docs/D07.md" pada jalur berkas.
        # Uji yang hanya mengenali satu ejaan menuntut penulisnya menghafal
        # ejaan mana yang lolos, dan yang dihafal salah adalah yang dipakai.
        teks = uraian.get(nama, "").replace("-", "")
        if not any(petunjuk in teks for petunjuk in ("D07", "ADR03", "Cormack", "Robertson")):
            tanpa_sumber.append(nama)
    assert not tanpa_sumber, "tetapan tanpa asal tertulis: " + ", ".join(tanpa_sumber)


def test_uraian_modul_menyebut_pasal_yang_melarang_penyetelannya() -> None:
    uraian = modul.__doc__ or ""
    assert "C-16" in uraian
    assert "BT-29" in uraian


def test_ambang_kecukupan_belum_ada_dan_itu_yang_benar() -> None:
    """**R-11 pada tingkat tetapan.**

    D-07 Bagian 4.6 menyerahkan ambang tinggi dan menengah ke BT-29, kalibrasi
    terhadap *gold set* yang baru ada bulan 4–5. Menuliskan nilai awal
    "sementara" di sini akan berjalan pada hari pertama, memberi hasil masuk
    akal, dan tidak seorang pun kembali kepadanya.

    Uji ini gagal ketika seseorang menambahkannya — termasuk ketika ia
    menambahkannya dengan maksud baik.
    """
    terlarang = [n for n in _tetapan_publik() if "AMBANG" in n]
    assert not terlarang, (
        "ambang kecukupan bukan milik berkas ini sampai BT-29 mengalibrasinya "
        "(C-16, D-07 Bagian 4.6): " + ", ".join(terlarang)
    )


@pytest.mark.parametrize(
    "nama",
    [
        "JUMLAH_KANDIDAT_PER_SUMBER",
        "JUMLAH_SEGMEN_DITERUSKAN_MINIMUM",
        "JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM",
        "TETAPAN_RRF_K",
        "JUMLAH_SUMBER_MINIMUM",
        "JUMLAH_SEGMEN_RELEVAN_MINIMUM",
    ],
)
def test_tetapan_berupa_bilangan_bulat_positif(nama: str) -> None:
    nilai = getattr(modul, nama)
    assert isinstance(nilai, int)
    assert nilai > 0


def test_tetapan_bm25_berupa_pecahan_dalam_rentang_yang_masuk_akal() -> None:
    """`b` adalah bobot antara 0 dan 1; `k1` positif. Di luar rentang itu,
    rumusnya tetap berjalan dan hasilnya tetap terurut — hanya salah."""
    from src.rag.pengambilan.tetapan import BM25_B, BM25_K1

    assert isinstance(BM25_K1, float) and BM25_K1 > 0
    assert isinstance(BM25_B, float) and 0.0 <= BM25_B <= 1.0


def test_rentang_segmen_diteruskan_masuk_akal() -> None:
    """Batas bawah tidak melampaui batas atas, dan keduanya tidak melampaui
    jumlah kandidat yang tersedia dari satu sumber."""
    assert JUMLAH_SEGMEN_DITERUSKAN_MINIMUM < JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM
    assert JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM < JUMLAH_KANDIDAT_PER_SUMBER


def test_tetapan_ini_tidak_tertulis_di_berkas_lain() -> None:
    """R-08: angkanya **tidak boleh** tertulis di lebih dari satu tempat.

    Disapu hanya atas `src/rag/pengambilan/`, bukan seluruh `src/`. Angka 20,
    5, dan 8 adalah bilangan bulat kecil yang muncul sah di banyak tempat —
    sapuan seluruh pohon akan menandai indeks daftar dan panjang untai, lalu
    dimatikan orang. Sapuan yang dimatikan tidak menjaga apa pun.
    """
    nilai = {getattr(modul, n) for n in _tetapan_publik()}
    rumah = (AKAR / "src" / "rag" / "pengambilan" / "tetapan.py").resolve()
    pelanggaran: list[str] = []
    for berkas in sorted((AKAR / "src" / "rag" / "pengambilan").rglob("*.py")):
        if berkas.resolve() == rumah:
            continue
        pohon = ast.parse(berkas.read_text(encoding="utf-8"))
        for simpul in ast.walk(pohon):
            if isinstance(simpul, ast.Constant) and simpul.value in nilai:
                if isinstance(simpul.value, bool):
                    continue
                pelanggaran.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno}: {simpul.value}")
    assert not pelanggaran, "angka D-07 di luar tetapan.py: " + "; ".join(pelanggaran)
