"""Uji pembagian data — A-1 dan A-2 fitur 004, R-01 s.d. R-03, D-08 Bagian 4.2.

D-08 menyebut kekeliruan yang dijaga di sini dengan kalimatnya sendiri: bila
dua segmen dari dokumen yang sama tersebar ke himpunan latih dan uji, **model
akan tampak lebih baik daripada kenyataannya** karena telah melihat konteks
yang sangat mirip — dan itu "kekeliruan yang mudah terjadi dan sulit
terdeteksi setelahnya".

Yang membuatnya sulit terdeteksi: tidak ada satu pun angka yang terlihat
janggal. F1 naik, dan kenaikan F1 adalah hal yang semua orang harapkan.

Bentuk yang mencegahnya bukan kehati-hatian melainkan **tipe**:
`PembagianData` hanya menerima id dokumen. Pembagian pada tingkat segmen
karena itu tidak dapat dilakukan tanpa mengubah tipenya, dan tipe yang berubah
menuntut penjelasan — bentuk yang sama dengan `PutusanKategori` yang menjaga
Kappa pada fitur 003.
"""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.nlp.pelatihan.pembagian import PORSI, PembagianData
from tests.nlp.test_ambang_kesepakatan import RUMAH_TETAPAN

AKAR = Path(__file__).resolve().parents[2]
D08 = (AKAR / "docs" / "D08.md").read_text(encoding="utf-8")


def _pembagian(latih: int = 70, validasi: int = 15, uji: int = 15) -> PembagianData:
    n = 0

    def ambil(jumlah: int) -> frozenset[str]:
        nonlocal n
        hasil = frozenset(f"dok{i}" for i in range(n, n + jumlah))
        n += jumlah
        return hasil

    return PembagianData(
        id_pembagian="BAGI-2026-001",
        latih=ambil(latih),
        validasi=ambil(validasi),
        uji=ambil(uji),
        seed=42,
        versi_korpus="1.0",
    )


def test_pembagian_terbentuk() -> None:
    bagi = _pembagian()
    assert len(bagi.latih) == 70
    assert bagi.jumlah_dokumen == 100


