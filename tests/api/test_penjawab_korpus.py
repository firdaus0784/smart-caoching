"""Muatan dan penjawab korpus — T-6 fitur 039, R-01 s.d. R-08; K-5, K-6.

Bagian pertama murni: kelayakan baris dan muatan, tanpa basis data. Bagian
kedua merakit `PenjawabKorpus` atas PostgreSQL dengan peran sungguhan; ambang,
penyemat, dan model di sana tiruan yang menyatakan dirinya — yang sungguhan
menunggu BT-29 dan ADR-12, dan tidak dibuat di mana pun (C-16).

Teks dan metadata contoh dibuat-buat.
"""

from __future__ import annotations

import json
import secrets
from datetime import date
from pathlib import Path

import pytest
from src.api.penjawab_korpus import (
    AlasanTakLayak,
    PenjawabKorpus,
    SumberLayak,
    alasan_tak_layak,
    bangun_muatan,
    pilih_bacaan_lanjutan,
)
from src.kamus.segmen import IndeksTujuan, Peringkat, StatusKeberlakuan
from src.llm.pembungkus import Pembungkus
from src.llm.sematan import PenyematTiruan
from src.llm.tipe import Konfigurasi
from src.logbook.versi import Versi as VersiLogbook
from src.penyimpanan.dasar import MetadataDokumen
from src.penyimpanan.indeks import SegmenTerindeks, StatusLisensi
from src.penyimpanan.korpus_penjawab import (
    BarisKorpus,
    MuatanKorpus,
    PemuatKorpus,
    PemuatKorpusPostgres,
)
from src.penyimpanan.kredensial import Kredensial
from src.penyimpanan.skema_indeks import SKEMA_INDEKS
from src.rag.jawaban.tanggapan import BacaanLanjutan
from src.rag.pengambilan.bm25 import SumberBM25, bangun_indeks
from src.rag.pengambilan.kecukupan import AmbangKecukupan, CatatanKalibrasi
from src.rag.pengambilan.peringkat_ulang import PemeringkatTidakTersedia
from src.rag.pengambilan.tetapan import JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM
from tests.api.test_tanya import AdaptorTerhitung, pemeriksaan_model_lulus
from tests.konftes_asinkron import jalankan
from tests.peladen import DIMENSI_UJI, psql, siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

UTAMA, METADATA = IndeksTujuan.UTAMA, IndeksTujuan.METADATA


def _metadata(**ubah: object) -> MetadataDokumen:
    bidang: dict[str, object] = {
        "judul": "Peraturan Contoh Nomor 1 Tahun 2026",
        "jenis": "regulasi_resmi",
        "penerbit": "Kementerian Contoh",
        "tahun": 2026,
        "tingkat_kerahasiaan": "publik",
        "lisensi": "CC BY 4.0",
        "tautan": "https://jdih.contoh.go.id/p/1",
    }
    bidang.update(ubah)
    return MetadataDokumen(**bidang)  # type: ignore[arg-type]


def _baris(id_segmen: str = "d1:0001", **ubah: object) -> BarisKorpus:
    bidang: dict[str, object] = {
        "id_segmen": id_segmen,
        "id_dokumen": id_segmen.split(":")[0],
        "teks": "Kepala sekolah menyusun rencana kerja tahunan.",
        "penanda_bagian": "Pasal 1",
        "lisensi_segmen": "terbuka",
        "anonimisasi_terverifikasi": True,
        "metadata": _metadata(),
        "status": "berlaku",
        "rujukan_pengganti": None,
    }
    bidang.update(ubah)
    return BarisKorpus(**bidang)  # type: ignore[arg-type]


