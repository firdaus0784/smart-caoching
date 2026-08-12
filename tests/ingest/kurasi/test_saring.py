"""Uji penyaringan berlapis dan rumah tetapan kurasi — A-2 fitur 010.

Kebutuhan: R-03 s.d. R-06, R-12. Dokumen: D-06 Bagian 6 dan Bagian 8.3.

Dua hal diuji di sini, dan keduanya menahan hal yang sama dari arah berbeda.

**Penyaringan** menahan kandidat yang tidak boleh masuk antrean. **Rumah
tetapan** menahan angka yang tidak boleh ada. Angka yang tidak boleh ada itu
ambang relevansi L4: D-06 Bagian 6 menyerahkannya ke BT-24, uji ingesti
percobaan bulan 3, dan menuliskan nilai awal apa pun adalah menyetel ambang
yang C-16 larang. Kekosongannya **yang benar**, dan uji di bawah menegakkannya
— sebab kekosongan yang tidak diuji akan diisi seseorang yang bermaksud baik.

Angka D-06 Bagian 8.3 **dibaca dari `docs/D06.md`**, bukan disalin ke berkas
ini. Uji yang menyalin angkanya hanya membuktikan dua salinan sama, termasuk
ketika keduanya sudah menyimpang dari pemiliknya. Bentuk yang sama dengan
`test_butir.py` (A-1), `test_ambang_kesepakatan.py` (003), dan pemeriksa arah
(009).
"""

import re
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from perkakas.pemeriksa.ambang import rumah_tetapan
from src.ingest.kurasi import tetapan
from src.ingest.kurasi.butir import ButirPengetahuan, JenisSumberButir
from src.ingest.kurasi.saring import (
    HasilSaring,
    Keadaan,
    Lapis,
    Tindakan,
    saring,
)
from src.ingest.kurasi.tetapan import (
    HARI_BERTURUT_SEBELUM_PENGEREMAN,
    PAGU_KURASI_HARIAN,
    PAGU_TAYANG_PER_PENGGUNA,
    PENGALI_AMBANG_ANTREAN,
)
from src.kamus.segmen import StatusKeberlakuan
from src.nlp.anotasi.skema import KategoriMasalah

AKAR = Path(__file__).resolve().parents[3]

TETAPAN_YANG_DIMILIKI_D06 = {
    "PAGU_KURASI_HARIAN",
    "PENGALI_AMBANG_ANTREAN",
    "HARI_BERTURUT_SEBELUM_PENGEREMAN",
    "PAGU_TAYANG_PER_PENGGUNA",
    "TENGGAT_PENARIKAN_HARI_KERJA",
}
"""Angka D-06 yang rumah ini miliki, disebut namanya satu per satu.

Empat dari Bagian 8.3; `TENGGAT_PENARIKAN_HARI_KERJA` dari Bagian 7.5, masuk
pada tugas B-3. Penambahannya menyalakan uji ini lebih dulu — itu memang
gunanya: sebuah angka tidak masuk rumah tetapan tanpa seseorang menyatakannya.

Bukan "boleh ada tetapan lain". Rumah tetapan yang menerima tambahan tanpa
disebut namanya adalah tempat ambang relevansi L4 akan mendarat — dan ia
mendarat sebagai angka yang tampak sah karena tetangganya sah.
"""


def _butir(**ganti: object) -> ButirPengetahuan:
    """Kandidat yang lolos L1 s.d. L3 kecuali bidang yang diganti.

    Sengaja berbeda dari pembangun pada `test_butir.py`: yang itu menguji batas
    bidang, yang ini menguji jalur lapis. Nilai bawaannya karena itu dipilih
    agar lolos, bukan agar menguji batas.
    """
    argumen: dict[str, object] = {
        "id_butir": "BTR-001",
        "jenis_sumber": JenisSumberButir.REGULASI,
        "judul": "Kewajiban sekolah menyusun rencana kegiatan dan anggaran",
        "alasan_relevansi": (
            "Sekolah Anda menetapkan tata kelola sebagai prioritas, "
            "dan penyusunan anggaran jatuh bulan depan."
        ),
        "inti_temuan": "Rencana kegiatan disusun bersama komite sekolah setiap tahun.",
        "implikasi_tindakan": ("Susun jadwal rapat komite sekolah.",),
        "perkiraan_waktu_baca": 3,
        "kategori": KategoriMasalah.K3,
        "id_dokumen_sumber": "DOC-001",
        "lisensi": "CC-BY-4.0",
        "status_keberlakuan": StatusKeberlakuan.BERLAKU,
        "tanggal_akses": date(2026, 8, 12),
    }
    argumen.update(ganti)
    return ButirPengetahuan(**argumen)  # type: ignore[arg-type]


