# Tasks: 006-indeks-terpisah-lisensi

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026 (KB-031). Lima tugas selesai |
| Jumlah tugas | **5** |
| Ketergantungan baru | **Nol** |

## Fase A · Tipe dan penempatan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `IndeksTujuan` dan `SegmenTerindeks` | Uji: dua nilai persis D-14 Bagian 5. **Uji: segmen tanpa indeks tujuan tidak dapat dibentuk** | R-01, R-02 | [x] |
| A-2 | Penempatan dari lisensi sumber, saat masuk | **Uji: lisensi tertutup ke indeks utama ditolak.** Uji: penempatan menolak, tidak menyaring | R-03 | [x] |
| A-3 | **Status anonimisasi selain `terverifikasi` ditolak dari indeks mana pun** | Uji: status `menunggu` ditolak; uji: `ditolak` juga | R-05 | [x] — ditolak dari **kedua** indeks; metadata bukan tempat pembuangan |

**A-3 menjaga hal yang berbeda dari nama fiturnya.** Penegakan lisensi mudah
menyita seluruh perhatian, dan sementara itu dokumen yang anonimisasinya masih
menunggu verifikasi masuk indeks utama tanpa satu pun pemeriksaan menyala.
Yang bocor bukan lisensi melainkan data pribadi.

## Fase B · Pemisahan kredensial dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | **Kredensial jalur penjawaban tanpa izin baca metadata** | **Uji: jalur penjawaban tidak dapat membaca indeks metadata.** Uji mutasi: izin ditambahkan → uji sifat gagal | R-04 | [x] — garisnya jatuh pada `PEMANGGIL_LLM`, bukan `PENJAWABAN`; spec dikoreksi |
| B-2 | Pemeriksa C-02 dan pemindahannya pada `daftar_pasal.py`; catatan penempatan ke `logbook/` | **Uji: `make compliance` menyusut satu — 9 lulus, 11 belum.** Uji: kode di luar `src/penyimpanan/` yang membaca indeks metadata → pemeriksa menyala | R-06, R-07, R-08 | [x] — tagihan kepatuhan menyusut untuk pertama kalinya sejak fitur 002 |

**B-1 adalah tugas terpenting fitur ini.** Penyaringan saat kueri terasa cukup
dan lebih sederhana. Yang membuatnya tidak cukup: klausa penyaringnya ada pada
setiap kueri, dan satu kueri yang lupa memuatnya menghasilkan jawaban yang
lebih lengkap — bukan galat.

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` **menyusut satu** — 9 lulus, 0 gagal, **11** belum
- [x] Kelima uji mutasi `plan.md` Bagian 4 dijalankan; seluruhnya menyala
- [x] Cakupan uji tidak turun — 99% atas 1.553 pernyataan
- [x] **Nol ketergantungan baru** — tetap 10 langsung, 26 terkunci

## Satu koreksi pada `spec.md`, dilakukan saat implementasi

R-04 semula berbunyi "jalur penjawaban tidak boleh membaca `indeks_metadata`".
Itu **lebih ketat daripada C-02 dan melanggar D-14 Bagian 6**, yang menetapkan
`bacaan_lanjutan` sebagai tempat satu-satunya bagi sumber `indeks_metadata` —
sehingga jalur yang menyusun tanggapan justru wajib dapat membacanya.

Garis C-02 jatuh pada **`PEMANGGIL_LLM`**, bukan `PENJAWABAN`. Kekeliruannya
menyamakan "jalur penjawaban" dengan "yang menyusun permintaan LLM"; keduanya
dipisahkan sejak fitur 001 justru agar garis seperti ini dapat ditarik.

`AGENTS.md` melarang mengubah `spec.md` saat implementasi. Penyimpangan ini
dicatat pada `spec.md`, di sini, dan pada uraian ujinya — **bukan dilakukan
diam-diam**, dan tetap menunggu penilaian Anda apakah ia seharusnya diajukan
terpisah.
