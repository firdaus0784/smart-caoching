# Spec: 036-penilaian-jawaban-dan-aduan

| | |
|---|---|
| Kebutuhan | FR-F07, FR-I04; NFR-09; C-04, C-05, C-06, C-07, C-13, C-14, C-16, C-17, C-20 |
| Dokumen terkait | D-01 Bagian 9 (`answer_rated`) · D-02 J5 · D-04 Bagian 7.4 (`pesan`, TK-69) · D-05 S-09 blok 6, S-09 keadaan tidak-ditemukan, S-17 · D-06 jadwal kurator · D-14 Bagian 3.2, 3.4, 4.1, 4.3 · spec fitur 028, 033, 034, 035 |
| Status | **Gerbang 3 lolos** — 8 Oktober 2026 atas pendelegasian KB-168 (KB-229). Satu dari delapan tugas selesai |

## Mengapa fitur ini diusulkan sekarang

Baris D-12 036 disisipkan pada Gerbang 1 fitur 035 (KB-215) untuk menutup
TK-77: `POST /api/v1/pesan/{id}/penilaian` tertulis pada D-14 Bagian 3.2 tetapi
tidak dimiliki baris mana pun, dan tanpa penilaian antrean aduan kurator (S-17)
selalu kosong. Sejak fitur 034 peristiwa `answer_rated` sudah bernama pada
taksonomi, dan sejak fitur 035 analitik menampilkan "ketepatan jawaban menurut
penilaian pengguna" sebagai **belum terukur** dengan sebab "penilaian jawaban
oleh pengguna belum dibangun". Fitur ini mengisi kekosongan itu.

## Hambatan yang diajukan bersama usulan ini

**Kurator tidak dapat menindaklanjuti jawaban yang tidak pernah tersimpan.**
D-14 Bagian 4.3 menetapkan riwayat **tidak** menyimpan tanggapan, dengan
sengaja: tanggapan menua, dan menampilkannya ulang melanggar C-07. Akibatnya
peladen hanya memegang pertanyaan dan `id_pesan` — bukan jawaban yang dinilai
keliru. S-17 menuntut kurator membaca jawaban itu.

Hambatan ini bukan temuan baru: ia adalah **TK-69** (D-00), terbuka sejak
fitur 028 dengan pertanyaan "apakah `pesan` dibangun sebagai catatan audit —
dengan pseudonim, tanpa ditayangkan ulang — atau dihapus dari model data".
Fitur 036 tidak dapat dibangun utuh tanpa memutusnya, sehingga TK-69 diajukan
sebagai P-1 di bawah, bukan diputus pelaksana.

Jalan ketiga — klien mengirim ulang isi jawaban bersama penilaiannya — **tidak
diajukan**: isi itu dikarang pemanggil, sehingga siapa pun dapat menaruh teks
pilihannya di depan kurator dengan cap "jawaban sistem", dan kurator tidak
dapat membedakannya dari jawaban yang sungguh disusun sistem.

## Di luar cakupan

- Penilaian mengubah apa pun secara otomatis — pengambilan, ambang, validator,
  atau pemilihan beranda (C-14, C-16). Penilaian dikumpulkan bagi kurator dan
  analisis, sejajar "belum relevan sekarang" (`tandai_belum_relevan`, FR-G07)
- Kurator menulis jawaban rujukan yang langsung masuk korpus atau indeks
  (P-3 pilihan A) — menyentuh peringkat kepercayaan T1–T4 (C-19) dan
  pengambilan; tidak diajukan pada siklus ini
- Menampilkan ulang jawaban lama kepada pengguna (C-07, D-14 Bagian 4.3) —
  tidak berubah oleh pilihan P-1 mana pun
- Pemberitahuan kepada pengguna bahwa aduannya ditindaklanjuti — pengiriman
  keluar (C-17)
