"""Uji peristiwa telemetri — A-1 dan A-2 fitur 012, R-01 s.d. R-03, R-06, R-09.

Taksonomi **dibaca dari `docs/D01.md` Bagian 9**, bukan disalin ke berkas ini.
D-01 menyebutnya "luaran teknis kunci 2026", dan daftar yang disalin akan
menyimpang dari pemiliknya tanpa seorang pun tahu — lalu kelompok pembanding
2028 dibandingkan terhadap taksonomi yang berbeda.

## `properti` dijaga dua arah, dan keduanya perlu

**Nilainya** disapu pendeteksi FR-B04. **Kuncinya** ditolak bila beridentitas.
Kunci beridentitas lolos pendeteksi pola sebab nilainya belum tentu berpola:
`{"nama": "Siti Aminah"}` bersih menurut keenam pola dan tetap data pribadi.
"""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.telemetri.peristiwa import JenisPeristiwa, Peristiwa

AKAR = Path(__file__).resolve().parents[2]

WAKTU = datetime(2026, 8, 13, 4, 0, tzinfo=UTC)


def _peristiwa(**ganti: object) -> Peristiwa:
    argumen: dict[str, object] = {
        "pseudonim": "PSD-a1",
        "jenis": JenisPeristiwa.QUESTION_ASKED,
        "waktu": WAKTU,
        "properti": {"kategori": "K3", "panjang_teks": 42},
        "versi_aplikasi": "0.12.0",
        "versi_model": "tiruan-0",
    }
    argumen.update(ganti)
    return Peristiwa(**argumen)  # type: ignore[arg-type]


def _kode_d01() -> set[str]:
    """Kode peristiwa pada tabel D-01 Bagian 9 — sumbernya, bukan salinannya.

    D-01 menuliskan beberapa baris sebagai pasangan (`session_start` /
    `session_end`, `knowledge_check_started` / `_completed`), dan bentuk
    berakhiran `_completed` diuraikan dari pasangannya.
    """
    teks = (AKAR / "docs" / "D01.md").read_text(encoding="utf-8")
    awal = teks.index("## 9. Instrumentasi Telemetri")
    akhir = teks.index("### 9.1")
    kode: set[str] = set()
    for garis in teks[awal:akhir].splitlines():
        if not garis.startswith("|"):
            continue
        sel = garis.split("|")[1]
        ditemukan = re.findall(r"`(_?[a-z][a-z_]*)`", sel)
        penuh = [k for k in ditemukan if not k.startswith("_")]
        kode.update(penuh)
        for pendek in (k for k in ditemukan if k.startswith("_")):
            if penuh:
                awalan = penuh[0].split("_")[0:-1] or [penuh[0]]
                kode.add("_".join(awalan) + pendek)
    return kode


# ------------------------------------------------------------ R-01 · taksonomi


def test_taksonomi_d01_memang_terbaca() -> None:
    """Pemeriksaan yang tidak menemukan sumbernya tidak memeriksa apa pun."""
    assert len(_kode_d01()) >= 20


def test_seluruh_kode_d01_ada_pada_enum() -> None:
    """**Uji terpenting berkas ini.** Kode yang hilang berarti peristiwa yang
    tidak pernah terekam — dan metrik turunan Bagian 9.1 yang bersandar
    padanya menjadi nol yang terbaca seperti temuan."""
    hilang = _kode_d01() - {j.value for j in JenisPeristiwa}
    assert not hilang, f"kode D-01 Bagian 9 yang hilang: {sorted(hilang)}"


def test_tidak_ada_kode_di_luar_d01() -> None:
    """Kode yang tidak dimiliki D-01 akan terekam tanpa definisi pemicunya, dan
    analisis 2028 tidak dapat menafsirkannya."""
    tambahan = {j.value for j in JenisPeristiwa} - _kode_d01()
    assert tambahan == set(), f"kode di luar D-01 Bagian 9: {sorted(tambahan)}"


def test_kode_di_luar_taksonomi_ditolak() -> None:
    """KM-04: enum tidak pernah menyimpan nilai di luar daftar."""
    with pytest.raises(ValidationError):
        _peristiwa(jenis="button_clicked")


# ------------------------------------------------- R-02 dan R-03 · enam bidang


def test_enam_bidang_fr_j02() -> None:
    assert set(Peristiwa.model_fields) == {
        "pseudonim",
        "jenis",
        "waktu",
        "properti",
        "versi_aplikasi",
        "versi_model",
    }


def test_tidak_ada_bidang_id_pengguna() -> None:
    """**R-03.** FR-J02 menulis "id pengguna **terpseudonim**".

    Bidangnya tidak ada sama sekali — bukan ada lalu dikosongkan. Yang tidak
    ada tidak dapat terisi, dan bidang yang boleh kosong akan terisi pada
    pemanggilan pertama yang menganggapnya berguna.
    """
    for terlarang in ("id_pengguna", "nama", "surel", "email"):
        assert terlarang not in Peristiwa.model_fields


def test_bidang_wajib_tanpa_bawaan() -> None:
    for bidang in Peristiwa.model_fields:
        assert Peristiwa.model_fields[bidang].is_required(), bidang


