# L8 · Tagihan Pasal Belum Dapat Diperiksa

Salinan daftar pasal berkeadaan `BELUM-DAPAT-DIPERIKSA` pada akhir sebuah
fitur, beserta fitur penguncinya. Diminta pada Gerbang 2 fitur 001.

**Ia tagihan, bukan pengecualian.** Daftar ini wajib menyusut pada setiap
fitur berikutnya dan tidak pernah bertambah. Bertambahnya daftar adalah
temuan, bukan keadaan biasa.

Bahan untuk audit AK-10 sebelum pilot: prasyarat PS-01 mensyaratkan seluruh
uji kepatuhan lolos, dan pasal yang tidak pernah dapat diperiksa mesin tidak
dapat dinyatakan lolos maupun gagal.

**Ditambah, tidak disunting.** Rekaman lama tetap berdiri agar penyusutannya
terbaca. Lihat `AGENTS.md` bagian Batas.

---

## Fitur 001 · kerangka proyek — 2026-08-05

| Versi kode | `d01e9e2` |
|---|---|
| Dapat diperiksa | **7** dari 20 |
| Belum dapat diperiksa | **13** |

Yang sudah dapat diperiksa: C-08, C-09, C-11, C-12, C-15, C-17, C-18.

| Pasal | Ringkas | Fitur pengunci |
|---|---|---|
| C-01 | klaim manajerial tidak tayang tanpa sitasi terverifikasi | 008 validator sitasi |
| C-02 | segmen berlisensi tertutup tidak masuk konteks LLM | 006 indeks terpisah menurut lisensi |
| C-03 | layanan RAG dan pelatihan tanpa akses area karantina | 002 gerbang karantina |
| C-04 | telemetri tidak merekam tanpa persetujuan aktif | 012 telemetri |
| C-05 | kunci pseudonim terpisah dari data perilaku | 012 telemetri |
| C-06 | butir pengetahuan tidak tayang tanpa persetujuan kurator | 010 pipeline pengetahuan dan gerbang kurasi |
| C-07 | sistem tidak menjawab berdasarkan regulasi dicabut | 010 pipeline pengetahuan dan gerbang kurasi |
| C-10 | rentang anotasi memakai indeks karakter, bukan token | 003 perangkat anotasi |
| C-13 | bahasa antarmuka: kalimat <= 20 kata, tanpa singkatan tak diuraikan | 013 penyempurnaan antarmuka |
| C-14 | fitur D-01 Bagian 4.2 tidak dibangun, termasuk kerangka kosong | 010 s.d. 013; sebagian dapat diperiksa lebih awal |
| C-16 | ambang tidak disetel di luar prosedur kalibrasi BT-29 | 007 pengambilan hibrida dan kalibrasi ambang |
| C-19 | klaim tidak bersandar tunggal pada segmen T3 atau T4 | 008 validator sitasi |
| C-20 | bentuk tanggapan dan daftar rute mengikuti D-14 | 009 penyusunan jawaban dan rute /api/v1/tanya |

Tiga pasal berpindah dari BELUM ke LULUS selama fitur ini: C-09 pada Fase C,
C-17 dan C-18 pada Fase D. Ketiganya diuji lewat uji mutasi — pelanggaran
disisipkan secara buatan untuk memastikan pemeriksanya benar-benar menyala.

Satu catatan untuk pembaca berikutnya: C-14 tercatat menunggu fitur 010 s.d.
013, tetapi sebagiannya dapat diperiksa lebih awal — larangan tabel poin dan
lencana sudah ditegakkan C-15 sejak sekarang. Baris itu ditinjau tiap fitur,
bukan dibiarkan sampai 013.

## Pemutakhiran fitur 002 — 6 Agustus 2026

C-03 berpindah dari BELUM ke LULUS pada tugas D-3. Tagihan menyusut dari 13
menjadi 12; `make compliance` melaporkan 8 lulus, 0 gagal, 12 belum.

Ia diuji lewat uji mutasi yang diminta `tasks.md`: `Area.KARANTINA`
ditambahkan ke himpunan baca `PENJAWABAN`, dan `make check` gagal pada V-01
dan V-02. Pemeriksa yang tidak pernah dilihat menyala tidak dapat dinyatakan
menjaga apa pun.

Satu batas yang wajib diketahui pembaca berikutnya: dua dari empat aturan
pemeriksa C-03 berlaku atas jalur penjawaban, dan dari jalur itu baru
`src/llm/` yang ada. `src/rag/`, `src/api/`, dan `src/nlp/` belum dibangun,
sehingga kedua aturan itu hari ini menjaga pohon yang sebagian besar masih
kosong. Ia menjadi penjagaan penuh ketika ketiga direktori itu ada — bukan
sesuatu yang perlu dikerjakan ulang, tetapi juga bukan sesuatu yang boleh
dianggap sudah terbukti.

## Pemutakhiran — delapan langkah tertinggal disusulkan — 17 Agustus 2026

Ledger ini berhenti diperbarui sesudah fitur 002 (6 Agustus) sekalipun
`make compliance` sudah bergerak dari 8 menjadi 17 lulus sepanjang delapan
langkah berikutnya — bukan pelanggaran aturan mana pun (setiap keputusan
tetap tercatat lengkap pada `logbook/L4-keputusan.md`), tetapi celah yang
sama dengan yang TK-45 temukan pada register `docs/D00.md`: kewajiban
mencatat pada L4 selalu dipenuhi, kewajiban menyusulkan salinannya ke sini
tidak pernah dinyatakan eksplisit sehingga tidak pernah diperiksa. Delapan
entri di bawah menyusulkannya sekali jalan, disusun dari `logbook/L4`
langsung, bukan dari ingatan.

### Fitur 006 — 10 Agustus 2026

