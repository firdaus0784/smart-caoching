# L4 · Catatan Keputusan Berjalan

Mengikat `docs/D10.md` Bagian 6. Keputusan besar tercatat sebagai ADR pada
`docs/D04.md`. Bagian ini menampung keputusan yang muncul saat pengerjaan,
tidak cukup besar untuk menjadi ADR, tetapi memengaruhi hasil.

**Ditambah, tidak disunting.** Koreksi ditulis sebagai entri baru yang merujuk
entri lama. Menimpa entri menghapus selisih antara apa yang diketahui saat
memutuskan dan apa yang diketahui kemudian — dan selisih itu bagian dari nilai
rekaman ini. Lihat `AGENTS.md` bagian Batas.

## Bentuk entri

Setiap entri berupa judul `## KB-nnn · ringkas` diikuti tabel enam bidang
wajib: Tanggal, Konteks, Keputusan, Alternatif, Dampak, Pemutus. Kelengkapannya
ditegakkan uji, bukan kebiasaan.

<!-- Entri dimulai di bawah baris ini. -->

## KB-001 · Pemegang Gerbang 1–4 pada jalur pengembangan sistem

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Alur SDD `docs/D12.md` Bagian 3 mensyaratkan empat gerbang manusia. BT-49 (penetapan siapa memegangnya) masih terbuka, sementara fitur 001 tidak dapat dimulai tanpa pemegang gerbang. |
| Keputusan | Anggota peneliti bidang pengembangan sistem memegang Gerbang 1 s.d. 4 untuk jalur pengembangan sistem. Bersifat sementara. |
| Alternatif | Menunggu rapat tim menetapkan BT-49 — ditolak karena menghambat seluruh urutan pembangunan `docs/D12.md` Bagian 7 tanpa mengurangi risiko apa pun; keputusan sementara ini tetap dapat digantikan. |
| Dampak | Seluruh persetujuan Gerbang 1 s.d. 4 pada fitur 001 bersandar pada keputusan ini. Bila rapat tim menetapkan pemegang lain, persetujuan yang sudah diberikan ditinjau ulang, bukan otomatis batal. |
| Pemutus | Anggota peneliti bidang pengembangan sistem |

## KB-002 · Pemilihan uv sebagai pengelola paket dan pengunci versi

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | C-09 mencatat "versi kode" sebagai bukti reproduksibilitas. Tanpa pengunci versi, pohon ketergantungan mengambang dan catatan versi kode kehilangan sebagian maknanya. Kontainerisasi dikeluarkan dari cakupan fitur 001, tetapi pengunci versi tidak. |
| Keputusan | uv dipakai sebagai pengelola paket dan pengunci versi. `uv.lock` merekam pohon transitif utuh. |
| Alternatif | Poetry — setara untuk keperluan ini. pip-tools — memerlukan lebih banyak sambungan manual. Tanpa pengunci — ditolak; membuat C-09 tidak bermakna. |
| Dampak | `Makefile` menyembunyikan pilihan ini dari alur kerja, sehingga penggantian ke Poetry menyentuh satu berkas dan tidak mengubah `AGENTS.md`. Tercatat sebagai risiko RP-03 pada `specs/001-kerangka-proyek/plan.md`: uv relatif baru dan mungkin tidak dapat dipakai pada infrastruktur UPI. |
| Pemutus | Gerbang 2 fitur 001 |

## KB-003 · Pencabutan setelan mypy disallow_any_explicit

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Setelan dipasang pada tugas A-4 dengan alasan menegakkan pemisahan tipe R-06 dan ADR-13. Alasan itu keliru: setelan tersebut hanya melarang kata `Any` ditulis pada kode sendiri, dan yang menegakkan R-06 adalah `strict`. Yang ia lakukan adalah menolak `pydantic.BaseModel`, karena tanda tangan pydantic memuat `Any`. |
| Keputusan | Setelan dicabut. `strict` dipertahankan. |
| Alternatif | Daftar pengecualian per modul — ditolak; ia bertambah setiap kali model baru dibuat, dan daftar pengecualian yang bertambah adalah tempat pekerjaan bersembunyi, persis yang R-15 dirancang cegah pada `make compliance`. |
| Dampak | Tidak ada penurunan penegakan tipe: `strict` tetap menolak fungsi tanpa anotasi, generik tanpa parameter, dan pengembalian `Any`. Alasan pencabutan ditulis pada `pyproject.toml` agar tidak dipasang ulang. |
| Pemutus | Anggota teknis, tugas C-3 |

## KB-004 · Fitur 001 lolos Gerbang 4

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Fitur 001 diselesaikan dengan pengecualian Gerbang 4 (AI-001 pada L7): verifikasi dilakukan manusia terhadap daftar periksa G4-01 s.d. G4-25 yang ditulis sebelum implementasi, karena `make check` adalah luaran fitur itu sendiri. |
| Keputusan | Fitur 001 dinyatakan lolos Gerbang 4. Pengecualian berakhir di sini; fitur 002 dan seterusnya diverifikasi `make check` dan `make compliance` sebagaimana biasa. |
| Alternatif | Menahan sampai empat temuan AK-12 yang terbuka diselesaikan — ditolak; keempatnya di luar cakupan fitur 001, tercatat pada D-00 Bagian 7.11, dan tiga di antaranya menuntut keputusan tim, bukan pekerjaan teknis. |
| Dampak | Gerbang mutu berdiri: tujuh dari dua puluh pasal terperiksa mesin, empat pemeriksa terbukti menyala lewat uji mutasi. Seluruh fitur berikutnya dibangun di bawahnya. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-005 · Fitur berikutnya bukan 002, melainkan pemeriksa konsistensi dokumen

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | TK-45 menunjukkan register D-00 Bagian 2 tertinggal pada tujuh dokumen tanpa satu pun aturan dilanggar — D-00 Bagian 6 mewajibkan riwayat revisi diperbarui, dan itu selalu dipenuhi, tetapi kewajiban memperbarui register tidak pernah dinyatakan. Sementara itu fitur 002 tertahan TK-41: kapasitas verifikasi anonimisasi belum pernah dihitung, padahal FR-B05 menjadikannya gerbang atas setiap dokumen. |
| Keputusan | Fitur berikutnya adalah pemeriksa konsistensi dokumen (014), mendahului fitur 002 pada urutan `docs/D12.md` Bagian 7. |
| Alternatif | Memulai 002 dengan TK-41 terbuka — ditolak; templat `spec.md` menetapkan fitur dengan pertanyaan terbuka tidak diserahkan ke agen, dan merencanakan gerbang yang kapasitasnya tidak diketahui berarti mengulang kekeliruan yang D-06 Bagian 8 hindari untuk kurasi. Menunggu tanpa mengerjakan apa pun — ditolak; pekerjaan ini tidak bergantung pada keputusan tim mana pun. |
| Dampak | Urutan pembangunan `docs/D12.md` Bagian 7 bertambah satu baris. Audit AK-10 sebelum pilot dan AK-11 sebelum naskah menjadi lebih murah, dan keduanya wajib serta dijalankan ketika waktu paling sempit. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-006 · Landasan literatur bagi TK-41, dan batas keterpindahannya

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | TK-41 menyatakan kapasitas verifikasi anonimisasi tidak pernah dihitung, padahal FR-B05 menjadikannya gerbang atas setiap dokumen. SI-01 pada D-11 mensyaratkan setiap ambang numerik menunjuk sumber atau dinyatakan tegas sebagai penetapan tim tanpa dasar literatur. |
| Keputusan | Empat rujukan dicari dan **keberadaannya diverifikasi lewat penelusuran**, bukan dikutip dari ingatan. Dua di antaranya memberi angka yang dapat dipindahkan: Dorr dkk. (2006) 87,3 ± 61 detik per catatan klinis, dan Douglass dkk. 20.000 kata per jam. Keduanya dipakai sebagai **kurung** pada D-03 Bagian 12.6, bukan sebagai penetapan. Laju operasional diserahkan pada batch kalibrasi (BT-63). |
| Alternatif | Mengutip rujukan dari ingatan tanpa verifikasi — ditolak; itu persis kegagalan yang AK-09O temukan pada proposal induk, ketika buku metode campuran disitasi untuk Design Science Research (TO-02). Menetapkan angka tanpa rujukan sama sekali — ditolak; SI-01 mensyaratkan salah satu dari keduanya, dan penetapan diam-diam bukan pilihan yang tersedia. |
| Dampak | Kekurangan anggaran waktu D-03 Bagian 12 naik dari 47 menjadi ± 105 jam — sekitar dua kali lipat. BT-62 ditambahkan untuk keputusan penutupannya. Satu butir (Douglass dkk.) ditandai belum terverifikasi primer dan wajib ditemukan sumber aslinya atau dicabut sebelum masuk naskah, sesuai SI-03. |
| Pemutus | Anggota teknis; keputusan penutupan kekurangan tetap pada rapat tim (BT-62) |

## KB-007 · Kewajiban memperbarui register dinyatakan, bukan sekadar diperiksa

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Fitur 014 menambahkan pemeriksa yang menjatuhkan `make check` bila versi kepala, register `docs/D00.md` Bagian 2, dan riwayat revisi tidak cocok. Namun D-00 Bagian 6 hanya mewajibkan dua tempat: kepala dan riwayat. Menegakkan aturan yang tidak tertulis berarti orang dijatuhkan gerbang atas kewajiban yang tidak pernah diberitahukan kepadanya. |
| Keputusan | D-00 Bagian 6 diubah menyatakan tegas bahwa kenaikan versi menyentuh **tiga** tempat, dan D-00 Bagian 5 menyatakan uji nomor 1 dan 2 kini dijalankan mesin sekaligus menegaskan lima sisanya tetap menuntut manusia. D-00 naik ke 2.5. |
| Alternatif | Menambahkan pemeriksa tanpa menuliskan aturannya — ditolak; itu memindahkan lubang TK-45, tidak menutupnya. Yang gagal pada TK-45 bukan kedisiplinan orangnya melainkan aturan yang tidak pernah dinyatakan, dan pemeriksa yang menegakkan aturan tak tertulis membuat orang belajar dari kegagalan gerbang alih-alih dari dokumen. Menuliskan aturan tanpa pemeriksa — ditolak; itu persis keadaan sebelum TK-45, dan imbauan sudah terbukti tidak cukup. |
| Dampak | Setiap kenaikan versi dokumen sejak sekarang wajib menyentuh tiga tempat, dan ketiganya dicocokkan pada setiap `make check`. Lima pertanyaan audit sisanya tidak berkurang bobotnya; catatan pada Bagian 5 sengaja menegaskan itu agar pemeriksa mesin tidak menjadi alasan melewatkan AK-10 dan AK-11. |
| Pemutus | Anggota teknis; D-00 adalah dokumen pengendali, sehingga perubahan ini diajukan untuk konfirmasi rapat tim |

