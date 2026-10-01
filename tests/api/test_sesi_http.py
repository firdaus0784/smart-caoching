"""Identitas dari sesi — T-5 fitur 029, R-05, R-10, KA-01, D-14 Bagian 4.4.

Penentu identitas sungguhan menolak bekerja tanpa sesi sah: tanpa kuki,
kuki tak dikenal, kuki yang dicabut, sesi yang diam melampaui batas, dan sesi
yang lewat masa mutlaknya — kelimanya menghasilkan 401 `TIDAK_TERAUTENTIKASI`
**sebelum** badan permintaan dibaca dan sebelum jalur penjawab tersentuh.

Sesi disiapkan langsung pada `AkunMemori` dengan pengenal yang diketahui uji;
rute masuk yang membangkitkannya diuji pada T-6. Jam disuntikkan, sehingga
batas 30 menit dan 8 jam diuji tanpa menunggu.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import BATAS_DIAM, MASA_SESI, NAMA_KUKI, PenentuSesi
from src.api.identitas import PenentuIdentitas
from src.api.peran import Peran
from src.api.tanya import HasilTanya
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.riwayat import RiwayatMemori
from tests.api.test_aplikasi import ID_PERCAKAPAN, JalurPalsu, _tanggapan

AKAR = Path(__file__).resolve().parents[2]
T0 = datetime(2026, 10, 1, 7, 0, tzinfo=UTC)


class Jam:
    def __init__(self) -> None:
        self.kini = T0

    def __call__(self) -> datetime:
        return self.kini


AKUN = BarisAkun(
    id="ks-017",
    pseudonim="psd_abcdefghjkmnpqrs",
    peran="pengguna",
    status_aktif=True,
    turunan_sandi="scrypt$16$8$1$AAAA$AAAA",
    gagal_beruntun=0,
    ditahan_sampai=None,
)


class Lingkungan:
    def __init__(self, akun: BarisAkun = AKUN) -> None:
        self.jam = Jam()
        self.akun = AkunMemori()
        self.akun.pasang_akun(akun)
        self.riwayat = RiwayatMemori()
        self.jalur = JalurPalsu(HasilTanya(tanggapan=_tanggapan()))
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=self.jam),
                riwayat=self.riwayat,
                sekarang=self.jam,
            )
        )

    async def sesi_baru(self, id_akun: str = AKUN.id) -> str:
        pengenal = secrets.token_urlsafe(32)
        await self.akun.buat_sesi(
            hashlib.sha256(pengenal.encode()).digest(),
            id_akun,
            sekarang=self.jam(),
            kedaluwarsa_pada=self.jam() + MASA_SESI,
        )
        return pengenal

    def tanya(self, pengenal: str | None, *, badan: object = None) -> object:
        kuki = {"Cookie": f"{NAMA_KUKI}={pengenal}"} if pengenal is not None else {}
        return self.klien.post(
            "/api/v1/tanya",
            json=badan
            if badan is not None
            else {"pertanyaan": "Bagaimana supervisi?", "id_percakapan": ID_PERCAKAPAN},
            headers=kuki,
        )

    def daftar(self, pengenal: str | None) -> object:
        kuki = {"Cookie": f"{NAMA_KUKI}={pengenal}"} if pengenal is not None else {}
        return self.klien.get("/api/v1/percakapan", headers=kuki)

    def satu(self, pengenal: str | None) -> object:
        kuki = {"Cookie": f"{NAMA_KUKI}={pengenal}"} if pengenal is not None else {}
        return self.klien.get(f"/api/v1/percakapan/{ID_PERCAKAPAN}", headers=kuki)


def _jalankan(coro: object) -> object:
    from tests.konftes_asinkron import jalankan

    return jalankan(coro)  # type: ignore[arg-type]


def _tak_terautentikasi(tanggapan: object) -> None:
    assert tanggapan.status_code == 401, tanggapan.text  # type: ignore[attr-defined]
    galat = tanggapan.json()["galat"]  # type: ignore[attr-defined]
    assert galat["kode"] == "TIDAK_TERAUTENTIKASI"
    assert set(galat) == {"kode", "pesan_pengguna", "id_jejak"}


def _ketiga_rute(ling: Lingkungan, pengenal: str | None) -> None:
    for tanggapan in (ling.tanya(pengenal), ling.daftar(pengenal), ling.satu(pengenal)):
        _tak_terautentikasi(tanggapan)
    assert ling.jalur.jumlah_panggilan == 0


def test_penentu_sesi_memenuhi_protokol() -> None:
    assert isinstance(PenentuSesi(AkunMemori(), sekarang=Jam()), PenentuIdentitas)


def test_tanpa_kuki_ditolak_pada_ketiga_rute() -> None:
    _ketiga_rute(Lingkungan(), None)


def test_kuki_tak_dikenal_ditolak() -> None:
    _ketiga_rute(Lingkungan(), secrets.token_urlsafe(32))


@pytest.mark.parametrize("nilai", ["", "a", "x" * 4096, "%C3%A9" * 10, "a=b"])
def test_kuki_berbentuk_aneh_ditolak_bukan_galat_internal(nilai: str) -> None:
    ling = Lingkungan()
    _tak_terautentikasi(ling.daftar(nilai))


def test_sesi_sah_membuka_rute_dengan_pseudonim_sebagai_pemilik() -> None:
    ling = Lingkungan()
    pengenal = _jalankan(ling.sesi_baru())
    tanggapan = ling.tanya(pengenal)  # type: ignore[arg-type]
    assert tanggapan.status_code == 200, tanggapan.text  # type: ignore[attr-defined]
    assert ling.jalur.jumlah_panggilan == 1
    # Pemilik riwayat adalah pseudonim akun — bukan nama akunnya (K-1).
    assert _jalankan(ling.riwayat.daftar(pemilik=AKUN.pseudonim)) == (uuid.UUID(ID_PERCAKAPAN),)
    assert _jalankan(ling.riwayat.daftar(pemilik=AKUN.id)) == ()


def test_tanpa_sesi_ditolak_sebelum_badan_dibaca() -> None:
    """Badan cacat tanpa sesi tetap 401, bukan 400: peladen tidak membaca
    masukan orang yang belum dikenal."""
    ling = Lingkungan()
    _tak_terautentikasi(ling.tanya(None, badan={"bidang": "cacat"}))


def test_sesi_dicabut_ditolak() -> None:
    ling = Lingkungan()
    pengenal = _jalankan(ling.sesi_baru())
    _jalankan(
        ling.akun.cabut_sesi(hashlib.sha256(pengenal.encode()).digest(), sekarang=ling.jam())  # type: ignore[union-attr]
    )
    _ketiga_rute(ling, pengenal)  # type: ignore[arg-type]


def test_sesi_diam_tiga_puluh_menit_ditolak() -> None:
    ling = Lingkungan()
    pengenal = _jalankan(ling.sesi_baru())
    ling.jam.kini = T0 + BATAS_DIAM
    _ketiga_rute(ling, pengenal)  # type: ignore[arg-type]


def test_aktivitas_memperpanjang_batas_diam() -> None:
    """Sesi disentuh pada tiap permintaan sah — paling sering sekali semenit."""
    ling = Lingkungan()
    pengenal = _jalankan(ling.sesi_baru())
    ling.jam.kini = T0 + timedelta(minutes=20)
    assert ling.daftar(pengenal).status_code == 200  # type: ignore[attr-defined]
    ling.jam.kini = T0 + timedelta(minutes=45)
    assert ling.daftar(pengenal).status_code == 200  # type: ignore[attr-defined]


def test_masa_mutlak_delapan_jam_tidak_diperpanjang_aktivitas() -> None:
    ling = Lingkungan()
    pengenal = _jalankan(ling.sesi_baru())
    while ling.jam.kini < T0 + MASA_SESI - timedelta(minutes=20):
        ling.jam.kini += timedelta(minutes=20)
        assert ling.daftar(pengenal).status_code == 200  # type: ignore[attr-defined]
    ling.jam.kini = T0 + MASA_SESI
    _ketiga_rute(ling, pengenal)  # type: ignore[arg-type]


def test_akun_dinonaktifkan_ditolak_pada_permintaan_berikutnya() -> None:
    """KA-01, M-11: peran dan status dibaca dari akun tiap permintaan."""
    from dataclasses import replace

    ling = Lingkungan()
    pengenal = _jalankan(ling.sesi_baru())
    assert ling.daftar(pengenal).status_code == 200  # type: ignore[attr-defined]
    ling.akun.pasang_akun(replace(AKUN, status_aktif=False))
    _ketiga_rute(ling, pengenal)  # type: ignore[arg-type]


def test_peran_dibaca_dari_akun_setiap_permintaan() -> None:
    """Peran yang berubah sesudah masuk berlaku seketika — 403, bukan 401."""
    from dataclasses import replace

    ling = Lingkungan()
    pengenal = _jalankan(ling.sesi_baru())
    assert ling.daftar(pengenal).status_code == 200  # type: ignore[attr-defined]
    ling.akun.pasang_akun(replace(AKUN, peran="anotator"))
    tanggapan = ling.daftar(pengenal)
    assert tanggapan.status_code == 403  # type: ignore[attr-defined]
    assert tanggapan.json()["galat"]["kode"] == "TIDAK_BERWENANG"  # type: ignore[attr-defined]


def test_pesan_belum_masuk_lolos_c13() -> None:
    from src.api.autentikasi import PESAN_BELUM_MASUK
    from src.llm.galat import kalimat_terlalu_panjang

    assert not kalimat_terlalu_panjang(PESAN_BELUM_MASUK)


def test_identitas_pengembangan_tidak_disebut_pada_src() -> None:
    """R-10: tiruan tanpa pemeriksaan tetap hanya terjangkau titik jalan."""
    tersangka = [
        str(b.relative_to(AKAR))
        for b in sorted((AKAR / "src").rglob("*.py"))
        if "IdentitasPengembangan" in b.read_text(encoding="utf-8")
    ]
    assert not tersangka, tersangka


def test_kode_peran_tak_dikenal_tidak_diterima() -> None:
    """Batasan tabel menjaga nilai peran; bila ia lolos juga, penentu sesi
    menolak alih-alih menebak peran."""
    from dataclasses import replace

    ling = Lingkungan(replace(AKUN, peran="kepala"))
    pengenal = _jalankan(ling.sesi_baru())
    _tak_terautentikasi(ling.daftar(pengenal))  # type: ignore[arg-type]


def test_peran_tidak_pernah_jatuh_ke_pengguna() -> None:
    """M-9: penentu sesi tidak menyediakan peran bawaan."""
    hasil = _jalankan(PenentuSesi(AkunMemori(), sekarang=Jam()).identitas(_PermintaanTanpaKuki()))
    assert hasil is None


class _PermintaanTanpaKuki:
    cookies: ClassVar[dict[str, str]] = {}


def test_peran_valid_seluruhnya_dikenali() -> None:
    from dataclasses import replace

    for peran in Peran:
        ling = Lingkungan(replace(AKUN, peran=peran.value))
        pengenal = _jalankan(ling.sesi_baru())
        tanggapan = ling.daftar(pengenal)  # type: ignore[arg-type]
        assert tanggapan.status_code in (200, 403), (peran, tanggapan.text)  # type: ignore[attr-defined]
