"""Uji pemeriksa ruang lingkup 2026 — C-14, `docs/D01.md` Bagian 4.2.

## Mengapa pemeriksa ini baru dibangun sekarang

C-14 terdaftar `fitur_pengunci="010 s.d. 013; sebagian dapat diperiksa lebih
awal"` sejak fitur 001, dan catatan L8 fitur yang sama memerintahkan baris itu
**ditinjau tiap fitur, bukan dibiarkan sampai 013**. Peninjauan itu tidak
pernah dilakukan sesudahnya.

Yang berubah: fitur 010, 011, dan 012 sudah lolos Gerbang 4. Sebelum ketiganya
ada, ketiadaan personalisasi dan analitik prediktif tidak bermakna — ia dapat
berarti "belum dibangun" alih-alih "sengaja tidak dibangun". Sesudah ketiganya
ada, ketiadaan itu **menjadi pernyataan**.

## Enam baris, dan siapa yang menjaga masing-masing

`docs/D01.md` Bagian 4.2 memuat enam baris. Pemeriksa ini menjaga lima; baris
pertama sudah dijaga C-15 sejak fitur 001 dan **sengaja tidak diduakan** di
sini — dua pemeriksa atas aturan yang sama akan berselisih pada hari salah
satunya disunting.

## Bahaya terbesarnya sama dengan C-15, dan lebih tajam

Menjelaskan mengapa personalisasi dilarang bukan membangun personalisasi.
`src/pengguna/feed.py` memuat kata "personalisasi" empat kali pada uraiannya —
seluruhnya menerangkan larangannya. Pemeriksa yang menyalak pada prosa akan
membuat penulis menghapus penjelasan yang justru menjaga aturan tetap dipahami.
Uji `test_prosa_yang_menjelaskan_larangan_tidak_menjadi_temuan` menuntutnya.

Lebih tajam daripada C-15 pada satu hal: "riwayat" **dipakai sah** sebagai
pengenal pada `src/llm/pembungkus.py` (riwayat pemanggilan bagi pencatatan
biaya) dan `src/nlp/pelatihan/lemari_uji.py` (riwayat pembukaan himpunan uji).
Sapuan nama atas "riwayat" akan menyalak pada keduanya. Karena itu larangan
personalisasi berbasis riwayat diperiksa **secara struktural** — hanya pada
tanda tangan fungsi penyusun feed — bukan lewat sapuan nama.
"""

from __future__ import annotations

from pathlib import Path

from perkakas.pemeriksa.ruang_lingkup import (
    BERKAS_MOBILE_NATIVE,
    TERLARANG_LINGKUP,
    periksa_ruang_lingkup,
)

AKAR = Path(__file__).resolve().parents[2]


def _tulis(akar: Path, jalur: str, isi: str) -> None:
    berkas = akar / jalur
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(isi, encoding="utf-8")


# ── Repositori nyata ────────────────────────────────────────────────


def test_repositori_nyata_bersih() -> None:
    """Tidak ada pelanggaran C-14 pada kode yang sesungguhnya."""
    assert periksa_ruang_lingkup(AKAR) == []


# ── Sapuan nama: yang harus menyala ─────────────────────────────────


def test_pengenal_dapodik_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/x.py", "def tarik_dapodik() -> None:\n    pass\n")
    temuan = periksa_ruang_lingkup(tmp_path)
    assert len(temuan) == 1
    assert "dapodik" in temuan[0].pesan


def test_pengenal_prediktif_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/x.py", "skor_prediktif = 1\n")
    assert any("prediktif" in t.pesan for t in periksa_ruang_lingkup(tmp_path))


def test_nama_berkas_terlarang_menjadi_temuan(tmp_path: Path) -> None:
    """Berkas kosong bernama terlarang tetap melanggar — C-14 menyebut kerangka kosong."""
    _tulis(tmp_path, "src/rekomendasi.py", "")
    temuan = periksa_ruang_lingkup(tmp_path)
    assert len(temuan) == 1
    assert "nama berkas" in temuan[0].pesan


def test_web_ikut_diperiksa(tmp_path: Path) -> None:
    """`web/` belum ada hari ini, dan pemeriksa sudah menunggunya."""
    _tulis(tmp_path, "web/x.py", "def peer_mentoring() -> None:\n    pass\n")
    assert any("mentoring" in t.pesan for t in periksa_ruang_lingkup(tmp_path))


# ── Sapuan nama: yang tidak boleh menyala ───────────────────────────


def test_prosa_yang_menjelaskan_larangan_tidak_menjadi_temuan(tmp_path: Path) -> None:
    """Menjelaskan mengapa personalisasi dilarang bukan membangun personalisasi.

    Bentuk yang sama dengan `src/pengguna/feed.py` sesungguhnya.
    """
    _tulis(
        tmp_path,
        "src/feed.py",
        '"""Penyaringan berbasis riwayat adalah personalisasi, dan C-14 melarangnya."""\n'
        "# rekomendasi otomatis dan analitik prediktif juga dilarang di sini\n"
        "PESAN = 'sistem ini tidak melakukan personalisasi berbasis riwayat'\n",
    )
    assert periksa_ruang_lingkup(tmp_path) == []


def test_tests_dan_perkakas_tidak_diperiksa(tmp_path: Path) -> None:
    """Keduanya memuat pelanggaran buatan yang memang harus ada — bentuk C-15."""
    _tulis(tmp_path, "tests/x.py", "def uji_dapodik() -> None:\n    pass\n")
    _tulis(tmp_path, "perkakas/x.py", "TERLARANG = ('dapodik',)\n")
    assert periksa_ruang_lingkup(tmp_path) == []