C-02 berpindah dari BELUM ke LULUS: `fitur_pengunci` pada `daftar_pasal.py`
diganti `pemeriksa=periksa_pemisahan_indeks`. Tagihan menyusut dari 12
menjadi 11; `make compliance` melaporkan 9 lulus, 0 gagal, 11 belum. Kelima
uji mutasi `plan.md` Bagian 4 dijalankan dan seluruhnya menyala. Tercatat
KB-031 — penyusutan pertama sejak fitur 002.

### Fitur 007 — 12 Agustus 2026

C-16 berpindah dari BELUM ke LULUS: `pemeriksa=periksa_ambang`. Tagihan
menyusut dari 11 menjadi 10 — separuh dari dua puluh pasal, penyusutan kedua
berturut-turut. `make compliance` melaporkan 10 lulus, 0 gagal, 10 belum.
Buku besar hitungan pasal dipindahkan ke `tests/perkakas/test_tagihan_kepatuhan.py`
pada langkah ini — sebelumnya tinggal pada uji fitur 006, dan angkanya sempat
tertulis pada dua berkas fitur berbeda. Tercatat KB-035.

Satu batas yang wajib diketahui pembaca berikutnya: sesudah fitur ini sistem
tidak dapat menjawab pertanyaan apa pun sampai fitur 019 memasang sumber
vektor dan BT-29 mengalibrasi ambang. Disengaja, bukan cacat — sistem yang
menjawab dengan leksikal saja adalah yang ADR-03 tolak, dan ia tidak akan
terlihat berbeda dari sistem yang benar.

### Fitur 008 — 12 Agustus 2026

C-19 berpindah dari BELUM ke LULUS: `pemeriksa=periksa_peringkat_klaim`.
Tagihan menyusut dari 10 menjadi 9. `make compliance` melaporkan 11 lulus,
0 gagal, 9 belum. Kesembilan uji mutasi `plan.md` Bagian 6 dijalankan dan
seluruhnya menyala. Tercatat KB-037.

Satu batas: C-01 tidak ikut berpindah pada fitur ini meski validator sitasi
dibangun bersamaan — tiga dari sembilan pemeriksaannya (VS-03, VS-05, VS-07)
menuntut model sematan yang belum ada, dan itu menjadi fitur 020 tersendiri.

### Fitur 009 — 12 Agustus 2026

C-20 berpindah dari BELUM ke LULUS: `pemeriksa=periksa_bentuk_tanggapan`.
Tagihan menyusut dari 9 menjadi 8. `make compliance` melaporkan 12 lulus,
0 gagal, 8 belum. Kesembilan uji mutasi dijalankan dan seluruhnya menyala.
Tercatat KB-040.

### Fitur 010 — 12 Agustus 2026

Dua pasal berpindah sekaligus — penyusutan pertama sebanyak dua pada satu
fitur: C-06 menjadi `pemeriksa=periksa_gerbang_kurasi`, C-07 menjadi
`pemeriksa=periksa_regulasi_dicabut`. Tagihan menyusut dari 8 menjadi 6.
`make compliance` melaporkan 14 lulus, 0 gagal, 6 belum. Kesembilan uji
mutasi `plan.md` Bagian 5 dijalankan beserta sembilan mutasi tambahan;
seluruhnya menyala. Tercatat KB-043.

Satu batas yang wajib diketahui pembaca berikutnya: pipeline kurasi berdiri
seluruhnya — butir, penyaringan, putusan, jejak, penarikan, pemantauan
antrean — kecuali lapis relevansi L4, yang menunggu klasifikasi K1–K8 fitur
017. Itu menunggu korpus teranotasi, bukan kode.

### Fitur 022 — 13 Agustus 2026

C-05 berpindah dari BELUM ke LULUS: `pemeriksa=periksa_peta_pseudonim`.
Tagihan menyusut dari 6 menjadi 5. `make compliance` melaporkan 15 lulus,
0 gagal, 5 belum. Kesepuluh uji mutasi `plan.md` dijalankan beserta sembilan
tambahan; seluruhnya menyala. Tercatat KB-047.

### Fitur 012 — 13 Agustus 2026

C-04 berpindah dari BELUM ke LULUS: `pemeriksa=periksa_perekaman_telemetri`.
Tagihan menyusut dari 5 menjadi 4. `make compliance` melaporkan 16 lulus,
0 gagal, 4 belum. Kesepuluh uji mutasi dijalankan beserta empat tambahan;
seluruhnya menyala. Tercatat KB-049.

### Pemeriksa C-10 — 13 Agustus 2026

C-10 berpindah dari BELUM ke LULUS lewat commit berdiri sendiri, bukan lewat
fitur baru — bentuk yang sama dengan pemeriksa arah arsitektur (KB-038):
pekerjaan yang menutup celah pada fitur yang sudah lolos gerbangnya (fitur
003) bukan fitur, ia perbaikan. Tagihan menyusut dari 4 menjadi 3.
`make compliance` melaporkan 17 lulus, 0 gagal, 3 belum. Tercatat KB-050.

Tiga pasal tersisa sejak titik ini — C-01, C-13, C-14 — dan tidak satu pun
dapat berpindah tanpa `web/` atau tanpa model sematan yang belum terpasang.
Tidak ada lagi pekerjaan kepatuhan yang tertahan pemrograman sesudah langkah
ini; laju berikutnya ditentukan rapat dan pekerjaan lapangan (KB-050,
KB-060). Keadaan ini tidak berubah sampai catatan ini ditulis.

## Pemeriksa C-14 — 18 Agustus 2026

