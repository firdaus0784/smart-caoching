"""Uji daftar pasal C-01 s.d. C-20 — R-15.

Daftar ini adalah yang membuat `make compliance` tidak dapat berbohong. Dua
sifatnya yang menentukan:

- kedua puluh pasal wajib hadir; pasal tanpa entri menggagalkan pembangunan,
  bukan lolos senyap
- setiap pasal punya **tepat satu** dari dua hal: pemeriksa, atau alasan
  beserta fitur penguncinya. Tidak pernah keduanya, tidak pernah tidak
  keduanya

Sifat kedua itu yang mencegah daftar berubah menjadi tempat menyembunyikan
pekerjaan: pasal yang sudah punya pemeriksa tidak boleh sekaligus membawa
alasan menunggu.
"""

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL

DIHARAPKAN = {f"C-{n:02d}" for n in range(1, 21)}


def test_dua_puluh_pasal_hadir() -> None:
    kode = {p.kode for p in DAFTAR_PASAL}
    hilang = sorted(DIHARAPKAN - kode)
    asing = sorted(kode - DIHARAPKAN)
    assert not hilang, f"pasal hilang dari daftar: {hilang}"
    assert not asing, f"kode di luar C-01 s.d. C-20: {asing}"


def test_tidak_ada_pasal_ganda() -> None:
    kode = [p.kode for p in DAFTAR_PASAL]
    ganda = sorted({k for k in kode if kode.count(k) > 1})
    assert not ganda, f"pasal terdaftar lebih dari sekali: {ganda}"


def test_setiap_pasal_punya_tepat_satu_keadaan() -> None:
    keliru = []
    for pasal in DAFTAR_PASAL:
        punya_pemeriksa = pasal.pemeriksa is not None
        punya_alasan = bool(pasal.fitur_pengunci)
        if punya_pemeriksa == punya_alasan:
            keadaan = "keduanya" if punya_pemeriksa else "tidak keduanya"
            keliru.append(f"{pasal.kode}: {keadaan}")
    assert not keliru, (
        "pasal wajib punya pemeriksa ATAU fitur pengunci, tidak keduanya: " + "; ".join(keliru)
    )


def test_setiap_pasal_punya_ringkasan() -> None:
    kosong = [p.kode for p in DAFTAR_PASAL if not p.ringkas.strip()]
    assert not kosong, f"pasal tanpa ringkasan: {kosong}"


def test_pasal_menunggu_menyebut_fitur_penguncinya() -> None:
    """Alasan tanpa fitur pengunci adalah tempat menyembunyikan pekerjaan."""
    tanpa = [
        p.kode for p in DAFTAR_PASAL if p.pemeriksa is None and not (p.fitur_pengunci or "").strip()
    ]
    assert not tanpa, f"pasal menunggu tanpa fitur pengunci: {tanpa}"


def test_daftar_selaras_dengan_constitution() -> None:
    """Pasal pada daftar wajib benar-benar ada di constitution.md."""
    import re
    from pathlib import Path

    akar = Path(__file__).resolve().parents[2]
    isi = (akar / "constitution.md").read_text(encoding="utf-8")
    pada_konstitusi = set(re.findall(r"^\*\*(C-\d{2})\*\*", isi, re.MULTILINE))
    pada_daftar = {p.kode for p in DAFTAR_PASAL}
    assert pada_daftar == pada_konstitusi, (
        f"daftar menyimpang dari constitution.md. "
        f"hanya di daftar={sorted(pada_daftar - pada_konstitusi)} "
        f"hanya di konstitusi={sorted(pada_konstitusi - pada_daftar)}"
    )