def _saring(butir: ButirPengetahuan, **ganti: object) -> HasilSaring:
    argumen: dict[str, object] = {"id_dokumen_dikenal": frozenset[str]()}
    argumen.update(ganti)
    return saring(butir, **argumen)  # type: ignore[arg-type]


# --------------------------------------------------------- R-06 · L4 menunggu


def test_l4_menunggu_tidak_masuk_antrean_dan_tidak_dibuang() -> None:
    """**Uji terpenting berkas ini** — R-06, dan ia menegakkan dua penyangkalan.

    Kandidat yang lolos L1 s.d. L3 tidak berhak masuk antrean: skor relevansi
    menuntut klasifikasi K1–K8 (fitur 017) dan ambang BT-24 yang belum ada.
    Ia juga tidak berhak dibuang: tidak ada dasar untuk menyatakannya tidak
    relevan.

    D-06 Bagian 6 menyebut kedua akibat yang salah dan tidak menyebut mana yang
    lebih ringan — meloloskan membanjiri kurator yang hanya punya empat jam per
    minggu; membuang mengosongkan feed dan memicu titik kritis T5 pada D-02.
    """
    hasil = _saring(_butir())
    assert hasil.lapis_terakhir is Lapis.L4_RELEVANSI
    assert hasil.keadaan is Keadaan.MENUNGGU
    assert not hasil.boleh_masuk_antrean
    assert hasil.tindakan is Tindakan.TERTAHAN
    assert hasil.tindakan is not Tindakan.DIBUANG


def test_menunggu_bukan_ragam_gugur_maupun_lolos() -> None:
    """Pengulangan keenam pola "tiga keadaan, bukan dua".

    `HasilSistem` (015), `HasilKesepakatan` (003), `bendera` (016), `Nilai`
    (004), `HasilHitung` (005), `Status` validator (008). Keadaan kedua yang
    dipakai untuk dua hal adalah keadaan yang salah satunya hilang.
    """
    assert len(Keadaan) == 3
    assert Keadaan.MENUNGGU not in (Keadaan.LOLOS, Keadaan.GUGUR)


def test_alasan_menunggu_menyebut_apa_yang_ditunggunya() -> None:
    """Alasan yang tidak menyebut apa yang ditunggu adalah alasan yang tidak
    dapat ditagih.

    Bentuk yang sama dengan `_MENUNGGU_FITUR_020` pada fitur 008: siapa pun
    yang membaca hasilnya dapat memeriksa apakah penghalangnya sudah hilang.
    """
    alasan = _saring(_butir()).alasan
    assert "017" in alasan
    assert "BT-24" in alasan


def test_belum_ada_kandidat_yang_dapat_masuk_antrean() -> None:
    """Keadaan jujur pipeline ini: **belum ada** jalur menuju antrean.

    Diuji atas keempat jenis sumber agar pernyataannya tidak bergantung pada
    satu kandidat yang kebetulan dipilih. `tasks.md` menyatakannya terbuka —
    pipeline ini belum dapat mengisi antrean kurasi, dan yang berdiri sesudahnya
    adalah seluruh jalur sesudahnya.
    """
    for jenis in JenisSumberButir:
        status = (
            StatusKeberlakuan.BERLAKU if jenis is JenisSumberButir.REGULASI else None
        )
        hasil = _saring(_butir(jenis_sumber=jenis, status_keberlakuan=status))
        assert not hasil.boleh_masuk_antrean, jenis


def test_boleh_masuk_antrean_sifat_terhitung_bukan_bidang() -> None:
    """Bidang dapat diisi `True` oleh pemanggil yang lelah; sifat terhitung
    tidak dapat.

    Antrean yang menerima kandidat tak tersaring adalah antrean yang membanjiri
    kurator, dan gerbang yang antreannya membanjir akan dilewati orang — yang
    dilewati bersamanya adalah C-06.
    """
    assert "boleh_masuk_antrean" not in HasilSaring.model_fields
    with pytest.raises(ValidationError):
        HasilSaring(
            lapis_terakhir=Lapis.L4_RELEVANSI,
            keadaan=Keadaan.MENUNGGU,
            tindakan=Tindakan.TERTAHAN,
            alasan="apa pun",
            boleh_masuk_antrean=True,  # type: ignore[call-arg]
        )


