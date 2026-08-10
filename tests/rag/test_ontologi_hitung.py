"""Uji penghitungan ontologi — B-1 fitur 005, R-03, R-06, R-07.

**Tugas terpenting fitur ini, dan ia tentang cara melapor bukan cara
menghitung.** Menghitung anggota himpunan tidak menuntut satu berkas; yang
menuntutnya adalah menolak melaporkan satu angka.

Laporan yang hanya menyebut "512 konsep" tidak dapat dibedakan antara 512
konsep berdefinisi dan 512 baris tabel. MK-06 adalah syarat Definisi Selesai
dengan tenggat bulan 8, dan menambah baris tabel jauh lebih cepat daripada
menyusun definisi — godaannya tidak menuntut niat buruk, hanya tenggat.
"""

from src.rag.ontologi.hitung import HasilHitung, hitung_ontologi
from src.rag.ontologi.skema import JenisRelasi, Konsep, Ontologi, Relasi

DOK = frozenset({"DOC-001"})


def _konsep(
    id_konsep: str, definisi: str = "Definisi yang terisi.", terkurasi: bool = True
) -> Konsep:
    return Konsep(
        id_konsep=id_konsep,
        label=f"Label {id_konsep}",
        definisi=definisi,
        id_dokumen_rujukan=DOK,
        sumber_terkurasi=terkurasi,
    )


def _relasi(id_relasi: str, asal: str, tujuan: str) -> Relasi:
    return Relasi(
        id_relasi=id_relasi,
        konsep_asal=asal,
        konsep_tujuan=tujuan,
        jenis=JenisRelasi.MENGATUR,
        id_dokumen_rujukan=DOK,
    )


def test_seluruhnya_sah_menghasilkan_dua_angka_yang_sama() -> None:
    onto = Ontologi(konsep=(_konsep("K1"), _konsep("K2")), relasi=(_relasi("R1", "K1", "K2"),))
    hasil = hitung_ontologi(onto)
    assert hasil.konsep_sah == 2
    assert hasil.konsep_mentah == 2
    assert hasil.relasi_sah == 1
    assert hasil.relasi_mentah == 1


def test_konsep_tanpa_definisi_tidak_terhitung_sah_tetapi_terhitung_mentah() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-03 dan R-07.**

    Dua angka bersama. Satu angka saja dapat dibaca sebagai yang lain, dan
    yang dibaca adalah yang lebih besar.
    """
    onto = Ontologi(konsep=(_konsep("K1"), _konsep("K2", definisi="")), relasi=())
    hasil = hitung_ontologi(onto)
    assert hasil.konsep_sah == 1
    assert hasil.konsep_mentah == 2
    assert hasil.konsep_tanpa_definisi == 1


def test_konsep_dari_karantina_tidak_terhitung_sah() -> None:
    """**R-06, dan ini C-03 yang merambat ke tempat yang tidak terduga.**

    D-06 Bagian 11.2: "Konsep dari bahan karantina tidak sah — konsekuensi
    C-03." Ontologi diekspor untuk HKI dan publikasi; dokumen yang belum
    diverifikasi anonimisasinya lolos ke berkas yang dilampirkan naskah.
    """
    onto = Ontologi(konsep=(_konsep("K1"), _konsep("K2", terkurasi=False)), relasi=())
    hasil = hitung_ontologi(onto)
    assert hasil.konsep_sah == 1
    assert hasil.konsep_mentah == 2


def test_relasi_menuju_konsep_tak_sah_tidak_terhitung() -> None:
    """Menghitungnya menaikkan angka MK-06 lewat pintu belakang: konsep
    kosong tidak terhitung, tetapi relasi menujunya terhitung."""
    onto = Ontologi(
        konsep=(_konsep("K1"), _konsep("K2", definisi="")),
        relasi=(_relasi("R1", "K1", "K2"),),
    )
    hasil = hitung_ontologi(onto)
    assert hasil.relasi_sah == 0
    assert hasil.relasi_mentah == 1


def test_relasi_dari_konsep_tak_sah_juga_tidak_terhitung() -> None:
    """Kedua ujung. Memeriksa satu ujung meloloskan separuh, dan separuh yang
    lolos adalah yang arahnya kebetulan tidak diuji."""
    onto = Ontologi(
        konsep=(_konsep("K1", definisi=""), _konsep("K2")),
        relasi=(_relasi("R1", "K1", "K2"),),
    )
    assert hitung_ontologi(onto).relasi_sah == 0


def test_tidak_ada_bidang_bernama_jumlah_saja() -> None:
    """**Sifat, bukan kasus.**

    Bidang tunggal adalah bidang yang pembacanya anggap sebagai yang ia
    harapkan, dan yang ia harapkan adalah yang lebih besar. Bentuk yang sama
    dengan kedua rerata bernama fitur 004.
    """
    bidang = set(HasilHitung.model_fields)
    assert "jumlah" not in bidang
    assert "jumlah_konsep" not in bidang
    assert {"konsep_sah", "konsep_mentah", "relasi_sah", "relasi_mentah"} <= bidang


def test_selisih_dilaporkan_sebagai_pekerjaan_yang_tersisa() -> None:
    """Selisihnya satu-satunya angka yang berguna bagi orang yang
    menjadwalkan."""
    onto = Ontologi(
        konsep=(_konsep("K1"), _konsep("K2", definisi=""), _konsep("K3", terkurasi=False)),
        relasi=(),
    )
    hasil = hitung_ontologi(onto)
    assert hasil.konsep_tanpa_definisi == 2


def test_ontologi_kosong_menghasilkan_nol_pada_keduanya() -> None:
    """Nol pada keduanya, bukan galat. Ontologi kosong adalah keadaan awal
    yang sah; yang ditolak adalah mengekspornya."""
    hasil = hitung_ontologi(Ontologi(konsep=(), relasi=()))
    assert hasil.konsep_sah == 0
    assert hasil.konsep_mentah == 0


def test_uraian_menyebut_alasan_dua_angka() -> None:
    """Aturan tanpa alasan akan disederhanakan menjadi satu angka oleh orang
    yang merasa sedang merapikan."""
    import src.rag.ontologi.hitung as modul

    uraian = modul.__doc__ or ""
    assert "MK-06" in uraian
    assert "D-06" in uraian
