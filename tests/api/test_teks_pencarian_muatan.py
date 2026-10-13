"""Judul ikut teks pencarian pada muatan — T-2 fitur 041, R-01, R-04, R-05.

TK-88: segmen pasal tidak membawa identitas regulasinya. Uji pertama
membuktikan perbaikannya; uji pembanding membuktikan bahwa tanpa judul pasal
berisi sama dari regulasi berjudul serupa memang tidak terbedakan — sehingga
uji pertama tidak lulus karena kebetulan.
"""

from __future__ import annotations

from src.api.penjawab_korpus import bangun_muatan
from src.kamus.segmen import IndeksTujuan
from src.penyimpanan.indeks import SegmenTerindeks, StatusLisensi
from src.penyimpanan.korpus_penjawab import BarisKorpus, MuatanKorpus
from src.rag.pengambilan.bm25 import SumberBM25, bangun_indeks
from src.rag.pengambilan.teks_pencarian import ATURAN_PENCARIAN
from tests.api.test_penjawab_korpus import _baris, _metadata, _muatan
from tests.konftes_asinkron import jalankan

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA
ISI = "Kepala sekolah menyusun rencana sarana prasarana."
KUERI = "apa isi Peraturan Contoh Nomor 12 Tahun 2026 tentang rencana sarana prasarana?"


def _sepuluh_regulasi() -> list[BarisKorpus]:
    """Nomor 7 s.d. 16, tahun dan isi pasal sama; pembukaan memuat judulnya."""
    baris = []
    for n in range(7, 17):
        judul = f"Peraturan Contoh Nomor {n} Tahun 2026"
        m = _metadata(judul=judul)
        baris.append(
            _baris(f"d{n:02d}:0001", teks=judul.upper(), penanda_bagian="Pembukaan", metadata=m)
        )
        baris.append(_baris(f"d{n:02d}:0002", teks=ISI, penanda_bagian="Pasal 1", metadata=m))
    return baris


def _pasal_pertama(ids: list[str]) -> str:
    return next(i for i in ids if i.endswith(":0002"))


def test_pasal_regulasi_yang_disebut_terbedakan_oleh_judulnya() -> None:
    """R-01 (M-1): pasal regulasi Nomor 12 menjadi pasal teratas."""
    muatan = _muatan(_sepuluh_regulasi(), [])
    hasil = jalankan(SumberBM25(muatan.indeks_leksikal[UTAMA]).cari(KUERI, batas=20))
    ids = [k.id_segmen for k in hasil.peringkat]
    assert _pasal_pertama(ids) == "d12:0002"
    assert ids.index("d12:0002") < 2


def test_pembanding_tanpa_judul_pasal_tidak_terbedakan() -> None:
    """Tanpa judul, kesepuluh pasal berskor sama; urutannya ditentukan
    pengenal segmen, bukan regulasi yang ditanya."""
    segmen = [
        SegmenTerindeks(
            id_segmen=b.id_segmen,
            id_dokumen=b.id_dokumen,
            teks=b.teks,
            lisensi=StatusLisensi.TERBUKA,
            indeks_tujuan=UTAMA,
            anonimisasi_terverifikasi=True,
            penanda_bagian=b.penanda_bagian,
        )
        for b in _sepuluh_regulasi()
    ]
    indeks = bangun_indeks(segmen, versi="tanpa-judul", indeks_tujuan=UTAMA)
    hasil = jalankan(SumberBM25(indeks).cari(KUERI, batas=20))
    skor = {k.id_segmen: k.skor for k in hasil.peringkat if k.id_segmen.endswith(":0002")}
    assert len(set(skor.values())) == 1
    assert _pasal_pertama([k.id_segmen for k in hasil.peringkat]) == "d07:0002"


def test_teks_bahan_sitasi_dan_layak_tidak_berubah() -> None:
    """R-05, P-1 A (M-2): yang dikirim ke model dan dikutip tetap teks segmen."""
    baris = _sepuluh_regulasi()
    muatan = _muatan(baris, [])
    for b in baris:
        assert muatan.bahan[b.id_segmen].teks == b.teks
        assert muatan.sitasi[b.id_segmen].judul == b.metadata.judul  # type: ignore[union-attr]
    assert muatan.layak_utama == frozenset(b.id_segmen for b in baris)


def test_indeks_metadata_juga_dicari_dengan_judulnya() -> None:
    """P-5 A (M-4): bacaan lanjutan ditemukan lewat judulnya."""
    kajian = _baris(
        "k1:0001",
        teks="Ringkasan penelitian manajemen.",
        lisensi_segmen="tertutup",
        metadata=_metadata(judul="Laporan Zqvbtrx", lisensi="CC-BY-NC 4.0"),
    )
    muatan = _muatan([], [kajian])
    hasil = jalankan(SumberBM25(muatan.indeks_leksikal[METADATA]).cari("zqvbtrx", batas=5))
    assert [k.id_segmen for k in hasil.peringkat] == ["k1:0001"]


def test_versi_memuat_penanda_aturan() -> None:
    """R-04 (M-3): putaran sebelum dan sesudah tidak terbaca sebagai indeks
    yang sama."""
    muatan = _muatan([], [])
    assert muatan.versi_indeks == f"utama:sidik-u;metadata:sidik-m;{ATURAN_PENCARIAN}"
    assert muatan.indeks_leksikal[UTAMA].versi == f"utama:sidik-u;{ATURAN_PENCARIAN}"
    assert muatan.indeks_leksikal[METADATA].versi == f"metadata:sidik-m;{ATURAN_PENCARIAN}"


def test_muatan_tetap_murni_atas_potret() -> None:
    m = bangun_muatan(
        MuatanKorpus(sidik="a", baris=tuple(_sepuluh_regulasi())),
        MuatanKorpus(sidik="b", baris=()),
    )
    assert m.versi_indeks.startswith("utama:a;metadata:b;")
