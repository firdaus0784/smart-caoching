"""Uji adaptor tiruan deterministik — R-10, ADR-12.

Kriteria penerimaan spec menyebut satu hal yang tidak boleh dilanggar selama
seluruh rangkaian uji: **tidak ada pemanggilan ke penyedia luar** (G4-15).
Adaptor ini yang membuat hal itu mungkin tanpa memilih penyedia lebih dulu.

Determinisme bukan kenyamanan. Uji penanda C-18 pada D-5 membandingkan muatan
yang dihasilkan; muatan yang berubah tiap pemanggilan membuat perbandingan itu
tidak bermakna.
"""

from src.llm.adaptor.dasar import Permintaan
from src.llm.adaptor.tiruan import AdaptorTiruan
from src.llm.instruksi import KunciInstruksi, susun
from src.kamus.segmen import IndeksTujuan, Peringkat
from src.llm.tipe import Data, Konfigurasi

KONFIGURASI = Konfigurasi(nama_model="tiruan", versi_model="0.0.1", suhu=0.0, batas_token=256)


def _permintaan(teks_data: str = "isi segmen") -> Permintaan:
    return Permintaan(
        instruksi=susun(KunciInstruksi.UJI_ASAP),
        data=(
            Data(
                id_segmen="seg_1",
                teks=teks_data,
                peringkat_kepercayaan=Peringkat.T1,
                indeks_asal=IndeksTujuan.UTAMA,
            ),
        ),
        konfigurasi=KONFIGURASI,
    )


def test_masukan_sama_menghasilkan_keluaran_sama() -> None:
    a = AdaptorTiruan().kirim(_permintaan())
    b = AdaptorTiruan().kirim(_permintaan())
    assert a.teks == b.teks


def test_masukan_berbeda_menghasilkan_keluaran_berbeda() -> None:
    """Tanpa ini, adaptor yang selalu mengembalikan untai tetap juga lolos."""
    a = AdaptorTiruan().kirim(_permintaan("segmen pertama"))
    b = AdaptorTiruan().kirim(_permintaan("segmen kedua"))
    assert a.teks != b.teks


def test_tanggapan_membawa_jejak_yang_diwajibkan_c08() -> None:
    tanggapan = AdaptorTiruan().kirim(_permintaan())
    assert tanggapan.versi_model == "0.0.1"
    assert tanggapan.waktu_selesai >= tanggapan.waktu_mulai
    assert tanggapan.biaya == 0.0, "adaptor tiruan tidak boleh mengaku berbiaya"
    assert tanggapan.id_jejak


def test_permintaan_terakhir_terekam_untuk_diperiksa() -> None:
    """Uji penanda C-18 pada D-5 memeriksa muatan yang benar-benar terbentuk."""
    adaptor = AdaptorTiruan()
    permintaan = _permintaan()
    adaptor.kirim(permintaan)
    assert adaptor.terakhir == permintaan


def test_modul_tidak_mengimpor_pustaka_jaringan() -> None:
    """G4-15 — tidak ada pemanggilan jaringan selama rangkaian uji."""
    from pathlib import Path

    from perkakas.pemeriksa.ast_aturan import impor_pada

    berkas = Path(__file__).resolve().parents[2] / "src" / "llm" / "adaptor" / "tiruan.py"
    modul = {i.modul for i in impor_pada(berkas)}
    jaringan = {"socket", "http", "urllib", "requests", "httpx", "aiohttp"}
    assert not (modul & jaringan), f"adaptor tiruan mengimpor pustaka jaringan: {modul & jaringan}"


def test_adaptor_tiruan_memenuhi_kontrak_dasar() -> None:
    from src.llm.adaptor.dasar import AdaptorDasar

    assert isinstance(AdaptorTiruan(), AdaptorDasar)