# ── kelayakan ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("ubah", "alasan"),
    [
        ({"metadata": None}, AlasanTakLayak.TANPA_METADATA),
        ({"metadata": _metadata(jenis="buku")}, AlasanTakLayak.TANPA_METADATA),
        (
            {"metadata": _metadata(tingkat_kerahasiaan="internal_sekolah")},
            AlasanTakLayak.TIDAK_PUBLIK,
        ),
        ({"metadata": _metadata(jenis="dokumen_sekolah")}, AlasanTakLayak.TIDAK_PUBLIK),
        ({"metadata": _metadata(lisensi="CC-BY-NC 4.0")}, AlasanTakLayak.LISENSI_TERTUTUP),
        ({"metadata": _metadata(lisensi=None)}, AlasanTakLayak.LISENSI_TERTUTUP),
        ({"anonimisasi_terverifikasi": False}, AlasanTakLayak.BELUM_TERVERIFIKASI),
        ({"status": None}, AlasanTakLayak.REGULASI_TANPA_STATUS),
        ({"status": "dicabut"}, AlasanTakLayak.DICABUT),
        (
            {"metadata": _metadata(tingkat_kerahasiaan="internal_sekolah"), "status": "dicabut"},
            AlasanTakLayak.TIDAK_PUBLIK,
        ),
    ],
)
def test_alasan_tak_layak_berurutan(ubah: dict[str, object], alasan: AlasanTakLayak) -> None:
    """K-5: yang pertama berlaku menjadi alasannya. M-3, M-4, M-5, M-6."""
    assert alasan_tak_layak(_baris(**ubah), UTAMA) is alasan


def test_baris_yang_layak() -> None:
    assert alasan_tak_layak(_baris(), UTAMA) is None
    assert alasan_tak_layak(_baris(status="diubah"), UTAMA) is None


def test_lisensi_dibaca_ulang_hanya_pada_indeks_utama() -> None:
    """Lapis kedua TK-87: segmen indeks metadata memang tertutup."""
    tertutup = _baris(metadata=_metadata(lisensi="CC-BY-NC-ND 4.0"), lisensi_segmen="tertutup")
    assert alasan_tak_layak(tertutup, UTAMA) is AlasanTakLayak.LISENSI_TERTUTUP
    assert alasan_tak_layak(tertutup, METADATA) is None


def test_bukan_regulasi_tanpa_status_layak() -> None:
    """P-3 A: keberlakuan hanya bermakna bagi regulasi."""
    artikel = _baris(metadata=_metadata(jenis="artikel_lisensi_terbuka"), status=None)
    assert alasan_tak_layak(artikel, UTAMA) is None


# ── muatan ───────────────────────────────────────────────────────────


def _muatan(baris_utama: list[BarisKorpus], baris_metadata: list[BarisKorpus]):  # type: ignore[no-untyped-def]
    return bangun_muatan(
        MuatanKorpus(sidik="sidik-u", baris=tuple(baris_utama)),
        MuatanKorpus(sidik="sidik-m", baris=tuple(baris_metadata)),
    )


def test_bahan_hanya_segmen_utama_yang_layak_dengan_peringkat_dan_keberlakuan() -> None:
    """R-02, R-03: peringkat dari jenis lewat `peringkat_bagi`; keberlakuan
    dari catatan status; bukan regulasi tanpa status berlaku."""
    muatan = _muatan(
        [
            _baris("reg:0001", status="diubah", rujukan_pengganti="Peraturan Nomor 3"),
            _baris(
                "art:0001",
                metadata=_metadata(jenis="artikel_lisensi_terbuka", tautan=None),
                status=None,
            ),
            _baris("cbt:0001", status="dicabut"),
            _baris("skl:0001", metadata=_metadata(jenis="dokumen_sekolah")),
        ],
        [],
    )
    assert set(muatan.bahan) == {"reg:0001", "art:0001"}
    reg, art = muatan.bahan["reg:0001"].rujukan, muatan.bahan["art:0001"].rujukan
    assert (reg.peringkat_kepercayaan, reg.status_keberlakuan) == (
        Peringkat.T1,
        StatusKeberlakuan.DIUBAH,
    )
    assert (art.peringkat_kepercayaan, art.status_keberlakuan) == (
        Peringkat.T2,
        StatusKeberlakuan.BERLAKU,
    )
    assert reg.indeks_asal is UTAMA and reg.tautan == "https://jdih.contoh.go.id/p/1"
    assert muatan.segmen_resmi == frozenset({"reg:0001"})
    assert muatan.layak_utama == frozenset({"reg:0001", "art:0001"})


