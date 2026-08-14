"""Uji pembungkus pemanggilan model — R-05, C-08, C-09.

C-08 mensyaratkan pembungkus mencatat versi model, konfigurasi, waktu, dan
biaya. C-09 mensyaratkan keluaran eksperimen mencatat lima bidang versi ke
`logbook/`. Keduanya berbeda dan tidak boleh dicampur:

- **setiap pemanggilan** menghasilkan catatan pemanggilan (C-08)
- **hanya pemanggilan yang bagian dari percobaan** menulis baris L1 (C-09)

Menulis L1 pada setiap pemanggilan akan membanjiri rekaman penelitian dengan
ribuan baris saat pilot, dan `docs/D10.md` Bagian 3 menegaskan L1 adalah
riwayat percobaan — satu baris per percobaan, bukan per permintaan.
"""

import json
from pathlib import Path

from src.kamus.segmen import IndeksTujuan, Peringkat
from src.llm.adaptor.tiruan import AdaptorTiruan
from src.llm.instruksi import KunciInstruksi, susun
from src.llm.logbook_versi import versi_fitur_001
from src.llm.pembungkus import Pembungkus
from src.llm.tipe import Data, Konfigurasi

KONFIGURASI = Konfigurasi(nama_model="tiruan", versi_model="0.0.1", suhu=0.0, batas_token=256)
DATA = (
    Data(
        id_segmen="seg_1",
        teks="isi segmen",
        peringkat_kepercayaan=Peringkat.T1,
        indeks_asal=IndeksTujuan.UTAMA,
    ),
)


def _pembungkus(tmp_path: Path) -> Pembungkus:
    return Pembungkus(
        adaptor=AdaptorTiruan(), akar_logbook=tmp_path, versi=versi_fitur_001("abc123")
    )


def test_tanggapan_membawa_seluruh_jejak_c08(tmp_path: Path) -> None:
    tanggapan = _pembungkus(tmp_path).panggil(
        instruksi=susun(KunciInstruksi.UJI_ASAP), data=DATA, konfigurasi=KONFIGURASI
    )
    assert tanggapan.versi_model == "0.0.1"
    assert tanggapan.waktu_selesai >= tanggapan.waktu_mulai
    assert tanggapan.biaya >= 0.0
    assert tanggapan.id_jejak


def test_riwayat_pemanggilan_terekam(tmp_path: Path) -> None:
    """C-08 — setiap pemanggilan tercatat, bukan hanya yang berhasil diingat."""
    pembungkus = _pembungkus(tmp_path)
    pembungkus.panggil(instruksi=susun(KunciInstruksi.UJI_ASAP), data=DATA, konfigurasi=KONFIGURASI)
    pembungkus.panggil(instruksi=susun(KunciInstruksi.UJI_ASAP), data=(), konfigurasi=KONFIGURASI)
    assert len(pembungkus.riwayat) == 2
    assert pembungkus.riwayat[0].nama_model == "tiruan"


def test_pemanggilan_biasa_tidak_menulis_logbook(tmp_path: Path) -> None:
    """L1 adalah riwayat percobaan, bukan riwayat permintaan."""
    _pembungkus(tmp_path).panggil(
        instruksi=susun(KunciInstruksi.UJI_ASAP), data=DATA, konfigurasi=KONFIGURASI
    )
    assert not (tmp_path / "L1-percobaan.jsonl").exists()


