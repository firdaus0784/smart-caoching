"""Turunan sandi — T-3 fitur 029, R-03, P-3, plan Bagian 4.

Sandi tidak pernah tersimpan maupun tercatat dalam bentuk asli. Yang disimpan
turunan `scrypt` bergaram per akun, dan pembandingannya berwaktu tetap.

## Parameter, dari sumber yang dibaca

OWASP *Password Storage Cheat Sheet* memuat lima baris parameter `scrypt` yang
dinyatakannya setara dalam pertahanan. Yang dipakai **N=2^15, r=8, p=3**:
memorinya seperempat baris pertama per percobaan masuk, sehingga percobaan
masuk bersamaan — termasuk dari penyerang — tidak menghabiskan memori peladen
(KB-152, Gerbang 2 KB-153).

## Batas memori ditetapkan tegas

`hashlib.scrypt` pada OpenSSL 3 menolak parameter itu dengan `memory limit
exceeded` bila `maxmem` tidak diisi: batas bawaannya 32 MiB, dan kebutuhan
N=2^15 r=8 melampauinya sedikit. Batasnya karena itu dihitung dari rumus
kebutuhan OpenSSL sendiri, bukan ditebak.

## Parameter tinggal di dalam turunan

`scrypt$N$r$p$garam$turunan`. Menaikkan parameter kelak tidak membuat sandi
lama tidak dapat diperiksa; yang lama diperiksa dengan parameternya sendiri.

## Sandi dibangkitkan, tidak dipilih

D-14 Bagian 3 tidak memuat rute ganti sandi, sehingga pengguna tidak pernah
memilih sandinya sendiri. Perkakas tim membangkitkannya: 16 karakter dari 31
huruf kecil dan angka yang tidak mudah tertukar, sekitar 79 bit — melampaui
batas 15 karakter yang OWASP *Authentication Cheat Sheet* sebut bagi sandi
tanpa autentikasi multifaktor.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Final

from pydantic import BaseModel, ConfigDict, Field


class ParameterScrypt(BaseModel):
    """Tiga parameter `scrypt` — biaya memori, ukuran blok, paralelisme."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    n: int = Field(gt=1)
    r: int = Field(gt=0)
    p: int = Field(gt=0)


PARAMETER: Final = ParameterScrypt(n=2**15, r=8, p=3)
"""OWASP baris ketiga — P-4, KB-153."""

PANJANG_GARAM: Final = 16
"""Bita. Sumber yang dibaca tidak menyebut panjangnya — penetapan tim tanpa
dasar literatur (SI-01 pilihan kedua)."""

PANJANG_TURUNAN: Final = 32

BATAS_PANJANG_SANDI: Final = 128
"""Diperiksa **sebelum** turunan dijalankan: sandi sangat panjang adalah jalan
penolakan layanan yang OWASP sebut sendiri."""

ALFABET_SANDI: Final = "23456789abcdefghjkmnpqrstuvwxyz"
"""31 simbol: angka 2 sampai 9 dan huruf kecil tanpa `i l o` — yang tertukar dengan
`1` dan `0`. Huruf besar tidak dipakai sama sekali, sehingga `O` dan `I` pun
tidak ada."""

_KELOMPOK: Final = 4
_JUMLAH_KELOMPOK: Final = 4
_NAMA: Final = "scrypt"


class SandiTidakSah(ValueError):
    """Sandi masukan ditolak sebelum diturunkan — terlalu panjang."""


def bangkitkan_sandi() -> str:
    """Sandi awal bagi akun baru, berkelompok `xxxx-xxxx-xxxx-xxxx`."""
    huruf = "".join(secrets.choice(ALFABET_SANDI) for _ in range(_KELOMPOK * _JUMLAH_KELOMPOK))
    return "-".join(huruf[i : i + _KELOMPOK] for i in range(0, len(huruf), _KELOMPOK))


def turunkan(sandi: str, *, parameter: ParameterScrypt = PARAMETER) -> str:
    """Turunan bergaram baru, berbentuk `scrypt$N$r$p$garam$turunan`."""
    garam = secrets.token_bytes(PANJANG_GARAM)
    turunan = _scrypt(sandi, garam, parameter)
    return "$".join(
        (
            _NAMA,
            str(parameter.n),
            str(parameter.r),
            str(parameter.p),
            _b64(garam),
            _b64(turunan),
        )
    )


def cocok(sandi: str, tersimpan: str) -> bool:
    """Apakah `sandi` cocok dengan turunan tersimpan — berwaktu tetap.

    Turunan tersimpan yang rusak melempar `ValueError`: itu kerusakan data,
    bukan sandi salah, dan tidak boleh terbaca sebagai penolakan biasa.
    """
    parameter, garam, harapan = _urai(tersimpan)
    return hmac.compare_digest(_scrypt(sandi, garam, parameter), harapan)


def _scrypt(sandi: str, garam: bytes, parameter: ParameterScrypt) -> bytes:
    if len(sandi) > BATAS_PANJANG_SANDI:
        raise SandiTidakSah("sandi melampaui batas panjang")
    bersih = sandi.replace("-", "")
    return hashlib.scrypt(
        bersih.encode("utf-8"),
        salt=garam,
        n=parameter.n,
        r=parameter.r,
        p=parameter.p,
        maxmem=_batas_memori(parameter),
        dklen=PANJANG_TURUNAN,
    )


def _batas_memori(parameter: ParameterScrypt) -> int:
    """Rumus kebutuhan OpenSSL — `128·r·(N+2)` bagi V ditambah `128·r·p` bagi B
    — dengan satu MiB kelonggaran."""
    return 128 * parameter.r * (parameter.n + 2 + parameter.p) + 1024 * 1024


def _urai(tersimpan: str) -> tuple[ParameterScrypt, bytes, bytes]:
    bagian = tersimpan.split("$")
    if len(bagian) != 6 or bagian[0] != _NAMA:
        raise ValueError("turunan sandi tersimpan tidak dikenali")
    try:
        parameter = ParameterScrypt(n=int(bagian[1]), r=int(bagian[2]), p=int(bagian[3]))
        return parameter, _dari_b64(bagian[4]), _dari_b64(bagian[5])
    except ValueError as galat:
        raise ValueError("turunan sandi tersimpan rusak") from galat


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _dari_b64(teks: str) -> bytes:
    return base64.urlsafe_b64decode(teks + "=" * (-len(teks) % 4))
