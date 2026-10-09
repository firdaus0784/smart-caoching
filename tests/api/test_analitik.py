"""Metrik analitik — T-4 fitur 035, R-03, R-04, R-05; K-2; D-14 Bagian 4.8.

Peristiwa buatan yang jawabannya dihitung tangan. Kalender Maret 2031:
1 Sabtu, 2 Minggu, 3 Senin, 8 Sabtu, 9 Minggu, 30 Minggu, 31 Senin. "Hari
ini" 31 Maret 2031 WIB.

| Pseudonim | Tanggal berperistiwa (WIB) | Catatan |
|---|---|---|
| a | 1, 2, 8, 31 | tanggal 2 dari 1 Maret 18.00 UTC — batas WIB |
| b | 1, 3, 9, 31 | kembali sesudah hari ke-N, bukan tepat |
| c | 30, 31 | kohort yang belum berumur 7 hari |
| d | 31 | kohort hari ini |
| e | 1, 2 | `pengembangan` saja — tidak masuk metrik |
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from src.api.analitik import (
    VERSI_PENGEMBANGAN,
    MetrikTertunda,
    ringkasan,
)
from src.penyimpanan.telemetri import BarisPeristiwa

SEKARANG = datetime(2031, 3, 31, 5, 0, tzinfo=UTC)  # 12.00 WIB


def _psd(huruf: str) -> str:
    return "psd_" + huruf * 16


def _p(
    huruf: str,
    waktu: datetime,
    jenis: str = "session_start",
    properti: dict[str, Any] | None = None,
    versi: str = "pilot-1",
) -> BarisPeristiwa:
    return BarisPeristiwa(
        pseudonim=_psd(huruf),
        jenis=jenis,
        waktu=waktu,
        properti=properti or {},
        versi_aplikasi=versi,
        versi_model="tanpa_model",
    )


def _hari(tanggal: int, jam_utc: int = 1) -> datetime:
    return datetime(2031, 3, tanggal, jam_utc, 0, tzinfo=UTC)


PERISTIWA = [
    _p("a", _hari(1)),
    _p("a", _hari(1, jam_utc=18)),  # 2 Maret 01.00 WIB
    _p("a", _hari(8)),
    _p("a", _hari(31)),
    _p("b", _hari(1)),
    _p("b", _hari(3)),
    _p("b", _hari(9)),
    _p("b", _hari(31)),
    _p("c", _hari(30)),
    _p("c", _hari(31)),
    _p("d", _hari(31)),
    # Sesi — tanggal yang sudah ada, agar keaktifan tidak berubah.
    _p("a", _hari(31, 2), "session_end", {"durasi_menit": 10}),
    _p("b", _hari(31, 2), "session_end", {"durasi_menit": 20}),
    _p("c", _hari(31, 2), "session_end", {"durasi_menit": 45}),
    _p("d", _hari(31, 2), "session_end"),
    # Penemuan.
    *[_p("d", _hari(31, 3), "discovery_served", {"id_butir": f"b{i}"}) for i in range(4)],
    _p("d", _hari(31, 4), "discovery_opened", {"id_butir": "b0", "menit_sejak_tayang": 3}),
    # Pengembangan — tidak boleh masuk metrik.
    _p("e", _hari(1), versi=VERSI_PENGEMBANGAN),
    _p("e", _hari(2), versi=VERSI_PENGEMBANGAN),
    _p("e", _hari(2), "session_end", {"durasi_menit": 1000}, versi=VERSI_PENGEMBANGAN),
    _p("e", _hari(2), "discovery_served", {"id_butir": "x"}, versi=VERSI_PENGEMBANGAN),
]


def _r() -> Any:
    return ringkasan(PERISTIWA, sekarang=SEKARANG)


def test_aktif_harian_per_tanggal_wib() -> None:
    harian = {h.tanggal: h.pengguna for h in _r().keterlibatan.aktif_harian}
    assert harian == {
        date(2031, 3, 1): 2,
        date(2031, 3, 2): 1,
        date(2031, 3, 3): 1,
        date(2031, 3, 8): 1,
        date(2031, 3, 9): 1,
        date(2031, 3, 30): 1,
        date(2031, 3, 31): 4,
    }


def test_aktif_mingguan_senin_sampai_minggu() -> None:
    mingguan = {m.mulai: m.pengguna for m in _r().keterlibatan.aktif_mingguan}
    assert mingguan == {
        date(2031, 2, 24): 2,
        date(2031, 3, 3): 2,
        date(2031, 3, 24): 1,
        date(2031, 3, 31): 4,
    }


def test_retensi_berkohort_tepat_hari_ke_n() -> None:
    """M-2: "pada atau sesudah" menghitung b pada D1 dan D7.
    M-3: kohort c yang belum berumur 7 hari masuk penyebut D7."""
    retensi = {r.hari: (r.kohort, r.kembali, r.rasio) for r in _r().keterlibatan.retensi}
    assert retensi[1] == (3, 2, pytest.approx(2 / 3))
    assert retensi[7] == (2, 1, 0.5)
    assert retensi[30] == (2, 2, 1.0)
    assert list(retensi) == [1, 7, 30]


def test_panjang_sesi_dari_session_end_berdurasi() -> None:
    sesi = _r().keterlibatan.sesi
    assert (sesi.jumlah, sesi.median_menit, sesi.rerata_menit) == (3, 20, 25.0)


def test_rasio_penemuan() -> None:
    penemuan = _r().penemuan
    assert (penemuan.disajikan, penemuan.dibuka, penemuan.rasio) == (4, 1, 0.25)


def test_pengembangan_terpisah_dari_metrik() -> None:
    """M-4: peristiwa `pengembangan` yang tercampur mengubah setiap angka di atas."""
    integritas = _r().integritas
    assert integritas.pengembangan == 4
    assert VERSI_PENGEMBANGAN not in integritas.per_versi_aplikasi
    assert integritas.per_versi_aplikasi == {"pilot-1": len(PERISTIWA) - 4}
    assert integritas.per_jenis["discovery_served"] == 4
    assert integritas.per_jenis["session_start"] == 11
    assert integritas.per_versi_model == {"tanpa_model": len(PERISTIWA) - 4}
    assert (integritas.pertama, integritas.terakhir) == (_hari(1), _hari(31, 4))
    assert VERSI_PENGEMBANGAN == "pengembangan"


def test_tanpa_penyebut_bernilai_null_bukan_nol() -> None:
    """R-04, M-5."""
    kosong = ringkasan([], sekarang=SEKARANG)
    assert [r.rasio for r in kosong.keterlibatan.retensi] == [None, None, None]
    assert [r.kohort for r in kosong.keterlibatan.retensi] == [0, 0, 0]
    sesi = kosong.keterlibatan.sesi
    assert (sesi.jumlah, sesi.median_menit, sesi.rerata_menit) == (0, None, None)
    assert kosong.penemuan.rasio is None
    assert (kosong.integritas.pertama, kosong.integritas.terakhir) == (None, None)
    hanya_pengembangan = ringkasan(PERISTIWA[-4:], sekarang=SEKARANG)
    assert hanya_pengembangan.penemuan.rasio is None
    assert hanya_pengembangan.keterlibatan.aktif_harian == []


def test_metrik_belum_terukur_bernama_dan_bersebab() -> None:
    belum = {b.metrik: b.sebab for b in _r().belum_terukur}
    assert set(belum) == set(MetrikTertunda)
    assert {m.value for m in MetrikTertunda} == {
        "rasio_penuntasan",
        "rasio_verifikasi",
        "rasio_komitmen",
        "rasio_penerapan",
    }
    # Fitur 036 (P-4 B): `akurasi_qa` keluar, digantikan bagian `penilaian`.
    assert "akurasi_qa" not in {m.value for m in MetrikTertunda}
    # Fitur 032 (P-3 A; M-15): digantikan bagian `penelusuran_sumber`.
    assert "rasio_penelusuran_sumber" not in {m.value for m in MetrikTertunda}
    assert all(sebab.strip() for sebab in belum.values())


def _nilai(huruf: str, menit: int, id_pesan: str, nilai: str, **lain: Any) -> BarisPeristiwa:
    return _p(
        huruf,
        _hari(5) + timedelta(minutes=menit),
        "answer_rated",
        {"nilai": nilai, "beralasan": False, "id_pesan": id_pesan},
        **lain,
    )


def test_penilaian_dihitung_atas_yang_terakhir_tiap_pesan() -> None:
    """Fitur 036, KB-228; M-10: setiap penilaian dihitung, bukan yang terakhir."""
    peristiwa = [
        _nilai("a", 1, "msg_1", "keliru"),
        _nilai("a", 2, "msg_1", "membantu"),  # menggantikan yang di atas
        _nilai("a", 3, "msg_2", "tidak_membantu"),
        _nilai("b", 4, "msg_3", "keliru"),
        _nilai("b", 5, "msg_4", "keliru", versi=VERSI_PENGEMBANGAN),  # R-05 fitur 035
    ]
    r = ringkasan(peristiwa, sekarang=SEKARANG)
    assert r.penilaian.per_nilai == {"membantu": 1, "tidak_membantu": 1, "keliru": 1}


def test_penilaian_terakhir_menurut_waktu_bukan_urutan_masukan() -> None:
    peristiwa = [_nilai("a", 9, "msg_1", "keliru"), _nilai("a", 1, "msg_1", "membantu")]
    r = ringkasan(peristiwa, sekarang=SEKARANG)
    assert r.penilaian.per_nilai == {"membantu": 0, "tidak_membantu": 0, "keliru": 1}


def test_penilaian_tanpa_peristiwa_tetap_bertiga_dan_nol() -> None:
    """Nol di sini berarti diukur dan tidak ada — peristiwanya sudah terekam."""
    assert _r().penilaian.per_nilai == {"membantu": 0, "tidak_membantu": 0, "keliru": 0}


def test_dihitung_pada_saat_diminta() -> None:
    assert _r().dihitung_pada == SEKARANG
    lain = ringkasan(PERISTIWA, sekarang=SEKARANG + timedelta(days=7))
    # Seminggu kemudian, kohort c dan d sudah berumur 7 hari.
    assert {r.hari: r.kohort for r in lain.keterlibatan.retensi}[7] == 4


def test_penanda_pengembangan_sama_dengan_titik_jalan() -> None:
    from perkakas.jalankan_lokal import VERSI_APLIKASI_PENGEMBANGAN

    assert VERSI_PENGEMBANGAN == VERSI_APLIKASI_PENGEMBANGAN


def test_rasio_penelusuran_sumber_d01() -> None:
    """D-01 Bagian 9.1: `citation_opened` / `answer_served`, pilot saja (P-3 A)."""
    peristiwa = [
        *[_p("a", _hari(5, j), "answer_served") for j in range(5)],
        _p(
            "a",
            _hari(5, 6),
            "citation_opened",
            {"id_sumber": "d1", "jenis_sumber": "regulasi_resmi"},
        ),
        _p("b", _hari(6), "citation_opened", {"id_sumber": "d1", "jenis_sumber": "regulasi_resmi"}),
        _p("e", _hari(6), "citation_opened", {"id_sumber": "d2"}, versi=VERSI_PENGEMBANGAN),
        _p("e", _hari(6), "answer_served", versi=VERSI_PENGEMBANGAN),
    ]
    sumber = ringkasan(peristiwa, sekarang=SEKARANG).penelusuran_sumber
    assert (sumber.jawaban, sumber.dibuka, sumber.rasio) == (5, 2, 0.4)


def test_rasio_penelusuran_tanpa_jawaban_bernilai_null() -> None:
    peristiwa = [_p("a", _hari(5), "citation_opened", {"id_sumber": "d1"})]
    sumber = ringkasan(peristiwa, sekarang=SEKARANG).penelusuran_sumber
    assert (sumber.jawaban, sumber.dibuka, sumber.rasio) == (0, 1, None)