def test_pemanggilan_percobaan_menulis_satu_baris_l1(tmp_path: Path) -> None:
    _pembungkus(tmp_path).panggil(
        instruksi=susun(KunciInstruksi.UJI_ASAP),
        data=DATA,
        konfigurasi=KONFIGURASI,
        id_percobaan="EXP-2026-001",
        tujuan="menguji jalur pembungkus dari ujung ke ujung",
    )
    baris = (tmp_path / "L1-percobaan.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(baris) == 1
    catatan = json.loads(baris[0])
    for bidang in (
        "versi_kode",
        "versi_model",
        "versi_indeks",
        "versi_skema_anotasi",
        "pembagian_data",
    ):
        assert bidang in catatan, f"bidang versi {bidang} tidak tercatat"


def test_percobaan_tanpa_tujuan_ditolak(tmp_path: Path) -> None:
    """`docs/D10.md` Bagian 3 — tujuan satu kalimat: apa yang ingin diketahui."""
    try:
        _pembungkus(tmp_path).panggil(
            instruksi=susun(KunciInstruksi.UJI_ASAP),
            data=DATA,
            konfigurasi=KONFIGURASI,
            id_percobaan="EXP-2026-002",
        )
    except ValueError:
        return
    raise AssertionError("percobaan tanpa tujuan diterima")


def test_versi_model_pada_l1_diambil_dari_konfigurasi_bukan_tetapan(tmp_path: Path) -> None:
    """Versi yang dicatat wajib versi yang benar-benar dipakai."""
    lain = Konfigurasi(nama_model="tiruan", versi_model="9.9.9", suhu=0.0, batas_token=64)
    _pembungkus(tmp_path).panggil(
        instruksi=susun(KunciInstruksi.UJI_ASAP),
        data=(),
        konfigurasi=lain,
        id_percobaan="EXP-2026-003",
        tujuan="memastikan versi tercatat mengikuti konfigurasi",
    )
    catatan = json.loads((tmp_path / "L1-percobaan.jsonl").read_text(encoding="utf-8").strip())
    assert catatan["versi_model"] == "9.9.9"


def test_muatan_yang_benar_benar_dikirim_memisahkan_posisi(tmp_path: Path) -> None:
    """Uji penanda pada jalur utuh, bukan hanya pada pembangun muatan."""
    penanda = "PENANDA-JALUR-UTUH-91af-JANGAN-DI-INSTRUKSI"
    adaptor = AdaptorTiruan()
    pembungkus = Pembungkus(adaptor=adaptor, akar_logbook=tmp_path, versi=versi_fitur_001("abc123"))
    pembungkus.panggil(
        instruksi=susun(KunciInstruksi.UJI_ASAP),
        data=(
            Data(
                id_segmen="seg_x",
                teks=penanda,
                peringkat_kepercayaan=Peringkat.T3,
                indeks_asal=IndeksTujuan.UTAMA,
            ),
        ),
        konfigurasi=KONFIGURASI,
    )
    assert adaptor.muatan_terakhir is not None
    assert penanda not in adaptor.muatan_terakhir.posisi_instruksi
    assert any(penanda in b.teks for b in adaptor.muatan_terakhir.posisi_konten)


def test_kegagalan_penyedia_menjadi_galat_layanan_model(tmp_path: Path) -> None:
    """R-09 — seluruh kegagalan penyedia diseragamkan menjadi satu bentuk aman."""
    import pytest
    from src.llm.adaptor.dasar import AdaptorDasar, Permintaan
    from src.llm.galat import GalatLayananModel, KodeGalat
    from src.llm.tipe import Tanggapan

    class AdaptorGagal(AdaptorDasar):
        def kirim(self, permintaan: Permintaan) -> Tanggapan:
            raise RuntimeError("HTTP 503 from api.penyedia.example")

    pembungkus = Pembungkus(
        adaptor=AdaptorGagal(), akar_logbook=tmp_path, versi=versi_fitur_001("abc123")
    )
    with pytest.raises(GalatLayananModel) as tertangkap:
        pembungkus.panggil(
            instruksi=susun(KunciInstruksi.UJI_ASAP), data=DATA, konfigurasi=KONFIGURASI
        )

    tanggapan = tertangkap.value.tanggapan()
    assert tanggapan.galat.kode is KodeGalat.LAYANAN_MODEL_GAGAL
    assert "503" not in tanggapan.galat.pesan_pengguna
    assert "503" in tertangkap.value.untuk_log()


def test_kegagalan_penyedia_tidak_menulis_baris_l1(tmp_path: Path) -> None:
    """Percobaan yang tidak menghasilkan apa pun bukan percobaan yang berhasil."""
    import pytest
    from src.llm.adaptor.dasar import AdaptorDasar, Permintaan
    from src.llm.galat import GalatLayananModel
    from src.llm.tipe import Tanggapan

    class AdaptorGagal(AdaptorDasar):
        def kirim(self, permintaan: Permintaan) -> Tanggapan:
            raise RuntimeError("gagal")

    pembungkus = Pembungkus(
        adaptor=AdaptorGagal(), akar_logbook=tmp_path, versi=versi_fitur_001("abc123")
    )
    with pytest.raises(GalatLayananModel):
        pembungkus.panggil(
            instruksi=susun(KunciInstruksi.UJI_ASAP),
            data=DATA,
            konfigurasi=KONFIGURASI,
            id_percobaan="EXP-2026-004",
            tujuan="menguji perilaku saat penyedia gagal",
        )
    assert not (tmp_path / "L1-percobaan.jsonl").exists()
