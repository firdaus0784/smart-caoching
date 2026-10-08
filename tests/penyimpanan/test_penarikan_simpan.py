"""Penghapusan penarikan data — T-5 fitur 033, R-02, R-03, R-04, R-09; K-1.

Terhadap PostgreSQL sungguhan, dengan **kedua peran perkakas** — bukan
pengelola. Dua pengguna berdata pada sepuluh tabel dan pada pemetaan
pseudonim; sesudah permintaan yang satu dipenuhi, setiap tempat kosong
darinya dan utuh bagi yang lain.

Data uji dimasukkan pengelola dengan pemicu kunci asing dimatikan sesaat
(`session_replication_role`): butir hari ini dan "belum relevan" merujuk butir
tayang, dan rantai kurasi lengkap tidak menambah apa pun pada yang diuji di
sini — penghapusan anak tidak menuntut induknya.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from src.penyimpanan.akun import PERAN_AUTENTIKASI, AkunPostgres
from src.penyimpanan.penarikan import (
    PERAN_PENARIKAN,
    PERAN_PENARIKAN_PSEUDONIM,
    TABEL_DATA_PENGGUNA,
    PenarikanPostgres,
)
from tests.konftes_asinkron import jalankan
from tests.peladen import HOST, PORT, siapkan

siapkan()

T0 = datetime(2026, 10, 6, 1, 0, tzinfo=UTC)
PENGELOLA = "pengelola"


class Sambungan:
    """Satu sambungan baru per kueri, sebagai satu peran pada satu basis data."""

    def __init__(self, peran: str, basis_data: str = "smart_coaching") -> None:
        self._peran, self._basis = peran, basis_data

    async def _dengan(self, nama: str, kueri: str, *argumen: object) -> Any:
        import asyncpg

        sambungan = await asyncpg.connect(
            host=HOST, port=int(PORT), user=self._peran, database=self._basis
        )
        try:
            return await getattr(sambungan, nama)(kueri, *argumen)
        finally:
            await sambungan.close()

    async def fetchrow(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetchrow", kueri, *argumen)

    async def fetch(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("fetch", kueri, *argumen)

    async def execute(self, kueri: str, *argumen: object) -> Any:
        return await self._dengan("execute", kueri, *argumen)


def _psd() -> str:
    return "psd_" + "".join(secrets.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(16))


def _id_akun() -> str:
    return "".join(secrets.choice("abcdefghjkmnpqrstuvwxyz") for _ in range(6)) + (
        f"-{secrets.randbelow(1000):03d}"
    )


async def _isi(psd: str) -> str:
    """Satu baris pada tiap tabel data pengguna dan pada pemetaan."""
    import asyncpg

    id_akun = _id_akun()
    percakapan = uuid.uuid4()
    s = await asyncpg.connect(host=HOST, port=int(PORT), user=PENGELOLA, database="smart_coaching")
    try:
        await s.execute("SET session_replication_role = replica")
        for kueri, argumen in (
            (
                "INSERT INTO akun.pengguna (id, pseudonim, peran, tanggal_dibuat, turunan_sandi) "
                "VALUES ($1, $2, 'pengguna', $3, 'scrypt$16$8$1$AAAA$AAAA')",
                (id_akun, psd, T0),
            ),
            (
                "INSERT INTO akun.sesi (turunan_pengenal, id_pengguna, dibuat_pada, "
                "terakhir_aktif, kedaluwarsa_pada) VALUES ($1, $2, $3, $3, $4)",
                (secrets.token_bytes(32), id_akun, T0, T0 + timedelta(hours=8)),
            ),
            (
                "INSERT INTO pengguna.profil_sekolah (id_pengguna, jabatan, masa_kerja, "
                "jumlah_rombel, jumlah_ptk, jalur_akreditasi, wilayah) "
                "VALUES ($1, 'Kepala Sekolah', 3, 6, 9, 'visitasi', 'Kabupaten Contoh')",
                (psd,),
            ),
            (
                "INSERT INTO pengguna.prioritas_manajerial (id_pengguna, kategori, "
                "ditetapkan_pada) VALUES ($1, ARRAY['K1','K2','K3'], $2)",
                (psd, T0),
            ),
            (
                "INSERT INTO pengguna.persetujuan (id_pengguna, jenis, versi_naskah, "
                "disetujui, tanggal) VALUES ($1, 'penelitian', 'uji', true, $2)",
                (psd, T0),
            ),
            (
                "INSERT INTO riwayat.percakapan (id_percakapan, pemilik, dibuat_pada) "
                "VALUES ($1, $2, $3)",
                (percakapan, psd, T0),
            ),
            (
                "INSERT INTO riwayat.giliran (id_percakapan, pertanyaan, id_pesan, waktu) "
                "VALUES ($1, 'Bagaimana menyusun jadwal supervisi?', 'p1', $2)",
                (percakapan, T0),
            ),
            (
                "INSERT INTO penemuan.tayang_harian (id_pengguna, tanggal, id_butir, urutan, "
                "ditayangkan_pada) VALUES ($1, $2, 'b-uji-033', 1, $3)",
                (psd, T0.date(), T0),
            ),
            (
                "INSERT INTO penemuan.belum_relevan (id_pengguna, id_butir, alasan, waktu) "
                "VALUES ($1, 'b-uji-033', 'Belum menjadi fokus', $2)",
                (psd, T0),
            ),
            (
                "INSERT INTO telemetri.peristiwa (pseudonim, jenis, waktu, properti, "
                "versi_aplikasi, versi_model) "
                "VALUES ($1, 'session_start', $2, '{}', 'uji', 'tanpa_model')",
                (psd, T0),
            ),
        ):
            await s.execute(kueri, *argumen)
        # Fitur 036: tanggapan, penilaian, aduan beserta penanda gugur dan
        # tindak lanjutnya. Penanda berpseudonim pada isinya, agar hitungan
        # tidak bergantung pada induk yang ikut terhapus (M-11).
        await s.execute(
            "INSERT INTO riwayat.pesan (id_pesan, id_percakapan, tanggapan, waktu) "
            "VALUES ($1, $2, $3::jsonb, $4)",
            f"msg_{psd}",
            percakapan,
            f'{{"id_pesan": "msg_{psd}", "versi": {{"model": "m"}}}}',
            T0,
        )
        nomor_penilaian = await s.fetchval(
            "INSERT INTO riwayat.penilaian (id_pesan, nilai, alasan, kirim_ke_kurator, waktu) "
            "VALUES ($1, 'keliru', $2, true, $3) RETURNING nomor",
            f"msg_{psd}",
            f"Alasan {psd}",
            T0,
        )
        nomor_aduan = await s.fetchval(
            "INSERT INTO kurasi.aduan (nomor_penilaian, pertanyaan, tanggapan, alasan, "
            'diadukan_pada) VALUES ($1, $2, \'{"status_dasar": "kuat"}\', null, $3) '
            "RETURNING nomor",
            nomor_penilaian,
            f"Pertanyaan {psd}",
            T0,
        )
        await s.execute(
            "INSERT INTO kurasi.aduan_digantikan (nomor_aduan, waktu) VALUES ($1, $2)",
            nomor_aduan,
            T0,
        )
        await s.execute(
            "INSERT INTO kurasi.tindak_lanjut_aduan (nomor_aduan, tindak_lanjut, catatan, "
            "peran, pseudonim_kurator, waktu) "
            "VALUES ($1, 'jawaban_sesuai_dasar', $2, 'kurator', 'psd_kkkkkkkkkkkkkkkk', $3)",
            nomor_aduan,
            f"Catatan {psd}",
            T0,
        )
    finally:
        await s.close()
    await Sambungan(PENGELOLA, "smart_coaching_pseudonim").execute(
        "INSERT INTO pseudonim.peta_pseudonim (id_pengguna, pseudonim) VALUES ($1, $2)",
        id_akun,
        psd,
    )
    return id_akun


_HITUNG: dict[str, str] = {
    "akun.pengguna": "SELECT count(*) FROM akun.pengguna WHERE pseudonim = $1",
    "akun.sesi": "SELECT count(*) FROM akun.sesi WHERE id_pengguna = $2 AND $1::text <> ''",
    "pengguna.profil_sekolah": "SELECT count(*) FROM pengguna.profil_sekolah WHERE id_pengguna = $1",
    "pengguna.prioritas_manajerial": (
        "SELECT count(*) FROM pengguna.prioritas_manajerial WHERE id_pengguna = $1"
    ),
    "pengguna.persetujuan": "SELECT count(*) FROM pengguna.persetujuan WHERE id_pengguna = $1",
    "riwayat.percakapan": "SELECT count(*) FROM riwayat.percakapan WHERE pemilik = $1",
    "riwayat.giliran": (
        "SELECT count(*) FROM riwayat.giliran g JOIN riwayat.percakapan p "
        "USING (id_percakapan) WHERE p.pemilik = $1"
    ),
    "penemuan.tayang_harian": "SELECT count(*) FROM penemuan.tayang_harian WHERE id_pengguna = $1",
    "penemuan.belum_relevan": "SELECT count(*) FROM penemuan.belum_relevan WHERE id_pengguna = $1",
    "telemetri.peristiwa": "SELECT count(*) FROM telemetri.peristiwa WHERE pseudonim = $1",
    "riwayat.pesan": "SELECT count(*) FROM riwayat.pesan WHERE id_pesan = 'msg_' || $1",
    "riwayat.penilaian": "SELECT count(*) FROM riwayat.penilaian WHERE alasan = 'Alasan ' || $1",
    "kurasi.aduan": "SELECT count(*) FROM kurasi.aduan WHERE pertanyaan = 'Pertanyaan ' || $1",
    "kurasi.aduan_digantikan": (
        "SELECT count(*) FROM kurasi.aduan_digantikan d JOIN kurasi.aduan a "
        "ON a.nomor = d.nomor_aduan WHERE a.pertanyaan = 'Pertanyaan ' || $1"
    ),
    "kurasi.tindak_lanjut_aduan": (
        "SELECT count(*) FROM kurasi.tindak_lanjut_aduan WHERE catatan = 'Catatan ' || $1"
    ),
}


async def _jumlah(psd: str, id_akun: str) -> dict[str, int]:
    s = Sambungan(PENGELOLA)
    hasil: dict[str, int] = {}
    for tabel, kueri in _HITUNG.items():
        argumen = (psd, id_akun) if "$2" in kueri else (psd,)
        b = await s.fetchrow(kueri, *argumen)
        hasil[tabel] = int(b[0])
    peta = await Sambungan(PENGELOLA, "smart_coaching_pseudonim").fetchrow(
        "SELECT count(*) FROM pseudonim.peta_pseudonim WHERE pseudonim = $1", psd
    )
    hasil["pseudonim.peta_pseudonim"] = int(peta[0])
    return hasil


def _penarikan() -> PenarikanPostgres:
    return PenarikanPostgres(
        Sambungan(PERAN_PENARIKAN),  # type: ignore[arg-type]
        Sambungan(PERAN_PENARIKAN_PSEUDONIM, "smart_coaching_pseudonim"),  # type: ignore[arg-type]
    )


async def _minta(psd: str, kini: datetime = T0) -> int:
    await AkunPostgres(Sambungan(PERAN_AUTENTIKASI)).catat_penarikan(  # type: ignore[arg-type]
        psd, sekarang=kini
    )
    b = await Sambungan(PENGELOLA).fetchrow(
        "SELECT nomor FROM akun.permintaan_penarikan WHERE pseudonim = $1", psd
    )
    return int(b[0])


def test_lima_belas_tabel_terdaftar() -> None:
    """Sepuluh tabel fitur 033, ditambah lima tabel fitur 036 (R-07)."""
    assert set(TABEL_DATA_PENGGUNA) == set(_HITUNG)
    assert len(TABEL_DATA_PENGGUNA) == 15


def test_satu_kosong_satu_utuh_dan_bukti_tanpa_pseudonim() -> None:
    """R-02 dan R-03. M-3: tabel yang terlewat; M-4: tanpa saringan pemilik; M-5:
    pseudonim tertinggal pada bukti."""

    async def uji() -> None:
        a, b = _psd(), _psd()
        id_a, id_b = await _isi(a), await _isi(b)
        nomor = await _minta(a)
        tertunda = await _penarikan().tertunda()
        assert nomor in [p.nomor for p in tertunda]

        kini = T0 + timedelta(days=3)
        hasil = await _penarikan().jalankan(nomor, sekarang=kini)
        assert hasil is not None
        assert hasil.nomor == nomor
        assert hasil.pemetaan == 1
        assert hasil.jumlah_baris == {t: 1 for t in TABEL_DATA_PENGGUNA}

        assert set((await _jumlah(a, id_a)).values()) == {0}
        assert set((await _jumlah(b, id_b)).values()) == {1}

        bukti = await Sambungan(PENGELOLA).fetchrow(
            "SELECT pseudonim, diminta_pada, dipenuhi_pada, jumlah_baris "
            "FROM akun.permintaan_penarikan WHERE nomor = $1",
            nomor,
        )
        assert bukti["pseudonim"] is None
        assert (bukti["diminta_pada"], bukti["dipenuhi_pada"]) == (T0, kini)
        import json

        assert json.loads(bukti["jumlah_baris"]) == {t: 1 for t in TABEL_DATA_PENGGUNA}
        assert nomor not in [p.nomor for p in await _penarikan().tertunda()]

    jalankan(uji())


def test_menjalankan_ulang_tidak_melakukan_apa_pun() -> None:
    async def uji() -> None:
        a = _psd()
        await _isi(a)
        nomor = await _minta(a)
        assert await _penarikan().jalankan(nomor, sekarang=T0) is not None
        assert await _penarikan().jalankan(nomor, sekarang=T0) is None
        assert await _penarikan().jalankan(10**12, sekarang=T0) is None

    jalankan(uji())


def test_tertunda_terlama_lebih_dulu_beserta_waktunya() -> None:
    async def uji() -> None:
        a, b = _psd(), _psd()
        await _isi(a)
        await _isi(b)
        lama = await _minta(a, T0 - timedelta(days=20))
        baru = await _minta(b, T0)
        daftar = [p for p in await _penarikan().tertunda() if p.nomor in (lama, baru)]
        assert [(p.nomor, p.diminta_pada) for p in daftar] == [
            (lama, T0 - timedelta(days=20)),
            (baru, T0),
        ]
        assert not any(hasattr(p, "pseudonim") for p in daftar)

    jalankan(uji())


def test_waktu_tanpa_zona_ditolak() -> None:
    with pytest.raises(ValueError):
        jalankan(_penarikan().jalankan(1, sekarang=T0.replace(tzinfo=None)))


class _DidahuluiProsesLain(Sambungan):
    """Perkakas kedua memenuhi permintaan yang sama tepat sebelum pernyataan
    penghapusan perkakas ini berjalan."""

    def __init__(self, nomor: int) -> None:
        super().__init__(PERAN_PENARIKAN)
        self._nomor = nomor

    async def fetchrow(self, kueri: str, *argumen: object) -> Any:
        # Dikenali dari isinya, bukan kata pembukanya: urutan CTE berubah
        # ketika tabel bertambah (fitur 036).
        if "DELETE FROM telemetri.peristiwa" in kueri:
            await Sambungan(PERAN_PENARIKAN).execute(
                "UPDATE akun.permintaan_penarikan SET pseudonim = NULL, dipenuhi_pada = $2, "
                "jumlah_baris = '{}' WHERE nomor = $1",
                self._nomor,
                T0,
            )
        return await super().fetchrow(kueri, *argumen)


def test_permintaan_yang_didahului_proses_lain_tidak_dilaporkan_dipenuhi() -> None:
    """Dua perkakas bersamaan: yang terlambat tidak menimpa bukti yang sudah ada."""

    async def uji() -> None:
        a = _psd()
        await _isi(a)
        nomor = await _minta(a)
        terlambat = PenarikanPostgres(
            _DidahuluiProsesLain(nomor),  # type: ignore[arg-type]
            Sambungan(PERAN_PENARIKAN_PSEUDONIM, "smart_coaching_pseudonim"),  # type: ignore[arg-type]
        )
        assert await terlambat.jalankan(nomor, sekarang=T0 + timedelta(days=1)) is None
        bukti = await Sambungan(PENGELOLA).fetchrow(
            "SELECT dipenuhi_pada, jumlah_baris FROM akun.permintaan_penarikan WHERE nomor = $1",
            nomor,
        )
        assert (bukti["dipenuhi_pada"], bukti["jumlah_baris"]) == (T0, "{}")

    jalankan(uji())
