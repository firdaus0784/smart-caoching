"""Uji pemeriksa bahasa antarmuka — C-13, NFR-19, `docs/D05.md` Bagian 10.

## Mengapa pemeriksa ini dibangun sebelum `web/` ada

C-13 terdaftar `fitur_pengunci="013 penyempurnaan antarmuka"` sejak fitur 001,
dan catatan L8 pemeriksa C-14 memerintahkan dua pasal yang tersisa **ditinjau
tiap fitur, bukan dipercaya begitu saja**. Pertanyaan tinjauan bagi C-13 sudah
tertulis di sana: *"apakah kaidah bahasa antarmuka dapat diperiksa atas
mikrokopi D-05 sebelum layarnya dibangun"*.

Jawabannya ya, dan lebih dari itu: **untai yang menghadap pengguna sudah ada
di dalam `src/` hari ini** — penafian jawaban, pesan di luar domain, tiga pesan
galat lapisan HTTP, dan lima pesan jalur ekstraksi. Seluruhnya kode yang
disebarkan, seluruhnya terikat C-13, dan tidak satu pun diperiksa mesin.

Menunggu `web/` berarti membiarkan tiga belas untai berjalan tanpa penjaga
selama enam bulan.

## Dua aturan, dan mengapa yang kedua yang memberi gigi

**Aturan 1 memeriksa isi** untai yang menghadap pengguna: panjang kalimat,
tanda seru, kata terlarang D-05 Bagian 10, kode galat, dan singkatan teknis.

**Aturan 2 memeriksa bentuk.** Aturan 1 sendirian dapat dilewati siapa pun yang
menulis untai harfiah langsung pada jalan keluar alih-alih memakai tetapan yang
terdaftar. Karena itu jalan keluar yang menghadap pengguna **tidak boleh
menerima untai harfiah sama sekali** — ia wajib menunjuk tetapan. Yang dijaga
bukan kata-katanya melainkan tidak adanya pintu samping.

## Singkatan mana yang dilarang, dan mengapa bukan semuanya

C-13 berbunyi "tanpa singkatan yang tidak diuraikan". Menyapu **seluruh**
singkatan akan menyalak pada RKAS, BOS, dan SPJ — singkatan yang kepala sekolah
justru lebih paham daripada tim ini. Pemeriksa yang menyalak keliru adalah
pemeriksa yang dimatikan orang; itu pelajaran yang sudah tertulis pada
pemeriksa C-14.

Yang dilarang karena itu singkatan **sistem**, bukan singkatan domain: API,
HTTP, JSON, LLM, OCR, RAG, NER, SQL, URL, UUID. Batas ini dinyatakan terbuka —
singkatan domain yang benar-benar asing bagi pembaca tetap lolos, dan yang
menangkapnya uji keterbacaan BT-20 bersama persona P1 dan P3, bukan mesin.
"""

from __future__ import annotations

from pathlib import Path

from perkakas.pemeriksa.bahasa_antarmuka import periksa_bahasa_antarmuka

AKAR = Path(__file__).resolve().parents[2]


def _tulis(akar: Path, jalur: str, isi: str) -> None:
    berkas = akar / jalur
    berkas.parent.mkdir(parents=True, exist_ok=True)
    berkas.write_text(isi, encoding="utf-8")


# ── Keadaan sesungguhnya ──────────────────────────────────────────────


def test_repositori_nyata_bersih() -> None:
    """Tiga belas untai yang sudah ada wajib lulus aturannya sendiri."""
    assert periksa_bahasa_antarmuka(AKAR) == []


def test_untai_nyata_memang_ditemukan_pemeriksa() -> None:
    """Penjaga atas uji di atasnya.

    `test_repositori_nyata_bersih` akan lulus juga seandainya pemeriksa tidak
    menemukan satu untai pun — dan lulus yang begitu adalah lulus palsu.
    """
    from perkakas.pemeriksa.bahasa_antarmuka import untai_menghadap_pengguna

    ditemukan = untai_menghadap_pengguna(AKAR)
    nama = {n for _, _, n, _ in ditemukan}
    assert "PENAFIAN_BAKU" in nama
    assert "PESAN_DI_LUAR_DOMAIN" in nama
    assert "PESAN_TIDAK_BERHAK" in nama
    assert "PESAN_PENGGUNA" in nama, "atribut kelas terlewat — lihat _tetapan"
    assert len(ditemukan) == 12, f"{len(ditemukan)} untai terbaca, seharusnya 12"


