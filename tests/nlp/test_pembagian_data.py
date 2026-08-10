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
from src.nlp.pelatihan.pembagian import (
    JUMLAH_DOKUMEN_MINIMUM,
    PORSI,
    GalatPembagian,
    PembagianData,
    buat_pembagian,
    pastikan_beku,
)
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


# ------------------------------------------------------------ A-3, R-05


def _korpus(jumlah: int) -> list[str]:
    return [f"dok{i:04d}" for i in range(jumlah)]


def test_seed_sama_menghasilkan_susunan_sama() -> None:
    """**R-05.** Pembagian yang tidak dapat diulang membatalkan klaim
    reproduktibilitas NFR-15, dan pembatalannya baru ketahuan ketika seseorang
    mencoba mengulang hasil pada bulan 8."""
    a = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    b = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    assert a.latih == b.latih
    assert a.validasi == b.validasi
    assert a.uji == b.uji


def test_seed_berbeda_menghasilkan_susunan_berbeda() -> None:
    """Tanpa uji ini, pembagian yang mengabaikan seed sama sekali akan lolos
    uji sebelumnya — ia deterministik, hanya saja tidak terhadap seed."""
    a = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    b = buat_pembagian(_korpus(100), seed=8, versi_korpus="1.0", id_pembagian="B1")
    assert a.latih != b.latih


def test_urutan_masukan_tidak_mengubah_hasil() -> None:
    """Korpus yang sama dengan urutan berbeda adalah korpus yang sama.

    Tanpa ini, pembagian bergantung pada urutan berkas pada cakram — dan
    urutan itu berubah antar-mesin tanpa seorang pun mengubah apa pun.
    """
    maju = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    mundur = buat_pembagian(
        list(reversed(_korpus(100))), seed=7, versi_korpus="1.0", id_pembagian="B1"
    )
    assert maju.latih == mundur.latih


def test_porsi_hasil_mendekati_d08() -> None:
    bagi = buat_pembagian(_korpus(1000), seed=7, versi_korpus="1.0", id_pembagian="B1")
    assert len(bagi.latih) == 700
    assert len(bagi.validasi) == 150
    assert len(bagi.uji) == 150


def test_seluruh_dokumen_terpakai() -> None:
    """Korpus anotasi adalah artefak yang paling mahal dihasilkan proyek ini.
    Satu dokumen yang hilang karena pembulatan adalah pekerjaan anotator yang
    dibuang tanpa jejak."""
    bagi = buat_pembagian(_korpus(101), seed=7, versi_korpus="1.0", id_pembagian="B1")
    assert bagi.jumlah_dokumen == 101


def test_korpus_terlalu_kecil_ditolak_dengan_menyebut_jumlah_minimumnya() -> None:
    """Galat yang hanya berkata "terlalu kecil" memaksa pembacanya menebak
    berapa yang cukup."""
    with pytest.raises(GalatPembagian) as galat:
        buat_pembagian(_korpus(5), seed=7, versi_korpus="1.0", id_pembagian="B1")
    assert str(JUMLAH_DOKUMEN_MINIMUM) in str(galat.value)


def test_dokumen_berulang_pada_korpus_ditolak() -> None:
    """Dokumen yang tercatat dua kali akan masuk dua himpunan sekaligus —
    kebocoran yang sama dengan R-02, tetapi datang dari daftar masukannya."""
    with pytest.raises(GalatPembagian):
        buat_pembagian([*_korpus(50), "dok0000"], seed=7, versi_korpus="1.0", id_pembagian="B1")


# ------------------------------------------------------------ A-4, R-04


def test_pembagian_membawa_sidiknya() -> None:
    bagi = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    assert bagi.sidik.startswith("sha256:")


