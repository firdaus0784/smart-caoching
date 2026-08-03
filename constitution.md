# constitution.md

Pasal yang berlaku pada setiap tugas. Tidak dapat ditawar, tidak dapat dilewati
untuk mengejar tenggat. Pelanggaran satu pasal membatalkan tugas, bukan
mengurangi nilainya.

Diubah hanya lewat keputusan tim, dicatat pada `docs/D12.md`. Agen tidak
mengubah berkas ini.

## Kepatuhan

**C-01** Sistem tidak menayangkan klaim manajerial tanpa sitasi yang
terverifikasi terhadap segmen yang diambil.
→ MK-07, D07 §6

**C-02** Segmen berlisensi tertutup tidak pernah masuk konteks yang dikirim
ke LLM. Pemisahan pada tingkat indeks, bukan penyaringan saat kueri.
→ FR-D06, VS-04

**C-03** Layanan RAG dan pelatihan tidak memiliki akses ke area karantina.
Kredensial berbeda, bukan penanda status.
→ ADR-06

**C-04** Telemetri tidak merekam bagi pengguna tanpa persetujuan aktif.
Pencabutan menghentikan perekaman seketika.
→ FR-J05

**C-05** Kunci pemetaan pseudonim tidak berada pada basis data yang sama
dengan data perilaku, dan tidak terjangkau dari layanan aplikasi.
→ KA-03, RE-05

**C-06** Butir pengetahuan tidak tayang tanpa persetujuan kurator.
→ FR-I03

**C-07** Sistem tidak menjawab berdasarkan regulasi berstatus dicabut.
→ VS-06, KL-07

**C-17** Sistem tidak memiliki kemampuan bertindak: tanpa pemanggilan alat,
tanpa akses tulis dari jalur penjawaban, tanpa pengiriman pesan keluar.
→ FR-F17, D13 KD-09

**C-18** Konten hasil pengambilan tidak pernah ditempatkan pada posisi
instruksi dalam permintaan ke LLM.
→ NFR-22, D13 KD-07

**C-19** Klaim tidak bersandar tunggal pada segmen peringkat T3 atau T4.
→ FR-F15, VS-08

## Teknis

**C-08** Seluruh pemanggilan model lewat `src/llm/`. Pembungkus mencatat
versi model, konfigurasi, waktu, biaya.
→ ADR-11

**C-09** Setiap keluaran eksperimen mencatat versi kode, model, indeks,
skema anotasi, dan pembagian data ke `logbook/`.
→ NFR-15, D10 L1

**C-10** Rentang anotasi memakai indeks karakter, bukan indeks token.
→ D03 §15

**C-11** Cakupan uji pada modul inti tidak turun.
→ NFR-16

**C-12** Tidak ada ketergantungan baru tanpa persetujuan penanggung jawab
teknis.

**C-13** Bahasa antarmuka: kalimat ≤ 20 kata, istilah teknis dijelaskan pada
kemunculan pertama, tanpa singkatan yang tidak diuraikan.
→ NFR-19

**C-20** Bentuk tanggapan dan daftar rute mengikuti `docs/D14.md`.
Penambahan bidang pada tanggapan `/api/v1/tanya` dilarang tanpa persetujuan
manusia — bentuk itu adalah tempat C-02, C-07, dan C-19 diwujudkan.
→ D14 AG-03

## Ruang lingkup

**C-14** Fitur pada `docs/D01.md` Bagian 4.2 tidak dibangun pada siklus 2026,
dalam bentuk apa pun, termasuk kerangka kosong: gamifikasi, aplikasi mobile
native, personalisasi berbasis riwayat, peer mentoring, integrasi Dapodik
tingkat sistem, analitik prediktif.

**C-15** Tidak membuat tabel poin, lencana, papan peringkat, atau pertemanan.
Membuatnya kosong pun tidak.
→ D04 §9

**C-16** Ambang tidak disetel di luar prosedur kalibrasi `docs/D07.md` BT-29.
Bila tingkat penolakan validator terlalu tinggi, perbaiki pengambilan —
jangan longgarkan validator.

## Catatan

C-17 sampai C-19 ada karena validator sitasi tidak melindungi dari penyisipan
instruksi; pada segmen yang disusupi ia justru dapat mengesahkan jawaban jahat
karena klaimnya memang didukung segmen tersebut. Ketiadaan kemampuan bertindak
(C-17) adalah yang membatasi kerugian. Jangan menambahkannya.

Latar lengkap: `docs/D13.md` Bagian 1 dan 7.
