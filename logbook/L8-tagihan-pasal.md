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
