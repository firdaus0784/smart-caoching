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
