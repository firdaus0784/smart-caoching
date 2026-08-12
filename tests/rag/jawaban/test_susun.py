"""Uji penyusun tanggapan — C-1 fitur 009, R-10, R-11, R-12.

Lapisan **kedua**, bukan pertama. Yang menjaga jalur dari keluaran model ke
tanggapan sudah tiga, dan masing-masing menutup yang di bawahnya:

| Lapisan | Menutup |
|---|---|
| `JawabanTervalidasi` hanya dibentuk validator | jalur pintas dari keluaran model |
| `susun()` hanya menerima tipe itu | jalur pintas dari `KeluaranModel` |
| Pemeriksa C-19 aturan 1 | pembentukan tipe itu di luar validator |

Menghapus salah satunya meninggalkan dua. Itu sebabnya ketiganya ada meski
masing-masing terlihat cukup sendiri.
"""

import inspect

import pytest
from src.kamus.segmen import StatusKeberlakuan
from src.rag.jawaban.susun import status_tanggapan, susun
from src.rag.jawaban.tanggapan import (
    PENAFIAN_BAKU,
    BacaanLanjutan,
    Sitasi,
    StatusDasar,
    Versi,
)
from src.rag.pengambilan.kecukupan import StatusDasar as StatusKecukupan
from src.rag.validator.keluaran import Klaim, KeluaranModel
from src.rag.validator.pemeriksaan import HasilPemeriksaan, KodePemeriksaan, Status
from src.rag.validator.validator import HasilValidasi, JawabanTervalidasi


def _jawaban(**ganti: object) -> JawabanTervalidasi:
    argumen: dict[str, object] = {
        "ringkasan_tindakan": ("Susun RKAS bersama komite sekolah.",),
        "penjelasan": "RKAS disusun bersama komite sekolah.",
        "klaim": (
            Klaim(
                id_klaim="K1",
                teks="RKAS disusun bersama komite sekolah.",
                id_segmen=("SEG-A",),
            ),
        ),
    }
    argumen.update(ganti)
    hasil = HasilValidasi(
        pemeriksaan=tuple(
            HasilPemeriksaan(kode=k, status=Status.LULUS, alasan="lulus")
            for k in KodePemeriksaan
        )
    )
    return JawabanTervalidasi(keluaran=KeluaranModel(**argumen), hasil=hasil)  # type: ignore[arg-type]


def _versi() -> Versi:
    return Versi(model="tiruan-1", indeks="leksikal-7", kode="abc1234")


def _sitasi(status: StatusKeberlakuan = StatusKeberlakuan.BERLAKU) -> Sitasi:
    return Sitasi(
        id_dokumen="DOC-1",
        judul="Permendikdasmen Nomor 1 Tahun 2026",
        penerbit="Kemendikdasmen",
        tahun=2026,
        bagian="Pasal 7 ayat (2)",
        status_keberlakuan=status,
    )


# ------------------------------------------------------------------------ R-10


def test_susun_hanya_menerima_jawaban_tervalidasi() -> None:
    """**R-10.** Tanda tangan menuntut `JawabanTervalidasi`, dan tipe itu hanya
    dapat dibentuk validator.

    Diperiksa pada anotasinya, bukan dengan memanggil `susun()` dengan objek
    keliru: Python tidak memeriksa tipe saat jalan, sehingga uji semacam itu
    hanya membuktikan pydantic menolak bidangnya — bukan bahwa kontraknya
    benar.
    """
    tanda = inspect.signature(susun)
    assert tanda.parameters["jawaban"].annotation == "JawabanTervalidasi"


def test_susun_tidak_menyebut_keluaran_model_pada_tanda_tangannya() -> None:
    """Sisi lain: `KeluaranModel` tidak boleh menjadi jalan masuk.

    Menambahkannya sebagai parameter alternatif akan melewati validator tanpa
    satu uji perilaku pun gagal.
    """
    sumber = inspect.getsource(susun)
    kepala = sumber.split('"""')[0]
    assert "KeluaranModel" not in kepala


def test_tanggapan_membawa_isi_keluaran_yang_tervalidasi() -> None:
    tanggapan = susun(
        _jawaban(),
        id_pesan="msg_1",
        versi=_versi(),
        status=StatusKecukupan.TERBATAS,
        sitasi=(_sitasi(),),
    )
    assert tanggapan.status_dasar is StatusDasar.TERBATAS
    assert tanggapan.klaim[0].teks == "RKAS disusun bersama komite sekolah."
    assert tanggapan.klaim[0].id_segmen == ("SEG-A",)
    assert tanggapan.penafian == PENAFIAN_BAKU