def test_sitasi_per_segmen_dari_catatan_korpus() -> None:
    muatan = _muatan([_baris("reg:0002", status="diubah", rujukan_pengganti="Nomor 3")], [])
    sitasi = muatan.sitasi["reg:0002"]
    assert (sitasi.id_dokumen, sitasi.judul, sitasi.penerbit, sitasi.tahun, sitasi.bagian) == (
        "reg",
        "Peraturan Contoh Nomor 1 Tahun 2026",
        "Kementerian Contoh",
        2026,
        "Pasal 1",
    )
    assert (sitasi.status_keberlakuan, sitasi.rujukan_pengganti, sitasi.tautan) == (
        StatusKeberlakuan.DIUBAH,
        "Nomor 3",
        "https://jdih.contoh.go.id/p/1",
    )


def test_bacaan_lanjutan_hanya_dokumen_metadata_bertautan() -> None:
    """KL-04, D-14 Bagian 4.1: tanpa tautan tidak menjadi bacaan lanjutan."""
    muatan = _muatan(
        [],
        [
            _baris("tt1:0001", metadata=_metadata(lisensi=None), lisensi_segmen="tertutup"),
            _baris(
                "tt2:0001",
                metadata=_metadata(lisensi=None, tautan=None),
                lisensi_segmen="tertutup",
            ),
        ],
    )
    assert muatan.bacaan == {
        "tt1:0001": (
            "tt1",
            BacaanLanjutan(
                judul="Peraturan Contoh Nomor 1 Tahun 2026", tautan="https://jdih.contoh.go.id/p/1"
            ),
        )
    }
    assert muatan.bahan == {}


def test_tak_layak_dihitung_dan_dokumen_perlu_indeks_ulang() -> None:
    """Alasan dihitung, tidak dibuang; dokumen utama yang lisensinya kini
    tertutup tercatat untuk diindeks ulang (TK-87)."""
    muatan = _muatan(
        [
            _baris("nc:0001", metadata=_metadata(lisensi="CC-BY-NC 4.0")),
            _baris("nc:0002", metadata=_metadata(lisensi="CC-BY-NC 4.0")),
            _baris("cb:0001", status="dicabut"),
        ],
        [
            _baris(
                "ts:0001", status=None, lisensi_segmen="tertutup", metadata=_metadata(lisensi=None)
            )
        ],
    )
    assert muatan.tak_layak[UTAMA] == {
        AlasanTakLayak.LISENSI_TERTUTUP: 2,
        AlasanTakLayak.DICABUT: 1,
    }
    assert muatan.tak_layak[METADATA] == {AlasanTakLayak.REGULASI_TANPA_STATUS: 1}
    assert muatan.perlu_indeks_ulang == frozenset({"nc"})


def test_bacaan_lanjutan_unik_per_dokumen_dan_terbatas() -> None:
    """D-14 Bagian 4.1: unik per dokumen menurut peringkat, paling banyak
    sejumlah segmen yang diteruskan (D-07 Bagian 9)."""
    baris = [
        _baris(
            f"m{i:02d}:000{j}",
            teks="Kajian rencana kerja sekolah dasar." + " rencana" * (12 - i),
            metadata=_metadata(
                lisensi=None, judul=f"Kajian {i:02d}", tautan=f"https://contoh.id/{i}"
            ),
            lisensi_segmen="tertutup",
        )
        for i in range(12)
        for j in (1, 2)
    ]
    muatan = _muatan([], baris)
    bacaan = jalankan(pilih_bacaan_lanjutan("rencana kerja", muatan))
    assert len(bacaan) == JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM
    assert len({b.judul for b in bacaan}) == len(bacaan)
    assert bacaan[0].judul == "Kajian 00"


