"""Uji jurnal belajar — A-2 fitur 011, R-15, R-18; FR-H06, FR-H07, C-15.

## Yang diuji bukan bahwa jurnal dapat menampilkan

Yang diuji: jurnal **tidak meringkas** menjadi satu angka kemajuan, **tidak
menyimpulkan** status yang belum dijawab, dan **tidak memiliki** satu pun
bentuk gamifikasi.

Yang terakhir diuji di sini alih-alih dianggap aman karena justru di sinilah
lencana terasa paling wajar: jurnal sudah menghitung, sudah berurut waktu, dan
sudah menjadi milik satu orang.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.pengguna.jurnal import (
    ALASAN_PDF_TERTAHAN,
    BarisPenerapan,
    ButirDipelajari,
    Jurnal,
    PemahamanTercatat,
    pdf_tertahan,
)
from src.pengguna.komitmen import StatusPenerapan, catat_penerapan, susun_komitmen

AKAR = Path(__file__).resolve().parents[2]
SAAT = datetime(2026, 8, 16, 3, 0, tzinfo=UTC)


def _komitmen(nomor: int = 1, tenggat: date = date(2026, 9, 1)):  # type: ignore[no-untyped-def]
    return susun_komitmen(
        id_komitmen=f"KMT-{nomor}",
        id_butir=f"BTR-{nomor}",
        isyarat="Jika rapat komite sekolah berikutnya dibuka",
        tindakan="maka saya sampaikan tiga butir supervisi ini",
        tenggat=tenggat,
        dibuat=SAAT,
    )


def _jurnal_terisi() -> Jurnal:
    return Jurnal(
        dipelajari=(ButirDipelajari(id_butir="BTR-1", judul="Supervisi akademik", dibuka=SAAT),),
        dipahami=(PemahamanTercatat(id_butir="BTR-1", benar=2, jumlah_pertanyaan=3, dijawab=SAAT),),
        diterapkan=(
            BarisPenerapan(
                komitmen=_komitmen(1),
                jawaban=catat_penerapan(
                    id_komitmen="KMT-1",
                    status=StatusPenerapan.SUDAH_DITERAPKAN,
                    waktu=SAAT,
                ),
            ),
            BarisPenerapan(komitmen=_komitmen(2)),
        ),
    )


# ------------------------------------------------------ R-15 · tiga bagian


def test_ketiga_bagian_fr_h06_ada_dan_tidak_ada_yang_keempat() -> None:
    """**Uji terpenting berkas ini.**

    FR-H06 menyebut tiga: dipelajari, dipahami, diterapkan. Bidang keempat
    berupa angka kemajuan adalah papan skor yang belum diberi nama.
    """
    assert set(Jurnal.model_fields) == {"dipelajari", "dipahami", "diterapkan"}


def test_jurnal_kosong_sah() -> None:
    """Pengguna baru belum mempelajari apa pun, dan jurnal kosong bukan galat."""
    kosong = Jurnal()
    assert kosong.dipelajari == ()
    assert kosong.jumlah_menurut_status() == dict.fromkeys(StatusPenerapan, 0)


def test_ketiga_bagian_terisi_terbaca() -> None:
    jurnal = _jurnal_terisi()
    assert jurnal.dipelajari[0].judul == "Supervisi akademik"
    assert jurnal.dipahami[0].benar == 2
    assert len(jurnal.diterapkan) == 2


# ------------------------------------------ komitmen belum dijawab tidak disimpulkan


def test_komitmen_belum_dijawab_tidak_dihitung_pada_status_mana_pun() -> None:
    """Memasukkan yang belum dijawab ke `BELUM` menyamakan "belum ditanya"
    dengan "sudah ditanya dan belum dikerjakan" — dan keduanya menuntut
    tindakan yang berbeda."""
    cacah = _jurnal_terisi().jumlah_menurut_status()
    assert cacah[StatusPenerapan.SUDAH_DITERAPKAN] == 1
    assert cacah[StatusPenerapan.BELUM] == 0
    assert sum(cacah.values()) == 1


def test_status_none_ketika_belum_dijawab() -> None:
    assert BarisPenerapan(komitmen=_komitmen()).status is None


def test_cacah_berkunci_seluruh_status() -> None:
    """Kunci yang hilang adalah status yang tidak dihitung, dan itu terlihat.
    Daftar berurut menyembunyikannya."""
    assert set(Jurnal().jumlah_menurut_status()) == set(StatusPenerapan)


def test_belum_dijawab_memakai_tanggal_yang_diserahkan_pemanggil() -> None:
    """Fungsi yang membaca jamnya sendiri tidak dapat diuji tanpa membekukan
    waktu, dan yang tidak dapat diuji akan dipercaya begitu saja."""
    jurnal = Jurnal(diterapkan=(BarisPenerapan(komitmen=_komitmen(9, date(2026, 9, 1))),))
    assert jurnal.belum_dijawab(date(2026, 8, 31)) == ()
    assert len(jurnal.belum_dijawab(date(2026, 9, 1))) == 1


def test_komitmen_yang_sudah_dijawab_tidak_muncul_sebagai_tertunggak() -> None:
    jurnal = _jurnal_terisi()
    tertunggak = jurnal.belum_dijawab(date(2026, 12, 31))
    assert [k.id_komitmen for k in tertunggak] == ["KMT-2"]


def test_jam_sistem_tidak_dipakai() -> None:
    naskah = (AKAR / "src" / "pengguna" / "jurnal.py").read_text(encoding="utf-8")
    assert "datetime.now" not in naskah
    assert "date.today" not in naskah


# ----------------------------------------------------------- R-18 · C-15


def test_tidak_ada_gamifikasi_pada_permukaan_modul() -> None:
    """**C-15 diuji sebagai ketiadaan, dan justru di sini.**

    Jurnal berisi rekapitulasi adalah tempat lencana terasa paling wajar: ia
    sudah menghitung, sudah berurut waktu, sudah milik satu orang. C-15
    melarang membuat tabelnya "kosong pun tidak".
    """
    terlarang = {"poin", "lencana", "peringkat", "runtun", "skor", "badge", "streak", "level"}
    permukaan = {n.lower() for n in dir(Jurnal) if not n.startswith("_")}
    permukaan |= {n.lower() for n in Jurnal.model_fields}
    assert not (permukaan & terlarang)


def test_naskah_modul_tidak_menyebut_bentuk_gamifikasi_sebagai_bidang() -> None:
    """Sapuan naskah, bukan hanya permukaan: bidang yang ditambahkan pada kelas
    lain di modul yang sama tetap tertangkap."""
    naskah = (AKAR / "src" / "pengguna" / "jurnal.py").read_text(encoding="utf-8")
    for terlarang in ("poin:", "lencana:", "peringkat:", "skor:", "runtun:"):
        assert terlarang not in naskah, terlarang


def test_tidak_ada_bidang_ringkasan_berupa_angka() -> None:
    """Satu angka kemajuan adalah papan skor yang belum diberi nama. Ketiga
    bagian berdiri sebagai tiga daftar, dan tidak ada yang menjumlahkannya
    menjadi nilai tunggal."""
    for nama, bidang in Jurnal.model_fields.items():
        assert bidang.annotation is not int, nama
        assert bidang.annotation is not float, nama


def test_pemahaman_menyimpan_benar_dari_berapa_bukan_nilai() -> None:
    """Nilai mengundang perbandingan antarpengguna, dan perbandingan
    antarpengguna adalah papan peringkat yang belum diberi nama."""
    assert set(PemahamanTercatat.model_fields) == {
        "id_butir",
        "benar",
        "jumlah_pertanyaan",
        "dijawab",
    }


def test_jumlah_pertanyaan_wajib_positif() -> None:
    """Nol pertanyaan menghasilkan pembagian yang tidak berarti bagi siapa pun
    yang menghitung rasionya kelak."""
    with pytest.raises(ValidationError):
        PemahamanTercatat(id_butir="BTR-1", benar=0, jumlah_pertanyaan=0, dijawab=SAAT)


# ------------------------------------------------------- FR-H07 · tertahan


def test_ekspor_pdf_menyatakan_alasan_tertahannya() -> None:
    """Fungsi yang tidak ada terbaca sebagai fitur yang tidak pernah diminta;
    alasan yang dapat dipanggil terbaca sebagai utang yang dapat ditagih.
    Bentuk yang sama dengan `parquet_tertahan()` fitur 012."""
    assert pdf_tertahan() == ALASAN_PDF_TERTAHAN
    assert "C-12" in ALASAN_PDF_TERTAHAN
    assert "FR-H07" in ALASAN_PDF_TERTAHAN


def test_alasan_menyebut_apa_yang_ditunggu_bukan_sekadar_belum_tersedia() -> None:
    """Alasan yang tidak menyebut apa yang ditunggu adalah alasan yang tidak
    dapat ditagih — bentuk yang sama dengan `pemeriksaan_menunggu_model` (008)."""
    assert "rapat" in ALASAN_PDF_TERTAHAN.lower()


# --------------------------------------------------------------- bentuk


def test_jurnal_beku() -> None:
    with pytest.raises(ValidationError):
        Jurnal().dipelajari = ()  # type: ignore[misc]


def test_waktu_wajib_berzona() -> None:
    with pytest.raises(ValidationError):
        ButirDipelajari(id_butir="BTR-1", judul="x", dibuka=datetime(2026, 8, 16, 3, 0))
    with pytest.raises(ValidationError):
        PemahamanTercatat(
            id_butir="BTR-1", benar=1, jumlah_pertanyaan=2, dijawab=datetime(2026, 8, 16, 3, 0)
        )
