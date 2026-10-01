"""Rute masuk dan keluar — T-6 fitur 029, R-01, R-03, R-04, R-06, R-09; K-3, K-4.

Bentuknya D-14 Bagian 4.4. Turunan sandi memakai parameter **murah** dan
pembanding yang **menghitung**: R-04 menuntut keempat penolakan menjalankan
tepat satu turunan, dan "tepat satu" hanya terlihat bila ada yang menghitung.
Waktu tanggap tidak diukur dengan jam dinding — uji seperti itu rapuh dan
lulus secara kebetulan.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import threading
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from src.api import sandi
from src.api.aplikasi import susun_aplikasi
from src.api.autentikasi import (
    AMBANG_PENAHANAN,
    LAMA_PENAHANAN,
    NAMA_KUKI,
    PESAN_MASUK_DITOLAK,
    PESAN_MASUK_TIDAK_LENGKAP,
    PenentuSesi,
    PenjagaMasuk,
)
from src.api.galat import LOG_OPERASIONAL
from src.api.tanya import HasilTanya
from src.llm.galat import kalimat_terlalu_panjang
from src.penyimpanan.akun import AkunMemori, BarisAkun
from src.penyimpanan.riwayat import RiwayatMemori
from tests.api.test_aplikasi import ID_PERCAKAPAN, JalurPalsu, _tanggapan
from tests.konftes_asinkron import jalankan

MURAH = sandi.ParameterScrypt(n=2**4, r=8, p=1)
SANDI = "abcd-efgh-jkmn-pqrs"
T0 = datetime(2026, 10, 1, 7, 0, tzinfo=UTC)

AKUN = BarisAkun(
    id="ks-017",
    pseudonim="psd_abcdefghjkmnpqrs",
    peran="pengguna",
    status_aktif=True,
    turunan_sandi=sandi.turunkan(SANDI, parameter=MURAH),
    gagal_beruntun=0,
    ditahan_sampai=None,
)


class Jam:
    def __init__(self) -> None:
        self.kini = T0

    def __call__(self) -> datetime:
        return self.kini


class Pembanding:
    """`sandi.cocok` yang menghitung panggilannya."""

    def __init__(self) -> None:
        self.jumlah = 0

    def __call__(self, masukan: str, tersimpan: str) -> bool:
        self.jumlah += 1
        return sandi.cocok(masukan, tersimpan)


class Lingkungan:
    def __init__(self, *akun: BarisAkun) -> None:
        self.jam = Jam()
        self.akun = AkunMemori()
        for a in akun or (AKUN,):
            self.akun.pasang_akun(a)
        self.pembanding = Pembanding()
        self.jalur = JalurPalsu(HasilTanya(tanggapan=_tanggapan()))
        self.penjaga = PenjagaMasuk(
            self.akun,
            sekarang=self.jam,
            cocok=self.pembanding,
            turunan_tiruan=sandi.turunkan("tiruan", parameter=MURAH),
        )
        self.klien = TestClient(
            susun_aplikasi(
                jalur=self.jalur,
                identitas=PenentuSesi(self.akun, sekarang=self.jam),
                riwayat=RiwayatMemori(),
                masuk=self.penjaga,
                sekarang=self.jam,
            ),
            base_url="https://testserver",
        )

    def masuk(self, nama: str = AKUN.id, kata: str = SANDI, **lain: object) -> object:
        tanggapan = self.klien.post(
            "/api/v1/auth/masuk", json={"nama_pengguna": nama, "sandi": kata}, **lain
        )
        # Kuki dikirim tegas oleh tiap uji, bukan oleh wadah kuki klien: uji
        # yang lulus karena kuki tersimpan diam-diam tidak menguji pengirimnya.
        self.klien.cookies.clear()
        return tanggapan

    def daftar(self, kuki: str) -> object:
        return self.klien.get("/api/v1/percakapan", headers={"Cookie": f"{NAMA_KUKI}={kuki}"})


def _kuki(tanggapan: object) -> str:
    baris = tanggapan.headers.get("set-cookie", "")  # type: ignore[attr-defined]
    assert baris.startswith(f"{NAMA_KUKI}="), baris
    return baris.split(";", 1)[0].split("=", 1)[1]


def _bagian_kuki(tanggapan: object) -> set[str]:
    baris = tanggapan.headers["set-cookie"]  # type: ignore[attr-defined]
    return {b.strip().lower() for b in baris.split(";")[1:]}


# ── masuk berhasil ──────────────────────────────────────────────────


def test_masuk_berhasil_204_tanpa_badan_dengan_kuki_sesi() -> None:
    ling = Lingkungan()
    tanggapan = ling.masuk()
    assert tanggapan.status_code == 204, tanggapan.text  # type: ignore[attr-defined]
    assert tanggapan.content == b""  # type: ignore[attr-defined]
    kuki = _kuki(tanggapan)
    assert len(kuki) >= 43  # 256 bit acak
    assert ling.daftar(kuki).status_code == 200  # type: ignore[attr-defined]


def test_atribut_kuki_sesi() -> None:
    """M-5, M-6 — contoh OWASP kata demi kata, ditambah masa yang sama dengan
    masa sesi di peladen."""
    bagian = _bagian_kuki(Lingkungan().masuk())
    assert {"httponly", "secure", "samesite=strict", "path=/", "max-age=28800"} <= bagian
    assert not any(b.startswith("domain") for b in bagian)


def test_dua_kali_masuk_dua_pengenal_berbeda() -> None:
    ling = Lingkungan()
    assert _kuki(ling.masuk()) != _kuki(ling.masuk())


def test_masuk_mencabut_sesi_lama_pada_kuki_yang_sama() -> None:
    ling = Lingkungan()
    lama = _kuki(ling.masuk())
    baru = _kuki(ling.masuk(headers={"Cookie": f"{NAMA_KUKI}={lama}"}))
    assert ling.daftar(lama).status_code == 401  # type: ignore[attr-defined]
    assert ling.daftar(baru).status_code == 200  # type: ignore[attr-defined]


def test_tanda_hubung_sandi_boleh_dilewatkan() -> None:
    assert Lingkungan().masuk(kata=SANDI.replace("-", "")).status_code == 204  # type: ignore[attr-defined]


# ── R-04 · empat penolakan yang sama ────────────────────────────────


def _penolakan(ling: Lingkungan, **masuk: object) -> tuple[int, dict[str, str], bool, int]:
    sebelum = ling.pembanding.jumlah
    tanggapan = ling.masuk(**masuk)  # type: ignore[arg-type]
    galat = tanggapan.json()["galat"]  # type: ignore[attr-defined]
    return (
        tanggapan.status_code,  # type: ignore[attr-defined]
        {k: v for k, v in galat.items() if k != "id_jejak"},
        "set-cookie" in tanggapan.headers,  # type: ignore[attr-defined]
        ling.pembanding.jumlah - sebelum,
    )


def test_empat_penolakan_sama_persis_dan_satu_turunan_masing_masing() -> None:
    """M-1: akun tak ada tanpa turunan dijawab dalam milidetik — terbaca."""
    ditahan = replace(
        AKUN,
        id="ks-018",
        pseudonim="psd_bbbbbbbbbbbbbbbb",
        ditahan_sampai=T0 + timedelta(minutes=5),
    )
    nonaktif = replace(AKUN, id="ks-019", pseudonim="psd_cccccccccccccccc", status_aktif=False)
    ling = Lingkungan(AKUN, ditahan, nonaktif)
    hasil = [
        _penolakan(ling, nama="ks-999"),
        _penolakan(ling, kata="salah-salah-salah"),
        _penolakan(ling, nama=ditahan.id),  # sandi BENAR, tetap ditolak
        _penolakan(ling, nama=nonaktif.id),  # sandi BENAR, tetap ditolak
    ]
    harapan = (
        401,
        {"kode": "TIDAK_TERAUTENTIKASI", "pesan_pengguna": PESAN_MASUK_DITOLAK},
        False,
        1,
    )
    assert hasil == [harapan] * 4


def test_nama_pengguna_berbentuk_aneh_tetap_satu_turunan() -> None:
    ling = Lingkungan()
    for nama in ("Budi Santoso", "3201010101010001", "a" * 64):
        assert _penolakan(ling, nama=nama)[0::3] == (401, 1)


# ── penahanan lewat rute ────────────────────────────────────────────


def test_penahanan_lewat_rute_lalu_berakhir() -> None:
    """M-2."""
    ling = Lingkungan()
    for _ in range(AMBANG_PENAHANAN):
        assert ling.masuk(kata="salah").status_code == 401  # type: ignore[attr-defined]
    assert ling.masuk().status_code == 401, "sandi benar selama ditahan diterima"  # type: ignore[attr-defined]
    ling.jam.kini = T0 + LAMA_PENAHANAN
    assert ling.masuk().status_code == 204  # type: ignore[attr-defined]


def test_masuk_berhasil_mengembalikan_penghitung() -> None:
    ling = Lingkungan()
    for _ in range(AMBANG_PENAHANAN - 1):
        ling.masuk(kata="salah")
    assert ling.masuk().status_code == 204  # type: ignore[attr-defined]
    for _ in range(AMBANG_PENAHANAN - 1):
        ling.masuk(kata="salah")
    assert ling.masuk().status_code == 204  # type: ignore[attr-defined]


# ── R-06 · keluar ───────────────────────────────────────────────────


def test_keluar_mencabut_di_peladen_bukan_hanya_kuki() -> None:
    """M-4: kuki lama yang disalin sebelum keluar ditolak sesudahnya."""
    ling = Lingkungan()
    kuki = _kuki(ling.masuk())
    tanggapan = ling.klien.post(
        "/api/v1/auth/keluar", json={}, headers={"Cookie": f"{NAMA_KUKI}={kuki}"}
    )
    assert tanggapan.status_code == 204
    assert tanggapan.content == b""
    bagian = _bagian_kuki(tanggapan)
    assert "max-age=0" in bagian or any(b.startswith("expires=") for b in bagian)
    assert ling.daftar(kuki).status_code == 401  # type: ignore[attr-defined]


def test_keluar_tanpa_sesi_401() -> None:
    tanggapan = Lingkungan().klien.post("/api/v1/auth/keluar", json={})
    assert tanggapan.status_code == 401
    assert tanggapan.json()["galat"]["kode"] == "TIDAK_TERAUTENTIKASI"


# ── K-4 · Content-Type ──────────────────────────────────────────────


def test_masuk_bukan_json_ditolak_tanpa_turunan() -> None:
    """M-12: formulir lintas situs tidak dapat mengirim `application/json`."""
    ling = Lingkungan()
    tanggapan = ling.klien.post(
        "/api/v1/auth/masuk", data={"nama_pengguna": AKUN.id, "sandi": SANDI}
    )
    assert tanggapan.status_code == 400
    assert tanggapan.json()["galat"]["kode"] == "VALIDASI_GAGAL"
    assert ling.pembanding.jumlah == 0


def test_keluar_bukan_json_ditolak_dan_sesi_tetap() -> None:
    ling = Lingkungan()
    kuki = _kuki(ling.masuk())
    tanggapan = ling.klien.post(
        "/api/v1/auth/keluar",
        content=b"",
        headers={"Cookie": f"{NAMA_KUKI}={kuki}", "Content-Type": "text/plain"},
    )
    assert tanggapan.status_code == 400
    assert ling.daftar(kuki).status_code == 200  # type: ignore[attr-defined]


def test_tanya_bukan_json_ditolak_tanpa_panggilan_jalur() -> None:
    ling = Lingkungan()
    kuki = _kuki(ling.masuk())
    tanggapan = ling.klien.post(
        "/api/v1/tanya",
        content=f'{{"pertanyaan": "Bagaimana supervisi?", "id_percakapan": "{ID_PERCAKAPAN}"}}',
        headers={"Cookie": f"{NAMA_KUKI}={kuki}", "Content-Type": "text/plain"},
    )
    assert tanggapan.status_code == 400
    assert ling.jalur.jumlah_panggilan == 0


def test_content_type_json_dengan_charset_diterima() -> None:
    ling = Lingkungan()
    tanggapan = ling.klien.post(
        "/api/v1/auth/masuk",
        content=f'{{"nama_pengguna": "{AKUN.id}", "sandi": "{SANDI}"}}',
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    assert tanggapan.status_code == 204


# ── badan masuk ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "badan",
    [
        {"nama_pengguna": AKUN.id},
        {"sandi": SANDI},
        {"nama_pengguna": AKUN.id, "sandi": SANDI, "peran": "admin"},
        {"nama_pengguna": "", "sandi": SANDI},
        {"nama_pengguna": AKUN.id, "sandi": ""},
        {"nama_pengguna": AKUN.id, "sandi": "a" * 129},
        {"nama_pengguna": "a" * 65, "sandi": SANDI},
        [],
    ],
)
def test_badan_cacat_400_tanpa_turunan(badan: object) -> None:
    ling = Lingkungan()
    tanggapan = ling.klien.post("/api/v1/auth/masuk", json=badan)
    assert tanggapan.status_code == 400
    galat = tanggapan.json()["galat"]
    assert (galat["kode"], galat["pesan_pengguna"]) == ("VALIDASI_GAGAL", PESAN_MASUK_TIDAK_LENGKAP)
    assert ling.pembanding.jumlah == 0


def test_badan_bukan_json_sah_400() -> None:
    ling = Lingkungan()
    tanggapan = ling.klien.post(
        "/api/v1/auth/masuk", content=b"{", headers={"Content-Type": "application/json"}
    )
    assert tanggapan.status_code == 400


def test_pesan_lolos_c13() -> None:
    for pesan in (PESAN_MASUK_DITOLAK, PESAN_MASUK_TIDAK_LENGKAP):
        assert not kalimat_terlalu_panjang(pesan), pesan


# ── R-09 · log ──────────────────────────────────────────────────────


def _seluruh_log(caplog: pytest.LogCaptureFixture) -> str:
    return "\n".join(f"{r.name} {r.getMessage()} {r.__dict__}" for r in caplog.records)


def test_log_tanpa_sandi_pengenal_maupun_nama_yang_diketik(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """M-13: orang sering mengetik sandinya pada isian nama pengguna."""
    ling = Lingkungan()
    with caplog.at_level(logging.DEBUG):
        ling.masuk(nama="sandi-tertukar-xyz", kata="rahasia-sekali-123")
        ling.masuk(kata="rahasia-sekali-456")
        kuki = _kuki(ling.masuk())
        ling.daftar(kuki)
        ling.klien.post("/api/v1/auth/keluar", json={}, headers={"Cookie": f"{NAMA_KUKI}={kuki}"})
    teks = _seluruh_log(caplog)
    for rahasia in (
        "sandi-tertukar-xyz",
        "rahasia-sekali-123",
        "rahasia-sekali-456",
        SANDI,
        kuki,
        hashlib.sha256(kuki.encode()).hexdigest(),
    ):
        assert rahasia not in teks, rahasia


def test_penahanan_akun_tercatat_dengan_id_akun(caplog: pytest.LogCaptureFixture) -> None:
    """OWASP: setiap penahanan dicatat dan ditinjau. `id` akun bukan data
    pribadi di bawah P-1 A; pseudonim tidak dicatat."""
    ling = Lingkungan()
    with caplog.at_level(logging.WARNING, logger=LOG_OPERASIONAL.name):
        for _ in range(AMBANG_PENAHANAN):
            ling.masuk(kata="salah")
    catatan = [r.getMessage() for r in caplog.records if "ditahan" in r.getMessage()]
    assert len(catatan) == 1, catatan
    assert AKUN.id in catatan[0]
    assert "trc_" in catatan[0]
    assert AKUN.pseudonim not in _seluruh_log(caplog)


# ── semafor turunan ─────────────────────────────────────────────────


def test_paling_banyak_dua_turunan_bersamaan() -> None:
    aktif = 0
    puncak = 0
    kunci = threading.Lock()

    def lambat(masukan: str, tersimpan: str) -> bool:
        nonlocal aktif, puncak
        with kunci:
            aktif += 1
            puncak = max(puncak, aktif)
        time.sleep(0.05)
        with kunci:
            aktif -= 1
        return False

    akun = AkunMemori()
    akun.pasang_akun(AKUN)
    penjaga = PenjagaMasuk(
        akun, sekarang=Jam(), cocok=lambat, turunan_tiruan=sandi.turunkan("t", parameter=MURAH)
    )

    async def uji() -> None:
        await asyncio.gather(*[penjaga.masuk(AKUN.id, "salah") for _ in range(6)])

    jalankan(uji())
    assert puncak == 2


def test_turunan_tiruan_bawaan_berparameter_sungguhan() -> None:
    """Akun tak ada diperiksa terhadap turunan berparameter yang SAMA dengan
    akun sungguhan; parameter yang lebih murah membuat waktunya terbaca."""
    penjaga = PenjagaMasuk(AkunMemori(), sekarang=Jam())
    assert penjaga.turunan_tiruan.split("$")[1:4] == [
        str(sandi.PARAMETER.n),
        str(sandi.PARAMETER.r),
        str(sandi.PARAMETER.p),
    ]


def test_rute_masuk_tidak_terpasang_tanpa_penjaga() -> None:
    """Titik jalan pengembangan tanpa autentikasi tidak memasang rute masuk
    yang tidak dapat berbuat apa pun."""
    from src.api.peran import Peran
    from tests.api.test_aplikasi import IdentitasTetap

    klien = TestClient(
        susun_aplikasi(
            jalur=JalurPalsu(HasilTanya(tanggapan=_tanggapan())),
            identitas=IdentitasTetap(Peran.PENGGUNA),
            riwayat=RiwayatMemori(),
        )
    )
    assert klien.post("/api/v1/auth/masuk", json={}).status_code in (404, 405)


def test_postgres_menyimpan_turunan_pengenal_bukan_pengenalnya() -> None:
    """M-3, lewat rute sungguhan dan peran produksi `peran_autentikasi`.

    Pembaca basis data tidak memperoleh sesi yang dapat dipakai: baris `sesi`
    memuat SHA-256 kuki, dan tidak ada baris yang memuat kukinya sendiri.
    """
    import secrets as acak

    from src.penyimpanan.akun import PERAN_AUTENTIKASI, AkunPostgres
    from tests.peladen import psql, siapkan
    from tests.penyimpanan.test_akun import SambunganPeran

    siapkan()
    huruf = "abcdefghjkmnpqrstuvwxyz"
    nama = "".join(acak.choice(huruf) for _ in range(6)) + f"-{acak.randbelow(1000):03d}"
    pseudonim = "psd_" + "".join(acak.choice(huruf) for _ in range(16))
    dibuat = psql(
        "smart_coaching",
        "-c",
        "insert into akun.pengguna (id, pseudonim, peran, tanggal_dibuat, turunan_sandi) "
        f"values ('{nama}', '{pseudonim}', 'pengguna', now(), '{AKUN.turunan_sandi}')",
        pengguna="peran_pengelola_akun",
    )
    assert dibuat.returncode == 0, dibuat.stderr

    akun = AkunPostgres(SambunganPeran(PERAN_AUTENTIKASI))  # type: ignore[arg-type]
    klien = TestClient(
        susun_aplikasi(
            jalur=JalurPalsu(HasilTanya(tanggapan=_tanggapan())),
            identitas=PenentuSesi(akun),
            riwayat=RiwayatMemori(),
            masuk=PenjagaMasuk(akun, turunan_tiruan=sandi.turunkan("t", parameter=MURAH)),
        ),
        base_url="https://testserver",
    )
    kuki = _kuki(klien.post("/api/v1/auth/masuk", json={"nama_pengguna": nama, "sandi": SANDI}))

    def hitung(syarat: str) -> str:
        hasil = psql("smart_coaching", "-c", f"select count(*) from akun.sesi where {syarat}")
        return hasil.stdout.strip()

    assert hitung(f"turunan_pengenal = sha256(convert_to('{kuki}', 'UTF8'))") == "1"
    assert hitung(f"turunan_pengenal = convert_to('{kuki}', 'UTF8')") == "0"
    assert hitung(f"encode(turunan_pengenal, 'escape') like '%{kuki[:16]}%'") == "0"


def test_masuk_text_plain_berisi_json_sah_tetap_ditolak() -> None:
    """Formulir lintas situs ber-`enctype="text/plain"` dapat menyusun badan
    yang JSON-nya sah. Tanpa syarat `Content-Type`, penyerang dapat
    memasukkan korban ke akun milik penyerang. Uji formulir di atas lulus juga
    tanpa syarat itu — badannya memang bukan JSON — sehingga uji ini yang
    menjaga syaratnya pada rute masuk (M-12)."""
    ling = Lingkungan()
    tanggapan = ling.klien.post(
        "/api/v1/auth/masuk",
        content=f'{{"nama_pengguna": "{AKUN.id}", "sandi": "{SANDI}"}}',
        headers={"Content-Type": "text/plain"},
    )
    assert tanggapan.status_code == 400
    assert "set-cookie" not in tanggapan.headers
    assert ling.pembanding.jumlah == 0