C-14 berpindah dari BELUM ke LULUS: `fitur_pengunci` diganti
`pemeriksa=periksa_ruang_lingkup`. Tagihan menyusut dari 3 menjadi **2**;
`make compliance` melaporkan **18 lulus, 0 gagal, 2 belum**. Enam uji mutasi
dijalankan dan seluruhnya menyala. Tercatat KB-066.

Dikerjakan sebagai commit berdiri sendiri, bentuk yang sama dengan pemeriksa
C-10 dan pemeriksa arah — pekerjaan yang menutup celah pada pasal yang alasan
tunggunya kedaluwarsa bukan fitur, ia perbaikan.

**Koreksi atas paragraf di atas, dan itu bagian yang paling perlu dibaca.**
Paragraf penutup catatan pemeriksa C-10 menyatakan tidak ada lagi pekerjaan
kepatuhan yang tertahan pemrograman. Pernyataan itu **keliru**, dan
kekeliruannya bertahan tiga fitur. C-14 dapat berpindah sejak fitur 012 lolos
Gerbang 4 pada 13 Agustus; ia baru berpindah lima hari kemudian.

Yang menyembunyikannya bukan kerumitan melainkan **bentuk pencatatannya**.
Alasan tunggu C-14 tertulis sebagai untai bebas — `"010 s.d. 013; sebagian
dapat diperiksa lebih awal"` — dan untai bebas tidak dapat kedaluwarsa dengan
sendirinya. Ia menyebut syaratnya sendiri, memuat peringatan pada dirinya
sendiri, dan tidak ada yang memeriksa apakah syarat itu sudah terpenuhi.

Dua pasal yang tersisa memakai bentuk pencatatan yang sama. Keduanya wajib
ditinjau tiap fitur, bukan dipercaya begitu saja:

| Pasal | Alasan tunggu tercatat | Yang wajib diperiksa ulang |
|---|---|---|
| C-01 | `020 VS-03 dukungan isi klaim; menuntut model sematan dan BT-29` | Apakah fitur 020 sudah berjalan, dan apakah sebagian VS dapat diperiksa lebih awal |
| C-13 | `013 penyempurnaan antarmuka` | Apakah `web/` sudah ada, dan apakah kaidah bahasa antarmuka dapat diperiksa atas mikrokopi D-05 sebelum layarnya dibangun |

Dua pasal tersisa sejak titik ini. Keduanya menunggu sesuatu yang benar-benar
belum ada — tetapi itu pernyataan yang wajib diperiksa ulang tiap fitur, bukan
disimpulkan sekali lalu dipercaya, sebab pernyataan sejenis sudah keliru
sekali.

## Koreksi tanggal atas dua pemutakhiran di atas — 31 Agustus 2026

Judul kedua pemutakhiran di atas bertanggal keliru. Tanggal sesungguhnya
dibaca dari tanggal commit, bukan dari tulisan tangan:

| Pemutakhiran | Judulnya berbunyi | Tanggal sesungguhnya |
|---|---|---|
| Delapan langkah tertinggal disusulkan | 17 Agustus 2026 | **18 Agustus 2026** |
| Pemeriksa C-14 | 18 Agustus 2026 | **28 Agustus 2026** |

Judul aslinya dibiarkan apa adanya: berkas ini menyatakan pada kepalanya
sendiri bahwa rekaman lama tetap berdiri, dan itu berlaku pula bagi rekaman
yang keliru. Sebab dan akibatnya tercatat pada `logbook/L4` KB-069.

---

## Pemeriksa C-13 — 3 September 2026

C-13 berpindah dari BELUM ke LULUS: `fitur_pengunci` diganti
`pemeriksa=periksa_bahasa_antarmuka`. Tagihan menyusut dari 2 menjadi **1**;
`make compliance` melaporkan **19 lulus, 0 gagal, 1 belum**. Dua belas uji
mutasi dijalankan dan seluruhnya menyala. Tercatat KB-078.

Dikerjakan sebagai commit berdiri sendiri, bentuk yang sama dengan pemeriksa
C-10, C-14, dan pemeriksa arah.

### Alasan tunggunya tidak pernah benar

Alasan tunggu C-13 berbunyi `"013 penyempurnaan antarmuka"`, dan pertanyaan
tinjauan yang tertulis pada catatan pemeriksa C-14 sudah menduga sebagiannya:
*"apakah kaidah bahasa antarmuka dapat diperiksa atas mikrokopi D-05 sebelum
layarnya dibangun"*.

Keadaannya lebih tegas daripada dugaan itu. **Dua belas untai yang menghadap
pengguna sudah berada di dalam `src/`**, dan yang paling awal ada sejak fitur
002 — penafian jawaban, pesan di luar domain, tiga pesan lapisan HTTP, lima
pesan jalur ekstraksi, dan dua `PESAN_PENGGUNA` pada kelas galat. Seluruhnya
kode yang disebarkan; seluruhnya terikat C-13; tidak satu pun diperiksa.

C-13 karena itu bukan pasal yang menunggu `web/`. Ia pasal yang **sebagian
besar permukaannya sudah ada sejak awal** dan tidak pernah ditinjau.

### Ini kekeliruan ketiga dengan bentuk yang sama

| Kali | Uji berbunyi | Yang ternyata dapat berpindah |
|---|---|---|
| 1 | "empat pasal tersisa" | C-10 — kodenya ada sejak fitur 003 |
| 2 | "tiga pasal tersisa" | C-14 — alasannya kedaluwarsa sejak fitur 012 |
| 3 | "dua pasal tersisa, keduanya menunggu layar" | C-13 — untainya ada sejak fitur 002 |

Tiga kali berturut-turut, dan sebabnya sama setiap kali: `fitur_pengunci`
berupa **untai bebas** yang menyebut syaratnya sendiri tanpa ada mekanisme
yang memeriksa apakah syarat itu sudah terpenuhi. Untai bebas tidak dapat
kedaluwarsa dengan sendirinya.