# ------------------------------------------------------------- pemetaan status


@pytest.mark.parametrize(
    ("kecukupan", "tampil"),
    [
        (StatusKecukupan.KUAT, StatusDasar.KUAT),
        (StatusKecukupan.TERBATAS, StatusDasar.TERBATAS),
        (StatusKecukupan.TIDAK_DITEMUKAN, StatusDasar.TIDAK_DITEMUKAN),
        (StatusKecukupan.DI_LUAR_DOMAIN, StatusDasar.DI_LUAR_DOMAIN),
    ],
)
def test_keempat_status_terpetakan(
    kecukupan: StatusKecukupan, tampil: StatusDasar
) -> None:
    assert status_tanggapan(kecukupan) is tampil


def test_setiap_nilai_kecukupan_punya_pemetaan() -> None:
    """Sifat, bukan kasus. Nilai kelima yang D-14 tambahkan kelak wajib
    diputuskan pemetaannya."""
    for nilai in StatusKecukupan:
        assert status_tanggapan(nilai) is not None


def test_pemetaan_tidak_memakai_cabang_else() -> None:
    """**Nilai yang belum dipetakan wajib berisik.**

    Cabang `else` yang mengembalikan `TIDAK_DITEMUKAN` akan membuat nilai baru
    berakhir sebagai penolakan tanpa seorang pun memutuskannya — dan penolakan
    yang tidak diputuskan siapa pun terbaca sama persis dengan penolakan yang
    benar.
    """
    import src.rag.jawaban.susun as modul

    with pytest.raises(KeyError):
        modul._PETA_STATUS[object()]  # type: ignore[index]


# ------------------------------------------------------------------ R-11, R-12


def test_ringkasan_melampaui_dua_puluh_kata_ditolak_saat_disusun() -> None:
    """Ditegakkan `Tanggapan`, dan diuji dari sini agar kegagalannya terbaca
    pada jalur yang benar-benar dipakai."""
    from pydantic import ValidationError

    panjang = " ".join(["kata"] * 21) + "."
    with pytest.raises(ValidationError):
        susun(
            _jawaban(ringkasan_tindakan=(panjang,)),
            id_pesan="msg_1",
            versi=_versi(),
            status=StatusKecukupan.TERBATAS,
            sitasi=(_sitasi(),),
        )


def test_penyusun_tidak_menulis_dan_tidak_memanggil_model() -> None:
    """**R-12, C-17, C-08.**"""
    import ast

    import src.rag.jawaban.susun as modul

    sumber = inspect.getsource(modul)
    pohon = ast.parse(sumber)
    dipanggil = {
        s.func.attr
        for s in ast.walk(pohon)
        if isinstance(s, ast.Call) and isinstance(s.func, ast.Attribute)
    }
    assert not (dipanggil & {"write_text", "write_bytes", "mkdir", "unlink", "open"})
    assert "src.llm" not in sumber


def test_sitasi_dan_bacaan_lanjutan_diserahkan_pemanggil() -> None:
    """Keduanya menuntut metadata dokumen yang tinggal pada `src/ingest/`, dan
    `AGENTS.md` tidak memberi `rag` tepi ke sana.

    Menyimpulkannya di sini akan menciptakan tepi tanpa keputusan gerbang — dan
    pemeriksa arah fitur 009 menolaknya. Bentuk yang sama dengan `segmen_resmi`
    fitur 007.
    """
    sumber = inspect.getsource(susun)
    assert "src.ingest" not in sumber
    tanda = inspect.signature(susun)
    assert "sitasi" in tanda.parameters
    assert "bacaan_lanjutan" in tanda.parameters


def test_bacaan_lanjutan_diteruskan_apa_adanya() -> None:
    bacaan = BacaanLanjutan(judul="Artikel jurnal", tautan="https://jurnal.contoh/x")
    tanggapan = susun(
        _jawaban(),
        id_pesan="msg_1",
        versi=_versi(),
        status=StatusKecukupan.TERBATAS,
        sitasi=(_sitasi(),),
        bacaan_lanjutan=(bacaan,),
    )
    assert tanggapan.bacaan_lanjutan == (bacaan,)
    assert all(not isinstance(s, BacaanLanjutan) for s in tanggapan.sitasi)