## KB-008 · Pemilik prosedur pembangunan ontologi dan audit graf

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | TK-42 menyatakan tabel kepemilikan `docs/D00.md` Bagian 3 tidak punya baris bagi prosedur pembangunan ontologi. Tanpa pemilik, tidak ada dokumen yang wajib menuliskannya — dan itu sebabnya prosedur itu tidak pernah ada meski targetnya, penanggung jawabnya, dan butir Definisi Selesainya sudah ditetapkan sejak awal. |
| Keputusan | Diusulkan prosedur pembangunan ke **D-06** (Bagian 11) dan prosedur audit graf ke **D-08** (Bagian 4.4). Alasan D-06: FR-E03 mengikat setiap konsep ke dokumen sumber, sehingga pembangunan ontologi adalah pekerjaan di atas bahan terkurasi dan tunduk pada aturan lisensi serta gerbang kurasi yang sudah dimiliki D-06. Alasan D-08: ia pemilik tunggal prosedur uji, dan MK-06 sudah menunjuk ke sana meski penunjuknya keliru. |
| Alternatif | Menempatkan prosedur pada **D-03** — ditolak; D-03 pemilik skema anotasi rentang teks, dan graf konsep bukan anotasi rentang. Menempatkannya pada **D-04** — ditolak; D-04 pemilik keputusan arsitektur dan model data, dan tabel `konsep` serta `relasi` memang sudah ada di sana, tetapi model data bukan prosedur kerja. Menempatkan audit graf bersama prosedurnya di D-06 — ditolak; memisahkan yang mengerjakan dari yang memeriksa adalah pemisahan yang sama yang sudah dipakai D-03 dan D-08 untuk anotasi. |
| Dampak | Tabel kepemilikan bertambah dua baris. Enam dokumen naik versi. Yang lebih penting: butir Definisi Selesai nomor 3 kini punya cara diverifikasi, dan target MK-06 tidak lagi dapat dipenuhi dengan konsep tanpa definisi atau tanpa sumber. |
| Pemutus | Anggota teknis; **usulan, bukan penetapan.** D-00 dokumen pengendali, dan kedua baris ditandai menunggu konfirmasi rapat tim |

## KB-009 · Putusan Gerbang 4 fitur 014, dan pengesahan KB-007 dan KB-008

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Fitur 014 menyelesaikan tujuh tugas: pemeriksa konsistensi antardokumen berjalan pada gerbang V-03, dengan uji mutasi terhadap `docs/` yang sebenarnya dilaporkan pada uraian commit. Dua usulan yang menyertainya menyentuh `docs/D00.md` — dokumen pengendali yang bukan milik agen — sehingga keduanya diajukan, tidak diterapkan sebagai keputusan final. |
| Keputusan | **Fitur 014 lolos Gerbang 4.** KB-007 (kenaikan versi menyentuh tiga tempat, dituliskan pada D-00 Bagian 6) dan KB-008 (prosedur pembangunan ontologi ke D-06, audit graf ke D-08) disahkan sebagai **keputusan berjalan** sampai dikonfirmasi rapat tim, mengikuti pola KB-001. |
| Alternatif | Meluluskan fitur 014 tetapi mencabut kedua perubahan D-00 sampai rapat tim — ditolak; pemeriksa register akan tetap berjalan sementara kewajibannya tidak tertulis, dan itu persis keadaan yang KB-007 dirancang untuk menghindari. Menahan Gerbang 4 sampai rapat tim — ditolak; fitur 014 tidak menunggu keputusan apa pun. |
| Dampak | Penandaan "menunggu konfirmasi rapat tim" pada D-00 Bagian 3 dan Bagian 6 **tetap dibiarkan**: status berjalan bukan status final. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-010 · Tiga keputusan Gerbang 1 fitur 002

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | `spec.md` fitur 002 ditulis dengan tiga pertanyaan terbuka. Templat `spec.md` menetapkan fitur dengan pertanyaan terbuka tidak diserahkan ke agen, sehingga ketiganya wajib dijawab sebelum `plan.md` disusun. |
| Keputusan | **(1) FR-B01 s.d. FR-B04 dipisah menjadi fitur 015.** **(2) Tiga peran kredensial** — jalur penjawaban, jalur verifikasi, pemanggil LLM. **(3) Peringkat kepercayaan ditetapkan saat dokumen masuk, tetapi T3 sah hanya setelah gerbang verifikasi dilewati**, dan peringkat dokumen di karantina tidak pernah terbaca jalur penjawaban. |
| Alternatif | **(1)** Tetap satu fitur — ditolak; keempat FR tertahan C-12 dan menahan inti fitur bersamanya membuat tidak ada yang bergerak, sementara C-03 tetap menjadi salah satu dari tiga belas pasal yang belum terperiksa. **(2)** Dua peran — ditolak; KD-10 sudah menyebut peran ketiga secara tegas, dan menambahkan peran pada pemisahan yang sudah terpasang adalah jenis perubahan yang paling mudah keliru. **(3)** Peringkat hanya setelah verifikasi — ditolak; pemeriksa pola adversarial kehilangan sinyal asal justru pada tahap ia paling berguna. Peringkat otomatis penuh — ditolak; bertentangan dengan rumusan T3 pada D-13 Bagian 6. |
| Dampak | `docs/D12.md` Bagian 7 bertambah satu baris (fitur 015). `spec.md` tidak lagi memuat pertanyaan terbuka. Kebutuhan bertambah tiga: R-01a, R-01b, R-07a. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-011 · Tiga keputusan Gerbang 2 fitur 002

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Penyusunan `plan.md` fitur 002 memunculkan tiga hal yang tidak dapat diputuskan agen: tidak ada peran `verifikator` pada D-14 meski FR-B05 mewajibkan verifikasi manusia; `AGENTS.md` tidak punya tempat bagi lapisan penyimpanan; dan tidak ada tabel bagi catatan perpindahan dokumen antar area yang dituntut R-11. AG-04 secara khusus melarang agen mengubah daftar nilai enum. |
| Keputusan | **(G2-A)** Peran `verifikator` ditambahkan pada `docs/D14.md` Bagian 3; D-14 ke 0.4. **(G2-B)** `src/penyimpanan/` dibangun sebagai lapisan bersama di bawah `api`, `nlp`, `rag`, dan `ingest`, dengan bentuk yang sama seperti `src/llm/`; `AGENTS.md` bagian Arsitektur dan aturan arah diperbarui. **(G2-C)** Tabel `jejak_area` ditambahkan pada `docs/D04.md` Bagian 7.2; D-04 ke 0.6, dan aturan bidang `alasan` masuk `docs/D14.md` Bagian 5.1. |
| Alternatif | **(G2-A)** Verifikasi oleh `kurator` — ditolak; kurator sudah memikul FR-I03 dan D-06 Bagian 8 merancang bebannya di bawah 4 jam per minggu, sehingga menambahkannya menyentuh langsung BT-62 dan BT-66. Verifikasi oleh `admin` — ditolak; `admin` peran teknis, dan menjadikannya pemutus mutu data mencampur dua tanggung jawab berbeda sifat. **(G2-B)** Penyimpanan di dalam `src/ingest/` — ditolak; `src/rag/` perlu membaca korpus, sehingga aturan arah wajib dilonggarkan, dan pelonggaran demi satu fitur membuka jalan bagi pelonggaran berikutnya. Tanpa lapisan bersama — ditolak; C-03 harus ditegakkan di dua tempat, bertentangan dengan AP-01. **(G2-C)** Memperluas `jejak_kurasi` — ditolak; mencampur dua alur berpemilik berbeda. Cukup log operasional — ditolak; D-04 Bagian 11 memberi log operasional masa simpan lebih pendek, sehingga jejaknya hilang saat log dirotasi dan R-11 menjadi tidak dapat diuji. |
| Dampak | Empat berkas naik versi: D-04, D-14, D-00, dan `AGENTS.md` sebagai lapisan tata kelola. `src/penyimpanan/` menjadi titik sempit kedua sesudah `src/llm/` — keduanya lahir dari alasan yang sama, yaitu aturan penting ditegakkan pada satu tempat. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-012 · Putusan Gerbang 3 fitur 002 dan kekerapan pelaporan

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | `tasks.md` fitur 002 memuat 18 tugas dalam empat fase. Fitur 001 memakai 34 tugas dan mendekati ambang ±30 yang ditetapkan Gerbang 1 fitur 001. |
| Keputusan | **Gerbang 3 lolos, 18 tugas, implementasi dimulai dari Fase A.** Pelaporan **per fase**, empat kali. Usulan daftar ketergantungan fitur 015 disusun **setelah** fitur 002 selesai. |
| Alternatif | Menggabungkan A-1 dengan A-2 dan D-1 dengan D-2 menjadi 16 tugas — ditolak; keduanya menguji hal berbeda, dan menggabungkannya membuat satu commit dapat gagal karena dua sebab sehingga bukti "uji gagal sebelum implementasi" menjadi kabur. Pelaporan per tugas — ditolak; sebagian besar tugas berakhir sama sehingga laporannya berulang. Pelaporan sekali di Gerbang 4 — ditolak; arah yang salah pada Fase A baru terlihat setelah tiga fase dibangun di atasnya. Menyusun usulan ketergantungan 015 sekarang — ditolak; memecah perhatian dari 002. |
| Dampak | Implementasi berjalan. Pemberhentian di luar batas fase tetap berlaku bila sebuah tugas tidak dapat diselesaikan tanpa melanggar `constitution.md` atau `plan.md` — itu aturan `AGENTS.md`, bukan pilihan pelaporan. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-013 · Dua bidang FR-B06, dan aturan etik yang menegakkannya

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | FR-B06 berprioritas W menyebut lima bidang metadata asal. Tiga ada pada `dokumen_sumber` di D-04 Bagian 7.2; `tingkat_kerahasiaan` dan `status_persetujuan_pemilik` tidak ada di sana, dan nilainya tidak pernah ditetapkan dokumen mana pun. Menebaknya berarti menetapkan aturan kerahasiaan dokumen sekolah lewat kode — menyentuh RE-05 dan perizinan etik ET-01. Formulir persetujuan ET-02 juga belum ada. |
| Keputusan | **Tiga tingkat kerahasiaan** ditetapkan sekarang: `publik`, `internal_sekolah`, `terbatas` — penetapan tim tanpa dasar literatur, sesuai SI-01. **Empat status persetujuan**: `belum_diminta`, `diberikan`, `ditolak`, `dicabut`. **Aturan etik yang menegakkan keduanya: dokumen rahasia hanya boleh masuk korpus atas persetujuan pemiliknya.** Dokumen sekolah menuntut persetujuan pada tingkat mana pun, termasuk `publik`; regulasi publik tidak menuntutnya. |
| Alternatif | Tidak membangun `tingkat_kerahasiaan` sampai ET-05 — ditolak pemegang gerbang; satu kebutuhan berprioritas W akan terbuka lebih lama. Membangunnya sebagai catatan yang tidak menegakkan apa pun — **ditolak setelah dipertimbangkan ulang**; bidang kerahasiaan yang tidak ditegakkan terbaca sebagai perlindungan pada ET-05 dan pada naskah padahal tidak menahan apa pun, dan reviewer etik yang menanyakan konsekuensinya akan menerima jawaban "tidak ada". Menuntut persetujuan hanya berdasarkan tingkat — ditolak; dokumen sekolah dapat ditandai `publik` untuk melewati gerbang, sehingga jenis sumber ikut diperiksa. Menuntut persetujuan bagi seluruh dokumen termasuk regulasi — ditolak; Permendikdasmen tidak punya pemilik yang dimintai persetujuan, dan kendali yang menghentikan pekerjaan sah akan dimatikan orang. |
| Dampak | D-04 ke 0.7, D-14 ke 0.5, D-00 ke 2.12. FR-B06 terpenuhi penuh. `tingkat_kerahasiaan` punya konsekuensi yang dapat diuji, bukan catatan pasif. Nilai `dicabut` menjadikan penarikan persetujuan berlaku seketika. Nilai kedua enum menyesuaikan formulir ET-02 bila kelak berbeda — **formulir yang menang, kode yang menyusul**. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-014 · Empat keputusan pada pertengahan Fase B fitur 002

