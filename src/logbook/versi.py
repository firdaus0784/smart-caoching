"""Lima bidang versi wajib pada setiap catatan percobaan — R-11, R-12, C-09.

NFR-15 menjanjikan hasil dapat diulang, dan `docs/D10.md` Bagian 3 memerinci
apa yang membuat janji itu bermakna. Kelima bidang di bawah adalah yang
menyusun jejaknya.

Satu aturan yang mudah diabaikan dan mahal akibatnya: bidang yang belum
berlaku **diisi penanda** `belum-berlaku`, tidak dikosongkan. Bidang kosong
tidak dapat dibedakan antara "belum ada" dan "lupa dicatat", dan selisih itu
baru terasa pada Bulan 8 ketika bagian metode naskah disusun — saat tidak ada
lagi yang mengingat mana yang mana.

Pada fitur 001, tiga dari lima bidang memang belum berlaku: indeks belum
dibangun (fitur 006), skema anotasi belum dibekukan (fitur 003), dan
pembagian data belum ditetapkan (fitur 004, FR-D07).
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, field_validator

BELUM_BERLAKU: Final = "belum-berlaku"


class Versi(BaseModel, frozen=True, extra="forbid"):
    """Jejak versi yang menyertai setiap keluaran eksperimen (C-09).

    Disetel `frozen` agar catatan versi tidak dapat diubah setelah dibentuk,
    dan `extra="forbid"` agar bidang yang salah nama tertangkap saat memanggil
    alih-alih diam-diam terbuang.
    """

    versi_kode: str
    versi_model: str
    versi_indeks: str
    versi_skema_anotasi: str
    pembagian_data: str

    @field_validator("*")
    @classmethod
    def _tidak_boleh_kosong(cls, nilai: str) -> str:
        if not nilai.strip():
            raise ValueError(
                "bidang versi tidak boleh kosong — isi 'belum-berlaku' bila "
                "memang belum berlaku (R-12). Bidang kosong tidak dapat "
                "dibedakan antara belum ada dan lupa dicatat"
            )
        return nilai