# ------------------------------------------------------------- R-03 · L1 lisensi


def test_l1_lisensi_tidak_dikenali_dibuang() -> None:
    """PP-01 dan KL-02. Lisensi diambil dari metadata, **tidak disimpulkan**:
    keterangan yang tidak terbaca mesin diperlakukan sebagai tertutup."""
    hasil = _saring(_butir(lisensi="Hak cipta dilindungi undang-undang"))
    assert hasil.lapis_terakhir is Lapis.L1_LISENSI
    assert hasil.keadaan is Keadaan.GUGUR
    assert hasil.tindakan is Tindakan.DIBUANG


def test_l1_gugur_tidak_melanjutkan_ke_lapis_yang_menyimpan() -> None:
    """**Inilah arti "dibuang, tidak disimpan".**

    Kandidat di bawah gugur pada ketiga lapis sekaligus: lisensinya tertutup,
    dokumennya duplikat, regulasinya dicabut. Bila lapis dijalankan seluruhnya
    lalu hasilnya dipilih, ia akan mendarat pada L3 — **rujukan historis, yang
    disimpan**. Butir berlisensi tidak jelas yang tersimpan adalah butir yang
    kelak diangkat seseorang yang tidak tahu mengapa ia ada di sana.

    Uji ini karena itu menguji **urutan**, bukan hanya hasil satu lapis.
    """
    hasil = _saring(
        _butir(
            lisensi="Hak cipta dilindungi undang-undang",
            status_keberlakuan=StatusKeberlakuan.DICABUT,
        ),
        id_dokumen_dikenal={"DOC-001"},
    )
    assert hasil.lapis_terakhir is Lapis.L1_LISENSI
    assert hasil.tindakan is Tindakan.DIBUANG
    assert hasil.tindakan is not Tindakan.RUJUKAN_HISTORIS


def test_l1_meloloskan_lisensi_terbuka() -> None:
    assert _saring(_butir(lisensi="CC0-1.0")).lapis_terakhir is Lapis.L4_RELEVANSI


# ------------------------------------------------------------ R-04 · L2 kebaruan


def test_l2_duplikat_dibuang() -> None:
    hasil = _saring(_butir(), id_dokumen_dikenal={"DOC-001"})
    assert hasil.lapis_terakhir is Lapis.L2_KEBARUAN
    assert hasil.keadaan is Keadaan.GUGUR
    assert hasil.tindakan is Tindakan.DIBUANG


def test_l2_versi_lebih_baru_menggantikan_yang_lama() -> None:
    """R-04 memuat dua aturan, dan yang kedua mudah luput: duplikat dibuang,
    **tetapi versi lebih baru menggantikan yang lama**.

    Tanpa uji ini, penyaringan yang membuang setiap dokumen yang id-nya sudah
    dikenal tetap lulus — dan pembaruan regulasi tidak akan pernah masuk.
    """
    hasil = _saring(
        _butir(), id_dokumen_dikenal={"DOC-001"}, versi_lebih_baru_dari="2025-01-01"
    )
    assert hasil.lapis_terakhir is Lapis.L4_RELEVANSI
    assert hasil.keadaan is not Keadaan.GUGUR


def test_l2_dokumen_belum_dikenal_lolos() -> None:
    assert (
        _saring(_butir(), id_dokumen_dikenal={"DOC-999"}).lapis_terakhir
        is Lapis.L4_RELEVANSI
    )


# --------------------------------------------------------- R-05 · L3 keberlakuan


def test_l3_menolak_dicabut_dan_diubah() -> None:
    """**Keduanya, bukan salah satunya** — D-06 Bagian 6 menuntut status
    `berlaku`, sehingga `diubah` gugur sama seperti `dicabut`.

    Aturan ini berbeda dari D-07 Bagian 4.5, yang mengizinkan regulasi `diubah`
    dipakai menjawab dengan penanda. Yang satu mengatur **ingesti**, yang lain
    mengatur **penjawaban**; menyamakannya adalah kekeliruan yang saya buat pada
    spec fitur ini dan saya perbaiki sebelum kode ditulis.
    """
    for status in (StatusKeberlakuan.DICABUT, StatusKeberlakuan.DIUBAH):
        hasil = _saring(_butir(status_keberlakuan=status))
        assert hasil.lapis_terakhir is Lapis.L3_KEBERLAKUAN, status
        assert hasil.keadaan is Keadaan.GUGUR, status
        assert hasil.tindakan is Tindakan.RUJUKAN_HISTORIS, status


