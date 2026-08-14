"""Uji profil sekolah — A-1 fitur 022, R-02, R-10, R-12, FR-A02, FR-A06.

Bidangnya **dibaca dari `docs/D04.md` Bagian 7.1**, bukan disalin ke berkas
ini. Uji yang menyalin daftarnya hanya membuktikan dua salinan sama, termasuk
ketika keduanya sudah menyimpang dari pemiliknya. Bentuk yang sama dengan
`test_butir.py` (010), `test_ambang_kesepakatan.py` (003), dan pemeriksa arah
(009).

## Enam, dan angka itu tidak berdasar literatur

FR-A02 menetapkan **maksimal 6 isian** pada *onboarding*. Penelusuran 13
Agustus 2026 tidak menemukan rujukan terverifikasi yang menetapkannya — hanya
tulisan pemasaran, yang D-11 tolak lewat SI-03. Usul menyatakannya **penetapan
tim tanpa dasar literatur** tercatat pada D-11 Bagian 5.

Berkas ini karena itu menegakkan angkanya **apa adanya**, dan tidak berpura-pura
ia berdasar. Yang membuatnya tetap dapat dipertahankan: enam bidang itu persis
yang D-04 Bagian 7.1 daftarkan, sehingga kode dan model data sepakat meski
angkanya belum bersandar.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.pengguna.profil import BIDANG_ONBOARDING_MAKSIMUM, JalurAkreditasi, ProfilSekolah

AKAR = Path(__file__).resolve().parents[2]

NAMA_MENURUT_D14 = {"akreditasi": "jalur_akreditasi"}
"""Bidang yang D-04 dan D-14 namai berbeda — **selisih dokumen, bukan kelonggaran.**

D-04 Bagian 7.1 menulis `akreditasi`; D-14 Bagian 5.1 menulis
`profil_sekolah.jalur_akreditasi` beserta maknanya. `AGENTS.md` menetapkan nama
bidang mengikuti D-14 Bagian 5, sehingga kode memakai `jalur_akreditasi`.

Pemetaan ini disebut satu per satu, bukan dibiarkan sebagai "boleh berbeda".
Usul menyelaraskan D-04 tercatat pada D-11 Bagian 5 — dan sampai ia diputus,
selisihnya terbaca di sini alih-alih tersembunyi di dalam kode.
"""

BUKAN_ISIAN_PENGGUNA = {"id_pengguna", "tanggal_perbarui"}
"""Bidang D-04 yang bukan isian *onboarding*, disebut namanya satu per satu.

`id_pengguna` adalah kunci penghubung; `tanggal_perbarui` diisi sistem saat
FR-A06 dijalankan. Keduanya ada pada tabel dan **tidak** dihitung terhadap
pagu enam isian FR-A02.

