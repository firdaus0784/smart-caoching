# Tasks: 006-indeks-terpisah-lisensi

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 3** — 10 Agustus 2026 (KB-030) |
| Jumlah tugas | **5** |
| Ketergantungan baru | **Nol** |

## Fase A · Tipe dan penempatan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `IndeksTujuan` dan `SegmenTerindeks` | Uji: dua nilai persis D-14 Bagian 5. **Uji: segmen tanpa indeks tujuan tidak dapat dibentuk** | R-01, R-02 | [ ] |
| A-2 | Penempatan dari lisensi sumber, saat masuk | **Uji: lisensi tertutup ke indeks utama ditolak.** Uji: penempatan menolak, tidak menyaring | R-03 | [ ] |
| A-3 | **Status anonimisasi selain `terverifikasi` ditolak dari indeks mana pun** | Uji: status `menunggu` ditolak; uji: `ditolak` juga | R-05 | [ ] |

**A-3 menjaga hal yang berbeda dari nama fiturnya.** Penegakan lisensi mudah
menyita seluruh perhatian, dan sementara itu dokumen yang anonimisasinya masih
menunggu verifikasi masuk indeks utama tanpa satu pun pemeriksaan menyala.
Yang bocor bukan lisensi melainkan data pribadi.

## Fase B · Pemisahan kredensial dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | **Kredensial jalur penjawaban tanpa izin baca metadata** | **Uji: jalur penjawaban tidak dapat membaca indeks metadata.** Uji mutasi: izin ditambahkan → uji sifat gagal | R-04 | [ ] |
| B-2 | Pemeriksa C-02 dan pemindahannya pada `daftar_pasal.py`; catatan penempatan ke `logbook/` | **Uji: `make compliance` menyusut satu — 9 lulus, 11 belum.** Uji: kode di luar `src/penyimpanan/` yang membaca indeks metadata → pemeriksa menyala | R-06, R-07, R-08 | [ ] |

**B-1 adalah tugas terpenting fitur ini.** Penyaringan saat kueri terasa cukup
dan lebih sederhana. Yang membuatnya tidak cukup: klausa penyaringnya ada pada
setiap kueri, dan satu kueri yang lupa memuatnya menghasilkan jawaban yang
lebih lengkap — bukan galat.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` **menyusut satu** — 9 lulus, 0 gagal, 11 belum
- [ ] Kelima uji mutasi `plan.md` Bagian 4 dijalankan dan dilaporkan
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