- Naskah persetujuan ET-02 — bila P-2 menuntut naskah menyebut alur aduan,
  kalimatnya milik tim etik (sejajar TK-75)

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | `POST /pesan/{id}/penilaian` **HARUS** hanya terbuka bagi peran `pengguna`, dan hanya bagi `id_pesan` yang tercatat pada riwayat **milik pemanggil**; `id_pesan` milik orang lain **HARUS** berbentuk sama persis dengan yang tidak dikenal (D-14 Bagian 4.3) |
| R-02 | `nilai` **HARUS** salah satu dari tiga nilai FR-F07 — membantu, tidak membantu, keliru — sebagai enum yang ditulis lebih dulu ke D-14 Bagian 5 |
| R-03 | `alasan` boleh kosong; **JIKA** ia memuat data pribadi berpola (FR-B04), **MAKA** penilaian ditolak sebelum disimpan dan alasan **TIDAK BOLEH** sampai ke log (KM-03) |
| R-04 | Penilaian **TIDAK BOLEH** mengubah jawaban, pengambilan, ambang, maupun pemilihan beranda (C-14, C-16) |
| R-05 | Penilaian ulang atas pesan yang sama **HARUS** tercatat tambah-saja; yang **terakhir** berlaku bagi aduan dan analitik |
| R-06 | `GET /kurasi/aduan` **HARUS** hanya terbuka bagi peran `kurator`; aduan **TIDAK BOLEH** memuat pseudonim, nama akun, maupun pengenal percakapan penilai (C-05) |
| R-07 | Penarikan data (fitur 033) **HARUS** menghapus penilaian dan aduan milik pseudonim itu — dan catatan tanggapan bila P-1 A; daftar tabel penarikan bertambah dan ujinya menagih kelengkapannya |
| R-08 | Bentuk tanggapan `POST /tanya` **TIDAK BOLEH** berubah (C-20); bentuk rute penilaian dan aduan **HARUS** ditulis ke D-14 sebelum kodenya |
| R-09 | `answer_rated` **HARUS** direkam lewat gerbang perekaman fitur 034 (C-04); tanpa persetujuan aktif, penilaian tetap tersimpan bagi kurator tetapi tidak direkam sebagai peristiwa |
| R-10 | Kontrol penilaian **HARUS** tampil pada keempat status dasar. "Laporkan bahwa ini seharusnya ada" pada keadaan tidak-ditemukan (D-05) **HARUS** berarti penilaian `keliru` atas pesan itu; aduan menampilkan status dasarnya sehingga kurator membedakan celah korpus dari jawaban salah |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · TK-69 — apakah jawaban disimpan.**

| Pilihan | Arti |
|---|---|
| A | **Catatan audit tanggapan.** Setiap tanggapan `/tanya` yang sudah lolos validator disimpan tambah-saja pada skema `riwayat` — bentuk D-14 Bagian 4.1 apa adanya, dengan pseudonim, tanpa `tingkat_keyakinan` (FR-F06). Ditulis lapisan `api` sesudah jalur penjawab selesai, bukan oleh `rag` (C-17). **Tidak pernah ditayangkan ulang kepada pengguna** (C-07); kurator membacanya hanya lewat aduan. Baris `pesan` D-04 ditulis ulang mengikuti ini, dan TK-69 selesai |
| B | **Tanpa jawaban.** Aduan memuat pertanyaan, nilai, alasan, status dasar, dan waktu; kurator menilai dari pertanyaan dan alasan saja. TK-69 tetap terbuka |

**Anjuran: A.** Pilihan B membuat S-17 menampilkan keluhan tanpa hal yang
dikeluhkan. Biaya A dinyatakan: seluruh jawaban tersimpan, bukan hanya yang
diadukan, sebab penilaian datang sesudah tanggapan terkirim. Penarikan data
menghapusnya (R-07).

**P-2 · Pertanyaan peserta dibaca kurator.** Pertanyaan dapat memuat data
pribadi tak berpola — nama orang — yang pendeteksi FR-B04 tidak tangkap
(BT-70). Sampai kini pertanyaan hanya terbaca oleh pemiliknya.

| Pilihan | Arti |
|---|---|
| A | Setiap penilaian `keliru` menjadi aduan beserta pertanyaannya |
| B | **Peserta memilih tegas per aduan.** Saat menandai keliru, peserta mencentang "kirim pertanyaan dan jawaban ini kepada kurator". Tanpa centang, penilaian tercatat bagi analitik tetapi tidak menjadi aduan |
| C | Aduan tanpa pertanyaan; kurator hanya melihat jawaban dan alasan |

**Anjuran: B.** Pertanyaan berpindah pembaca hanya atas tindakan pemiliknya.
Apakah naskah ET-02 perlu menyebut alur ini adalah putusan tim etik.

**P-3 · Menutup aduan.** FR-I04 menyebut kurator "dapat menambahkan jawaban
rujukan yang benar ke basis pengetahuan". D-14 Bagian 3.4 hanya memuat
`GET /kurasi/aduan`.

