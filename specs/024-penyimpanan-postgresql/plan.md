# Plan: 024-penyimpanan-postgresql

| | |
|---|---|
| Spec | `specs/024-penyimpanan-postgresql/spec.md` — Gerbang 1 lolos 3 September 2026 |
| Status | **Menunggu Gerbang 2** |
| Kebutuhan | ADR-05, ADR-06, ADR-12; C-03, C-05, C-12; KA-04 |

## 1. Bentuk yang dituju

Satu berkas pelaksana baru dan satu berkas konfigurasi, keduanya di
`src/penyimpanan/`. Tidak ada modul lain berubah — itu ukuran keberhasilan
fitur ini, bukan sekadar harapannya.

```
src/penyimpanan/
├── dasar.py          (ada)     PenyimpanDasar — antarmuka abstrak
├── tiruan.py         (ada)     PenyimpanTiruan — dalam ingatan
├── kredensial.py     (ada)     Kredensial, area, CatatanAkses
├── sambungan.py      (baru)    KonfigurasiSambungan, dua sambungan terpisah
└── postgres.py       (baru)    PenyimpanPostgres — pelaksana sesungguhnya
```

`AGENTS.md` tidak perlu diperbarui: `src/penyimpanan/` sudah terdaftar, dan
tidak ada tepi arah baru. Diperiksa sebelum ditulis, bukan diasumsikan.

## 2. Letak keputusan Gerbang 1 di dalam kode

| Keputusan | Diwujudkan di mana | Yang membuatnya tidak dapat dilanggar |
|---|---|---|
| Dua basis data, dua konfigurasi berdiri sendiri | `sambungan.py` | Dua tipe konfigurasi **berbeda**, bukan satu tipe dengan dua nilai. Fungsi penyusun sambungan perilaku tidak menerima tipe konfigurasi pseudonim, dan sebaliknya — ketidakcocokannya ditangkap pemeriksa tipe, bukan uji |
| Karantina: skema terpisah + pengguna basis data terpisah | `sambungan.py`, dan pernyataan hak akses pada berkas persiapan | Sambungan jalur penjawaban dibangun dari pengguna yang **tidak pernah diberi** hak baca skema karantina. Ditolak peladen, bukan ditolak kode |
| Penyesuaian `PenyimpanDasar` lewat Gerbang 2 tersendiri | Tidak ada dalam kode — prosedural | Dicatat di sini agar tagihannya terbaca bila muncul |

**"Bentuk, bukan pemeriksaan"** diterapkan pada butir pertama. Konfigurasi
yang salah pasang tidak menghasilkan galat saat jalan; ia tidak dapat ditulis.

## 3. Cara C-03 dan C-05 tetap terjaga

Keduanya **sudah** dijaga mesin sejak fitur 002 lewat `periksa_pemisahan_penyimpanan`
dan `periksa_peta_pseudonim`. Fitur ini tidak menambah pemeriksa; ia menambah
pelaksana yang harus lolos pemeriksa yang sudah ada.

Satu hal yang berubah: sampai hari ini kedua pasal itu dijaga atas kode yang
menyimpan dalam ingatan. Sesudah fitur ini, ia dijaga atas basis data
sesungguhnya — dan di situlah pemisahan diuji pada tempat yang benar.

## 4. Uji

### 4.1 Uji yang tidak boleh diubah satu baris pun

R-01 menuntut `PenyimpanPostgres` lulus rangkaian uji yang sama dengan
`PenyimpanTiruan`. Caranya: rangkaian uji `PenyimpanDasar` yang sudah ada
dijalankan **dua kali** lewat parameter, sekali untuk tiap pelaksana.

Bila satu uji perlu diubah agar pelaksana baru lulus, itu **temuan**, bukan
pekerjaan pemeliharaan: ia berarti abstraksinya tidak pas, dan Keputusan
Gerbang 1 nomor 3 berlaku — diajukan, ditunggu, tidak diperbaiki sambil jalan.

### 4.2 Uji yang menuntut peladen sungguhan

Sebagian sifat hanya ada pada basis data sungguhan dan **tidak dapat**
ditiru: penolakan hak akses oleh peladen, keutuhan penulisan saat sambungan
putus, dan galat "tidak dapat dihubungi" yang wajib dibedakan dari galat
kredensial.