def test_sumber_layak_membatasi_kandidat_tanpa_mengubah_identitasnya() -> None:
    """Sisi vektor tidak mengetahui catatan korpus; kandidat tak layak tidak
    sampai ke penggabungan, dan nama serta versinya tetap milik sumbernya."""
    muatan = _muatan([_baris("a:0001"), _baris("b:0001", status="dicabut")], [])
    semua = SumberBM25(
        bangun_indeks(
            [
                SegmenTerindeks(
                    id_segmen=i,
                    id_dokumen=i.split(":")[0],
                    teks="Kepala sekolah menyusun rencana kerja tahunan.",
                    lisensi=StatusLisensi.TERBUKA,
                    indeks_tujuan=UTAMA,
                    anonimisasi_terverifikasi=True,
                    penanda_bagian="Pasal 1",
                )
                for i in ("a:0001", "b:0001")
            ],
            versi="uji",
            indeks_tujuan=UTAMA,
        )
    )
    terbatas = SumberLayak(semua, muatan.layak_utama)
    hasil = jalankan(terbatas.cari("rencana kerja", batas=20))
    assert [k.id_segmen for k in hasil.peringkat] == ["a:0001"]
    assert (terbatas.nama, terbatas.indeks_tujuan, terbatas.versi_indeks) == (
        semua.nama,
        UTAMA,
        "uji",
    )


def test_versi_indeks_menyebut_kedua_sidik() -> None:
    """R-06, RT-05: bacaan lanjutan berasal dari indeks metadata, sehingga
    versinya ikut."""
    assert _muatan([], []).versi_indeks.startswith("utama:sidik-u;metadata:sidik-m;")


# ── PenjawabKorpus atas PostgreSQL ───────────────────────────────────


class PemuatTerhitung(PemuatKorpus):
    """Menghitung pemuatan penuh — penggantian muatan hanya terlihat dari sini."""

    def __init__(self, dasar: PemuatKorpus) -> None:
        self._dasar = dasar
        self.jumlah_muat = 0

    async def muat(self, kredensial: Kredensial, indeks: IndeksTujuan) -> MuatanKorpus:
        self.jumlah_muat += 1
        return await self._dasar.muat(kredensial, indeks)

    async def sidik(self, kredensial: Kredensial, indeks: IndeksTujuan) -> str:
        return await self._dasar.sidik(kredensial, indeks)


def _sql(nilai: object) -> str:
    return "null" if nilai is None else "'" + str(nilai).replace("'", "''") + "'"


def _pengelola(kueri: str) -> None:
    hasil = psql("smart_coaching", "-v", "ON_ERROR_STOP=1", "-c", kueri)
    assert hasil.returncode == 0, hasil.stderr


def _tanam(
    id_dokumen: str,
    indeks: IndeksTujuan,
    teks: str,
    *,
    status: str | None = "berlaku",
    **metadata: object,
) -> str:
    m = _metadata(**metadata)
    _pengelola(
        f"insert into korpus.dokumen_sumber (id, isi) values ({_sql(id_dokumen)}, "
        f"{_sql(json.dumps(teks))}::jsonb); "
        "insert into korpus.metadata_dokumen (id_dokumen, judul, jenis, penerbit, tahun, "
        "tingkat_kerahasiaan, lisensi, tautan) values ("
        + ", ".join(
            _sql(v)
            for v in (
                id_dokumen,
                m.judul,
                m.jenis,
                m.penerbit,
                m.tahun,
                m.tingkat_kerahasiaan,
                m.lisensi,
                m.tautan,
            )
        )
        + "); "
        + (
            ""
            if status is None
            else "insert into korpus.status_dokumen (id_dokumen, status) "
            f"values ({_sql(id_dokumen)}, {_sql(status)}); "
        )
        + f"insert into {SKEMA_INDEKS[indeks]}.segmen_teks (id_segmen, id_dokumen, teks, "
        "lisensi, anonimisasi_terverifikasi, penanda_bagian) values ("
        f"{_sql(id_dokumen + ':0001')}, {_sql(id_dokumen)}, {_sql(teks)}, "
        f"{_sql('terbuka' if indeks is UTAMA else 'tertutup')}, true, 'Pasal 1')"
    )
    return f"{id_dokumen}:0001"