Daftar putih yang berbunyi "kecuali bidang teknis" adalah daftar yang akan
ditambahi. Yang dikecualikan wajib disebut namanya.
"""


def _bidang_d04() -> list[str]:
    """Bidang `profil_sekolah` pada D-04 Bagian 7.1 — sumbernya, bukan salinannya."""
    teks = (AKAR / "docs" / "D04.md").read_text(encoding="utf-8")
    awal = teks.index("### 7.1 Kelompok Pengguna dan Persetujuan")
    akhir = teks.index("### 7.2")
    baris = next(g for g in teks[awal:akhir].splitlines() if g.startswith("| `profil_sekolah`"))
    mentah = [n.strip() for n in baris.split("|")[2].split(",")]
    return [NAMA_MENURUT_D14.get(n, n) for n in mentah]


def _profil(**ganti: object) -> ProfilSekolah:
    argumen: dict[str, object] = {
        "id_pengguna": "PGN-001",
        "jabatan": "Kepala Sekolah",
        "masa_kerja": 7,
        "jumlah_rombel": 12,
        "jumlah_ptk": 18,
        "jalur_akreditasi": JalurAkreditasi.VISITASI,
        "wilayah": "Kabupaten Sumedang",
    }
    argumen.update(ganti)
    return ProfilSekolah(**argumen)  # type: ignore[arg-type]


# ------------------------------------------------------------ R-02 · enam bidang


def test_seluruh_bidang_d04_ada_pada_profil() -> None:
    """**Uji terpenting berkas ini**, dan ia membaca D-04 sungguhan."""
    hilang = set(_bidang_d04()) - set(ProfilSekolah.model_fields)
    assert not hilang, f"bidang D-04 Bagian 7.1 yang hilang: {sorted(hilang)}"


def test_tidak_ada_bidang_di_luar_d04() -> None:
    """Bidang ketujuh yang ditambahkan tanpa persetujuan manusia melanggar R-02
    **dan** menggeser pagu FR-A02 tanpa seorang pun memutuskannya."""
    tambahan = set(ProfilSekolah.model_fields) - set(_bidang_d04())
    assert tambahan == set(), f"bidang di luar D-04 Bagian 7.1: {sorted(tambahan)}"


def test_d04_memang_terbaca() -> None:
    """Pemeriksaan yang tidak menemukan sumbernya tidak memeriksa apa pun.

    Tanpa uji ini, perubahan judul bagian pada D-04 akan membuat kedua uji di
    atas membandingkan terhadap daftar kosong — dan keduanya lulus.
    """
    assert len(_bidang_d04()) == 8


def test_isian_onboarding_tepat_enam() -> None:
    """**FR-A02.** Dihitung dari model, bukan dari angka yang disalin.

    Yang dikecualikan disebut namanya pada `BUKAN_ISIAN_PENGGUNA`; kecuali
    bertuliskan "bidang teknis", daftar itu akan ditambahi.
    """
    isian = set(ProfilSekolah.model_fields) - BUKAN_ISIAN_PENGGUNA
    assert len(isian) == BIDANG_ONBOARDING_MAKSIMUM == 6


def test_bidang_wajib_tanpa_nilai_bawaan() -> None:
    """Bidang berbawaan pada profil yang disusun tergesa akan terisi diam-diam,
    dan yang terisi diam-diam tidak pernah ditinjau siapa pun."""
    for bidang in (
        "id_pengguna",
        "jabatan",
        "masa_kerja",
        "jumlah_rombel",
        "jumlah_ptk",
        "jalur_akreditasi",
        "wilayah",
    ):
        assert ProfilSekolah.model_fields[bidang].is_required(), bidang


# --------------------------------------------------- D-14 Bagian 5.1 · akreditasi


def test_nama_bidang_mengikuti_d14_bukan_d04() -> None:
    """`AGENTS.md` menetapkan nama bidang mengikuti D-14 Bagian 5.

    D-04 menulis `akreditasi`, D-14 menulis `jalur_akreditasi`. Uji ini
    memastikan yang menang adalah D-14 — dan bahwa selisihnya tidak diam-diam
    diselesaikan ke arah sebaliknya kelak.
    """
    assert "jalur_akreditasi" in ProfilSekolah.model_fields
    assert "akreditasi" not in ProfilSekolah.model_fields
    teks = (AKAR / "docs" / "D14.md").read_text(encoding="utf-8")
    assert "`profil_sekolah.jalur_akreditasi`" in teks


def test_jalur_akreditasi_dua_nilai_d14() -> None:
    """`profil_sekolah.jalur_akreditasi` bernilai `visitasi` atau `automasi`
    (D-14 Bagian 5.1). AG-04 melarang mengubah daftar nilai enum."""
    assert {j.value for j in JalurAkreditasi} == {"visitasi", "automasi"}


def test_akreditasi_untai_bebas_ditolak() -> None:
    """Enum sebagai tipe, bukan untai bebas — KM-04 dan gaya proyek.

    Untai bebas mengumpul menjadi beberapa ejaan bagi satu jalur, dan pemicu
    kontekstual D-02 Bagian 5 kemudian membedakan hal yang sama.
    """
    with pytest.raises(ValidationError):
        _profil(jalur_akreditasi="Visitasi")


# ------------------------------------------------------------- batas nilai wajar


def test_masa_kerja_negatif_ditolak() -> None:
    with pytest.raises(ValidationError):
        _profil(masa_kerja=-1)


def test_masa_kerja_nol_diterima() -> None:
    """Kepala sekolah yang baru diangkat bermasa kerja nol tahun, dan menolaknya
    akan menutup justru persona yang paling membutuhkan pendampingan."""
    assert _profil(masa_kerja=0).masa_kerja == 0


def test_jumlah_rombel_dan_ptk_wajib_positif() -> None:
    """Sekolah tanpa rombongan belajar atau tanpa PTK bukan sekolah dasar yang
    sedang dikelola; nilai nol menandakan isian yang belum diisi, bukan fakta."""
    with pytest.raises(ValidationError):
        _profil(jumlah_rombel=0)
    with pytest.raises(ValidationError):
        _profil(jumlah_ptk=0)


def test_wilayah_kosong_ditolak() -> None:
    with pytest.raises(ValidationError):
        _profil(wilayah="   ")


# ------------------------------------------------------------ R-10 · pembaruan


def test_pembaruan_mencatat_waktunya() -> None:
    """**FR-A06.** Profil yang dapat diperbarui tanpa jejak waktu membuat
    prioritas manajerial lama tidak dapat dibedakan dari yang baru — dan
    penyaringan feed FR-G01 bersandar padanya."""
    awal = _profil()
    sesudah = awal.diperbarui(jumlah_rombel=14)
    assert sesudah.jumlah_rombel == 14
    assert sesudah.tanggal_perbarui is not None
    assert awal.tanggal_perbarui != sesudah.tanggal_perbarui


def test_pembaruan_menghasilkan_profil_baru_bukan_menyunting() -> None:
    """Beku. Profil yang dapat disunting di tempat membuat "kapan ia berubah"
    tidak terjawab, dan FR-A06 menuntut justru itu."""
    awal = _profil()
    awal.diperbarui(jumlah_rombel=14)
    assert awal.jumlah_rombel == 12
    with pytest.raises(ValidationError):
        awal.wilayah = "lain"  # type: ignore[misc]


def test_pembaruan_tidak_dapat_mengganti_pemiliknya() -> None:
    """Profil yang berpindah pengguna adalah profil yang tidak dapat ditelusuri
    kepada siapa pun."""
    with pytest.raises(ValueError):
        _profil().diperbarui(id_pengguna="PGN-002")


def test_pembaruan_juga_menolak_data_pribadi() -> None:
    """**Uji yang menutup mutasi yang selamat.**

    `model_copy` menyalin tanpa menjalankan validator, sehingga pembaruan yang
    menyisipkan nomor telepon ke `wilayah` akan lolos meski pembentukan
    pertamanya ditolak — R-11 kemudian hanya berlaku sekali seumur profil.

    Uraian modul sudah menyebut alasan memakai `model_validate`; sampai uji ini
    ada, alasan itu adalah klaim tanpa penjaga. Uji mutasi 13 Agustus 2026
    menemukannya selamat.
    """
    with pytest.raises(ValidationError):
        _profil().diperbarui(wilayah="Sumedang 081234567890")


def test_pembaruan_juga_menegakkan_batas_nilai() -> None:
    """Alasan yang sama pada bidang bilangan: pembaruan yang menurunkan jumlah
    rombel menjadi nol tidak boleh lolos hanya karena ia pembaruan."""
    with pytest.raises(ValidationError):
        _profil().diperbarui(jumlah_rombel=0)


def test_waktu_pembaruan_tidak_dapat_diisi_pemanggil() -> None:
    """Waktu yang diisi pemanggil dapat mendahului perubahannya, dan urutan
    pembaruan profil adalah yang FR-A06 buat dapat ditelusuri.

    Sejajar dengan `BarisKurasi.waktu` fitur 010 yang diambil dari putusan,
    bukan dari jam penulisan: satu sumber waktu, bukan dua yang dapat
    berselisih.
    """
    with pytest.raises(ValueError):
        _profil().diperbarui(tanggal_perbarui=datetime(2020, 1, 1, tzinfo=UTC))


def test_waktu_perbarui_berzona_utc() -> None:
    """KM-01: seluruh waktu disimpan UTC. Waktu tanpa zona dari dua mesin tidak
    dapat diurutkan."""
    sesudah = _profil().diperbarui(masa_kerja=8)
    assert sesudah.tanggal_perbarui is not None
    assert sesudah.tanggal_perbarui.tzinfo is not None
    assert sesudah.tanggal_perbarui.utcoffset() == datetime.now(UTC).utcoffset()


def test_profil_baru_belum_pernah_diperbarui() -> None:
    """`None` di sini bukan nilai yang hilang: profil yang baru dibuat memang
    belum pernah diperbarui, dan mengisinya dengan waktu pembuatan akan membuat
    "sudah pernah diperbarui" tidak dapat dibedakan."""
    assert _profil().tanggal_perbarui is None


# ------------------------------------------------------------ R-11 · data pribadi


@pytest.mark.parametrize(
    "wilayah",
    ["Sumedang, NIK 3211010101800001", "Sumedang 081234567890"],
)
def test_bidang_teks_bebas_menolak_data_pribadi(wilayah: str) -> None:
    """KM-03 dan R-11 — **tolak, jangan saring.**

    `wilayah` satu-satunya bidang teks bebas pada profil, dan bidang teks bebas
    adalah tempat data pribadi mendarat. Pendeteksinya dipakai ulang dari
    `src/ingest/data_pribadi.py`, bukan disalin.
    """
    with pytest.raises(ValidationError):
        _profil(wilayah=wilayah)


def test_pendeteksi_data_pribadi_dipakai_ulang_bukan_disalin() -> None:
    """Pendeteksi FR-B04 tinggal di `src/nlp/anonimisasi/pola.py`, dan modul ini
    memanggilnya lewat tepi `pengguna → nlp`.

    Pola yang disalin akan berbeda dari aslinya pada hari salah satunya
    diperbarui — kekeliruan `IndeksTujuan` (KB-036) berbentuk persis begini,
    dan ia terulang sekali lagi pada fitur 010 B-2 sebelum diperbaiki.
    """
    isi = (AKAR / "src" / "pengguna" / "profil.py").read_text(encoding="utf-8")
    assert "from src.nlp.anonimisasi.pola import" in isi
    assert "re.compile" not in isi
