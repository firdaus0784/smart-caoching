"""Uji penempatan dokumen spesifikasi di docs/ — R-01.

`make compliance` dan seluruh rujukan pada AGENTS.md membaca dari sini. Nama
dipendekkan (D01.md, bukan D01-BRD-PRD-...md) agar rujukan tetap pendek,
sesuai BACADULU.

Uji tidak hanya memeriksa keberadaan berkas, tetapi juga bahwa isi berkas
sesuai namanya — salah salin adalah kekeliruan yang sunyi dan mahal.
"""

from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
DOCS = AKAR / "docs"

# nama berkas -> penanda yang wajib ada di dalamnya
DOKUMEN = {
    "00-INDEKS.md": "Indeks Himpunan Dokumen",
    **{f"D{n:02d}.md": f"D-{n:02d}" for n in range(0, 15)},
}


def test_seluruh_dokumen_ada() -> None:
    hilang = [n for n in DOKUMEN if not (DOCS / n).is_file()]
    assert not hilang, f"dokumen belum ada di docs/: {hilang}"


def test_dokumen_tidak_kosong() -> None:
    # Berkas hilang dihitung sebagai kegagalan, bukan dilewati. Uji yang
    # melewati berkas hilang akan lulus secara hampa sebelum ada apa pun.
    bermasalah = [n for n in DOKUMEN if not (DOCS / n).is_file() or (DOCS / n).stat().st_size == 0]
    assert not bermasalah, f"dokumen hilang atau kosong: {bermasalah}"


def test_isi_dokumen_sesuai_namanya() -> None:
    keliru = []
    for nama, penanda in DOKUMEN.items():
        berkas = DOCS / nama
        if not berkas.is_file():
            keliru.append(f"{nama} tidak ada")
            continue
        kepala = berkas.read_text(encoding="utf-8")[:4000]
        if penanda not in kepala:
            keliru.append(f"{nama} tidak memuat penanda {penanda!r}")
    assert not keliru, "berkas tersalin ke nama yang keliru: " + "; ".join(keliru)