def _kata_unik() -> str:
    """Kata yang tidak dimuat segmen lain pada peladen bersama, dan tidak
    berimbuhan sehingga pemotong imbuhan tidak mengubahnya."""
    return "zq" + "".join(secrets.choice("bcdfghjklmnpqrstvwz") for _ in range(8)) + "x"


def _keluaran(id_segmen: str) -> str:
    return json.dumps(
        {
            "ringkasan_tindakan": ["Susun rencana kerja tahunan bersama guru."],
            "penjelasan": "Rencana kerja disusun kepala sekolah.",
            "klaim": [
                {
                    "id_klaim": "K1",
                    "teks": "Kepala sekolah menyusun rencana.",
                    "id_segmen": [id_segmen],
                }
            ],
            "catatan_keberlakuan": "",
        }
    )


def _penjawab(
    tmp_path: Path, adaptor: AdaptorTerhitung
) -> tuple[PenjawabKorpus, PemuatTerhitung, PemuatTerhitung]:
    konteks = PemuatTerhitung(PemuatKorpusPostgres(SambunganPeran("peran_pemanggil_llm")))  # type: ignore[arg-type]
    metadata = PemuatTerhitung(PemuatKorpusPostgres(SambunganPeran("peran_penjawaban")))  # type: ignore[arg-type]
    penjawab = PenjawabKorpus(
        pemuat_konteks=konteks,
        pemuat_metadata=metadata,
        sambungan_vektor=SambunganPeran("peran_pemanggil_llm"),  # type: ignore[arg-type]
        penyemat=PenyematTiruan(dimensi=DIMENSI_UJI),
        pemeringkat=PemeringkatTidakTersedia(),
        ambang=AmbangKecukupan(
            # Ambang uji atas RRF satu sumber pada peringkat pertama (1/61):
            # sisi vektor tidak menemukan apa pun karena segmen uji belum
            # disematkan. Kalibrasi sungguhan mengikuti BT-29.
            menengah=0.01,
            tinggi=0.015,
            kalibrasi=CatatanKalibrasi(
                tanggal=date(2026, 10, 13),
                gold_set="uji-039-v1",
                jumlah_pertanyaan=1,
                pemutus="uji",
                prosedur="Ambang uji; kalibrasi sungguhan mengikuti BT-29.",
            ),
        ),
        pembungkus=Pembungkus(
            adaptor,
            tmp_path,
            VersiLogbook(
                versi_kode="uji",
                versi_model="tiruan-1",
                versi_indeks="uji-039",
                versi_skema_anotasi="belum-berlaku",
                pembagian_data="belum-berlaku",
            ),
        ),
        konfigurasi=Konfigurasi(
            nama_model="tiruan", versi_model="tiruan-1", suhu=0.0, batas_token=512
        ),
        versi_model="tiruan-1",
        versi_kode="uji",
    )
    return penjawab, konteks, metadata