Uji ini ditandai agar dilewati ketika peladen tidak ada, dan **kelewatannya
dilaporkan**, bukan didiamkan. Rangkaian uji yang diam ketika tidak menguji
apa pun adalah laporan yang keliru — pelajaran TA-01.

### 4.3 Uji mutasi

Delapan mutasi direncanakan atas pemisahan kredensial, dan **yang tidak
menyala tetap dilaporkan**:

| | Mutasi | Yang wajib menangkapnya |
|---|---|---|
| M-1 | Pemeriksaan kredensial dipindah sesudah pencarian dokumen | R-02 |
| M-2 | Galat "tidak berhak" diganti galat "tidak ada" | R-03 |
| M-3 | Sambungan jalur penjawaban diberi hak baca karantina | R-04 |
| M-4 | Kedua konfigurasi disusun dari satu sumber yang sama | R-05 |
| M-5 | Pelaksana memilih dirinya sendiri, bukan dipilih pemanggil | R-06 |
| M-6 | Satu nama tabel menyimpang dari D-14 Bagian 5 | R-07 |
| M-7 | `CatatanAkses` tidak ditulis pada jalur penolakan | R-08 |
| M-8 | Penulisan yang gagal di tengah dibiarkan setengah jadi | Keadaan wajib ditangani |

## 5. Ketergantungan

**Nol ketergantungan baru.** `asyncpg` sudah ada pada
`ketergantungan-disetujui.toml`. Diperiksa, bukan diperkirakan.

`pgvector` **tidak** dipakai fitur ini — kolom vektornya menunggu fitur 019,
sebagaimana spec Bagian "Di luar cakupan" menyatakan.

## 6. Urutan tugas yang diusulkan untuk `tasks.md`

Satu tugas = satu commit. Uji lebih dulu, lalu implementasi.

1. `sambungan.py` — dua tipe konfigurasi berbeda; uji bahwa yang satu tidak dapat menggantikan yang lain
2. Rangkaian uji `PenyimpanDasar` dijadikan berparameter — masih satu pelaksana, agar perubahan ini terbukti tidak mengubah hasil
3. `postgres.py` kerangka — lulus uji yang tidak menuntut peladen
4. Jalur kredensial: R-02, R-03, R-04 beserta uji yang menuntut peladen
5. Sambungan pseudonim terpisah: R-05
6. Pemilihan pelaksana oleh pemanggil: R-06
7. Nama tabel D-14 Bagian 5: R-07; `CatatanAkses`: R-08
8. Keutuhan penulisan; uji mutasi dijalankan dan **hasilnya dilaporkan apa adanya**
9. Berkas persiapan basis data — pengguna, skema, pernyataan hak akses — beserta uraian batas antara kode dan operasi (TK-56)

## 7. Yang tidak dikerjakan fitur ini

Diulang dari spec agar terbaca oleh yang hanya membuka rencana: penyediaan
dan pengoperasian peladen, penyimpanan vektor, pemindahan data dari tiruan,
dan penyediaan basis data kunci pseudonim. **Menulis adaptornya adalah kode;
menyediakan peladennya adalah operasi.**

## 8. Risiko yang diketahui sekarang

| Risiko | Bila terjadi |
|---|---|
| Abstraksi `PenyimpanDasar` tidak pas dengan basis data sungguhan | Keputusan Gerbang 1 nomor 3: diajukan lewat Gerbang 2 tersendiri, tidak diperbaiki sambil jalan |
| Uji yang menuntut peladen selalu dilewati karena peladen tak pernah ada | Angka kelewatan dilaporkan tiap `make check`; bila tidak pernah menyusut, itu tagihan yang wajib dibicarakan, bukan keadaan normal |
| Penyiapan hak akses hanya dilakukan pada mesin pengembangan | Berkas persiapan disimpan pada repositori dan dijalankan sama pada setiap lingkungan |

## 9. Berhenti di Gerbang 2

`tasks.md` dan kode menunggu putusan. Yang paling perlu Anda periksa adalah
Bagian 2 dan Bagian 4.1 — di situ keputusan Gerbang 1 berubah menjadi bentuk,
dan di situ pula letak kemungkinan fitur ini menemukan bahwa abstraksinya
salah.
