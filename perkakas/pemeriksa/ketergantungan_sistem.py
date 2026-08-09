"""Pemeriksa ketergantungan di luar paket Python — R-13, C-12, C-09, KB-017.

`ketergantungan.py` membandingkan `uv.lock` dengan titik nol yang disetujui,
dan itu menutup seluruh pohon paket Python. Mesin OCR **tidak ada di sana**:
ia program sistem beserta berkas model yang diunduh terpisah, sehingga versi
yang bergeser tidak tertangkap apa pun.

Akibatnya dua, dan keduanya berat:

- **C-09 kehilangan versi yang wajib dicatatnya.** Hasil OCR yang tidak dapat
  diulang membatalkan klaim reproduktibilitas pada naskah.
- **Komponen penentu isi korpus berada di luar seluruh gerbang.** Model yang
  tertukar menghasilkan teks yang tetap terbaca seperti teks, sehingga tidak
  ada yang menyadarinya dari hasilnya saja.

**Tiga keadaan dibedakan, bukan dua.** Ini bagian terpenting modul ini:

| Keadaan | `terperiksa` | Temuan |
|---|---|---|
| Mesin terpasang dan cocok | `True` | tidak ada |
| Mesin terpasang dan menyimpang | `True` | ada |
| **Mesin tidak terpasang** | **`False`** | **tidak ada** |

Baris ketiga sengaja tidak menghasilkan temuan — tidak ada yang dilanggar oleh
lingkungan yang belum memasang mesin — tetapi ia juga **tidak boleh terbaca
sebagai lulus**. Pemeriksa yang tidak menemukan bahannya lalu melapor bersih
adalah laporan palsu, dan laporan palsu menghentikan kewaspadaan. Itu pelajaran
TA-01 pada `docs/D00.md` Bagian 7.10, diterapkan pada perkakas alih-alih pada
sistem — sama dengan yang sudah dilakukan `daftar_pasal.py`.

Bagian `[sistem]` hanya dituntut bila `pytesseract` ada pada daftar `langsung`.
Proyek yang tidak memakai OCR tidak perlu mencatat mesin OCR, dan tanpa
kelonggaran itu pemeriksa akan menyala atas riwayat sebelum fitur 015.
"""

from __future__ import annotations

import shutil
import subprocess
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from src.ingest.ekstraksi.model_ocr import sidik_model as _sidik_model

from perkakas.pemeriksa.ast_aturan import Temuan

# Pencarian berkas model tinggal di `src/`, dan pemeriksa memakainya —
# bukan sebaliknya. Perkakas boleh bergantung pada kode; kode tidak boleh
# bergantung pada perkakas. Menyalinnya ke sini akan menghasilkan aturan
# kedua yang lupa diperbarui ketika tempat pemasangan Tesseract berubah.

PAKET_PENANDA = "pytesseract"
"""Kehadirannya pada `langsung` yang menuntut bagian `[sistem]` ada."""


@dataclass(frozen=True)
class HasilSistem:
    """Tiga keadaan, bukan dua — lihat uraian modul."""

    temuan: list[Temuan] = field(default_factory=list)
    terperiksa: bool = True
    catatan: str = ""


def _versi_tesseract() -> str | None:
    """Versi mesin, atau `None` bila mesin tidak terpasang.

    Kegagalan pemanggilan diperlakukan sama dengan tidak terpasang: keduanya
    berarti tidak ada yang dapat diperiksa, dan membedakannya di sini tidak
    mengubah apa pun bagi pembaca laporan.
    """
    if shutil.which("tesseract") is None:
        return None
    try:
        keluaran = subprocess.run(
            ["tesseract", "--version"], capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    baris = keluaran.stdout.splitlines() or keluaran.stderr.splitlines()
    if not baris:
        return None
    bagian = baris[0].split()
    return bagian[1] if len(bagian) > 1 else None


def periksa_ketergantungan_sistem(
    akar: Path,
    versi_mesin: Callable[[], str | None] = _versi_tesseract,
    sidik_model: Callable[[str], str | None] = _sidik_model,
) -> HasilSistem:
    """Bandingkan mesin OCR terpasang dengan yang tercatat disetujui.

    Kedua pembacaan lingkungan disuntikkan sebagai parameter agar ujinya tidak
    menuntut mesin terpasang. Uji yang menuntut perkakas luar adalah uji yang
    kelak dilewati orang, dan uji yang dilewati tidak menjaga apa pun.
    """
    disetujui = akar / "ketergantungan-disetujui.toml"
    if not disetujui.is_file():
        return HasilSistem(
            temuan=[
                Temuan(
                    disetujui,
                    0,
                    "ketergantungan-disetujui.toml tidak ditemukan — menghapus "
                    "pembandingnya bukan cara sah meloloskan pemeriksa ini",
                )
            ]
        )

    isi = tomllib.loads(disetujui.read_text(encoding="utf-8"))
    langsung = {str(n).strip().lower().replace("_", "-") for n in isi.get("langsung", [])}
    if PAKET_PENANDA not in langsung:
        return HasilSistem()

    tercatat = isi.get("sistem", {}).get("tesseract")
    if not tercatat:
        return HasilSistem(
            temuan=[
                Temuan(
                    disetujui,
                    0,
                    f"{PAKET_PENANDA!r} disetujui tetapi bagian [sistem.tesseract] "
                    "tidak ada — mesin OCR menentukan isi korpus dan tidak boleh "
                    "berada di luar catatan persetujuan (R-13, C-12)",
                )
            ]
        )

    if not str(tercatat.get("versi", "")):
        return HasilSistem(
            terperiksa=False,
            catatan=(
                "versi mesin OCR belum ditetapkan pada catatan persetujuan — "
                "ia dipatok ketika mesin pertama kali dipasang pada lingkungan "
                "penelitian, bukan ditebak dari lingkungan mana pun"
            ),
        )

    terpasang = versi_mesin()
    if terpasang is None:
        return HasilSistem(
            terperiksa=False,
            catatan=(
                "ketergantungan sistem belum dapat diperiksa — mesin OCR tidak "
                "terpasang pada lingkungan ini; ini bukan pelanggaran, tetapi "
                "juga bukan lulus"
            ),
        )

    temuan: list[Temuan] = []
    if terpasang != str(tercatat.get("versi", "")):
        temuan.append(
            Temuan(
                disetujui,
                0,
                f"versi mesin OCR bergeser tanpa persetujuan: tercatat "
                f"{tercatat.get('versi')!r} menjadi {terpasang!r} — C-09 menuntut "
                "versi yang menghasilkan korpus dapat ditelusuri",
            )
        )

    nama_berkas = str(tercatat.get("berkas_model", ""))
    sidik = sidik_model(nama_berkas)
    if sidik is None:
        temuan.append(
            Temuan(
                disetujui,
                0,
                f"mesin OCR terpasang tetapi berkas model {nama_berkas!r} tidak "
                "ditemukan — keadaan ini berbeda dari mesin yang tidak terpasang, "
                "dan hanya yang ini pelanggaran",
            )
        )
    elif sidik != str(tercatat.get("sidik", "")):
        temuan.append(
            Temuan(
                disetujui,
                0,
                f"sidik berkas model {nama_berkas!r} berbeda dari yang tercatat — "
                "model yang tertukar menghasilkan teks yang tetap terbaca seperti "
                "teks, sehingga tidak terlihat dari hasilnya saja",
            )
        )

    return HasilSistem(temuan=temuan)