**C-01 yang tersisa memakai bentuk pencatatan yang sama.** Alasannya berbunyi
`"020 VS-03 dukungan isi klaim; menuntut model sematan dan BT-29"`. Ditinjau
hari ini: fitur 019 dan 020 keduanya belum dimulai, dan VS-03 menuntut model
sematan yang belum dipasang. Alasan itu **masih berlaku** — tetapi ia wajib
ditinjau lagi pada fitur berikutnya, bukan dipercaya.

### Yang tetap tidak terjaga, dinyatakan terus terang

Pemeriksa membaca tetapan pada berkas Python. Yang tidak terbaca:

| Tidak terjaga | Sebab | Yang kelak menjaganya |
|---|---|---|
| Untai yang disusun saat jalan | Sambungan dan pemformatan tidak terbaca statis (RP-01, RP-05) | — |
| Mikrokopi pada layar `web/` | `web/` belum ada | Fitur 013 |
| Keterbacaan sesungguhnya bagi pembaca | Mesin menghitung kata, bukan memahami | Uji BT-20 bersama persona P1 dan P3 |
| Singkatan domain yang asing bagi pembaca | Sengaja tidak disapu — sapuan atas RKAS dan BOS akan menyalak keliru | Uji BT-20 |

Perpindahan ini karena itu bukan "C-13 kini terjaga penuh", melainkan **C-13
berpindah dari tidak diperiksa sama sekali menjadi diperiksa pada permukaan
yang sudah ada**. Bagian layarnya tetap menunggu fitur 013, dan itu tercatat
pada uraian pemeriksanya.

---

### Fitur 023 dan 019 — 23 September 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — angka yang sama dengan akhir fitur 024 pada 20 September, dan sama
dengan akhir fitur 022 pada 13 September. Tidak ada pasal berpindah.

Itu keadaan yang sah, dan berkas ini menuntutnya dinyatakan alih-alih
dilewatkan: C-01 satu-satunya yang tersisa, dan tidak satu pun dari ketiga
fitur itu menyentuh apa yang C-01 tunggu.

**Tiga fitur berturut-turut berakhir tanpa catatan di sini.** Fitur 023
(Gerbang 3, 10 September), 024 (Gerbang 4, 20 September), dan 019 (tugas
selesai 21 September) seluruhnya lewat tanpa baris pada berkas ini, padahal
kepalanya menyatakan ia diisi "pada akhir sebuah fitur". Ketiganya dicatat
sekarang, terlambat, dengan keterlambatannya dinyatakan. Catatan yang hanya
ditulis ketika tagihannya menyusut berhenti menjadi tagihan dan menjadi
daftar kemenangan.

#### C-01 ditinjau, dan alasannya masih berlaku