@pytest.mark.parametrize("status", list(StatusKeberlakuan))
def test_l3_hanya_berlaku_yang_melanjutkan(status: StatusKeberlakuan) -> None:
    """Disapu atas **seluruh** nilai enum, bukan atas daftar yang disalin ke sini.

    Nilai keempat yang ditambahkan D-14 kelak akan menyalakan uji ini, bukan
    lolos diam-diam. Daftar yang disalin akan lulus tanpa pernah melihatnya.
    """
    hasil = _saring(_butir(status_keberlakuan=status))
    if status is StatusKeberlakuan.BERLAKU:
        assert hasil.lapis_terakhir is Lapis.L4_RELEVANSI
    else:
        assert hasil.lapis_terakhir is Lapis.L3_KEBERLAKUAN


def test_status_keberlakuan_memang_memuat_diubah() -> None:
    """Sapuan atas enum yang menyusut adalah sapuan yang berhenti memeriksa.

    Tanpa uji ini, menghapus `DIUBAH` dari `StatusKeberlakuan` akan membuat
    uji sapuan di atas tetap lulus — dan L3 berhenti menolaknya.
    """
    assert {s.value for s in StatusKeberlakuan} >= {"berlaku", "diubah", "dicabut"}


def test_l3_dilewati_bagi_sumber_bukan_regulasi() -> None:
    """Riset dan praktik baik tidak memiliki status keberlakuan.

    Memeriksanya akan menuntut setiap butir riset mengaku `berlaku`, dan L3
    kemudian memeriksa hal yang tidak berarti apa-apa.
    """
    hasil = _saring(
        _butir(jenis_sumber=JenisSumberButir.RISET, status_keberlakuan=None)
    )
    assert hasil.lapis_terakhir is Lapis.L4_RELEVANSI


def test_l3_regulasi_tanpa_status_gugur() -> None:
    """Regulasi yang statusnya belum terisi **tidak** dianggap berlaku.

    Arah kekeliruannya disengaja dan sejalan dengan KL-01: kekeliruan ke arah
    ini hanya mengurangi jumlah butir; kekeliruan ke arah sebaliknya membuat
    sistem menjawab berdasarkan regulasi yang mungkin sudah dicabut (C-07).
    """
    hasil = _saring(
        _butir(jenis_sumber=JenisSumberButir.REGULASI, status_keberlakuan=None)
    )
    assert hasil.lapis_terakhir is Lapis.L3_KEBERLAKUAN
    assert hasil.tindakan is Tindakan.RUJUKAN_HISTORIS


# ------------------------------------------------------- keempat tindakan berbeda


def test_empat_tindakan_gugur_tidak_disamakan() -> None:
    """D-06 memisahkan dibuang, rujukan historis, kolam cadangan, dan tertahan.

    Menyamakan keempatnya menjadi "gugur" akan kehilangan tiga di antaranya —
    dan yang hilang menentukan apakah sebuah butir tersimpan atau tidak.
    """
    assert len(Tindakan) == 5
    assert Tindakan.DIBUANG is not Tindakan.RUJUKAN_HISTORIS


def test_hasil_saring_beku() -> None:
    with pytest.raises(ValidationError):
        _saring(_butir()).keadaan = Keadaan.LOLOS  # type: ignore[misc]


def test_alasan_selalu_terisi() -> None:
    """Termasuk pada lapis yang meloloskan. Hasil tanpa alasan adalah hasil yang
    tidak dapat ditinjau kurator maupun peneliti."""
    for butir in (
        _butir(),
        _butir(lisensi="tertutup"),
        _butir(status_keberlakuan=StatusKeberlakuan.DICABUT),
    ):
        assert _saring(butir).alasan.strip()


# ------------------------------------------------- R-12 · angka dibaca dari D-06


def _tabel_8_3() -> dict[str, str]:
    """Baris tabel D-06 Bagian 8.3 — kendali → nilai awal. Sumbernya, bukan
    salinannya."""
    teks = (AKAR / "docs" / "D06.md").read_text(encoding="utf-8")
    awal = teks.index("### 8.3 Pagu dan Pengereman")
    akhir = teks.index("### 8.4")
    baris: dict[str, str] = {}
    for garis in teks[awal:akhir].splitlines():
        sel = [s.strip() for s in garis.split("|")[1:-1]]
        if len(sel) != 3 or sel[0] == "Kendali" or set(sel[0]) <= set("-: "):
            continue
        baris[sel[0]] = sel[1]
    return baris


