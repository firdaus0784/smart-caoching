# Tasks: 002-gerbang-karantina

Ditinjau manusia sebelum kode ditulis. Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 3** — 5 Agustus 2026. Implementasi berjalan |
| Jumlah tugas | **18** — di bawah ambang ±30 |
| Pelaporan | Per fase: A, B, C, D. Bila sebuah tugas tidak dapat diselesaikan tanpa melanggar konstitusi atau `plan.md`, pekerjaan berhenti saat itu juga |

## Fase A · Lapisan penyimpanan

Dibangun lebih dulu karena ia yang menegakkan C-03; seluruh fase berikutnya
berdiri di atasnya.

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | Enum `Area` pada `src/penyimpanan/area.py` — `karantina`, `korpus` | Uji: nilai enum persis mengikuti `dokumen_sumber.area_simpan` pada D-14 Bagian 5.1; nilai di luar itu ditolak | R-03 | [x] |
| A-2 | `Kredensial` pada `src/penyimpanan/kredensial.py`, dengan himpunan baca dan himpunan tulis | Uji: `Kredensial` tidak dapat diubah setelah dibentuk. **Uji: himpunan kosong bukan berarti semua** | R-01 | [x] |
| A-3 | Tiga kredensial baku: `PENJAWABAN`, `VERIFIKASI`, `PEMANGGIL_LLM` — tetapan, bukan fungsi pembangun | Uji: `PENJAWABAN` dan `PEMANGGIL_LLM` tidak memuat `KARANTINA` pada himpunan baca. **Uji: `PEMANGGIL_LLM` berhimpunan tulis kosong** | R-01, R-01a, R-01b | [x] |
| A-4 | `GalatAksesDitolak` pada `src/penyimpanan/galat.py` | Uji: pesan pengguna ≤ 20 kata, Bahasa Indonesia, tanpa istilah teknis, **tanpa nama area** (C-13, D-14 Bagian 4.2) | R-02 | [x] |
| A-5 | Antarmuka abstrak `PenyimpanDasar` pada `src/penyimpanan/dasar.py` | Uji: setiap metode menerima `Kredensial` sebagai parameter wajib, bukan opsional | R-01, R-02 | [x] |
| A-6 | Pelaksana tiruan dalam memori pada `src/penyimpanan/tiruan.py` | Uji: **kredensial diperiksa sebelum data disentuh** — dokumen yang tidak ada pada area terlarang tetap menghasilkan galat akses, bukan galat tidak ditemukan | R-01a, R-02 | [x] |
| A-7 | Pencatatan percobaan akses yang ditolak | Uji: percobaan tercatat; **uji: catatannya tidak memuat id maupun isi dokumen** | R-02, R-12 | [x] |

**A-6 adalah tugas terpenting pada fase ini.** Penyimpan yang memeriksa
keberadaan lebih dulu membocorkan keberadaan dokumen karantina lewat perbedaan
galat, dan itu meruntuhkan C-03 tanpa satu pun dokumen terbaca.

## Fase B · Gerbang dan peringkat

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | Metadata asal dokumen pada `src/ingest/dokumen.py` | Uji: bidang FR-B06 wajib terisi; dokumen tanpa salah satunya ditolak saat dibentuk | R-06 | [x] |
| B-2 | Pemetaan jenis sumber ke peringkat T1–T4 pada `src/ingest/peringkat.py` | Uji: seluruh baris D-13 Bagian 6 terpetakan. **Uji: jenis sumber tak dikenal → galat, bukan T4 diam-diam** | R-07 | [x] |
| B-3 | Masuk selalu ke karantina pada `src/ingest/gerbang.py` | Uji: dokumen baru berada di `karantina`; **uji: tidak ada jalan membuat dokumen langsung di `korpus`** | R-03 | [ ] |
| B-4 | Perpindahan hanya dengan persetujuan verifikator tercatat | Uji: perpindahan tanpa id verifikator → galat. **Uji: perpindahan dengan kredensial `PENJAWABAN` → galat akses** | R-04 | [ ] |
| B-5 | Penolakan menahan dokumen beserta alasannya | Uji: dokumen ditolak tetap di `karantina`, `status_anonimisasi` menjadi `ditolak`, alasan tersimpan | R-05 | [ ] |
| B-6 | Peringkat T3 tidak terjangkau selama dokumen di karantina | **Uji tersendiri:** kredensial `PENJAWABAN` meminta segmen dokumen karantina berperingkat T3 → galat akses | R-07a | [ ] |
| B-7 | Peringkat tidak dapat diubah sesudah ditetapkan | Uji: percobaan mengubah peringkat lewat kredensial `PENJAWABAN` maupun `PEMANGGIL_LLM` → galat | R-08 | [ ] |