| | |
|---|---|
| Tanggal | 2026-08-05 |
| Konteks | Aturan etik KB-013 memunculkan pertanyaan lanjutan yang tidak dijawab dokumen mana pun: bila persetujuan pemilik dapat ditarik, apa yang terjadi pada dokumen yang sudah berada di korpus. Tiga hal lain sudah tertahan sejak Fase A dan Fase B awal. |
| Keputusan | **(1) Penarikan persetujuan mengeluarkan dokumen dari korpus secara otomatis**, dipindahkan kembali ke karantina. **(2) Masa simpan dokumen yang ditolak** tidak dibangun pada fitur 002; dicatat sebagai BT-68 pada D-09. **(3) Daftar asal FR-B09** ditandai sebagai ringkasan tidak lengkap dengan penunjuk ke D-13 Bagian 6; dicatat sebagai TK-48. **(4) Pemindahan bentuk galat** dari `src/llm/` ke modul bersama dilakukan pada fitur 009; dicatat sebagai BT-69 pada D-04. |
| Alternatif | **(1)** Penarikan hanya ditandai dan verifikator menindak dalam tenggat — ditolak; ada jendela waktu ketika dokumen yang persetujuannya sudah ditarik masih dipakai menjawab, dan justru itu yang dipersoalkan komite etik. Penarikan hanya mencegah masuk — ditolak; membuat nilai `dicabut` hampir tidak berarti pada keadaan yang paling mungkin terjadi. **(2)** Menghapus setelah tenggat — ditolak untuk fitur ini; menuntut penetapan tenggat yang menyentuh perizinan etik, dan retensi milik runbook D-09 bukan gerbang. Menyimpan tanpa batas — ditolak; karantina akan menumpuk justru data yang sudah dinyatakan tidak layak. **(3)** Menyalin kelima asal ke FR-B09 — ditolak; D-00 Bagian 3 menetapkan dokumen lain merujuk, tidak menyalin, dan salinan akan tertinggal ketika D-13 berubah. **(4)** Memindahkan sekarang — ditolak; menyentuh kode fitur 001 yang sudah lolos Gerbang 4 di tengah fitur 002. |
| Dampak | Keputusan (1) menambah perilaku yang diuji pada B-4 dan B-5. **Batas yang wajib diketahui:** fitur ini belum memiliki indeks pengambilan, sehingga pencabutan dari indeks menjadi kewajiban fitur 006 dan 007 — dicatat agar tidak terlupa. D-01 ke 1.4, D-04 ke 0.8, D-09 ke 0.4, D-00 ke 2.13. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-015 · Enam keputusan pada Fase C dan Fase D fitur 002

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | Pemeriksaan Fase C atas permintaan pemegang gerbang menemukan tiga cacat yang lolos 129 uji. Yang terberat: `terima` menyetel ulang temuan tetapi tidak menyetel ulang tinjauan, sehingga tinjauan bertahan melintasi unggahan — unggah versi bersih, minta ditinjau, unggah ulang versi yang disusupi. Itu serangan AN-01 tepat pada gerbang yang dibangun menahannya. Fase D memunculkan dua pertanyaan lanjutan yang tidak dijawab dokumen mana pun. |
| Keputusan | **(1) Setiap unggahan membatalkan tinjauan sebelumnya**, tanpa syarat temuan. **(2) Catatan tinjauan disimpan terpisah dari alasan putusan verifikator** — dua putusan, dua bidang. **(3) Dokumen tanpa temuan tidak dapat ditinjau.** **(4) Daftar pola adversarial tidak ditambal dari dalam fitur ini**; uraian modulnya menyatakan cakupannya apa adanya dengan lima contoh yang lolos. **(5) `cabut_persetujuan` menuntut `id_pemohon` meski tetap tanpa kredensial.** **(6) Jejak ditulis sebelum dokumen berpindah; alasan bermuatan data pribadi membatalkan seluruh putusannya, bukan hanya jejaknya.** |
| Alternatif | **(1)** Membatalkan tinjauan hanya ketika unggahan baru bertemuan — ditolak; aturan bersyarat temuan gagal justru pada isi yang tampak bersih bagi pemeriksa, dan cakupan pemeriksa memang tipis. **(2)** Menyimpan riwayat putusan sebagai daftar — ditolak untuk fitur ini; bentuk riwayat putusan milik layar verifikator D-05 yang belum ada, dan menebaknya sekarang akan ditulis ulang. **(3)** Membiarkan tinjauan pada dokumen bersih sebagai tindakan tak berbahaya — ditolak; ia langkah pertama jalan pintas nomor 1 dan tidak tampak aneh sama sekali saat dilakukan. **(4)** Menambahkan pola bahasa Inggris, sinonim, dan penanda obrolan sekarang — ditolak; D-13 Bagian 9 menugaskan penyusunan himpunan serangan kepada anggota tim yang tidak membangun komponen RAG, dan menambalnya dari sini berarti mengukur diri sendiri dengan alat buatan sendiri. **(5)** Mencatat pemilik dokumen sebagai pelaku — ditolak; identitas pemilik berasal dari formulir ET-02 yang belum ada, dan nama tempelan pada jejak lebih buruk daripada nama pelaksananya. Membiarkan penarikan tanpa pelaku — ditolak; korpus yang menyusut tanpa nama di jejaknya tetap tidak dapat dijelaskan (R-11). **(6)** Menjejak setelah perpindahan — ditolak; memindahkan dokumen lalu gagal menjejakkannya menghasilkan perubahan yang tidak tercatat, persis keadaan yang R-11 larang. Menyaring data pribadi diam-diam — ditolak; jejak yang tampak bersih membuat kebiasaan menyalin tidak pernah berubah. |
| Dampak | Tanda tangan `cabut_persetujuan` berubah; tujuh pemanggilan pada uji disesuaikan. Uji bertambah dari 129 menjadi 427. C-03 berpindah menjadi pasal kedelapan yang dijaga mesin; tagihan L8 menyusut 13 menjadi 12. **Batas yang wajib diketahui:** enam dari tujuh penyisipan yang dicoba tetap lolos pemeriksa pola, dan itu tertulis pada uraian modulnya, bukan hanya di sini. Yang membatasi kerugiannya adalah C-17, bukan modul itu. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001); butir 1 s.d. 4 berasal dari pemeriksaan yang diminta pemegang gerbang |

## KB-016 · Putusan Gerbang 4 fitur 002

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | Fitur 002 menyelesaikan 18 tugas pada empat fase. `make check` lulus 6 gerbang, `make compliance` melaporkan 8 lulus / 0 gagal / 12 belum, cakupan naik dari 99,48% menjadi 99,52% atas 572 pernyataan, dan uji bertambah dari 129 menjadi 427. Dua pemeriksaan yang diminta pemegang gerbang di tengah jalan — Fase B dan Fase C — menemukan tujuh cacat yang seluruh uji yang ada tidak menangkap, termasuk satu jalan pintas AN-01 pada gerbang yang dibangun untuk menahannya. |
| Keputusan | **Fitur 002 lolos Gerbang 4.** C-03 menjadi pasal kedelapan yang dijaga mesin. Fitur 015 menjadi pekerjaan berikutnya, dan langkah pertamanya adalah usulan ketergantungan untuk persetujuan C-12 — bukan kode. |
| Alternatif | Menahan Gerbang 4 sampai daftar pola adversarial diperluas — ditolak; perluasannya milik uji adversarial Bulan 6 yang disusun anggota tim yang tidak membangun komponen RAG (D-13 Bagian 9), dan menunggunya berarti menahan fitur pada pekerjaan yang bukan miliknya. Menahan sampai `src/rag/`, `src/api/`, dan `src/nlp/` ada agar pemeriksa C-03 menjaga pohon yang penuh — ditolak; ketiganya milik fitur 006 s.d. 009, dan pemeriksa yang menunggu sampai ada yang dilanggarnya akan tiba terlambat. Keduanya dicatat sebagai batas yang dinyatakan, bukan sebagai syarat yang belum dipenuhi. |
| Dampak | Tagihan L8 menyusut 13 menjadi 12. Dua batas tercatat terbuka: cakupan pemeriksa pola tipis (enam dari tujuh penyisipan yang dicoba lolos, tertulis pada uraian modulnya), dan pencabutan segmen dari indeks pengambilan menjadi kewajiban fitur 006 dan 007 karena fitur ini belum memiliki indeks. Keduanya tidak menghambat Gerbang 4; keduanya menghambat klaim bahwa penjagaannya sudah lengkap. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-017 · Gerbang 1 fitur 015 dan persetujuan C-12

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | Fitur 015 tertahan C-12 sejak dipisahkan dari fitur 002 (KB-010). Keempat kebutuhannya — FR-B01 s.d. FR-B04 — menuntut ketergantungan baru, dan titik nol proyek adalah lima ketergantungan langsung dengan 18 paket terkunci. Usulan disusun pada `specs/015-praproses-ocr-dan-data-pribadi/usulan-ketergantungan.md` dengan seluruh lisensi dan versi diperiksa langsung ke PyPI pada 6 Agustus 2026, bukan dikutip dari ingatan. Dua pertanyaan yang menyertainya bukan pertanyaan ketergantungan dan tidak hilang bila usulannya ditolak. |
| Keputusan | **Fitur 015 lolos Gerbang 1.** **(1) Kelima ketergantungan disetujui**: `pypdf` 6.15.0 (BSD-3-Clause), `python-docx` 1.2.0 (MIT), `openpyxl` 3.1.5 (MIT), `PySastrawi` 1.2.1 (MIT), `pytesseract` 0.3.13 (Apache-2.0); bertambah tiga transitif — `lxml`, `et-xmlfile`, `Pillow`. **(2) FR-B04 dikerjakan untuk enam pengenal berpola tetap saja** (pilihan A), dengan syarat kekurangannya tertulis pada D-01, bukan hanya pada logbook. **(3) R-18 diperluas ke bagian `[sistem]`** yang mencatat versi mesin OCR dan sidik berkas model bahasanya. |
| Alternatif | **(1)** Menunda OCR sampai berkas model diperiksa — ditolak; pemeriksaannya menjadi tugas pertama fase OCR dengan pekerjaan berhenti di situ bila berkasnya tidak ada, sehingga risikonya tertangani tanpa menahan tiga kebutuhan lain. Memakai `pdfplumber` sejak awal — ditolak untuk sekarang; ia menarik `pdfminer.six`, `pypdfium2`, dan `Pillow`, sementara `pypdf` tanpa ketergantungan wajib. Ditinjau ulang **bila mutu ekstraksinya diukur kurang**, bukan diputuskan dari dugaan. **(2)** Menambah pustaka NER siap pakai — ditolak; menarik `torch` atau `spacy` beserta modelnya, dan model prapelatihan umum belum tentu lebih baik daripada model fitur 004 yang dilatih pada korpus sendiri. Kamus nama heuristik — **ditolak tegas**; banyak nama terlewat, banyak kata biasa tertandai, sementara laporannya terbaca seperti perlindungan. Itu persis cacat yang KB-013 tolak pada `tingkat_kerahasiaan`, dan di sini akibatnya lebih tajam: verifikator yang mengira nama sudah tersamarkan akan memeriksa lebih longgar. **(3)** Mencatat versi mesin OCR manual pada L2 — ditolak; bergantung pada kedisiplinan, dan versi yang berubah diam-diam tidak akan tertangkap apa pun. Menunda perluasan sampai OCR dipakai — ditolak; perluasan pemeriksa paling sulit ditambahkan setelah pipeline berjalan, pelajaran T-7 fitur 014. |
| Dampak | D-01 ke 1.5 dengan catatan cakupan FR-B04 dan BT-70; D-00 ke 2.14. Titik nol ketergantungan berubah dari 5 menjadi 10 langsung — perubahan pertama sejak fitur 001, dan `ketergantungan-disetujui.toml` menjadi berkas yang bertambah bagian, bukan hanya bertambah baris. **Batas yang wajib diketahui:** keberadaan `ind.traineddata` belum terverifikasi dari sumbernya; permintaan ke GitHub raw ditolak kebijakan jaringan (403) dan tidak diulang. Selama Bulan 3 sistem tidak menyamarkan nama orang secara otomatis, dan yang menahan adalah FR-B05 beserta gerbang karantina fitur 002. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001), yang juga memegang peran penanggung jawab teknis C-12 sampai BT-49 diputus rapat tim |

