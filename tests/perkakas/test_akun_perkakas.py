"""Perkakas akun tim — T-7 fitur 029, P-5, P-7, K-5, plan Bagian 9.

Dijalankan terhadap PostgreSQL sungguhan sebagai `peran_pengelola_akun`:
perkakas ini justru ada untuk memakai hak per kolom T-2, dan tiruannya tidak
membuktikan apa pun tentang hak itu.

Sandi dicetak **sekali** ke keluaran dan tidak ke mana pun selain itu —
diuji dengan menjalankan perkakas di direktori kosong lalu memeriksa bahwa
direktori itu tetap kosong, dan bahwa log tidak memuatnya.
"""

from __future__ import annotations

import io
import logging
import os
import re
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from src.api import sandi
from src.nlp.anonimisasi.pola import periksa_data_pribadi
from src.penyimpanan.akun import PERAN_AUTENTIKASI, AkunPostgres
from tests.konftes_asinkron import jalankan
from tests.peladen import psql, siapkan
from tests.penyimpanan.test_akun import SambunganPeran

from perkakas import akun as perkakas_akun

siapkan()

T0 = datetime.now(UTC)
HURUF = "abcdefghjkmnpqrstuvwxyz"


def _id_baru() -> str:
    return "".join(secrets.choice(HURUF) for _ in range(6)) + f"-{secrets.randbelow(1000):03d}"


def _jalan(*argumen: str) -> tuple[int, str, str]:
    keluar, galat = io.StringIO(), io.StringIO()
    kode = perkakas_akun.utama(
        list(argumen),
        pengelola=perkakas_akun.PengelolaAkunPostgres(SambunganPeran("peran_pengelola_akun")),  # type: ignore[arg-type]
        keluar=keluar,
        galat=galat,
        parameter=sandi.ParameterScrypt(n=2**4, r=8, p=1),
    )
    return kode, keluar.getvalue(), galat.getvalue()


def _sandi_pada(keluaran: str) -> str:
    temuan = re.findall(r"\b[2-9a-z]{4}-[2-9a-z]{4}-[2-9a-z]{4}-[2-9a-z]{4}\b", keluaran)
    assert len(temuan) == 1, keluaran
    return temuan[0]


def _baris(id_akun: str, kolom: str) -> str:
    hasil = psql(
        "smart_coaching", "-c", f"select {kolom} from akun.pengguna where id = '{id_akun}'"
    )
    return hasil.stdout.strip()


def test_buat_akun_mencetak_sandi_sekali_dan_menyimpan_turunannya() -> None:
    id_akun = _id_baru()
    kode, keluar, galat = _jalan("buat", "--id", id_akun, "--peran", "pengguna")
    assert kode == 0, galat
    kata = _sandi_pada(keluar)
    assert keluar.count(kata) == 1
    tersimpan = _baris(id_akun, "turunan_sandi")
    assert kata not in tersimpan
    assert sandi.cocok(kata, tersimpan)
    assert _baris(id_akun, "peran || ':' || status_aktif") == "pengguna:true"


def test_pseudonim_tidak_dicetak() -> None:
    id_akun = _id_baru()
    _, keluar, _ = _jalan("buat", "--id", id_akun, "--peran", "pengguna")
    pseudonim = _baris(id_akun, "pseudonim")
    assert re.fullmatch(r"psd_[a-z]{16}", pseudonim)
    assert pseudonim not in keluar


@pytest.mark.parametrize(
    "id_akun",
    ["Budi Santoso", "budi", "KS-017", "3201010101010001", "ks-0170", "budi.santoso@sekolah.id"],
)
def test_id_yang_bukan_pola_akun_ditolak(id_akun: str) -> None:
    """Perkakas tidak menerima nama orang, nomor, maupun surel (C-05)."""
    kode, keluar, galat = _jalan("buat", "--id", id_akun, "--peran", "pengguna")
    assert kode != 0
    assert keluar == ""
    assert id_akun not in galat, "pesan penolakan mengutip masukan yang ditolak"
    hasil = psql(
        "smart_coaching", "-c", f"select count(*) from akun.pengguna where id = '{id_akun}'"
    )
    assert hasil.stdout.strip() == "0"


def test_peran_di_luar_d14_ditolak() -> None:
    kode, keluar, _ = _jalan("buat", "--id", _id_baru(), "--peran", "kepala")
    assert kode != 0
    assert keluar == ""