| Pilihan | Arti |
|---|---|
| A | Jawaban rujukan ditulis kurator dan masuk korpus — di luar cakupan (lihat atas) |
| B | **Aduan ditutup dengan tindak lanjut bernama** — enum baru D-14 Bagian 5, misalnya sumber diajukan lewat kanal D-06, butir ditarik (FR-I06), jawaban sudah sesuai dasar, di luar cakupan sistem — beserta catatan. Pengetahuan baru masuk lewat kanal dan gerbang kurasi yang sudah ada (C-06). **Menuntut satu rute baru** `POST /api/v1/kurasi/aduan/{id}/tindak-lanjut` pada D-14 Bagian 3.4 (AG-02) |
| C | Aduan hanya dibaca; tanpa penutupan di dalam sistem |

**Anjuran: B.** Antrean yang tidak dapat dikosongkan bukan antrean; D-06
menjadwalkan kurator 20 menit per pekan untuk aduan, dan pilihan C membuatnya
membaca ulang aduan yang sama setiap pekan. Rute baru hanya sah atas putusan
Anda.

**P-4 · Telemetri dan analitik.** D-01 Bagian 9 menetapkan properti
`answer_rated` sebagai "nilai, alasan". Alasan adalah teks bebas, dan
peristiwa diekspor ke luar sistem lewat CSV fitur 035.

| Pilihan | Arti |
|---|---|
| A | Properti sesuai D-01: `nilai` dan `alasan` |
| B | **`nilai` dan `beralasan` (ya/tidak) saja**; teks alasan tinggal pada penyimpan aduan. D-01 Bagian 9 ditulis ulang. Analitik fitur 035 menampilkan **jumlah per nilai** atas penilaian terakhir tiap pesan, menggantikan "belum terukur" — tanpa rasio "ketepatan" yang definisinya belum ditetapkan D-08 |
| C | B tanpa mengubah analitik; metrik tetap belum terukur |

**Anjuran: B.** Teks bebas yang diekspor adalah jalan data pribadi tak berpola
keluar dari sistem. Mengubah analitik berarti mengubah bentuk D-14 Bagian 4.8
dan daftar `MetrikTertunda` — keduanya hanya atas putusan ini.

## Putusan Gerbang 1 (KB-227)

Pemegang Gerbang 1–4 memilih anjuran pada setiap pertanyaan:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **A** — tanggapan disimpan sebagai catatan audit tambah-saja berpseudonim; tidak pernah ditayangkan ulang kepada pengguna; dibaca kurator hanya lewat aduan. **TK-69 diputus** |
| P-2 | **B** — peserta memilih tegas per aduan; tanpa centang, penilaian hanya bagi analitik. Perlu tidaknya naskah ET-02 menyebutnya diputus tim etik |
| P-3 | **B** — aduan ditutup dengan tindak lanjut bernama dan catatan; **rute baru `POST /api/v1/kurasi/aduan/{id}/tindak-lanjut` disetujui** untuk D-14 Bagian 3.4 |
| P-4 | **B** — `answer_rated` membawa `nilai` dan `beralasan` saja; D-01 Bagian 9 ditulis ulang; analitik fitur 035 menampilkan jumlah per nilai atas penilaian terakhir tiap pesan |
| P-4 susulan (KB-228) | Putusan P-4 B bertentangan dengan dirinya: "terakhir tiap pesan" tidak dapat dihitung dari peristiwa tanpa penanda pesan. Pemegang gerbang memilih **menambah `id_pesan`** — properti `answer_rated` menjadi `nilai`, `beralasan`, `id_pesan` |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | FR-F07; D-14 Bagian 3.2 dan 4.3; C-05 |
| R-02 | FR-F07; AGENTS.md "enum sebagai tipe" |
| R-03 | FR-B04; KM-03; pola alasan `tandai_belum_relevan` (FR-G07) |
| R-04 | C-14; C-16 |
| R-05 | Pola tambah-saja D-14 Bagian 4.3 |
| R-06 | FR-I04; D-14 Bagian 3.4; C-05 |
| R-07 | NFR-09; fitur 033 |
| R-08 | C-20 |
| R-09 | C-04; fitur 034 |
| R-10 | D-05 S-09 blok 6 dan keadaan tidak-ditemukan |

## Kriteria penerimaan

- [x] P-1 s.d. P-4 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Hak peran basis data diuji terhadap peladen: penilai menambah saja,
      kurator tidak menjangkau pseudonim
- [ ] Penarikan data menghapus seluruh tabel baru, diuji terhadap PostgreSQL
- [ ] `make check` lulus enam gerbang