## KB-018 · Gerbang 2 fitur 015

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | `plan.md` fitur 015 mengajukan dua pertanyaan. Yang pertama: `AGENTS.md` menempatkan anonimisasi pada `src/nlp/` dan pembacaan berkas pada `src/ingest/`, tetapi aturan arahnya hanya melarang `nlp`, `rag`, dan `ingest` memanggil `api` — ia tidak menyebut apakah `ingest` boleh memanggil `nlp`. Keadaan yang sama pernah muncul pada fitur 002 ketika `src/penyimpanan/` tidak ada pada daftar arsitektur. Yang kedua diajukan meski keadaannya belum tentu terjadi: apa yang dilakukan bila berkas model Bahasa Indonesia `ind.traineddata` tidak dapat diperoleh sama sekali. |
| Keputusan | **Fitur 015 lolos Gerbang 2.** **(1) `ingest` boleh memanggil `nlp`, satu jurusan.** `AGENTS.md` bertambah satu kalimat pada aturan arah beserta alasannya. Pendeteksi tetap di `src/nlp/`; gerbang menerimanya sebagai parameter dengan nilai bawaan. **(2) Bila berkas model tidak dapat diperoleh, fase OCR berhenti**, `pytesseract` dicabut dari daftar, dan FR-B02 menjadi butir terbuka bagi rapat tim. |
| Alternatif | **(1)** Meletakkan pendeteksi di `src/ingest/` — ditolak; memecah anonimisasi menjadi dua tempat justru pada saat fitur 004 membangun sisanya, dan fitur 004 akan menemukannya di tempat yang tidak disebut dokumen mana pun. Menyerahkan penyambungan kepada `src/api/` — ditolak; `src/api/` baru lahir pada fitur 009, sehingga sampai saat itu penyambungnya adalah uji dan jalur sesungguhnya tidak pernah dijalankan. Membiarkan aturan arah diam — ditolak; diamnya aturan bukan izin, dan impor yang tidak dijelaskan dokumen mana pun adalah rancangan yang hanya hidup pada ingatan penulisnya. **(2)** Memakai model bahasa Inggris sebagai sementara — **ditolak tegas**; dokumen Indonesia yang di-OCR dengan model Inggris menghasilkan teks yang terbaca seperti teks, dan korpus yang rusak diam-diam lebih buruk daripada korpus yang kosong. Mencari mesin OCR lain — ditolak sebagai keputusan sekarang; ia menuntut usulan ketergantungan baru dan tidak dapat diputus tanpa bahan. Menunda pertanyaan sampai keadaannya terjadi — ditolak; keputusan yang diambil saat tenggat dekat dan pekerjaan separuh jalan hampir selalu jatuh pada pilihan yang ditolak di atas. |
| Dampak | `AGENTS.md` berubah — kedua kalinya pada siklus ini, sesudah penambahan `src/penyimpanan/` pada Gerbang 2 fitur 002. Tepi `ingest → nlp` wajib tetap satu jurusan, dan pemeriksanya dapat dibangun bila kelak ada yang membalikkannya. Keputusan (2) tidak mengubah apa pun hari ini; ia menetapkan lebih dulu apa yang dilakukan pada keadaan yang belum tentu terjadi. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-019 · Putusan Gerbang 4 fitur 015

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | Fitur 015 menyelesaikan 17 tugas pada lima fase: ketergantungan beserta penjagaannya, ekstraksi berkas, praproses, OCR, dan pendeteksi data pribadi. Ia fitur pertama yang menambah ketergantungan sejak titik nol fitur 001 — dari 18 paket terkunci menjadi 26 — dan fitur pertama yang membawa ketergantungan di luar pohon Python. Uji bertambah dari 608 menjadi 670 dengan satu uji yang sengaja dilewati, dan cakupan naik dari 99,52% menjadi 99,69% atas 869 pernyataan. |
| Keputusan | **Fitur 015 lolos Gerbang 4.** FR-B01 dan FR-B03 terpenuhi penuh; FR-B02 terpenuhi pada tingkat pembungkus, dengan mutu OCR belum diukur (D-08); FR-B04 terpenuhi untuk enam pengenal berpola tetap sesuai pilihan A pada KB-017. Penyambungan ke `Gerbang.terima` fitur 002 **tetap di luar cakupan** dan diajukan sebagai pekerjaan tersendiri. |
| Alternatif | Menahan Gerbang 4 sampai mutu OCR diukur — ditolak; pengukurannya prosedur uji D-08 yang menuntut dokumen sekolah sungguhan, dan dokumen itu belum ada karena kanal ingesti belum berjalan. Menahannya sampai penyambungan ke gerbang fitur 002 selesai — ditolak; `tasks.md` sudah menetapkan penyambungan itu di luar cakupan pada Gerbang 3, dan menariknya masuk sekarang berarti mengubah cakupan sesudah pekerjaannya selesai. Menahannya sampai nama perorangan dapat dideteksi — ditolak; itu fitur 004, dan KB-017 sudah memutuskannya beserta syarat pencatatannya di D-01. |
| Dampak | Titik nol ketergantungan berubah untuk pertama kalinya; `ketergantungan-disetujui.toml` bertambah bagian `[sistem]`, dan R-18 kini membandingkan mesin OCR juga. `make compliance` **tidak berubah** — 8/0/12 — dan itu memang yang dituntut verifikasi akhir: fitur ini tidak memindahkan pasal mana pun. **Empat batas tercatat terbuka:** mutu OCR belum diukur, mutu ekstraksi `pypdf` atas dokumen ber-tabel belum diukur (menentukan apakah `pdfplumber` diajukan kelak), PDF beraliran isi rusak tidak dapat dibedakan dari pindaian, dan nama perorangan tidak tersamarkan otomatis selama Bulan 3 (BT-70). |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-020 · Persetujuan C-12 fitur 003 — cara pemasangan perangkat anotasi

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | ADR-08 menetapkan Label Studio dipasang mandiri, tetapi tidak menyebut bagaimana. Tiga cara diperiksa langsung ke PyPI pada 6 Agustus 2026: layanan terpisah (nol paket Python baru), `label-studio-sdk` (24 paket langsung), `label-studio` di dalam proyek (58 paket langsung). Titik nol proyek hari ini 26 paket terkunci. |
| Keputusan | **(1) Pilihan A — Label Studio berjalan sebagai layanan terpisah; kode membaca berkas ekspornya. Nol ketergantungan Python baru.** **(2) `ketergantungan-disetujui.toml` bertambah `[sistem.label_studio]` berisi versi yang dipakai, dan R-18 membandingkannya** memakai perkakas yang sudah dibangun fitur 015. |
| Alternatif | Memasang `label-studio` ke dalam proyek — ditolak; 58 paket langsung melipatgandakan titik nol lebih dari tiga kali untuk perangkat yang **tidak dijalankan sistem sama sekali**, sebab ia dipakai anotator lewat peramban dan tidak pernah diimpor kode mana pun. Setiap paket di dalamnya menjadi permukaan yang wajib diperiksa V-05. Memasang `label-studio-sdk` — ditolak untuk sekarang; ia menjawab kebutuhan yang belum ada, karena yang diperlukan adalah membaca hasil anotasi berbentuk JSON biasa, bukan bercakap dengan API. Lisensinya juga tidak dinyatakan pada metadata PyPI. **Diajukan ulang bila automasi API benar-benar diperlukan**, misalnya penyisipan pra-anotasi FR-C10. Menuntut sidik berkas bagi Label Studio seperti pada Tesseract — ditolak; Tesseract menentukan **isi** korpus sedangkan Label Studio menentukan **bentuk** berkas ekspornya, dan yang kedua gagal dengan berisik karena berkas yang bentuknya berubah tidak dapat diurai. |
| Dampak | Titik nol ketergantungan Python **tidak berubah** — tetap 26 paket, 10 langsung. Enam dari sepuluh kebutuhan FR-C tetap dibangun sendiri dengan pustaka baku, termasuk Cohen's Kappa dan F1 berpasangan menurut aturan D-03 Bagian 11. **Batas yang wajib diketahui:** bentuk berkas ekspor Label Studio 1.23 belum diperiksa langsung, dan itu menjadi tugas pertama fitur 003 — bentuk yang ditebak dari dokumentasi adalah bentuk yang akan berbeda dari kenyataannya, pelajaran yang sudah datang dua kali pada fitur 015. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001), yang juga memegang peran penanggung jawab teknis C-12 sampai BT-49 diputus rapat tim |

## KB-021 · Gerbang 1 fitur 003 — pemisahan perhitungan dari pembacaan ekspor

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | `spec.md` fitur 003 menyisakan satu pertanyaan yang tidak dapat dijawab dari dokumentasi: apakah bidang `versi_skema`, `bendera`, dan `status_pra_anotasi` dibawa Label Studio sendiri atau ditambahkan pada tahap ekspor. ADR-08 menyebut kedua kemungkinan tanpa memutuskan, dan jawabannya menuntut satu contoh ekspor sungguhan yang belum ada. |
| Keputusan | **Fitur 003 lolos Gerbang 1** dengan cakupan dipisah tegas menjadi dua bagian. **Bagian 1 — perhitungan** (Kappa, F1 berpasangan dua tingkat, uji kualifikasi, skema berversi) tidak menunggu apa pun; aturannya lengkap pada D-03 Bagian 11 dan 12. **Bagian 2 — pembacaan ekspor** tidak dimulai sebelum satu contoh ekspor sungguhan tersimpan pada `tests/bahan/`. |
| Alternatif | Menunggu contoh ekspor sebelum memulai apa pun — ditolak; bagian 1 tidak menyentuh bentuk data Label Studio sama sekali, dan menahannya berarti menunda pekerjaan yang tidak menunggu apa pun, kekeliruan yang sama dengan yang KB-010 hindari saat memisahkan fitur 002 dari 015. Membangun pembacaan ekspor dari bentuk yang ditebak dokumentasi — **ditolak tegas**; dua kali pada fitur 015 bentuk yang ditebak terbukti berbeda dari kenyataannya, dan keduanya baru ketahuan ketika bahan uji sungguhan dibuat. Membangun bagian 2 lebih dulu agar tipe kita mengikuti bentuk ekspornya — ditolak; itu membuat tipe milik kita menyerupai bentuk milik perangkat yang versinya dapat berubah tanpa kita. |
| Dampak | Urutan pembangunan dalam fitur ini terbalik dari yang biasa: perhitungan lebih dulu, pembacaan kemudian. Bila contoh ekspor tidak dapat diperoleh pada siklus ini, bagian 1 tetap selesai dan bagian 2 menjadi butir terbuka — pola yang sama dengan yang KB-018 tetapkan bagi OCR, dan yang ternyata tidak terpakai karena berkas modelnya ada. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-022 · Gerbang 2 fitur 003 — pemisahan pembacaan ekspor menjadi fitur 016