Alasan tunggu berbunyi `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Ditinjau hari ini terhadap keadaan sesungguhnya:

| Klausa | Keadaan 23 September 2026 | Masih berlaku? |
|---|---|---|
| menunggu fitur 020 | Belum memiliki `spec.md` sama sekali | Ya |
| menuntut model sematan | Antarmuka `Penyemat` **sudah ada** (fitur 019 T-3), pelaksana tiruan ada; **pelaksana sungguhan dan bobotnya belum** | Ya, tetapi klausanya kini kurang tepat |
| menuntut BT-29 | Fitur 025 belum dimulai; *gold set* BT-35 belum disusun | Ya |

Klausa kedua yang perlu diperhatikan pada peninjauan berikutnya. Hari ini
"model sematan" berarti dua hal yang berbeda nasibnya: **antarmukanya sudah
berdiri, bobotnya belum diunduh.** Selama keduanya disebut satu nama, selesainya
yang pertama akan terbaca seolah menutup keduanya — dan itu bentuk yang sama
dengan tiga kekeliruan yang berkas ini sudah catat.

Alasannya **tidak** saya ubah pada `daftar_pasal.py`: ia masih benar, dan
mengubah untai alasan tanpa pasalnya berpindah adalah menyentuh gerbang tanpa
gerbang berpindah. Yang dituntut berkas ini adalah peninjauan, dan peninjauan
itu ada di atas.

---

### Fitur 026 — 24 September 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 019 dan 023. Tidak ada pasal berpindah,
dan itu dicatat alih-alih dilewatkan.

Fitur ini menguatkan dua pasal tanpa memindahkannya, sebab keduanya sudah
LULUS: **C-09** memperoleh catatan versi bagi pembentukan indeks (L2), dan
**C-17** memperoleh pernyataan tegas ketiadaan hak tulis indeks pada ketiga
kredensial lama (`tulis_indeks=frozenset()`, TK-62). Pasal yang sudah lulus
dapat menjadi lebih benar tanpa angkanya bergerak.

#### C-01 ditinjau lagi

Alasan tunggu masih `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`.

| Klausa | Keadaan 24 September 2026 | Masih berlaku? |
|---|---|---|
| menunggu fitur 020 | Belum memiliki `spec.md` | Ya |
| menuntut model sematan | Antarmuka ada (019); **jalur penyematan korpus kini ada** (026); **bobot model sungguhan belum diunduh** | Ya — dan kini klausa itu berarti **hanya** bobotnya |
| menuntut BT-29 | Fitur 025 belum dimulai; *gold set* BT-35 belum ada | Ya |

Catatan L8 sebelumnya memperingatkan bahwa "model sematan" menyebut dua hal
berbeda nasib. Sejak fitur 026, dua dari tiga hal yang dapat dimaksudkannya —
antarmuka dan jalur penulisan — sudah berdiri. Yang tersisa satu, dan ia bukan
pekerjaan pemrograman: mengunduh bobot model pada mesin penelitian dan menulis
adaptor sungguhan di belakang `Penyemat`.

---

### Fitur 027 — 28 September 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 026. Tidak ada pasal berpindah, dan itu
dicatat alih-alih dilewatkan.

Fitur ini tidak memindahkan pasal, tetapi **memperluas tiga pasal yang sudah
lulus ke permukaan yang sebelumnya tidak diperiksa**:

| Pasal | Sebelum fitur 027 | Sesudahnya |
|---|---|---|
| C-13 | Tetapan Python di `src/`; bagian layar tercatat "menunggu fitur 013" pada catatan 3 September di atas | Juga setiap untai `web/src/mikrokopi.ts`, dan teks harfiah pada `.tsx` ditolak |
| C-14 | `DIPERIKSA` memuat `web`, tetapi hanya berkas Python yang dibaca | Juga pengenal TypeScript, nama berkas `web/`, dan kelas CSS |
| C-15 | Sama dengan C-14 | Sama dengan C-14 |

Baris kedua dan ketiga adalah temuan, bukan kemajuan biasa (KB-133). Kedua
pasal dilaporkan LULUS sejak `web/` ada **tanpa pernah membaca satu baris
TypeScript**. Nama direktori tercantum pada daftar yang diperiksa, dan justru
itu yang membuat celahnya tidak terlihat. Bentuknya sama dengan tiga
kekeliruan pada catatan C-13 di atas — pernyataan yang tampak terpenuhi
karena tidak ada mekanisme yang menagihnya — dan ia ditemukan dengan cara
yang sama: memeriksa apa yang benar-benar dibaca pemeriksa, bukan apa yang
dicantumkan.

**Tabel "yang tetap tidak terjaga" pada catatan C-13, 3 September**, berubah
satu baris: "Mikrokopi pada layar `web/` — menunggu fitur 013" kini terjaga
bagi layar Tanya. Tiga baris lainnya tetap berlaku: untai yang disusun saat
jalan, keterbacaan sesungguhnya (BT-20), dan singkatan domain.

#### C-01 ditinjau lagi

Alasan tunggu masih `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`.

| Klausa | Keadaan 28 September 2026 | Masih berlaku? |
|---|---|---|
| menunggu fitur 020 | Belum memiliki `spec.md` | Ya |
| menuntut model sematan | Hanya bobot model yang tersisa (lihat catatan fitur 026) | Ya |
| menuntut BT-29 | Fitur 025 belum dimulai; *gold set* BT-35 belum ada | Ya |

Fitur 027 tidak menyentuh apa pun yang C-01 tunggu. Layar Tanya
**menampilkan** sitasi yang diterimanya, tetapi tidak memverifikasinya —
verifikasi terhadap segmen tetap tugas validator di belakang peladen, dan
layar yang tampak memperlihatkan sitasi tidak boleh dibaca sebagai C-01
terpenuhi.

---

### Fitur 028 — 29 September 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 027. Tidak ada pasal berpindah, dan itu
dicatat alih-alih dilewatkan.

Fitur ini menguatkan empat pasal yang sudah lulus, dan dua di antaranya kini
**ditegakkan peladen basis data**, bukan hanya oleh kode:

| Pasal | Yang bertambah pada fitur 028 |
|---|---|
| C-05 | Pemilik riwayat berupa pseudonim; `peran_riwayat` tidak dapat menyambung basis data pseudonim — diuji terhadap peladen dengan sebab `permission denied`. `Identitas` menolak pemilik berpola NIK atau telepon |
| C-07 | Riwayat menyimpan rujukan `id_pesan`, tidak pernah tanggapan; layar dan klien menolak giliran yang membawa bidang tanggapan; pemeriksa kontrak V-03 kini membandingkan `Giliran` |
| C-13 | Aturan 2 mengenal jalan keluar galat baru `tanggapan_galat()`, termasuk kata kunci `pesan_pengguna` — tanpanya pesan baru lolos tanpa dibaca |
| C-17 | Jalur penjawaban tidak diberi `USAGE` atas skema `riwayat`: tidak menulis dan tidak membaca. Penulisan riwayat oleh lapisan HTTP dengan peran tersendiri yang hanya dapat menambah |

Satu kebutuhan yang tidak berupa pasal tetapi dekat dengannya: **C-14** —
jawaban tidak dipengaruhi riwayat. Diuji bahwa jalur penjawab menerima
pertanyaan saja, dan mutasi M-11 yang meneruskan riwayat ke jalur menjadi
merah.

#### C-01 ditinjau lagi

Alasan tunggu masih `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Tidak satu klausanya berubah sejak catatan fitur 027: fitur 020
belum memiliki `spec.md`, bobot model penyemat belum diunduh, dan fitur 025
belum dimulai. Fitur 028 tidak menyentuh apa pun yang C-01 tunggu — riwayat
menyimpan pertanyaan, bukan klaim.

### Fitur 029 — 1 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 028. Tidak ada pasal berpindah, dan itu
dicatat alih-alih dilewatkan.

Fitur ini menguatkan tiga pasal yang sudah lulus:

| Pasal | Yang bertambah pada fitur 029 |
|---|---|
| C-05 | Akun berpseudonim (TK-70 selesai): basis data perilaku tidak menyimpan nama, nomor induk, maupun surel siapa pun. Pseudonim acak huruf saja — heksadesimal ditolak karena dapat berpola rekening (KB-158). `peran_autentikasi` dan `peran_pengelola_akun` ditolak peladen menyambung basis data pseudonim, dengan sebab `permission denied`; mutasi M-8 menyala |
| C-13 | Lima kalimat peladen dan tiga belas kalimat layar baru melewati pemeriksa; kawat sandung naik ke 17 dengan nama disebut tegas |
| C-17 | Rute masuk menulis sesi, tetapi bukan jalur penjawaban: `jalur.jawab` tetap tanpa kredensial tulis, dan `src/rag/` serta `src/llm/` nol baris berubah sejak Gerbang 3 |