def test_penjawab_korpus_atas_postgresql(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R-01 s.d. R-07 sekaligus, atas peladen dengan peran sungguhan:

    - hanya segmen utama yang layak sampai ke model — regulasi tanpa status,
      dicabut, dokumen sekolah, dan berlisensi kini tertutup tidak (C-02, C-07,
      P-3, P-4, TK-87);
    - sitasi dari klaim membawa tautan; bacaan lanjutan dari indeks metadata
      hanya yang bertautan (KL-04);
    - versi indeks tercatat; muatan dipakai ulang selama sidik sama dan diganti
      ketika status berubah (R-06).
    """
    pemeriksaan_model_lulus(monkeypatch)
    kata = _kata_unik()
    awal = "d39-" + secrets.token_hex(3)
    teks = f"Kepala sekolah menyusun {kata} rencana kerja tahunan."
    layak = _tanam(f"{awal}-a", UTAMA, teks, tautan="https://jdih.contoh.go.id/a")
    tak_layak = [
        _tanam(f"{awal}-b", UTAMA, teks, status=None),
        _tanam(f"{awal}-c", UTAMA, teks, status="dicabut"),
        _tanam(f"{awal}-s", UTAMA, teks, jenis="dokumen_sekolah"),
        _tanam(f"{awal}-n", UTAMA, teks, lisensi="CC-BY-NC 4.0"),
    ]
    _tanam(
        f"{awal}-m",
        METADATA,
        teks,
        lisensi=None,
        judul="Kajian Rencana Kerja",
        tautan="https://contoh.id/m",
    )
    _tanam(f"{awal}-k", METADATA, teks, lisensi=None, tautan=None)

    adaptor = AdaptorTerhitung(_keluaran(layak))
    penjawab, konteks, metadata = _penjawab(tmp_path, adaptor)
    # Hanya kata unik: kata umum mencocokkan dokumen putaran uji sebelumnya
    # pada peladen bersama.
    pertanyaan = kata

    hasil = jalankan(penjawab.jawab(pertanyaan))
    assert hasil.alasan_berhenti is None, hasil.alasan_berhenti
    assert adaptor.terakhir is not None
    terkirim = {d.id_segmen for d in adaptor.terakhir.data}
    assert layak in terkirim
    assert not terkirim & set(tak_layak), terkirim
    assert [(s.id_dokumen, s.tautan) for s in hasil.tanggapan.sitasi] == [
        (f"{awal}-a", "https://jdih.contoh.go.id/a")
    ]
    assert list(hasil.tanggapan.bacaan_lanjutan) == [
        BacaanLanjutan(judul="Kajian Rencana Kerja", tautan="https://contoh.id/m")
    ]
    versi = hasil.tanggapan.versi.indeks
    assert versi.startswith("utama:") and ";metadata:" in versi
    assert hasil.tanggapan.id_pesan.startswith("msg_")

    jalankan(penjawab.jawab(pertanyaan))
    assert (konteks.jumlah_muat, metadata.jumlah_muat) == (1, 1), "sidik sama: muatan dipakai ulang"

    _pengelola(
        f"insert into korpus.status_dokumen (id_dokumen, status) values ('{awal}-a', 'dicabut')"
    )
    terakhir = jalankan(penjawab.jawab(pertanyaan))
    assert konteks.jumlah_muat == 2, "status berubah: muatan diganti"
    assert terakhir.tanggapan.versi.indeks != versi
    assert adaptor.jumlah_kirim == 2, "regulasi yang baru dicabut tidak sampai ke model"


def test_pertanyaan_di_luar_domain_tidak_mencari_bacaan_lanjutan(tmp_path: Path) -> None:
    """R-07 fitur 021: tahap 1 sebelum pengambilan — termasuk pencarian bacaan
    lanjutan atas indeks metadata."""
    adaptor = AdaptorTerhitung(_keluaran("tidak-dipakai"))
    penjawab, _, _ = _penjawab(tmp_path, adaptor)
    hasil = jalankan(penjawab.jawab("Saya pasien rumah sakit, obat apa yang cocok bagi saya?"))
    assert hasil.tanggapan.bacaan_lanjutan == ()
    assert adaptor.jumlah_kirim == 0