def _angka(teks: str) -> int:
    cocok = re.search(r"\d+", teks)
    assert cocok is not None, teks
    return int(cocok.group())


def test_tabel_8_3_memang_terbaca() -> None:
    """Pemeriksaan yang tidak menemukan sumbernya tidak memeriksa apa pun.

    Tanpa uji ini, perubahan judul bagian pada D-06 akan membuat keempat uji di
    bawah membandingkan terhadap tabel kosong — dan seluruhnya lulus.
    """
    assert len(_tabel_8_3()) == 4


def test_pagu_kurasi_harian_dari_d06() -> None:
    assert _angka(_tabel_8_3()["Pagu kurasi harian"]) == PAGU_KURASI_HARIAN


def test_pengali_ambang_antrean_dari_d06() -> None:
    """D-06 menuliskannya sebagai "Antrean > 2× pagu kurasi harian".

    Kode menyimpannya sebagai pengali, bukan sebagai angka 30, agar ia tetap
    benar ketika pagu harian berubah — dan pagu harian akan berubah bila
    kapasitas kurator berubah.
    """
    assert _angka(_tabel_8_3()["Ambang rasio antrean"]) == PENGALI_AMBANG_ANTREAN


def test_hari_berturut_sebelum_pengereman_dari_d06() -> None:
    """Angkanya berada pada **kolom kendali**, bukan kolom nilai — D-06
    menuliskannya "Tindakan bila melampaui 3 hari berturut-turut"."""
    kendali = [k for k in _tabel_8_3() if k.startswith("Tindakan bila melampaui")]
    assert len(kendali) == 1
    assert _angka(kendali[0]) == HARI_BERTURUT_SEBELUM_PENGEREMAN


def test_pagu_tayang_per_pengguna_dari_d06() -> None:
    """Berbeda dari pagu kurasi harian, dan D-06 menuliskan keduanya terpisah.

    Menyatukannya akan membuat penambahan kapasitas kurator membanjiri pengguna.
    """
    assert _angka(_tabel_8_3()["Pagu tayang per pengguna"]) == PAGU_TAYANG_PER_PENGGUNA
    assert PAGU_TAYANG_PER_PENGGUNA != PAGU_KURASI_HARIAN


# ------------------------------------------- R-12 · rumah tetapan dan kekosongan


def test_tetapan_kurasi_terdaftar_sebagai_rumah_tetapan() -> None:
    """Rumah keempat, dan pendaftarannya keputusan — bukan cara meloloskan
    sapuan.

    Yang ia peroleh dengan masuk daftar adalah **aturan 3** pemeriksa C-16:
    setiap tetapan di dalamnya wajib menyebut sumbernya. Modul yang menyebut
    dirinya rumah tetapan pada uraiannya tetapi tidak terdaftar pada
    pemeriksanya adalah modul yang uraiannya tidak ditegakkan siapa pun.
    """
    assert Path(tetapan.__file__).resolve() in rumah_tetapan(AKAR)


def test_isi_rumah_tetapan_disebut_satu_per_satu() -> None:
    """**Bukan "boleh ada tetapan lain".**

    Rumah tetapan dilewati sapuan nilai pemeriksa C-16, sehingga daftar yang
    berbunyi "boleh ada tambahan" menjadi tempat teraman bagi angka yang tidak
    boleh ada.
    """
    isi = {
        nama
        for nama, nilai in vars(tetapan).items()
        if not nama.startswith("_") and isinstance(nilai, int)
    }
    assert isi == TETAPAN_YANG_DIMILIKI_D06


def test_ambang_relevansi_l4_belum_ada_dan_itu_yang_benar() -> None:
    """C-16, D-06 Bagian 6. **Kekosongan yang diuji.**

    D-06 menyerahkan ambang relevansi L4 ke BT-24, uji ingesti percobaan bulan
    3. Menuliskan nilai awal di sini adalah menyetel ambang, bukan mengutipnya —
    dan D-06 menyebut kedua akibat yang salah bila ia ditebak: terlalu longgar
    membanjiri antrean kurasi; terlalu ketat membuat feed kekurangan isi dan
    memicu titik kritis T5 pada D-02.

    Bentuk yang sama dengan `AmbangKecukupan` fitur 007, dan alasannya sama:
    yang paling mungkin mengisinya adalah orang yang bermaksud baik.
    """
    for nama in vars(tetapan):
        assert "RELEVANSI" not in nama, nama
        assert "L4" not in nama, nama
