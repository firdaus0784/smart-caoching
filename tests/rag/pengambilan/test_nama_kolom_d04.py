"""Nama kolom `segmen_teks` mengikuti `docs/D04.md` Bagian 7.2 — T-1 fitur 026.

**TK-60.** D-04 Bagian 7.2 menetapkan `segmen_teks` memuat `vektor_sematan`
dan `versi_model_sematan`. Fitur 019 membuat kolomnya bernama `vektor`, dan
`versi_model_sematan` tidak pernah dibuat sama sekali — sehingga R-06 fitur
019 hanya terpenuhi separuh dan uji mutasi M-7 tidak dapat dipasang.

Berkas ini menjaga tiga hal. Dua di antaranya **menjaga cara penggantian
dilakukan**, bukan perilaku sistem, dan keduanya ada karena pengukuran
`plan.md` Bagian 6 menemukan jebakan yang tidak terlihat dari membaca.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from tests.peladen import psql, siapkan

siapkan()

AKAR = Path(__file__).resolve().parents[3]

KOLOM_D04 = ("vektor_sematan", "versi_model_sematan")
"""Kedua bidang yang `docs/D04.md` Bagian 7.2 tetapkan bagi `segmen_teks`."""

JUMLAH_NAMA_SUMBER = 26
"""Berapa kali untai `"vektor"` berarti **nama sumber**, bukan nama kolom.

Diukur pada 23 September 2026 dengan menyapu repositori, bukan diperkirakan.
Angka ini berubah bila sumber vektor dipakai pada uji baru — dan bila ia
berubah, yang wajib diperiksa adalah **mana** yang berubah, bukan angkanya
disesuaikan agar hijau.
"""


@pytest.mark.parametrize("skema", ["indeks_utama", "indeks_metadata"])
@pytest.mark.parametrize("kolom", KOLOM_D04)
def test_kolom_d04_ada_pada_kedua_skema(skema: str, kolom: str) -> None:
    """**R-11.** Nama bidang mengikuti D-04 Bagian 7.2.

    Diperiksa pada **kedua** skema. Uji mutasi T4-6 fitur 019 menemukan versi
    sebelumnya hanya memeriksa `indeks_utama`, sehingga penyimpangan pada
    tabel metadata lolos tanpa suara.
    """
    hasil = psql(
        "smart_coaching",
        "-c",
        "select column_name from information_schema.columns "
        f"where table_schema='{skema}' and table_name='segmen_teks'",
    )
    ada = {b.strip() for b in hasil.stdout.splitlines() if b.strip()}
    assert kolom in ada, f"kolom D-04 {kolom!r} tidak ada pada {skema}: {sorted(ada)}"


def test_nama_kolom_lama_tidak_tersisa() -> None:
    """Kolom `vektor` diganti, bukan didampingi.

    Dua kolom yang menyimpan hal yang sama akan berbeda isinya pada hari salah
    satunya lupa ditulis, dan yang lupa ditulis adalah yang tidak dibaca uji.
    """
    hasil = psql(
        "smart_coaching",
        "-c",
        "select column_name from information_schema.columns "
        "where table_name='segmen_teks' and column_name='vektor'",
    )
    assert not hasil.stdout.strip(), "kolom lama `vektor` masih ada berdampingan"


# ── dua sapuan yang menjaga cara penggantian, bukan perilaku ─────────


def _berkas_python() -> list[Path]:
    return [
        b
        for direktori in ("src", "tests")
        for b in sorted((AKAR / direktori).rglob("*.py"))
        if "__pycache__" not in b.parts and b != Path(__file__).resolve()
    ]
    # Berkas ini sendiri dikecualikan: uraiannya menyebut untai yang sedang
    # dihitung, sehingga sapuan yang memuatnya **mengukur dirinya sendiri**.
    # Ditemukan saat T-1 dijalankan — hitungannya naik 28 → 30, bukan turun
    # ke 26.


def test_nama_sumber_vektor_tidak_ikut_terganti() -> None:
    """**Jebakan (a) `plan.md` Bagian 6.**

    `"vektor"` berarti dua hal: nama kolom, dan nama sumber yang
    `SumberVektor.nama` kembalikan. Penggantian dengan sapuan seluruh berkas
    akan merusak yang kedua, dan ujinya gagal pada tempat yang tidak ada
    hubungannya dengan kolom — bentuk yang sama dengan KB-088, sasaran yang
    mengenai hal yang salah.

    Yang dihitung di sini **hanya** untai `"vektor"` persis; nama kolom
    sesudah T-1 berbunyi `"vektor_sematan"` dan tidak ikut terhitung.
    """
    pola = re.compile(r'"vektor"')
    tempat = [
        f"{b.relative_to(AKAR)}:{nomor}"
        for b in _berkas_python()
        for nomor, baris in enumerate(b.read_text(encoding="utf-8").splitlines(), start=1)
        if pola.search(baris)
    ]
    assert len(tempat) == JUMLAH_NAMA_SUMBER, (
        f"nama sumber `vektor` ditemukan {len(tempat)} kali, bukan "
        f"{JUMLAH_NAMA_SUMBER}. Periksa **mana** yang berubah sebelum "
        f"menyesuaikan angkanya:\n" + "\n".join(tempat)
    )


def test_tidak_ada_untai_sql_menyebut_nama_kolom_di_luar_tetapannya() -> None:
    """**Jebakan (b) `plan.md` Bagian 6.**

    `vektor.py` memiliki tetapan nama kolom, tetapi dua untai SQL sempat
    menuliskannya harfiah. Mengganti lewat tetapan saja akan meninggalkan
    keduanya menunjuk kolom yang tidak ada — dan keduanya **baru gagal ketika
    kueri dijalankan**, bukan saat diimpor dan bukan saat `mypy` berjalan.

    Sapuan statis, bukan uji perilaku: ia menjaga untai yang belum ditulis.
    """
    berkas = AKAR / "src" / "rag" / "pengambilan" / "vektor.py"
    tersangka = [
        f"{berkas.name}:{nomor}"
        for nomor, baris in enumerate(berkas.read_text(encoding="utf-8").splitlines(), start=1)
        if ("vektor_sematan" in baris or "versi_model_sematan" in baris)
        and baris.lstrip().startswith(("f'", 'f"', "'", '"'))
    ]
    assert not tersangka, (
        f"nama kolom ditulis harfiah di dalam untai SQL alih-alih lewat tetapannya: {tersangka}"
    )