def test_sidik_berubah_bila_satu_dokumen_berpindah_himpunan() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-04.**

    Sidik yang tidak berubah ketika susunannya berubah adalah sidik yang tidak
    menjaga apa pun.
    """
    satu = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    pindah = sorted(satu.latih)[0]
    dua = PembagianData(
        id_pembagian=satu.id_pembagian,
        latih=satu.latih - {pindah},
        validasi=satu.validasi | {pindah},
        uji=satu.uji,
        seed=satu.seed,
        versi_korpus=satu.versi_korpus,
    )
    assert satu.sidik != dua.sidik


def test_sidik_sama_bagi_pembagian_yang_sama() -> None:
    a = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    b = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    assert a.sidik == b.sidik


def test_pembagian_ulang_yang_berbeda_ditolak() -> None:
    """**Pembekuan (R-04).**

    D-08 Bagian 4.2: pembagian dibekukan sebelum pelatihan pertama. Membagi
    ulang dengan hasil berbeda sesudah itu berarti angka pada laporan lama dan
    laporan baru dihitung atas himpunan uji yang berlainan — dan keduanya
    tercatat dengan nama yang sama.
    """
    beku = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    lain = buat_pembagian(_korpus(100), seed=8, versi_korpus="1.0", id_pembagian="B1")
    with pytest.raises(GalatPembagian) as galat:
        pastikan_beku(beku, lain)
    assert "beku" in str(galat.value).lower()


def test_pembagian_ulang_yang_sama_diterima() -> None:
    """Membagi ulang bukan pelanggaran; membagi ulang **dengan hasil berbeda**
    yang pelanggaran. Tanpa uji ini, penjagaannya akan menolak pemeriksaan ulang
    yang sah dan lalu dilucuti seseorang."""
    a = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    b = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    pastikan_beku(a, b)


def test_sisa_pembulatan_jatuh_ke_latih() -> None:
    """**Uji ini lahir dari mutasi yang tidak menyala.**

    `test_seluruh_dokumen_terpakai` memeriksa jumlah totalnya, dan total tetap
    utuh ke mana pun sisanya jatuh — sehingga uji itu lolos pada versi yang
    melemparkan sisa ke himpunan uji.

    Ke mana sisa jatuh bukan hal sepele: melemparkannya ke uji membuat
    himpunan uji tumbuh melampaui 15% D-08 pada setiap korpus yang tidak habis
    dibagi, dan porsi yang melar tanpa dinyatakan adalah porsi yang tidak lagi
    mengikuti dokumennya.
    """
    bagi = buat_pembagian(_korpus(101), seed=7, versi_korpus="1.0", id_pembagian="B1")
    assert len(bagi.validasi) == 15
    assert len(bagi.uji) == 15
    assert len(bagi.latih) == 71


def test_sidik_berubah_ketika_dua_dokumen_bertukar_himpunan() -> None:
    """**Uji kedua yang lahir dari mutasi yang tidak menyala, dan yang ini
    lebih penting.**

    `test_sidik_berubah_bila_satu_dokumen_berpindah_himpunan` memindahkan satu
    dokumen, sehingga **jumlah** kedua himpunan ikut berubah. Sidik yang
    dihitung dari jumlah saja tetap lolos uji itu.

    Pertukaran dua dokumen membiarkan jumlahnya persis sama dan hanya mengubah
    isinya — dan pertukaran itulah bentuk yang paling mungkin terjadi ketika
    seseorang membagi ulang dengan seed berbeda.
    """
    satu = buat_pembagian(_korpus(100), seed=7, versi_korpus="1.0", id_pembagian="B1")
    dari_latih = sorted(satu.latih)[0]
    dari_validasi = sorted(satu.validasi)[0]
    tukar = PembagianData(
        id_pembagian=satu.id_pembagian,
        latih=(satu.latih - {dari_latih}) | {dari_validasi},
        validasi=(satu.validasi - {dari_validasi}) | {dari_latih},
        uji=satu.uji,
        seed=satu.seed,
        versi_korpus=satu.versi_korpus,
    )
    assert len(tukar.latih) == len(satu.latih)
    assert len(tukar.validasi) == len(satu.validasi)
    assert tukar.sidik != satu.sidik
