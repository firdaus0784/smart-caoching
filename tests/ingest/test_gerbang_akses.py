"""Uji penjagaan akses pada Gerbang — R-02, R-05, R-12, C-03.

Ditulis setelah pemeriksaan Fase B menemukan empat cacat yang lolos seluruh
99 uji sebelumnya. Sebab keempatnya sama: **uji menguji jalur yang dibayangkan
penulisnya, bukan jalur yang tersedia.** `setujui` diuji dengan kredensial
salah; `tolak` tidak. `peringkat` diuji digerbangi; `area` dan
`alasan_terakhir` tidak.

Uji terakhir berkas ini adalah uji sifat menyeluruh — ia yang mencegah metode
kelima lolos dengan cara yang sama.
"""

import inspect

import pytest
from src.ingest.dokumen import Dokumen, StatusAnonimisasi, StatusPersetujuan, TingkatKerahasiaan
from src.ingest.gerbang import Gerbang
from src.ingest.peringkat import JenisSumber
from src.penyimpanan.area import Area
from src.penyimpanan.galat import GalatAksesDitolak
from src.penyimpanan.kredensial_baku import PEMANGGIL_LLM, PENJAWABAN, VERIFIKASI
from src.penyimpanan.tiruan import PenyimpanTiruan

ID_VERIFIKATOR = "vrf_001"
ALASAN_PEKA = "memuat NIK pada halaman 3"

# Metode yang mengembalikan keterangan tentang sebuah dokumen. Seluruhnya
# wajib menuntut kredensial.
PEMBACA = ("area", "alasan_terakhir", "peringkat")

# Dikecualikan dengan alasan yang dinyatakan, bukan karena terlupa:
# `terima` menerima dokumen baru dari jalur ingesti dan tidak mengembalikan
# keterangan apa pun; `cabut_persetujuan` sengaja tanpa kredensial (KB-014).
DIKECUALIKAN = frozenset({"terima", "cabut_persetujuan"})


def _dokumen() -> Dokumen:
    return Dokumen(
        id="dok_001",
        judul="Notulen rapat pleno",
        jenis=JenisSumber.DOKUMEN_SEKOLAH,
        penerbit="SDN Sukamaju",
        tahun=2026,
        tingkat_kerahasiaan=TingkatKerahasiaan.INTERNAL_SEKOLAH,
        status_persetujuan_pemilik=StatusPersetujuan.DIBERIKAN,
    )


def _gerbang() -> Gerbang:
    gerbang = Gerbang(PenyimpanTiruan())
    gerbang.terima(_dokumen(), "Notulen rapat pleno bulan Maret.")
    return gerbang


# --- Cacat 1: tolak() mengabaikan kredensial ---------------------------------


def test_jalur_penjawaban_tidak_dapat_menolak_dokumen() -> None:
    """Menilai isi karantina menuntut hak membacanya."""
    with pytest.raises(GalatAksesDitolak):
        _gerbang().tolak(PENJAWABAN, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan=ALASAN_PEKA)


def test_pemanggil_llm_tidak_dapat_menolak_dokumen() -> None:
    with pytest.raises(GalatAksesDitolak):
        _gerbang().tolak(
            PEMANGGIL_LLM, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan=ALASAN_PEKA
        )


# --- Cacat 2: alasan_terakhir bocor -----------------------------------------


def test_alasan_penolakan_tidak_terbaca_jalur_penjawaban() -> None:
    """R-12 pada pintu yang terlupa.

    Alasan penolakan secara alami berbunyi "memuat NIK pada halaman 3", dan
    dokumennya berada di karantina — area yang jalur penjawaban tidak berhak
    sentuh sama sekali.
    """
    gerbang = _gerbang()
    gerbang.tolak(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan=ALASAN_PEKA)
    with pytest.raises(GalatAksesDitolak):
        gerbang.alasan_terakhir(PENJAWABAN, "dok_001")


def test_verifikasi_tetap_dapat_membaca_alasan() -> None:
    """Penjagaan yang menutup semua orang bukan penjagaan melainkan kelumpuhan."""
    gerbang = _gerbang()
    gerbang.tolak(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan=ALASAN_PEKA)
    assert gerbang.alasan_terakhir(VERIFIKASI, "dok_001") == ALASAN_PEKA


