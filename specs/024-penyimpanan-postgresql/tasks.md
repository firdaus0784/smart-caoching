# Tasks: 024-penyimpanan-postgresql

| | |
|---|---|
| Spec | Gerbang 1 lolos 3 September 2026 |
| Plan | Gerbang 2 lolos 3 September 2026 |
| Status | **Menunggu Gerbang 3** |
| Kebutuhan | ADR-05, ADR-06, ADR-12; C-03, C-05, C-12; KA-04 |

Satu tugas = satu commit. Uji ditulis lebih dulu. `make check` lulus sebelum
tiap tugas dinyatakan selesai.

---

## T-1 · `sambungan.py` — dua konfigurasi yang tidak dapat saling menggantikan

**Kebutuhan:** R-05, Keputusan Gerbang 1 nomor 1.

Dua tipe konfigurasi **berbeda**, bukan satu tipe dengan dua nilai:
`KonfigurasiPerilaku` dan `KonfigurasiPseudonim`. Penyusun sambungan perilaku
tidak menerima tipe pseudonim, dan sebaliknya.

**Uji lebih dulu.** Ketidakcocokannya wajib tertangkap `mypy`, bukan hanya
tertangkap uji saat jalan — uji yang membuktikannya memanggil `mypy` atas
cuplikan yang sengaja salah pasang dan menuntutnya gagal. Ini bentuk yang
sama dengan uji linter pada `tests/tata_kelola/`.

Selesai bila: satu konfigurasi tidak dapat menghasilkan kedua sambungan, dan
pemeriksa tipe yang menyatakannya, bukan catatan pada uraian.

---

## T-2 · Rangkaian uji `PenyimpanDasar` dijadikan berparameter

**Kebutuhan:** R-01.

Rangkaian uji yang sudah ada dijalankan lewat parameter, **masih dengan satu
pelaksana** (`PenyimpanTiruan`). Tugas ini sengaja tidak menambah pelaksana:
ia membuktikan perubahan bentuk uji tidak mengubah hasilnya.

Selesai bila: jumlah uji yang lulus sama persis sebelum dan sesudah, dan
cakupan tidak turun.

> Bila satu uji perlu diubah agar berparameter, itu **temuan** — catat, jangan
> rapikan. Uji yang bergantung pada pelaksana tertentu adalah uji yang selama
> ini menguji pelaksana, bukan kontrak.

---

## T-3 · `postgres.py` kerangka

**Kebutuhan:** R-01, R-06, R-07.

Pelaksana `PenyimpanPostgres` dengan nama tabel dan kolom mengikuti D-14
Bagian 5. Lulus bagian rangkaian uji yang **tidak** menuntut peladen.

`PenyimpanTiruan` tetap dipilih pemanggil; pelaksana tidak memilih dirinya
sendiri (R-06). Tidak ada bacaan berkas konfigurasi di dalam pelaksana — yang
memilih adalah yang memanggil.

---

## T-4 · Jalur kredensial: R-02, R-03, R-04

**Kebutuhan:** R-02, R-03, R-04; C-03, KA-04.

Tiga hal, dan urutannya yang menentukan:

1. Kredensial diperiksa **sebelum** menyentuh data — termasuk sebelum
   memeriksa keberadaan dokumen (R-02).
2. Tanggapan sama persis baik dokumen ada maupun tidak, bila pemanggil tidak
   berhak (R-03). Selisih waktu tanggap pun tidak boleh membedakannya.
3. Sambungan jalur penjawaban **tidak diberi** hak baca skema karantina pada
   tingkat basis data (R-04).

Butir 3 menuntut peladen sungguhan; ujinya masuk golongan 4.2 pada rencana.

---

## T-5 · Sambungan pseudonim terpisah

**Kebutuhan:** R-05; C-05.

Sambungan kunci pseudonim dibangun dari `KonfigurasiPseudonim` dan menunjuk
basis data kedua. Layanan aplikasi tidak dapat menyusunnya.

---

## T-6 · Pemilihan pelaksana oleh pemanggil

**Kebutuhan:** R-06.

Selama peladen belum tersedia, sistem tetap berjalan memakai `PenyimpanTiruan`.
Uji membuktikan **pemanggil** yang memilih — bukan variabel lingkungan yang
dibaca pelaksana, bukan percabangan di dalam pelaksana.

---

## T-7 · `CatatanAkses` pada setiap jalur, termasuk jalur penolakan

**Kebutuhan:** R-08; R-12 pada fitur 002.

Bentuk catatannya tidak berubah. Yang wajib dijaga: penolakan **juga**
tercatat, dan yang dicatat percobaannya, bukan sasarannya — id dokumen pada
log akses menghasilkan daftar dokumen karantina bagi siapa pun yang dapat
membaca log.

---

## T-8 · Keutuhan penulisan, dan uji mutasi dijalankan

**Kebutuhan:** keadaan "sambungan putus di tengah penulisan".

Penulisan tidak setengah jadi. Delapan mutasi M-1 s.d. M-8 pada rencana
Bagian 4.3 dijalankan, dan **hasilnya dilaporkan apa adanya** — mutasi yang
tidak menyala tetap dilaporkan beserta sebabnya, bukan dihapus dari daftar.

---

## T-9 · Berkas persiapan basis data

**Kebutuhan:** Keputusan Gerbang 1 nomor 2; TK-56.

Pernyataan pembuatan basis data, skema, pengguna, dan hak aksesnya. Disimpan
pada repositori dan dijalankan sama pada setiap lingkungan — penyiapan yang
hanya ada di kepala satu orang adalah penyiapan yang berbeda di tiap mesin.

Uraiannya menuliskan batas yang TK-56 kaburkan: **menulis adaptornya kode,
menyediakan peladennya operasi.** Berkas ini yang menandai perbatasannya.

---

## Urutan dan alasannya

T-1 dan T-2 mendahului T-3 dengan sengaja: keduanya tidak menyentuh
PostgreSQL sama sekali, sehingga bila abstraksinya ternyata tidak pas
(Keputusan Gerbang 1 nomor 3), hal itu terlihat pada T-3 dengan dua tugas
sebelumnya sudah aman di belakang.

T-9 terakhir karena ia satu-satunya yang keluarannya bukan kode Python, dan
karena isinya baru pasti sesudah T-4 dan T-5 menetapkan hak apa yang
sesungguhnya dibutuhkan tiap sambungan.

## Yang menghentikan pekerjaan, bukan yang memperlambatnya

| Keadaan | Yang dilakukan |
|---|---|
| Abstraksi `PenyimpanDasar` tidak pas | Berhenti, ajukan lewat Gerbang 2 tersendiri. Tidak diperbaiki sambil jalan |
| Peladen tidak tersedia untuk uji golongan 4.2 | Lanjut, tandai uji dilewati, **laporkan jumlahnya** tiap `make check` |
| Satu uji T-2 perlu diubah | Berhenti, catat sebagai temuan sebelum mengubah |
