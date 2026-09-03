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
TERPERIKSA_MESIN = 19
"""Tujuh belas dari dua puluh, sejak C-10 pada 13 Agustus 2026.

Riwayatnya: 7 (fitur 001) → 8 (002, C-03) → 9 (006, C-02) → 10 (007, C-16) →
11 (008, C-19) → 12 (009, C-20) → 14 (010, C-06 dan C-07) → 15 (022, C-05) → 16 (012, C-04) → 17 (C-10).
Empat fitur di
antara 002 dan 006 tidak menyusutkannya sama sekali, dan itu yang mendorong
KB-030 mendahulukan fitur 006 atas 005.

Fitur 010 memindahkan **dua** pasal sekaligus, dan keduanya memang miliknya:
C-06 adalah gerbang kurasi yang fitur ini bangun, dan C-07 lapis ingestinya.
Pemeriksa C-07 tetap memeriksa ketiga lapis, bukan lapis yang fitur ini bangun
saja — pasal yang dijaga tiga lapis dan diperiksa pada satu di antaranya adalah
pasal yang lolos ketika lapis itu dipindahkan.

**C-05 berpindah pada fitur 022, C-04 tidak.** Keduanya semula tertahan fitur
012. Yang membedakan: C-05 pernyataan **struktural** tentang di mana kunci
berada, dan strukturnya dibangun fitur 022 — bentuk yang sama dengan C-03 yang
berpindah pada fitur 002 sebelum layanan RAG ada. C-04 menuntut telemetri
**tidak merekam** tanpa persetujuan, dan telemetri belum ada; fitur 022
menyediakan yang diperiksanya, bukan pemeriksanya.

**C-04 berpindah pada fitur 012**, satu fitur sesudah C-05. Keduanya semula
tertahan bersama; yang memisahkannya adalah bahwa C-05 pernyataan struktural
tentang di mana kunci berada, sedangkan C-04 menuntut sebuah gerbang yang
belum ada sampai telemetri dibangun.

**C-10 berpindah tanpa fitur baru.** Kodenya sudah ada sejak fitur 003; yang
kurang pemeriksanya, dan ketiadaan itu bertahan enam fitur. Ia dikerjakan
sebagai commit berdiri sendiri, bentuk yang sama dengan pemeriksa arah
(KB-038).

**Tiga pasal tersisa, dan tidak satu pun dapat berpindah tanpa `web/` atau
tanpa model yang belum ada** — C-01 (fitur 020), C-13 (013), C-14 (010 s.d.
013).

**C-01 tidak ikut berpindah pada fitur 008**, meski `daftar_pasal.py` semula
mencatatnya demikian. Verifikasi yang C-01 tuntut mencakup VS-03, dan VS-03
menunggu model sematan serta BT-29. Alasan tunggunya dikoreksi menjadi menyebut
fitur 020 — mengoreksi alasan tunggu bukan menambah utang, ia membuat utang
yang sudah ada terbaca benar.

**C-14 berpindah tanpa fitur baru, dan tanpa menunggu fitur 013.** Ia terdaftar
menunggu "010 s.d. 013" sejak fitur 001, dengan catatan pada dirinya sendiri —
"sebagian dapat diperiksa lebih awal" — dan perintah L8 fitur 001 agar baris
itu **ditinjau tiap fitur**. Peninjauan itu tidak pernah dilakukan sesudahnya,
dan alasan tunggunya sudah kedaluwarsa sejak fitur 012 lolos Gerbang 4.

Yang berubah bukan kodenya melainkan **maknanya**: sebelum fitur 010, 011, dan
012 ada, ketiadaan personalisasi dan analitik prediktif dapat berarti "belum
dibangun" alih-alih "sengaja tidak dibangun". Sesudah ketiganya ada,
ketiadaannya menjadi pernyataan yang dapat ditagih.

Fitur 013 tidak ditunggu, dan itu disengaja: pemeriksanya berdiri lebih dulu
agar `web/` lahir di bawah aturan yang sudah ada — bentuk yang sama dengan
C-17 dan C-18 yang dibangun fitur 001 sebelum ada pemanggil yang perlu
dijaganya. Dikerjakan sebagai commit berdiri sendiri, bentuk yang sama dengan
C-10 (KB-050) dan pemeriksa arah (KB-038).

**Dua pasal tersisa** — C-01 (fitur 020, menunggu model sematan) dan C-13
(fitur 013, menunggu `web/`).
"""


def test_tagihan_menyusut_menjadi_sembilan_belas() -> None:
    belum = [p for p in DAFTAR_PASAL if p.pemeriksa is None]
    assert len(DAFTAR_PASAL) == JUMLAH_PASAL
    assert JUMLAH_PASAL - len(belum) == TERPERIKSA_MESIN
    assert len(belum) == JUMLAH_PASAL - TERPERIKSA_MESIN


def test_setiap_pasal_membawa_tepat_satu_keterangan() -> None:
    """Pasal yang membawa pemeriksa **dan** alasan menunggu adalah tempat
    menyembunyikan pekerjaan; pasal tanpa keduanya adalah pasal yang terlupa."""
    for pasal in DAFTAR_PASAL:
        assert (pasal.pemeriksa is None) != (pasal.fitur_pengunci is None), pasal.kode