# ── Aturan 1 · isi ────────────────────────────────────────────────────


def test_kalimat_lebih_dari_dua_puluh_kata_menjadi_temuan(tmp_path: Path) -> None:
    panjang = " ".join(["kata"] * 21)
    _tulis(tmp_path, "src/x.py", f'PESAN_UJI = "{panjang}."\n')
    temuan = periksa_bahasa_antarmuka(tmp_path)
    assert any("21 kata" in t.pesan for t in temuan), temuan


def test_kalimat_tepat_dua_puluh_kata_diterima(tmp_path: Path) -> None:
    """Ambangnya inklusif. Batas yang bergeser satu adalah batas yang salah."""
    pas = " ".join(["kata"] * 20)
    _tulis(tmp_path, "src/x.py", f'PESAN_UJI = "{pas}."\n')
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_dua_kalimat_pendek_diterima(tmp_path: Path) -> None:
    """Panjang diukur per kalimat, bukan per untai."""
    _tulis(tmp_path, "src/x.py", 'PESAN_UJI = "Berkas belum terbaca. Mohon unggah ulang."\n')
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_tanda_seru_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/x.py", 'PESAN_UJI = "Sudah selesai semua!"\n')
    assert any("tanda seru" in t.pesan for t in periksa_bahasa_antarmuka(tmp_path))


def test_kata_terlarang_menjadi_temuan(tmp_path: Path) -> None:
    """D-05 Bagian 10 larangan kedua: gagal, belum tuntas, terlambat."""
    for kata in ("gagal", "belum tuntas", "terlambat"):
        _tulis(tmp_path, "src/x.py", f'PESAN_UJI = "Komitmen Anda {kata}."\n')
        temuan = periksa_bahasa_antarmuka(tmp_path)
        assert any(kata in t.pesan for t in temuan), kata


def test_kode_galat_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/x.py", 'PESAN_UJI = "Ada gangguan. Kode 500."\n')
    assert any("kode galat" in t.pesan for t in periksa_bahasa_antarmuka(tmp_path))


def test_singkatan_sistem_menjadi_temuan(tmp_path: Path) -> None:
    _tulis(tmp_path, "src/x.py", 'PESAN_UJI = "Sambungan API terputus."\n')
    assert any("API" in t.pesan for t in periksa_bahasa_antarmuka(tmp_path))


def test_singkatan_domain_tidak_menjadi_temuan(tmp_path: Path) -> None:
    """RKAS dan BOS dipahami pembacanya. Menyalak di sini melatih orang
    mematikan pemeriksa."""
    _tulis(tmp_path, "src/x.py", 'PESAN_UJI = "Dokumen RKAS dan dana BOS belum terbaca."\n')
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_nilai_di_dalam_peta_pesan_ikut_diperiksa(tmp_path: Path) -> None:
    """`src/ingest/ekstraksi/galat.py` menyimpan lima pesannya dalam dict."""
    _tulis(tmp_path, "src/x.py", 'PESAN = {"a": "Berkas gagal dibaca."}\n')
    assert any("gagal" in t.pesan for t in periksa_bahasa_antarmuka(tmp_path))


# ── Yang sengaja tidak diperiksa ──────────────────────────────────────