def test_dokumen_pada_dua_himpunan_ditolak() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-02.**

    Satu dokumen pada latih dan uji sekaligus adalah persis kebocoran yang
    D-08 peringatkan — dan ia tidak meninggalkan jejak apa pun pada angka.
    """
    with pytest.raises(ValidationError) as galat:
        PembagianData(
            id_pembagian="BAGI-2026-001",
            latih=frozenset({"dok1", "dok2"}),
            validasi=frozenset({"dok3"}),
            uji=frozenset({"dok1"}),
            seed=42,
            versi_korpus="1.0",
        )
    assert "dok1" in str(galat.value)


def test_irisan_antara_validasi_dan_uji_juga_ditolak() -> None:
    """Ketiga pasangan diperiksa, bukan hanya latih lawan uji.

    Kebocoran validasi ke uji lebih halus dan sama merusaknya: konfigurasi
    dipilih pada dokumen yang kemudian dipakai menilai hasilnya.
    """
    with pytest.raises(ValidationError):
        PembagianData(
            id_pembagian="BAGI-2026-001",
            latih=frozenset({"dok1"}),
            validasi=frozenset({"dok2"}),
            uji=frozenset({"dok2"}),
            seed=42,
            versi_korpus="1.0",
        )


def test_himpunan_kosong_ditolak() -> None:
    """Himpunan uji kosong membuat seluruh evaluasi lolos tanpa menguji apa
    pun — bentuk kegagalan diam yang sama dengan pengekstrak yang
    mengembalikan untai kosong pada fitur 015."""
    with pytest.raises(ValidationError):
        PembagianData(
            id_pembagian="BAGI-2026-001",
            latih=frozenset({"dok1"}),
            validasi=frozenset({"dok2"}),
            uji=frozenset(),
            seed=42,
            versi_korpus="1.0",
        )


def test_pembagian_beku() -> None:
    """Pembagian yang dapat diubah setelah dibentuk adalah pembagian yang
    dapat disesuaikan ketika hasilnya mengecewakan."""
    bagi = _pembagian()
    with pytest.raises(ValidationError):
        bagi.latih = frozenset({"dok999"})  # type: ignore[misc]


def test_tipe_hanya_menerima_pengenal_dokumen() -> None:
    """**Sifat, bukan kasus.**

    Ketiga bidangnya bertipe `frozenset[str]` berisi id dokumen, dan tidak ada
    bidang yang menerima segmen. Pembagian pada tingkat segmen karena itu
    tidak dapat dilakukan tanpa mengubah tipenya.
    """
    bidang = set(PembagianData.model_fields)
    assert "segmen" not in bidang
    assert {"latih", "validasi", "uji"} <= bidang


def test_seed_wajib() -> None:
    """R-05 diuji penuh pada A-3; di sini hanya bahwa bidangnya tidak punya
    nilai bawaan. Seed bawaan adalah seed yang tidak pernah dipilih siapa pun,
    dan pembagian yang tidak dapat diulang membatalkan klaim reproduktibilitas
    NFR-15."""
    assert PembagianData.model_fields["seed"].is_required()


def _porsi_d08() -> dict[str, float]:
    """Baca porsi dari tabel D-08 Bagian 4.2, bukan menyalin angkanya.

    Uji yang menyalin hanya membuktikan dua salinan sama, termasuk ketika
    keduanya sudah menyimpang dari pemiliknya.
    """
    hasil: dict[str, float] = {}
    for nama, kunci in (("Latih", "latih"), ("Validasi", "validasi"), ("Uji", "uji")):
        for baris in D08.splitlines():
            if baris.startswith(f"| {nama} |"):
                cocok = re.search(r"\|\s*(\d+)%\s*\|", baris)
                assert cocok, baris
                hasil[kunci] = int(cocok.group(1)) / 100
                break
    return hasil


def test_porsi_sama_dengan_d08_bagian_4_2() -> None:
    """**R-03.** Dibaca dari `docs/D08.md` sungguhan."""
    assert _porsi_d08() == PORSI


def test_porsi_berjumlah_satu() -> None:
    """Bukan kerapian: porsi yang berjumlah 0,95 membuang 5% korpus tanpa
    seorang pun menyadarinya, dan korpus anotasi adalah yang paling mahal
    dihasilkan pada proyek ini."""
    assert sum(PORSI.values()) == pytest.approx(1.0)


def test_tidak_ada_angka_porsi_di_luar_satu_tempat() -> None:
    """**Uji yang menegakkan C-16 pada fitur ini.**

    Bentuknya sama dengan sapuan ambang B-6 fitur 003, termasuk daftar rumah
    tetapannya. Kedua sapuan bertabrakan pada satu nilai: porsi latih D-08
    adalah 0,70, sama dengan ambang Kappa D-03, sedangkan keduanya besaran
    yang sama sekali berbeda.

    **Batas itu diakui, bukan disembunyikan.** Sapuan berbasis nilai tidak
    dapat membedakan dua besaran yang bernilai sama; yang dipakai adalah
    daftar modul yang sengaja menjadi rumah sekelompok angka, dan daftar itu
    wajib tetap pendek — menambahnya adalah keputusan, bukan cara meloloskan
    berkas yang menyalakan sapuan.
    """
    import ast

    nilai = set(PORSI.values())
    pelanggaran: list[str] = []
    for berkas in sorted((AKAR / "src").rglob("*.py")):
        if berkas.resolve() in RUMAH_TETAPAN:
            continue
        for simpul in ast.walk(ast.parse(berkas.read_text(encoding="utf-8"))):
            if (
                isinstance(simpul, ast.Constant)
                and isinstance(simpul.value, float)
                and simpul.value in nilai
            ):
                pelanggaran.append(f"{berkas.relative_to(AKAR)}:{simpul.lineno}")
    assert not pelanggaran, "angka porsi di luar pembagian.py: " + "; ".join(pelanggaran)


def test_uraian_menyebut_alasan_pembagian_tingkat_dokumen() -> None:
    """Aturan tanpa alasan akan dilanggar oleh orang yang mengira ia usang.

    Pembagian tingkat segmen menghasilkan angka yang lebih tinggi, dan angka
    yang lebih tinggi tidak pernah terasa seperti kekeliruan.
    """
    import src.nlp.pelatihan.pembagian as modul

    uraian = modul.__doc__ or ""
    assert "segmen" in uraian
    assert "D-08" in uraian