**B-6 diberi tugas tersendiri, tidak digabung ke B-4.** R-07a adalah kebutuhan
yang paling mudah dianggap sudah dipenuhi oleh kebutuhan lain, dan justru itu
sebabnya ia perlu uji yang berdiri sendiri.

## Fase C · Pemeriksa pola adversarial

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Pemeriksa pola pada `src/ingest/adversarial.py` — mengembalikan temuan, tidak memutuskan | Uji: pola penyisipan yang dikenali tertangkap; teks biasa tidak menghasilkan temuan | R-09 | [ ] |
| C-2 | Temuan menahan dokumen untuk tinjauan manusia | Uji: dokumen bertemuan tidak dapat berpindah ke `korpus` meski verifikator menyetujui, sampai temuan ditinjau | R-09 | [ ] |
| C-3 | **Pemeriksa yang gagal berarti menahan** | Uji: pemeriksa dibuat melempar galat → dokumen tertahan, bukan lolos | R-10 | [ ] |

Ambang pemeriksa dinyatakan **nilai awal**, bukan hasil kalibrasi, dan ditulis
demikian pada uraian modulnya. Kalibrasinya BT-29 (C-16).

## Fase D · Jejak dan kepatuhan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| D-1 | `jejak_area` pada `src/ingest/jejak.py` — tambah saja, tujuh bidang D-04 Bagian 7.2 | Uji: setiap perpindahan menghasilkan satu baris; **uji: tidak ada jalan menyunting atau menghapus baris** | R-11 | [ ] |
| D-2 | Alasan pada jejak tidak memuat data pribadi | Uji: alasan yang memuat pola NIK, NIP, atau nomor telepon → ditolak saat ditulis, bukan disaring diam-diam | R-12 | [ ] |
| D-3 | Pemeriksa C-03 pada `perkakas/pemeriksa/pemisahan_penyimpanan.py`; C-03 berpindah dari `fitur_pengunci` ke `pemeriksa` | Uji: pemeriksa menyala pada pelanggaran buatan. **Uji mutasi:** `KARANTINA` ditambahkan ke himpunan baca `PENJAWABAN` → `make check` gagal | R-01, R-01a | [ ] |

**D-3 terakhir.** Menyambungkan pemeriksa sebelum yang diperiksanya lengkap
menghasilkan gerbang yang lulus karena tidak memeriksa apa pun — pelajaran T-7
fitur 014.

## Urutan

Fase A mendahului seluruhnya karena ia yang menegakkan C-03; membangun gerbang
di atas penyimpan yang belum memisahkan kredensial berarti gerbang yang menjaga
pintu tanpa dinding.

Di dalam fase A, A-3 mengikuti A-2, dan A-6 mengikuti A-5. Di dalam fase B,
B-3 s.d. B-5 mengikuti B-1 dan B-2 karena keduanya menyediakan bahan yang
dipindahkan gerbang.

Fase C dapat berjalan sejajar dengan fase B, tetapi C-2 memerlukan B-4.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` — **C-03 berpindah menjadi lulus; tagihan 13 → 12**
- [ ] R-01 s.d. R-12, termasuk R-01a, R-01b, R-07a, punya uji yang lulus
- [ ] Uji mutasi D-3 dijalankan dan hasilnya dilaporkan pada uraian commit
- [ ] Cakupan uji tidak turun
- [ ] Nol ketergantungan baru
- [ ] Nol rute baru; `docs/D14.md` Bagian 3 tidak disentuh
- [ ] Setiap pesan galat pengguna ≤ 20 kata, tanpa istilah teknis (C-13)
