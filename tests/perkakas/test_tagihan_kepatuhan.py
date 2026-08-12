"""Buku besar tagihan kepatuhan — C-3 fitur 007, R-15.

D-12 menyatakan daftar pasal yang belum dapat diperiksa mesin adalah
**"tagihan, bukan pengecualian — wajib menyusut pada setiap fitur berikutnya,
tidak pernah bertambah"**.

Berkas ini memuat satu angka yang ditulis tegas, dan hanya satu.

**Mengapa ia berkas tersendiri.** Angkanya dahulu tinggal pada
`test_pemisahan_indeks.py`, uji fitur 006 yang menyusutkannya menjadi sebelas.
Fitur 007 menyusutkannya lagi, dan angkanya sempat tertulis pada dua berkas
fitur yang berbeda. Buku besar yang tinggal di berkas satu fitur akan
diperbarui oleh fitur berikutnya di berkasnya sendiri, dan sesudah beberapa
fitur tidak ada yang tahu berkas mana yang berlaku.

**Mengapa angkanya ditulis tegas, bukan dihitung.** Uji yang menghitung dari
daftarnya sendiri hanya membuktikan daftar sama dengan dirinya sendiri, dan ia
akan tetap lulus ketika sebuah pasal dikembalikan menjadi tertunda. Angka
tertulis memaksa penyusutan — dan pengembalian — menjadi keputusan yang
disengaja.

Memperbarui angka di sini adalah bagian dari tugas fitur yang memindahkan
sebuah pasal, bukan perawatan terpisah.
"""

from perkakas.kepatuhan.daftar_pasal import DAFTAR_PASAL

JUMLAH_PASAL = 20
TERPERIKSA_MESIN = 10
"""Sepuluh dari dua puluh — **separuh**, sejak C-16 pada fitur 007.

Riwayatnya: 7 (fitur 001) → 8 (fitur 002, C-03) → 9 (fitur 006, C-02) →
10 (fitur 007, C-16). Empat fitur di antara 002 dan 006 tidak menyusutkannya
sama sekali, dan itu yang mendorong KB-030 mendahulukan fitur 006 atas 005.
"""


def test_tagihan_menyusut_menjadi_sepuluh() -> None:
    belum = [p for p in DAFTAR_PASAL if p.pemeriksa is None]
    assert len(DAFTAR_PASAL) == JUMLAH_PASAL
    assert JUMLAH_PASAL - len(belum) == TERPERIKSA_MESIN
    assert len(belum) == JUMLAH_PASAL - TERPERIKSA_MESIN


def test_setiap_pasal_membawa_tepat_satu_keterangan() -> None:
    """Pasal yang membawa pemeriksa **dan** alasan menunggu adalah tempat
    menyembunyikan pekerjaan; pasal tanpa keduanya adalah pasal yang terlupa."""
    for pasal in DAFTAR_PASAL:
        assert (pasal.pemeriksa is None) != (pasal.fitur_pengunci is None), pasal.kode