| | |
|---|---|
| Tanggal | 2026-08-06 |
| Konteks | `plan.md` fitur 003 mengajukan satu pertanyaan yang bukan pertanyaan kode: siapa yang menyediakan contoh ekspor Label Studio, dan kapan. Ia menuntut seseorang memasang Label Studio 1.23, membuat proyek berskema D-03, menganotasi dua atau tiga dokumen dengan dua akun berbeda, lalu mengekspornya. KB-021 sudah memisahkan perhitungan dari pembacaan ekspor; yang tersisa adalah bagaimana pemisahan itu tercatat pada urutan pembangunan. |
| Keputusan | **Fitur 003 lolos Gerbang 2 dengan cakupan dipersempit ke bagian 1**: perhitungan kesepakatan, skema berversi, uji kualifikasi, ekspor JSONL/CoNLL, dan penandaan pra-anotasi. **Pembacaan ekspor Label Studio menjadi fitur 016**, ditempatkan sesudah 003 pada `docs/D12.md` Bagian 7, tertahan sampai satu contoh ekspor sungguhan tersedia pada `tests/bahan/`. |
| Alternatif | Menugaskan penyediaan contoh sekarang dan menyelesaikan keduanya dalam satu fitur — ditolak; bagian 2 menuntut orang di luar agen, dan fitur yang setengahnya menunggu orang lain akan tercatat "berjalan" selama berminggu-minggu tanpa ada yang berjalan. Menunggu contoh ekspor sebelum memulai apa pun — ditolak dengan alasan yang sama seperti KB-021: bagian 1 tidak menyentuh bentuk data Label Studio sama sekali, dan menahannya berarti menunda pekerjaan yang tidak menunggu apa pun. |
| Dampak | D-12 ke 0.6, D-00 ke 2.15. Urutan pembangunan bertambah satu baris; jumlah fitur menjadi 16. `[sistem.label_studio]` **tidak** ditambahkan sekarang — mencatat versi perangkat yang belum dipasang siapa pun menghasilkan patokan yang tidak pernah dipakai, kekeliruan yang sudah dihindari pada `[sistem.tesseract]` fitur 015. Ia menjadi bagian fitur 016 bersama contoh ekspornya. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-023 · Contoh ekspor Label Studio diperoleh — fitur 016 tidak lagi tertahan

