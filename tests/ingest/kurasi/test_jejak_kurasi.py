"""Uji jejak kurasi — B-2 fitur 010, R-09, R-13, FR-I05.

FR-I05: *"Sistem mencatat jejak audit setiap tindakan kurasi (siapa, kapan,
apa, alasan)."* Empat bidang, dan **"siapa" berarti peran** — C-05 dan KM-03
melarang data pribadi kurator masuk jejak.

## Yang diuji di sini bukan bahwa jejak dapat menulis

Yang diuji: jejak **tidak dapat** menulis nama, **tidak dapat** melupakan salah
satu dari empat bidang, dan **tidak dapat** disunting sesudah ditulis. Jejak
yang dapat disunting tidak membuktikan apa pun tentang saat ia ditulis, dan
justru itu yang ditanyakan seseorang yang menelusuri sebuah putusan.
"""

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from src.ingest.kurasi.jejak import BarisKurasi, GalatJejakKurasi, JejakKurasi
from src.ingest.kurasi.putusan import (
    AlasanTolak,
    JenisPutusan,
    PeranKurasi,
    Putusan,
)

AKAR = Path(__file__).resolve().parents[3]


def _putusan(**ganti: object) -> Putusan:
    argumen: dict[str, object] = {
        "jenis": JenisPutusan.SETUJUI,
        "id_butir": "BTR-001",
        "peran_pemutus": PeranKurasi.KURATOR,
        "waktu": datetime(2026, 8, 12, 3, 0, tzinfo=UTC),
    }
    argumen.update(ganti)
    return Putusan(**argumen)  # type: ignore[arg-type]


def _tolak(kode: AlasanTolak = AlasanTolak.TL_01) -> Putusan:
    return _putusan(jenis=JenisPutusan.TOLAK, alasan_tolak=kode)


# ------------------------------------------------------- R-09 · empat bidang


def test_keempat_bidang_fr_i05_ada() -> None:
    """Siapa, kapan, apa, alasan. Bidang yang hilang membuat baris jejak tidak
    dapat menjawab pertanyaan yang membuatnya ditulis."""
    jejak = JejakKurasi()
    jejak.catat(_putusan(), catatan="Bidang lengkap dan parafrase memadai.")
    (baris,) = jejak.baris
    assert baris.peran is PeranKurasi.KURATOR
    assert baris.waktu == datetime(2026, 8, 12, 3, 0, tzinfo=UTC)
    assert baris.id_butir == "BTR-001"
    assert baris.jenis is JenisPutusan.SETUJUI
    assert baris.alasan


def test_tidak_ada_bidang_kelima() -> None:
    """FR-I05 menyebut empat, dan bidang kelima yang bermuatan bebas adalah
    tempat data pribadi mendarat tanpa melewati pemeriksaan mana pun."""
    assert set(BarisKurasi.__dataclass_fields__) == {
        "peran",
        "waktu",
        "id_butir",
        "jenis",
        "alasan",
    }


def test_setiap_putusan_tercatat_termasuk_yang_tidak_menyetujui() -> None:
    """Jejak yang hanya mencatat persetujuan tidak dapat menjawab mengapa
    sebuah butir tidak pernah tayang — dan itu pertanyaan yang lebih sering
    diajukan."""
    jejak = JejakKurasi()
    jejak.catat(_putusan(), catatan="Layak tayang.")
    jejak.catat(_tolak())
    jejak.catat(
        _putusan(jenis=JenisPutusan.TUNDA, kembali_pada=date(2026, 9, 1)),
        catatan="Tenggat masih jauh.",
    )
    assert [b.jenis for b in jejak.baris] == [
        JenisPutusan.SETUJUI,
        JenisPutusan.TOLAK,
        JenisPutusan.TUNDA,
    ]


def test_waktu_diambil_dari_putusan_bukan_dari_jam_penulisan() -> None:
    """FR-I05 menanyakan kapan tindakan kurasi terjadi.

    Dua stempel waktu yang dapat berselisih akan menimbulkan pertanyaan mana
    yang berlaku, dan pertanyaan itu tidak memiliki jawaban yang tertulis di
    mana pun.
    """
    putusan = _putusan(waktu=datetime(2026, 1, 1, 0, 0, tzinfo=UTC))
    jejak = JejakKurasi()
    jejak.catat(putusan, catatan="Layak tayang.")
    assert jejak.baris[0].waktu == putusan.waktu


# --------------------------------------------------- R-08 · alasan tetap berkode


def test_penolakan_mencatat_kode_tl_bukan_untai_bebas() -> None:
    """Kodenya **adalah** alasannya. Menyalinnya ke jejak sebagai untai bebas
    akan membuat FR-I02 menghitung sebelas ejaan bagi satu alasan."""
    jejak = JejakKurasi()
    jejak.catat(_tolak(AlasanTolak.TL_09))
    assert jejak.baris[0].alasan == "TL-09"


def test_catatan_bebas_pada_penolakan_ditolak() -> None:
    """Penolakan sudah membawa alasannya. Untai bebas di sampingnya akan
    menjadi tempat alasan yang sesungguhnya ditulis, dan kolom berkode menjadi
    hiasan yang tetap dapat dijumlahkan tetapi tidak lagi berarti."""
    with pytest.raises(GalatJejakKurasi):
        JejakKurasi().catat(_tolak(), catatan="sebenarnya karena sumbernya lemah")


