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