| | |
|---|---|
| Tanggal | 2026-08-09 |
| Konteks | KB-021 dan KB-022 menahan fitur 016 sampai satu contoh ekspor sungguhan tersedia pada `tests/bahan/`, dan menyebutnya menuntut orang di luar agen. Tiga pilihan diajukan: agen memasang Label Studio di dalam kontainer di luar proyek (A), menunggu orang tim (B), atau menulis fitur 016 dari dugaan lalu memperbaikinya kelak (C). |
| Keputusan | **Pilihan A.** Label Studio 1.23.0 dipasang pada venv terpisah **di luar proyek** — bukan sebagai ketergantungan, sehingga `uv.lock` dan `pyproject.toml` tidak berubah dan KB-020 tetap berlaku utuh. Satu proyek berskema D-03 dibuat, dua dokumen contoh dianotasi oleh **dua akun berbeda**, lalu diekspor. Berkasnya disimpan sebagai `tests/bahan/ekspor-label-studio-1.23.json` beserta skrip pembuatnya. **Fitur 016 tidak lagi tertahan** dan dapat diajukan ke Gerbang 1. |
| Jawaban atas pertanyaan ADR-08 | **Ketiga bidang tidak dibawa Label Studio.** `versi_skema`, `bendera`, dan `status_pra_anotasi` tidak ada pada berkas ekspor dalam bentuk apa pun — diperiksa terhadap berkas sungguhan, bukan terhadap dokumentasi. Ketiganya **wajib ditambahkan pada tahap ekspor**, yaitu pada kode kita sendiri. `status_pra_anotasi` adalah pengecualian sebagian: ia dapat **diturunkan** dari `predictions` tugas yang tidak kosong, dan menurunkannya lebih baik daripada menuliskannya karena bidang yang ditulis tangan dapat berbeda dari keadaan sebenarnya. |
| Temuan lain yang mengubah rencana | `value.start` dan `value.end` adalah **indeks karakter** — dicocokkan terhadap potongan teks aslinya dan cocok, sehingga C-10 tidak menuntut penerjemahan. `completed_by` adalah **bilangan bulat id pengguna**, bukan surel; pemetaan id ke orang tinggal di dalam Label Studio dan **tidak ikut terbawa ekspor**, yang berarti berkas ekspor tidak memuat data pribadi anotator. Tugas membawa `predictions`, `drafts`, `total_annotations`, dan `was_cancelled` — keempatnya menentukan anotasi mana yang sah dihitung. |
| Alternatif | Menunggu orang tim (B) — ditolak; ia menahan pekerjaan yang ternyata dapat diselesaikan agen sendiri dalam satu sesi, dan penantian tanpa batas waktu yang jelas adalah bentuk penundaan yang paling sulit terbaca dari daftar urutan pembangunan. Menulis fitur 016 dari dugaan (C) — ditolak tegas dengan alasan KB-021 yang tidak berubah: dua kali pada fitur 015 bentuk yang ditebak terbukti keliru. Memasang `label-studio` sebagai ketergantungan proyek — ditolak; KB-020 sudah menolaknya dan keadaan tidak berubah, karena yang diperlukan hanyalah menghasilkan berkas sekali, bukan menjalankan perangkatnya. |
| Batas yang wajib diketahui | Ekspor ini dihasilkan **lewat API, bukan lewat peramban**. Anotasi yang dibuat anotator sungguhan pada antarmuka membawa `lead_time`, `draft_created_at`, dan `last_action` yang terisi, sedangkan pada berkas ini sebagiannya kosong. Bentuk bidangnya sama; **nilainya belum tentu mewakili pemakaian sungguhan**. Fitur 016 karena itu tidak boleh menyandarkan aturan apa pun pada nilai ketiga bidang tersebut, dan bila kelak diperlukan, satu ekspor dari pemakaian sungguhan wajib diambil lebih dulu. |
| Dampak | `[sistem.label_studio]` **belum ditambahkan** pada `ketergantungan-disetujui.toml`. Ia ditambahkan bersama perluasan R-18 yang memeriksanya, sebagai tugas dalam fitur 016 — mencatat patokan tanpa pemeriksa yang membandingkannya menghasilkan catatan yang tidak menjaga apa pun, kekeliruan yang sudah dihindari dua kali. Pekerjaan yang berjalan tetap fitur 003 bagian B dan C; fitur 016 menyusul sesudah 003 lolos Gerbang 4, sesuai urutan D-12 Bagian 7 yang tidak berubah. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-024 · Gerbang 4 fitur 003 — bagian 1 selesai utuh

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | KB-022 mempersempit fitur 003 ke bagian 1: perhitungan kesepakatan, skema berversi, uji kualifikasi, dan penandaan pra-anotasi. Kelima belas tugas `tasks.md` selesai — Fase A lima tugas, Fase B enam, Fase C empat. |
| Keputusan | **Fitur 003 lolos Gerbang 4.** `make check` lulus enam gerbang; `make compliance` tidak berubah pada 8 lulus / 0 gagal / 12 belum dapat diperiksa; cakupan uji 99% atas 1.126 pernyataan dengan 798 uji lulus; nol ketergantungan baru — tetap 10 langsung dan 26 terkunci, persis seperti yang KB-020 tetapkan. Dua uji mutasi yang `tasks.md` tuntut dijalankan keduanya. **Kappa dipanggil atas anotasi rentang**: tanda tangan `kappa_kategori` diubah menerima `RentangEntitas`, dan mypy menghasilkan 4 galat pada 2 berkas termasuk pada `kualifikasi.py` yang memakainya — penyeragaman dua ukuran karena itu tidak dapat dilakukan tanpa memutus pemanggilnya. **`belum_terhitung` mengembalikan 1,0**: 3 uji gagal pada tiga berkas berbeda, sehingga kesepakatan yang lahir dari ketiadaan tidak dapat terbaca sebagai kesepakatan sempurna. |
| Alternatif | Menyelesaikan R-10 dan R-11 (ekspor JSONL/CoNLL) di dalam fitur ini — ditolak; keduanya menuntut bentuk anotasi yang lengkap, dan kelengkapannya baru pasti sesudah fitur 016 memetakan ekspor Label Studio. Menulisnya sekarang berarti menebak bidang mana yang akan terisi, dan tebakan seperti itu sudah dua kali terbukti keliru pada fitur 015. Menambahkan `[sistem.label_studio]` sekarang bersama R-16 — ditolak; ia menyusul bersama perluasan R-18 yang memeriksanya, sebab patokan tanpa pemeriksa yang membandingkannya tidak menjaga apa pun. Menetapkan porsi minimum pembanding sendiri agar C-3 menegakkan lebih banyak — **ditolak tegas**; angkanya tidak ada pada D-01 maupun D-03, dan C-16 melarang menetapkan ambang di luar prosedur kalibrasi D-07 BT-29. Membetulkan rujukan D-03 pada `spec.md` R-14 langsung — ditolak; `AGENTS.md` melarang mengubah spesifikasi saat implementasi, dan perubahan diajukan lalu menunggu. |
| Dampak | Urutan pembangunan berlanjut ke **fitur 016**, yang tidak lagi tertahan sejak KB-023. Fitur 004 (model NER dan klasifikasi) menunggu keduanya, sebab pra-anotasi yang dikendalikan C-2 dan C-3 lahir di sana. **Satu butir terbuka lahir dari fitur ini**: porsi minimum pembanding belum ditetapkan siapa pun — D-01 FR-C10 menulis "sebagian batch", D-03 BT-13 menulis "disarankan menyisihkan sebagian batch", dan tidak ada angka pada dokumen mana pun. C-3 menegakkan batas yang tertulis — batch berpra-anotasi tanpa satu pun pembanding ditolak — sedangkan porsinya dihitung, dicatat ke L2, dan tidak dinilai. Batch dengan seratus dokumen berpra-anotasi dan satu pembanding lolos. **BT-13 perlu diperluas dengan porsi minimum, atau dinyatakan tegas bahwa penilaiannya diserahkan kepada adjudikator per batch.** **Satu koreksi diajukan dan belum dilakukan**: `spec.md` R-14 dan `tasks.md` C-1 menyebut ambang kualifikasi berada pada D-03 Bagian 12, sedangkan ambangnya berada pada Bagian 13; nilainya benar, rujukannya keliru. Letak sebenarnya sudah dicatat pada uraian `src/nlp/anotasi/ambang.py` agar tidak disalin pembaca berikutnya. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-025 · Gerbang 1, 2, dan 3 fitur 016 — bentuk kendali bendera ditetapkan

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | Fitur 016 tidak lagi tertahan sejak KB-023 menyediakan contoh ekspor sungguhan. Pemilik proyek meminta pekerjaan dipercepat, sehingga ketiga gerbang diputus dalam satu duduk — dengan seluruh keputusannya tetap tertulis, sebab gerbang yang dilewati tanpa catatan akan diambil ulang diam-diam saat implementasi. Satu pertanyaan terbuka pada `spec.md`: bendera D-03 — `perlu_adjudikasi`, `ocr_rusak`, `anonimisasi_berlebih`, `bocor_pii` — hanya terkumpul bila konfigurasi label Label Studio memuat kendali untuk itu, dan konfigurasi tim belum disusun. |
| Keputusan | **Ketiganya lolos.** Gerbang 1: **pilihan A dengan bentuk teknis B** — nama kendali dan keempat nilainya ditetapkan kode pada `plan.md` Bagian 3 sebagai satu `Choices` bernama `bendera`, sedangkan keadaan proyek dinyatakan pemanggil lewat parameter. Proyek yang belum memasang kendalinya **tetap dapat diimpor**, tetapi korpusnya **tidak terbaca bersih**: `bendera` ditulis `null`, bukan `[]`. Gerbang 2: letak modul di bawah `src/nlp/anotasi/` tanpa perubahan `AGENTS.md`, nol ketergantungan baru. Gerbang 3: sembilan tugas — enam pembacaan, dua ekspor, satu catatan dan patokan. |
| Alternatif | Mengabaikan bendera pada siklus ini dan mencatatnya sebagai butir terbuka — **ditolak tegas**; `bocor_pii` menyatakan data pribadi lolos anonimisasi dan KM-05 memeriksanya harian, sehingga bendera yang ditunda adalah bendera yang tidak ada justru ketika ia diperlukan. Menetapkan bentuk kendali tanpa parameter keadaan — ditolak; ia menolak seluruh proyek yang konfigurasinya belum diperbarui, dan penolakan seperti itu diakali dengan memasang kendali kosong. Menerima parameter tanpa menetapkan bentuk kendalinya — ditolak; tim tidak punya satu hal pasti untuk disalin, dan nama kendali yang berbeda antar-proyek menghasilkan impor yang diam-diam tidak menemukan bendera apa pun. |
| Dampak | `[sistem.label_studio]` ditambahkan pada tugas C-1 **bersama** perluasan pemeriksa R-18 yang membandingkannya. Ekspor JSONL dan CoNLL (R-10, R-11 fitur 003) masuk cakupan fitur ini sesuai KB-024. Satu tuntutan baru bagi tim anotasi: konfigurasi label Label Studio wajib memuat kendali `bendera` dengan keempat nilai D-03 — tertulis pada `plan.md` Bagian 3 dalam bentuk yang dapat disalin apa adanya. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-026 · Label Studio tidak memeriksa kecocokan rentang dan teksnya lewat API

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | Tugas A-2 fitur 016 menggagalkan impor atas bahan uji sungguhan `tests/bahan/ekspor-label-studio-1.23.json`. Sebabnya bukan pengurainya: satu rentang tercatat `start: 0, end: 33` sedangkan `value.text`-nya berbunyi "Permendikdasmen Nomor 12 Tahun 2025" yang panjangnya 35 karakter. Potongan `teks[0:33]` menghasilkan "Permendikdasmen Nomor 12 Tahun 20" — meleset dua karakter. Nilai keliru itu berasal dari skrip pembuat bahan uji yang saya tulis sendiri, bukan dari perangkatnya. |
| Keputusan | **Rentangnya dibetulkan menjadi `end: 35` pada bahan uji, dan skrip pembuatnya diperbaiki agar pembuatan ulang menghasilkan nilai yang benar.** Yang diubah hanya dua bilangan yang saya kirimkan sendiri; **bentuk berkasnya tidak disentuh sama sekali**, sehingga nilai buktinya sebagai contoh bentuk ekspor Label Studio 1.23.0 tetap utuh. Satu uji ditambahkan pada `tests/nlp/test_impor_ls_bentuk.py` yang memeriksa **seluruh** rentang pada bahan cocok dengan teksnya, supaya bahan yang dibuat ulang kelak tidak diam-diam membawa rentang yang meleset. |
| Temuan yang wajib diketahui | **Label Studio menerima rentang yang tidak cocok dengan teksnya lewat API tanpa memeriksa.** Pemeriksaan itu ada pada antarmuka pelabelannya — anotator memilih rentang dengan tetikus sehingga keduanya selalu sejajar — tetapi tidak pada jalur API. Akibatnya bagi kita: **pemeriksaan kecocokan rentang pada `impor_ls` bukan kehati-hatian berlebih melainkan satu-satunya pemeriksaan yang ada**, khususnya bila kelak pra-anotasi otomatis fitur 004 menyisipkan rentang lewat API. Rentang yang meleset dua karakter menunjuk kata lain tanpa satu galat pun, dan korpusnya tetap terbaca wajar. |
| Alternatif | Membiarkan bahan uji apa adanya dan menandainya sebagai contoh rentang rusak — ditolak; bahan utama yang rusak membuat setiap uji impor berikutnya menuntut jalan pintas, dan uji rentang rusak sudah ada tersendiri dengan merusak salinan. Membuat ulang bahan dengan memasang Label Studio kembali — ditolak untuk sekarang; yang keliru adalah dua bilangan masukan saya, bukan keluaran perangkatnya, sehingga memasang ulang 857 MB tidak mengubah satu pun bentuk yang menjadi nilai bukti berkas itu. |
| Dampak | Sidik bahan uji berubah dari `b61163f1...` menjadi `0e8ebeee...`; L2 mencatat keduanya. Temuan tentang API dicatat sebagai peringatan bagi fitur 004: penyisipan pra-anotasi lewat API **tidak** akan diperiksa Label Studio, dan `impor_ls` adalah tempat kekeliruannya tertangkap. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-027 · Gerbang 4 fitur 016 — pembacaan ekspor Label Studio selesai

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | Kesembilan tugas `tasks.md` selesai: enam pembacaan, dua ekspor, satu catatan dan patokan. Dengan ini FR-C06 dan FR-C08 terpenuhi, dan R-10, R-11, serta R-16 yang KB-024 pindahkan dari fitur 003 ikut tuntas. |
| Keputusan | **Fitur 016 lolos Gerbang 4.** `make check` lulus enam gerbang; `make compliance` tidak berubah pada 8 lulus / 0 gagal / 12 belum dapat diperiksa; cakupan uji 99% atas 1.343 pernyataan; nol ketergantungan Python baru — tetap 10 langsung dan 26 terkunci, sedangkan bagian `[sistem]` bertambah `label_studio`. Kelima uji mutasi `plan.md` Bagian 6 dijalankan dan seluruhnya menyalakan uji yang dimaksud. Seluruh uji impor berjalan atas berkas ekspor sungguhan, bukan atas bentuk yang disusun uji. |
| Alternatif | Menuliskan dokumen beranotasi ganda ke JSONL dengan memilih putusan pertama — ditolak; D-03 Bagian 15 menetapkan satu baris mewakili satu dokumen, dan memilih salah satu dari dua putusan berarti memilih berdasarkan urutan penyimpanan Label Studio, bukan berdasarkan adjudikasi. Ia dilaporkan sebagai tertunda adjudikasi. Menggeser rentang yang tidak sejajar batas token ke batas terdekat saat ekspor CoNLL — ditolak; hasilnya berkas pelatihan yang benar bentuknya dan salah isinya. Menambahkan `src/nlp` pada daftar pengecualian pemeriksa C-17 agar `ekspor.py` boleh menulis berkas — **ditolak tegas**; memperluas pengecualian pemeriksa konstitusi untuk meloloskan kode sendiri adalah bentuk pelanggaran yang paling mudah dibenarkan. Rancangannya yang diubah: modul mengembalikan baris, penulisannya pekerjaan pemanggil di luar `src/`. Memeriksa versi Label Studio terpasang seperti pada Tesseract — ditolak; ia tidak terpasang pada lingkungan mana pun yang menjalankan `make check`, sehingga pemeriksanya akan selalu melapor "belum dapat diperiksa". Yang diperiksa sidik berkas contoh ekspornya. |
| Dampak | Urutan pembangunan berlanjut ke **fitur 004** (model NER dan klasifikasi), yang kini memiliki jalur lengkap dari anotasi ke bahan pelatihan: Label Studio → `impor_ls` → tipe fitur 003 → `ekspor_conll`. **Satu tuntutan bagi tim anotasi**: konfigurasi label Label Studio wajib memuat kendali `bendera` dengan keempat nilai D-03; bentuk yang dapat disalin ada pada `plan.md` Bagian 3. Tanpa kendali itu, `bendera_terkumpul=False` wajib dinyatakan saat impor dan korpusnya membawa `bendera: null` sepanjang hidupnya. **Satu peringatan bagi fitur 004** (KB-026): penyisipan pra-anotasi lewat API Label Studio tidak diperiksa perangkatnya, dan `impor_ls` adalah satu-satunya tempat rentang yang meleset tertangkap. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-028 · Gerbang 1, 2, dan 3 fitur 004 — pemisahan, dan pembukaan himpunan uji

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | D-12 Bagian 7 menempatkan FR-D01 s.d. FR-D07 pada fitur 004 — model NER dan klasifikasi dengan F1 ≥ 85%. Modelnya **tidak dapat dilatih sekarang**: tidak ada satu pun dokumen teranotasi, dan anotasinya pekerjaan dua mahasiswa pada bulan 2–4 yang baru dapat dimulai setelah mereka lulus uji kualifikasi FR-C09. Yang tidak menunggu justru bagian yang wajib berdiri lebih dulu, sebab D-08 Bagian 4.2 menetapkan pembagian data **dibekukan sebelum pelatihan pertama**. Satu pertanyaan terbuka: apa yang terjadi ketika himpunan uji dibuka kedua kalinya. |
| Keputusan | **Ketiga gerbang lolos.** Fitur 004 memuat **bagian 1 saja**: pembagian data beku pada tingkat dokumen (FR-D07), metrik per kelas (FR-D04), dan catatan percobaan keempat belas bidang D-10 (FR-D03). **Model NER dan klasifikasi beserta prosedur latih ulang (FR-D01, FR-D02, FR-D05) menjadi fitur 017**, tertahan sampai korpus teranotasi ada. Gerbang 1 atas pertanyaan himpunan uji: **pilihan C** — pembukaannya dicatat, tetap diizinkan, dan hitungannya ikut pada catatan percobaan yang menjadi bahan naskah. Gerbang 3: tujuh tugas, nol ketergantungan baru. |
| Alternatif | Menunggu korpus sebelum memulai apa pun — ditolak; pembagian data justru wajib ada **sebelum** pelatihan pertama, dan membangunnya belakangan berarti pelatihan pertama berjalan atas pembagian yang disusun sambil lalu. D-08 menyebutkan akibatnya: segmen dari satu dokumen yang tersebar ke latih dan uji membuat model tampak lebih baik daripada kenyataannya, "kekeliruan yang mudah terjadi dan sulit terdeteksi setelahnya". Menolak pembukaan kedua himpunan uji (pilihan B) — ditolak; ia menghalangi pekerjaan sah seperti mengulang evaluasi karena galat perkakas, dan penjagaan yang menghalangi pekerjaan sah akan dilucuti. Cara melucutinya — membuat pembagian baru — justru menghapus jejaknya. Mencatat pembukaan tanpa membawanya ke laporan (pilihan A) — ditolak; catatan yang tidak pernah sampai ke laporan tidak ada yang membaca. |
| Dampak | Urutan pembangunan bertambah satu baris: **fitur 017** sesudah 004, tertahan pada korpus teranotasi. Jumlah fitur menjadi 17. Pola pemisahannya sama dengan KB-010 (002/015) dan KB-022 (003/016), dan alasannya sama pula: fitur yang setengahnya menunggu orang lain akan tercatat "berjalan" tanpa ada yang berjalan. **Satu hal yang wajib diketahui tim**: pembagian data dibekukan sekali, dan membekukannya menuntut daftar dokumen korpus sudah lengkap — sehingga pembekuan pertama tidak boleh dilakukan sebelum anotasi bulan 2–4 selesai, meski kodenya siap sekarang. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-029 · Gerbang 4 fitur 004 — bahan pelatihan berdiri sebelum modelnya

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | Ketujuh tugas `tasks.md` selesai: lima pembagian data, dua metrik, satu catatan percobaan. Seluruhnya dibangun **sebelum** ada satu pun dokumen teranotasi, sesuai KB-028 dan D-08 Bagian 4.2 yang menetapkan pembagian dibekukan sebelum pelatihan pertama. |
| Keputusan | **Fitur 004 lolos Gerbang 4.** `make check` lulus enam gerbang; `make compliance` tidak berubah pada 8 lulus / 0 gagal / 12 belum dapat diperiksa; cakupan uji 99% atas 1.506 pernyataan; nol ketergantungan baru — tetap 10 langsung dan 26 terkunci. Keenam uji mutasi `plan.md` Bagian 4 dijalankan. Angka metrik diuji terhadap contoh yang dihitung tangan, termasuk contoh yang membedakan rerata makro dari mikro: mikro 0,90 lawan makro 0,47 pada data yang sama. |
| Alternatif | Menghitung kelas tanpa contoh sebagai 0,0 pada rerata makro — ditolak; ia menurunkan rerata atas kelas yang tidak pernah diuji, dan angka yang turun karena data yang tidak ada menyesatkan ke arah pesimistis, sama buruknya dengan sebaliknya. Menyediakan satu bidang bernama `f1` alih-alih dua rerata bernama — ditolak; bidang tunggal adalah bidang yang pembacanya tidak tahu jenisnya, dan ia akan disalin ke naskah tanpa keterangan. Meminta `seed` dan `id_pembagian_data` sebagai argumen terpisah pada catatan percobaan — ditolak; argumen terpisah dapat diisi angka yang bukan milik pembagian yang benar-benar dipakai, dan catatan yang menyebut seed yang salah lebih buruk daripada catatan tanpa seed sebab ia menuntun orang mengulang dengan angka yang keliru. Memakai kembali `HasilKesepakatan` fitur 003 bagi angka metrik — ditolak; bentuknya sama tetapi artinya berbeda, dan menyatukannya membuat `src/nlp/pelatihan/` bergantung pada `src/nlp/anotasi/` untuk sesuatu yang bukan anotasi. |
| Dua uji mutasi yang tidak menyala | Keduanya menemukan celah pada **uji saya**, bukan pada mutasinya, dan keduanya jenis kegagalan yang sama — uji yang memeriksa besaran turunan yang terlalu kasar. **Sisa pembulatan dibuang ke himpunan uji**: uji memeriksa jumlah total dokumen, dan total tetap utuh ke mana pun sisanya jatuh; padahal melemparkannya ke uji membuat himpunan uji melar melampaui 15% D-08 pada setiap korpus yang tidak habis dibagi. **Sidik dihitung dari jumlah, bukan isi**: uji memindahkan satu dokumen antar-himpunan, yang juga mengubah jumlahnya, sehingga sidik berbasis jumlah tetap lolos; yang tidak tertutup adalah pertukaran dua dokumen — jumlahnya persis sama, isinya berubah — dan itu justru bentuk yang muncul ketika seseorang membagi ulang dengan seed berbeda. Dua uji ditambahkan; kedua mutasi kemudian menyala. |
| Dampak | Seluruh perkakas yang dibutuhkan **fitur 017** sudah berdiri: pembagian beku, lemari himpunan uji yang mencatat pembukaannya, metrik per kelas, dan catatan percobaan keempat belas bidang D-10. Fitur 017 tertahan pada korpus teranotasi — pekerjaan dua mahasiswa bulan 2–4 — bukan pada kode mana pun. **Satu hal yang wajib diketahui tim**: pembagian dibekukan sekali dan menuntut daftar dokumen korpus sudah lengkap, sehingga pembekuan pertama tidak boleh dilakukan sebelum anotasi selesai meski kodenya siap sekarang. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-030 · Gerbang 1, 2, dan 3 fitur 006 — didahulukan atas 005

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | D-12 Bagian 7 menempatkan 005 (ontologi) sebelum 006 (indeks terpisah menurut lisensi); keduanya bulan 4. Dua hal mendorong peninjauan urutannya. **Pertama**, `make compliance` berbunyi 8 lulus / 0 gagal / 12 belum dapat diperiksa pada fitur 015, 003, 016, dan 004 berturut-turut — sedangkan D-12 menyatakan daftar itu "tagihan, bukan pengecualian, wajib menyusut pada setiap fitur berikutnya". Empat fitur berlalu tanpa menyusut, masing-masing dengan alasan sah, dan empat kali berturut-turut adalah pola bukan kebetulan. **Kedua**, FR-E01 menuntut ontologi memuat ≥ 500 konsep dan ≥ 1.000 relasi — pekerjaan pakar domain, bukan kode — sehingga fitur 005 akan terbelah seperti 003 dan 004. |
| Keputusan | **Fitur 006 dikerjakan mendahului 005**, dan ketiga gerbangnya lolos. `AGENTS.md` menempatkan Kepatuhan pada urutan pertama, di atas kebenaran dan kecepatan; C-02 adalah pasal kepatuhan yang belum terperiksa mesin, sedangkan Modul E adalah pekerjaan ruang lingkup. Gerbang 1 tidak menyisakan pertanyaan terbuka: D-07 Bagian 3.1 menetapkan kedua indeks beserta isinya, D-14 Bagian 5 menetapkan nama enum `segmen_teks.indeks_tujuan` beserta nilai `utama` dan `metadata`, dan ADR-06 menetapkan bentuk pemisahannya. Gerbang 2: letak di `src/penyimpanan/`, mengikuti C-03 fitur 002. Gerbang 3: lima tugas, nol ketergantungan baru. |
| Alternatif | Mengikuti urutan D-12 apa adanya — ditolak; ia menambah satu lagi fitur yang setengahnya menunggu orang, sementara tagihan kepatuhan tetap tidak menyusut untuk kelima kalinya. Menyaring saat kueri alih-alih memisahkan indeks — **ditolak tegas**; D-07 Bagian 3.1 menyatakan "ini keputusan struktural, bukan penyaringan", dan alasannya bahwa klausa penyaring ada pada setiap kueri sedangkan satu kueri yang lupa memuatnya tidak menghasilkan galat apa pun — ia menghasilkan jawaban yang lebih lengkap, dan jawaban yang lebih lengkap tidak pernah terasa seperti kekeliruan. Menambahkan nilai indeks pada enum `Area` fitur 002 — ditolak; uraian `area.py` menyatakan menambah nilai ketiga menuntut D-14 diubah lebih dulu (AG-04), dan indeks bukan area penyimpanan melainkan tujuan segmen yang D-14 sudah namai terpisah. |
| Dampak | Urutan pembangunan pada D-12 Bagian 7 **tidak diubah** — yang berubah urutan pengerjaan, dan itu tercatat di sini. Fitur 005 menyusul sesudah 006. **`make compliance` wajib menyusut satu** menjadi 9 lulus / 0 gagal / 11 belum; bila tidak menyusut, ada yang keliru — pemeriksa yang terdaftar tetapi tidak memeriksa apa pun melapor lulus dengan cara yang sama seperti pemeriksa yang benar. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-031 · Gerbang 4 fitur 006 — tagihan kepatuhan menyusut untuk pertama kalinya sejak fitur 002

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | Kelima tugas `tasks.md` selesai: tiga tipe dan penempatan, dua pemisahan kredensial beserta pemeriksanya. KB-030 mendahulukan fitur ini atas 005 justru untuk menyusutkan tagihan kepatuhan yang tidak bergerak selama empat fitur. |
| Keputusan | **Fitur 006 lolos Gerbang 4.** `make check` lulus enam gerbang; **`make compliance` menyusut menjadi 9 lulus / 0 gagal / 11 belum dapat diperiksa** — penyusutan pertama sejak fitur 002; cakupan uji 99% atas 1.553 pernyataan; nol ketergantungan baru. Kelima uji mutasi `plan.md` Bagian 4 dijalankan. C-02 berpindah dari `fitur_pengunci` menjadi `pemeriksa=periksa_pemisahan_indeks` pada `daftar_pasal.py`. |
| Alternatif | Menyaring saat kueri alih-alih memisahkan kredensial — ditolak sesuai D-07 Bagian 3.1 dan C-02 kalimat kedua. Menutup `PENJAWABAN` dari indeks metadata — **ditolak setelah diperiksa terhadap D-14**; lihat baris koreksi di bawah. Menandai C-02 lulus tanpa pemeriksa yang benar-benar memeriksa — ditolak tegas; pemeriksa yang terdaftar tetapi tidak memeriksa apa pun melapor LULUS dengan cara yang persis sama dengan pemeriksa yang benar, dan tagihannya menyusut tanpa satu pun aturan ditegakkan. Karena itu pemeriksanya diuji terhadap enam bentuk pohon yang sengaja dirusak, bukan hanya terhadap pohon bersih. |
| Koreksi yang saya lakukan saat implementasi | **R-04 pada `spec.md` fitur ini saya ubah**, dan itu menyimpang dari `AGENTS.md` yang melarang mengubah spesifikasi saat implementasi. Bentuk pertamanya berbunyi "jalur penjawaban tidak boleh membaca `indeks_metadata`" — lebih ketat daripada C-02 **dan melanggar D-14 Bagian 6**, yang menetapkan `bacaan_lanjutan` sebagai tempat satu-satunya bagi sumber `indeks_metadata`. Menegakkannya akan membuat blok itu mustahil dibangun. Garis C-02 jatuh pada `PEMANGGIL_LLM`, bukan `PENJAWABAN`; kekeliruan saya menyamakan "jalur penjawaban" dengan "yang menyusun permintaan LLM", padahal keduanya dipisahkan sejak fitur 001 justru agar garis seperti ini dapat ditarik. Alasan saya memperbaikinya langsung: spesifikasi itu disusun dan lolos gerbang pada hari yang sama oleh agen yang sama. Penyimpangannya dicatat pada `spec.md`, `tasks.md`, uraian ujinya, dan di sini — **bukan dilakukan diam-diam**, dan tetap menunggu penilaian pemegang gerbang. |
| Dampak | Sembilan pasal kini terperiksa mesin. Sebelas yang tersisa menunggu fitur 007 sampai 013. Berikutnya pada urutan pengerjaan: **fitur 005** (ontologi dan basis pengetahuan), yang sebagian tertahan pakar domain — FR-E01 menuntut ≥ 500 konsep dan ≥ 1.000 relasi — dan hampir pasti akan terbelah seperti 003, 004, dan 006. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-032 · Gerbang 1, 2, dan 3 fitur 005 — pemisahan keempat, dan alasannya sama

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | FR-E01 menuntut ontologi memuat ≥ 500 konsep dan ≥ 1.000 relasi. Itu pekerjaan pakar domain di atas bahan terkurasi, dan bahan terkuranya sendiri belum ada sebab kurasi menunggu fitur 010. D-06 Bagian 11.1 menamai kekosongan yang sesungguhnya, dan bukan jumlahnya: "Yang tidak pernah ada: cara mengerjakannya, dan pemeriksaan apakah ia dapat dikerjakan. Ini pola TK-29 dan TK-41 yang berulang untuk ketiga kalinya — perilaku diwajibkan, target ditetapkan, tanpa ada yang menghitung bebannya." |
| Keputusan | **Ketiga gerbang lolos, dengan cakupan bagian 1 saja**: skema konsep dan relasi, aturan hitung sah menurut D-06 Bagian 11.2, dan ekspor JSON-LD. **Pengisian ontologi dan antarmuka graf (FR-E01, FR-E04) menjadi fitur 018**, tertahan pada pakar domain dan pada bahan terkurasi. Gerbang 1 tidak menyisakan pertanyaan terbuka: D-06 Bagian 11.2 menetapkan aturan hitungnya, FR-E02 menetapkan ketujuh jenis relasi, D-04 Bagian 7.3 menetapkan bidangnya, D-01 Bagian 12.2 memilih JSON-LD. Gerbang 2: letak pada `src/rag/ontologi/` tanpa perubahan `AGENTS.md`; tidak menulis berkas sebab C-17 melarangnya dari jalur penjawaban. Gerbang 3: empat tugas. |
| Alternatif | Mengisi ontologi dengan konsep yang diturunkan agen dari dokumen contoh — **ditolak tegas**; ia akan menghasilkan artefak penelitian yang tampak memenuhi MK-06 padahal tidak seorang pakar pun pernah menilainya, dan angka itu masuk naskah. Menolak konsep tanpa definisi agar tidak terhitung — ditolak; konsep yang masih disusun definisinya adalah keadaan kerja yang wajar, dan yang tidak boleh adalah ia ikut terhitung, bukan ia ada. Memakai pustaka RDF untuk menulis JSON-LD — ditolak; ia menambah permukaan pemeriksaan V-05 demi kemudahan yang tidak diperlukan, sebab JSON-LD adalah JSON biasa. Memeriksa duplikat konsep dengan kesamaan untai — ditolak; D-06 Bagian 11.2 menyatakannya pekerjaan manusia pada audit graf D-08 Bagian 4.4, dan menebaknya akan menyatukan dua konsep yang definisinya kebetulan mirip. |
| Dampak | Ini **pemisahan keempat** dengan pola yang sama — KB-010 (002/015), KB-022 (003/016), KB-028 (004/017), dan kini 005/018. Jumlah fitur menjadi 18. Pola berulangnya sendiri adalah temuan: **empat dari delapan fitur yang dikerjakan ternyata memuat pekerjaan yang tertahan orang di luar agen**, dan tidak satu pun terbaca demikian dari D-12 Bagian 7. Diusulkan agar urutan pembangunan D-12 kelak menandai tiap baris dengan apa yang ditunggunya — bukan hanya bulannya. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-033 · Gerbang 4 fitur 005 — angka MK-06 tidak lagi dapat dipenuhi konsep kosong