#### C-01 ditinjau lagi

Alasan tunggu masih `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 029 tidak menyentuh apa pun yang C-01 tunggu.

**Koreksi atas baris C-13 di atas**, ditambahkan sebelum commit sesudah
dihitung ulang dari selisih kode: kalimat peladen baru berjumlah **tiga**
(`PESAN_BELUM_MASUK`, `PESAN_MASUK_DITOLAK`, `PESAN_MASUK_TIDAK_LENGKAP`),
bukan lima; kalimat layar baru berjumlah **enam belas** (empat belas kunci
`MIKROKOPI` dan dua bentuk `PESAN_GALAT.belum_masuk`), bukan tiga belas.
Baris di atas tidak disunting.

### Fitur 030 — 4 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 029. Tidak ada pasal berpindah.

Fitur ini menguatkan empat pasal yang sudah lulus, dan satu di antaranya
untuk pertama kali **dapat dipenuhi di lapangan**:

| Pasal | Yang bertambah pada fitur 030 |
|---|---|
| C-04 | Persetujuan penelitian kini dapat diambil (S-02) dan dicabut (P-5); keadaannya dibaca lewat `KeadaanPersetujuan.dari` fitur 022 — jalur yang sama dengan gerbang perekaman fitur 012. **Tanpa naskah ET-02 terpasang, setiap persetujuan ditolak peladen**, sehingga telemetri tetap mati bagi semua orang sampai naskahnya ada (mutasi M-3) |
| C-05 | Pemilik profil, prioritas, dan persetujuan berupa pseudonim — ditegakkan batasan pola pada ketiga tabel; `peran_pengguna` tanpa jalur ke basis data pseudonim (M-6) |
| C-13 | Tiga kalimat peladen dan dua puluh tujuh kalimat layar baru melewati pemeriksa; satu kalimat yang tertulis harfiah di JSX tertangkap dan dipindah |
| C-14 | Profil dan prioritas tidak diteruskan ke jalur penjawaban (M-9) |

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 030 tidak menyentuh apa pun yang C-01 tunggu.

**Koreksi atas baris C-13 di atas**, ditambahkan sebelum commit sesudah
dihitung ulang dari selisih `web/src/mikrokopi.ts` sejak Gerbang 3: untai
layar baru berjumlah **empat puluh lima** — 28 kunci `MIKROKOPI`, 8 untai
`PENGENALAN`, 8 label kategori, dan 1 fungsi penanda layar — bukan dua puluh
tujuh. Baris di atas tidak disunting.

### Fitur 013 — 5 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 030. Tidak ada pasal berpindah.

Fitur ini menguatkan sembilan pasal yang sudah lulus. Dua di antaranya untuk
pertama kali ditegakkan **peladen basis data** pada jalur penayangan:

| Pasal | Yang bertambah pada fitur 013 |
|---|---|
| C-02 | Butir lengkap tidak membawa untai lisensi; `boleh_teks_penuh` ditetapkan peladen lewat `boleh_teks_penuh()` fitur 011 (M-9). Metadata sumber disalin ke kandidat, sehingga peran penayang tidak membaca korpus yang memuat teks penuh |
| C-03 | Tiga peran baru tanpa hak atas `karantina` maupun `korpus` — diuji dengan sebab `permission denied` |
| C-05 | Pemutus putusan dan penarikan, pemilik butir hari ini dan "belum relevan" berpola pseudonim, ditegakkan batasan tabel; jejak membawa pseudonim sesi, tidak pernah nama akun (M-10); ketiga peran tanpa jalur ke basis data pseudonim |
| C-06 | Ditegakkan **dua kali oleh peladen**: penayang tidak dapat membaca antrean (M-2), dan butir tayang hanya dapat merujuk putusan yang menyetujui butir itu sendiri — kunci asing gabungan `(nomor, id_butir, menyetujui)`. `ButirTayang` dibentuk hanya lewat `terapkan()`; pemeriksa C-06 menolak pembentukan langsung yang sempat ditulis pada T-5. Ujung ke ujung lewat HTTP (M-1) dan lewat peramban |
| C-07 | Status regulasi salinan diperbarui perkakas; putusan memakai status terkini dan menolak TL-04 (M-5); butir yang regulasinya dicabut tidak tampil meski belum ditarik; `status dicabut` menarik otomatis butir tayang |
| C-13 | Lima kalimat peladen dan delapan puluh lima untai layar baru — 64 kunci `MIKROKOPI`, 21 label (jenis sumber, alasan penolakan, pemicu, status) — serta empat fungsi penyusun baris melewati pemeriksa. Dua rujukan bersingkatan pada label D-06 dilepas; pemisah yang semula tertulis di `.tsx` dipindah ke mikrokopi |
| C-14 | Pemilihan beranda membaca prioritas saja, bukan riwayat buka; diuji dengan dua pengguna berprioritas sama sesudah salah satunya membuka butir. Jalur penjawab tidak menerima prioritas maupun butir |
| C-15 | Tidak ada poin, lencana, runtun, maupun peringkat — diuji sebagai ketiadaan pada layar |
| C-16 | **Lapis L4 tidak dilonggarkan.** Kandidat yang tertahan di L4 tidak dimasukkan perkakas; pilihan itu diajukan kepada tim sebagai TK-72. Skor relevansi tidak tampil pada S-15 |
| C-20 | Bentuk enam rute ditulis ke D-14 4.6 dan 4.7 sebelum kodenya; tanggapan disusun lewat model pydantic bernama dan dijaga pemeriksa kontrak web |

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 013 tidak menyentuh jalur penjawaban.

### Fitur 034 — 6 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 013. Tidak ada pasal berpindah.

Fitur ini menguatkan enam pasal yang sudah lulus. C-04 untuk pertama kali
**berlaku pada data sungguhan**: sebelum fitur ini gerbang `rekam()` ada,
tetapi tidak ada yang memanggilnya.

| Pasal | Yang bertambah pada fitur 034 |
|---|---|
| C-04 | Persetujuan dibaca dari penyimpan pengguna pada **setiap** pemanggilan perekam; tanpa persetujuan nol peristiwa, sesudah mencabut nol peristiwa baru — diuji lewat HTTP (M-1, M-2) dan lewat peramban terhadap PostgreSQL |
| C-05 | Pemilik peristiwa berpola pseudonim, ditegakkan batasan tabel dan perekam (M-3); `peran_telemetri` tanpa `CONNECT` basis data pseudonim (M-5) |
| C-09 | Setiap peristiwa membawa versi aplikasi dan versi model; peristiwa jawaban membawa versi model tanggapan (M-9) |
| C-14 | Pemilihan beranda dan jalur penjawab tidak membaca peristiwa — diuji dengan menghitung pembacaan penyimpan telemetri: nol |
| C-17 | Perekam hanya menulis tabel peristiwa; jalur penjawaban tidak menerimanya |
| C-20 | Bentuk tanggapan tidak berubah dengan maupun tanpa persetujuan; satu tajuk permintaan opsional ditulis ke D-14 0.14 sebelum kodenya (KB-199) |

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 034 tidak menyentuh jalur penjawaban.

### Fitur 033 — 6 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 034. Tidak ada pasal berpindah.

Fitur ini menguatkan lima pasal yang sudah lulus:

| Pasal | Yang bertambah pada fitur 033 |
|---|---|
| C-04 | Perekaman berhenti seketika saat penarikan diminta — seluruh sesi dicabut, sehingga tidak ada pemilik bagi peristiwa berikutnya; diuji lewat HTTP dengan pengguna yang menyetujui |
| C-05 | Dua peran penarikan, masing-masing tanpa jangkauan ke basis data lainnya (M-6); bukti permintaan tanpa pseudonim sesudah dipenuhi, ditegakkan batasan tabel (M-5); keluaran perkakas tanpa pseudonim |
| C-13 | Satu kalimat peladen dan dua puluh untai layar baru melewati pemeriksa; penjaga jumlah untai peladen naik ke 26 |
| C-17 | Jalur penjawaban dan seluruh peran aplikasi tetap tanpa hak hapus; uji arah menjaga bahwa layanan aplikasi tidak mengimpor penyimpan penarikan (M-7) |
| C-20 | Bentuk `DELETE /saya/data` dan tabel `permintaan_penarikan` ditulis ke D-14 0.15 sebelum kodenya |

**Yang tidak dijangkau sistem, dinyatakan:** pasangan akun dengan orang
sungguhan dipegang tim di luar sistem, sehingga penarikan baru utuh bila
prosedur tim ikut menghapusnya (TK-76).

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 033 tidak menyentuh jalur penjawaban.

*Koreksi atas baris C-13 di atas:* untai layar baru berjumlah **dua puluh
lima** — delapan belas kunci `MIKROKOPI` dan tujuh butir daftar data — bukan
dua puluh. Baris di atas tidak disunting (tambah-saja).

### Fitur 035 — 6 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 033. Tidak ada pasal berpindah.

Fitur ini menguatkan enam pasal yang sudah lulus:

| Pasal | Yang bertambah pada fitur 035 |
|---|---|
| C-04 | Analitik hanya membaca peristiwa yang lahir lewat gerbang `rekam()`; ekspor menulis CSV dari baris tersimpan tanpa membentuk ulang `Peristiwa` di luar gerbang |
| C-05 | `peran_analitik` tanpa akun, profil, riwayat, maupun basis data pseudonim (M-1); jejak ekspor mencatat pseudonim peneliti, bukan nama |
| C-12 | Ekspor Parquet tetap tertahan; S-18 berupa tabel tanpa pustaka grafik |
| C-13 | Satu kalimat peladen dan empat puluh lima untai layar baru melewati pemeriksa; "CSV" dihapus dari mikrokopi karena pemeriksa menolaknya sebagai singkatan sistem |
| C-14 | Metrik dihitung saat diminta dan tidak dibaca pemilihan beranda maupun jawaban |
| C-20 | Bentuk kedua rute dan tabel `ekspor` ditulis ke D-14 0.16 sebelum kodenya; sepuluh model dan satu enum didaftarkan pada pemeriksa kontrak web |

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 035 tidak menyentuh jalur penjawaban.

*Koreksi atas baris C-13 fitur 035 di atas:* untai layar baru berjumlah
**empat puluh delapan** — empat puluh dua kunci `MIKROKOPI` dan enam label
metrik tertunda — ditambah empat fungsi penyusun, bukan empat puluh lima.
Baris di atas tidak disunting (tambah-saja).

### Fitur 036 — 8 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 035. Tidak ada pasal berpindah.

Fitur ini menguatkan delapan pasal yang sudah lulus:

| Pasal | Yang bertambah pada fitur 036 |
|---|---|
| C-04 | `answer_rated` lahir lewat gerbang `rekam()`; tanpa persetujuan, penilaian tetap tersimpan bagi kurator tetapi tidak direkam (R-09) |
| C-05 | Aduan tanpa pseudonim, akun, pengenal percakapan, maupun `id_pesan`, ditegakkan batasan tabel dan penjaga klien; `peran_kurasi` tanpa hak atas skema `riwayat` (M-2); `peran_penilaian` tanpa basis data pseudonim |
| C-07 | `peran_riwayat` menambah tanggapan tanpa dapat membacanya (M-1); jawaban lama hanya tampil pada S-17, dinyatakan sebagai jawaban saat diadukan |
| C-13 | Empat kalimat peladen dan empat puluh untai layar baru — tiga puluh dua kunci `MIKROKOPI`, tiga label nilai, empat label tindak lanjut, satu butir daftar data yang ditarik — ditambah satu fungsi penyusun |
| C-14 | Penilaian tidak dibaca jalur penjawab maupun pemilihan beranda; uji memeriksa jalur menerima pertanyaan saja |
| C-16 | Penilaian tidak menyetel ambang, pengambilan, maupun validator |
| C-17 | Tanggapan dicatat lapisan `api` sesudah jalur penjawab selesai; tindak lanjut tidak mengirim apa pun keluar sistem |
| C-20 | D-14 0.17 sebelum kodenya; satu rute baru atas putusan pemegang gerbang (P-3 B); bentuk `/tanya` tidak berubah; enam model dan dua enum didaftarkan pada pemeriksa kontrak web |

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 036 menyimpan tanggapan, tetapi tidak menyentuh jalur
penjawaban maupun validatornya.

### Fitur 032 — 9 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 036. Tidak ada pasal berpindah.

Fitur ini menguatkan sepuluh pasal yang sudah lulus:

| Pasal | Yang bertambah pada fitur 032 |
|---|---|
| C-02 | Pembaca sumber tidak memegang `isi` korpus, kolom vektor, maupun skema `indeks_metadata` (M-1, M-2); segmen berlisensi tertutup — juga lisensi yang tidak dikenal — tidak tampil sebagai teks |
| C-03 | `peran_pembaca_sumber` dan `peran_koleksi` tanpa hak atas skema karantina; ditolak peladen, bukan oleh kode |
| C-04 | `citation_opened` dan `discovery_saved` lahir lewat gerbang `rekam()`; tanpa persetujuan dan pada permintaan yang ditolak, tidak direkam |
| C-05 | Koleksi dimiliki pseudonim dari sesi; kedua peran baru tanpa basis data pseudonim; `discovery_saved` membawa `ada_catatan` saja (M-12); catatan berdata pribadi ditolak tanpa dikutip (M-11) |
| C-07 | Dokumen `dicabut` dan regulasi tanpa status tercatat tampil tanpa teks (M-7, M-8); status keberlakuan tampil sebelum teks (M-16); butir yang ditarik tetap terbaca dengan penanda dasar berubah sebelum isinya (M-14, M-17); jawaban S-09 tidak disimpan untuk pembaca sumber |
| C-13 | Lima kalimat peladen dan empat puluh delapan untai layar baru — tiga puluh lima kunci `MIKROKOPI`, lima label jenis dokumen, tiga kalimat status, empat kalimat tanpa teks, satu butir daftar data yang ditarik — ditambah tiga fungsi penyusun |
| C-14 | Koleksi tidak dibaca pemilihan beranda: `peran_penayangan` tanpa hak atas `penemuan.koleksi` (M-3); jalur penjawab tidak disentuh |
| C-15 | Tanpa hitungan, poin, maupun lencana koleksi pada S-11 |
| C-17 | Pembaca sumber hanya membaca; status dan metadata dicatat perkakas tim dan gerbang ingesti, bukan jalur penjawaban |
| C-20 | D-14 0.18 sebelum kodenya; dua rute baru atas putusan pemegang gerbang (P-1 A, TK-80); bentuk `/tanya` tidak berubah; lima model dan dua enum didaftarkan pada pemeriksa kontrak web |

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Pembaca sumber menampilkan bagian yang dirujuk sitasi, tetapi
tidak memeriksa dukungan isi klaim; jalur penjawaban dan validatornya tidak
disentuh.

### Fitur 037 — 10 Oktober 2026

**Tagihan tidak menyusut.** `make compliance` melaporkan **19 lulus, 0 gagal,
1 belum** — sama dengan akhir fitur 032. Tidak ada pasal berpindah.

Fitur ini menguatkan lima pasal yang sudah lulus:

| Pasal | Yang bertambah pada fitur 037 |
|---|---|
| C-03 | Karantina dijangkau tiga peran dokumen saja, satu per kredensial kode (M-4); ingesti menaruh tanpa dapat membaca (M-2), verifikator hanya dapat mengeluarkan — hak bawaan skema yang memberinya tambah dan ubah dicabut, juga bagi tabel kelak (M-1, M-3); setiap peran diuji berjalan dengan haknya sendiri |
| C-05 | Kedua peran baru tanpa basis data pseudonim; pelaku pada catatan karantina kode anggota tim, bukan nama, ditegakkan batasan tabel (M-11) |
| C-09 | Keluaran OCR perkakas tercatat ke L2 beserta versi mesin dan sidik model |
| C-12 | Tanpa paket baru: ekstraksi lewat pengekstrak fitur 015, penyamaran dengan pustaka baku |
| C-17 | Penarikan dokumen hanya mengurangi — tidak dapat menyisipkan ke korpus maupun indeks; tanpa rute; jalur penjawaban tidak disentuh |
| C-20 | D-14 0.19 sebelum kodenya; `PutusanGerbang` di kamus, diuji terhadap D-14; tanpa rute baru; bentuk `/tanya` tidak berubah |

#### C-01 ditinjau lagi

Alasan tunggu tetap `"020 VS-03 dukungan isi klaim; menuntut model sematan
dan BT-29"`. Fitur 037 mengisi korpus, tetapi tidak menyentuh jalur
penjawaban maupun validatornya; segmentasi milik baris 038.