def test_pseudonim_kosong_ditolak() -> None:
    with pytest.raises(ValidationError):
        _peristiwa(pseudonim="")


def test_versi_wajib_terisi() -> None:
    """FR-J02 menuntut versi aplikasi dan versi model. Peristiwa tanpa versi
    tidak dapat dibandingkan lintas percobaan — dan C-09 menuntut justru itu."""
    with pytest.raises(ValidationError):
        _peristiwa(versi_aplikasi="")
    with pytest.raises(ValidationError):
        _peristiwa(versi_model="   ")


# ------------------------------------------------------------------ R-09 · waktu


def test_waktu_wajib_berzona() -> None:
    """KM-01. Peristiwa tanpa zona dari dua perangkat tidak dapat diurutkan,
    dan retensi D1/D7/D30 dihitung dari urutannya."""
    with pytest.raises(ValidationError):
        _peristiwa(waktu=datetime(2026, 8, 13, 4, 0))


def test_peristiwa_beku() -> None:
    """R-07 pada bentuknya: peristiwa yang dapat diubah sesudah terekam tidak
    membuktikan apa pun tentang apa yang terjadi."""
    with pytest.raises(ValidationError):
        _peristiwa().pseudonim = "PSD-b2"  # type: ignore[misc]


# ------------------------------------------------- R-06 · properti dua arah


@pytest.mark.parametrize(
    "properti",
    [
        {"catatan": "hubungi 081234567890"},
        {"rujukan": "NIK 3273010101800001"},
    ],
)
def test_nilai_properti_bermuatan_data_pribadi_ditolak(
    properti: dict[str, object],
) -> None:
    """Arah pertama — **tolak, jangan saring.** D-14 Bagian 5.1:
    `peristiwa.properti` *"tidak pernah memuat data pribadi"*."""
    with pytest.raises(ValidationError):
        _peristiwa(properti=properti)


@pytest.mark.parametrize("kunci", ["id_pengguna", "nama", "surel", "Nama_Lengkap"])
def test_kunci_properti_beridentitas_ditolak(kunci: str) -> None:
    """**Arah kedua, dan ia yang paling mudah terlewat.**

    Kunci beridentitas lolos pendeteksi pola sebab nilainya belum tentu
    berpola: `{"nama": "Siti Aminah"}` bersih menurut keenam pola FR-B04 dan
    tetap data pribadi. Pemeriksaan huruf besar-kecil disamakan, sebab kunci
    yang ditulis `Nama_Lengkap` sama saja isinya.
    """
    with pytest.raises(ValidationError):
        _peristiwa(properti={kunci: "apa pun"})


def test_properti_bersih_diterima() -> None:
    """Kekeliruan ke arah ketat harus tetap membiarkan taksonomi berjalan:
    properti sah D-01 Bagian 9 tidak boleh ikut tertolak."""
    assert _peristiwa(
        properti={
            "durasi": 120,
            "jenis_perangkat": "ponsel",
            "kualitas_jaringan": "sedang",
            "jumlah_sitasi": 3,
        }
    )


def test_properti_bersarang_juga_disapu() -> None:
    """Data pribadi yang disembunyikan satu lapis lebih dalam adalah bentuk
    yang paling mungkin terjadi ketika pemanggil menyalin objek apa adanya."""
    with pytest.raises(ValidationError):
        _peristiwa(properti={"konteks": {"catatan": "hubungi 081234567890"}})
    with pytest.raises(ValidationError):
        _peristiwa(properti={"konteks": {"nama": "apa pun"}})


def test_properti_berupa_daftar_juga_disapu() -> None:
    """D-01 Bagian 9 memberi `injection_suspected` properti "pola yang cocok" —
    jamak, dan karena itu berupa daftar.

    Data pribadi di dalam daftar lolos setiap sapuan yang hanya menelusuri
    pemetaan, dan bentuk itu justru yang muncul ketika pemanggil menyalin hasil
    pencocokan apa adanya.
    """
    with pytest.raises(ValidationError):
        _peristiwa(properti={"pola_cocok": ["bersih", "hubungi 081234567890"]})
    with pytest.raises(ValidationError):
        _peristiwa(properti={"jejak": ({"nama": "apa pun"},)})


def test_daftar_bersih_diterima() -> None:
    """Kekeliruan ke arah ketat tidak boleh menutup properti jamak yang sah."""
    assert _peristiwa(properti={"pola_cocok": ["abaikan_instruksi", "peran_baru"]})


def test_properti_kosong_diterima() -> None:
    """Beberapa peristiwa D-01 Bagian 9 tidak membawa properti utama. Menolak
    properti kosong akan memaksa pemanggil mengisinya dengan sesuatu."""
    assert _peristiwa(properti={}).properti == {}


def test_galat_properti_tidak_mengulang_muatannya() -> None:
    """Galat yang mengutip muatannya memindahkan kebocoran dari basis data ke
    log — bentuk yang sama dengan `GalatJejak` fitur 002."""
    with pytest.raises(ValidationError) as galat:
        _peristiwa(properti={"catatan": "hubungi 081234567890"})
    assert "081234567890" not in str(galat.value)
