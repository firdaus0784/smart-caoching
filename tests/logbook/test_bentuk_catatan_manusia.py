"""Uji bentuk entri L4 dan L7 — R-11, `docs/D10.md` Bagian 6 dan 9.

L1 dan L2 ditulis kode dan dijaga tipe. L4 dan L7 ditulis manusia, dan di
situlah bidang paling mudah terlewat — terutama bidang yang paling penting.

Pada L5 `docs/D10.md` menyebut satu bidang yang sengaja dibuat eksplisit:
`dilaporkan_dalam_naskah`. Alasannya berlaku juga di sini — keputusan untuk
tidak melaporkan sesuatu harus diambil sadar, bukan terjadi karena lupa.
"""

from pathlib import Path

from src.logbook.bentuk_catatan import BIDANG_L4, BIDANG_L7, periksa_bentuk_catatan

KEPALA = "# L4 · Catatan keputusan berjalan\n\nUraian.\n\n"


def _entri(kode: str, bidang: dict[str, str]) -> str:
    baris = [f"## {kode} · contoh\n", "\n", "| | |\n", "|---|---|\n"]
    baris += [f"| {nama} | {nilai} |\n" for nama, nilai in bidang.items()]
    return "".join(baris) + "\n"


def _tulis(tmp_path: Path, nama: str, isi: str) -> Path:
    berkas = tmp_path / nama
    berkas.write_text(isi, encoding="utf-8")
    return berkas


def test_berkas_tanpa_entri_bukan_pelanggaran(tmp_path: Path) -> None:
    """Belum ada keputusan tercatat adalah keadaan sah di awal siklus."""
    berkas = _tulis(tmp_path, "L4-keputusan.md", KEPALA)
    assert periksa_bentuk_catatan(berkas, BIDANG_L4) == []


def test_entri_lengkap_lolos(tmp_path: Path) -> None:
    isi = KEPALA + _entri("KB-001", dict.fromkeys(BIDANG_L4, "diisi"))
    assert periksa_bentuk_catatan(_tulis(tmp_path, "L4-keputusan.md", isi), BIDANG_L4) == []


def test_bidang_hilang_tertangkap(tmp_path: Path) -> None:
    for bidang in BIDANG_L4:
        kurang = {k: "diisi" for k in BIDANG_L4 if k != bidang}
        isi = KEPALA + _entri("KB-001", kurang)
        berkas = _tulis(tmp_path, f"L4-{bidang}.md", isi)
        temuan = periksa_bentuk_catatan(berkas, BIDANG_L4)
        assert len(temuan) == 1, f"bidang {bidang} hilang tetapi lolos"
        assert bidang in temuan[0].pesan


def test_bidang_kosong_tertangkap(tmp_path: Path) -> None:
    """Bidang yang ada tetapi tidak diisi sama saja dengan tidak ada."""
    bidang = dict.fromkeys(BIDANG_L4, "diisi") | {"Pemutus": ""}
    isi = KEPALA + _entri("KB-001", bidang)
    temuan = periksa_bentuk_catatan(_tulis(tmp_path, "L4-keputusan.md", isi), BIDANG_L4)
    assert len(temuan) == 1
    assert "Pemutus" in temuan[0].pesan


def test_beberapa_entri_diperiksa_seluruhnya(tmp_path: Path) -> None:
    isi = (
        KEPALA
        + _entri("KB-001", dict.fromkeys(BIDANG_L4, "diisi"))
        + _entri("KB-002", {k: "diisi" for k in BIDANG_L4 if k != "Dampak"})
    )
    temuan = periksa_bentuk_catatan(_tulis(tmp_path, "L4-keputusan.md", isi), BIDANG_L4)
    assert len(temuan) == 1
    assert "KB-002" in temuan[0].pesan


def test_bidang_l7_memuat_pemberi_izin() -> None:
    """D-12 Bagian 8 mensyaratkan gerbang yang dilewati dicatat beserta pemberi izin."""
    assert "Pemberi izin" in BIDANG_L7


def test_bidang_l7_memuat_verifikasi_manusia() -> None:
    """D-10 Bagian 9 — siapa memeriksa, bagaimana."""
    assert "Verifikasi manusia" in BIDANG_L7


def test_berkas_l4_dan_l7_nyata_ada_dan_sah() -> None:
    akar = Path(__file__).resolve().parents[2] / "logbook"
    for nama, bidang in (("L4-keputusan.md", BIDANG_L4), ("L7-alat-bantu-ai.md", BIDANG_L7)):
        berkas = akar / nama
        assert berkas.is_file(), f"{nama} belum ada"
        temuan = periksa_bentuk_catatan(berkas, bidang)
        assert temuan == [], "; ".join(str(t) for t in temuan)


def test_judul_dokumentasi_tidak_dihitung_sebagai_entri(tmp_path: Path) -> None:
    """Kepala berkas memuat judul "## Bentuk entri" yang bukan entri.

    Pemeriksa versi pertama membacanya sebagai entri yang kekurangan seluruh
    bidang — ditemukan saat memeriksa berkas L4 yang sebenarnya.
    """
    isi = KEPALA + "## Bentuk entri\n\nUraian bentuk.\n\n"
    berkas = _tulis(tmp_path, "L4-keputusan.md", isi)
    assert periksa_bentuk_catatan(berkas, BIDANG_L4) == []