# ── Aturan struktural: personalisasi berbasis riwayat ────────────────


def test_fungsi_feed_berparameter_riwayat_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/f.py", "def susun_feed(*, riwayat: list[str]) -> None:\n    pass\n")
    temuan = periksa_ruang_lingkup(tmp_path)
    assert len(temuan) == 1
    assert "riwayat" in temuan[0].pesan


def test_fungsi_feed_berparameter_umpan_balik_menjadi_temuan(tmp_path: Path) -> None:
    """Umpan balik relevansi dikumpulkan (FR-G07), tetapi tidak boleh menyaring."""
    _tulis(tmp_path, "src/f.py", "def susun_feed(*, umpan_balik: list[str]) -> None:\n    pass\n")
    assert any("umpan_balik" in t.pesan for t in periksa_ruang_lingkup(tmp_path))


def test_fungsi_feed_tanpa_riwayat_bersih(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/f.py", "def susun_feed(*, prioritas: str) -> None:\n    pass\n")
    assert periksa_ruang_lingkup(tmp_path) == []


def test_riwayat_di_luar_fungsi_feed_tidak_menjadi_temuan(tmp_path: Path) -> None:
    """`src/llm/pembungkus.py` dan `lemari_uji.py` memakainya sah.

    Sapuan nama akan menyalak pada keduanya; aturan struktural tidak.
    """
    _tulis(
        tmp_path,
        "src/p.py",
        "class Pembungkus:\n"
        "    def __init__(self) -> None:\n"
        "        self.riwayat: list[str] = []\n"
        "def buka(riwayat: list[str]) -> None:\n"
        "    pass\n",
    )
    assert periksa_ruang_lingkup(tmp_path) == []


# ── Aplikasi mobile native ──────────────────────────────────────────


def test_berkas_proyek_android_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "web/android/build.gradle", "// proyek android\n")
    temuan = periksa_ruang_lingkup(tmp_path)
    assert len(temuan) == 1
    assert "mobile native" in temuan[0].pesan


def test_berkas_proyek_ios_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "web/ios/Podfile", "platform :ios\n")
    assert any("mobile native" in t.pesan for t in periksa_ruang_lingkup(tmp_path))


def test_pwa_tidak_menjadi_temuan(tmp_path: Path) -> None:
    """PWA adalah bentuk yang D-01 setujui; yang dilarang aplikasi native."""
    _tulis(tmp_path, "web/manifest.json", '{"name": "Smart-Coaching"}\n')
    _tulis(tmp_path, "web/package.json", '{"dependencies": {"react": "18.0.0"}}\n')
    assert periksa_ruang_lingkup(tmp_path) == []


def test_react_native_pada_package_json_menjadi_temuan(tmp_path: Path) -> None:
    """Bentuk yang paling mungkin masuk diam-diam pada fitur 013."""
    _tulis(tmp_path, "web/package.json", '{"dependencies": {"react-native": "0.7.0"}}\n')
    assert any("mobile native" in t.pesan for t in periksa_ruang_lingkup(tmp_path))


# ── Cakupan keenam baris D-01 Bagian 4.2 ────────────────────────────


def test_lima_baris_dijaga_di_sini_dan_satu_dijaga_c15() -> None:
    """Keenam baris D-01 Bagian 4.2 memiliki penjaganya.

    Baris gamifikasi sengaja tidak diduakan di sini — C-15 sudah menjaganya
    sejak fitur 001, dan dua pemeriksa atas aturan yang sama akan berselisih
    pada hari salah satunya disunting.
    """
    from perkakas.pemeriksa.nama_terlarang import TERLARANG as TERLARANG_C15

    # Baris 1 — gamifikasi: dijaga C-15.
    assert "gamifikasi" in TERLARANG_C15

    # Baris 2 — aplikasi mobile native.
    assert BERKAS_MOBILE_NATIVE

    # Baris 3 — personalisasi, sentimen, rekomendasi.
    assert {"personalisasi", "sentimen", "rekomendasi"} <= set(TERLARANG_LINGKUP)

    # Baris 4 — peer mentoring dan pembelajaran kolaboratif.
    assert {"mentoring", "kolaboratif"} <= set(TERLARANG_LINGKUP)

    # Baris 5 — integrasi Dapodik dan SIMPATIKA.
    assert {"dapodik", "simpatika"} <= set(TERLARANG_LINGKUP)

    # Baris 6 — analitik prediktif, voice assistant, explainable AI.
    assert {"prediktif", "voiceassistant", "explainableai"} <= set(TERLARANG_LINGKUP)


def test_kata_terlarang_cukup_khas_untuk_tidak_menyalak_pada_istilah_sah() -> None:
    """Bahaya pemeriksa ini bukan melewatkan, melainkan menyalak keliru.

    Bentuk yang sama dengan alasan C-15 memakai "papanperingkat" alih-alih
    "peringkat": setiap kata di bawah wajib cukup panjang dan khas sehingga
    tidak dapat menjadi potongan istilah yang kamus data D-14 wajibkan.
    """
    for kata in TERLARANG_LINGKUP:
        assert len(kata) >= 7, f"{kata!r} terlalu pendek untuk dicocokkan sebagai potongan"
