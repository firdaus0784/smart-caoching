"""Uji ekspor ontologi — B-2 fitur 005, R-08 s.d. R-10, FR-E05.

Berkas yang dihasilkan **dilampirkan pada pendaftaran HKI dan naskah
publikasi**. Yang membacanya tidak punya akses ke `docs/`, tidak dapat
bertanya, dan tidak ada di ruangan.

Dua hal yang lebih mudah luput daripada bentuk JSON-LD-nya:

1. **Hanya yang sah diekspor.** Konsep tanpa definisi tidak terhitung pada
   MK-06; mengekspornya membuat berkas memuat lebih banyak simpul daripada
   angka yang dilaporkan naskah. Selisih itu pertanyaan pertama penelaah.

2. **Ontologi kosong ditolak.** Berkas berisi nol simpul terbaca seperti
   ekspor yang berjalan dan tidak menemukan apa-apa — tidak dapat dibedakan
   dari ekspor yang gagal diam.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from src.rag.ontologi.ekspor import GalatEksporOntologi, ekspor_jsonld, ringkas, tulis
from src.rag.ontologi.jejak import catat_ekspor
from src.rag.ontologi.skema import JenisRelasi, Konsep, Ontologi, Relasi

DOK = frozenset({"DOC-001"})


def _konsep(id_konsep: str, definisi: str = "Definisi terisi.", terkurasi: bool = True) -> Konsep:
    return Konsep(
        id_konsep=id_konsep,
        label=f"Label {id_konsep}",
        definisi=definisi,
        id_dokumen_rujukan=DOK,
        sumber_terkurasi=terkurasi,
    )


def _onto(**ganti: Any) -> Ontologi:
    konsep = ganti.get("konsep", (_konsep("K1"), _konsep("K2")))
    relasi = ganti.get(
        "relasi",
        (
            Relasi(
                id_relasi="R1",
                konsep_asal="K1",
                konsep_tujuan="K2",
                jenis=JenisRelasi.MENGATUR,
                id_dokumen_rujukan=DOK,
            ),
        ),
    )
    return Ontologi(konsep=konsep, relasi=relasi)


def _muat(**ganti: Any) -> dict[str, Any]:
    hasil: dict[str, Any] = json.loads(ekspor_jsonld(_onto(**ganti), versi="0.1"))
    return hasil


def test_hasil_dapat_diurai_sebagai_json() -> None:
    assert _muat()["versi"] == "0.1"


def test_konteks_menamai_ketujuh_jenis_relasi() -> None:
    """**R-08.** Ekspor yang menamai relasi dengan untai bebas menuntut
    pembacanya menebak artinya — dan pembacanya tidak dapat bertanya."""
    konteks = _muat()["@context"]
    for jenis in JenisRelasi:
        assert jenis.value in konteks, jenis.value


def test_konteks_disusun_dari_enum_bukan_ditulis_tangan() -> None:
    """Daftar yang ditulis tangan akan berbeda dari enumnya ketika FR-E02
    berubah, dan yang berbeda adalah yang tidak diperbarui."""
    konteks = _muat()["@context"]
    istilah_relasi = {k for k in konteks if k in {j.value for j in JenisRelasi}}
    assert len(istilah_relasi) == len(list(JenisRelasi))


def test_konsep_sah_masuk_graf() -> None:
    graf = _muat()["@graph"]
    assert len(graf) == 2
    assert {s["label"] for s in graf} == {"Label K1", "Label K2"}


def test_konsep_tanpa_definisi_tidak_masuk_ekspor() -> None:
    """**Uji yang dituntut `tasks.md`, dan inti R-09.**

    Berkas yang memuat lebih banyak simpul daripada angka yang dilaporkan
    naskah menghasilkan selisih yang tidak dapat diterangkan siapa pun.
    """
    hasil = _muat(konsep=(_konsep("K1"), _konsep("K2", definisi="")), relasi=())
    assert len(hasil["@graph"]) == 1
    assert hasil["jumlah_konsep_sah"] == 1


def test_konsep_dari_karantina_tidak_masuk_ekspor() -> None:
    """C-03 merambat sampai ke berkas yang dilampirkan naskah."""
    hasil = _muat(konsep=(_konsep("K1"), _konsep("K2", terkurasi=False)), relasi=())
    assert len(hasil["@graph"]) == 1


def test_relasi_menuju_konsep_tak_sah_tidak_masuk_ekspor() -> None:
    """Relasi yang menunjuk simpul yang tidak ada pada berkasnya menghasilkan
    graf menggantung — dan penelaah yang membukanya menemukan tautan buntu."""
    hasil = _muat(
        konsep=(_konsep("K1"), _konsep("K2", definisi="")),
        relasi=(
            Relasi(
                id_relasi="R1",
                konsep_asal="K1",
                konsep_tujuan="K2",
                jenis=JenisRelasi.MENGATUR,
                id_dokumen_rujukan=DOK,
            ),
        ),
    )
    simpul = hasil["@graph"][0]
    assert "mengatur" not in simpul


def test_relasi_sah_muncul_sebagai_sifat_simpulnya() -> None:
    graf = _muat()["@graph"]
    asal = next(s for s in graf if s["label"] == "Label K1")
    assert asal["mengatur"] == ["https://smart-coaching.upi.edu/ontologi#K2"]


def test_ontologi_tanpa_konsep_sah_ditolak() -> None:
    """**Uji kedua yang dituntut `tasks.md`.**

    Berkas berisi nol simpul tidak dapat dibedakan dari ekspor yang gagal
    diam. Bentuk yang sama dengan penolakan metrik atas nol contoh fitur 004.
    """
    with pytest.raises(GalatEksporOntologi) as galat:
        ekspor_jsonld(_onto(konsep=(_konsep("K1", definisi=""),), relasi=()), versi="0.1")
    assert "nol simpul" in str(galat.value)


def test_ontologi_kosong_ditolak() -> None:
    with pytest.raises(GalatEksporOntologi):
        ekspor_jsonld(Ontologi(konsep=(), relasi=()), versi="0.1")


def test_versi_wajib() -> None:
    """Berkas yang dilampirkan naskah tanpa versi tidak dapat dicocokkan
    dengan angka yang dilaporkan naskah itu."""
    with pytest.raises(GalatEksporOntologi):
        ekspor_jsonld(_onto(), versi="  ")


def test_jumlah_sah_tertulis_pada_berkasnya() -> None:
    """Angkanya ikut supaya pembaca berkas tidak perlu menghitung simpul
    sendiri — dan supaya selisihnya, bila ada, terbaca sebagai cacat."""
    hasil = _muat()
    assert hasil["jumlah_konsep_sah"] == len(hasil["@graph"])


def test_modul_tidak_menulis_berkas(tmp_path: Path) -> None:
    """C-17 melarang akses tulis dari `src/rag` — pelajaran fitur 016."""
    with pytest.raises(NotImplementedError) as galat:
        tulis(tmp_path / "ontologi.jsonld")
    assert "C-17" in str(galat.value)


# ---------------------------------------------------------------- R-10


def _catat(tmp: Path) -> dict[str, Any]:
    untai = ekspor_jsonld(_onto(), versi="0.1")
    sidik = "sha256:" + hashlib.sha256(untai.encode("utf-8")).hexdigest()
    catat_ekspor(tmp, ringkas(_onto()), versi="0.1", sidik=sidik)
    baris = (tmp / "L2-versi-artefak.jsonl").read_text(encoding="utf-8").splitlines()
    hasil: dict[str, Any] = json.loads(baris[-1])
    return hasil


def test_catatan_membawa_kedua_angka(tmp_path: Path) -> None:
    """**Inti R-10.**

    Naskah akan menyebut satu angka. Bila kelak seseorang membandingkannya
    dengan jumlah simpul pada berkas ekspornya, selisih yang tidak dapat
    diterangkan menjadi pertanyaan yang tidak ada yang dapat menjawab.
    """
    catatan = _catat(tmp_path)
    assert catatan["konsep_sah"] == 2
    assert catatan["konsep_mentah"] == 2
    assert catatan["relasi_sah"] == 1


def test_catatan_membawa_sidik_hasilnya(tmp_path: Path) -> None:
    """Dua ekspor berversi sama yang isinya berbeda tidak dapat dibedakan
    tanpa sidik — dan keadaan itu muncul justru ketika seseorang memperbaiki
    satu definisi tanpa menaikkan versinya."""
    assert _catat(tmp_path)["sidik"].startswith("sha256:")


def test_isi_konsep_tidak_masuk_catatan(tmp_path: Path) -> None:
    """Catatan L2 membawa angka dan versi, bukan isi."""
    assert "Label K1" not in json.dumps(_catat(tmp_path), ensure_ascii=False)
