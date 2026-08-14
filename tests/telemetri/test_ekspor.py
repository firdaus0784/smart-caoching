"""Uji ekspor telemetri — C-1 fitur 012, R-03, R-08, FR-J03.

Berkas ekspor **berpindah tangan** — ke R, ke Python, ke lampiran surel. Ia
tempat paling mungkin data pribadi keluar dari sistem, dan justru di sana
pemeriksaan paling mudah terlupa.
"""

import csv
import json
from datetime import UTC, datetime
from io import StringIO

from src.pengguna.persetujuan import KeadaanPersetujuan
from src.telemetri.ekspor import KOLOM, ke_csv, parquet_tertahan
from src.telemetri.gerbang import rekam
from src.telemetri.peristiwa import JenisPeristiwa, Peristiwa

WAKTU = datetime(2026, 8, 13, 4, 0, tzinfo=UTC)


def _peristiwa(**ganti: object) -> Peristiwa:
    argumen: dict[str, object] = {
        "keadaan": KeadaanPersetujuan.DIBERIKAN,
        "pseudonim": "PSD-a1",
        "jenis": JenisPeristiwa.QUESTION_ASKED,
        "waktu": WAKTU,
        "properti": {"kategori": "K3", "panjang_teks": 42},
        "versi_aplikasi": "0.12.0",
        "versi_model": "tiruan-0",
    }
    argumen.update(ganti)
    _, peristiwa = rekam(**argumen)  # type: ignore[arg-type]
    assert peristiwa is not None
    return peristiwa


def _baca(teks: str) -> list[dict[str, str]]:
    return list(csv.DictReader(StringIO(teks)))


# ------------------------------------------------------------ R-03 · identitas


def test_kolom_tidak_memuat_identitas() -> None:
    """**Uji terpenting berkas ini.** Berkas ekspor berpindah tangan."""
    for terlarang in ("id_pengguna", "nama", "surel", "email"):
        assert terlarang not in KOLOM


def test_kolom_diturunkan_dari_model_bukan_ditulis_ulang() -> None:
    """Daftar yang ditulis ulang dapat menambah kolom yang modelnya tidak
    punya — dan kolom yang paling mungkin ditambahkan seseorang adalah
    `id_pengguna`, sebab analisis terasa lebih mudah dengannya."""
    assert tuple(Peristiwa.model_fields) == KOLOM


def test_kepala_csv_sama_dengan_kolom() -> None:
    kepala = ke_csv([]).strip().split(",")
    assert tuple(kepala) == KOLOM


# ------------------------------------------------------------- R-08 · isi CSV


def test_baris_memuat_keenam_bidang() -> None:
    (baris,) = _baca(ke_csv([_peristiwa()]))
    assert baris["pseudonim"] == "PSD-a1"
    assert baris["jenis"] == "question_asked"
    assert baris["versi_aplikasi"] == "0.12.0"
    assert baris["versi_model"] == "tiruan-0"


def test_waktu_ditulis_berzona() -> None:
    """KM-01. Analisis di R yang membaca waktu tanpa zona akan menafsirkannya
    sebagai waktu setempat mesin pembaca — dan retensi D1/D7/D30 bergeser
    sebanyak selisih zonanya."""
    (baris,) = _baca(ke_csv([_peristiwa()]))
    assert baris["waktu"] == WAKTU.isoformat()
    assert "+00:00" in baris["waktu"]


def test_properti_ditulis_sebagai_json_satu_kolom() -> None:
    """Memekarkannya menjadi kolom-kolom akan membuat lebar berkas bergantung
    pada peristiwa mana yang kebetulan terekam, dan dua ekspor dari dua pekan
    tidak dapat ditumpuk."""
    (baris,) = _baca(ke_csv([_peristiwa()]))
    assert json.loads(baris["properti"]) == {"kategori": "K3", "panjang_teks": 42}


def test_properti_berkunci_terurut() -> None:
    """Urutan kunci yang berubah antarjalan membuat dua ekspor dari data yang
    sama menghasilkan berkas yang berbeda — dan selisih berkas berhenti
    menandakan selisih data."""
    satu = ke_csv([_peristiwa(properti={"b": 1, "a": 2})])
    dua = ke_csv([_peristiwa(properti={"a": 2, "b": 1})])
    assert satu == dua


def test_ekspor_kosong_tetap_berkepala() -> None:
    """Berkas tanpa kepala tidak dapat dibaca `read.csv` maupun `pandas` tanpa
    keterangan tambahan, dan ekspor nol peristiwa adalah keadaan yang wajar
    pada pekan pertama."""
    assert ke_csv([]).strip() == ",".join(KOLOM)


def test_beberapa_peristiwa_berurutan() -> None:
    baris = _baca(ke_csv([_peristiwa(), _peristiwa(jenis=JenisPeristiwa.ANSWER_SERVED)]))
    assert [b["jenis"] for b in baris] == ["question_asked", "answer_served"]


def test_properti_bertanda_kutip_tidak_merusak_kolom() -> None:
    """CSV yang tidak melarikan tanda kutip menggeser seluruh kolom sesudahnya,
    dan `versi_model` terbaca sebagai potongan properti."""
    (baris,) = _baca(_kutip())
    assert baris["versi_model"] == "tiruan-0"


def _kutip() -> str:
    return ke_csv([_peristiwa(properti={"catatan": 'ada "kutip", dan koma'})])


# ------------------------------------------- Parquet dinyatakan, bukan hilang


def test_parquet_dinyatakan_tertahan_bukan_diam() -> None:
    """Fungsi yang tidak ada terbaca sebagai fitur yang tidak pernah diminta;
    alasan yang dapat dipanggil terbaca sebagai utang yang dapat ditagih."""
    alasan = parquet_tertahan()
    assert "pyarrow" in alasan
    assert "C-12" in alasan


def test_tidak_ada_ekspor_parquet_yang_berpura_pura() -> None:
    """Ekspor Parquet yang sebenarnya menulis CSV berganti nama adalah bentuk
    laporan bersih yang tidak memeriksa apa pun (TA-01) pada lapisan ekspor."""
    from src.telemetri import ekspor

    menyebut_parquet = {n for n in dir(ekspor) if "parquet" in n.lower()}
    assert menyebut_parquet == {"ALASAN_PARQUET_TERTAHAN", "parquet_tertahan"}, (
        "permukaan modul memuat nama parquet di luar pernyataan tertahannya: "
        f"{sorted(menyebut_parquet - {'ALASAN_PARQUET_TERTAHAN', 'parquet_tertahan'})}"
    )
