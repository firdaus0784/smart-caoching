"""Uji penyisihan batch pembanding — C-3 fitur 003, R-13, FR-C10, D-03 BT-13.

Batch yang memakai pra-anotasi wajib menyisihkan sebagian dokumen tanpa
pra-anotasi sebagai pembanding. Tanpa pembanding, tidak ada cara mengetahui
apakah kesepakatan yang tinggi berasal dari anotator yang sepaham atau dari
anotator yang menyetujui saran mesin yang sama — dan keduanya menghasilkan
angka yang serupa pada laporan.

**Yang tidak diuji di sini, dan sebabnya penting:** berapa porsi minimum
pembanding. D-01 FR-C10 menulis "sebagian"; D-03 BT-13 menulis "disarankan
menyisihkan sebagian batch". Tidak ada angka pada dokumen mana pun. C-16
melarang menetapkan ambang di luar prosedur kalibrasi, dan menaruh satu angka
di sini akan menjadi ambang yang tidak pernah dikalibrasi siapa pun —
kekeliruan yang justru dijaga B-6.

Karena itu yang ditegakkan adalah **batas yang tertulis**: batch berpra-anotasi
tanpa satu pun pembanding ditolak. Porsinya dihitung dan dilaporkan, tidak
dinilai. Batas ini diakui terbuka dan tertulis pada uraian modulnya.
"""

import pytest
from pydantic import ValidationError
from src.nlp.anotasi.batch import BatchAnotasi, DokumenAnotasi, StatusPraAnotasi

TANPA = StatusPraAnotasi.TANPA_PRA_ANOTASI
DENGAN = StatusPraAnotasi.DENGAN_PRA_ANOTASI
PEMBANDING = StatusPraAnotasi.PEMBANDING


def _dokumen(*status: StatusPraAnotasi) -> tuple[DokumenAnotasi, ...]:
    return tuple(
        DokumenAnotasi(id_dokumen=f"dok{i}", status_pra_anotasi=s) for i, s in enumerate(status)
    )


def test_batch_berpra_anotasi_tanpa_pembanding_ditolak() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-13.**"""
    with pytest.raises(ValidationError):
        BatchAnotasi(id_batch="b1", dokumen=_dokumen(DENGAN, DENGAN, DENGAN))


def test_batch_berpra_anotasi_dengan_pembanding_diterima() -> None:
    batch = BatchAnotasi(id_batch="b1", dokumen=_dokumen(DENGAN, DENGAN, PEMBANDING))
    assert batch.memakai_pra_anotasi
    assert batch.jumlah_pembanding == 1


def test_batch_tanpa_pra_anotasi_sama_sekali_tidak_menuntut_pembanding() -> None:
    """Batch yang tidak memakai pra-anotasi tidak mengendalikan apa pun.

    Menuntut pembanding di sini akan menolak seluruh batch bulan 3 — seluruh
    anotasi sebelum fitur 004 ada — dan penolakan itu akan diakali dengan
    menandai dokumen sebagai pembanding tanpa arti apa pun.
    """
    batch = BatchAnotasi(id_batch="b1", dokumen=_dokumen(TANPA, TANPA, TANPA))
    assert not batch.memakai_pra_anotasi
    assert batch.jumlah_pembanding == 0


def test_pembanding_pada_batch_tanpa_pra_anotasi_ditolak() -> None:
    """Pembanding tanpa yang dibandingkan adalah penandaan yang keliru.

    Ia tampak tidak berbahaya, dan justru itu bahayanya: dokumen bertanda
    pembanding masuk hitungan porsi pembanding pada laporan batch, sehingga
    angka yang dilaporkan menyatakan pengendalian yang tidak pernah ada.
    """
    with pytest.raises(ValidationError):
        BatchAnotasi(id_batch="b1", dokumen=_dokumen(TANPA, PEMBANDING))


def test_batch_kosong_ditolak() -> None:
    """Batch tanpa dokumen lolos seluruh pemeriksaan pembanding karena tidak
    ada yang diperiksa — bentuk kegagalan diam yang sama dengan pengekstrak
    yang mengembalikan untai kosong pada fitur 015."""
    with pytest.raises(ValidationError):
        BatchAnotasi(id_batch="b1", dokumen=())


def test_dokumen_berulang_ditolak() -> None:
    """Satu dokumen yang tercatat dua kali menggeser porsi pembanding tanpa
    satu dokumen pun benar-benar disisihkan."""
    berulang = (
        DokumenAnotasi(id_dokumen="dok1", status_pra_anotasi=DENGAN),
        DokumenAnotasi(id_dokumen="dok1", status_pra_anotasi=PEMBANDING),
    )
    with pytest.raises(ValidationError):
        BatchAnotasi(id_batch="b1", dokumen=berulang)


def test_porsi_pembanding_dihitung_atas_seluruh_batch() -> None:
    """Satu pembanding dari empat dokumen: 0,25."""
    batch = BatchAnotasi(id_batch="b1", dokumen=_dokumen(DENGAN, DENGAN, DENGAN, PEMBANDING))
    assert batch.porsi_pembanding == pytest.approx(0.25)


def test_porsi_pembanding_tidak_berlaku_bagi_batch_tanpa_pra_anotasi() -> None:
    """**Keadaan ketiga, dan ia bukan nol.**

    Porsi 0,0 pada batch yang tidak memakai pra-anotasi terbaca sebagai
    pengendalian yang hilang, padahal tidak ada yang perlu dikendalikan.
    Bentuk yang sama dengan `HasilKesepakatan.nilai` yang `None` ketika belum
    terhitung.
    """
    batch = BatchAnotasi(id_batch="b1", dokumen=_dokumen(TANPA, TANPA))
    assert batch.porsi_pembanding is None


def test_batch_beku() -> None:
    """Batch yang dapat ditambah dokumen sesudah dibentuk adalah batch yang
    pemeriksaan pembandingnya hanya berlaku sesaat."""
    batch = BatchAnotasi(id_batch="b1", dokumen=_dokumen(DENGAN, PEMBANDING))
    with pytest.raises(ValidationError):
        batch.dokumen = _dokumen(DENGAN, DENGAN)  # type: ignore[misc]


def test_uraian_menyatakan_porsi_minimum_belum_ditetapkan_siapa_pun() -> None:
    """**Uji terpenting berkas ini, dan ia tentang batas modulnya sendiri.**

    Batch dengan seratus dokumen berpra-anotasi dan satu pembanding lolos
    pemeriksaan ini. Itu memenuhi kata "sebagian" pada FR-C10 dan hampir pasti
    tidak memenuhi maksudnya. Modul yang tidak menyatakan batas seperti itu
    akan dipercayai melampaui batasnya — pelajaran yang sama dengan uraian
    pendeteksi data pribadi fitur 015 yang menyebut apa yang tidak
    dideteksinya.
    """
    import src.nlp.anotasi.batch as modul_batch

    uraian = modul_batch.__doc__ or ""
    assert "porsi minimum" in uraian.lower()
    assert "C-16" in uraian
    assert "BT-13" in uraian