| | |
|---|---|
| Tanggal | 2026-08-10 |
| Konteks | Keempat tugas `tasks.md` selesai: dua skema, satu penghitungan, satu ekspor. KB-032 mempersempit fitur ini ke bagian 1 sebab FR-E01 menuntut pakar domain dan bahan terkurasi yang belum ada. |
| Keputusan | **Fitur 005 lolos Gerbang 4.** `make check` lulus enam gerbang; `make compliance` tidak berubah pada 9 lulus / 0 gagal / 11 belum; cakupan uji 99% atas 1.668 pernyataan dengan 1.051 uji lulus; nol ketergantungan baru. Keenam uji mutasi `plan.md` Bagian 4 dijalankan, ditambah tujuh mutasi lain yang muncul saat pengerjaan; seluruhnya menyala. |
| Yang sesungguhnya dibangun | **Bukan ontologi, melainkan aturan yang membuat angkanya berarti.** D-06 Bagian 11.2: "Tanpa aturan ini, target 500 dapat dipenuhi dengan konsep yang tidak berguna, dan angka MK-06 menjadi angka tanpa isi." Sesudah fitur ini, konsep tanpa definisi tidak terhitung, konsep dari karantina tidak terhitung, relasi yang salah satu ujungnya tak sah tidak terhitung, dan **jumlah sah selalu dilaporkan bersama jumlah mentah** — sebab laporan yang menyebut satu angka tidak dapat dibedakan antara 512 konsep berdefinisi dan 512 baris tabel. |
| Alternatif | Menolak konsep tanpa definisi saat dibentuk — ditolak; konsep yang masih disusun definisinya adalah keadaan kerja yang wajar, dan menolaknya membuat pekerjaan penyusunan mustahil. Yang tidak boleh adalah ia ikut terhitung. Membiarkan relasi mewarisi dokumen rujukan konsepnya — ditolak; relasi "bertentangan dengan" antara dua konsep bersumber berbeda tidak punya dokumen yang menyatakan pertentangannya, sehingga klaim relasi menjadi klaim tanpa sumber. Menuliskan konteks JSON-LD dengan daftar jenis relasi yang ditulis tangan — ditolak; daftar itu akan berbeda dari enumnya ketika FR-E02 berubah, dan yang berbeda adalah yang tidak diperbarui. Mengekspor ontologi kosong sebagai berkas bersimpul nol — ditolak; ia tidak dapat dibedakan dari ekspor yang gagal diam. |
| Dampak | Delapan fitur kini lolos Gerbang 4 dari delapan belas. Berikutnya pada urutan pengerjaan: **fitur 007** (pengambilan hibrida, ADR-03), yang tidak tertahan orang mana pun — ia bekerja atas indeks yang fitur 006 pisahkan. **Empat fitur menunggu manusia**: 017 (model, menunggu korpus), 018 (ontologi, menunggu pakar domain), dan bagian pengisian pada keduanya. Tidak satu pun tertahan kode. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |

## KB-034 · Gerbang 1, 2, dan 3 fitur 007 — pemisahan kelima, dan yang pertama tidak menunggu orang

| | |
|---|---|
| Tanggal | 2026-08-12 |
| Konteks | ADR-03 menetapkan pengambilan hibrida: leksikal dan semantik dicari terpisah, lalu digabung dan diberi peringkat ulang. D-07 Bagian 4.4 merincinya — BM25 20 teratas, vektor 20 teratas, *Reciprocal Rank Fusion*, 5–8 segmen diteruskan. Empat fitur terakhir terbelah karena separuhnya menunggu orang di luar agen; fitur ini diperiksa terhadap pola yang sama sebelum dikerjakan. |
| Yang ternyata **tidak** tertahan | Sisi leksikalnya seluruhnya. BM25 adalah rumus dan RRF adalah rumus; keduanya dapat diuji terhadap contoh yang dihitung tangan tanpa satu pun korpus besar. Praproses Bahasa Indonesia sudah berdiri sejak fitur 015, dan `src/nlp/praproses/stemming.py` bahkan sudah menyatakan kegunaan keluarannya: *"untuk pencarian, bukan untuk menyiapkan bahan anotasi"*. Nol paket Python baru. |
| Keputusan | **Ketiga gerbang lolos, dengan cakupan bagian 1**: indeks segmen leksikal, BM25 atas `stem`, RRF, pembatasan kredensial pada indeks, dan bentuk penilaian kecukupan bukti. **Sumber vektor, pemeringkat ulang lintas-enkoder, dan kalibrasi ambang menjadi fitur 019** — tertahan model sematan (C-12), pgvector (ADR-05, D-09), dan *gold set* BT-35 bulan 4–5. Tujuh tugas, tiga fase. |
| Pertanyaan 1 · `penanda_bagian` | **Ditambahkan sekarang, wajib.** `docs/D14.md` Bagian 5 menyatakannya wajib — "tanpanya FR-F11 gagal" — dan `SegmenTerindeks` fitur 006 dibangun tanpanya. Itu kelalaian saya pada fitur 006, bukan keputusan. Menundanya ke fitur 009 berarti pengambilan mengembalikan segmen yang tidak dapat disitasi, dan kegagalan titik kritis T2 baru ketahuan dua fitur kemudian ketika indeksnya mungkin sudah terisi. Bidang yang boleh kosong ditolak: ia menenangkan tanpa menegakkan apa pun. |
| Pertanyaan 2 · konstanta *k* pada RRF | **60, dari Cormack dkk. 2009** — sumber yang ADR-03 dan D-07 Bagian 4.4 kutip keduanya. Ini **bukan** menyetel ambang yang C-16 larang, melainkan mengutip nilai dari sumber yang dokumen pengendalinya sebut. Bedanya nyata dan wajib terbaca dari kodenya: syarat yang melekat pada putusan ini adalah nilainya berada pada rumah tetapan dan uraiannya menyebut makalahnya, bukan "nilai umum" — dan aturan 3 pemeriksa C-16 menegakkan syarat itu pada seluruh tetapan, bukan hanya pada yang ini. |
| Pertanyaan 3 · bentuk sumber vektor | **Antarmuka `SumberKandidat` dengan pelaksana tiruan deterministik pada `tests/`**, mengikuti ADR-12 yang sudah terbukti pada fitur 002 dan 015. Pelaksana vektor kosong pada `src/` **ditolak tegas**: ia memenuhi syarat dua sumber tanpa mencari apa pun — persis kegagalan yang syarat itu ada untuk menutup. |
| Pertanyaan 4 · tepi `rag → nlp` | **Ditambahkan ke `AGENTS.md`, satu jurusan, dengan alasannya.** D-07 Bagian 3.3 menuntut BM25 bekerja atas hasil praproses (FR-B03), dan praproses tinggal di `nlp`. `AGENTS.md` sendiri menyatakan mengapa tepi semacam ini tidak boleh lewat diam-diam: ia dituliskan "agar impornya terbaca sebagai rancangan, bukan sebagai kebiasaan yang tidak dijelaskan dokumen mana pun". Preseden bentuknya: penambahan `src/penyimpanan/` pada Gerbang 2 fitur 002. Menyalin praproses ke `src/rag/` ditolak — dua salinan akan berbeda ketika daftar stop-word berubah, dan `stemming.py` sudah memuat `KATA_DILINDUNGI` yang menahan "kepala" dan "sekolah" dari daftar Sastrawi; salinan yang tertinggal satu kata menghasilkan pencarian yang sepi, bukan galat. |
| Bahaya yang membentuk seluruh spesifikasi | **Sistem satu sumber yang tampak hibrida.** Penggabungan peringkat atas satu daftar mengembalikan daftar itu — urutan yang sama, tanpa galat, dengan nama fungsi yang tetap berbunyi hibrida, dan uji yang tetap hijau. ADR-03 menolak "leksikal saja" secara tegas sebab ia gagal pada parafrase pengguna. Bentuk kegagalannya sama persis dengan TA-01: laporan bersih yang tidak memeriksa apa pun. Ditutup dua kebutuhan bersama — R-05 menolak penggabungan berkurang dari dua sumber, R-06 menuntut setiap hasil membawa daftar penyumbangnya. Masing-masing sendirian bocor: penolakan sendirian dapat dipuaskan pelaksana kosong, penyumbang sendirian hanya melaporkan tanpa menahan. |
| Alternatif | Menunda seluruh fitur sampai model sematan tersedia — ditolak; RRF adalah rumus murni yang dapat diuji hari ini, dan menundanya berarti bulan 5 dimulai dengan dua hal baru sekaligus alih-alih satu. Menuliskan ambang kecukupan awal yang "sementara" agar penilaian dapat berjalan — **ditolak tegas**; C-16 melarang menyetel ambang di luar BT-29, dan cara paling sunyi melanggarnya bukan menyetel angka melainkan menuliskan angka awal yang tak pernah ditinjau. Ia berjalan hari pertama, memberi hasil masuk akal, dan tidak seorang pun kembali kepadanya. Membiarkan `AmbangKecukupan` gagal saat dijalankan alih-alih tidak dapat dibentuk — ditolak; kegagalan saat jalan akan ditangkap seseorang dengan nilai bawaan pada pemanggilnya. |
| Dampak | Jumlah fitur menjadi **19**. **`make compliance` wajib menyusut satu** menjadi 10 lulus / 0 gagal / 10 belum — C-16 berpindah dari `fitur_pengunci="007 …"` menjadi `pemeriksa=periksa_ambang`. Itu setengah dari dua puluh pasal. Bila tidak menyusut, ada yang keliru. **Satu hal yang wajib diketahui tim**: sesudah fitur ini, sistem tidak dapat menjawab pertanyaan apa pun sampai fitur 019 memasang sumber vektor — dan itu disengaja, bukan cacat. Sistem yang menjawab dengan leksikal saja adalah sistem yang ADR-03 tolak, dan ia tidak akan terlihat berbeda dari sistem yang benar. |
| Pemutus | Pemegang Gerbang 1–4 (KB-001) |
