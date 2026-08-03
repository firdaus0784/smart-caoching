"""Uji larangan RP-05 pada bagian Batas AGENTS.md — G2-6.

Sifat tambah-saja `logbook/` ditegakkan pada kode (R-13), tetapi kode tidak
dapat menahan penyuntingan berkas langsung maupun penulisan ulang riwayat git.
Kendali terhadap keduanya bersifat prosedural, dan Gerbang 2 memutuskan:
karena prosedural, ia harus tertulis.
"""

from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]


def _bagian_batas() -> str:
    isi = (AKAR / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Batas" in isi, "AGENTS.md tidak memuat bagian Batas"
    setelah = isi.split("## Batas", 1)[1]
    return setelah.split("\n## ", 1)[0].lower()


def test_larangan_menyunting_logbook_tertulis() -> None:
    batas = _bagian_batas()
    assert "logbook" in batas, "bagian Batas tidak menyebut logbook/"
    assert "menambah baris" in batas, (
        "larangan logbook/ harus menyatakan yang diizinkan hanya menambah baris"
    )

    baris_logbook = [b for b in batas.splitlines() if "logbook" in b]
    menyempit = [b for b in baris_logbook if "percobaan" in b and "l4" not in b]
    assert not menyempit, (
        "larangan logbook/ menyempit pada baris percobaan saja. L4 keputusan "
        "dan L7 penggunaan alat bantu AI bukan percobaan, dan keduanya sama "
        f"terlindungi: {menyempit}"
    )


def test_larangan_menulis_ulang_riwayat_git_tertulis() -> None:
    batas = _bagian_batas()
    petunjuk = ("riwayat git", "rebase", "amend", "force")
    assert any(p in batas for p in petunjuk), (
        "bagian Batas tidak melarang penulisan ulang riwayat git — RP-05 "
        "menyatakan kendalinya prosedural, sehingga ia wajib tertulis"
    )