def test_putusan_bukan_penolakan_wajib_membawa_catatan() -> None:
    """"Alasan" adalah salah satu dari empat bidang FR-I05, dan persetujuan
    tanpa alasan adalah baris jejak yang tidak menjelaskan apa pun."""
    with pytest.raises(GalatJejakKurasi):
        JejakKurasi().catat(_putusan())
    with pytest.raises(GalatJejakKurasi):
        JejakKurasi().catat(_putusan(), catatan="   ")


# ---------------------------------------------------- R-13 · tanpa data pribadi


def test_jejak_tidak_memuat_nama_kurator() -> None:
    """**Uji terpenting berkas ini.**

    Ditegakkan tipe, bukan pemeriksaan: `peran` bertipe `PeranKurasi`, sehingga
    tidak ada tempat bagi nama untuk masuk. Pemeriksaan atas untai akan
    meloloskan nama yang tidak dikenali daftarnya, dan nama yang tidak dikenali
    justru yang paling mungkin milik orang sungguhan.
    """
    assert BarisKurasi.__dataclass_fields__["peran"].type in (
        "PeranKurasi",
        PeranKurasi,
    )
    jejak = JejakKurasi()
    jejak.catat(_putusan(), catatan="Layak tayang.")
    assert jejak.baris[0].peran in set(PeranKurasi)


@pytest.mark.parametrize(
    "catatan",
    [
        "Sesuai arahan pemilik NIK 3273010101800001.",
        "Konfirmasi lewat 081234567890 sudah dilakukan.",
    ],
)
def test_catatan_bermuatan_data_pribadi_ditolak(catatan: str) -> None:
    """R-13 dan KM-03 — **tolak, jangan saring.**

    Menyaring diam-diam menghasilkan baris yang tampak bersih sementara
    penulisnya tidak pernah tahu ia hampir membocorkan sesuatu, dan ia akan
    menulisnya lagi.
    """
    with pytest.raises(GalatJejakKurasi):
        JejakKurasi().catat(_putusan(), catatan=catatan)


def test_galat_tidak_mengulang_muatan_yang_ditolaknya() -> None:
    """Galat yang mengutip alasannya memindahkan kebocoran dari jejak ke log —
    kebalikan persis dari maksudnya. Bentuk yang sama dengan `GalatJejak`
    fitur 002."""
    with pytest.raises(GalatJejakKurasi) as galat:
        JejakKurasi().catat(_putusan(), catatan="Hubungi 081234567890 dahulu.")
    assert "081234567890" not in str(galat.value)
    assert "nomor telepon" in str(galat.value)


def test_pendeteksi_data_pribadi_satu_salinan() -> None:
    """Pendeteksi yang disalin akan berbeda dari aslinya pada hari salah satunya
    diperbarui, dan yang tertinggal adalah yang menjaga jejak kurasi.

    Kekeliruan `IndeksTujuan` yang ditulis dua kali dan lolos dua fitur (KB-036)
    berbentuk persis seperti ini.
    """
    berkas = [
        AKAR / "src" / "ingest" / "jejak.py",
        AKAR / "src" / "ingest" / "kurasi" / "jejak.py",
    ]
    for jalur in berkas:
        isi = jalur.read_text(encoding="utf-8")
        assert "from src.ingest.data_pribadi import" in isi, jalur
        assert "re.compile" not in isi, jalur


# ------------------------------------------------------------ R-09 · tambah-saja


def test_jejak_tanpa_cara_menyunting_maupun_menghapus() -> None:
    """Sifat tambah-saja ditegakkan **permukaan modul**, bukan tata tertib.

    Yang tidak disediakan tidak dapat dipanggil karena lupa. Bentuk yang sama
    dengan `JejakArea` fitur 002 dan `src/logbook/penulis.py`.
    """
    terlarang = {"sunting", "hapus", "ubah", "ganti", "kosongkan", "timpa"}
    tersedia = {n for n in dir(JejakKurasi) if not n.startswith("_")}
    assert not (tersedia & terlarang)


def test_baris_yang_dikembalikan_tidak_dapat_diubah_pemanggil() -> None:
    """Daftar yang dikembalikan apa adanya dapat ditambahi maupun dikosongkan
    pemanggil, dan sifat tambah-saja kemudian hanya berlaku bagi yang sopan."""
    jejak = JejakKurasi()
    jejak.catat(_putusan(), catatan="Layak tayang.")
    baris = jejak.baris
    assert isinstance(baris, tuple)
    with pytest.raises(AttributeError):
        baris.append(baris[0])  # type: ignore[attr-defined]


def test_baris_beku() -> None:
    jejak = JejakKurasi()
    jejak.catat(_putusan(), catatan="Layak tayang.")
    with pytest.raises(Exception):
        jejak.baris[0].alasan = "lain"  # type: ignore[misc]


def test_baris_ditolak_tidak_meninggalkan_setengah_catatan() -> None:
    """Seluruh pemeriksaan berjalan **sebelum** baris ditambahkan. Galat yang
    tetap menulis barisnya membocorkan justru yang dilarangnya."""
    jejak = JejakKurasi()
    with pytest.raises(GalatJejakKurasi):
        jejak.catat(_putusan(), catatan="Hubungi 081234567890 dahulu.")
    assert jejak.baris == ()
