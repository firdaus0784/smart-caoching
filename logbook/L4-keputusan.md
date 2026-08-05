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