def test_akun_ganda_ditolak_tanpa_mencetak_sandi() -> None:
    id_akun = _id_baru()
    assert _jalan("buat", "--id", id_akun, "--peran", "pengguna")[0] == 0
    kode, keluar, _ = _jalan("buat", "--id", id_akun, "--peran", "admin")
    assert kode != 0
    assert keluar == ""
    assert _baris(id_akun, "peran") == "pengguna"


def _sesi_aktif(id_akun: str) -> bytes:
    akun = AkunPostgres(SambunganPeran(PERAN_AUTENTIKASI))  # type: ignore[arg-type]
    turunan = secrets.token_bytes(32)
    jalankan(
        akun.buat_sesi(turunan, id_akun, sekarang=T0, kedaluwarsa_pada=T0 + timedelta(hours=8))
    )
    return turunan


def _sesi_terbaca(turunan: bytes) -> bool:
    akun = AkunPostgres(SambunganPeran(PERAN_AUTENTIKASI))  # type: ignore[arg-type]
    return (
        jalankan(akun.baca_sesi(turunan, sekarang=T0, batas_diam=timedelta(minutes=30))) is not None
    )


def test_atur_ulang_sandi_mencabut_sesi_dan_membuka_penahanan() -> None:
    id_akun = _id_baru()
    _, keluar, _ = _jalan("buat", "--id", id_akun, "--peran", "pengguna")
    lama = _sandi_pada(keluar)
    turunan = _sesi_aktif(id_akun)
    psql(
        "smart_coaching",
        "-c",
        f"update akun.pengguna set gagal_beruntun = 10, ditahan_sampai = now() + interval '1 hour' "
        f"where id = '{id_akun}'",
    )
    kode, keluar, galat = _jalan("atur-ulang-sandi", "--id", id_akun)
    assert kode == 0, galat
    baru = _sandi_pada(keluar)
    assert baru != lama
    tersimpan = _baris(id_akun, "turunan_sandi")
    assert sandi.cocok(baru, tersimpan) and not sandi.cocok(lama, tersimpan)
    assert _baris(id_akun, "gagal_beruntun || ':' || coalesce(ditahan_sampai::text, '-')") == "0:-"
    assert not _sesi_terbaca(turunan)


def test_nonaktifkan_mencabut_seluruh_sesi() -> None:
    id_akun = _id_baru()
    _jalan("buat", "--id", id_akun, "--peran", "pengguna")
    satu, dua = _sesi_aktif(id_akun), _sesi_aktif(id_akun)
    kode, keluar, galat = _jalan("nonaktifkan", "--id", id_akun)
    assert kode == 0, galat
    assert _baris(id_akun, "status_aktif") == "f"
    assert not _sesi_terbaca(satu) and not _sesi_terbaca(dua)
    hasil = psql(
        "smart_coaching",
        "-c",
        f"select count(*) from akun.sesi where id_pengguna = '{id_akun}' and dicabut_pada is null",
    )
    assert hasil.stdout.strip() == "0"


@pytest.mark.parametrize("perintah", ["atur-ulang-sandi", "nonaktifkan"])
def test_akun_tak_ada_ditolak(perintah: str) -> None:
    kode, keluar, _ = _jalan(perintah, "--id", "tak-ada-000")
    assert kode != 0
    assert keluar == ""


def test_sandi_tidak_tertulis_ke_berkas_maupun_log(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    sebelum = os.getcwd()
    os.chdir(tmp_path)
    try:
        with caplog.at_level(logging.DEBUG):
            _, keluar, _ = _jalan("buat", "--id", _id_baru(), "--peran", "pengguna")
    finally:
        os.chdir(sebelum)
    kata = _sandi_pada(keluar)
    assert list(tmp_path.iterdir()) == []
    assert kata not in "\n".join(r.getMessage() for r in caplog.records)


def test_pseudonim_bangkitan_tidak_pernah_berpola_data_pribadi() -> None:
    """KB-158: pseudonim heksadesimal sekitar satu dari dua puluh berderet
    angka berpola rekening. Huruf saja tidak dapat."""
    for _ in range(2000):
        pseudonim = perkakas_akun.bangkitkan_pseudonim()
        assert re.fullmatch(r"psd_[a-z]{16}", pseudonim)
        assert not periksa_data_pribadi(pseudonim)


def test_perintah_tanpa_argumen_menolak_dengan_bantuan() -> None:
    with pytest.raises(SystemExit) as galat:
        _jalan()
    assert galat.value.code != 0