# --- Cacat 3: area() mengungkap keberadaan ----------------------------------


def test_area_dokumen_karantina_tidak_terbaca_jalur_penjawaban() -> None:
    """Kelas kebocoran yang sama dengan yang A-6 tutup: daftar dokumen
    karantina dapat disusun hanya dengan menanyakan areanya."""
    with pytest.raises(GalatAksesDitolak):
        _gerbang().area(PENJAWABAN, "dok_001")


def test_dokumen_tak_dikenal_dijawab_sama_dengan_dokumen_karantina() -> None:
    """Jawaban yang berbeda sudah cukup untuk menyusun daftarnya."""
    gerbang = _gerbang()
    pesan = []
    for id_dokumen in ("dok_001", "dok_tidak_pernah_ada"):
        with pytest.raises(GalatAksesDitolak) as tertangkap:
            gerbang.area(PENJAWABAN, id_dokumen)
        pesan.append(tertangkap.value.tanggapan().galat.pesan_pengguna)
    assert pesan[0] == pesan[1]


def test_area_terbaca_jalur_penjawaban_setelah_disetujui() -> None:
    gerbang = _gerbang()
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
    assert gerbang.area(PENJAWABAN, "dok_001") is Area.KORPUS


# --- Cacat 4: status_anonimisasi tidak pernah disetel ------------------------


def test_status_anonimisasi_awalnya_menunggu() -> None:
    """D-14 Bagian 5.1 — `menunggu`, `terverifikasi`, `ditolak`."""
    assert _dokumen().status_anonimisasi is StatusAnonimisasi.MENUNGGU


def test_penolakan_menyetel_status_anonimisasi_ditolak() -> None:
    """tasks.md B-5 mensyaratkannya, dan saya sempat menandai B-5 selesai
    tanpa memenuhinya."""
    gerbang = _gerbang()
    gerbang.tolak(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan=ALASAN_PEKA)
    assert gerbang.dokumen(VERIFIKASI, "dok_001").status_anonimisasi is StatusAnonimisasi.DITOLAK


def test_persetujuan_menyetel_status_anonimisasi_terverifikasi() -> None:
    gerbang = _gerbang()
    gerbang.setujui(VERIFIKASI, "dok_001", id_verifikator=ID_VERIFIKATOR, alasan="bersih")
    dokumen = gerbang.dokumen(VERIFIKASI, "dok_001")
    assert dokumen.status_anonimisasi is StatusAnonimisasi.TERVERIFIKASI


def test_hanya_terverifikasi_yang_boleh_diindeks() -> None:
    """D-14 Bagian 5.1 menyatakannya sebagai sifat daftar, bukan satu nilai."""
    boleh = {s for s in StatusAnonimisasi if Dokumen.anonimisasi_mengizinkan_indeks(s)}
    assert boleh == {StatusAnonimisasi.TERVERIFIKASI}


# --- Uji sifat menyeluruh ----------------------------------------------------


def test_setiap_pembaca_keterangan_menuntut_kredensial() -> None:
    """**Uji terpenting berkas ini.**

    Ia tidak memeriksa satu metode melainkan seluruh permukaan kelasnya,
    sehingga metode kelima yang ditambahkan kelak tanpa kredensial akan
    tertangkap di sini — bukan pada pemeriksaan manual berikutnya yang mungkin
    tidak pernah terjadi.
    """
    publik = {
        nama
        for nama, anggota in inspect.getmembers(Gerbang, inspect.isfunction)
        if not nama.startswith("_")
    }
    wajib = publik - DIKECUALIKAN
    tanpa_kredensial = {
        nama
        for nama in wajib
        if "kredensial" not in inspect.signature(getattr(Gerbang, nama)).parameters
    }
    assert tanpa_kredensial == set(), f"metode tanpa kredensial: {tanpa_kredensial}"


def test_daftar_pembaca_tidak_tertinggal_dari_kelasnya() -> None:
    """Menjaga daftar PEMBACA di atas tetap sepadan dengan kenyataan."""
    for nama in PEMBACA:
        assert hasattr(Gerbang, nama), nama
