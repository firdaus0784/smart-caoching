"""Uji tipe pembungkus model — R-06, C-17, C-18, D-13 Bagian 6.

Pemisahan instruksi dan data adalah wujud C-18. Ia dimulai di sini, pada
tipenya: `Instruksi` dan `Data` bukan dua nama untuk untai yang sama,
melainkan dua tipe yang tidak dapat saling menggantikan.

`Data` sudah membawa `peringkat_kepercayaan` dan `indeks_asal` meskipun
pengambilan belum ada. Bila bidang itu baru ditambahkan pada fitur 007, C-02
dan C-19 harus disisipkan ke jalur yang sudah berjalan — pola yang persis
ingin dihindari G1-4.
"""

import pytest
from pydantic import ValidationError
from src.kamus.segmen import IndeksTujuan, Peringkat
from src.llm.tipe import Data, Konfigurasi, Tanggapan


def test_peringkat_hanya_t1_sampai_t4() -> None:
    """D-13 Bagian 6 — empat peringkat, tidak lebih."""
    assert {p.value for p in Peringkat} == {"T1", "T2", "T3", "T4"}


def test_indeks_tujuan_hanya_utama_dan_metadata() -> None:
    """D-14 Bagian 5 — menentukan boleh tidaknya masuk konteks LLM (FR-D06)."""
    assert {i.value for i in IndeksTujuan} == {"utama", "metadata"}


def test_data_menolak_peringkat_di_luar_daftar() -> None:
    with pytest.raises(ValidationError):
        Data(
            id_segmen="seg_1",
            teks="isi",
            peringkat_kepercayaan="T9",  # type: ignore[arg-type]
            indeks_asal=IndeksTujuan.UTAMA,
        )


def test_data_menolak_indeks_asal_di_luar_daftar() -> None:
    with pytest.raises(ValidationError):
        Data(
            id_segmen="seg_1",
            teks="isi",
            peringkat_kepercayaan=Peringkat.T1,
            indeks_asal="lain",  # type: ignore[arg-type]
        )


def test_data_menolak_id_segmen_kosong() -> None:
    """Segmen tanpa pengenal tidak dapat disitasi, dan sitasi wajib (MK-07)."""
    with pytest.raises(ValidationError):
        Data(
            id_segmen="",
            teks="isi",
            peringkat_kepercayaan=Peringkat.T1,
            indeks_asal=IndeksTujuan.UTAMA,
        )


def test_data_tidak_dapat_dipakai_sebagai_instruksi() -> None:
    """Inti C-18: keduanya bukan dua nama untuk untai yang sama."""
    from src.llm.tipe import Instruksi

    assert not issubclass(Data, Instruksi)
    assert not issubclass(Instruksi, Data)


def test_konfigurasi_tidak_memuat_parameter_alat() -> None:
    """C-17 — ketiadaan kemampuan bertindak dimulai dari bentuk konfigurasinya."""
    terlarang = ("tool", "alat", "function", "fungsi", "plugin", "agent")
    bidang = set(Konfigurasi.model_fields)
    tercemar = [b for b in bidang if any(k in b.lower() for k in terlarang)]
    assert not tercemar, f"konfigurasi memuat parameter alat: {tercemar}"


def test_tanggapan_mewajibkan_jejak_biaya_dan_waktu() -> None:
    """C-08 — pembungkus mencatat versi model, konfigurasi, waktu, biaya."""
    wajib = {"teks", "versi_model", "waktu_mulai", "waktu_selesai", "biaya", "id_jejak"}
    assert wajib <= set(Tanggapan.model_fields)


def test_tipe_tidak_dapat_diubah_setelah_dibentuk() -> None:
    data = Data(
        id_segmen="seg_1",
        teks="isi",
        peringkat_kepercayaan=Peringkat.T3,
        indeks_asal=IndeksTujuan.UTAMA,
    )
    with pytest.raises(ValidationError):
        data.peringkat_kepercayaan = Peringkat.T1  # type: ignore[misc]


def test_bidang_asing_ditolak() -> None:
    with pytest.raises(ValidationError):
        Data(
            id_segmen="seg_1",
            teks="isi",
            peringkat_kepercayaan=Peringkat.T1,
            indeks_asal=IndeksTujuan.UTAMA,
            alat="jalankan_perintah",  # type: ignore[call-arg]
        )
