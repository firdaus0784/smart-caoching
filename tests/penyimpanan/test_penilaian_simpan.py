"""Penyimpan penilaian dan aduan — T-4 fitur 036, R-01, R-02, R-05, R-06; P-2 B.

Satu himpunan uji atas pelaksana memori **dan** PostgreSQL. Yang kedua
tersambung sebagai peran produksinya sendiri: riwayat sebagai `peran_riwayat`,
penilaian sebagai `peran_penilaian`, aduan sebagai `peran_kurasi` — uji yang
tersambung sebagai pengelola menyembunyikan kegagalan hak (TK-64).

Basis data bersama: antrean aduan memuat aduan uji lain, sehingga setiap uji
menyaring aduannya sendiri lewat pertanyaan yang dibangkitkan unik.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from src.kamus.penilaian import NilaiPenilaian, TindakLanjutAduan
from src.penyimpanan.kurasi import PERAN_KURASI
from src.penyimpanan.penilaian import (
    PERAN_PENILAIAN,
    AduanMemori,
    AduanPostgres,
    BarisAduan,
    PenilaianMemori,
    PenilaianPostgres,
    PenyimpanAduan,
    PenyimpanPenilaian,
    PesanTidakAda,
)
from src.penyimpanan.riwayat import PERAN_RIWAYAT, PenyimpanRiwayat, RiwayatMemori, RiwayatPostgres
from tests.konftes_asinkron import jalankan
from tests.peladen import siapkan
from tests.penyimpanan.test_akun import SambunganPeran

siapkan()

AKAR = Path(__file__).resolve().parents[2]
T0 = datetime(2026, 10, 8, 3, 0, tzinfo=UTC)
KURATOR = "psd_kkkkkkkkkkkkkkkk"


@dataclass
class Dunia:
    riwayat: PenyimpanRiwayat
    penilaian: PenyimpanPenilaian
    aduan: PenyimpanAduan


@pytest.fixture(params=["memori", "postgres"])
def dunia(request: pytest.FixtureRequest) -> Dunia:
    if request.param == "memori":
        riwayat = RiwayatMemori()
        penilaian = PenilaianMemori(riwayat)
        return Dunia(riwayat, penilaian, AduanMemori(penilaian))
    return Dunia(
        RiwayatPostgres(SambunganPeran(PERAN_RIWAYAT)),  # type: ignore[arg-type]
        PenilaianPostgres(SambunganPeran(PERAN_PENILAIAN)),  # type: ignore[arg-type]
        AduanPostgres(SambunganPeran(PERAN_KURASI)),  # type: ignore[arg-type]
    )


def _psd() -> str:
    return "psd_" + "".join(uuid.uuid4().hex[i] for i in range(16)).translate(
        str.maketrans("0123456789", "ghijklmnop")
    )


def _tanggapan(id_pesan: str) -> dict[str, Any]:
    return {
        "id_pesan": id_pesan,
        "status_dasar": "kuat",
        "ringkasan_tindakan": ["Susun jadwal bergilir."],
        "penjelasan": "Jadwal yang diumumkan sejak awal semester.",
        "versi": {"model": "model-uji-036", "indeks": "i", "kode": "k"},
    }


def _tanya(d: Dunia, pemilik: str) -> tuple[str, str]:
    """Satu giliran beserta tanggapannya; kembalikan id pesan dan pertanyaan unik."""
    id_pesan, pertanyaan = f"msg_{uuid.uuid4().hex}", f"Pertanyaan {uuid.uuid4().hex}?"
    jalankan(
        d.riwayat.catat(
            pemilik=pemilik,
            id_percakapan=uuid.uuid4(),
            pertanyaan=pertanyaan,
            id_pesan=id_pesan,
            waktu=T0,
            tanggapan=_tanggapan(id_pesan),
        )
    )
    return id_pesan, pertanyaan


def _nilai(
    d: Dunia,
    pemilik: str,
    id_pesan: str,
    nilai: NilaiPenilaian = NilaiPenilaian.KELIRU,
    *,
    kirim: bool = True,
    alasan: str | None = "Pasalnya sudah diubah.",
    waktu: datetime = T0,
) -> Any:
    return jalankan(
        d.penilaian.catat(
            pemilik=pemilik,
            id_pesan=id_pesan,
            nilai=nilai,
            alasan=alasan,
            kirim_ke_kurator=kirim,
            waktu=waktu,
        )
    )


def _aduanku(d: Dunia, pertanyaan: str) -> list[BarisAduan]:
    return [a for a in jalankan(d.aduan.terbuka()) if a.pertanyaan == pertanyaan]


# ── P-2 B · aduan hanya bila dikirim ─────────────────────────────────


def test_keliru_tanpa_centang_tercatat_tetapi_tidak_menjadi_aduan(dunia: Dunia) -> None:
    """M-5: `kirim_ke_kurator` diabaikan."""
    a = _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    hasil = _nilai(dunia, a, id_pesan, kirim=False)
    assert hasil.nomor > 0
    assert _aduanku(dunia, pertanyaan) == []


def test_keliru_dengan_centang_menjadi_aduan_salinan(dunia: Dunia) -> None:
    """M-6: `id_pesan` tertinggal pada salinan."""
    a = _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    _nilai(dunia, a, id_pesan, alasan="Pasalnya sudah diubah.", waktu=T0 + timedelta(minutes=5))
    (aduan,) = _aduanku(dunia, pertanyaan)
    tanpa_id = {k: v for k, v in _tanggapan(id_pesan).items() if k != "id_pesan"}
    assert dict(aduan.tanggapan) == tanpa_id
    assert aduan.alasan == "Pasalnya sudah diubah."
    assert aduan.diadukan_pada == T0 + timedelta(minutes=5)
    # R-06: tidak ada penaut ke peserta di mana pun pada baris aduan.
    assert {f.name for f in fields(BarisAduan)} == {
        "nomor",
        "diadukan_pada",
        "pertanyaan",
        "alasan",
        "tanggapan",
    }
    assert a not in repr(aduan) and id_pesan not in repr(aduan)


def test_penilaian_berikutnya_menggugurkan_aduan_sebelumnya(dunia: Dunia) -> None:
    """R-05, M-7: yang terakhir berlaku — apa pun nilainya."""
    a = _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    _nilai(dunia, a, id_pesan)
    (pertama,) = _aduanku(dunia, pertanyaan)
    _nilai(dunia, a, id_pesan, NilaiPenilaian.MEMBANTU, kirim=False, alasan=None)
    assert _aduanku(dunia, pertanyaan) == []
    _nilai(dunia, a, id_pesan, alasan="Tetap keliru.")
    (kedua,) = _aduanku(dunia, pertanyaan)
    assert kedua.nomor != pertama.nomor
    assert kedua.alasan == "Tetap keliru."


# ── R-01 · pemilik ───────────────────────────────────────────────────


def test_pesan_milik_orang_lain_sama_dengan_tidak_dikenal(dunia: Dunia) -> None:
    a, b = _psd(), _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    for pemilik, pesan in ((b, id_pesan), (a, f"msg_{uuid.uuid4().hex}")):
        with pytest.raises(PesanTidakAda) as galat:
            _nilai(dunia, pemilik, pesan)
        assert str(galat.value) == "pesan tidak ada"
    assert _aduanku(dunia, pertanyaan) == []


def test_pemilik_kosong_ditolak_tanpa_menulis(dunia: Dunia) -> None:
    id_pesan, pertanyaan = _tanya(dunia, _psd())
    with pytest.raises(ValueError, match="pemilik"):
        _nilai(dunia, " ", id_pesan)
    assert _aduanku(dunia, pertanyaan) == []


def test_versi_model_dibaca_dari_tanggapan_yang_dinilai(dunia: Dunia) -> None:
    a = _psd()
    id_pesan, _ = _tanya(dunia, a)
    assert _nilai(dunia, a, id_pesan, kirim=False).versi_model == "model-uji-036"


@pytest.mark.parametrize(
    ("argumen", "pesan"),
    [
        ({"nilai": NilaiPenilaian.MEMBANTU, "kirim": True}, "keliru"),
        ({"alasan": "   "}, "alasan"),
        ({"waktu": datetime(2026, 10, 8, 3, 0)}, "UTC"),
    ],
)
def test_penilaian_salah_bentuk_ditolak_tanpa_menulis(
    dunia: Dunia, argumen: dict[str, Any], pesan: str
) -> None:
    a = _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    with pytest.raises(ValueError, match=pesan):
        _nilai(dunia, a, id_pesan, **argumen)
    assert _aduanku(dunia, pertanyaan) == []


# ── tindak lanjut ────────────────────────────────────────────────────


def _tindak(d: Dunia, nomor: int, catatan: str = "Sudah sesuai dasarnya.", **lain: Any) -> bool:
    argumen: dict[str, Any] = {
        "tindak_lanjut": TindakLanjutAduan.JAWABAN_SESUAI_DASAR,
        "catatan": catatan,
        "peran": "kurator",
        "pseudonim_kurator": KURATOR,
        "waktu": T0,
        **lain,
    }
    return bool(jalankan(d.aduan.tindak_lanjut(nomor, **argumen)))


def test_tindak_lanjut_sekali_dan_aduan_keluar_dari_antrean(dunia: Dunia) -> None:
    """M-12: tindak lanjut kedua diterima."""
    a = _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    _nilai(dunia, a, id_pesan)
    (aduan,) = _aduanku(dunia, pertanyaan)
    assert _tindak(dunia, aduan.nomor)
    assert _aduanku(dunia, pertanyaan) == []
    assert not _tindak(dunia, aduan.nomor, "Kedua kali.")


def test_aduan_gugur_atau_tak_dikenal_tidak_dapat_ditindaklanjuti(dunia: Dunia) -> None:
    a = _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    _nilai(dunia, a, id_pesan)
    (aduan,) = _aduanku(dunia, pertanyaan)
    _nilai(dunia, a, id_pesan, NilaiPenilaian.TIDAK_MEMBANTU, kirim=False)
    assert not _tindak(dunia, aduan.nomor)
    assert not _tindak(dunia, 9_000_000_000)


def test_antrean_terlama_lebih_dulu(dunia: Dunia) -> None:
    a = _psd()
    (p1, q1), (p2, q2) = _tanya(dunia, a), _tanya(dunia, a)
    _nilai(dunia, a, p2, waktu=T0 + timedelta(minutes=2))
    _nilai(dunia, a, p1, waktu=T0 + timedelta(minutes=1))
    urutan = [x.pertanyaan for x in jalankan(dunia.aduan.terbuka()) if x.pertanyaan in (q1, q2)]
    assert urutan == [q1, q2]


@pytest.mark.parametrize(
    ("lain", "pesan"),
    [
        ({"catatan": "  "}, "catatan"),
        ({"pseudonim_kurator": "ks-017"}, "pseudonim"),
        ({"peran": "pengguna"}, "peran"),
    ],
)
def test_tindak_lanjut_salah_bentuk_ditolak(dunia: Dunia, lain: dict[str, Any], pesan: str) -> None:
    a = _psd()
    id_pesan, pertanyaan = _tanya(dunia, a)
    _nilai(dunia, a, id_pesan)
    (aduan,) = _aduanku(dunia, pertanyaan)
    with pytest.raises(ValueError, match=pesan):
        _tindak(dunia, aduan.nomor, **lain)
    assert _aduanku(dunia, pertanyaan) == [aduan]


# ── permukaan dan arah ───────────────────────────────────────────────


@pytest.mark.parametrize(
    ("kelas", "harapan"),
    [
        (PenilaianPostgres, {"catat"}),
        (PenilaianMemori, {"catat", "baris_aduan", "digantikan"}),
        (AduanPostgres, {"terbuka", "tindak_lanjut"}),
        (AduanMemori, {"terbuka", "tindak_lanjut"}),
    ],
)
def test_permukaan_tanpa_ubah_maupun_hapus(kelas: type, harapan: set[str]) -> None:
    assert {n for n in dir(kelas) if not n.startswith("_")} == harapan


def test_penyimpan_tidak_mengimpor_api_maupun_nlp() -> None:
    isi = (AKAR / "src" / "penyimpanan" / "penilaian.py").read_text(encoding="utf-8")
    assert "src.api" not in isi and "src.nlp" not in isi
