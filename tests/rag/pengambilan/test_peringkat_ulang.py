"""Uji tahap 5 dan jalur mundur BT-30 — R-05, C-09.

Yang diuji di sini bukan "urutannya benar". Jalur mundur BT-30 memang tidak
mengubah urutan, sehingga uji atas urutan saja **lulus pada kedua keadaan**
yang R-05 minta dibedakan.

Yang diuji: dua keadaan dengan urutan keluaran yang persis sama tetap dapat
dibedakan dari keterangannya. Itu satu-satunya pernyataan yang jalur mundur
diam tidak dapat memenuhinya.
"""

import pytest
from pydantic import ValidationError
from src.rag.pengambilan.gabung import HasilGabungan, Penyumbang
from src.rag.pengambilan.peringkat_ulang import (
    SEBAB_BT30,
    HasilPeringkatUlang,
    JalurMundurBT30,
    Pemeringkat,
    Pemeringkatan,
    PemeringkatDipakai,
    PemeringkatTidakTersedia,
    peringkat_ulang,
)
from tests.konftes_asinkron import jalankan


def _segmen(*id_segmen: str) -> tuple[HasilGabungan, ...]:
    """Hasil gabungan berskor menurun, sesuai urutan yang diberikan."""
    return tuple(
        HasilGabungan(
            id_segmen=satu,
            skor=1.0 / (urutan + 1),
            penyumbang=(Penyumbang(nama_sumber="bm25", peringkat=urutan + 1),),
        )
        for urutan, satu in enumerate(id_segmen)
    )


class PemeringkatTiruan(Pemeringkat):
    """Pemeringkat yang benar-benar berjalan; urutan keluarannya ditentukan uji."""

    def __init__(self, urutan_keluar: tuple[str, ...]) -> None:
        self._urutan_keluar = urutan_keluar

    @property
    def keterangan(self) -> Pemeringkatan:
        return PemeringkatDipakai(nama_model="lintas-enkoder-tiruan", versi_model="1.0")

    async def urutkan(self, kueri, segmen):
        menurut_id = {s.id_segmen: s for s in segmen}
        return tuple(menurut_id[satu] for satu in self._urutan_keluar if satu in menurut_id)


# ------------------------------------------------------------- R-05, BT-30


def test_jalur_mundur_menyatakan_dirinya_pada_keluaran() -> None:
    """**Inti R-05.** Ketiadaan pemeringkat ulang tercatat, bukan didiamkan."""
    hasil = jalankan(
        peringkat_ulang("kueri", _segmen("SEG-A", "SEG-B"), pemeringkat=PemeringkatTidakTersedia())
    )
    assert isinstance(hasil.pemeringkatan, JalurMundurBT30)
    assert hasil.pemeringkatan.sebab == SEBAB_BT30


def test_jalur_mundur_memakai_urutan_penggabungan_apa_adanya() -> None:
    """BT-30: tahap 5 memakai hasil penggabungan langsung."""
    masuk = _segmen("SEG-A", "SEG-B", "SEG-C")
    hasil = jalankan(peringkat_ulang("kueri", masuk, pemeringkat=PemeringkatTidakTersedia()))
    assert [s.id_segmen for s in hasil.segmen] == ["SEG-A", "SEG-B", "SEG-C"]


def test_pemeringkat_yang_berjalan_tanpa_mengubah_urutan_tetap_terbedakan() -> None:
    """**Uji yang membuat R-05 berarti.**

    Dua pemanggilan menghasilkan urutan segmen yang **persis sama**. Uji atas
    urutan saja lulus pada keduanya. Hanya keterangannya yang membedakan, dan
    itulah yang jalur mundur diam tidak dapat sediakan.
    """
    masuk = _segmen("SEG-A", "SEG-B")
    berjalan = jalankan(
        peringkat_ulang("kueri", masuk, pemeringkat=PemeringkatTiruan(("SEG-A", "SEG-B")))
    )
    mundur = jalankan(peringkat_ulang("kueri", masuk, pemeringkat=PemeringkatTidakTersedia()))

    assert [s.id_segmen for s in berjalan.segmen] == [s.id_segmen for s in mundur.segmen]
    assert berjalan.pemeringkatan != mundur.pemeringkatan
    assert isinstance(berjalan.pemeringkatan, PemeringkatDipakai)
    assert isinstance(mundur.pemeringkatan, JalurMundurBT30)


