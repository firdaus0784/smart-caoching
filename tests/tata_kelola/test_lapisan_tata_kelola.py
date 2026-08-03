"""Uji penempatan lapisan tata kelola — R-01, R-02.

Tanpa berkas ini di tempatnya, aturan yang mengikat agen tidak terbaca dan
`make compliance` tidak punya rujukan untuk diperiksa.
"""

import re
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]

BERKAS_AKAR = ("AGENTS.md", "CLAUDE.md", "constitution.md")
TEMPLAT = ("spec.md", "plan.md", "tasks.md")

# Pasal ditulis sebagai penanda tebal di awal baris: **C-01** ...
POLA_PASAL = re.compile(r"^\*\*(C-\d{2})\*\*", re.MULTILINE)


def test_berkas_akar_ada() -> None:
    hilang = [b for b in BERKAS_AKAR if not (AKAR / b).is_file()]
    assert not hilang, f"berkas tata kelola belum ada di akar: {hilang}"


def test_templat_spec_ada() -> None:
    hilang = [t for t in TEMPLAT if not (AKAR / "specs/_template" / t).is_file()]
    assert not hilang, f"templat belum ada di specs/_template/: {hilang}"


def test_constitution_memuat_dua_puluh_pasal_tepat_sekali() -> None:
    isi = (AKAR / "constitution.md").read_text(encoding="utf-8")
    ditemukan = POLA_PASAL.findall(isi)

    diharapkan = {f"C-{n:02d}" for n in range(1, 21)}
    hilang = sorted(diharapkan - set(ditemukan))
    assert not hilang, f"pasal hilang dari constitution.md: {hilang}"

    ganda = sorted({p for p in ditemukan if ditemukan.count(p) > 1})
    assert not ganda, f"pasal terdefinisi lebih dari sekali: {ganda}"

    asing = sorted(set(ditemukan) - diharapkan)
    assert not asing, f"pasal di luar C-01 s.d. C-20: {asing}"


def test_claude_md_merujuk_kedua_berkas() -> None:
    isi = (AKAR / "CLAUDE.md").read_text(encoding="utf-8")
    for rujukan in ("@AGENTS.md", "@constitution.md"):
        assert rujukan in isi, f"CLAUDE.md tidak merujuk {rujukan}"
