"""Pemeriksaan API UK-05, UK-07, UK-14, UK-15 — T-5 fitur 042, R-03, R-04, R-05, P-3 A.

Terhadap **API yang berjalan**, dengan kuki sesi akun uji kepatuhan yang
dibuat operator (D-09 langkah 5). Penjalan tidak masuk, tidak keluar, dan
tidak memanggil rute yang mengubah data akun uji. Satu-satunya perubahan:
waktu aktif terakhir sesi akun uji — dinyatakan pada D-08 Bagian 8.

**Kewarasan lebih dulu.** Profil akun uji wajib terbaca. Tanpa itu alamat
yang salah menghasilkan 404 pada setiap rute dan terbaca "tidak terjangkau".

Daftar rute dibaca dari tabel D-14 Bagian 3 saat berjalan, sehingga rute baru
langsung diuji (D-14 AG-05). Badan permintaan kosong: rute yang lalai
memeriksa peran berhenti di validasi alih-alih mengubah data.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import httpx
from src.api.autentikasi import NAMA_KUKI

from perkakas.kepatuhan.basis_data import BASIS_DATA
from perkakas.kepatuhan.hasil import HasilUK, Keadaan, KonfigurasiApi, Konteks, gabung

ID_UJI: Final = "uji-kepatuhan"


_PERAN_TANPA_KUKI: Final = frozenset({"publik"})
_PERAN_PENGGUNA_BIASA: Final = frozenset({"publik", "semua", "pengguna"})
_BARIS_RUTE: Final = re.compile(r"^\| (GET|POST|PUT|PATCH|DELETE) \| `([^`]+)` \| ([a-z]+) \|")


def nik_rekaan() -> str:
    """Enam belas digit baru tiap putaran, berawal `00` — kode provinsi yang
    tidak ada, sehingga tidak mungkin NIK seseorang. Tidak ada nomor tetap pada
    kode (V-06), dan tanggapan yang menggemakan nomor lama tidak lolos."""
    return "00" + "".join(secrets.choice("0123456789") for _ in range(14))


@dataclass(frozen=True)
class Rute:
    metode: str
    jalur: str
    peran: str

    def nyata(self) -> str:
        return re.sub(r"\{[^}]+\}", ID_UJI, self.jalur)


def rute_d14(akar_repo: Path) -> tuple[Rute, ...]:
    """Tabel D-14 Bagian 3."""
    teks = (akar_repo / "docs" / "D14.md").read_text(encoding="utf-8")
    bagian = teks.split("## 3. Peta Rute", 1)[1].split("\n## 4.", 1)[0]
    return tuple(
        Rute(m.group(1), m.group(2), m.group(3))
        for b in bagian.splitlines()
        if (m := _BARIS_RUTE.match(b))
    )


def _belum(kode: str) -> HasilUK:
    return HasilUK(
        kode,
        Keadaan.BELUM,
        ("KEPATUHAN_API, KEPATUHAN_AKUN, atau KEPATUHAN_KUKI tidak diberikan",),
    )


def _klien(api: KonfigurasiApi) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=api.alamat, timeout=15, follow_redirects=False)


async def _profil(klien: httpx.AsyncClient, api: KonfigurasiApi) -> dict[str, object] | None:
    try:
        t = await klien.get("/api/v1/saya/profil", headers=_kuki(api))
        profil = t.json() if t.status_code == 200 else None
    except (httpx.HTTPError, ValueError):
        profil = None
    return profil if isinstance(profil, dict) else None


def _kuki(api: KonfigurasiApi) -> dict[str, str]:
    return {"Cookie": f"{NAMA_KUKI}={api.kuki}"}


def _tak_waras(kode: str) -> HasilUK:
    return HasilUK(kode, Keadaan.GAGAL, ("kewarasan: profil akun uji tidak terbaca",))


async def _rute(kode: str, konteks: Konteks, dengan_kuki: bool) -> HasilUK:
    api = konteks.api
    if api is None:
        return _belum(kode)
    async with _klien(api) as klien:
        profil = await _profil(klien, api)
        if profil is None:
            return _tak_waras(kode)
        diharapkan = 403 if dengan_kuki else 401
        dikecualikan = _PERAN_PENGGUNA_BIASA if dengan_kuki else _PERAN_TANPA_KUKI
        bagian: list[HasilUK] = []
        for r in rute_d14(konteks.akar_repo):
            if r.peran in dikecualikan:
                continue
            t = await klien.request(r.metode, r.nyata(), headers=_kuki(api) if dengan_kuki else {})
            uraian = f"{r.metode} {r.jalur} ({r.peran}) — HTTP {t.status_code}"
            if t.status_code == diharapkan:
                bagian.append(HasilUK("", Keadaan.LULUS, (uraian,)))
            elif t.status_code == 404:
                bagian.append(HasilUK("", Keadaan.LULUS, (f"{uraian}, rute tidak terpasang",)))
            else:
                bagian.append(HasilUK("", Keadaan.GAGAL, (f"{uraian}, diharapkan {diharapkan}",)))
    return gabung(kode, bagian)


async def periksa_uk07(konteks: Konteks) -> HasilUK:
    """Kendali akses di lapisan API: rute non-publik menolak tanpa sesi."""
    return await _rute("UK-07", konteks, dengan_kuki=False)


async def periksa_uk15(konteks: Konteks) -> HasilUK:
    """Pengguna biasa tidak menjangkau rute kurator, anotator, analitik."""
    return await _rute("UK-15", konteks, dengan_kuki=True)


async def periksa_uk14(konteks: Konteks) -> HasilUK:
    """Data pribadi yang diketik pengguna tidak keluar kembali — TK-68, KM-03."""
    api = konteks.api
    if api is None:
        return _belum("UK-14")
    async with _klien(api) as klien:
        profil = await _profil(klien, api)
        if profil is None:
            return _tak_waras("UK-14")
        nik = nik_rekaan()
        t = await klien.post(
            "/api/v1/tanya",
            headers=_kuki(api),
            json={"pertanyaan": f"Uji kepatuhan: NIK saya {nik}, bagaimana izinnya?"},
        )
    ditolak = 400 <= t.status_code < 500
    bergema = nik in t.text
    uraian = f"POST /api/v1/tanya berpola NIK rekaan — HTTP {t.status_code}"
    if ditolak and not bergema:
        return HasilUK("UK-14", Keadaan.LULUS, (f"{uraian}, tanpa gema",))
    sebab = "nomor tergema" if bergema else "tidak ditolak"
    return HasilUK("UK-14", Keadaan.GAGAL, (f"{uraian}, {sebab}",))


async def _satu(konteks: Konteks, peran: str, kueri: str, *argumen: object) -> object:
    sambungan = await konteks.buka(peran, BASIS_DATA)
    try:
        return await sambungan.fetchval(kueri, *argumen)
    finally:
        await sambungan.close()


async def periksa_uk05(konteks: Konteks) -> HasilUK:
    """Telemetri tidak merekam tanpa persetujuan — C-04, FR-J05."""
    api = konteks.api
    if api is None:
        return _belum("UK-05")
    async with _klien(api) as klien:
        profil = await _profil(klien, api)
        if profil is None:
            return _tak_waras("UK-05")
        if profil.get("persetujuan") == "diberikan":
            return HasilUK(
                "UK-05", Keadaan.BELUM, ("akun uji memiliki persetujuan penelitian aktif",)
            )
        pseudonim = await _satu(
            konteks,
            "peran_autentikasi",
            "SELECT pseudonim FROM akun.pengguna WHERE id = $1",
            api.akun,
        )
        if pseudonim is None:
            return HasilUK("UK-05", Keadaan.GAGAL, (f"akun {api.akun} tidak dikenal peladen",))
        hitung = "SELECT count(*) FROM telemetri.peristiwa WHERE pseudonim = $1"
        sebelum = await _satu(konteks, "peran_analitik", hitung, pseudonim)
        sambungan = await konteks.buka("peran_pembaca_sumber", BASIS_DATA)
        try:
            calon = [
                (b["id_dokumen"], b["penanda_bagian"])
                for b in await sambungan.fetch(
                    "SELECT DISTINCT ON (id_dokumen) id_dokumen, penanda_bagian "
                    "FROM indeks_utama.segmen_teks ORDER BY id_dokumen, id_segmen LIMIT 20"
                )
            ]
        finally:
            await sambungan.close()
        dibuka = None
        for id_dokumen, bagian in calon:
            t = await klien.get(
                f"/api/v1/sumber/{id_dokumen}", params={"bagian": bagian}, headers=_kuki(api)
            )
            if t.status_code == 200:
                dibuka = id_dokumen
                break
        if dibuka is None:
            return HasilUK(
                "UK-05", Keadaan.BELUM, ("tidak ada sumber korpus yang dapat dibuka akun uji",)
            )
        sesudah = await _satu(konteks, "peran_analitik", hitung, pseudonim)
    uraian = f"GET /api/v1/sumber/{dibuka} — peristiwa akun uji {sebelum} lalu {sesudah}"
    keadaan = Keadaan.LULUS if sesudah == sebelum else Keadaan.GAGAL
    return HasilUK("UK-05", keadaan, (uraian,))