def test_pemeringkat_yang_berjalan_mengubah_urutan() -> None:
    hasil = jalankan(
        peringkat_ulang(
            "kueri",
            _segmen("SEG-A", "SEG-B", "SEG-C"),
            pemeringkat=PemeringkatTiruan(("SEG-C", "SEG-A", "SEG-B")),
        )
    )
    assert [s.id_segmen for s in hasil.segmen] == ["SEG-C", "SEG-A", "SEG-B"]


# ----------------------------------------------------------------- C-09


def test_pemeringkat_yang_berjalan_mencatat_nama_dan_versi_model() -> None:
    """C-09 menuntut versi model pada setiap keluaran percobaan."""
    hasil = jalankan(
        peringkat_ulang("kueri", _segmen("SEG-A"), pemeringkat=PemeringkatTiruan(("SEG-A",)))
    )
    assert hasil.pemeringkatan == PemeringkatDipakai(
        nama_model="lintas-enkoder-tiruan", versi_model="1.0"
    )


# ------------------------------------------------- bentuk, bukan pemeriksaan


def test_keterangan_pemeringkatan_tidak_memiliki_nilai_baku() -> None:
    """Tidak ada cara menyusun hasil tahap 5 tanpa menyatakan siapa yang
    menjalankannya. Nilai baku apa pun di sini mengembalikan jalur mundur yang
    diam lewat pintu belakang."""
    with pytest.raises(ValidationError):
        HasilPeringkatUlang(segmen=())


def test_jalur_mundur_menuntut_sebab_yang_tidak_kosong() -> None:
    with pytest.raises(ValidationError):
        JalurMundurBT30(sebab="")


def test_pemeringkat_dipakai_menuntut_nama_dan_versi_yang_tidak_kosong() -> None:
    with pytest.raises(ValidationError):
        PemeringkatDipakai(nama_model="lintas-enkoder", versi_model="")


def test_pemeringkat_wajib_diserahkan_pemanggil() -> None:
    """Tanpa nilai baku: pemanggil yang tidak punya pemeringkat menuliskan
    `PemeringkatTidakTersedia()`, bukan menghilangkan parameternya."""
    with pytest.raises(TypeError):
        jalankan(peringkat_ulang("kueri", _segmen("SEG-A")))  # type: ignore[call-arg]


# ------------------------------------------------------------------ C-01


def test_pemeringkat_tidak_boleh_menghilangkan_segmen() -> None:
    """Bukti yang lenyap pada tahap 5 lenyap tanpa satu pun catatan."""
    with pytest.raises(ValueError, match="himpunan segmen"):
        jalankan(
            peringkat_ulang(
                "kueri",
                _segmen("SEG-A", "SEG-B"),
                pemeringkat=PemeringkatTiruan(("SEG-A",)),
            )
        )


def test_pemeringkat_tidak_boleh_mengarang_segmen() -> None:
    """Segmen yang muncul di tahap 5 tidak pernah ditemukan sumber mana pun."""

    class PemeringkatMengarang(PemeringkatTiruan):
        async def urutkan(self, kueri, segmen):
            dikarang = HasilGabungan(
                id_segmen="SEG-KARANGAN",
                skor=9.0,
                penyumbang=(Penyumbang(nama_sumber="bm25", peringkat=1),),
            )
            return (dikarang, *segmen)

    with pytest.raises(ValueError, match="himpunan segmen"):
        jalankan(
            peringkat_ulang("kueri", _segmen("SEG-A"), pemeringkat=PemeringkatMengarang(("SEG-A",)))
        )