def test_uraian_dan_komentar_tidak_diperiksa(tmp_path: Path) -> None:
    """Menjelaskan mengapa kata "gagal" dilarang bukan memakainya."""
    _tulis(
        tmp_path,
        "src/x.py",
        '"""Kata "gagal" dan "terlambat" dilarang D-05 Bagian 10!"""\n'
        "# Tanda seru pada komentar tidak menghadap siapa pun!\n"
        'PESAN_UJI = "Berkas belum terbaca."\n',
    )
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_tetapan_bukan_pesan_tidak_diperiksa(tmp_path: Path) -> None:
    """Hanya untai yang menghadap pengguna. `JALUR_INDEKS` bukan salah satunya."""
    _tulis(tmp_path, "src/x.py", 'JALUR_INDEKS = "indeks/json/500!"\n')
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_tests_dan_perkakas_tidak_diperiksa(tmp_path: Path) -> None:
    _tulis(tmp_path, "tests/x.py", 'PESAN_UJI = "Sudah selesai semua!"\n')
    _tulis(tmp_path, "perkakas/x.py", 'TERLARANG = ("gagal", "terlambat")\n')
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_web_ikut_diperiksa_bila_ada(tmp_path: Path) -> None:
    """Pemeriksa berdiri lebih dulu, menunggu `web/` dengan aturan yang sudah ada."""
    _tulis(tmp_path, "web/x.py", 'PESAN_UJI = "Anda terlambat!"\n')
    assert periksa_bahasa_antarmuka(tmp_path) != []


# ── Aturan 2 · bentuk ─────────────────────────────────────────────────


def test_jalan_keluar_dengan_untai_harfiah_menjadi_temuan(tmp_path: Path) -> None:
    """Inilah pintu samping yang membuat Aturan 1 sendirian tidak cukup."""
    _tulis(tmp_path, "src/x.py", 'def f():\n    return _galat(400, "Permintaan tidak sah.")\n')
    temuan = periksa_bahasa_antarmuka(tmp_path)
    assert any("untai harfiah" in t.pesan for t in temuan), temuan


def test_jalan_keluar_yang_menunjuk_tetapan_diterima(tmp_path: Path) -> None:
    _tulis(
        tmp_path,
        "src/x.py",
        'PESAN_TIDAK_SAH = "Permintaan belum lengkap."\n'
        "def f():\n    return _galat(400, PESAN_TIDAK_SAH)\n",
    )
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_isi_tanggapan_berkunci_pesan_dengan_untai_harfiah_menjadi_temuan(
    tmp_path: Path,
) -> None:
    """Jalan keluar kedua: `content={"pesan": ...}` langsung, tanpa `_galat`."""
    _tulis(
        tmp_path,
        "src/x.py",
        'def f():\n    return JSONResponse(status_code=400, content={"pesan": "Tidak sah."})\n',
    )
    assert any("untai harfiah" in t.pesan for t in periksa_bahasa_antarmuka(tmp_path))


def test_atribut_kelas_ikut_diperiksa(tmp_path: Path) -> None:
    """Dua untai sungguhan pernah terlewat karena berada di dalam kelas.

    `GalatLayananModel.PESAN_PENGGUNA` dan `GalatAksesDitolak.PESAN_PENGGUNA`
    memakai kesepakatan penamaan dengan benar; yang keliru adalah penyusuran
    pemeriksa yang berhenti pada tingkat modul. Hasilnya bersih, dan bersih
    yang begitu adalah bersih palsu.
    """
    _tulis(
        tmp_path,
        "src/x.py",
        'class GalatUji(Exception):\n    PESAN_PENGGUNA = "Permintaan Anda gagal diproses."\n',
    )
    assert any("gagal" in t.pesan for t in periksa_bahasa_antarmuka(tmp_path))


def test_peubah_setempat_huruf_kecil_tidak_diperiksa(tmp_path: Path) -> None:
    """`pesan` sebagai peubah biasa bukan tetapan menghadap pengguna."""
    _tulis(
        tmp_path, "src/x.py", 'def f(pesan: str) -> str:\n    pesan = "gagal!"\n    return pesan\n'
    )
    assert periksa_bahasa_antarmuka(tmp_path) == []


def test_tetapan_huruf_campuran_tetap_diperiksa(tmp_path: Path) -> None:
    """Lubang yang ditemukan uji mutasi M-7.

    Syarat `nama.isupper()` semula ada pada `_menghadap_pengguna`. Ia tidak
    menolak apa pun yang belum ditolak — perbandingan peka huruf besar-kecil
    sudah menyaring `pesan` — tetapi ia **meloloskan** `PESAN_Pengguna`. Uji
    ini mengunci lubang itu tertutup.
    """
    _tulis(tmp_path, "src/x.py", 'PESAN_Pengguna = "Permintaan Anda gagal."\n')
    assert any("gagal" in t.pesan for t in periksa_bahasa_antarmuka(tmp_path))
